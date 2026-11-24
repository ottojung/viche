"""Revoke only obsolete gap-local compiler processes, never agent sessions.

No remote calls, no model invocation, no process-group signals. A pidfd pins
the actual process; the gap lock serializes the terminal check with reacquire.
"""
import ctypes
import fcntl
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from . import config, state
from . import assignment as bindings

COMPILERS = {"lean", "lake", "checklemma"}
TERMINAL = {"STALE", "RELEASED", "ACCEPTED", "PR_OPEN"}
INTERVAL = 2
GRACE = 3
PROC = Path("/proc")


def pidfd_open(pid):
    if hasattr(os, "pidfd_open"):
        return os.pidfd_open(pid, 0)
    libc = ctypes.CDLL(None, use_errno=True)
    func = getattr(libc, "pidfd_open", None)
    if func is None:
        raise OSError("pidfd_open unavailable")
    fd = func(ctypes.c_int(pid), ctypes.c_uint(0))
    if fd < 0:
        err = ctypes.get_errno()
        raise OSError(err, os.strerror(err))
    return fd


def send(fd, sig):
    if hasattr(signal, "pidfd_send_signal"):
        return signal.pidfd_send_signal(fd, sig)
    libc = ctypes.CDLL(None, use_errno=True)
    func = getattr(libc, "pidfd_send_signal", None)
    if func is None:
        raise OSError("pidfd_send_signal unavailable")
    if func(ctypes.c_int(fd), ctypes.c_int(sig), None, ctypes.c_uint(0)) < 0:
        err = ctypes.get_errno()
        raise OSError(err, os.strerror(err))


def assignment(cwd):
    """Only exact canonical gap worktrees; no loose process-title matching."""
    local = bindings.workspace(cwd)
    if local:
        return local[0]
    for root, research in ((config.WORKTREES_DIR, False),):
        try:
            parts = cwd.relative_to(Path(root).resolve()).parts
        except ValueError:
            continue
        if not parts or not config.GAP_ID_RE.fullmatch(parts[0]):
            continue
        if research and (len(parts) < 2 or parts[1] != "path"):
            continue
        return parts[0]
    return None


def identity(entry):
    """Confirm executable, working tree, UID and start identity."""
    try:
        if entry.stat().st_uid != os.getuid():
            return None
        if (entry / "comm").read_text().strip() not in COMPILERS:
            return None
        if (entry / "exe").resolve(strict=True).name not in COMPILERS:
            return None
        gap = assignment((entry / "cwd").resolve(strict=True))
        if gap is None:
            return None
        fields = (entry / "stat").read_text().rsplit(")", 1)[1].split()
        if fields[0] == "Z":
            return None
        return gap, int(fields[19])
    except (OSError, ValueError, IndexError, RuntimeError):
        return None


def managed_lease(entry, gap):
    """Recover the exact lease inherited by a managed compiler, not a guess."""
    try:
        env = dict(part.split(b"=", 1) for part in
                   (entry / "environ").read_bytes().split(b"\0") if b"=" in part)
        if env.get(b"PNP_MANAGED_COMPILER") != b"1" or env.get(b"PNP_PUBLISH_GAP") != gap.encode():
            return None
        return env.get(b"PNP_PUBLISH_LEASE", b"").decode() or None
    except (OSError, ValueError):
        return None


def stop_if_terminal(entry, expected, pending, now):
    pid = int(entry.name)
    fd = pidfd_open(pid)
    try:
        if identity(entry) != expected:
            return None
        gap, start = expected
        lock = os.open(os.path.join(state.gap_dir(gap), ".lock"), os.O_RDWR)
        try:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return None
            rec = state.load(gap)
            if not isinstance(rec, dict) or rec.get("gap_id") != gap:
                return None
            current = rec.get("lease")
            if not isinstance(current, str) or not current:
                return None
            previous = managed_lease(entry, gap)
            if previous is None:
                try:
                    bound = bindings.binding((entry / "cwd").resolve(strict=True))
                    if bound and bound[0] == gap:
                        previous = bound[1]
                except OSError:
                    pass
            superseded = previous is not None and previous != current
            if rec.get("state") not in TERMINAL and not superseded:
                return None
            # Recheck after acquiring the gap lock. A replaced PID or cwd
            # cannot be used to authorize sending a signal to another job.
            if identity(entry) != expected:
                return None
            key = pid, start, gap, previous or current
            first = pending.get(key)
            if first is not None and now - first < GRACE:
                return key, first
            sig = signal.SIGTERM if first is None else signal.SIGKILL
            send(fd, sig)
            print("obsolete compiler", pid, gap, "SUPERSEDED" if superseded else rec["state"], sig.name, flush=True)
            return key, now if first is None else first
        finally:
            os.close(lock)
    finally:
        os.close(fd)


def scan(pending=None, proc=PROC, now=None):
    pending = pending or {}
    now = time.monotonic() if now is None else now
    result = {}
    try:
        entries = list(proc.iterdir())
    except OSError:
        return result
    for entry in entries:
        if not entry.name.isdigit():
            continue
        item = identity(entry)
        if item is None:
            continue
        try:
            killed = stop_if_terminal(entry, item, pending, now)
            if killed:
                key, first = killed
                result[key] = first
        except (OSError, ValueError, TypeError, KeyError):
            # A disappearing process, malformed state or unsupported pidfd
            # never licenses a less precise fallback signal.
            continue
    return result


def lock_path():
    return os.path.join(config.CACHE_DIR, "compiler-watchdog.lock")


def ensure():
    """Start only this deterministic local watchdog; kernel lock owns lifetime."""
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    fd = os.open(lock_path(), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        log = os.path.join(config.CACHE_DIR, "compiler-watchdog.log")
        with open(log, "a", encoding="utf-8") as out:
            subprocess.Popen([sys.executable, "-m", "missions.pnp.watchdog",
                              "--serve", str(fd)],
                             cwd=str(Path(__file__).resolve().parents[2]),
                             stdin=subprocess.DEVNULL, stdout=out, stderr=out,
                             start_new_session=True, pass_fds=(fd,))
    finally:
        os.close(fd)


def serve(fd):
    # Exit on replacement of our implementation; ordinary lifecycle restarts.
    source = Path(__file__).resolve()
    version = source.stat().st_mtime_ns, source.stat().st_ino
    pending = {}
    try:
        while (source.stat().st_mtime_ns, source.stat().st_ino) == version:
            pending = scan(pending)
            time.sleep(INTERVAL)
    finally:
        os.close(fd)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--serve":
        serve(int(sys.argv[2]))
    else:
        ensure()

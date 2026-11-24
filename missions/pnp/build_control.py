"""Priority reader/writer queue for PnP Lean builds, not agent sessions."""
import contextlib
import fcntl
import os
from pathlib import Path
import time

from . import config, state

GIB = 1024 ** 3
RESERVE = 2 * GIB
LIGHT_RSS = 2 * GIB
HEAVY_MIN = 4 * GIB
LIGHT_SLOTS = 2


class BuildDeferred(Exception):
    pass


class MemoryDeferred(BuildDeferred):
    def __init__(self, reason, required):
        super().__init__(reason)
        self.required = required


def lock_path():
    return os.path.join(config.CACHE_DIR, "publication-build.lock")


def priority_path():
    return os.path.join(config.CACHE_DIR, "publication-priority.lock")


def obsolete(gap=None, lease=None):
    gap = gap or os.environ.get("PNP_PUBLISH_GAP")
    lease = lease or os.environ.get("PNP_PUBLISH_LEASE")
    if not gap:
        return False
    try:
        rec = state.load(gap)
    except (OSError, ValueError, TypeError):
        return False
    if not isinstance(rec, dict):
        return False
    if lease and rec.get("lease") and lease != rec["lease"]:
        return True
    return rec.get("state") in ("STALE", "RELEASED", "ACCEPTED", "PR_OPEN")


def try_lock(fd, mode):
    try:
        fcntl.flock(fd, mode | fcntl.LOCK_NB)
        return True
    except BlockingIOError:
        return False


def legacy_compilers(proc=Path("/proc")):
    """Detect existing unmanaged PnP compilers; never terminate them here."""
    try:
        entries = list(proc.iterdir())
    except OSError:
        return []
    found = []
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            if (entry / "comm").read_text().strip() not in ("lean", "lake", "checklemma"):
                continue
            cwd = (entry / "cwd").resolve(strict=True)
            if not any(part in ("pnp", "pnp-work") or part.startswith("pequalnp")
                       or part.startswith("pnp-") for part in cwd.parts):
                continue
            if b"PNP_MANAGED_COMPILER=1" in (entry / "environ").read_bytes().split(b"\0"):
                continue
            found.append(int(entry.name))
        except (OSError, ValueError):
            continue
    return found


def light_slot():
    """At most two light reservations, admitted against measured headroom."""
    for index in range(LIGHT_SLOTS):
        path = os.path.join(config.CACHE_DIR, "lean-light-%d.lock" % index)
        fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
        if try_lock(fd, fcntl.LOCK_EX):
            return fd, index + 1
        os.close(fd)
    return None, LIGHT_SLOTS


@contextlib.contextmanager
def slot(timeout=600, heavy=True, publication=True):
    """Heavy=exclusive; light=shared; a waiting publisher bars new research."""
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    fd = os.open(lock_path(), os.O_CREAT | os.O_RDWR, 0o600)
    priority = os.open(priority_path(), os.O_CREAT | os.O_RDWR, 0o600)
    deadline = time.monotonic() + timeout
    preferred = False
    light = None
    try:
        while True:
            if obsolete():
                raise BuildDeferred("compilation assignment ended")
            # A publisher retains the gate while waiting for existing builds.
            # Research holds it only during the short admission decision.
            if not preferred:
                preferred = try_lock(priority, fcntl.LOCK_EX)
            if preferred:
                if try_lock(fd, fcntl.LOCK_EX if heavy else fcntl.LOCK_SH):
                    free = headroom()
                    # During migration, defer rather than fighting a legacy
                    # raw Lean/checklemma process for RAM.
                    legacy = legacy_compilers()
                    if heavy:
                        enough = free is not None and free >= RESERVE + HEAVY_MIN
                    else:
                        light, _ = light_slot()
                        # Reserve both potential light jobs conservatively.
                        enough = light is not None and free is not None and free >= RESERVE + LIGHT_SLOTS * LIGHT_RSS
                    if enough and not legacy:
                        fcntl.flock(priority, fcntl.LOCK_UN)
                        preferred = False
                        break
                    if light is not None:
                        os.close(light)
                        light = None
                    fcntl.flock(fd, fcntl.LOCK_UN)
                    # If admission fails for memory/legacy reasons, allow
                    # other requests to re-evaluate; do not monopolize gate.
                    fcntl.flock(priority, fcntl.LOCK_UN)
                    preferred = False
                elif not publication:
                    fcntl.flock(priority, fcntl.LOCK_UN)
                    preferred = False
            if time.monotonic() >= deadline:
                raise BuildDeferred("Lean queue, legacy compiler or host memory busy; retry later")
            time.sleep(0.25)
        yield (fd,) if light is None else (fd, light)
    finally:
        if light is not None:
            os.close(light)
        os.close(priority)
        os.close(fd)


def busy():
    """True while a heavy build holds the lock or publication is waiting."""
    for path in (priority_path(), lock_path()):
        try:
            fd = os.open(path, os.O_RDONLY)
        except FileNotFoundError:
            continue
        except OSError:
            return None
        try:
            if not try_lock(fd, fcntl.LOCK_EX):
                return True
        except OSError:
            return None
        finally:
            os.close(fd)
    return False


def headroom(root=Path("/sys/fs/cgroup"), meminfo=Path("/proc/meminfo")):
    """Budget clean, reclaimable cache with a haircut and host-availability cap."""
    try:
        maximum = (root / "memory.max").read_text().strip()
        if maximum == "max":
            return None
        limit = int(maximum)
        current = int((root / "memory.current").read_text())
        stats = {k: int(v) for k, v in (line.split() for line in
                 (root / "memory.stat").read_text().splitlines())}
        if "file" in stats:
            clean = max(0, stats["file"] - sum(stats.get(k, 0) for k in
                         ("shmem", "file_dirty", "file_writeback", "unevictable")))
            reclaimable = clean * 9 // 10 + stats.get("slab_reclaimable", 0) // 2
        else:
            reclaimable = stats.get("inactive_file", 0)
        result = max(0, min(limit, limit - current + reclaimable))
        # Root cgroup cannot reclaim more memory than the host can supply.
        try:
            available = next(int(line.split()[1]) * 1024 for line in
                             meminfo.read_text().splitlines()
                             if line.startswith("MemAvailable:"))
            result = min(result, available)
        except (OSError, ValueError, StopIteration):
            pass
        return result
    except (OSError, ValueError, TypeError):
        return None


def group_rss(group, proc=Path("/proc")):
    rss = 0
    page = os.sysconf("SC_PAGE_SIZE")
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            fields = (entry / "stat").read_text().rsplit(")", 1)[1].split()
            if int(fields[2]) == group:
                rss += max(0, int(fields[21])) * page
        except (OSError, ValueError, IndexError):
            continue
    return rss


def memory_reason(group, heavy=True):
    free = headroom()
    if free is not None and free < RESERVE:
        return "host memory reserve threatened"
    # The light class is deliberately bounded; a larger job belongs in heavy.
    # No fixed RSS ceiling applies to heavy builds.
    if not heavy:
        try:
            if group_rss(group) > LIGHT_RSS:
                return "light compilation exceeded 2 GiB; retry as heavy"
        except OSError:
            pass
    return None


def resource_ready(rec):
    required = rec.get("publisher_memory_required")
    if not required:
        return True
    free = headroom()
    return free is not None and free >= required


def oom_count(root=Path("/sys/fs/cgroup")):
    try:
        return int(dict(line.split() for line in
                        (root / "memory.events").read_text().splitlines())["oom_kill"])
    except (OSError, KeyError, ValueError):
        return None

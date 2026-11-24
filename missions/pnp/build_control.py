"""Bound publication memory and cancel only an obsolete publisher's own build."""
import contextlib
import fcntl
import os
from pathlib import Path
import time

from . import config, state


class BuildDeferred(Exception):
    pass


def lock_path():
    return os.path.join(config.CACHE_DIR, "publication-build.lock")


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
    return rec.get("state") in ("STALE", "RELEASED", "ACCEPTED")


@contextlib.contextmanager
def slot(timeout=600):
    # Full Mathlib loads have consumed 6-9 GiB each on the 15 GiB host.
    # Serialize only heavyweight publisher builds, not reasoning workers.
    # The descriptor survives in the compiler child; kernel release on death.
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    fd = os.open(lock_path(), os.O_CREAT | os.O_RDWR, 0o600)
    deadline = time.monotonic() + timeout
    try:
        while True:
            if obsolete():
                raise BuildDeferred("publication assignment ended")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                free = headroom()
                if free is not None and free < MAX_BUILD_RSS + RESERVE:
                    fcntl.flock(fd, fcntl.LOCK_UN)
                    if time.monotonic() >= deadline:
                        raise BuildDeferred("insufficient memory for full publication build")
                    time.sleep(2)
                    continue
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise BuildDeferred("publication compiler busy; retry")
                time.sleep(2)
        yield fd
    finally:
        os.close(fd)


def busy():
    try:
        fd = os.open(lock_path(), os.O_RDONLY)
    except FileNotFoundError:
        return False
    except OSError:
        return None
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        return False
    except OSError:
        return None
    finally:
        os.close(fd)


GIB = 1024 ** 3
RESERVE = 2 * GIB
MAX_BUILD_RSS = 6 * GIB


def headroom(root=Path("/sys/fs/cgroup")):
    """Conservative cgroup headroom, excluding reclaimable inactive file cache."""
    try:
        limit = int((root / "memory.max").read_text())
        current = int((root / "memory.current").read_text())
        stats = dict(line.split() for line in
                     (root / "memory.stat").read_text().splitlines())
        return max(0, limit - current + int(stats.get("inactive_file", "0")))
    except (OSError, ValueError, TypeError):
        return None


def group_rss(group, proc=Path("/proc")):
    """Sum RSS in our own process group; no arbitrary process selection."""
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


def memory_reason(group):
    free = headroom()
    if free is not None and free < RESERVE:
        return "host memory reserve threatened"
    try:
        if group_rss(group) > MAX_BUILD_RSS:
            return "publication build exceeded 6 GiB RSS budget"
    except OSError:
        pass
    return None

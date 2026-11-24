"""Bound publication memory and cancel only an obsolete publisher's own build."""
import contextlib
import fcntl
import os
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

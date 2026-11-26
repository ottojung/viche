"""Shared memory admission for relay compilers (legacy and exact-base)."""
import contextlib
import fcntl
import os
from pathlib import Path
import time

MIB = 1024 * 1024
RESERVE = 3072
SLOTS = 2
LEGACY_SLOTS = 3


def headroom(cgroup=Path("/sys/fs/cgroup"), meminfo=Path("/proc/meminfo")):
    try:
        host = next(int(x.split()[1])*1024 for x in meminfo.read_text().splitlines()
                    if x.startswith("MemAvailable:"))
        limit = (cgroup/"memory.max").read_text().strip()
        if limit == "max":
            return host//MIB
        used = int((cgroup/"memory.current").read_text())
        stats = dict(x.split() for x in (cgroup/"memory.stat").read_text().splitlines())
        # Clean file-backed cache is reclaimable even when on the active LRU.
        # Never count tmpfs, dirty/writeback pages or unevictable pages.
        reclaimable = max(0, int(stats.get("file","0")) -
            sum(int(stats.get(k,"0")) for k in ("shmem","file_dirty","file_writeback","unevictable")))
        return max(0, min(host, int(limit)-used+reclaimable))//MIB
    except (OSError, ValueError, StopIteration):
        return None


def trylock(f):
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except BlockingIOError:
        return False


@contextlib.contextmanager
def slot(rss_mib=8192, timeout=180, cancelled=lambda:False, directory=None):
    """Account for all relay compile lanes, including older slot holders.

    Conservative reservation: do not count on an existing job already having
    allocated its predicted memory. Cgroup headroom includes reclaimable
    clean file cache but is capped by host available memory.
    """
    if not 256 <= rss_mib <= 12288:
        raise ValueError("invalid compiler reservation")
    root = Path(directory or Path.home()/".local/state/sibling")
    root.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic()+timeout
    own = None
    while not cancelled() and time.monotonic()<deadline:
        with (root/"memory-admission.lock").open("a+") as gate:
            if trylock(gate):
                free = []
                active = []
                try:
                    for i in range(LEGACY_SLOTS):
                        f = (root/("slot%d.lock"%i)).open("a+")
                        if trylock(f):
                            free.append(f)
                        else:
                            f.seek(0)
                            try: amount=int(f.read().strip())
                            except ValueError: amount=12288
                            active.append(max(256,min(12288,amount)))
                            f.close()
                    available=headroom()
                    if (free and len(active)<SLOTS and available is not None
                            and available>=RESERVE+rss_mib+sum(active)):
                        own=free.pop(0)
                        own.seek(0);own.truncate()
                        own.write(str(rss_mib));own.flush()
                finally:
                    for f in free:f.close()
        if own:
            break
        time.sleep(.5)
    if own is None:
        raise TimeoutError("shared compiler memory/slot admission deferred")
    try:
        yield
    finally:
        own.close()

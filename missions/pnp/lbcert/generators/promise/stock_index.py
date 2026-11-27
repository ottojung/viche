"""Optional local positive-witness index. An index hit is NOT a Lean receipt.

Read fixed-size slices, validate domain/arity/topology/budget, then replay
with the independent generator evaluator. No index is built during claims.
"""
import os
import re
import stat
import struct
from pathlib import Path

MAGIC = b"VICHER01"
MAX_BYTES = 512 * 1024 * 1024


def root():
    return Path(os.environ.get("PNP_STATE_ROOT",
        "/var/lib/lubko/wd/viche-state/pnp")) / "lbcert" / "formula-index"


def path_for(problem):
    kind, n, m, _, _, pred = problem
    if kind not in ("two", "matrix") or pred not in ("FanInTwo", "Monotone2"):
        return None
    if type(n) is not int or type(m) is not int or not 1 <= n <= 10 or not 1 <= m <= 10:
        return None
    return root() / f"{kind}-{n}-{m}-{pred}.idx"


def file_version(path):
    """Cheap metadata identity; only regular, non-symlink files count."""
    try:
        st = path.lstat()
    except OSError:
        return None
    if not stat.S_ISREG(st.st_mode):
        return None
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def index_versions():
    """Snapshot each supported index once per plugin discovery pass."""
    result = {}
    try:
        entries = list(root().iterdir())
    except OSError:
        return result
    for p in entries:
        match = re.fullmatch(r"(two|matrix)-([1-9]|10)-([1-9]|10)-(FanInTwo|Monotone2)\.idx", p.name)
        if not match:
            continue
        kind, a, b, pred = match.groups()
        n, m = int(a), int(b)
        if kind == "two":
            if n != m or n * (n + 1) // 2 > 22:
                continue
        elif n + m > 10 or n * m > 22:
            continue
        version = file_version(p)
        if version is not None:
            result[p.name] = repr(version).encode()
    return result


def version_for(problem, versions):
    """Only the relevant domain invalidates a failed plugin attempt."""
    path = path_for(problem) if problem else None
    return versions.get(path.name, b"missing") if path else b"unsupported"


def batch_version():
    """Only two-lit stock affects the two-lit batch's generation version."""
    result = []
    for n in (5, 6):
        for pred in ("FanInTwo", "Monotone2"):
            p = path_for(("two", n, n, 0, 0, pred))
            version = file_version(p)
            if version is not None:
                result.append((n, pred, version))
    return repr(result).encode()


def lookup_file(path, problem, gen):
    n, rows, target = gen.domain(problem)
    w = len(rows)
    if not 1 <= n <= 10 or not 1 <= w <= 22 or not 0 <= target < (1 << w):
        return None
    start = 24 + 4 * n
    end = start + 4 * (1 << w)
    fd = None
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or not end <= st.st_size <= MAX_BYTES:
            return None
        header = os.pread(fd, start, 0)
        if len(header) != start or header[:8] != MAGIC:
            return None
        ni, wi, k, u = struct.unpack_from("<4I", header, 8)
        if (ni, wi) != (n, w) or k > 15 or u > 3:
            return None
        if list(struct.unpack_from(f"<{n}I", header, 24)) != gen.input_tables(n, rows):
            return None
        off, = struct.unpack("<I", os.pread(fd, 4, start + 4 * target))
        if not end <= off <= st.st_size - 2:
            return None
        ng, out = os.pread(fd, 2, off)
        if ng > min(problem[3], k) or out >= n + ng or off + 2 + 3 * ng > st.st_size:
            return None
        data = os.pread(fd, 3 * ng, off + 2)
        if len(data) != 3 * ng:
            return None
        gates = []
        for i, (op, a, b) in enumerate(struct.iter_unpack("BBB", data)):
            if (op > 2 or a >= n + i or (op < 2 and b >= n + i)
                    or (op == 2 and problem[-1] != "FanInTwo")):
                return None
            gates.append((("and", "or", "not")[op], [a] if op == 2 else [a, b]))
        sol = (gates, out)
        return sol if gen.valid(problem, sol) else None
    except (OSError, ValueError, struct.error, AssertionError, IndexError):
        return None
    finally:
        if fd is not None:
            os.close(fd)


def lookup(problem, gen):
    path = path_for(problem)
    return lookup_file(path, problem, gen) if path is not None else None

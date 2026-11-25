"""Compact terminal research worktrees; preserve every non-reproducible file."""
import argparse
import collections
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import time

from . import assignment, config, staff, state
from .staffing import backend

OUT = "lean/PEqualNP/Outside"
TERMINAL = {"STALE", "RELEASED", "ACCEPTED"}


def git(path, *args):
    return subprocess.check_output(
        ["git", "--no-optional-locks", "-C", str(path), *args],
        stderr=subprocess.PIPE, timeout=60)


def names(raw):
    return [os.fsdecode(x) for x in raw.split(b"\0") if x]


def inside(value, path):
    return value == str(path) or value.startswith(str(path) + "/")


def idle(path, proc=Path("/proc")):
    for agent in backend.running():
        for key in ("cwd", "invocation_cwd"):
            if isinstance(agent.get(key), str) and inside(agent[key], path):
                return False
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            if entry.stat().st_uid != os.getuid():
                continue
            for link in [entry / "cwd", entry / "root", *(entry / "fd").iterdir()]:
                try:
                    if inside(os.readlink(link).removesuffix(" (deleted)"), path):
                        return False
                except FileNotFoundError:
                    pass
        except FileNotFoundError:
            pass
        except PermissionError:
            return False
    return True


def signature(path):
    status = git(path, "status", "--porcelain=v1", "-z", "--no-renames",
                 "--untracked-files=all")
    changed = set(names(git(path, "diff", "HEAD", "--name-only", "-z", "--", OUT)))
    for item in names(status):
        if item[:2] != "??" and item[3:].startswith(OUT + "/"):
            changed.add(item[3:])
    for flags in [("--others", "--exclude-standard"),
                  ("--others", "--ignored", "--exclude-standard")]:
        changed.update(names(git(path, "ls-files", "-z", *flags, "--", OUT)))
    files = {}
    for name in sorted(changed):
        q = path / name
        if q.is_symlink():
            files[name] = ["symlink", os.readlink(q)]
        elif q.is_file():
            with q.open("rb") as f:
                files[name] = ["file", hashlib.file_digest(f, "sha256").hexdigest(),
                               q.stat().st_mode & 0o777]
        elif not q.exists():
            files[name] = ["absent"]
        else:
            raise ValueError("unusual research file: " + name)
    return hashlib.sha256(status).hexdigest(), files


def backup(path, dest, files):
    """Verify compressed copies of unique excluded files before sparsifying."""
    if not files:
        return
    fd, tmp = tempfile.mkstemp(prefix=".retention-", suffix=".tgz", dir=dest.parent)
    os.close(fd)
    try:
        with tarfile.open(tmp, "w:gz", compresslevel=3, dereference=False) as out:
            for name, info in files.items():
                if info[0] != "absent":
                    out.add(path / name, arcname=name, recursive=False)
        with tarfile.open(tmp, "r:gz") as inp:
            for name, info in files.items():
                if info[0] == "absent":
                    continue
                member = inp.getmember(name)
                if info[0] == "symlink":
                    if not member.issym() or member.linkname != info[1]:
                        raise ValueError("backup link mismatch")
                elif not member.isfile():
                    raise ValueError("backup type mismatch")
                else:
                    with inp.extractfile(member) as f:
                        if hashlib.file_digest(f, "sha256").hexdigest() != info[1]:
                            raise ValueError("backup content mismatch")
        with open(tmp, "rb") as f:
            os.fsync(f.fileno())
        os.replace(tmp, dest)
        fd = os.open(dest.parent, os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


@contextlib.contextmanager
def gap_lock(gap):
    fd = os.open(Path(state.gap_dir(gap), ".lock"), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)


def size_kib(path):
    return int(subprocess.check_output(["du", "-sk", str(path)], timeout=60).split()[0])


def terminal(rec):
    return (isinstance(rec, dict) and rec.get("state") in TERMINAL
            and not rec.get("intent") and not rec.get("queued_lease"))


def compact(path):
    path = path.resolve()
    root = Path(config.GAPS_DIR).resolve()
    gap = path.relative_to(root).parts[0]
    marker = path.parent / "storage-compact.json"
    if marker.exists():
        return "already"
    # Same lock order as the staffing controller; never compete with launch.
    with staff.staffing_lock(), gap_lock(gap):
        if marker.exists():
            return "already"
        if not terminal(state.load(gap)) or not assignment.binding(path):
            return "active_or_unbound"
        if not idle(path):
            return "in_use"
        if not (path / OUT).is_dir():
            return "already_sparse"
        if git(path, "ls-files", "-u"):
            return "unmerged"
        flags = git(path, "ls-files", "-v", "-z", "--", OUT)
        if any(x and x[:1] not in (b"H", b"S") for x in flags.split(b"\0")):
            return "unusual_index"
        base = git(path, "rev-parse", "HEAD").decode().strip()
        git(path, "cat-file", "-e", base + "^{commit}")
        before = size_kib(path)
        old = signature(path)
        backup(path, path.parent / "storage-delta.tar.gz", old[1])
        if not idle(path):
            return "in_use"
        ref = "refs/viche/storage-archive/" + hashlib.sha256(str(path).encode()).hexdigest()
        git(path, "update-ref", ref, base)
        git(path, "sparse-checkout", "set", "--no-cone", "/*", "!/" + OUT + "/")
        if signature(path) != old:
            git(path, "sparse-checkout", "disable")
            raise ValueError("status/content changed; restored full materialization")
        after = size_kib(path)
        state.atomic_write(str(marker), json.dumps(
            {"base": base, "ref": ref, "status_sha256": old[0],
             "unique_excluded_files": old[1], "before_kib": before, "after_kib": after,
             "restore": "git sparse-checkout disable", "at": time.time()},
            sort_keys=True, indent=2) + "\n")
        return before - after


def sweep(limit=3):
    root = Path(config.GAPS_DIR).resolve()
    paths = sorted(p for pattern in ("*/attempts/*/workers/*/path", "*/attempts/*/path", "*/path")
                   for p in root.glob(pattern) if (p / ".git").is_file())
    counts = collections.Counter()
    saved = 0
    for path in paths:
        gap = path.relative_to(root).parts[0]
        if not terminal(state.load(gap)) or (path.parent / "storage-compact.json").exists():
            continue
        try:
            result = compact(path)
            if isinstance(result, int):
                counts["compacted"] += 1
                saved += result
                print("compacted", path.relative_to(root), "saved_kib", result, flush=True)
                if counts["compacted"] >= limit:
                    break
            else:
                counts[result] += 1
        except BlockingIOError:
            counts["busy"] += 1
            break
        except (OSError, ValueError, subprocess.SubprocessError, backend.Uncertain) as exc:
            counts["error"] += 1
            print("deferred", path.relative_to(root), type(exc).__name__, flush=True)
    return {"counts": dict(counts), "saved_kib": saved}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()
    if not 1 <= args.limit <= 30:
        parser.error("limit must be 1..30")
    print(json.dumps(sweep(args.limit), sort_keys=True))

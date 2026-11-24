"""Reuse only a successful managed build of the exact proof on a clean base."""
import hashlib
from pathlib import Path
import subprocess

from . import assignment, state


def snapshot(rec, cwd, args):
    """Ignore scratch builds, dirty inputs or custom caches."""
    if args not in (["lake", "build", rec["module"]],
                    ["lake", "build", "+" + rec["module"]]):
        return None
    found = assignment.workspace(Path(cwd))
    if not found or assignment.binding(Path(cwd)) != (rec["gap_id"], rec["lease"]):
        return None
    root = found[1]
    if Path(cwd).resolve() != (root / "lean").resolve():
        return None
    from . import gitctl
    try:
        def git(*args):
            return subprocess.check_output(["git", "-C", str(root), *args],
                                           timeout=10, text=True).strip()
        # Only the exact proof may differ under lean/. Notes elsewhere are fine.
        if git("status", "--porcelain", "--untracked-files=all", "--", "lean") not in (
                "?? " + rec["path"], "A  " + rec["path"]):
            return None
        if git("diff", "HEAD", "--name-only", "--", "lean") not in ("", rec["path"]):
            return None
        path = root / rec["path"]
        if path.is_symlink() or not path.is_file():
            return None
        gitctl.prepare_build_cache(str(root))
        packages = root / "lean/.lake/packages"
        seed = Path("/home/lubko/pequalnp-research-20261123/lean/.lake/packages")
        if packages.resolve() != seed.resolve():
            return None
        return {"lease": rec["lease"], "base": git("rev-parse", "HEAD"),
                "digest": hashlib.sha256(path.read_bytes()).hexdigest(),
                "module": rec["module"], "path": rec["path"],
                "statement": rec["statement"], "imports": rec["imports"]}
    except (OSError, ValueError, subprocess.SubprocessError, gitctl.GitError):
        return None


def record(rec, before, after):
    if not before or before != after:
        return
    with state.lock(rec["gap_id"]):
        current = state.load(rec["gap_id"])
        if current and current["lease"] == rec["lease"] and current["state"] in (
                "LEASED", "RESEARCHING", "CANDIDATE_READY"):
            current["build_evidence"] = before
            state.save(current)
            state.event(rec["gap_id"], "managed_build_evidence", {"digest": before["digest"],
                                                                "base": before["base"]})


def matching(rec, digest, base):
    e = rec.get("build_evidence")
    return isinstance(e, dict) and e == {
        "lease": rec["lease"], "base": base, "digest": digest,
        "module": rec["module"], "path": rec["path"],
        "statement": rec["statement"], "imports": rec["imports"]}

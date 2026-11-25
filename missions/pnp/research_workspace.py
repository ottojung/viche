"""Small pinned research checkout; public Outside sources remain in Git."""
import re
from pathlib import Path

from . import gitctl

OUTSIDE = "lean/PEqualNP/Outside/"
PATTERNS = ("/*", "!/" + OUTSIDE)
MODULE = re.compile(r"PEqualNP\.Outside\.[A-Za-z0-9_.]+")


def required(mirror, base, imports):
    """Include explicitly allowed Outside modules and their Outside imports."""
    pending = list(imports or ())
    seen = set()
    while pending:
        module = pending.pop()
        if not isinstance(module, str) or not MODULE.fullmatch(module):
            continue
        path = "lean/" + module.replace(".", "/") + ".lean"
        if path in seen:
            continue
        src = gitctl.run(["git", "--git-dir=" + mirror, "show", base + ":" + path]).stdout
        seen.add(path)
        for line in src.splitlines():
            if line.startswith("import "):
                pending.extend(line.split()[1:])
    return sorted(seen)


def create(mirror, path, base, imports):
    """Do not expand the huge proof corpus even temporarily."""
    path = Path(path)
    patterns = [*PATTERNS, *("/" + f for f in required(mirror, base, imports))]
    gitctl.run(["git", "--git-dir=" + mirror, "worktree", "add",
                "--detach", "--no-checkout", str(path), base])
    gitctl.run(["git", "sparse-checkout", "set", "--no-cone", *patterns], cwd=path)
    # This is exclusively the freshly created, never dispatched checkout.
    gitctl.run(["git", "reset", "--hard", base], cwd=path)
    (path / OUTSIDE).mkdir(parents=True, exist_ok=True)


def restore_incomplete(mirror, path, base, imports):
    """Only resume a marked initialization; refuse any unexpected local content."""
    path = Path(path)
    if not (path / ".git").is_file():
        create(mirror, path, base, imports)
        return
    head = gitctl.run(["git", "rev-parse", "HEAD"], cwd=path).stdout.strip()
    if head != base:
        raise gitctl.GitError("incomplete checkout has unexpected HEAD")
    # Incomplete initialization may have an empty or partially populated index.
    # Refuse to reset if a non-Git file is present, unless the checkout is already
    # fully initialized and clean. Never reset an existing researcher's work.
    files = [p for p in path.rglob("*") if p != path / ".git"
             and (p.is_file() or p.is_symlink())]
    status = gitctl.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=path).stdout
    if files:
        if status or not (path / "lean/lean-toolchain").is_file():
            raise gitctl.GitError("incomplete checkout contains local files; inspect manually")
    else:
        patterns = [*PATTERNS, *("/" + f for f in required(mirror, base, imports))]
        gitctl.run(["git", "sparse-checkout", "set", "--no-cone", *patterns], cwd=path)
        gitctl.run(["git", "reset", "--hard", base], cwd=path)
    (path / OUTSIDE).mkdir(parents=True, exist_ok=True)

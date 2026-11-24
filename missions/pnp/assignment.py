"""Immutable workspace-to-lease bindings. Researchers never type lease IDs."""
import hashlib
import json
import re
from pathlib import Path

from . import config, state


def attempt_id(lease):
    return hashlib.sha256(lease.encode()).hexdigest()[:24]


def workspace(cwd):
    try:
        parts = cwd.resolve().relative_to(Path(config.GAPS_DIR).resolve()).parts
    except ValueError:
        return None
    if not parts or not config.GAP_ID_RE.fullmatch(parts[0]):
        return None
    root = Path(state.gap_dir(parts[0]))
    if len(parts) >= 2 and parts[1] == "path":
        return parts[0], root / "path", root / "research-assignment.json"
    if len(parts) >= 6 and parts[1] == "attempts" and parts[3] == "workers" and parts[5] == "path":
        if not re.fullmatch(r"[0-9a-f]{24}", parts[2]) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,48}", parts[4]):
            return None
        parent = root / "attempts" / parts[2] / "workers" / parts[4]
        return parts[0], parent / "path", parent / "assignment.json"
    if len(parts) >= 4 and parts[1] == "attempts" and parts[3] == "path":
        if len(parts[2]) != 24 or any(c not in "0123456789abcdef" for c in parts[2]):
            return None
        parent = root / "attempts" / parts[2]
        return parts[0], parent / "path", parent / "assignment.json"
    return None


def binding(cwd=None):
    found = workspace(cwd or Path.cwd())
    if not found:
        return None
    gap, path, marker = found
    try:
        obj = json.loads(marker.read_text())
        if obj.get("gap") != gap or not isinstance(obj.get("lease"), str):
            return None
        if marker.name == "assignment.json":
            attempt = marker.parent.parent.parent.name if marker.parent.parent.name == "workers" else marker.parent.name
            if attempt != attempt_id(obj["lease"]):
                return None
        return gap, obj["lease"]
    except (OSError, ValueError, AttributeError):
        return None


def first_attempt(gap):
    try:
        with open(state.events_path(gap), encoding="utf-8") as f:
            events = [json.loads(line) for line in f]
        return sum(e.get("kind") == "acquired" for e in events) == 1 and not any(
            e.get("kind") == "reacquired" for e in events)
    except (OSError, ValueError, AttributeError):
        return False


def prepare(gap, checkout=True, worker=None):
    """Executive calls once per assignment. Never relabel an old checkout."""
    from . import gitctl
    if not isinstance(gap, str) or not config.GAP_ID_RE.fullmatch(gap):
        raise ValueError("invalid gap")
    with state.lock(gap):
        rec = state.load(gap)
        if not rec or rec.get("state") not in ("LEASED", "RESEARCHING") or not rec.get("lease"):
            raise ValueError("no live research assignment")
        lease = rec["lease"]
        root = Path(state.gap_dir(gap))
        old = root / "path"
        legacy = root / "research-assignment.json"
        if worker is not None:
            if not re.fullmatch(r"[a-zA-Z0-9_-]{1,48}", worker):
                raise ValueError("invalid worker workspace label")
            parent = root / "attempts" / attempt_id(lease) / "workers" / worker
            path, marker = parent / "path", parent / "assignment.json"
        elif old.is_dir() and first_attempt(gap) and not legacy.exists():
            path, marker = old, legacy
        elif binding(old) == (gap, lease):
            path, marker = old, legacy
        else:
            parent = root / "attempts" / attempt_id(lease)
            path, marker = parent / "path", parent / "assignment.json"
        marker.parent.mkdir(parents=True, exist_ok=True)
        if marker.exists():
            if binding(path) != (gap, lease):
                raise ValueError("workspace binding conflicts; never overwrite")
        else:
            state.atomic_write(str(marker), json.dumps({"gap": gap, "lease": lease}) + "\n")
    if checkout:
        # Keep network/Git work outside the gap state lock. Do not create a
        # second worktree if the Executive retries preparation concurrently.
        import fcntl
        import os
        fd = os.open(str(marker) + ".prepare.lock", os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if not (path / ".git").exists():
                base = gitctl.ensure_mirror()
                gitctl.run(["git", "--git-dir=" + gitctl.MIRROR, "worktree", "add",
                            "--detach", str(path), base])
            gitctl.prepare_build_cache(str(path))
        except gitctl.GitError as exc:
            raise ValueError(str(exc)) from exc
        finally:
            os.close(fd)
        latest = state.load(gap)
        if not latest or latest.get("lease") != lease or latest.get("state") not in ("LEASED", "RESEARCHING"):
            raise ValueError("assignment ended during checkout preparation")
    return {"gap": gap, "cwd": str(path), "guard": "python3 /var/lib/lubko/wd/viche/missions/pnp/cli.py guard",
            "compile": "PYTHONPATH=/var/lib/lubko/wd/viche python3 -m missions.pnp.compile"}


def resolve(gap=None, lease=None, cwd=None):
    """Prefer immutable workspace identity; never adopt a new lease silently."""
    local = workspace(cwd or Path.cwd())
    bound = binding(cwd or Path.cwd())
    if local:
        if not bound or (gap and gap != bound[0]):
            raise ValueError("workspace assignment unavailable or wrong gap")
        # A copied example or the gap itself is not an assignment identifier.
        if lease and lease not in (gap, bound[0], "LEASE") and lease != bound[1]:
            raise ValueError("explicit lease conflicts with workspace assignment")
        return bound
    if not gap or not config.GAP_ID_RE.fullmatch(gap) or not lease or lease in (gap, "LEASE"):
        raise ValueError("use the bound research workspace or exact assignment")
    return gap, lease

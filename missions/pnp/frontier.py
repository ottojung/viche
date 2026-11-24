"""Cheap desk observations and cooperative work checkpoints.

A failed or incomplete observation is unknown, never a stop instruction.
Only a recorded terminal state or a superseded lease tells a worker to stop.
No agent commands or desk mutations are performed here.
"""
import json
import os
import subprocess
import time
from urllib.parse import urlencode

from . import config, state, build_control

MAX_AGE = 300
ACTIVE = ("LEASED", "RESEARCHING", "CANDIDATE_READY", "LOCAL_CHECKED")
STOPPED = ("STALE", "RELEASED", "ACCEPTED", "PR_OPEN")


def cache_path():
    return os.path.join(config.STATE_ROOT, "frontier.json")


def count(x):
    return x if type(x) is int and x >= 0 else None


def normalize(raw, now):
    if not isinstance(raw, dict) or not isinstance(raw.get("gaps"), list):
        raise ValueError("unreadable frontier")
    rows = {}
    for item in raw["gaps"]:
        if not isinstance(item, dict):
            raise ValueError("unreadable gap")
        gid = item.get("id")
        if not isinstance(gid, str) or not config.GAP_ID_RE.fullmatch(gid):
            raise ValueError("invalid gap id")
        if gid in rows:
            raise ValueError("duplicate gap")
        rows[gid] = {"held": count(item.get("held")),
                     "parallel": count(item.get("parallel"))}
    total = count(raw.get("open_gaps"))
    return {"observed": now, "complete": total == len(rows),
            "open_gaps": total, "offerable": count(raw.get("offerable_now")),
            "ordinary": count(raw.get("offerable_now_ordinary")),
            "held": count(raw.get("held_now")), "gaps": rows}


def refresh():
    url = config.DESK_BASE + "/status?" + urlencode({"handle": config.GH_USER})
    result = subprocess.run(["curl", "-fsS", "--max-time", "8", url],
                            capture_output=True, text=True, timeout=10, check=True)
    snapshot = normalize(json.loads(result.stdout), time.time())
    state.atomic_write(cache_path(), json.dumps(snapshot) + "\n")
    return snapshot


def load(now=None):
    now = time.time() if now is None else now
    try:
        with open(cache_path(), encoding="utf-8") as f:
            data = json.load(f)
        age = now - data["observed"]
        if 0 <= age <= MAX_AGE and isinstance(data["gaps"], dict):
            return data
    except (OSError, ValueError, TypeError, KeyError):
        pass
    return {}


def missing(snapshot, gap):
    return (snapshot.get("complete") is True and
            isinstance(snapshot.get("gaps"), dict) and gap not in snapshot["gaps"])


def checkpoint(gap, lease=None, now=None):
    """Read-only, constant-time decision. No network, no agent termination."""
    now = time.time() if now is None else now
    try:
        rec = state.load(gap)
    except (OSError, ValueError, TypeError):
        rec = None
    if not isinstance(rec, dict):
        return {"decision": "wait", "reason": "assignment unavailable"}
    status = rec.get("state")
    if lease and not rec.get("lease"):
        return {"decision": "wait", "reason": "assignment identity unavailable"}
    if lease and rec.get("lease") != lease:
        return {"decision": "stop", "reason": "assignment superseded"}
    if status in STOPPED:
        return {"decision": "stop", "reason": status}
    if status == "REJECTED" and rec.get("pr_number"):
        return {"decision": "continue", "reason": "correct existing PR"}
    if status not in ACTIVE:
        return {"decision": "wait", "reason": status or "unknown"}
    expiry = rec.get("lease_expires_at")
    if type(expiry) not in (float, int) or expiry <= now:
        return {"decision": "wait", "reason": "lease needs confirmation"}
    if status in ("CANDIDATE_READY", "LOCAL_CHECKED") and rec.get("queued_lease"):
        return {"decision": "wait", "reason": (
            "publisher needs more memory; preserve or simplify proof"
            if not build_control.resource_ready(rec) else "publisher owns candidate")}
    return {"decision": "continue", "reason": "live local assignment",
            "publisher_build_busy": build_control.busy()}


if __name__ == "__main__":
    try:
        refresh()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print("frontier temporarily unavailable:", exc)

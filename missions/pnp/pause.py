"""Bounded maintenance pauses, distinct from the explicit emergency STOP."""
import argparse
import json
import math
from pathlib import Path
import time

from . import config, state

MAX_SECONDS = 3600


def status(root=None, now=None):
    root = Path(config.STATE_ROOT if root is None else root)/"lbcert"
    now = time.time() if now is None else now
    # Existing STOP is an emergency/host-boundary interlock. It is not
    # silently reinterpreted as permission to resume.
    try:
        (root/"STOP").lstat()
        return {"paused": True, "kind": "emergency", "reason": "explicit STOP"}
    except FileNotFoundError:
        pass
    except OSError:
        return {"paused": True, "kind": "invalid", "reason": "STOP unreadable"}
    try:
        raw = json.loads((root/"MAINTENANCE.json").read_text())
    except FileNotFoundError:
        return {"paused": False, "kind": "none"}
    except (OSError, ValueError):
        return {"paused": True, "kind": "invalid", "reason": "maintenance marker unreadable"}
    if not isinstance(raw, dict):
        return {"paused": True, "kind": "invalid"}
    at, expires = raw.get("at"), raw.get("expires")
    author, reason = raw.get("author"), raw.get("reason")
    if (type(at) not in (int, float) or type(expires) not in (int, float)
            or not math.isfinite(at) or not math.isfinite(expires)
            or not 0 < expires-at <= MAX_SECONDS or at > now+30
            or not isinstance(author,str) or not author.strip()
            or not isinstance(reason,str) or not reason.strip()):
        return {"paused": True, "kind": "invalid", "reason": "malformed maintenance marker"}
    return {**raw, "paused": now < expires, "kind": "maintenance"}


def paused(root=None, now=None):
    return status(root, now)["paused"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", choices=("status", "allowed", "maintenance"))
    ap.add_argument("--author")
    ap.add_argument("--reason")
    ap.add_argument("--seconds", type=int, default=MAX_SECONDS)
    a = ap.parse_args()
    if a.action == "maintenance":
        if not a.author or not a.author.strip() or not a.reason or not a.reason.strip() or not 0<a.seconds<=MAX_SECONDS:
            ap.error("maintenance requires author, reason, and duration 1..3600 s")
        if status()["kind"] in ("emergency", "invalid"):
            ap.error("resolve the existing safety interlock separately")
        path = Path(config.STATE_ROOT)/"lbcert"/"MAINTENANCE.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        now = time.time()
        state.atomic_write(str(path), json.dumps(dict(author=a.author, reason=a.reason,
                                                       at=now, expires=now+a.seconds))+"\n")
    result = status()
    if a.action == "allowed":
        return int(result["paused"])
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

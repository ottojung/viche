"""Validated live tuning, without permission to acquire or release leases."""
import json
import re
import fcntl
from pathlib import Path

from .. import config, state

DEFAULT = {
    "interval": 5, "parallel": 4, "retry_min": 5, "retry_max": 180,
    "short_run": 20, "ambiguity_grace": 45, "support_refresh": 600,
    "focus_obligations": 2, "rotate_after": 3, "paused": False, "extras": [],
}
BOUNDS = {
    "interval": (2, 60), "parallel": (1, 12), "retry_min": (2, 60),
    "retry_max": (30, 1800), "short_run": (5, 120),
    "ambiguity_grace": (30, 600), "support_refresh": (120, 3600),
    "focus_obligations": (0, 12), "rotate_after": (2, 12),
}


def root():
    return Path(config.STATE_ROOT, "staffing")


def load():
    path = root() / "policy.json"
    raw = json.loads(path.read_text()) if path.exists() else {}
    return validate(raw)


def validate(raw):
    if not isinstance(raw, dict) or set(raw) - set(DEFAULT):
        raise ValueError("invalid staffing policy keys")
    p = {**DEFAULT, **raw}
    for key, (lo, hi) in BOUNDS.items():
        if type(p[key]) is not int or not lo <= p[key] <= hi:
            raise ValueError("invalid staffing policy " + key)
    if p["retry_max"] < p["retry_min"] or type(p["paused"]) is not bool:
        raise ValueError("invalid retry bounds or pause")
    if not isinstance(p["extras"], list) or len(p["extras"]) > 24:
        raise ValueError("invalid extra assignments")
    seen = set()
    for x in p["extras"]:
        if not isinstance(x, dict) or set(x) != {"gap", "attempt", "label", "approach"}:
            raise ValueError("extra assignment must bind exact attempt")
        if (not config.GAP_ID_RE.fullmatch(x["gap"])
                or not re.fullmatch(r"[a-f0-9]{24}-[a-f0-9]{16}", x["attempt"])
                or not re.fullmatch(r"extra-[A-Za-z0-9_-]{1,40}", x["label"])
                or not isinstance(x["approach"], str) or not x["approach"].strip()
                or len(x["approach"]) > 4000):
            raise ValueError("invalid extra assignment")
        key = (x["gap"], x["attempt"], x["label"])
        if key in seen:
            raise ValueError("duplicate extra assignment")
        seen.add(key)
    return p

def change(update):
    directory=root()
    directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    with (directory/"policy.lock").open("a+") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        p=load()
        p=validate(update(p))
        state.atomic_write(str(directory/"policy.json"),json.dumps(p,indent=2,sort_keys=True)+"\n")
        return p

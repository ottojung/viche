"""Local first-observation evidence, independent of the desk's lease age.

A proof checked immediately after a newly seen unit is eligible for the
fast targeted path. Initial inventory or missing telemetry is not fresh.
"""
import json
import os
import time
from . import config

WINDOW = 300
CHECK_AGE = 120
OBSERVATION_MAX_GAP = 120


def observation_path():
    return os.path.join(config.STATE_ROOT, "lbcert", "seen-observation.json")


def recent(now=None):
    """Read the observer's atomic recent index, not the growing latency log.

    A missing, stale, pre-migration or malformed index is not evidence
    of a fresh release. The audit ledger remains available for reports.
    """
    now = time.time() if now is None else now
    try:
        with open(observation_path(), encoding="utf-8") as f:
            data = json.load(f)
        at = data["at"]
        rows = data["recent"]
        ids = data["ids"]
        if type(at) not in (int, float) or not 0 <= now - at <= OBSERVATION_MAX_GAP:
            return {}
        if not isinstance(rows, dict) or not isinstance(ids, list) or any(not isinstance(g, str) for g in ids):
            return {}
        known = set(ids)
        return {g: t for g, t in rows.items()
                if g in known and type(t) in (int, float)
                and t <= at and 0 <= now - t <= WINDOW}
    except (OSError, ValueError, KeyError, TypeError):
        return {}


def fresh(gid, receipt, seen, now):
    if not receipt or gid not in seen:
        return False
    at=receipt.get("at")
    return type(at) in (int,float) and seen[gid]<=at<=now and now-at<=CHECK_AGE


def available(gid, snapshot, seen=None):
    # A complete current frontier can rule out a settled unit. Missing
    # observations alone cannot rule out a freshly seen exact proof.
    if seen is not None and snapshot.get("observed",0)<seen:
        return True
    if snapshot.get("complete") and gid not in snapshot.get("gaps",{}):
        return False
    row=snapshot.get("gaps",{}).get(gid,{})
    held,parallel=row.get("held"),row.get("parallel")
    return not (type(held) is int and type(parallel) is int and held>=parallel)

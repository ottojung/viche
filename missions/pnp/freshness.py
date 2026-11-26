"""Local first-observation evidence, independent of the desk's lease age.

A proof checked immediately after a newly seen unit is eligible for the
fast targeted path. Initial inventory or missing telemetry is not fresh.
"""
import time
from . import ledger

WINDOW = 300
CHECK_AGE = 120


def recent(now=None):
    now = time.time() if now is None else now
    # First sighting is unique under note_seen. Look back enough to avoid
    # labelling a repeated observation of an old gap as a new release.
    seen = {}
    for row in ledger.read(hours=24):
        if row.get("stage") == "seen":
            gid, t = row.get("gid"), row.get("t")
            if isinstance(gid,str) and type(t) in (int,float):
                seen.setdefault(gid,t)
    return {g:t for g,t in seen.items() if 0<=now-t<=WINDOW}


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

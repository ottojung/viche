"""Batch mode: observed frontier only; no lease or worker mutations here."""
import json
from pathlib import Path
import sys
import time

from . import config, freshness, ledger, state

QUIET_SECONDS = 1200
OBSERVATION_MAX_AGE = 60
RECOVERY_WINDOW = 900
RECOVERY_MIN_SPAN = 600
RECOVERY_MIN_GAPS = 40
LEDGER_TAIL_BYTES = 256 * 1024
WITNESS_HINTS = ("two-lit", "two lit", "one-a-side", "one a side",
                 "fan-in-two", "fan in two", "table a", "representation")


def path():
    return Path(config.STATE_ROOT)/"cache"/"surge.json"


def load():
    try:
        obj = json.loads(path().read_text())
        return obj if isinstance(obj, dict) else {}
    except (OSError, ValueError):
        return {}


def decide(previous, snapshot, seen, now):
    """Do not interpret missing or stale observations as a quiet frontier."""
    observed = snapshot.get("observed")
    if type(observed) not in (int, float) or not 0 <= now-observed <= OBSERVATION_MAX_AGE:
        return previous
    ordinary = snapshot.get("ordinary")
    rows = snapshot.get("gaps", {})
    arrivals = [t for gid,t in seen.items() if gid in rows
                and type(t) in (int,float) and 0 <= now-t <= 300
                and any(h in str(rows[gid].get("title", "")).lower()
                        for h in WITNESS_HINTS)]
    witnesses = len(arrivals)
    busy = type(ordinary) is int and ordinary >= 100
    last_busy = previous.get("last_busy")
    if busy:
        last_busy = observed
    elif arrivals and (witnesses >= 50 or previous.get("active")):
        # Keep the batch alive through sporadic new arrivals, but never
        # refresh its timer merely because an old arrival remains in-window.
        last_busy = max(last_busy or 0, min(observed, max(arrivals)))
    active = bool(busy or (type(last_busy) in (int, float)
                            and 0 <= observed-last_busy < QUIET_SECONDS))
    # Stale input never extends a burst; a fresh positive observation does.
    return {"active": active, "last_busy": last_busy, "observed": observed,
            "ordinary": ordinary, "new_witnesses": witnesses}


def yield_evidence(events, now):
    """Separate raw supply from productive posting; no inference from missing data."""
    recent = [e for e in events if type(e.get("t")) in (int, float)
              and 0 <= now-e["t"] <= RECOVERY_WINDOW]
    successes = sum(e.get("stage") == "pr_opened" or
                    (e.get("stage") == "posting_generated" and e.get("result") == "generated")
                    for e in recent)
    failures = [e for e in recent if e.get("stage") == "posting_generated"
                and e.get("result") in ("unsupported", "unknown")
                and isinstance(e.get("gid"), str)]
    distinct = len({e["gid"] for e in failures})
    span = now-min((e["t"] for e in failures), default=now)
    return {"failed_gaps": distinct, "successes": successes,
            "span": int(span), "stalled": distinct >= RECOVERY_MIN_GAPS
            and span >= RECOVERY_MIN_SPAN and successes == 0}


def recent_yield(now):
    # The broker is latency-sensitive; read at most a bounded tail. A truncated
    # window is unknown, rather than evidence of zero successes.
    try:
        with open(ledger.path(), "rb") as f:
            f.seek(0, 2)
            start = max(0, f.tell()-LEDGER_TAIL_BYTES)
            f.seek(start)
            if start:
                f.readline()
            raw = f.read(LEDGER_TAIL_BYTES).splitlines()
        events = []
        for line in raw:
            try:
                e = json.loads(line)
                if isinstance(e, dict):events.append(e)
            except (ValueError, UnicodeError):
                return None
        if start and (not events or type(events[0].get("t")) not in (int, float)
                      or events[0]["t"] > now-RECOVERY_WINDOW):
            return None
        return yield_evidence(events, now)
    except OSError:
        return None


def recovery(now=None, record=None):
    now = time.time() if now is None else now
    record = load() if record is None else record
    return bool(active(now, record) and record.get("recovery") is True
                and type(record.get("observed")) in (int, float)
                and 0 <= now-record["observed"] <= OBSERVATION_MAX_AGE)


def update(snapshot, seen, now):
    old = load()
    new = decide(old, snapshot, seen, now)
    observed = snapshot.get("observed")
    if (type(observed) in (int,float) and 0 <= now-observed <= OBSERVATION_MAX_AGE
            and new.get("observed") == observed and active(now, new)):
        evidence = recent_yield(now)
        new = {**new, "yield": evidence,
               "recovery": bool(evidence and evidence["stalled"]
                                and new.get("new_witnesses", 0) < 50)}
    if new != old:
        path().parent.mkdir(parents=True, exist_ok=True)
        state.atomic_write(str(path()), json.dumps(new, sort_keys=True)+"\n")
        if bool(new.get("active")) != bool(old.get("active")):
            ledger.mark("surge_enter" if new.get("active") else "surge_exit",
                        "desk", ordinary=new.get("ordinary"),
                        new_witnesses=new.get("new_witnesses"))
        if bool(new.get("recovery")) != bool(old.get("recovery")):
            ledger.mark("surge_recovery_enter" if new.get("recovery") else "surge_recovery_exit",
                        "desk", evidence=new.get("yield"))
    return active(now, new)


def active(now=None, record=None):
    now = time.time() if now is None else now
    record = load() if record is None else record
    observed = record.get("observed")
    # Do not indefinitely suppress research when telemetry stops.
    return bool(record.get("active") and type(observed) in (int, float)
                and 0 <= now-observed <= QUIET_SECONDS)


if __name__ == "__main__":
    print("surge" if active() else "normal")

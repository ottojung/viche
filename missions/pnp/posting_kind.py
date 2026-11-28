"""Advisory ordinary-lease selection from fresh local catalog evidence.

A matcher hit is not a proof, and syntactic negation is only a proxy for
desk refute units. Bias three requests in four only while the supported
non-negated fraction is materially better; retain unfiltered exploration.
No network, lease acquisition, or proof-of authorization in this module.
"""
import json
import time
from pathlib import Path

from . import config, state

TTL = 120


def path():
    return Path(config.STATE_ROOT) / "cache" / "posting-kind.json"


def load(now):
    try:
        row = json.loads(path().read_text())
        if 0 <= now - row["at"] <= TTL:
            return row
    except (OSError, ValueError, TypeError, KeyError):
        pass
    return {}


def summarize(snapshot, rows, matches):
    counts = {"positive": 0, "negative": 0,
              "positive_match": 0, "negative_match": 0}
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or row.get("offerable_now") is not True or row.get("pr_open"):
            continue
        gid = row.get("id")
        if not isinstance(gid, str) or gid in seen:
            continue
        seen.add(gid)
        if snapshot.get("gaps", {}).get(gid, {}).get("level") != "solid":
            continue
        statement = row.get("statement")
        if not isinstance(statement, str) or not statement.strip():
            continue
        bucket = "negative" if statement.lstrip().startswith("¬") else "positive"
        counts[bucket] += 1
        if matches(statement):
            counts[bucket + "_match"] += 1
    return counts


def observe(snapshot, now=None):
    now = time.time() if now is None else now
    prior = load(now)
    if prior and now - prior["at"] < 60:
        return prior
    if snapshot.get("complete") is not True or not 0 <= now - snapshot.get("observed", 0) <= 60:
        return {}
    try:
        cache = Path(config.STATE_ROOT) / "lbcert" / "gaps-cache.json"
        meta = cache.with_suffix(".json.meta")
        before = json.loads(meta.read_text())
        at = before["at"]
        if not 0 <= now - at <= 90 or abs(snapshot["observed"] - at) > 90:
            return {}
        if cache.stat().st_size > 16 * 1024 * 1024 or cache.stat().st_mtime > at + 1:
            return {}
        rows = json.loads(cache.read_text())["gaps"]
        if json.loads(meta.read_text()) != before or not isinstance(rows, list):
            return {}
        from .lbcert import plugins
        found = plugins.discover()
        counts = summarize(snapshot, rows, lambda s: next(plugins.families_of(s, found), None) is not None)
        row = {"at": now, **counts}
        path().parent.mkdir(parents=True, exist_ok=True)
        state.atomic_write(path(), json.dumps(row) + "\n")
        return row
    except (OSError, ValueError, TypeError, KeyError):
        return {}


def choose(mem, snapshot, now):
    if snapshot.get("complete") is not True or not 0 <= now - snapshot.get("observed", 0) <= 60:
        return None
    r = load(now)
    p, n = r.get("positive", 0), r.get("negative", 0)
    pm, nm = r.get("positive_match", 0), r.get("negative_match", 0)
    if not all(type(x) is int and x >= 0 for x in (p,n,pm,nm)):
        return None
    if p < 40 or n < 40 or not 20 <= pm <= p or not 0 <= nm <= n:
        return None
    if pm / p < .20 or pm / p - nm / n < .20:
        return None
    counter = mem.get("posting_kind_counter", 0)
    if type(counter) is not int or not 0 <= counter < 4:
        counter = 0
    mem["posting_kind_counter"] = (counter + 1) % 4
    return "prove" if counter < 3 else None

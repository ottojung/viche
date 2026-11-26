"""Latency ledger: one timestamped line per pipeline stage of a step, and a report of where time goes.

Stages (first occurrence per step counts): seen (first in the open desk list), generated,
checked (exact compiler receipt), leased, pr_opened, verdict.  Publication also records its
own sub-stage durations (publish_timing).  Marking never raises: the ledger must not slow or
break the pipeline it measures.

report: python3 -m missions.pnp.ledger [HOURS]
"""
import json
import os
import statistics
import math
import sys
import time

from . import config

PATH = os.path.join(config.STATE_ROOT, "ledger.jsonl")
ORDER = ("seen", "generated", "checked", "leased", "pr_opened", "verdict")


def mark(stage, gid, **fields):
    try:
        line = json.dumps(dict(t=round(time.time(), 3), stage=stage, gid=gid, **fields),
                          sort_keys=True, default=str)
        with open(PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


class Timer:
    """with ledger.Timer() as t: ... t.lap('push') ... ; t.laps -> {name: seconds}"""

    def __init__(self):
        self.t0 = self.last = time.time()
        self.laps = {}

    def lap(self, name):
        now = time.time()
        self.laps[name] = round(self.laps.get(name, 0) + now - self.last, 2)
        self.last = now

    def total(self):
        return round(time.time() - self.t0, 2)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def read(hours=24):
    since = time.time() - hours * 3600
    out = []
    try:
        with open(PATH, encoding="utf-8") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                if e.get("t", 0) >= since:
                    out.append(e)
    except OSError:
        pass
    return out


def report(hours=24):
    ev = read(hours)
    first = {}
    timings = []
    for e in ev:
        if e["stage"] == "publish_timing":
            timings.append(e)
            continue
        first.setdefault(e["gid"], {}).setdefault(e["stage"], e["t"])
    lines = ["# Latency ledger, last %g h: %d events, %d steps" % (hours, len(ev), len(first)), ""]
    pairs = [(a, b) for i, a in enumerate(ORDER) for b in ORDER[i + 1:]]
    lines.append("| from -> to | steps | median s | p90 s |")
    lines.append("|---|---|---|---|")
    for a, b in pairs:
        d = sorted(s[b] - s[a] for s in first.values() if a in s and b in s and s[b] >= s[a])
        if d:
            lines.append("| %s -> %s | %d | %.0f | %.0f |" % (a, b, len(d), statistics.median(d),
                                                         d[max(0,math.ceil(.9*len(d))-1)]))
    if timings:
        lines += ["", "Publication sub-stages (median s over %d):" % len(timings)]
        keys = sorted({k for e in timings for k in (e.get("laps") or {})})
        for k in keys:
            v = [e["laps"][k] for e in timings if k in (e.get("laps") or {})]
            lines.append("- %s: %.1f" % (k, statistics.median(v)))
        lines.append("- total: %.1f" % statistics.median([e.get("total", 0) for e in timings]))
    return "\n".join(lines)


if __name__ == "__main__":
    print(report(float(sys.argv[1]) if len(sys.argv) > 1 else 24))

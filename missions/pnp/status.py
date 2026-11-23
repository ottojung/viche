#!/usr/bin/env python3
"""Read-only P vs NP mission state and independent, Executive-owned worker signal."""
import collections
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from missions.pnp import leaderboard
else:
    from . import leaderboard

STATE = Path(os.environ.get("VICHE_STATE_ROOT",
                            "/var/lib/lubko/wd/viche-state"))


def workers():
    """Unknown must never be reported as zero; the Executive must investigate."""
    try:
        p = subprocess.run(["antonina", "agent", "list", "--running",
                            "--page", "1", "--limit", "100", "--json"],
                           capture_output=True, text=True, timeout=8, check=True)
        data = json.loads(p.stdout)
        agents = data.get("agents")
        if not isinstance(agents, list):
            raise ValueError("unreadable agent roster")
        filtered = [a for a in agents if
                    (a.get("title") or "").startswith("Viche P vs NP:")]
        coverage = ("partial" if len(agents) >= 100 or data.get("unreadable")
                    else "complete")
        return {"count": len(filtered), "coverage": coverage,
                "agents": [{"id": a.get("id"), "title": a.get("title"),
                            "state": a.get("state")}
                           for a in filtered]}
    except (OSError, ValueError, subprocess.SubprocessError):
        return {"count": None, "coverage": "unavailable", "agents": []}


def snapshot():
    rows = []
    for path in sorted((STATE / "pnp/gaps").glob("*/state.json")):
        try:
            item = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        rows.append({"gap": item.get("gap_id"),
                     "state": item.get("state"),
                     "pr_url": item.get("pr_url"),
                     "failure_reason": item.get("failure_reason")})
    lb = leaderboard.load()
    stale = True
    if lb.get("available"):
        try:
            age = (datetime.datetime.now(datetime.timezone.utc) -
                   datetime.datetime.fromisoformat(
                       lb["observed_at"].replace("Z", "+00:00"))).total_seconds()
            stale = age > 1800
        except (KeyError, ValueError):
            stale = True
    w = workers()
    score = {k: lb.get(k) for k in ("rank", "our_steps", "leader",
                                   "runner_up", "lead_over_second",
                                   "our_margin_vs_best_competitor",
                                   "additional_steps_to_clear_first",
                                   "source_checked_at", "observed_at",
                                   "margin_change_since_previous_snapshot")}
    score["available"] = lb.get("available", False)
    score["stale"] = stale
    by_state = dict(collections.Counter(r["state"] for r in rows))
    return {
        "observed": len(rows), "by_state": by_state, "recent": rows[-12:],
        "leaderboard": score, "workers": w,
        "owned_by": "Viche Executive; other operators do not launch agents",
        "action": (
            "Executive must restore multiple independent P vs NP researchers "
            "and coordinate desk acquisition and submissions."
            if w["count"] == 0 else
            "Executive must replenish independent P vs NP research fronts; "
            "one worker is not a steady-state research program."
            if w["count"] == 1 else
            "Executive must restore visibility of the actual worker roster."
            if w["count"] is None else
            "Executive must increase the verified checked-step lead over #2 "
            "and protect the lead trajectory."
            if score.get("rank") == 1 else
            "Executive must increase checked-step throughput to gain #1; "
            "evaluate research yield, resources and worker replenishment."),
        # No timestamps here: the general government dispatch gate changes
        # only when mission facts or staffing change, not every refresh.
        "dispatch_signal": {
            "leaderboard": [score.get("rank"), score.get("our_steps"),
                            (score.get("leader") or {}).get("steps"),
                            (score.get("runner_up") or {}).get("steps")],
            "workers": w["count"], "coverage": w["coverage"],
            "gaps": by_state},
        "caveat": "Only public checked steps count; local activity is not proof."}


if __name__ == "__main__":
    print(json.dumps(snapshot(), sort_keys=True))

#!/bin/sh
# Hermetic scoreboard, ranking and staffing tests. No live network or agents.
set -eu
cd "$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)"
python3 - <<'PY'
import json
import os
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch
from missions.pnp import leaderboard, status, frontier

def people(*pairs):
    return [{"github": name, "steps": steps, "first_proof_at":
             "2026-11-23T12:00:00Z"} for name, steps in pairs]

first = leaderboard.scoreboard(people(("a", 4), ("ottojung", 5), ("b", 3)))
assert first["rank"] == 1
assert first["our_steps"] == 5
assert first["lead_over_second"] == 1
assert first["additional_steps_to_clear_first"] == 0

unranked = leaderboard.scoreboard(people(("kongeskog", 53), ("sanchan", 46)))
assert unranked["rank"] is None and unranked["our_steps"] == 0
assert unranked["additional_steps_to_clear_first"] == 54
assert unranked["our_margin_vs_best_competitor"] == -53

third = leaderboard.scoreboard(people(("a", 11), ("b", 8), ("ottojung", 2)))
assert third["rank"] == 3 and third["lead_over_second"] is None
assert third["additional_steps_to_clear_first"] == 10

same = leaderboard.scoreboard(people(("ottojung", 5), ("b", 5)))
assert same["rank"] in (1,2)
assert same["our_margin_vs_best_competitor"] == 0

for bad in (
    [{"github":"a","steps":0}], [{"github":"a","steps":True}],
    [{"github":"a","steps":1},{"github":"A","steps":2}]):
    try: leaderboard.scoreboard(bad)
    except ValueError: pass
    else: raise AssertionError("invalid leaderboard entry accepted")

with tempfile.TemporaryDirectory() as tmp:
    os.environ["VICHE_STATE_ROOT"] = tmp
    os.environ["PNP_STATE_ROOT"] = str(Path(tmp, "pnp"))
    a = {"available": True, **unranked, "observed_at": "2026-11-23T12:00:00+00:00",
         "source_checked_at": "2026-11-23T12:00:00Z", "source_version": "a"}
    leaderboard.save(a)
    history = Path(tmp, "pnp/leaderboard/history.jsonl")
    assert len(history.read_text().splitlines()) == 1
    # Same public count must not generate a new scoring event.
    leaderboard.save(dict(a, source_version="b"))
    assert len(history.read_text().splitlines()) == 1
    leaderboard.save(dict(a, **first, observed_at="2026-11-23T12:10:00+00:00"))
    assert len(history.read_text().splitlines()) == 2
    assert leaderboard.load()["margin_change_since_previous_snapshot"] == 54
    # A network failure does not wipe a prior verified rank.
    with patch.object(leaderboard, "fetch_json",
                      side_effect=subprocess.CalledProcessError(22, "curl")):
        try: leaderboard.update()
        except subprocess.CalledProcessError: pass
        else: raise AssertionError("network failure unexpectedly succeeded")
    assert leaderboard.load()["our_steps"] == 5

    def roster(n):
        return subprocess.CompletedProcess(
            args=[], returncode=0, stdout=json.dumps({
                "agents":[{"id":str(i),"title":"Viche P vs NP: proof",
                           "state":"running"} for i in range(n)],
                "unreadable":[]}),stderr="")
    with patch.object(status, "STATE", Path(tmp)), \
         patch.object(status.frontier, "load", return_value={
             "complete": True, "ordinary": 0, "offerable": 0, "gaps": {}}), \
         patch.object(status.focus, "current", return_value=None), \
         patch.object(status.support, "targets", return_value=[]), \
         patch.object(status.frontier.build_control, "busy", return_value=False), \
         patch.object(status.frontier.build_control, "legacy_compilers", return_value=[]), \
         patch.object(status.frontier.build_control, "headroom", return_value=0):
        with patch.object(status.subprocess, "run", return_value=roster(3)):
            full = status.snapshot()
        with patch.object(status.subprocess, "run", return_value=roster(0)):
            empty = status.snapshot()
        with patch.object(status.subprocess, "run",
                          side_effect=FileNotFoundError("antonina")):
            unknown = status.snapshot()
    assert full["workers"]["count"] == 3
    assert empty["workers"]["count"] == 0
    assert full["dispatch_signal"] != empty["dispatch_signal"]
    assert full["dispatch_signal"]["workers"] == 3
    assert empty["dispatch_signal"]["workers"] == 0
    assert empty["action"].startswith("Executive")
    assert unknown["workers"]["count"] is None
    assert unknown["workers"]["coverage"] == "unavailable"
    assert unknown["dispatch_signal"] != empty["dispatch_signal"]
# A malformed or partial response cannot signal that a lease has ended.
raw = {"open_gaps": 2, "offerable_now": 1, "offerable_now_ordinary": 1,
       "gaps": [{"id": "L-meta-1662", "held": 3, "parallel": 4}]}
part = frontier.normalize(raw, 100)
assert not part["complete"] and not frontier.missing(part, "L-meta-651")
full = frontier.normalize(dict(raw, open_gaps=1), 100)
assert frontier.missing(full, "L-meta-651")
for rec, expected in [
    ({"state": "LEASED", "lease": "a", "lease_expires_at": 200}, "continue"),
    ({"state": "LEASED", "lease": "a", "lease_expires_at": 50}, "wait"),
    ({"state": "STALE", "lease": "a"}, "stop"),
    ({"state": "LEASED", "lease": "b", "lease_expires_at": 200}, "stop"),
    ({"state": "CANDIDATE_READY", "lease": "a", "lease_expires_at": 200,
      "queued_lease": "a"}, "wait"),
    (None, "wait"),
]:
    with patch.object(frontier.state, "load", return_value=rec):
        assert frontier.checkpoint("L-meta-1662", "a", now=100)["decision"] == expected
gov = Path("government/executive-cycle.sh").read_text()
assert "mission_dispatch_signature=" in gov
assert "mission_dispatch_signature" in gov.split("# Founder directive 2026-11-16 (item 4):")[-1]
assert "frontier" not in gov.split("# Founder directive 2026-11-16 (item 4):")[-1]
print("PnP live-score ranking, reliable snapshots, staffing signals: passed")
PY

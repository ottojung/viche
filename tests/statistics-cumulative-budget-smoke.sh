#!/bin/sh
# Reservation liabilities persist and accumulate on the SAME real budget
# ledger; repeated runs cannot reset the 45-day Economy cap. No providers run.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
town="$d/town"
state="$d/state"
mkdir -p "$town/government" "$state"
cp "$repo/government/statistics-bounded-trial.py" "$repo/government/knowledge-budget-tool.py" \
   "$repo/government/knowledge-budget.sh" "$repo/government/knowledge-budget.conf" "$town/government/"
python3 - "$town/government/knowledge-budget.conf" <<'PY'
import json,sys
p=sys.argv[1]
c=json.load(open(p))
c["offices"]["statistics"]["enabled"]=True
open(p,"w").write(json.dumps(c))
PY
export VICHE_TOWN_ROOT="$town" VICHE_STATE_ROOT="$state"
python3 - "$town/government/statistics-bounded-trial.py" "$state" <<'PY'
import sys,importlib.util,json,time
from pathlib import Path
spec=importlib.util.spec_from_file_location("test_budget",sys.argv[1])
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
root=Path(sys.argv[2])/"knowledge/budget"
a=m.reserve("2026-11-01")
assert a is not None and m.reserve("2026-11-01") is None
row=json.loads(a.read_text())
assert row["state"]=="held" and row["charge"]==m.VOLUME
assert row["agent_id"]=="" and row["model_requests"]==0
# 7 uncertain/failed per-day attempts pessimistically charge 7*256
# host-CPU seconds. An 8th exceeds Statistics' 1800 cap.
for i in range(2,8):
 assert m.reserve("2026-11-%02d"%i) is not None
assert len(list(root.glob("reservations/*.json")))==7
try:
 m.reserve("2026-11-08")
except m.Denied as e:
 assert "Statistics cpu_seconds hard allowance exhausted" in str(e),str(e)
else:
 raise AssertionError("cumulative 160*12 > 1800 cap allowed")
agg=json.loads((root/"aggregate.json").read_text())
assert agg["by_office"]["statistics"]["cpu_seconds"]==7*256
assert agg["tokens_total"]==0
# No bypass by a corrupt aggregate: fail closed before any next reservation.
original_aggregate=(root/"aggregate.json").read_text()
(root/"aggregate.json").write_text("BROKEN")
try:
 m.reserve("2026-11-09")
except m.Denied:
 pass
else:
 raise AssertionError("corrupt budget accepted")
assert not (root/"reservations/det-statistics-2026-11-09.json").exists()
# The real engine intentionally will NOT heal a corrupt aggregate blindly.
# This isolated fixture restores the exact previously trusted bytes before
# verifying the independent, ordinary crash reconciliation path.
(root/"aggregate.json").write_text(original_aggregate)
PY
# Reboot-style reconciliation of an uncertain held charge cannot silently
# release it or erase its full pessimistic liability.
if ! /bin/sh "$town/government/knowledge-budget.sh" reconcile >/dev/null 2>&1; then
  echo 'FAIL: canonical budget engine could not reconcile held deterministic charges' >&2
  exit 1
fi
python3 - "$state" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1])/"knowledge/budget/aggregate.json"
a=json.loads(p.read_text())
assert a["by_office"]["statistics"]["cpu_seconds"]==1792
assert len(a["counted"])==7
PY
echo 'Statistics cumulative hard budget: 7 full holds precharged, 8th refused, corrupt aggregate fails, reboot retains debt'

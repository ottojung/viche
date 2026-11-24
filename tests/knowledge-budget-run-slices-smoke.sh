#!/bin/sh
# Act34 liveness: 45-day office allowance is NOT a one-session allowance.
# Real Economy shell guard + reserve, genuine DB, host-CPU baseline,
# durable receipts, cumulative liabilities and provider-overrun fail closed.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
town="$tmp/town"
state="$tmp/state"
mkdir -p "$town/government" "$state/knowledge/budget/reservations"
tool="$repo/government/knowledge-budget-tool.py"
engine="$repo/government/knowledge-budget.sh"
cp "$repo/government/knowledge-budget.conf" "$town/government/"
python3 - "$town/government/knowledge-budget.conf" "$tmp/meter.db" <<'PY'
import json,sqlite3,sys
from pathlib import Path
p=Path(sys.argv[1])
c=json.loads(p.read_text())
c["metering"]["opencode_db"]=sys.argv[2]
c["offices"]["statistics"]["enabled"]=True
for office in c["offices"].values():
    office["caps"]={"tokens_total":400000,"cpu_seconds":1800,"wall_seconds":3600}
    office.pop("per_run_caps",None)
c["aggregate"]["caps"]={"tokens_total":1600000,"cpu_seconds":7200,"wall_seconds":14400}
c["offices"]["statistics"]["per_run_caps"]={
    "tokens_total":120000, "cpu_seconds":400,"wall_seconds":600}
p.write_text(json.dumps(c))
db=sqlite3.connect(sys.argv[2])
db.execute("create table session_v2 (id text primary key,tokens_input int,tokens_output int,tokens_reasoning int,tokens_cache_read int,tokens_cache_write int,cost real,time_updated int)")
db.execute("insert into session_v2 values ('fixture',1,1,0,0,0,0,1790000000000)")
db.commit()
PY
export VICHE_TOWN_ROOT="$town" VICHE_STATE_ROOT="$state"
export VICHE_BUDGET_TOOL="$tool"
cfg="$town/government/knowledge-budget.conf"
python3 "$tool" validate "$cfg" | jq -e '.ok==true' >/dev/null
/bin/sh "$engine" guard statistics >/dev/null
first=$(/bin/sh "$engine" reserve statistics agent-first)
root="$state/knowledge/budget"
jq -e '.caps.tokens_total==120000 and .caps.cpu_seconds==400 and
       .caps.wall_seconds==600 and .state=="reserved"' \
  "$root/reservations/$first.json" >/dev/null
# First session used a tenth of its allowance. The remaining 45-day
# cumulative budget must admit another full 120k slice instead of deadlocking.
python3 - "$root/reservations/$first.json" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1])
a=json.loads(p.read_text())
a["state"]="closed"
a["usage"]={"tokens_total":10000,"cpu_seconds":3,"wall_seconds":12}
a["charge"]=None
p.write_text(json.dumps(a))
PY
now=$(date +%s)
python3 "$tool" aggregate "$root/reservations" 3888000 "$now" >"$root/aggregate.json"
/bin/sh "$engine" guard statistics >/dev/null
second=$(/bin/sh "$engine" reserve statistics agent-second)
[ "$first" != "$second" ] || { echo "FAIL: repeated reservation id" >&2; exit 1; }
jq -e '.caps.tokens_total==120000 and .state=="reserved"' \
  "$root/reservations/$second.json" >/dev/null
python3 "$tool" aggregate "$root/reservations" 3888000 "$(date +%s)" |
  jq -e '.tokens_total==130000 and
         .by_office.statistics.tokens_total==130000' >/dev/null
# An in-flight request may overrun the slice. Its ACTUAL cost is charged;
# another full slice then cannot erase the excess or exceed cumulative cap.
python3 - "$root/reservations/$first.json" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1])
a=json.loads(p.read_text())
a["usage"]["tokens_total"]=310000
p.write_text(json.dumps(a))
PY
python3 "$tool" aggregate "$root/reservations" 3888000 "$(date +%s)" >"$root/aggregate.json"
if python3 "$tool" admit "$cfg" "$(cat "$root/aggregate.json")" statistics |
      jq -e '.admit==true' >/dev/null; then
  echo 'FAIL: overrun beyond cumulative cap admitted' >&2
  exit 1
fi
# Optional per-run caps must themselves be valid and <= 45d office caps.
python3 - "$cfg" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);c=json.loads(p.read_text())
c["offices"]["statistics"]["per_run_caps"]["tokens_total"]=400001
p.write_text(json.dumps(c))
PY
if python3 "$tool" validate "$cfg" >/dev/null 2>&1; then
  echo 'FAIL: per-run cap larger than 45d allowance validated' >&2; exit 1
fi
echo 'PASS: multiple Act34 model sessions use per-run 120k slices; real Economy guard, usage and cumulative 45d liability enforce overrun'

#!/bin/sh
# Act 32 / Founder 2026-11-22 order: rigorous NEGATIVE tests for the Economy
# whole-host CPU UPPER_BOUND accounting. Isolated temp fixture only; no live
# state, no activation, no cap change. Tests pure functions deterministically.
set -eu
cd "$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)"
TOOL=$(pwd -P)/government/knowledge-budget-tool.py
ENGINE=$(pwd -P)/government/knowledge-budget.sh
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM

fail() { echo "FAIL: $*" >&2; exit 1; }
no()  { if "$@" >/dev/null 2>&1; then fail "$* unexpectedly succeeded"; fi; }
ok()  { "$@" >/dev/null || fail "$* failed"; }

BOSS="conservative-whole-host-upper-bound"
SRC="proc-stat-host-busy-upper-bound-v1"
NOW=$(date +%s)

mkcpu() { # bootid, absolute_seconds
  python3 -c 'import json,sys; print(json.dumps({"cpu_boot_id":sys.argv[1],"cpu_seconds":float(sys.argv[2]),"cpu_source":"proc-stat-host-busy-upper-bound-v1","cpu_available":True,"cpu_attribution":"conservative-whole-host-upper-bound"}))' "$1" "$2"
}
mksnap() { # bootid, abs_cpu, tok_total
  python3 -c 'import json,sys; t=int(sys.argv[3]); print(json.dumps({"cpu_boot_id":sys.argv[1],"cpu_seconds":float(sys.argv[2]),"cpu_source":"proc-stat-host-busy-upper-bound-v1","cpu_available":True,"cpu_attribution":"conservative-whole-host-upper-bound","tokens":{"input":t,"output":0,"reasoning":0,"cache_read":0,"cache_write":0,"total":t},"session_found":True,"session_id":"sid"}))' "$1" "$2" "$3"
}

echo '--- T1: CPU delta is a monotone whole-host delta, tagged UPPER_BOUND ---'
B=$(mkcpu boot-A 1000.0); C=$(mksnap boot-A 1180.5 500)
R=$(python3 "$TOOL" cpu-delta "$B" "$C") || fail 'cpu-delta failed'
D=$(printf '%s\n' "$R" | jq -r '.cpu_seconds')
[ "$D" = "180.5" ] || fail "cpu delta wrong: $D"
printf '%s\n' "$R" | jq -e '.cpu_upper_bound==true and .cpu_host_seconds==1180.5 and .token_accounting=="absolute-session-total-upper-bound" and .tokens.delta_total==500' >/dev/null || fail 'upper-bound tagging missing'
echo 'T1 ok'

echo '--- T2: reboot mid-trial fails closed (boot id change) ---'
no python3 "$TOOL" cpu-delta "$B" "$(mksnap boot-B 1200 500)"
echo 'T2 ok'

echo '--- T3: CPU counter regression fails closed ---'
no python3 "$TOOL" cpu-delta "$B" "$(mksnap boot-A 900 500)"
echo 'T3 ok'

echo '--- T4: successive trials ACCUMULATE deltas, CPU not reset by trial ---'
# Build two closed reservations with known per-trial cpu deltas + tokens + wall.
mkdir -p "$d/res"
python3 - "$d/res" "$NOW" <<'PY'
import json,sys,pathlib
res=pathlib.Path(sys.argv[1]); now=int(sys.argv[2])
def row(rid,created,cpu,tok,wall):
    return {"schema":"viche-knowledge-budget-reservation-v1","id":rid,"office":"statistics",
      "state":"closed","created_at":created,"caps":{"tokens_total":400000,"cpu_seconds":1800,"wall_seconds":3600},
      "usage":{"tokens_total":tok,"cpu_seconds":cpu,"wall_seconds":wall,"source":"opencode-service-session-v2",
               "cost":0.0,"cost_reported":False,"at":now,"cpu_upper_bound":True}}
(res/'r1.json').write_text(json.dumps(row('r1',now-100000,180.5,500,600)))
(res/'r2.json').write_text(json.dumps(row('r2',now-50000,220.25,700,900)))
PY
AGG=$(python3 "$TOOL" aggregate "$d/res" 3888000 "$NOW") || fail 'aggregate failed'
[ "$(printf '%s\n' "$AGG" | jq -r '.cpu_seconds')" = "400.75" ] || fail "cpu not accumulated: $(printf '%s\n' "$AGG" | jq -r '.cpu_seconds')"
[ "$(printf '%s\n' "$AGG" | jq -r '.tokens_total')" = "1200" ] || fail 'tokens not accumulated'
[ "$(printf '%s\n' "$AGG" | jq -r '.wall_seconds')" = "1500" ] || fail 'wall not accumulated'
echo 'T4 ok'

echo '--- T5: 45d window DROPS aged closed charges (liability expiry, documented) ---'
AGG2=$(python3 "$TOOL" aggregate "$d/res" 60 "$NOW") || fail 'aggregate(window=60) failed'
# r1 created 100000s ago, r2 50000s ago; window=60 -> both drop
printf '%s\n' "$AGG2" | jq -e '.cpu_seconds == 0' >/dev/null || fail "aged charges not expired: $(printf '%s\n' "$AGG2" | jq -r '.cpu_seconds')"
AGG3=$(python3 "$TOOL" aggregate "$d/res" 75000 "$NOW") || fail 'aggregate(window=75000) failed'
# only r1 (100000s ago) drops; r2 (50000s ago) stays -> 220.25
printf '%s\n' "$AGG3" | jq -e '.cpu_seconds == 220.25' >/dev/null || fail "window partial expiry wrong: $(printf '%s\n' "$AGG3" | jq -r '.cpu_seconds')"
echo 'T5 ok (window=45d >> 14d trial, so within Act life trials accumulate)'

echo '--- T6: concurrent active reservations each charge full-host CPU (conservative overcount, never undercount) ---'
python3 - "$d/res" "$NOW" <<'PY'
import json,sys,pathlib
res=pathlib.Path(sys.argv[1]); now=int(sys.argv[2])
for rid in ('a1','a2'):
    (res/(rid+'.json')).write_text(json.dumps({"schema":"viche-knowledge-budget-reservation-v1","id":rid,"office":"statistics",
      "state":"active","created_at":now-10,"caps":{"tokens_total":400000,"cpu_seconds":1800,"wall_seconds":3600}}))
PY
AGG4=$(python3 "$TOOL" aggregate "$d/res" 3888000 "$NOW") || fail 'aggregate(active) failed'
# active reservations charge their CAPS (not zero): 2*1800 cpu + closed 400.75
[ "$(printf '%s\n' "$AGG4" | jq -r '.cpu_seconds')" = "4000.75" ] || fail "active cap charge wrong: $(printf '%s\n' "$AGG4" | jq -r '.cpu_seconds')"
echo 'T6 ok (caps charged for active => conservative, no undercount)'

echo '--- T7: session reset / counter decrease fails closed ---'
BASE=$(mksnap boot-A 1000 500)
python3 "$TOOL" delta "$BASE" "$(mksnap boot-A 1000 400)" >/dev/null 2>&1 && fail 'token reset accepted'
python3 "$TOOL" delta "$BASE" "$(mksnap boot-A 1000 600)" >/dev/null 2>&1 || fail 'monotone token delta failed'
echo 'T7 ok'

echo '--- T8: disabled config cannot transition to enabled by guard/reserve ---'
mkdir -p "$d/town/government" "$d/state/knowledge/budget/reservations"
cp "$(pwd -P)/government/knowledge-budget.conf" "$d/town/government/"
cp "$(pwd -P)/government/knowledge-budget.sh" "$d/town/government/"
cp "$(pwd -P)/government/knowledge-budget-tool.py" "$d/town/government/"
export VICHE_TOWN_ROOT="$d/town" VICHE_STATE_ROOT="$d/state" VICHE_BUDGET_TOOL="$d/town/government/knowledge-budget-tool.py"
# Shipped config: all disabled. guard/reserve must refuse.
no /bin/sh "$ENGINE" guard statistics
no /bin/sh "$ENGINE" reserve statistics agent
# Only a lawful source-config edit (enabled=true) permits guard; engine self-certification cannot.
python3 - "$d/town/government/knowledge-budget.conf" <<'PY'
import json,sys
p=sys.argv[1]; c=json.load(open(p)); c['offices']['statistics']['enabled']=True; c['metering']['opencode_db']='/nonexistent.db'; json.dump(c,open(p,'w'))
PY
# With meter absent, still fails closed (no unmeasured budget claimed).
no /bin/sh "$ENGINE" guard statistics
echo 'T8 ok (disabled default + no-meter fail-closed; enable is a lawful source edit outside Economy)'

echo '--- T9: cap feasibility is an OBSERVATION, not a cap change ---'
python3 -c 'print("per-office cpu cap 1800s; 4-CPU host; measured busy rate 0.49-3.17 CPUs => cap exhausted in 9.5-61 min wall; NO CAP CHANGE without lawful Act")'

echo 'ALL NEGATIVE TESTS PASSED'

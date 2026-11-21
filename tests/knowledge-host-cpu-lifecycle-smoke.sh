#!/bin/sh
set -eu
cd "$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)"
town=$(pwd -P)
engine=$town/government/knowledge-budget.sh
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
mkdir -p "$tmp/fixture/government" "$tmp/state" "$tmp/bin"
cp government/knowledge-budget.conf "$tmp/fixture/government/"
db=$tmp/meter.sqlite3
python3 - "$db" "$tmp/fixture/government/knowledge-budget.conf" <<'PY'
import json,sqlite3,sys
db,conf=sys.argv[1:]
con=sqlite3.connect(db)
con.execute('create table session_v2 (id text primary key,tokens_input int,tokens_output int,tokens_reasoning int,tokens_cache_read int,tokens_cache_write int,cost real,time_updated int)')
con.execute("insert into session_v2 values ('sid',100,0,0,0,0,0.0,1795279700000)")
con.commit()
x=json.load(open(conf))
x['metering']['opencode_db']=db
x['monitor_interval_seconds']=1
x['offices']['statistics']['enabled']=True
x['offices']['statistics']['caps']['tokens_total']=150
json.dump(x,open(conf,'w'))
PY
cat > "$tmp/bin/antonina" <<'SH'
#!/bin/sh
case "$1 $2" in
  'agent status') cat "$TEST_AGENT_STATE" ;;
  'agent kill')
    printf '%s\n' "$*" >> "$TEST_AGENT_KILLS"
    if [ "$TEST_KILL_FAIL" = yes ]; then exit 1; fi
    printf '{"state":"clearexit","native_session_id":"sid"}\n' > "$TEST_AGENT_STATE"
    ;;
  'agent stop') : ;;
  *) exit 17 ;;
esac
SH
chmod +x "$tmp/bin/antonina"
export VICHE_TOWN_ROOT="$tmp/fixture" VICHE_STATE_ROOT="$tmp/state"
export VICHE_BUDGET_TOOL="$town/government/knowledge-budget-tool.py"
export TEST_AGENT_STATE="$tmp/agent.json" TEST_AGENT_KILLS="$tmp/kills.log"
export TEST_KILL_FAIL=no
export PATH="$tmp/bin:$PATH"
printf '{"state":"running","native_session_id":"sid"}\n' > "$TEST_AGENT_STATE"
r=$(/bin/sh "$engine" reserve statistics test-agent)
case "$r" in *'
'*|'{'*) echo "Reservation output contaminated: $r" >&2; exit 1 ;; esac
/bin/sh "$engine" mark-dispatched "$r"
result=$(/bin/sh "$engine" start "$r" test-agent)
[ "$result" = "active $r" ] || { echo "start failed: $result" >&2; exit 1; }
python3 - "$db" <<'PY'
import sqlite3,sys
con=sqlite3.connect(sys.argv[1])
con.execute("update session_v2 set tokens_input=185,time_updated=1795279800000 where id='sid'")
con.commit()
PY
reached=no
for attempt in 1 2 3 4 5 6 7 8; do
  state=$(jq -r '.state' "$tmp/state/knowledge/budget/reservations/$r.json")
  if [ "$state" = closed ]; then reached=yes; break; fi
  sleep 1
done
[ "$reached" = yes ] || { echo "Overrun monitor did not close after kill" >&2; exit 1; }
grep -q 'agent kill' "$TEST_AGENT_KILLS"
jq -e '.state=="closed" and .meter.cpu_upper_bound==true and
       .meter.token_accounting=="absolute-session-total-upper-bound" and
       .usage.tokens_total>=185 and .usage.cpu_seconds>=0 and
       (.closed_reason|startswith("overrun_tokens_total"))' \
  "$tmp/state/knowledge/budget/reservations/$r.json" >/dev/null || {
  echo 'Measured token overrun was not durably accounted' >&2; exit 1;
}
# A kill command that exits nonzero or leaves the backend running must
# NEVER release the cap. Stop verification is independent of kill invocation.
export TEST_KILL_FAIL=yes
printf '{"state":"running","native_session_id":"sid"}\n' > "$TEST_AGENT_STATE"
r2=$(/bin/sh "$engine" reserve statistics test-agent-2)
[ -n "$r2" ] || exit 1
/bin/sh "$engine" mark-dispatched "$r2"
/bin/sh "$engine" start "$r2" test-agent-2 >/dev/null
held=no
for attempt in 1 2 3 4 5 6 7 8; do
  state=$(jq -r '.state' "$tmp/state/knowledge/budget/reservations/$r2.json")
  if [ "$state" = held ]; then held=yes; break; fi
  sleep 1
done
[ "$held" = yes ] || { echo 'Failed termination released or stranded reservation' >&2; exit 1; }
jq -e '.state=="held" and .charge.tokens_total==150 and
        .held_reason=="agent_still_active_or_unknown_after_stop"' \
        "$tmp/state/knowledge/budget/reservations/$r2.json" >/dev/null || {
  echo 'Failed stop did not retain full reservation' >&2; exit 1;
}
if /bin/sh "$engine" reserve statistics agent-3 >/dev/null 2>&1; then
  echo 'Another agent was admitted over still-running held session' >&2; exit 1
fi
echo 'whole-host CPU and tokens: active overrun, verified stop, failed-kill hold and no replay passed'

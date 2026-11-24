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
  'agent status')
    if [ -n "${TEST_DELAY_CALLS:-}" ]; then
      _n=$(cat "$TEST_DELAY_COUNT" 2>/dev/null || printf '0\n')
      _n=$((_n + 1))
      printf '%s\n' "$_n" > "$TEST_DELAY_COUNT"
      if [ "$_n" -le "$TEST_DELAY_CALLS" ]; then
        printf '{"state":"starting","native_session_id":null}\n'
        exit 0
      fi
    fi
    cat "$TEST_AGENT_STATE"
    ;;
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
# The first agent exceeded its per-office 150-token allowance. Even though
# the aggregate budget still has room, repeat office reservations in this
# SAME accounting window MUST now be refused (cumulative office liability).
if /bin/sh "$engine" reserve statistics too-many >/dev/null 2>&1; then
  echo 'FAIL: spent office quota was silently reset by a new reservation' >&2
  exit 1
fi
# Test the separate kill-failure outcome under a FRESH isolated budget
# fixture. Do not delete or reset the first fixture's source-attested debit.
# An ordinary production office must not restart until Economy allocates more.
export VICHE_STATE_ROOT="$tmp/state-second"
mkdir -p "$VICHE_STATE_ROOT"
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
  state=$(jq -r '.state' "$VICHE_STATE_ROOT/knowledge/budget/reservations/$r2.json")
  if [ "$state" = held ]; then held=yes; break; fi
  sleep 1
done
[ "$held" = yes ] || { echo 'Failed termination released or stranded reservation' >&2; exit 1; }
jq -e '.state=="held" and .charge.tokens_total==150 and
        .held_reason=="agent_still_active_or_unknown_after_stop"' \
        "$VICHE_STATE_ROOT/knowledge/budget/reservations/$r2.json" >/dev/null || {
  echo 'Failed stop did not retain full reservation' >&2; exit 1;
}
if /bin/sh "$engine" reserve statistics agent-3 >/dev/null 2>&1; then
  echo 'Another agent was admitted over still-running held session' >&2; exit 1
fi

# Delayed native-session binding: `antonina agent run --detach` acknowledges
# only the runner claim; the native session id and its meter row appear on a
# later status poll. The bounded pre-lock wait must let this legitimate
# starting runner bind instead of killing it and consuming the whole
# reservation. Full liability stays charged at caps until binding is verified,
# and the wall deadline is NOT pushed out by the wait.
export TEST_KILL_FAIL=no
python3 - "$db" <<'PY'
import sqlite3,sys
con=sqlite3.connect(sys.argv[1])
con.execute("update session_v2 set tokens_input=100,time_updated=1795279850000 where id='sid'")
con.commit()
PY
# One monitor interval here is 5s; still far below the 3600s wall cap.
python3 - "$tmp/fixture/government/knowledge-budget.conf" <<'PY'
import json,sys
p=sys.argv[1]; c=json.load(open(p)); c['monitor_interval_seconds']=5; json.dump(c,open(p,'w'))
PY
export VICHE_STATE_ROOT="$tmp/state-delayed"
mkdir -p "$VICHE_STATE_ROOT"
export TEST_DELAY_CALLS=2
export TEST_DELAY_COUNT="$tmp/delay-count-delayed"
: > "$TEST_DELAY_COUNT"
printf '{"state":"running","native_session_id":"sid"}\n' > "$TEST_AGENT_STATE"
export TEST_AGENT_KILLS="$tmp/kills-delayed"
: > "$TEST_AGENT_KILLS"
r3=$(/bin/sh "$engine" reserve statistics delayed-agent)
/bin/sh "$engine" mark-dispatched "$r3"
result3=$(/bin/sh "$engine" start "$r3" delayed-agent)
[ "$result3" = "active $r3" ] || { echo "delayed-binding start failed: $result3" >&2; exit 1; }
[ ! -s "$TEST_AGENT_KILLS" ] || { echo 'Starting runner was killed during binding wait' >&2; exit 1; }
jq -e '.state=="active" and .native_session_id=="sid" and .agent_id=="delayed-agent" and
        .expires_at==(.created_at + .caps.wall_seconds)' \
  "$VICHE_STATE_ROOT/knowledge/budget/reservations/$r3.json" >/dev/null || {
  echo 'Delayed binding did not activate with conservative creation-based expiry' >&2; exit 1; }
python3 "$town/government/knowledge-budget-tool.py" aggregate \
  "$VICHE_STATE_ROOT/knowledge/budget/reservations" 3888000 "$(date +%s)" |
  jq -e '.tokens_total==150 and .by_office.statistics.tokens_total==150' >/dev/null || {
  echo 'Full per-run liability was not retained through binding' >&2; exit 1; }
unset TEST_DELAY_CALLS

# Missing native session (delay never resolves) still fails closed: the runner
# is stopped and the full cap is held, never activated on an unknown binding.
python3 - "$tmp/fixture/government/knowledge-budget.conf" <<'PY'
import json,sys
p=sys.argv[1]; c=json.load(open(p)); c['monitor_interval_seconds']=2; json.dump(c,open(p,'w'))
PY
export VICHE_STATE_ROOT="$tmp/state-missing"
mkdir -p "$VICHE_STATE_ROOT"
export TEST_DELAY_CALLS=999
export TEST_DELAY_COUNT="$tmp/delay-count-missing"
: > "$TEST_DELAY_COUNT"
printf '{"state":"running","native_session_id":"sid"}\n' > "$TEST_AGENT_STATE"
export TEST_AGENT_KILLS="$tmp/kills-missing"
: > "$TEST_AGENT_KILLS"
r4=$(/bin/sh "$engine" reserve statistics unbound-agent)
/bin/sh "$engine" mark-dispatched "$r4"
if /bin/sh "$engine" start "$r4" unbound-agent >/dev/null 2>&1; then
  echo 'FAIL: missing native-session binding was accepted' >&2; exit 1
fi
jq -e '.state=="held" and .charge.tokens_total==150 and
        .held_reason=="meter_or_session_binding_unknown_after_launch"' \
  "$VICHE_STATE_ROOT/knowledge/budget/reservations/$r4.json" >/dev/null || {
  echo 'Missing binding did not hold at full cap' >&2; exit 1; }
grep -q 'agent kill' "$TEST_AGENT_KILLS" || {
  echo 'Missing binding did not stop the runner' >&2; exit 1; }

# Unknown meter (sid present but no authoritative meter row) also fails closed.
unset TEST_DELAY_CALLS
export VICHE_STATE_ROOT="$tmp/state-unmetered"
mkdir -p "$VICHE_STATE_ROOT"
printf '{"state":"running","native_session_id":"absent-session"}\n' > "$TEST_AGENT_STATE"
export TEST_AGENT_KILLS="$tmp/kills-unmetered"
: > "$TEST_AGENT_KILLS"
r5=$(/bin/sh "$engine" reserve statistics unmetered-agent)
/bin/sh "$engine" mark-dispatched "$r5"
if /bin/sh "$engine" start "$r5" unmetered-agent >/dev/null 2>&1; then
  echo 'FAIL: unmetered native session was accepted' >&2; exit 1
fi
jq -e '.state=="held" and .charge.tokens_total==150 and
        .held_reason=="meter_or_session_binding_unknown_after_launch"' \
  "$VICHE_STATE_ROOT/knowledge/budget/reservations/$r5.json" >/dev/null || {
  echo 'Unknown meter did not hold at full cap' >&2; exit 1; }
echo 'whole-host CPU and tokens: active overrun, verified stop, failed-kill hold, delayed binding, missing/unknown fail-closed and no replay passed'

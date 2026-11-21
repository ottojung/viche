#!/bin/sh
# Act 32 H adversarial black-box tests: host busy CPU is a conservative
# upper bound, NOT per-session attribution; reset/unreadable must fail closed.
set -eu
cd "$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)"
TOOL=$(pwd -P)/government/knowledge-budget-tool.py
ENGINE=$(pwd -P)/government/knowledge-budget.sh
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
mkdir -p "$d/state/knowledge/budget/reservations" "$d/town/government"
cp government/knowledge-budget.conf "$d/town/government/"
export VICHE_TOWN_ROOT="$d/town" VICHE_STATE_ROOT="$d/state" VICHE_BUDGET_TOOL="$TOOL"

fail() { echo "FAIL: $*" >&2; exit 1; }
no() { if "$@" >/dev/null 2>&1; then fail "$* unexpectedly succeeded"; fi; }
ok() { "$@" >/dev/null || fail "$* failed"; }

DB=$d/meter.db
python3 - "$DB" <<'PY'
import sqlite3,sys
c=sqlite3.connect(sys.argv[1])
c.execute("create table session_v2 (id text primary key,tokens_input int,tokens_output int,tokens_reasoning int,tokens_cache_read int,tokens_cache_write int,cost real,time_updated int)")
c.execute("insert into session_v2 values ('sid',100,20,3,40,5,0.0,1795197102261)")
c.commit()
PY
python3 - "$d/town/government/knowledge-budget.conf" "$DB" <<'PY'
import json,sys
p=sys.argv[1]; c=json.load(open(p)); c['metering']['opencode_db']=sys.argv[2]
for x in c['offices'].values(): x['enabled']=True
json.dump(c,open(p,'w'))
PY

# All shipped office activations are disabled.
jq -e '[.offices[] | .enabled] | all(. == false)' government/knowledge-budget.conf >/dev/null ||
  fail 'shipped config did not default all offices disabled'

# Valid token telemetry plus host-wide busy CPU accounting admits a
# PRELAUNCH reservation with durable CPU baseline before any agent exists.
ok /bin/sh "$ENGINE" guard statistics
rid=$(/bin/sh "$ENGINE" reserve statistics test-agent) || fail 'reservation denied'
[ -n "$rid" ] && [ -s "$d/state/knowledge/budget/reservations/$rid.json" ] ||
  fail 'prelaunch reservation missing'
jq -e '.cpu_baseline.cpu_available==true and
       .cpu_baseline.cpu_source=="proc-stat-host-busy-upper-bound-v1" and
       (.cpu_baseline.cpu_boot_id|length)>20 and
       .cpu_accounting=="whole-host-busy-upper-bound-not-per-office"' \
    "$d/state/knowledge/budget/reservations/$rid.json" >/dev/null ||
    fail 'prelaunch CPU upper-bound baseline missing'
no /bin/sh "$ENGINE" reserve statistics second-agent
# The test fixture has no launched agent, so its reservation may be removed.
rm "$d/state/knowledge/budget/reservations/$rid.json" "$d/state/knowledge/budget/aggregate.json"
ok /bin/sh "$ENGINE" guard statistics
no /bin/sh "$ENGINE" reserve statistics

# The production cycle still blocks before appointment or detached launch
# whenever token telemetry is absent. Verify the real caller ordering using
# an isolated town fixture and a recording Antonina stub.
mkdir -p "$d/cycle-town/government" "$d/cycle-town/records/knowledge" "$d/cycle-state" "$d/cycle-bin"
cp government/knowledge-budget.conf government/knowledge-budget.sh government/knowledge-budget-tool.py \
  government/knowledge-office-cycle.sh "$d/cycle-town/government/"
printf '#!/bin/sh\nexit 0\n' > "$d/cycle-town/government/knowledge-activation-verify.sh"
printf '## Act 32 — Institutional Knowledge and Communications Act (enacted test)\n' > "$d/cycle-town/government/LAWS.md"
printf 'baseline\n' > "$d/cycle-town/records/knowledge/baseline-20261119.json"
cp "$DB" "$d/cycle-meter.db"
python3 - "$d/cycle-town/government/knowledge-budget.conf" "$d/cycle-meter.db" <<'PY'
import json,sys
p=sys.argv[1]; c=json.load(open(p)); c['metering']['opencode_db']=sys.argv[2]+'.missing'; c['offices']['statistics']['enabled']=True; json.dump(c,open(p,'w'))
PY
cat > "$d/cycle-bin/antonina" <<'SH'
#!/bin/sh
echo "$*" >> "$CYCLE_LOG"
exit 0
SH
chmod +x "$d/cycle-bin/antonina"
: > "$d/cycle.log"
export CYCLE_LOG="$d/cycle.log" PATH="$d/cycle-bin:$PATH"
env VICHE_TOWN_ROOT="$d/cycle-town" VICHE_STATE_ROOT="$d/cycle-state" \
  VICHE_BUDGET_TOOL="$d/cycle-town/government/knowledge-budget-tool.py" \
  VICHE_BUDGET_DB="$d/cycle-meter.db" VICHE_CONSTITUTION=/missing \
  /bin/sh "$d/cycle-town/government/knowledge-office-cycle.sh" statistics >/dev/null 2>&1 ||
  fail 'cycle budget denial returned an error instead of safe no-dispatch'
[ ! -s "$d/cycle.log" ] || fail 'cycle reached Antonina after CPU budget guard denied activation'

# Missing SID is an error, not a successful zero-token observation.
no python3 "$TOOL" snapshot "$DB" absent-session "$$"

# Session reuse must produce a monotone delta; changed SID and counter reset fail.
BASE=$(python3 "$TOOL" snapshot "$DB" sid "$$")
python3 - "$DB" <<'PY'
import sqlite3,sys
c=sqlite3.connect(sys.argv[1]); c.execute('update session_v2 set tokens_input=125'); c.commit()
PY
CUR=$(python3 "$TOOL" snapshot "$DB" sid "$$")
DELTA=$(python3 "$TOOL" delta "$BASE" "$CUR")
[ "$(printf '%s\n' "$DELTA" | jq -r '.tokens.delta_total')" -eq 25 ] || fail 'cumulative usage delta wrong'
no python3 "$TOOL" delta "$BASE" "$(printf '%s\n' "$CUR" | jq '.session_id="other"')"
python3 - "$DB" <<'PY'
import sqlite3,sys
c=sqlite3.connect(sys.argv[1]); c.execute('update session_v2 set tokens_input=1'); c.commit()
PY
RESET=$(python3 "$TOOL" snapshot "$DB" sid "$$")
no python3 "$TOOL" delta "$CUR" "$RESET"

# Authoritative time_updated is explicitly milliseconds, never interpreted as
# seconds or as a fabricated CPU signal.
printf '%s\n' "$CUR" | jq -e '.time_updated_ms==1795197102261 and .cpu_available==true and
    .cpu_source=="proc-stat-host-busy-upper-bound-v1" and
    .cpu_attribution=="conservative-whole-host-upper-bound" and
    .cpu_seconds>0 and (.cpu_boot_id|length)>20' >/dev/null ||
  fail 'meter units/provenance are ambiguous'

# Any malformed/unknown reservation is a hard aggregate error, not skipped.
printf 'CORRUPT' > "$d/state/knowledge/budget/reservations/unknown.json"
no python3 "$TOOL" aggregate "$d/state/knowledge/budget/reservations" 3888000 "$(date +%s)"
no /bin/sh "$ENGINE" guard statistics
rm "$d/state/knowledge/budget/reservations/unknown.json"

# Unknown state and malformed committed records fail closed.
cat > "$d/state/knowledge/budget/reservations/unknown.json" <<'JSON'
{"schema":"viche-knowledge-budget-reservation-v1","id":"unknown","office":"statistics","state":"mystery","created_at":1,"caps":{"tokens_total":5,"cpu_seconds":5,"wall_seconds":5}}
JSON
no python3 "$TOOL" aggregate "$d/state/knowledge/budget/reservations" 3888000 "$(date +%s)"
rm "$d/state/knowledge/budget/reservations/unknown.json"

# Crash after durable dispatch-intent but before session binding is held at the
# full reservation; age alone must never release it. An aged reservation with
# no dispatch intent is provably prelaunch (intent is fsynced before launcher)
# and may be rolled back.
mkdir -p "$d/bin"
cat > "$d/bin/antonina" <<'SH'
#!/bin/sh
case "$1 $2" in
  'agent status') printf '{"state":"running","native_session_id":"sid"}\n' ;;
  'agent kill'|'agent stop') exit 0 ;;
  *) exit 5 ;;
esac
SH
chmod +x "$d/bin/antonina"
export PATH="$d/bin:$PATH"
NOW=$(date +%s)
jq -n --argjson now "$NOW" '{schema:"viche-knowledge-budget-reservation-v1",id:"ambiguous",office:"statistics",state:"reserved",created_at:($now-1000),caps:{tokens_total:100,cpu_seconds:10,wall_seconds:60},accounting_window_seconds:3888000,monitor_interval_seconds:1,overrun_action:"kill",meter_db:"none",agent_id:"agent-1",dispatch_attempted:true,history:[]}' > "$d/state/knowledge/budget/reservations/ambiguous.json"
ok /bin/sh "$ENGINE" reconcile
[ "$(jq -r '.state' "$d/state/knowledge/budget/reservations/ambiguous.json")" = held ] || fail 'ambiguous launch intent was released after age'
[ "$(jq -r '.charge.tokens_total' "$d/state/knowledge/budget/reservations/ambiguous.json")" -eq 100 ] || fail 'ambiguous launch lacks pessimistic charge'
no /bin/sh "$ENGINE" guard statistics
rm "$d/state/knowledge/budget/reservations/ambiguous.json"
jq -n --argjson now "$NOW" '{schema:"viche-knowledge-budget-reservation-v1",id:"prelaunch",office:"statistics",state:"reserved",created_at:($now-1000),caps:{tokens_total:100,cpu_seconds:10,wall_seconds:60},accounting_window_seconds:3888000,monitor_interval_seconds:1,overrun_action:"kill",meter_db:"none",agent_id:"agent-1",dispatch_attempted:false,history:[]}' > "$d/state/knowledge/budget/reservations/prelaunch.json"
ok /bin/sh "$ENGINE" reconcile
[ "$(jq -r '.state' "$d/state/knowledge/budget/reservations/prelaunch.json")" = rolled_back ] || fail 'provably prelaunch stale reservation not rolled back'
rm "$d/state/knowledge/budget/reservations/prelaunch.json"

# An aggregate record that is corrupt or diverges from source reservations
# prevents activation. This remains true even when there are no reservations.
printf 'not-json\n' > "$d/state/knowledge/budget/aggregate.json"
no /bin/sh "$ENGINE" guard statistics

# Missing/corrupt meter schema fails closed and never creates a reservation.
printf 'not a database' > "$d/bad.db"
python3 - "$d/town/government/knowledge-budget.conf" "$d/bad.db" <<'PY'
import json,sys
p=sys.argv[1]; c=json.load(open(p)); c['metering']['opencode_db']=sys.argv[2]; json.dump(c,open(p,'w'))
PY
no /bin/sh "$ENGINE" reserve statistics test-agent

# Durable write uses file fsync + atomic replace + parent-directory fsync.
python3 "$TOOL" durable-mkdir "$d/durable/a/b" >/dev/null
printf 'old' | python3 "$TOOL" durable-write "$d/durable/a/file" >/dev/null
printf 'new' | python3 "$TOOL" durable-write "$d/durable/a/file" >/dev/null
[ "$(cat "$d/durable/a/file")" = new ] || fail 'durable replacement mismatch'

# Config activation validates before replacing; rollback restores exact bytes.
rm -f "$d/state/knowledge/budget/aggregate.json"
ok /bin/sh "$ENGINE" config activate
H1=$(sha256sum "$d/state/knowledge/budget/config.active.json" | awk '{print $1}')
python3 - "$d/town/government/knowledge-budget.conf" <<'PY'
import json,sys
p=sys.argv[1]; c=json.load(open(p)); c['aggregate']['caps']['tokens_total']+=1; json.dump(c,open(p,'w'))
PY
ok /bin/sh "$ENGINE" config activate
ok /bin/sh "$ENGINE" config rollback
H2=$(sha256sum "$d/state/knowledge/budget/config.active.json" | awk '{print $1}')
[ "$H1" = "$H2" ] || fail 'rollback was not byte-exact'

echo 'knowledge budget: disabled defaults; host CPU reservations, missing SID, corruption, cumulative deltas, durability and rollback verified'

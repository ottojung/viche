#!/bin/sh
# Act 32 amendment H: black-box tests for the metered budget engine.
# Hermetic: temp town/state/DB and a stub antonina; no production state, no real
# agent is ever signalled. Covers default-disabled, missing meter, race,
# crash-after-reserve, corrupt meter, overrun with a live agent, restart,
# expiry, exact config rollback, and the cycle integration gate.
set -eu
cd "$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)"
REPO=$(pwd -P)
ENGINE=$REPO/government/knowledge-budget.sh
TOOL=$REPO/government/knowledge-budget-tool.py

d=$(mktemp -d)
cleanup() {
  for f in "$d"/state/*/knowledge/budget/reservations/*.json; do
    [ -s "$f" ] || continue
    p=$(jq -r '.monitor_pid // ""' "$f" 2>/dev/null || :)
    [ -z "$p" ] || kill "$p" 2>/dev/null || :
  done
  rm -rf "$d"
}
trap 'cleanup' EXIT HUP INT TERM

eng() { /bin/sh "$ENGINE" "$@"; }
fail() { echo "FAIL: $*" >&2; exit 1; }
ok() { if "$@" >/dev/null 2>&1; then :; else fail "$* (expected success)"; fi; }
no() { if "$@" >/dev/null 2>&1; then fail "$* (expected failure)"; else :; fi; }

newcase() {
  CASE=$1
  STATE=$d/state/$CASE
  TOWN=$d/town/$CASE
  BIN=$d/bin/$CASE
  mkdir -p "$STATE" "$TOWN/government" "$BIN"
  cp "$REPO/government/knowledge-budget.conf" "$TOWN/government/"
  export VICHE_TOWN_ROOT="$TOWN" VICHE_STATE_ROOT="$STATE" VICHE_BUDGET_TOOL="$TOOL"
  export PATH="$BIN:$PATH"
  STUB_STATUS=$d/status-$CASE
  STUB_KILL_LOG=$d/kill-$CASE.log
  STUB_RUN_LOG=$d/run-$CASE.log
  : > "$STUB_KILL_LOG"; : > "$STUB_RUN_LOG"
  export STUB_STATUS STUB_KILL_LOG STUB_RUN_LOG
  cat > "$BIN/antonina" <<'SH'
#!/bin/sh
case "$1 $2" in
  'agent status') cat "$STUB_STATUS" ;;
  'agent stop')   echo "stop $4" >> "$STUB_KILL_LOG" ;;
  'agent kill')   echo "kill $4" >> "$STUB_KILL_LOG" ;;
  'agent run')    echo "run $4" >> "$STUB_RUN_LOG" ;;
  *) exit 5 ;;
esac
SH
  chmod +x "$BIN/antonina"
  DB=$d/meter-$CASE.db
  mkdb "$DB"
  # Defaults: all four enabled for scenario setup (S1 checks the shipped file
  # separately), generous caps, fast monitor tick.
  setcfg "$DB" 'offices.statistics.enabled=true,offices.foresight.enabled=true,offices.strategy.enabled=true,offices.spying.enabled=true'
  status_running
}

status_running() { printf '{"state":"running","native_session_id":"sess-1","runner_pid":%s}\n' "$$" > "$STUB_STATUS"; }
status_terminal() { printf '{"state":"clearexit","native_session_id":"sess-1","runner_pid":%s}\n' "$$" > "$STUB_STATUS"; }
status_unknown() { printf '{"state":"unknown","native_session_id":"sess-1","runner_pid":%s}\n' "$$" > "$STUB_STATUS"; }

mkdb() {
  python3 - "$1" <<'PY'
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
c.execute("create table session_v2 (id text primary key, tokens_input int, tokens_output int, "
          "tokens_reasoning int, tokens_cache_read int, tokens_cache_write int, cost real, time_updated int)")
c.execute("insert into session_v2 values ('sess-1', 1, 0, 0, 0, 0, 0.0, 1)")
c.commit()
PY
}

settokens() {
  python3 - "$1" "$2" <<'PY'
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
c.execute("update session_v2 set tokens_input=?", (int(sys.argv[2]),))
c.commit()
PY
}

setcfg() {
  _s_db=$1; _s_ov=${2:-}
  python3 - "$TOWN/government/knowledge-budget.conf" "$_s_db" "$_s_ov" <<'PY'
import json, sys
path, db, overrides = sys.argv[1], sys.argv[2], sys.argv[3]
cfg = json.load(open(path))
cfg["metering"]["opencode_db"] = db
cfg["monitor_interval_seconds"] = 1
for pair in filter(None, overrides.split(",")):
    key, value = pair.split("=", 1)
    cur = cfg
    parts = key.split(".")
    for part in parts[:-1]:
        cur = cur[int(part)] if part.isdigit() else cur[part]
    if value.lower() in ("true", "false"):
        val = value.lower() == "true"
    elif value.startswith("{"):
        val = json.loads(value)
    elif value.lstrip("-").isdigit():
        val = int(value)
    else:
        val = value
    cur[parts[-1]] = val
json.dump(cfg, open(path, "w"))
PY
}

resdir() { printf '%s\n' "$STATE/knowledge/budget/reservations"; }
resjson() { cat "$(resdir)/$1.json"; }
rstate() { resjson "$1" | jq -r '.state'; }
allids() { for f in "$(resdir)"/*.json; do [ -s "$f" ] || continue; jq -r '.id' "$f"; done; }
waitstate() {
  _w_id=$1; _w_want=$2; _w_n=${3:-40}
  while [ "$_w_n" -gt 0 ]; do
    [ "$(rstate "$_w_id")" = "$_w_want" ] && return 0
    sleep 0.25; _w_n=$((_w_n - 1))
  done
  fail "reservation $_w_id did not reach $_w_want"
}

# ---- S1: shipped default is all four offices DISABLED ------------------------
newcase s1
cp "$REPO/government/knowledge-budget.conf" "$TOWN/government/knowledge-budget.conf"
setcfg_default_check=$(jq -e '[.offices[] | .enabled] | all(. == false)' "$TOWN/government/knowledge-budget.conf") ||
  fail 'shipped config does not default all four offices to disabled'
no eng guard statistics
no eng reserve statistics
no eng reserve spying
[ -z "$(allids)" ] || fail 'disabled offices still created a reservation'

# ---- S2: token metering unavailable => fail closed, no invented token budget -
newcase s2
setcfg /nonexistent/opencode.db 'offices.statistics.enabled=true'
no eng guard statistics
no eng reserve statistics
[ -z "$(allids)" ] || fail 'reservation created without an authoritative meter'
mkdir -p "$d/corrupt-$CASE"
setcfg "$d/corrupt-$CASE" 'offices.statistics.enabled=true'
no eng reserve statistics
[ -z "$(allids)" ] || fail 'reservation created with a corrupt meter'

# ---- S3: concurrency (same-office race and aggregate cap) --------------------
newcase s3
setcfg "$DB" 'offices.statistics.enabled=true,offices.foresight.enabled=true,offices.strategy.enabled=true,offices.spying.enabled=true,aggregate.caps.tokens_total=250,offices.statistics.caps.tokens_total=100,offices.foresight.caps.tokens_total=100,offices.strategy.caps.tokens_total=100,offices.spying.caps.tokens_total=100'
i=0
while [ "$i" -lt 8 ]; do
  ( eng reserve statistics > "$d/race-$i.out" 2> "$d/race-$i.err"; echo $? > "$d/race-$i.rc" ) &
  i=$((i + 1))
done
wait
wins=$(grep -l '^0$' "$d"/race-*.rc 2>/dev/null | wc -l | tr -d ' ')
[ "$wins" -eq 1 ] || fail "same-office race admitted $wins reservations (expected exactly 1)"
[ "$(allids | wc -l | tr -d ' ')" -eq 1 ] || fail 'duplicate reservations survived the race'

newcase s3b
setcfg "$DB" 'offices.statistics.enabled=true,offices.foresight.enabled=true,offices.strategy.enabled=true,offices.spying.enabled=true,aggregate.caps.tokens_total=250,offices.statistics.caps.tokens_total=100,offices.foresight.caps.tokens_total=100,offices.strategy.caps.tokens_total=100,offices.spying.caps.tokens_total=100'
for off in statistics foresight strategy spying; do
  ( eng reserve "$off" > "$d/agg-$off.out" 2> "$d/agg-$off.err"; echo $? > "$d/agg-$off.rc" ) &
done
wait
aggwins=$(grep -l '^0$' "$d"/agg-*.rc 2>/dev/null | wc -l | tr -d ' ')
[ "$aggwins" -eq 2 ] || fail "aggregate cap admitted $aggwins offices (expected exactly 2)"
agg=$(jq -r '.tokens_total' "$STATE/knowledge/budget/aggregate.json")
[ "$agg" -eq 200 ] || fail "aggregate charge $agg (expected 200)"

# ---- S4: crash after reservation; idempotent rollback ------------------------
newcase s4
R=$(eng reserve statistics)
[ "$(rstate "$R")" = reserved ] || fail 'reservation not in reserved state'
ok eng reconcile   # fresh reservation must survive an ordinary sweep
[ "$(rstate "$R")" = reserved ] || fail 'fresh reservation was rolled back prematurely'
jq --argjson old "$(($(date +%s) - 1000))" '.created_at=$old' "$(resdir)/$R.json" > "$d/aged" && mv "$d/aged" "$(resdir)/$R.json"
ok eng reconcile
[ "$(rstate "$R")" = rolled_back ] || fail 'orphaned reservation was not rolled back'
[ "$(jq -r '.tokens_total' "$STATE/knowledge/budget/aggregate.json")" -eq 0 ] || fail 'rolled-back reservation still charges budget'
ok eng reconcile   # idempotent
[ "$(rstate "$R")" = rolled_back ] || fail 'second reconcile changed a rolled-back reservation'
ok eng reserve statistics

# ---- S4b: crash AFTER dispatch attempt but before meter registration --------
newcase s4b
R=$(eng reserve statistics)
ok eng mark-dispatched "$R"
jq --argjson old "$(($(date +%s) - 1000))" '.created_at=$old' "$(resdir)/$R.json" > "$d/aged2" && mv "$d/aged2" "$(resdir)/$R.json"
ok eng reconcile
[ "$(rstate "$R")" = held ] || fail 'ambiguous dispatch was not held pessimistically'
[ "$(resjson "$R" | jq -r '.charge.tokens_total')" -eq 400000 ] || fail 'ambiguous dispatch lacks full-cap pessimistic charge'
no eng reserve statistics   # halted future dispatch until an audited resolution
ok eng resolve "$R" 'verified from Antonina session log: no live agent'
[ "$(rstate "$R")" = closed ] || fail 'audited resolution did not close the held reservation'
[ "$(resjson "$R" | jq -r '.usage.tokens_total')" -eq 400000 ] || fail 'resolution lost the pessimistic charge'
[ "$(jq -r '.tokens_total' "$STATE/knowledge/budget/aggregate.json")" -eq 400000 ] || fail 'resolution did not keep the charge in the aggregate'
ok eng reserve statistics

# ---- S5: corrupt/missing meter after launch => hold, pessimistic, reconcile --
newcase s5
setcfg "$DB" 'offices.statistics.enabled=true,offices.statistics.caps.tokens_total=100000'
R=$(eng reserve statistics)
ok eng start "$R" test-agent
waitstate "$R" active
mv "$DB" "$DB.saved"
sleep 2
[ "$(rstate "$R")" = held ] || fail 'missing meter did not hold the reservation'
[ "$(resjson "$R" | jq -r '.charge.tokens_total')" -eq 100000 ] || fail 'held reservation lacks pessimistic full-cap charge'
grep -q '^kill ' "$STUB_KILL_LOG" || fail 'agent not killed when meter became unreadable'
no eng reserve statistics
mv "$DB.saved" "$DB"
status_terminal
settokens "$DB" 40
ok eng reconcile
[ "$(rstate "$R")" = closed ] || fail 'terminal held reservation was not reconciled to closed'
[ "$(resjson "$R" | jq -r '.usage.tokens_total')" -eq 40 ] || fail 'reconciled usage is not the verified actual reading'
ok eng reconcile
[ "$(resjson "$R" | jq -r '.usage.tokens_total')" -eq 40 ] || fail 'reconciliation is not idempotent'

# ---- S6: token overrun while the live agent is still running -----------------
newcase s6
setcfg "$DB" 'offices.statistics.enabled=true,offices.statistics.caps.tokens_total=100000'
R=$(eng reserve statistics)
ok eng start "$R" test-agent
waitstate "$R" active
status_running   # deliberately still running: the launcher timeout is irrelevant
settokens "$DB" 250000
sleep 3
[ "$(rstate "$R")" = closed ] || fail 'overrun did not close the reservation'
case "$(resjson "$R" | jq -r '.closed_reason')" in overrun_*) :;; *) fail 'wrong close reason for overrun';; esac
grep -q '^kill ' "$STUB_KILL_LOG" || fail 'live agent was not killed on overrun'
usage=$(resjson "$R" | jq -c '.usage')
[ "$(printf '%s\n' "$usage" | jq -r '.tokens_total')" -eq 250000 ] || fail 'overrun usage is not the authoritative token total'
[ "$(printf '%s\n' "$usage" | jq -r '.cost')" = 0.0 ] || fail 'cost was falsified'
[ "$(printf '%s\n' "$usage" | jq -r '.cost_reported')" = true ] || fail 'cost provenance lost'

# ---- S7: monitor crash / box restart reconciliation --------------------------
newcase s7
setcfg "$DB" 'offices.statistics.enabled=true,offices.statistics.caps.tokens_total=100000'
R=$(eng reserve statistics)
ok eng start "$R" test-agent
waitstate "$R" active
oldpid=$(resjson "$R" | jq -r '.monitor_pid')
[ -n "$oldpid" ] && kill -9 "$oldpid" 2>/dev/null || :
# Simulate a box restart: the recorded monitor is gone (no live pid).
jq '.monitor_pid=99999999' "$(resdir)/$R.json" > "$d/restart" && mv "$d/restart" "$(resdir)/$R.json"
status_running
settokens "$DB" 300000
ok eng reconcile   # boot-style sweep must relaunch the monitor after restart
newpid=$(resjson "$R" | jq -r '.monitor_pid')
[ "$newpid" != "$oldpid" ] || fail 'restart did not relaunch a fresh monitor'
sleep 3
[ "$(rstate "$R")" = closed ] || fail 'post-restart monitor did not stop the overrunning agent'
[ "$(allids | wc -l | tr -d ' ')" -eq 1 ] || fail 'restart caused double-counting'

# ---- S8: hard expiry stops a live agent and reconcile honours it -------------
newcase s8
setcfg "$DB" 'offices.statistics.enabled=true,offices.statistics.caps.tokens_total=1000000,offices.statistics.caps.wall_seconds=2'
R=$(eng reserve statistics)
ok eng start "$R" test-agent
waitstate "$R" active
sleep 4
[ "$(rstate "$R")" = closed ] || fail 'expiry did not close the reservation'
[ "$(resjson "$R" | jq -r '.closed_reason')" = expiry ] || fail 'wrong close reason for expiry'
grep -q '^kill ' "$STUB_KILL_LOG" || fail 'live agent not killed at expiry'

newcase s8b
setcfg "$DB" 'offices.statistics.enabled=true,offices.statistics.caps.tokens_total=1000000,offices.statistics.caps.wall_seconds=3600'
R=$(eng reserve statistics)
ok eng start "$R" test-agent
waitstate "$R" active
jq --argjson past "$(($(date +%s) - 5))" '.expires_at=$past' "$(resdir)/$R.json" > "$d/exp" && mv "$d/exp" "$(resdir)/$R.json"
status_running
ok eng reconcile
[ "$(rstate "$R")" = closed ] || fail 'reconcile past expiry did not stop the session'
[ "$(resjson "$R" | jq -r '.closed_reason')" = expiry ] || fail 'reconcile at expiry used wrong reason'

# ---- S9: source-controlled config validation and exact rollback --------------
newcase s9
CFG=$TOWN/government/knowledge-budget.conf
cp "$CFG" "$d/config-A.json"
ok eng config validate
ok eng config activate
hashA=$(sha256sum "$STATE/knowledge/budget/config.active.json" | awk '{print $1}')
cp "$DB" "$DB.bak"
setcfg "$DB" 'offices.statistics.caps.tokens_total=777777'
cp "$CFG" "$d/config-B.json"
ok eng config activate
hashB=$(sha256sum "$STATE/knowledge/budget/config.active.json" | awk '{print $1}')
[ "$hashA" != "$hashB" ] || fail 'activating a different config did not change the active hash'
ok eng config rollback
hashR=$(sha256sum "$STATE/knowledge/budget/config.active.json" | awk '{print $1}')
[ "$hashR" = "$hashA" ] || fail 'rollback was not byte-exact'
printf 'not json' > "$CFG"
no eng config activate
[ "$(sha256sum "$STATE/knowledge/budget/config.active.json" | awk '{print $1}')" = "$hashA" ] ||
  fail 'invalid config activation damaged the active config'
no eng reserve statistics   # missing/corrupt config fails closed

# ---- S10: cycle integration gate (no dispatch without a budget reservation) --
newcase s10
mkdir -p "$TOWN/records/knowledge" "$d/seats-$CASE/branches/statistics"
: > "$d/seats-$CASE/branches/statistics/.git"
printf '#!/bin/sh\nexit 0\n' > "$TOWN/government/knowledge-activation-verify.sh"
printf '#!/bin/sh\nexit 0\n' > "$TOWN/government/branch-bootstrap.sh"
printf '#!/bin/sh\nprintf "%%s\\n" test-agent\n' > "$TOWN/government/appointments.sh"
printf '#!/bin/sh\necho recover\n' > "$TOWN/government/terminal-continuity.sh"
printf '%s\n' '## Act 32 — Institutional Knowledge and Communications Act (enacted for test)' > "$TOWN/government/LAWS.md"
printf 'Synthetic frozen baseline\n' > "$TOWN/records/knowledge/baseline-20261119.json"
printf 'Synthetic charter\n' > "$d/charter-$CASE"
now=$(date +%s)
jq -n --argjson now "$now" '{schema:"viche-knowledge-activation-v1",offices:{statistics:{enabled:true,authorized_by:"act:32:statistics",not_before:($now-30),expires_at:($now+3600)}}}' > "$TOWN/records/knowledge/activation.json"
cp "$REPO/government/knowledge-office-cycle.sh" "$TOWN/government/"
cp "$ENGINE" "$TOWN/government/"; cp "$TOOL" "$TOWN/government/"
export VICHE_SEATS_ROOT="$d/seats-$CASE" VICHE_CONSTITUTION="$d/charter-$CASE"
VICHE_TOWN_ROOT="$TOWN" /bin/sh "$TOWN/government/knowledge-office-cycle.sh" statistics >/dev/null 2>&1 || :
# Shipped config has statistics disabled: guard must block before any run.
[ ! -s "$STUB_RUN_LOG" ] || fail 'cycle dispatched with the office disabled in the budget config'
setcfg "$DB" 'offices.statistics.enabled=true'
status_terminal   # idle/clearexit appointee proceeds past the cycle's liveness check
VICHE_TOWN_ROOT="$TOWN" /bin/sh "$TOWN/government/knowledge-office-cycle.sh" statistics >/dev/null 2>&1 || :
[ -s "$STUB_RUN_LOG" ] || fail 'cycle did not dispatch when the budget admitted the office'
[ -n "$(allids)" ] || fail 'cycle dispatched without an atomic budget reservation'

echo 'knowledge budget: default-disabled, fail-closed meter, race, crash rollback, corrupt meter, overrun kill, restart, expiry, exact rollback and cycle gate all verified'

#!/bin/sh
# Deterministic regressions for terminal budget accounting. No live agent, no
# provider, no real state: antonina is a recording stub and all budgets/ledgers
# live in a private temp directory.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
tool=$repo/government/knowledge-budget-tool.py
engine=$repo/government/knowledge-budget.sh
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM

fail() { echo "FAIL: $*" >&2; exit 1; }
ok() { "$@" >/dev/null 2>&1 || fail "$* failed"; }

town=$tmp/town
mkdir -p "$town/government" "$tmp/bin"
cp "$repo/government/knowledge-budget.conf" "$town/government/config.template"

# Per-case authoritative meter with the exact session_v2 schema the tool reads.
mkdb() { # path, token count
  python3 - "$1" "$2" <<'PY'
import sqlite3,sys
c=sqlite3.connect(sys.argv[1])
c.execute('create table session_v2 (id text primary key,tokens_input int,tokens_output int,tokens_reasoning int,tokens_cache_read int,tokens_cache_write int,cost real,time_updated int)')
c.execute("insert into session_v2 values ('sid',?,0,0,0,0,0.0,1795279700000)",(int(sys.argv[2]),))
c.commit()
PY
}

mkcfg() { # case state root, db, token cap
  cp "$town/government/config.template" "$town/government/knowledge-budget.conf"
  python3 - "$town/government/knowledge-budget.conf" "$2" "$3" <<'PY'
import json,sys
p,db,cap=sys.argv[1:]
c=json.load(open(p))
c['metering']['opencode_db']=db
c['monitor_interval_seconds']=300
c['offices']['statistics']['enabled']=True
c['offices']['statistics']['caps']['tokens_total']=int(cap)
c['offices']['statistics'].pop('per_run_caps',None)
json.dump(c,open(p,'w'))
PY
  mkdir -p "$1/knowledge/budget/reservations"
}

cat > "$tmp/mkactive.py" <<'PY'
import json,subprocess,sys,time
path,tool,db,sid,agent,tokens,delta=sys.argv[1:]
a=json.load(open(path))
snap=json.loads(subprocess.check_output(['python3',tool,'snapshot',db,sid,'123']))
adj=json.loads(subprocess.check_output(['python3',tool,'cpu-delta',
    json.dumps(a['cpu_baseline']),json.dumps(snap)]))
now=int(time.time())
a.update(state='active',agent_id=agent,native_session_id=sid,runner_pid='123',
         started_at=now-100,expires_at=now+int(delta),meter=adj)
json.dump(a,open(path,'w'))
PY

cat > "$tmp/mkheld.py" <<'PY'
import json,subprocess,sys,time
path,tool,db,sid,agent,observed=sys.argv[1:]
a=json.load(open(path))
snap=json.loads(subprocess.check_output(['python3',tool,'snapshot',db,sid,'123']))
adj=json.loads(subprocess.check_output(['python3',tool,'cpu-delta',
    json.dumps(a['cpu_baseline']),json.dumps(snap)]))
adj['tokens']['total']=int(observed)
adj['tokens']['delta_total']=int(observed)
now=int(time.time())
a.update(state='held',agent_id=agent,native_session_id=sid,runner_pid='123',
         started_at=now-100,expires_at=now+3600,meter=adj,
         charge=dict(a['caps']),held_at=now,
         held_reason='agent_still_active_or_unknown_after_stop')
json.dump(a,open(path,'w'))
PY

# The stub is the ONLY antonina any case can see. It never dispatches anything.
cat > "$tmp/bin/antonina" <<'SH'
#!/bin/sh
case "$1 $2" in
  'agent status')
    cat "$TEST_AGENT_STATE"
    ;;
  'agent kill'|'agent stop')
    printf '%s\n' "$*" >> "$TEST_AGENT_KILLS"
    case "${TEST_MODE:-}" in
      late_commit)
        python3 - "$TEST_DB" <<'PY'
import sqlite3,sys
c=sqlite3.connect(sys.argv[1])
c.execute("update session_v2 set tokens_input=180,time_updated=1795279800000 where id='sid'")
c.commit()
PY
        ;;
      unreadable_after_stop)
        mv "$TEST_DB" "$TEST_DB.moved"
        ;;
    esac
    printf '{"state":"clearexit","native_session_id":"sid"}\n' > "$TEST_AGENT_STATE"
    ;;
  *) exit 17 ;;
esac
SH
chmod +x "$tmp/bin/antonina"
export PATH="$tmp/bin:$PATH"
export VICHE_TOWN_ROOT="$town" VICHE_BUDGET_TOOL="$tool" TEST_AGENT_STATE="$tmp/agent.json"
export TEST_AGENT_KILLS="$tmp/kills.log"
printf '{"state":"running","native_session_id":"sid"}\n' > "$TEST_AGENT_STATE"

echo '--- T1: usage committed after the stop is charged, not lost ---'
s1=$tmp/s1; db1=$tmp/m1.db
mkdb "$db1" 100; mkcfg "$s1" "$db1" 1000
export VICHE_STATE_ROOT="$s1" TEST_DB="$db1" TEST_MODE=late_commit
rid=$(/bin/sh "$engine" reserve statistics late-agent)
python3 "$tmp/mkactive.py" "$s1/knowledge/budget/reservations/$rid.json" "$tool" "$db1" sid late-agent 100 -1
/bin/sh "$engine" reconcile >/dev/null
jq -e '.state=="closed" and .usage.tokens_total>=180 and .closed_reason=="expiry"' \
  "$s1/knowledge/budget/reservations/$rid.json" >/dev/null ||
  fail 'late post-stop commit was not charged'
echo 'T1 ok'

echo '--- T2: meter unreadable after stop holds at full cap ---'
s2=$tmp/s2; db2=$tmp/m2.db
mkdb "$db2" 100; mkcfg "$s2" "$db2" 1000
export VICHE_STATE_ROOT="$s2" TEST_DB="$db2" TEST_MODE=unreadable_after_stop
rid=$(/bin/sh "$engine" reserve statistics unreadable-agent)
python3 "$tmp/mkactive.py" "$s2/knowledge/budget/reservations/$rid.json" "$tool" "$db2" sid unreadable-agent 100 -1
/bin/sh "$engine" reconcile >/dev/null
jq -e '.state=="held" and .charge.tokens_total==1000 and
        .held_reason=="meter_unreadable_after_stop"' \
  "$s2/knowledge/budget/reservations/$rid.json" >/dev/null ||
  fail 'unreadable post-stop meter released an optimistic charge'
echo 'T2 ok'

echo '--- T3: a replaced/reset session row cannot erase observed liability ---'
s3=$tmp/s3; db3=$tmp/m3.db
mkdb "$db3" 100; mkcfg "$s3" "$db3" 1000
export VICHE_STATE_ROOT="$s3" TEST_DB="$db3" TEST_MODE=terminal
rid=$(/bin/sh "$engine" reserve statistics changed-session-agent)
python3 "$tmp/mkactive.py" "$s3/knowledge/budget/reservations/$rid.json" "$tool" "$db3" sid changed-session-agent 100 -1
# The monitor had already observed 185 tokens in this session; a later read of
# the pinned row shows only 100. The observed debt must still be charged.
python3 - "$s3/knowledge/budget/reservations/$rid.json" <<'PY'
import json,sys
p=sys.argv[1]; a=json.load(open(p))
a['meter']['tokens']['total']=185
a['meter']['tokens']['delta_total']=185
json.dump(a,open(p,'w'))
PY
/bin/sh "$engine" reconcile >/dev/null
jq -e '.state=="closed" and .usage.tokens_total>=185' \
  "$s3/knowledge/budget/reservations/$rid.json" >/dev/null ||
  fail 'stale/changed session row reduced a previously observed charge'
echo 'T3 ok'

echo '--- T4: held overrun cannot be released below its observed meter ---'
s4=$tmp/s4; db4=$tmp/m4.db
mkdb "$db4" 100; mkcfg "$s4" "$db4" 150
export VICHE_STATE_ROOT="$s4" TEST_DB="$db4" TEST_MODE=terminal
rid=$(/bin/sh "$engine" reserve statistics held-agent)
python3 "$tmp/mkheld.py" "$s4/knowledge/budget/reservations/$rid.json" "$tool" "$db4" sid held-agent 185
/bin/sh "$engine" reconcile >/dev/null
jq -e '.state=="closed" and .usage.tokens_total>=185 and
        (.closed_reason|startswith("reconciled_terminal"))' \
  "$s4/knowledge/budget/reservations/$rid.json" >/dev/null ||
  fail 'reconciliation released a held overrun below observed usage'
echo 'T4 ok'

echo '--- T5: missing native session identity at finalize stays a full-cap hold ---'
s5=$tmp/s5; db5=$tmp/m5.db
mkdb "$db5" 100; mkcfg "$s5" "$db5" 1000
export VICHE_STATE_ROOT="$s5" TEST_DB="$db5" TEST_MODE=terminal
rid=$(/bin/sh "$engine" reserve statistics missing-session-agent)
python3 "$tmp/mkactive.py" "$s5/knowledge/budget/reservations/$rid.json" "$tool" "$db5" sid missing-session-agent 100 -1
jq '.native_session_id="absent-session"' "$s5/knowledge/budget/reservations/$rid.json" > "$tmp/r5.json"
mv "$tmp/r5.json" "$s5/knowledge/budget/reservations/$rid.json"
/bin/sh "$engine" reconcile >/dev/null
jq -e '.state=="held" and .charge.tokens_total==1000 and
        .held_reason=="meter_unreadable_at_finalize"' \
  "$s5/knowledge/budget/reservations/$rid.json" >/dev/null ||
  fail 'missing session identity was not held at full cap'
echo 'T5 ok'

echo 'PASS: terminal accounting keeps late commits, fail-closed holds and observed overrun debt'

#!/bin/sh
# Exact-suite scheduling and detached fixture-monitor lifetime regressions.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)

# Act 31 verification is delivery-critical work, not speculative background
# research. Bare `nice` means +10 and starves the gate behind nice-0 research.
python3 - "$repo/government/boot.sh" <<'PY'
import re, sys
lines = open(sys.argv[1], encoding="utf-8").read().splitlines()
line = next((x for x in lines if "integrator.py" in x and " run" in x), "")
assert re.search(r'timeout\s+7200\s+python3\s+.*integrator\.py.*\srun', line), line
assert not re.search(r'\bnice(?:\s|$)', line), "integrator is still niced: " + line
PY

d=$(mktemp -d)
owner=
monitor=
cleanup() {
  if [ -n "$monitor" ]; then
    kill -KILL "-$monitor" 2>/dev/null || kill -KILL "$monitor" 2>/dev/null || :
  fi
  if [ -n "$owner" ]; then
    kill -KILL "$owner" 2>/dev/null || :
  fi
  rm -rf "$d"
}
trap cleanup EXIT HUP INT TERM
mkdir -p "$d/state/knowledge/budget/reservations"
now=$(date +%s)
cat > "$d/state/knowledge/budget/reservations/fixture.json" <<JSON
{"id":"fixture","state":"active","monitor_interval_seconds":30,"expires_at":$((now + 3600)),"agent_id":"fixture-agent","native_session_id":"sid"}
JSON

# A separate session models the setsid monitor that escaped a timed-out suite.
sleep 30 &
owner=$!
VICHE_TOWN_ROOT="$repo" VICHE_STATE_ROOT="$d/state" VICHE_SUITE_ROOT_PID="$owner" \
  setsid /bin/sh "$repo/government/knowledge-budget.sh" monitor fixture \
  9>&- </dev/null >> "$d/monitor.log" 2>&1 &
monitor=$!
sleep 0.2
kill -KILL "$owner"
wait "$owner" 2>/dev/null || :
owner=

# The production interval is 30s. The fixture-aware monitor must instead notice
# the dead suite owner and exit on its one-second ownership poll.
python3 - "$monitor" <<'PY'
import pathlib, sys, time
pid = int(sys.argv[1])
deadline = time.monotonic() + 4
while time.monotonic() < deadline:
    try:
        fields = pathlib.Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        if fields[0] == "Z":
            break
    except FileNotFoundError:
        break
    time.sleep(.05)
else:
    raise SystemExit(f"detached fixture monitor {pid} outlived its suite owner")
PY
monitor=
echo 'PASS: integrator runs at ordinary priority; detached fixture monitor exits with its suite owner'

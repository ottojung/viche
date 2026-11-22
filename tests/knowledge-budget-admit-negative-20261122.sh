#!/bin/sh
# Characterization test (POSIX /bin/sh) for the Economy 2026-11-22 per-request
# admission finding. Reproduces the exact negative case with the engine's own
# deterministic `admit` command, on an isolated in-memory aggregate. Touches no
# live state, config, meter, credential or record.
#
# PASS means the DOCUMENTED GAP IS PRESENT: at 399,000 used tokens the engine
# still admits another Statistics reservation. If a fix later makes admit false
# here, this test FAILS by design and the finding record must be updated.
set -eu
TOWN=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche-seats/branches/economy-perrequest-cap-20261122}
TOOL="$TOWN/government/knowledge-budget-tool.py"
CFG="$TOWN/government/knowledge-budget.conf"
[ -f "$TOOL" ] && [ -f "$CFG" ] || { echo "FATAL: tool/config missing" >&2; exit 2; }

admit_at() {
  _used=$1
  _agg=$(printf '{"tokens_total":%s,"cpu_seconds":0,"wall_seconds":0,"counted":[],"skipped":[]}' "$_used")
  python3 "$TOOL" admit "$CFG" "$_agg" statistics
}

t1=$(admit_at 0)
t2=$(admit_at 399000)
t3=$(admit_at 1200000)
printf 'used=0        -> %s\n' "$t1"
printf 'used=399000   -> %s\n' "$t2"
printf 'used=1200000  -> %s\n' "$t3"

v1=$(printf '%s\n' "$t1" | jq -r '.admit')
v2=$(printf '%s\n' "$t2" | jq -r '.admit')
v3=$(printf '%s\n' "$t3" | jq -r '.admit')
[ "$v1" = true ] || { echo "FAIL: sanity admit(0) not true" >&2; exit 1; }
[ "$v2" = true ] || { echo "FAIL: documented gap closed at 399000 (update finding)" >&2; exit 1; }
[ "$v3" = true ] || { echo "FAIL: documented gap closed at 1200000 (update finding)" >&2; exit 1; }
echo "PASS: engine admits a new Statistics reservation at 399000 and 1200000 used tokens (strict-cap claim refuted)."

#!/bin/sh
# A failed executive pauses visibly and delegates recovery to the office
# supervisor (branch-bootstrap via branch-liveness), which under Act 19 §3.1
# resets on a failure COUNT — 3 consecutive transient failures — regardless of
# the observed state, with a 1800 s cooldown: no dispatch, no reset outside
# the cooldown, no unbounded retry storm.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
mkdir -p "$scratch/bin" "$scratch/town/government" "$scratch/town/records" \
    "$scratch/seats/branches/executive" "$scratch/state" "$scratch/mock"
printf 'c1e00001\tClerk\tintake\n' > "$scratch/town/government/seats.tsv"
cp "$repo/government/branch-bootstrap.sh" "$scratch/town/government/branch-bootstrap.sh"
cp "$repo/government/office-continuity.sh" "$scratch/town/government/office-continuity.sh"
cp "$repo/government/executive-cycle.sh" "$scratch/town/government/executive-cycle.sh"
cp "$repo/government/eligible-work.py" "$scratch/town/government/eligible-work.py"
cp "$repo/government/handoff-queue.sh" "$scratch/town/government/handoff-queue.sh"
printf 'Founder charter fixture\n' > "$scratch/charter"
touch "$scratch/state/inaugurated"
printf '{"state":"failed","model":"example-provider/model-a","variant":"low","backend_error":{"classification":"upstream_endpoint_unavailable","transient":true}}\n' > "$scratch/mock/status.json"
cat > "$scratch/bin/antonina" <<'MOCK'
#!/bin/sh
set -eu
case "$1 $2" in
  'agent status') cat "$MOCK_ROOT/status.json" ;;
  'agent run') echo run >> "$MOCK_ROOT/dispatches" ;;
  'agent log') echo 'Endpoint is unavailable' ;;
  'agent delete') echo delete >> "$MOCK_ROOT/recovery" ;;
  'agent new')
    echo new >> "$MOCK_ROOT/recovery"
    printf '{"state":"idle","model":"example-provider/model-a","variant":"low"}\n' > "$MOCK_ROOT/status.json"
    ;;
  'board list') echo '[]' ;;
  'board show') echo '{"body":"","messages":[]}' ;;
  *) exit 9 ;;
esac
MOCK
chmod +x "$scratch/bin/antonina"
git -C "$scratch/seats/branches/executive" init -q
git -C "$scratch/seats/branches/executive" -c user.name=test -c user.email=test@example.test commit --allow-empty -qm baseline
PATH="$scratch/bin:$PATH"
MOCK_ROOT="$scratch/mock"
mkdir -p "$scratch/town/government"
cp "$repo/tests/appointment-id-stub.sh" "$scratch/town/government/appointments.sh"
VICHE_TOWN_ROOT="$scratch/town"
VICHE_SEATS_ROOT="$scratch/seats"
VICHE_STATE_ROOT="$scratch/state"
VICHE_CONSTITUTION="$scratch/charter"
export PATH MOCK_ROOT VICHE_TOWN_ROOT VICHE_SEATS_ROOT VICHE_STATE_ROOT VICHE_CONSTITUTION
failures=$scratch/state/liveness/failures/c1e00002

# A failed executive must not dispatch and must not reset below the threshold.
/bin/sh "$scratch/town/government/executive-cycle.sh" 2>/dev/null || true
/bin/sh "$scratch/town/government/branch-bootstrap.sh" executive
[ ! -e "$MOCK_ROOT/dispatches" ]
[ ! -e "$MOCK_ROOT/recovery" ]
[ "$(wc -l < "$failures")" -eq 1 ]

# Three consecutive transient failures fire exactly one bounded reset, even
# though the oscillating agent is observed "running" between failures.
printf '{"state":"running","model":"example-provider/model-a","variant":"low"}\n' > "$scratch/mock/status.json"
/bin/sh "$scratch/town/government/branch-bootstrap.sh" executive
[ ! -e "$MOCK_ROOT/recovery" ]
printf '{"state":"failed","model":"example-provider/model-a","variant":"low","backend_error":{"classification":"upstream_endpoint_unavailable","transient":true}}\n' > "$scratch/mock/status.json"
/bin/sh "$scratch/town/government/branch-bootstrap.sh" executive
[ "$(wc -l < "$failures")" -eq 2 ]
printf '{"state":"running","model":"example-provider/model-a","variant":"low"}\n' > "$scratch/mock/status.json"
/bin/sh "$scratch/town/government/branch-bootstrap.sh" executive
[ ! -e "$MOCK_ROOT/recovery" ]
printf '{"state":"failed","model":"example-provider/model-a","variant":"low","backend_error":{"classification":"upstream_endpoint_unavailable","transient":true}}\n' > "$scratch/mock/status.json"
/bin/sh "$scratch/town/government/branch-bootstrap.sh" executive
[ "$(wc -l < "$MOCK_ROOT/recovery")" -eq 2 ]
[ ! -e "$MOCK_ROOT/dispatches" ]
[ "$(wc -l < "$failures")" -eq 0 ]

# While the cooldown is unexpired, three more failures cannot reset again.
printf '{"state":"failed","model":"example-provider/model-a","variant":"low","backend_error":{"classification":"upstream_endpoint_unavailable","transient":true}}\n' > "$scratch/mock/status.json"
/bin/sh "$scratch/town/government/branch-bootstrap.sh" executive
/bin/sh "$scratch/town/government/branch-bootstrap.sh" executive
/bin/sh "$scratch/town/government/branch-bootstrap.sh" executive
[ "$(wc -l < "$MOCK_ROOT/recovery")" -eq 2 ]
[ "$(wc -l < "$failures")" -eq 3 ]
[ ! -e "$MOCK_ROOT/dispatches" ]

# Once the cooldown expires, the third consecutive failure resets exactly once
# more, never more.
printf '0\n' > "$scratch/state/liveness/last-reset-c1e00002"
printf '{"state":"failed","model":"example-provider/model-a","variant":"low","backend_error":{"classification":"upstream_endpoint_unavailable","transient":true}}\n' > "$scratch/mock/status.json"
/bin/sh "$scratch/town/government/branch-bootstrap.sh" executive
[ "$(wc -l < "$MOCK_ROOT/recovery")" -eq 4 ]
[ ! -e "$MOCK_ROOT/dispatches" ]
echo 'Executive recovery timing smoke checks passed'

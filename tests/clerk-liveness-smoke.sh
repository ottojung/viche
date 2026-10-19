#!/bin/sh
# Hermetic Clerk recovery under Act 19 §3.1: failure-count reset (3
# consecutive transient failures / 30 min, 1800 s cooldown), progress guard,
# permanent failures surfaced not reset, evidence preserved.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT
mkdir -p "$d/bin" "$d/town/government" "$d/seats/c1a00001" "$d/state/liveness" "$d/mock"
printf 'c1a00001\tClerk\tFounder intake\n' > "$d/town/government/seats.tsv"
cp "$repo/government/clerk-liveness.sh" "$d/town/government/clerk-liveness.sh"
cp "$repo/government/office-continuity.sh" "$d/town/government/office-continuity.sh"
git -C "$d/seats/c1a00001" init -q
git -C "$d/seats/c1a00001" -c user.name=test -c user.email=test@example.test commit --allow-empty -qm initial
printf 'valuable uncommitted work\n' > "$d/seats/c1a00001/uncommitted.txt"
cat > "$d/bin/antonina" <<'MOCK'
#!/bin/sh
set -eu
case "$1 $2" in
  'agent status') cat "$MOCK_ROOT/status" ;;
  'agent log') printf 'Endpoint is unavailable\n' ;;
  'agent delete') printf 'delete\n' >> "$MOCK_ROOT/actions" ;;
  'agent new')
    printf 'new\n' >> "$MOCK_ROOT/actions"
    printf '{"state":"idle"}\n' > "$MOCK_ROOT/status"
    ;;
  *) exit 9 ;;
esac
MOCK
chmod +x "$d/bin/antonina"
set_status() {
  printf '{"state":"%s","model":"opencode-go/longcat-2.5-preview-free","backend_error":{"classification":"%s","transient":%s}}\n' \
    "$1" "$2" "$3" > "$d/mock/status"
}
PATH="$d/bin:$PATH"
MOCK_ROOT="$d/mock"
VICHE_TOWN_ROOT="$d/town"
VICHE_SEATS_ROOT="$d/seats"
VICHE_STATE_ROOT="$d/state"
export PATH MOCK_ROOT VICHE_TOWN_ROOT VICHE_SEATS_ROOT VICHE_STATE_ROOT
failures=$d/state/liveness/failures/c1a00001

# Two observed transient failures are recorded but do not reset (threshold 3).
set_status failed upstream_endpoint_unavailable true
dash "$repo/government/clerk-liveness.sh"
dash "$repo/government/clerk-liveness.sh"
test "$(wc -l < "$failures")" -eq 2
test ! -e "$d/mock/actions"

# The third consecutive failure fires one bounded reset; evidence is preserved.
set_status failed upstream_endpoint_unavailable true
dash "$repo/government/clerk-liveness.sh"
test "$(wc -l < "$d/mock/actions")" -eq 2
test -f "$d/seats/c1a00001/uncommitted.txt"
test -s "$d/state/liveness/recoveries.log"
grep -Fq 'session_reset=failure_count threshold=3 window=1800 cooldown=1800' "$d/state/liveness/recoveries.log"
test -s "$d/state/liveness/last-reset-c1a00001"
test "$(find "$d/state/liveness" -name agent-status.json | wc -l)" -eq 1
# The failure record is cleared after the reset: the next streak starts at zero.
test "$(wc -l < "$failures")" -eq 0

# While the cooldown is unexpired, three fresh failures cannot reset again.
set_status failed upstream_endpoint_unavailable true
dash "$repo/government/clerk-liveness.sh"
dash "$repo/government/clerk-liveness.sh"
dash "$repo/government/clerk-liveness.sh"
test "$(wc -l < "$failures")" -eq 3
test "$(wc -l < "$d/mock/actions")" -eq 2

# Once the cooldown expires, the third consecutive failure resets exactly once.
printf '0\n' > "$d/state/liveness/last-reset-c1a00001"
set_status failed upstream_endpoint_unavailable true
dash "$repo/government/clerk-liveness.sh"
dash "$repo/government/clerk-liveness.sh"
dash "$repo/government/clerk-liveness.sh"
test "$(wc -l < "$d/mock/actions")" -eq 4
test -f "$d/seats/c1a00001/uncommitted.txt"

# Progress guard: with the cooldown expired, a durable commit between failures
# must be what prevents the reset of a healthy-but-slow office.
printf '0\n' > "$d/state/liveness/last-reset-c1a00001"
: > "$failures"
set_status failed upstream_endpoint_unavailable true
dash "$repo/government/clerk-liveness.sh"
dash "$repo/government/clerk-liveness.sh"
test "$(wc -l < "$failures")" -eq 2
git -C "$d/seats/c1a00001" -c user.name=test -c user.email=test@example.test commit --allow-empty -qm durable
set_status failed upstream_endpoint_unavailable true
dash "$repo/government/clerk-liveness.sh"
test "$(wc -l < "$failures")" -eq 1
test "$(wc -l < "$d/mock/actions")" -eq 4
set_status failed upstream_endpoint_unavailable true
dash "$repo/government/clerk-liveness.sh"
set_status failed upstream_endpoint_unavailable true
dash "$repo/government/clerk-liveness.sh"
test "$(wc -l < "$d/mock/actions")" -eq 6
test "$(wc -l < "$failures")" -eq 0

# A permanent failure is surfaced, never silently reset, never counted.
set_status failed invalid_api_key false
dash "$repo/government/clerk-liveness.sh"
test "$(wc -l < "$d/mock/actions")" -eq 6
test "$(wc -l < "$failures")" -eq 0
grep -Fq 'permanent_failure classification=invalid_api_key surfaced-not-reset' "$d/state/liveness/permanent-incidents.log"

# A failed session must never be continued directly through the gate, and after
# a cooldown-expired reset the healthy session passes the gate again.
printf '0\n' > "$d/state/liveness/last-reset-c1a00001"
set_status failed upstream_endpoint_unavailable true
if dash "$repo/government/clerk-liveness.sh" --gate; then exit 1; fi
dash "$repo/government/clerk-liveness.sh"
dash "$repo/government/clerk-liveness.sh"
dash "$repo/government/clerk-liveness.sh"
test "$(wc -l < "$d/mock/actions")" -eq 8
test "$(wc -l < "$failures")" -eq 0
dash "$repo/government/clerk-liveness.sh" --gate
test -f "$d/seats/c1a00001/uncommitted.txt"

# A healthy Clerk is never reset (the fresh session above is idle).
dash "$repo/government/clerk-liveness.sh"
test "$(wc -l < "$d/mock/actions")" -eq 8
test ! -s "$failures"
printf 'Viche Clerk liveness smoke passed\n'

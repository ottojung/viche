#!/bin/sh
# Hermetic Clerk recovery: preserve Git, evidence, cooldown, retry gate, and
# the Act 19 §3.1 failure-count threshold (3 consecutive transient failures).
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT
mkdir -p "$d/bin" "$d/town/government" "$d/seats/c1a00001" "$d/state" "$d/mock"
cp "$repo/government/office-recovery.sh" "$d/town/government/"
printf 'c1a00001\tClerk\tFounder intake\n' > "$d/town/government/seats.tsv"
git -C "$d/seats/c1a00001" init -q
git -C "$d/seats/c1a00001" -c user.name=test -c user.email=test@example.test commit --allow-empty -qm initial
printf 'valuable uncommitted work\n' > "$d/seats/c1a00001/uncommitted.txt"
cat > "$d/mock/status" <<'JSON'
{"state":"failed","model":"opencode-go/longcat-2.5-preview-free","backend_error":{"classification":"upstream_endpoint_unavailable"}}
JSON
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
PATH="$d/bin:$PATH"
MOCK_ROOT="$d/mock"
VICHE_TOWN_ROOT="$d/town"
VICHE_SEATS_ROOT="$d/seats"
VICHE_STATE_ROOT="$d/state"
export PATH MOCK_ROOT VICHE_TOWN_ROOT VICHE_SEATS_ROOT VICHE_STATE_ROOT

# 1. Below threshold (2 failures): no reset, work preserved.
dash "$repo/government/clerk-liveness.sh"
dash "$repo/government/clerk-liveness.sh"
test "$(wc -l < "$d/mock/actions" 2>/dev/null || printf '0')" -eq 0
test -f "$d/seats/c1a00001/uncommitted.txt"

# 2. Third failure reaches the threshold: reset fires (delete + new).
dash "$repo/government/clerk-liveness.sh"
test "$(wc -l < "$d/mock/actions")" -eq 2
test -f "$d/seats/c1a00001/uncommitted.txt"
test -s "$d/state/office-recovery/recoveries.log"
test -s "$d/state/office-recovery/last-reset-clerk"
test "$(find "$d/state/office-recovery" -name agent-status.json | wc -l)" -eq 1

# 3. A newly failed session cannot be restarted again during cooldown.
cat > "$d/mock/status" <<'JSON'
{"state":"failed","backend_error":{"classification":"upstream_endpoint_unavailable"}}
JSON
if dash "$repo/government/clerk-liveness.sh" --gate; then exit 1; fi
dash "$repo/government/clerk-liveness.sh"
test "$(wc -l < "$d/mock/actions")" -eq 2

# 4. Once the cooldown expires, 3 fresh failures allow one more reset.
printf '0\n' > "$d/state/office-recovery/last-reset-clerk"
if dash "$repo/government/clerk-liveness.sh" --gate; then exit 1; fi
dash "$repo/government/clerk-liveness.sh"
dash "$repo/government/clerk-liveness.sh"
dash "$repo/government/clerk-liveness.sh"
dash "$repo/government/clerk-liveness.sh" --gate
test "$(wc -l < "$d/mock/actions")" -eq 4
test -f "$d/seats/c1a00001/uncommitted.txt"
printf 'Viche Clerk liveness smoke passed\n'

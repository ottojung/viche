#!/bin/sh
# Hermetic Clerk recovery: preserve Git, evidence, cooldown, and retry gate.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT
mkdir -p "$d/bin" "$d/town/government" "$d/seats/c1a00001" "$d/state" "$d/mock"
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
dash "$repo/government/clerk-liveness.sh"
test "$(wc -l < "$d/mock/actions")" -eq 2
test -f "$d/seats/c1a00001/uncommitted.txt"
test -s "$d/state/liveness/recoveries.log"
test -s "$d/state/liveness/last-reset"
test "$(find "$d/state/liveness" -name agent-status.json | wc -l)" -eq 1
# A newly failed session cannot be restarted again during cooldown.
cat > "$d/mock/status" <<'JSON'
{"state":"failed","backend_error":{"classification":"upstream_endpoint_unavailable"}}
JSON
if dash "$repo/government/clerk-liveness.sh" --gate; then exit 1; fi
dash "$repo/government/clerk-liveness.sh"
test "$(wc -l < "$d/mock/actions")" -eq 2
# Once the window expires, one fresh session is allowed.
printf '0\n' > "$d/state/liveness/last-reset"
dash "$repo/government/clerk-liveness.sh" --gate
dash "$repo/government/clerk-liveness.sh"
test "$(wc -l < "$d/mock/actions")" -eq 4
test -f "$d/seats/c1a00001/uncommitted.txt"
printf 'Viche Clerk liveness smoke passed\n'

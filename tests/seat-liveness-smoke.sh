#!/bin/sh
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT
mkdir -p "$d/bin" "$d/town/government" "$d/seats/c1a00007" "$d/state" "$d/mock"
cp "$repo/government/office-recovery.sh" "$d/town/government/"
printf 'c1a00001\tClerk\tAgenda\nc1a00007\tConstitutional member\tLegality\n' > "$d/town/government/seats.tsv"
git -C "$d/seats/c1a00007" init -q
git -C "$d/seats/c1a00007" -c user.name=test -c user.email=test@example.test commit --allow-empty -qm baseline
printf 'uncommitted material\n' > "$d/seats/c1a00007/valuable.txt"
cat > "$d/mock/status" <<'JSON'
{"state":"failed","backend_error":{"classification":"upstream_endpoint_unavailable"}}
JSON
cat > "$d/bin/antonina" <<'MOCK'
#!/bin/sh
set -eu
case "$1 $2" in
 'agent status') cat "$MOCK_ROOT/status" ;;
 'agent log') echo 'Endpoint is unavailable' ;;
 'agent delete') echo delete >> "$MOCK_ROOT/actions" ;;
 'agent new')
   echo new >> "$MOCK_ROOT/actions"
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
dash "$repo/government/seat-liveness.sh" c1a00001
test ! -f "$d/mock/actions"
# Act 19 §3.1: below the 3-failure threshold, no reset.
dash "$repo/government/seat-liveness.sh" c1a00007
dash "$repo/government/seat-liveness.sh" c1a00007
test ! -f "$d/mock/actions"
# Third consecutive transient failure reaches the threshold: reset fires.
dash "$repo/government/seat-liveness.sh" c1a00007
test "$(wc -l < "$d/mock/actions")" -eq 2
test -f "$d/seats/c1a00007/valuable.txt"
test -s "$d/state/office-recovery/recoveries.log"
# Cooldown: an immediate re-check does not reset again.
dash "$repo/government/seat-liveness.sh" c1a00007
test "$(wc -l < "$d/mock/actions")" -eq 2
# After the cooldown expires, 3 fresh failures allow one more reset.
printf '0\n' > "$d/state/office-recovery/last-reset-c1a00007"
cat > "$d/mock/status" <<'JSON'
{"state":"failed","backend_error":{"classification":"upstream_endpoint_unavailable"}}
JSON
dash "$repo/government/seat-liveness.sh" c1a00007
dash "$repo/government/seat-liveness.sh" c1a00007
dash "$repo/government/seat-liveness.sh" c1a00007
test "$(wc -l < "$d/mock/actions")" -eq 4
test -f "$d/seats/c1a00007/valuable.txt"
echo 'Viche parliamentary seat liveness smoke passed'

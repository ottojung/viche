#!/bin/sh
# A failed executive pauses visibly and delegates recovery to seat-liveness,
# which bounds session resets with its own cooldown: no dispatch, no reset
# outside the cooldown, no unbounded retry storm.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
mkdir -p "$scratch/bin" "$scratch/town/government" "$scratch/town/records" \
    "$scratch/seats/b2000002" "$scratch/state" "$scratch/mock"
printf 'a1000001\tClerk\tintake\nb2000002\tExecutive\tdelivery\n' > "$scratch/town/government/seats.tsv"
cp "$repo/government/seat-liveness.sh" "$scratch/town/government/seat-liveness.sh"
printf 'Founder charter fixture\n' > "$scratch/charter"
touch "$scratch/state/inaugurated"
printf '{"state":"failed","backend_error":{"classification":"upstream_endpoint_unavailable"}}\n' > "$scratch/mock/status.json"
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
    printf '{"state":"idle"}\n' > "$MOCK_ROOT/status.json"
    ;;
  *) exit 9 ;;
esac
MOCK
chmod +x "$scratch/bin/antonina"
git -C "$scratch/seats/b2000002" init -q
git -C "$scratch/seats/b2000002" -c user.name=test -c user.email=test@example.test commit --allow-empty -qm baseline
PATH="$scratch/bin:$PATH"
MOCK_ROOT="$scratch/mock"
VICHE_TOWN_ROOT="$scratch/town"
VICHE_SEATS_ROOT="$scratch/seats"
VICHE_STATE_ROOT="$scratch/state"
VICHE_CONSTITUTION="$scratch/charter"
export PATH MOCK_ROOT VICHE_TOWN_ROOT VICHE_SEATS_ROOT VICHE_STATE_ROOT VICHE_CONSTITUTION

# A failed executive must not dispatch and must attempt exactly one bounded reset.
/bin/sh "$repo/government/executive-cycle.sh" 2>/dev/null
[ ! -e "$MOCK_ROOT/dispatches" ]
[ "$(wc -l < "$MOCK_ROOT/recovery")" -eq 2 ]

# While the cooldown is unexpired, a repeated failure cannot reset again.
printf '{"state":"failed","backend_error":{"classification":"upstream_endpoint_unavailable"}}\n' > "$MOCK_ROOT/status.json"
/bin/sh "$repo/government/executive-cycle.sh" 2>/dev/null
[ "$(wc -l < "$MOCK_ROOT/recovery")" -eq 2 ]
[ ! -e "$MOCK_ROOT/dispatches" ]

# Once the cooldown expires, recovery is attempted exactly once more, never more.
printf '0\n' > "$scratch/state/liveness/last-reset-b2000002"
printf '{"state":"failed","backend_error":{"classification":"upstream_endpoint_unavailable"}}\n' > "$MOCK_ROOT/status.json"
/bin/sh "$repo/government/executive-cycle.sh" 2>/dev/null
[ "$(wc -l < "$MOCK_ROOT/recovery")" -eq 4 ]
[ ! -e "$MOCK_ROOT/dispatches" ]
echo 'Executive recovery timing smoke checks passed'

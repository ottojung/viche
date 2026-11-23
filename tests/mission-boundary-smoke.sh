#!/bin/sh
# Regression: government contains no assignment-specific implementation or
# scheduling. Missions are replaceable without editing government.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)

# Historical enacted laws retain authentic original text and citations.
if grep -R -n --include=*.sh --include=*.py --include=*.md --include=*.txt -E '(SoringP1|pequalnp|P vs NP|Kawun|kawunapp|skrynia-apps)' "$repo/government" --exclude='LAWS.md' > /tmp/mission-boundary-matches-$$; then
    cat /tmp/mission-boundary-matches-$$ >&2
    rm -f /tmp/mission-boundary-matches-$$
    echo 'mission-specific code or policy leaked back into government' >&2
    exit 1
fi
rm -f /tmp/mission-boundary-matches-$$
[ ! -e "$repo/government/pnp" ]
[ ! -e "$repo/government/pnp-cycle.sh" ]
[ -s "$repo/missions/pnp/mandate.md" ]
[ -s "$repo/missions/soringp1/mandate.md" ]

d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
mkdir -p "$d/town/government" "$d/town/missions/alpha" "$d/town/missions/bravo" "$d/state"
cp "$repo/government/mission-cycle.sh" "$d/town/government/mission-cycle.sh"

cat > "$d/town/missions/alpha/cycle.sh" <<'HOOK'
#!/bin/sh
printf '%s\n' "alpha ran" > "$VICHE_STATE_ROOT/alpha-success"
HOOK
cat > "$d/town/missions/bravo/cycle.sh" <<'HOOK'
#!/bin/sh
echo "deliberate failure" >&2
exit 9
HOOK
VICHE_TOWN_ROOT="$d/town" VICHE_STATE_ROOT="$d/state" \
    /bin/sh "$d/town/government/mission-cycle.sh"
n=0
while [ ! -f "$d/state/alpha-success" ] && [ "$n" -lt 50 ]; do
    sleep .04
    n=$((n+1))
done
[ "$(cat "$d/state/alpha-success")" = "alpha ran" ]
[ -s "$d/state/missions/alpha/cycle.lock" ] || [ -f "$d/state/missions/alpha/cycle.lock" ]
[ -f "$d/state/missions/bravo/cycle.lock" ]
echo 'Task-independent mission dispatch and error isolation passed'

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
printf '%s\n' "alpha ran" > "$VICHE_STATE_ROOT/alpha-success.tmp"
mv "$VICHE_STATE_ROOT/alpha-success.tmp" "$VICHE_STATE_ROOT/alpha-success"
HOOK
cat > "$d/town/missions/bravo/cycle.sh" <<'HOOK'
#!/bin/sh
echo "deliberate failure" >&2
exit 9
HOOK
VICHE_TOWN_ROOT="$d/town" VICHE_STATE_ROOT="$d/state" \
    /bin/sh "$d/town/government/mission-cycle.sh"
# These production hooks are deliberately asynchronous. Await the expected
# content and the deliberately failing sibling's observed outcome, not the
# existence of an empty file opened before its writer was scheduled.
await_hook() {
    file=$1 expected=$2
    deadline=$(($(date +%s) + 30))
    until [ -f "$file" ] && grep -Fxq "$expected" "$file"; do
        if [ "$(date +%s)" -ge "$deadline" ]; then
            echo "mission-boundary: timed out waiting for $expected in $file" >&2
            [ ! -f "$file" ] || cat "$file" >&2
            return 1
        fi
        sleep .05
    done
}
await_hook "$d/state/alpha-success" "alpha ran"
await_hook "$d/state/missions/bravo/cycle.log" "Viche: mission bravo hook failed; retry next cycle"
[ -f "$d/state/missions/alpha/cycle.lock" ] || { echo 'alpha cycle lock missing' >&2; exit 1; }
[ -f "$d/state/missions/bravo/cycle.lock" ] || { echo 'bravo cycle lock missing' >&2; exit 1; }
echo 'Task-independent mission dispatch and error isolation passed'

cat > "$d/town/missions/alpha/executive.sh" <<'HOOK'
#!/bin/sh
printf '%s\n' "executive alpha ran" > "$VICHE_STATE_ROOT/alpha-executive.tmp"
mv "$VICHE_STATE_ROOT/alpha-executive.tmp" "$VICHE_STATE_ROOT/alpha-executive"
HOOK
echo 'standing order' > "$d/town/missions/alpha/mandate.md"
cat > "$d/town/missions/bravo/executive.sh" <<'HOOK'
#!/bin/sh
touch "$VICHE_STATE_ROOT/bravo-unauthorized"
HOOK
VICHE_TOWN_ROOT="$d/town" VICHE_STATE_ROOT="$d/state" \
    /bin/sh "$d/town/government/mission-cycle.sh" executive
await_hook "$d/state/alpha-executive" "executive alpha ran"
[ -f "$d/state/missions/alpha/executive.lock" ] || { echo 'alpha Executive lock missing' >&2; exit 1; }
# The non-mandated mission must not even be scheduled. Checking its lock
# prevents a false pass from a delayed unauthorized background process.
[ ! -e "$d/state/missions/bravo/executive.lock" ] || { echo 'unauthorized bravo Executive hook scheduled' >&2; exit 1; }
[ ! -e "$d/state/bravo-unauthorized" ] || { echo 'unauthorized bravo Executive hook ran' >&2; exit 1; }
echo 'Executive standing orders are independent and require a mission mandate'

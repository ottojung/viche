#!/bin/sh
# Operational bootstrap: keep authorized offices available; leave judgment to agents.
# The Founder-controlled constitutional bootstrap continues to own Parliament.
set -eu
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
seats=${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
mkdir -p "$seats/branches" "$state"
[ -s "$town/government/LAWS.md" ] || exit 1
[ -s "$town/government/seats.tsv" ] || exit 1
[ -s "${VICHE_CONSTITUTION:-/var/lib/lubko/from-host/viche-constitution/CONSTITUTION.md}" ] || exit 1

# Worktree creation is substrate work, not a decision about what Parliament does.
tab=$(printf '\t')
while IFS="$tab" read -r seat title focus; do
    [ -n "$seat" ] || continue
    target=$seats/$seat
    if [ ! -f "$target/.git" ] && [ ! -d "$target/.git" ]; then
        if [ -e "$target" ] && [ -n "$(ls -A "$target")" ]; then
            echo "Occupied parliamentary worktree: $target" >&2
            continue
        fi
        git -C "$town" worktree add --detach "$target" HEAD ||
            echo "Cannot create $seat worktree; preserve existing state" >&2
    fi
done < "$town/government/seats.tsv"

# No script may adjudicate what offices should investigate, repair or deliver.
# Each role keeps its own journal; the independent Recovery Steward handles
# uncertain terminal invocations without replaying their tools or messages.
for office in executive judiciary; do
    /bin/sh "$town/government/agentic-office.sh" "$office" ||
        echo "Office $office needs general-purpose recovery" >&2
done

if grep -Eq '^## Act [0-9]+ — Executive Innovation Office Act \(enacted ' "$town/government/LAWS.md"; then
    innovation_authority=executive
else
    innovation_authority=legislature
fi
/bin/sh "$town/government/agentic-office.sh" innovation-centre "$innovation_authority" ||
    echo "Innovation office needs independent investigation" >&2

# Marker records only that the launcher ran, never that the Town is healthy.
date +%s > "$state/launcher-last-attempt"

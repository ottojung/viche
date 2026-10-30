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
    # Legal Act 19 physical continuity: preserve evidence and apply lawful
    # threshold/cooldown gate; agents, not this launcher, decide substantive work.
    if [ -f "$town/government/seat-liveness.sh" ]; then
        /bin/sh "$town/government/seat-liveness.sh" "$seat" ||
            echo "Seat $seat requires independent continuity investigation" >&2
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

# Act 18 generated status index, Act 15 inexpensive independent monitoring,
# and Act 12 territory maintenance are mechanical obligations, not decisions
# about what agents should repair or whether a task was delivered.
if [ -f "$town/government/board-trail-refresh.sh" ]; then
    /bin/sh "$town/government/board-trail-refresh.sh" ||
        echo 'Board-trail collection requires attention' >&2
fi
if [ -f "$town/government/judiciary-measurements.py" ]; then
    python3 "$town/government/judiciary-measurements.py" ||
        echo 'Judiciary metrics collection unavailable' >&2
fi
if [ -f "$town/government/oversight-watch.sh" ]; then
    /bin/sh "$town/government/oversight-watch.sh" ||
        echo 'Independent oversight observation unavailable' >&2
fi
# Retain the deterministic capacity safeguard under Act 12. Existing Janitor
# quarantine and destructive capabilities remain subject to that Act.
if [ -f "$town/government/janitor.sh" ]; then
    mkdir -p "$state/janitor"
    (/bin/sh "$town/government/janitor.sh" cycle ||
        echo 'Janitor cycle requires investigation' >&2) >> "$state/janitor/boot-cycle.log" 2>&1 </dev/null &
fi

# These stamps mean only that bootstrap was ATTEMPTED, never that delivery or
# institutional health is verified. The legacy Sentinel reads the latter.
now=$(date +%s)
printf '%s
' "$now" > "$state/launcher-last-attempt"
mkdir -p "$state/health"
printf '%s
' "$now" > "$state/health/government-setup.last"

#!/bin/sh
# One generic, intentionally small, availability-only launcher for ordinary offices.
# No outcome inference, automatic retry of uncertain actions, or scripted diagnosis.
set -eu
[ "$#" -ge 1 ] && [ "$#" -le 2 ] || exit 2
office=$1
case "$office" in executive|judiciary|innovation-centre) : ;; *) exit 2 ;; esac
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
seats=${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
charter=${VICHE_CONSTITUTION:-/var/lib/lubko/from-host/viche-constitution/CONSTITUTION.md}
[ -s "$charter" ] || { echo 'Missing Founder charter' >&2; exit 1; }
[ -s "$town/government/AGENTIC-OPERATIONS.md" ] || exit 1
case "$office" in
    executive) title=Executive; authority=executive ;;
    judiciary) title=Judiciary; authority=judiciary ;;
    innovation-centre)
        authority=${2:-legislature}
        case "$authority" in
            legislature) title='Legislative Innovation Centre' ;;
            executive) title='Executive Innovation Office' ;;
            *) exit 2 ;;
        esac ;;
esac
cwd=$seats/branches/$office
mkdir -p "$seats/branches" "$state/office-journals"
if [ ! -f "$cwd/.git" ] && [ ! -d "$cwd/.git" ]; then
    [ ! -e "$cwd" ] || { echo "Occupied worktree: $cwd" >&2; exit 1; }
    git -C "$town" worktree add --detach "$cwd" HEAD
fi
id=$(/bin/sh "$town/government/appointments.sh" ensure "$office") || exit 1
meta=$(antonina agent status --id "$id" --json) || exit 1
mode=$(printf '%s\n' "$meta" | jq -er '.state') || exit 1
case "$mode" in
    running) exit 0 ;;
    idle|clearexit) : ;;
    failed|stopped|killed)
        echo "$title has terminal appointee $id ($mode); Recovery Steward must reconcile and replace, never replay" >&2
        exit 1 ;;
    *) echo "Unrecognized agent state $mode; keep evidence" >&2; exit 1 ;;
esac

# Deterministic physical safety, not a productivity quota or scheduling decision.
if [ -f "$town/government/resource-safety.sh" ]; then
    /bin/sh "$town/government/resource-safety.sh" "$office" || exit 1
fi

# Each invocation is a fresh assessment, not a continuation or a replay recipe.
# The journal is an agent-owned obligation ledger, not a scripted health assertion.
prompt=$(cat <<EOF
=== AUTHORITATIVE FOUNDER CONSTITUTION ===
$(cat "$charter")
=== END CONSTITUTION ===

You are the $title, operating under $authority authority.
$(cat "$town/government/AGENTIC-OPERATIONS.md")

Your independent responsibility: $office.
Current ordinary laws: $town/government/LAWS.md.
Your worktree: $cwd.
Your durable responsibility journal: $state/office-journals/$office.md.
Institutional evidence and outstanding old cases: $state.
Founder Town Hall issue: ${VICHE_TOWNHALL_ID:-302}; Founder authored messages must be checked.
Existing agent ID: $id. Current agent state: $mode.
This is a fresh appointment assessment. Before external writes, inspect prior
actions, worktree state, board and logs. Never replay uncertain side effects.
For an unfamiliar problem, investigate and solve it with your own judgment.
Read the law and existing office mandate before acting; never assume a
procedural dashboard is a complete inventory of obligations.
EOF
)
antonina agent run --id "$id" --cwd "$cwd" --prompt "$prompt" --detach

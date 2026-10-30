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
        mkdir -p "$state/office-blockers"
        notice="$state/office-blockers/$office"
        printf 'office=%s agent=%s state=%s action=Recovery_Steward_reconcile_before_successor
' "$office" "$id" "$mode" > "$notice.tmp.$$"
        mv -f "$notice.tmp.$$" "$notice"
        mkdir -p "$state/office-blockers/cases"
        case_file="$state/office-blockers/cases/office-$office--agent-$id"
        if [ ! -e "$case_file" ]; then
            printf 'case_id=office-%s--agent-%s
owner=Executive_and_Recovery_Steward
evidence=original_Antonina_invocation_and_external_effects
independent_verifier=Judiciary
closure_gate=independent_verification_of_reconciled_effects
state=open
' "$office" "$id" > "$case_file.tmp.$$"
            mv "$case_file.tmp.$$" "$case_file"
        fi
        echo "$title has terminal appointee $id ($mode); Recovery Steward must reconcile and replace, never replay" >&2
        exit 1 ;;
    *) echo "Unrecognized agent state $mode; keep evidence" >&2; exit 1 ;;
esac

# Deterministic physical safety, not a productivity quota or scheduling decision.
if [ -f "$town/government/resource-safety.sh" ]; then
    /bin/sh "$town/government/resource-safety.sh" "$office" || exit 1
fi

# Act 19: preserve the actual durable handoff queue in each dispatch.
# Fail closed on a queue read failure, never silently supersede pending work.
[ -f "$town/government/handoff-queue.sh" ] || exit 1
handoffs=$(/bin/sh "$town/government/handoff-queue.sh" list-open "$town") || exit 1

# Each invocation is a fresh assessment, not a continuation or a replay recipe.
# The journal is an agent-owned obligation ledger, not a scripted health assertion.
prompt=$(cat <<EOF
=== AUTHORITATIVE FOUNDER CONSTITUTION ===
$(cat "$charter")
=== END CONSTITUTION ===

You are the $title, operating under $authority authority.
$(cat "$town/government/AGENTIC-OPERATIONS.md")

=== OPEN DURABLE HANDOFFS: MUST BE RECONCILED BEFORE NEW ASSIGNMENTS ===
$handoffs
=== END OPEN HANDOFFS ===
Your independent responsibility: $office.
Current ordinary laws: $town/government/LAWS.md.
Your worktree: $cwd.
Your durable responsibility journal: $state/office-journals/$office.md.
Institutional evidence: $state.
Pre-cutover corrective cases: $state/institutional-cases/index.json and $state/institutional-cases/*.json; preserve case identity until independent verification.
Live blocked appointments: $state/office-blockers/
Durable individualized new cases: $state/office-blockers/cases/
Before assigning unrelated work, investigate every pending appointment
blocker and hand off unresolved cases to the independent Recovery Steward.
Do not erase or mark these records closed based on a clean agent exit.
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

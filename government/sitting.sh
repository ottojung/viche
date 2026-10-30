#!/bin/sh
# A parliamentary agenda is a responsibility of the Clerk and Parliament.
# The constitutional bootstrap supplies identity and charter independently.
set -eu
[ "$#" -eq 1 ] || exit 2
seat=$1
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
seats=${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}
[ -s "$town/government/AGENTIC-OPERATIONS.md" ] || exit 1
# The protected constitutional bootstrap may call this for a terminal seat.
# Refuse uncertain reuse; only a reconciled, independently appointed successor
# may receive a fresh prompt. This is a safety invariant, not case diagnosis.
id=$(/bin/sh "$town/government/appointments.sh" resolve "$seat") || exit 1
meta=$(antonina agent status --id "$id" --json) || exit 1
mode=$(printf '%s\n' "$meta" | jq -er '.state') || exit 1
case "$mode" in
    idle|clearexit) : ;;
    running) echo "Seat $seat became active; refusing duplicate dispatch" >&2; exit 1 ;;
    failed|stopped|killed)
        # Act 23 section 9: fail closed but notify a lawful recovery owner.
        mkdir -p "$state/office-blockers"
        notice="$state/office-blockers/$seat"
        printf 'seat=%s agent=%s state=%s action=Clerk_and_Recovery_Steward_reconcile_before_successor
' "$seat" "$id" "$mode" > "$notice.tmp.$$"
        mv -f "$notice.tmp.$$" "$notice"
        echo "Seat $seat has terminal invocation $id; preserve effects for a fresh investigator" >&2
        exit 1 ;;
    *) echo "Seat $seat status unknown; refuse unsafe dispatch" >&2; exit 1 ;;
esac
# A small deterministic physical safety gate is appropriate, not policy judgment.
if [ -f "$town/government/resource-safety.sh" ]; then
    /bin/sh "$town/government/resource-safety.sh" "$seat" || exit 1
fi
[ -f "$town/government/handoff-queue.sh" ] || exit 1
handoffs=$(/bin/sh "$town/government/handoff-queue.sh" list-open "$town") || exit 1
blockers=
for f in "$state"/office-blockers/*; do
    [ -f "$f" ] || continue
    blockers="$blockers$(cat "$f")
"
done
cat <<EOF
$(cat "$town/government/AGENTIC-OPERATIONS.md")

You are parliamentary seat $seat. Preserve institutional continuity.
=== OPEN DURABLE HANDOFFS ===
$handoffs
=== END HANDOFFS ===
=== BLOCKED APPOINTMENTS: CLERK MUST RECONCILE ===
$blockers
=== END BLOCKERS ===
Read the current Constitution supplied separately and enacted LAWS.md.
Read the Town Hall (issue #${VICHE_TOWNHALL_ID:-302}), the current agenda,
records/AGENDA.md, records/SUMMONED.txt and records/summons/$seat.md.
Read durable obligations in $state/office-journals/$seat.md and the old
recovery evidence in $state/continuity and $state/appointments.
Review previously attempted actions, Git and board effects before acting;
never replay uncertain tools. Record unfinished work for successors.

Clerk: own intake, agenda, legitimate summons, recorded votes and
institutional communications, not Executive delivery decisions. Check
unresolved founder mandates and verify what actually happened. Summon other
parliamentary seats for genuine legislative business.

Before publishing any bill for ballots, run government/predict-gate.sh BILL_ID
for bills in the Act 22 pilot subset, and independently check registration.
Only after lawful registration and publication may Parliament
solicit individual ballots. Never enact a bill through a prompt alone.

Member: deliberate independently, verify arguments and evidence, record votes
under enacted procedural law, and challenge unsupported claims.
Parliament alone enacts law, including any change in office authority.
Judiciary audits independently; Executive performs lawful operational repairs.
The Innovation Centre remains legislative until a valid enactment transfers it.

No report or process exit is proof of successful governance. Do not make work
for yourself simply to satisfy process metrics. Continue independently until
your concrete obligations are discharged, blocked with evidence, or handed off.
EOF

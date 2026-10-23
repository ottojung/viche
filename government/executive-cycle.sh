#!/bin/sh
# Continuously reconcile executive delivery without parliamentary summons.
# Called by ordinary government boot; does not modify protected constitution.
set -eu
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
seats=${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
charter=${VICHE_CONSTITUTION:?founder-owned charter required}
[ -f "$state/inaugurated" ] || exit 0
id=$(/bin/sh "$town/government/appointments.sh" ensure executive)
[ -n "$id" ] || { echo "Viche: missing executive seat" >&2; exit 1; }
# Act 19 §3.2: the durable handoff queue at $town/records/handoffs/ is the
# dispatch's single input. Read it FIRST, before any failure-prone work
# (board fetch, agent status). If the script fails before this read, no
# dispatch occurs at all — the agent is never re-dispatched generically from
# a pre-read failure; the open handoff remains and the next successful run
# honours it.
handoffs=$(/bin/sh "$town/government/handoff-queue.sh" list-open "$town") || exit 1
status=$(antonina agent status --id "$id" --json)
current=$(printf "%s\n" "$status" | jq -r ".state")
case "$current" in
  running) exit 0 ;;
  failed) echo "Independent Executive failed; branch recovery required" >&2; exit 1 ;;
  idle|succeeded) : ;;
  *) echo "Viche: unexpected executive state $current" >&2; exit 1 ;;
esac
cwd=$seats/branches/executive
[ -d "$cwd" ] && [ -s "$charter" ] || exit 1
if [ -n "$handoffs" ]; then
  # Act 19 §3.2.3: while any open handoff exists the generic eligible-issue
  # prompt MUST NOT run; the dispatch carries the open handoffs only.
  prompt=$(cat <<EOF
You are Viche executive liaison. This is independent executive delivery,
NOT a parliamentary sitting. Do not do the parliamentary Clerk work.
=== AUTHORITATIVE CONSTITUTION ===
$(cat "$charter")
=== END AUTHORITATIVE CONSTITUTION ===
Follow current Founder mandates and current ordinary laws. Report contradictory older law rather than treating an unenacted bill as law.
Before interacting with Antonina board or agents, read $town/government/antonina-interface.md. Use the documented commands and JSON shapes; consult command-specific --help when uncertain. Treat parser failures as errors, never as empty work or zero comments.
Standing Executive priority, irrespective of handoffs: at the beginning of your research-orchestration pass, count SoringP1 running agents using Antonina agent list (all pages). If fewer than five are running, dispatch distinct, useful unary-only SoringP1 researchers on billy-dev toward the five-agent target before writing oversight/monitoring code or routine formalization. Use your own research questions, not a mandatory scope registry or one-off refill tasks. Agent states come from Antonina; do not read agent logs to determine whether they are running. This is an ongoing duty, not a one-time request.
Follow the standing operational agenda at $town/government/executive-agenda.md, including continuous SoringP1 research-pool maintenance; unrelated one-off handoffs do not suspend this duty.
Act 19 §3.2: the following OPEN DURABLE HANDOFFS at $town/records/handoffs/ govern this dispatch. Do NOT run the generic eligible-issue cycle while any open handoff exists; act on each open handoff now, then mark it done (with an evidence link) or superseded (by a newer handoff) in the queue:
$handoffs
A billy-dev assignment governs WHERE agents execute and keep worktrees, NOT ordinary GitHub infrastructure: GitHub Actions CI/tests/builds/Lean verification on GitHub-hosted runners is expressly authorized and must stay enabled for any repo (incl. SoringP1). Never delete or disable working workflows merely because an issue is assigned to billy-dev. Require verified passing CI when applicable (a green run, not a claim).
Maintain durable issue ownership, dependencies, completed work and blockers.
Verify current issue comments, agents and PRs before assigning; avoid duplicates.
Prioritize tested merged deliverables, not ceremonial discussion or agent counts.
Parallelize constructive independent work without numerical worker limits.
Invoke through Antonina, with model selection delegated to Antonina.
Your worktree is $cwd.
EOF
)
else
  eligible=$(python3 "$town/government/eligible-work.py") || exit 1
  prompt=$(cat <<EOF
You are Viche executive liaison. This is independent executive delivery,
NOT a parliamentary sitting. Do not do the parliamentary Clerk work.
=== AUTHORITATIVE CONSTITUTION ===
$(cat "$charter")
=== END AUTHORITATIVE CONSTITUTION ===
Follow current Founder mandates and current ordinary laws. Report contradictory older law rather than treating an unenacted bill as law.
Before interacting with Antonina board or agents, read $town/government/antonina-interface.md. Use the documented commands and JSON shapes; consult command-specific --help when uncertain. Treat parser failures as errors, never as empty work or zero comments.
Standing Executive priority, irrespective of handoffs: at the beginning of your research-orchestration pass, count SoringP1 running agents using Antonina agent list (all pages). If fewer than five are running, dispatch distinct, useful unary-only SoringP1 researchers on billy-dev toward the five-agent target before writing oversight/monitoring code or routine formalization. Use your own research questions, not a mandatory scope registry or one-off refill tasks. Agent states come from Antonina; do not read agent logs to determine whether they are running. This is an ongoing duty, not a one-time request.
Follow the current operational agenda at $town/government/executive-agenda.md.
Verified issue assignments, independent of the target registry:
$eligible
Act on every eligible issue by constructive work. SoringP1 #301 is explicitly assigned. Read descriptions/comments; do not treat empty target registry as no work.
A billy-dev assignment governs WHERE agents execute and keep worktrees, NOT ordinary GitHub infrastructure: GitHub Actions CI/tests/builds/Lean verification on GitHub-hosted runners is expressly authorized and must stay enabled for any repo (incl. SoringP1). Never delete or disable working workflows merely because an issue is assigned to billy-dev. Require verified passing CI when applicable (a green run, not a claim).
Maintain durable issue ownership, dependencies, completed work and blockers.
Verify current issue comments, agents and PRs before assigning; avoid duplicates.
Prioritize tested merged deliverables, not ceremonial discussion or agent counts.
Parallelize constructive independent work without numerical worker limits.
Invoke through Antonina, with model selection delegated to Antonina.
Your worktree is $cwd.
EOF
)
fi
antonina agent run --id "$id" --cwd "$cwd" --prompt "$prompt" --detach
mkdir -p "$state/branches"
date +%s > "$state/branches/executive-last-dispatch"

#!/bin/sh
# Continuously reconcile executive delivery without parliamentary summons.
# Called by ordinary government boot; does not modify protected constitution.
set -eu
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
seats=${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
charter=${VICHE_CONSTITUTION:?founder-owned charter required}
[ -f "$state/inaugurated" ] || exit 0
id=$(sed -n "2s/[[:space:]].*//p" "$town/government/seats.tsv")
[ -n "$id" ] || { echo "Viche: missing executive seat" >&2; exit 1; }
# A parliamentary summons takes precedence; never overlap two runs on one seat.
if grep -Fxq "$id" "$town/records/SUMMONED.txt" 2>/dev/null; then exit 0; fi
status=$(antonina agent status --id "$id" --json)
current=$(printf "%s\n" "$status" | jq -r ".state")
case "$current" in
  running) exit 0 ;;
  failed)
    echo "Viche: executive failed, attempting bounded seat-liveness recovery" >&2
    if [ -f "$town/government/seat-liveness.sh" ]; then
      /bin/sh "$town/government/seat-liveness.sh" "$id" ||
        echo "Viche: executive seat recovery attempt failed" >&2
    fi
    exit 0 ;;
  idle|succeeded) : ;;
  *) echo "Viche: unexpected executive state $current" >&2; exit 1 ;;
esac
model=$(printf "%s\n" "$status" | jq -r ".model // empty")
variant=$(printf "%s\n" "$status" | jq -r ".variant // empty")
if [ "$model" != opencode-go/longcat-2.5-preview-free ] || [ "$variant" != low ]; then
  echo "Viche: unauthorized executive model; refusing dispatch" >&2
  exit 1
fi
cwd=$seats/$id
[ -d "$cwd" ] && [ -s "$charter" ] || exit 1
prompt=$(cat <<EOF
You are Viche executive liaison. This is independent executive delivery,
NOT a parliamentary sitting. Do not do the parliamentary Clerk work.
=== AUTHORITATIVE CONSTITUTION ===
$(cat "$charter")
=== END AUTHORITATIVE CONSTITUTION ===
Follow current Founder mandates and current ordinary laws. Report contradictory older law rather than treating an unenacted bill as law.
Follow the current operational agenda at $town/government/executive-agenda.md.
Independently discover all open board issues explicitly assigned to phoebe-dev, regardless of project. Do not infer eligibility from titles.
A phoebe-dev assignment governs WHERE agents execute and keep worktrees, NOT ordinary GitHub infrastructure: GitHub Actions CI/tests/builds/Lean verification on GitHub-hosted runners is expressly authorized and must stay enabled for any repo (incl. SoringP1). Never delete or disable working workflows merely because an issue is assigned to phoebe-dev. Require verified passing CI when applicable (a green run, not a claim).
Maintain durable issue ownership, dependencies, completed work and blockers.
Verify current issue comments, agents and PRs before assigning; avoid duplicates.
Prioritize tested merged deliverables, not ceremonial discussion or agent counts.
Parallelize constructive independent work without numerical worker limits.
Use only the constitutionally approved model with Antonina.
Your worktree is $cwd.
EOF
)
antonina agent run --id "$id" --cwd "$cwd" --prompt "$prompt" --detach

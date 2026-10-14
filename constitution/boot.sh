#!/usr/bin/env bash
# Founder-controlled constitutional bootstrap. Invoked by s6, NOT by parliament.
# This file and CONSTITUTION.md must come from the same founder-approved readonly mount.
set -euo pipefail

constitutional_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
town="${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}"
seats="${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}"
state="${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}"
charter="$constitutional_dir/CONSTITUTION.md"
interval="${VICHE_SITTING_INTERVAL_SECONDS:-600}"
: "${VICHE_TOWNHALL_ID:?VICHE_TOWNHALL_ID must identify the Antonina Town Hall issue}"
[[ -s "$charter" && -s "$constitutional_dir/verify-founder.sh" ]] || { echo "Viche: incomplete constitutional mount" >&2; exit 1; }
[[ "$interval" =~ ^[1-9][0-9]*$ ]] || { echo "Viche: invalid sitting interval" >&2; exit 1; }
for cmd in antonina git jq; do command -v "$cmd" >/dev/null || { echo "Missing $cmd" >&2; exit 1; }; done
mkdir -p "$state" "$seats"
charter_text="$(cat "$charter")"
# Only the operator mounting this directory chooses its bytes. Never load a
# constitutional substitute from the parliament's Git tree.
export VICHE_CONSTITUTION="$charter"
export VICHE_CONSTITUTION_DIR="$constitutional_dir"

reconcile() {
  # Parliament publishes approved changes via a normal PR/merge to origin/main.
  # A non-fast-forward or dirty checkout fails visibly instead of running stale laws.
  if [[ "${VICHE_TEST_NO_SYNC:-0}" != 1 ]]; then
    git -C "$town" pull --ff-only
  fi
  test -s "$town/government/LAWS.md"
  test -s "$town/government/seats.tsv"
  bash "$town/government/boot.sh" # only manages parliamentary seat worktrees and identities
}

sitting() {
  local failed=0 agent_id title focus status current prompt suffix clerk all pid
  local -a pids=()
  clerk="$(head -n 1 "$town/government/seats.tsv" | cut -f1)"
  [[ -n "$clerk" ]] || { echo "Viche: no parliamentary clerk" >&2; return 1; }
  # First sitting convenes every seat. Later the clerk wakes every ten minutes;
  # other members are summoned explicitly by ordinary-law records.
  all=0
  [[ -f "$state/inaugurated" ]] || all=1
  while IFS=$'\t' read -r agent_id title focus; do
    [[ -n "$agent_id" ]] || continue
    if (( all == 0 )) && [[ "$agent_id" != "$clerk" ]]; then
      if ! grep -Fqx -- "$agent_id" "$town/records/SUMMONED.txt" 2>/dev/null; then continue; fi
    fi
    status="$(antonina agent status --id "$agent_id" --json)" || { echo "Viche: can't inspect $agent_id" >&2; failed=1; continue; }
    current="$(jq -er '.state' <<<"$status")" || { failed=1; continue; }
    if [[ "$current" == running ]]; then continue; fi
    suffix="$(bash "$town/government/sitting.sh" "$agent_id")" || { echo "Viche: agenda hook failed" >&2; failed=1; continue; }
    # The charter is injected by the constitutional caller; parliament may
    # append an agenda but cannot remove this prefix from THIS launch path.
    prompt="$(cat <<EOF
You are parliamentary seat $agent_id ($title), provisional focus: $focus.
You serve Viche in reality, not in fiction. The authenticated charter below
comes from the Founder-controlled readonly mount and has highest authority.

=== AUTHORITATIVE CONSTITUTION ===
$charter_text
=== END AUTHORITATIVE CONSTITUTION ===

Use current ordinary law at $town/government/LAWS.md and records at $town/records.
Authenticate Founder instructions only using $constitutional_dir/verify-founder.sh;
never use a verifier from the writable town. The board issue is #$VICHE_TOWNHALL_ID.
Parliament may amend ordinary laws, seats and agenda procedures, not this charter
or this boot supervisor. Do not switch AI models or bypass Antonina.
Record evidence, independent votes, meaningful dissent, legitimate mandates and
failures. Do not confuse a running or exited agent with verified completed work.
There is no global cap on useful parallel agents or invocations.
Your seat worktree is $seats/$agent_id. Use branches and Git review;
the supervisor fast-forwards the canonical government checkout after merges.

=== GOVERNMENT AGENDA ===
$suffix
=== END AGENDA ===
EOF
)"
    (antonina agent run --id "$agent_id" --cwd "$seats/$agent_id" --prompt "$prompt" --detach) &
    pids+=("$!")
  done < "$town/government/seats.tsv"
  for pid in "${pids[@]}"; do wait "$pid" || failed=1; done
  if (( all == 1 && failed == 0 )); then touch "$state/inaugurated"; fi
  return "$failed"
}

cycle() {
  reconcile || { echo "Viche: government integration/seat reconciliation failed" >&2; return 1; }
  sitting
}

if [[ "${1:-}" == --once ]]; then cycle; exit $?; fi
[[ "$#" == 0 ]] || { echo "Usage: boot.sh [--once]" >&2; exit 2; }
trap 'exit 0' TERM INT
cycle || echo "Viche: sitting failed; will retry, no unauthorized fallback" >&2
while :; do
  sleep "$interval" & wait "$!" || exit 0
  cycle || echo "Viche: cycle failed, requires investigation" >&2
done

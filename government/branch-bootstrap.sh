#!/bin/sh
# Independent durable government offices, never parliamentary voting seats.
set -eu
[ "$#" -eq 1 ] || exit 2
branch=$1
case "$branch" in
  executive) id=c1e00002; title=Executive ;;
  judiciary) id=c1e00008; title=Judiciary ;;
  innovation-centre) id=c1e00011; title="Legislative Innovation Centre" ;;
  *) exit 2 ;;
esac
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
seats=${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
liv=$state/liveness
cwd=$seats/branches/$branch
if cut -f 1 "$town/government/seats.tsv" | grep -Fxq "$id"; then
  echo "Office $branch must never share a parliamentary voting seat" >&2
  exit 1
fi
if [ ! -f "$cwd/.git" ] && [ ! -d "$cwd/.git" ]; then
  if [ -d "$cwd" ] && [ -n "$(ls -A "$cwd")" ]; then
    echo "Refusing to replace occupied office worktree: $cwd" >&2
    exit 1
  fi
  mkdir -p "$(dirname "$cwd")"
  git -C "$town" worktree add --detach "$cwd" HEAD
fi
. "$(CDPATH= cd "$(dirname "$0")" && pwd -P)/office-continuity.sh"
mkdir -p "$liv"
umask 077
id=$(/bin/sh "$town/government/appointments.sh" ensure "$branch")
meta=$(antonina agent status --id "$id" --json)
now=$(date +%s)
mode=$(printf '%s\n' "$meta" | jq -r '.state')
reason=$(printf '%s\n' "$meta" | jq -r '.backend_error.classification // ""')
tflag=$(printf '%s\n' "$meta" | jq -r '.backend_error.transient // false')
if [ "$mode" = failed ]; then
  if oc_is_transient "$reason" "$tflag"; then
    oc_record_failure "$liv" "$id" "$reason" "$now" "$cwd"
  else
    oc_surface_permanent "$liv" "$id" "$reason"
  fi
fi
oc_commit_age_signal "$liv" "$id" "$cwd" "$now"
# Act 19 §3.1: the reset decision is decidable from the failure record alone
# and does not depend on the currently-observed state. An oscillating agent
# (failed -> re-dispatched -> running) is reset once it accumulates the
# threshold of consecutive transient failures inside the window.
if oc_reset_due "$liv" "$id" "$now"; then
  snapshot=$(mktemp -d "$liv/branch-$id-recovery-XXXXXX")
  printf '%s\n' "$meta" > "$snapshot/status.json"
  antonina agent log --id "$id" --lines 200 > "$snapshot/log.txt" 2>&1 || :
  git -C "$cwd" status --short > "$snapshot/worktree.txt"
  printf '%s\n' "$now" > "$liv/last-reset-$id"
  id=$(/bin/sh "$town/government/appointments.sh" replace "$branch")
  meta=$(antonina agent status --id "$id" --json)
  oc_clear_failures "$liv" "$id"
  printf '%s branch=%s session_reset=failure_count threshold=%s window=%s cooldown=%s evidence=%s\n' \
    "$(date -u +%FT%TZ)" "$branch" "$oc_threshold" "$oc_window" "$oc_cooldown" "$snapshot" \
    >> "$liv/recoveries.log"
fi
model=$(printf '%s\n' "$meta" | jq -r '.model // empty')
variant=$(printf '%s\n' "$meta" | jq -r '.variant // empty')
if [ "$model" != opencode-go/longcat-2.5-preview-free ] || [ "$variant" != low ]; then
  echo "Office $branch has unauthorized model; refusing dispatch" >&2
  exit 1
fi

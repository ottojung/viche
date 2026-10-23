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
invocation=$(printf '%s\n' "$meta" | jq -r '.invocation_id // .run_id // .finished_at // ""')
finished=$(printf '%s\n' "$meta" | jq -r '.finished_at // ""')
if [ "$mode" = failed ]; then
  if oc_is_transient "$reason" "$tflag"; then
    unsafe=$(printf '%s\n' "$meta" | jq -r 'if .backend_error.automatic_retry_safe == false then "yes" else "no" end')
    retry_safe=$(printf '%s\n' "$meta" | jq -r 'if .backend_error.automatic_retry_safe == true and .backend_error.transient == true then "yes" else "no" end')
    oc_record_failure "$liv" "$branch" "$id" "$invocation" "$reason" "$finished" "$retry_safe" "$now" "$cwd" || exit 1
    [ "$retry_safe" = yes ] || oc_mark_unsafe_hold "$liv" "$branch" "$id" "$invocation"
  else
    oc_surface_permanent "$liv" "$id" "$reason"
  fi
fi
oc_commit_age_signal "$liv" "$id" "$cwd" "$now"
# Act 19 §3.1: the reset decision is decidable from the failure record alone
# and does not depend on the currently-observed state. An oscillating agent
# (failed -> re-dispatched -> running) is reset once it accumulates the
# threshold of consecutive transient failures inside the window.
oc_worktree=$cwd
reset_due=false
if oc_reset_due "$liv" "$branch" "$now"; then reset_due=true; fi
if [ "$reset_due" = true ]; then
  snapshot=$(mktemp -d "$liv/branch-$id-recovery-XXXXXX")
  printf '%s\n' "$meta" > "$snapshot/status.json"
  antonina agent log --id "$id" --lines 200 > "$snapshot/log.txt" 2>&1 || :
  git -C "$cwd" status --short > "$snapshot/worktree.txt"
  oc_quiesce_for_reset "$id" || exit 1
  id=$(/bin/sh "$town/government/appointments.sh" replace "$branch" "$id")
  printf '%s\n' "$now" > "$liv/last-reset-$branch"
  meta=$(antonina agent status --id "$id" --json)
  oc_clear_failures "$liv" "$branch"
  printf '%s branch=%s session_reset=failure_count threshold=%s window=%s cooldown=%s evidence=%s\n' \
    "$(date -u +%FT%TZ)" "$branch" "$oc_threshold" "$oc_window" "$oc_cooldown" "$snapshot" \
    >> "$liv/recoveries.log"
  reset_due=true
  # The single replacement above completed this reset. Never create a
  # second appointment for the same threshold event.
fi
# Antonina selects the provider/model/variant under its own current policy.
# Appointment validity is determined by the managed agent state, not a pin.

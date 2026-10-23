#!/bin/sh
# Recover failed non-Clerk parliamentary sessions; retain their Git worktrees.
set -eu
[ "$#" -eq 1 ] || exit 2
seat_id=$1
case "$seat_id" in ''|*[!0123456789abcdef]*) exit 2;; esac
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
seats=${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}
root=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}/liveness
title=$(awk -F '\t' -v id="$seat_id" '$1==id {print $2; found=1; exit} END {if(!found) exit 1}' "$town/government/seats.tsv")
[ -n "$title" ] || exit 1
id=$(/bin/sh "$town/government/appointments.sh" ensure "$seat_id")
meta=$(antonina agent status --id "$id" --json)
mode=$(printf '%s\n' "$meta" | jq -r '.state')
reason=$(printf '%s\n' "$meta" | jq -r '.backend_error.classification // ""')
mkdir -p "$root"
. "$(CDPATH= cd "$(dirname "$0")" && pwd -P)/office-continuity.sh"
now=$(date +%s)
tflag=$(printf '%s\n' "$meta" | jq -r '.backend_error.transient // false')
invocation=$(printf '%s\n' "$meta" | jq -r '.invocation_id // .run_id // .finished_at // ""')
finished=$(printf '%s\n' "$meta" | jq -r '.finished_at // ""')
if [ "$mode" != failed ]; then
  oc_commit_age_signal "$root" "$id" "$seats/$seat_id" "$now"
  exit 0
fi
if ! oc_is_transient "$reason" "$tflag"; then
  oc_surface_permanent "$root" "$id" "$reason"
  exit 0
fi
retry_safe=$(printf '%s\n' "$meta" | jq -r 'if .backend_error.automatic_retry_safe == false then "no" else "yes" end')
oc_record_failure "$root" "$seat_id" "$id" "$invocation" "$reason" "$finished" "$retry_safe" "$now" "$seats/$seat_id"
[ "$retry_safe" = yes ] || oc_mark_unsafe_hold "$root" "$seat_id" "$id" "$invocation"
oc_commit_age_signal "$root" "$id" "$seats/$seat_id" "$now"
oc_worktree=$seats/$seat_id
oc_reset_due "$root" "$seat_id" "$now" || exit 0
umask 077
seat="$seats/$seat_id"
[ -d "$seat" ] || exit 1
snapshot=$(mktemp -d "$root/recovery-$id-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")
printf '%s\n' "$meta" > "$snapshot/agent-status.json"
antonina agent log --id "$id" --lines 200 > "$snapshot/agent-log-tail.txt" 2>&1 || :
git -C "$seat" status --short > "$snapshot/worktree-status.txt"
git -C "$seat" rev-parse HEAD > "$snapshot/worktree-head.txt"
printf '%s\n' "$now" > "$root/last-reset-$seat_id"
id=$(/bin/sh "$town/government/appointments.sh" replace "$seat_id" "$id")
oc_clear_failures "$root" "$seat_id"
printf '%s seat=%s session_reset=failure_count threshold=%s window=%s cooldown=%s evidence=%s\n' \
  "$(date -u +%FT%TZ)" "$seat_id" "$oc_threshold" "$oc_window" "$oc_cooldown" "$snapshot" >> "$root/recoveries.log"

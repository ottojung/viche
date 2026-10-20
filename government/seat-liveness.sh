#!/bin/sh
# Recover failed non-Clerk parliamentary sessions; retain their Git worktrees.
set -eu
[ "$#" -eq 1 ] || exit 2
seat_id=$1
id=$(/bin/sh "${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}/government/appointments.sh" ensure "$seat_id")
case "$seat_id" in ''|*[!0123456789abcdef]*) exit 2;; esac
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
seats=${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}
root=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}/liveness
clerk=$(head -n 1 "$town/government/seats.tsv" | cut -f1)
[ "$seat_id" != "$clerk" ] || exit 0
title=$(awk -F '\t' -v id="$seat_id" '$1==id {print $2; found=1; exit} END {if(!found) exit 1}' "$town/government/seats.tsv")
[ -n "$title" ] || exit 1
meta=$(antonina agent status --id "$id" --json)
mode=$(printf '%s\n' "$meta" | jq -r '.state')
reason=$(printf '%s\n' "$meta" | jq -r '.backend_error.classification // ""')
[ "$mode" = failed ] && [ "$reason" = upstream_endpoint_unavailable ] || exit 0
mkdir -p "$root"
umask 077
now=$(date +%s)
last=0
marker="$root/last-reset-$id"
[ ! -s "$marker" ] || last=$(cat "$marker")
case "$last" in ''|*[!0-9]*) last=0;; esac
[ $((now-last)) -ge 1800 ] || exit 0
seat="$seats/$seat_id"
[ -d "$seat" ] || exit 1
snapshot=$(mktemp -d "$root/recovery-$id-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")
printf '%s\n' "$meta" > "$snapshot/agent-status.json"
antonina agent log --id "$id" --lines 200 > "$snapshot/agent-log-tail.txt" 2>&1 || :
git -C "$seat" status --short > "$snapshot/worktree-status.txt"
git -C "$seat" rev-parse HEAD > "$snapshot/worktree-head.txt"
printf '%s\n' "$now" > "$marker"
id=$(/bin/sh "$town/government/appointments.sh" replace "$seat_id")
printf '%s seat=%s session_reset=endpoint_unavailable evidence=%s\n' "$(date -u +%FT%TZ)" "$id" "$snapshot" >> "$root/recoveries.log"

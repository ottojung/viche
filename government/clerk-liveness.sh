#!/bin/sh
# Recover a terminally failed Clerk while retaining all work and evidence.
# The only model remains the one configured by Antonina's constitutional boot.
set -eu
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
seats=${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}/liveness
mkdir -p "$state"
umask 077
id=$(head -n 1 "$town/government/seats.tsv" | cut -f1)
[ -n "$id" ] || exit 1
metadata=$(antonina agent status --id "$id" --json)
kind=$(printf '%s\n' "$metadata" | jq -r '.state')
reason=$(printf '%s\n' "$metadata" | jq -r '.backend_error.classification // ""')
[ "$kind" = failed ] || exit 0
[ "$reason" = upstream_endpoint_unavailable ] || exit 0
now=$(date +%s)
last=0
[ ! -s "$state/last-reset" ] || last=$(cat "$state/last-reset")
case "$last" in ''|*[!0-9]*) last=0;; esac
[ $((now-last)) -ge 1800 ] || exit 0
[ -d "$seats/$id" ] || exit 1
snapshot="$state/recovery-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir "$snapshot"
printf '%s\n' "$metadata" > "$snapshot/agent-status.json"
antonina agent log --id "$id" --lines 200 > "$snapshot/agent-log-tail.txt" 2>&1 || :
git -C "$seats/$id" status --short > "$snapshot/worktree-status.txt"
git -C "$seats/$id" rev-parse HEAD > "$snapshot/worktree-head.txt"
# Persist the attempted recovery before any destructive agent-metadata operation.
printf '%s\n' "$now" > "$state/last-reset"
antonina agent delete --id "$id"
antonina agent new --id "$id" --cwd "$seats/$id" --title 'Viche: Clerk'
printf '%s session_reset=endpoint_unavailable evidence=%s\n' "$(date -u +%FT%TZ)" "$snapshot" >> "$state/recoveries.log"

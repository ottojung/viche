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
# The intake and sitting gates must never reuse a terminally failed
# continuation if Antonina classifies automatic retry as unsafe. A cooldown
# expiring authorizes supervisor recovery, NOT direct reuse of that session.
if [ "${1:-}" = --gate ]; then
  unsafe=$(printf '%s\n' "$metadata" | jq -r 'if .backend_error.automatic_retry_safe == false then "yes" else "no" end')
  if [ "$kind" = failed ] && { [ "$reason" = upstream_endpoint_unavailable ] || [ "$unsafe" = yes ]; }; then
    echo "Viche: refusing failed Clerk continuation; supervisor recovery required" >&2
    exit 1
  fi
  exit 0
fi
. "$(CDPATH= cd "$(dirname "$0")" && pwd -P)/office-continuity.sh"
now=$(date +%s)
tflag=$(printf '%s\n' "$metadata" | jq -r '.backend_error.transient // false')
if [ "$kind" = failed ]; then
  if oc_is_transient "$reason" "$tflag"; then
    oc_record_failure "$state" "$id" "$reason" "$now" "$seats/$id"
  else
    oc_surface_permanent "$state" "$id" "$reason"
  fi
fi
oc_commit_age_signal "$state" "$id" "$seats/$id" "$now"
# Act 19 §3.1: failure-count-based reset, decidable from the durable record
# regardless of the currently-observed state; §3.1.3: permanent failures are
# surfaced above, never silently reset.
if oc_reset_due "$state" "$id" "$now"; then
  [ -d "$seats/$id" ] || exit 1
  snapshot=$(mktemp -d "$state/recovery-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")
  printf '%s\n' "$metadata" > "$snapshot/agent-status.json"
  antonina agent log --id "$id" --lines 200 > "$snapshot/agent-log-tail.txt" 2>&1 || :
  git -C "$seats/$id" status --short > "$snapshot/worktree-status.txt"
  git -C "$seats/$id" rev-parse HEAD > "$snapshot/worktree-head.txt"
  # Persist the attempted recovery before any destructive agent-metadata operation.
  printf '%s\n' "$now" > "$state/last-reset-$id"
  antonina agent delete --id "$id"
  antonina agent new --id "$id" --cwd "$seats/$id" --title 'Viche: Clerk'
  oc_clear_failures "$state" "$id"
  printf '%s session_reset=failure_count threshold=%s window=%s cooldown=%s evidence=%s\n' \
    "$(date -u +%FT%TZ)" "$oc_threshold" "$oc_window" "$oc_cooldown" "$snapshot" \
    >> "$state/recoveries.log"
fi

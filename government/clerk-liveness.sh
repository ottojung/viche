#!/bin/sh
# Recover a terminally failed Clerk while retaining all work and evidence.
# Act 19 §3.1: failure-count-based reset (3 consecutive transient failures in a
# 30-min window, 1800 s cooldown, progress guard), decidable from the failure
# record rather than the transient state. Permanent failures are surfaced, not
# reset. The only model remains the one configured by Antonina's constitutional boot.
set -eu
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
seats=${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}/liveness
mkdir -p "$state"
umask 077
id=$(head -n 1 "$town/government/seats.tsv" | cut -f1)
[ -n "$id" ] || exit 1
. "$town/government/office-recovery.sh"
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
[ "$kind" = failed ] || exit 0
# Act 19 §3.1: record the failure; reset only on the failure-count threshold.
or_record clerk "$reason" || true
if [ "$(or_classify "$reason")" = permanent ]; then
  echo "Viche: Clerk permanent failure ($reason); surfaced, not reset" >&2
  exit 0
fi
if or_should_reset clerk "$seats/c1a00001"; then
  echo "Viche: Clerk reached failure threshold; resetting" >&2
  or_reset clerk c1a00001 "Clerk" "$seats/c1a00001" >/dev/null
fi
exit 0

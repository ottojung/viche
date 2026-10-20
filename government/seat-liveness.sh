#!/bin/sh
# Recover failed non-Clerk parliamentary sessions; retain their Git worktrees.
# Act 19 §3.1: failure-count-based reset decidable from the failure record.
set -eu
[ "$#" -eq 1 ] || exit 2
id=$1
case "$id" in ''|*[!0123456789abcdef]*) exit 2;; esac
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
seats=${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}
root=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}/liveness
. "$town/government/office-recovery.sh"
clerk=$(head -n 1 "$town/government/seats.tsv" | cut -f1)
[ "$id" != "$clerk" ] || exit 0
title=$(awk -F '\t' -v id="$id" '$1==id {print $2; found=1; exit} END {if(!found) exit 1}' "$town/government/seats.tsv")
[ -n "$title" ] || exit 1
meta=$(antonina agent status --id "$id" --json)
mode=$(printf '%s\n' "$meta" | jq -r '.state')
reason=$(printf '%s\n' "$meta" | jq -r '.backend_error.classification // ""')
[ "$mode" = failed ] || exit 0
or_record "$id" "$reason" "$seats/$id" || true
if [ "$(or_classify "$reason")" = permanent ]; then
  echo "Viche: seat $id permanent failure ($reason); surfaced, not reset" >&2
  exit 0
fi
if or_should_reset "$id" "$seats/$id"; then
  echo "Viche: seat $id reached failure threshold; resetting" >&2
  or_reset "$id" "$id" "$title" "$seats/$id" >/dev/null
fi
exit 0

#!/bin/sh
# Aggregate objective branch readiness; failure mandates inquiry, not punishment.
set -eu
root=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}/branches
mkdir -p "$root"
now=${VICHE_BRANCH_NOW:-$(date +%s)}
max_age=${VICHE_BRANCH_MAX_AGE:-1800}
case "$now:$max_age" in *[!0-9:]*|:*|*:) exit 2;; esac
signals=
for branch in legislature executive judiciary; do
  path=$root/$branch.json
  if [ ! -s "$path" ]; then
    signals="${signals}${signals:+,}${branch}_missing"
    continue
  fi
  valid=$(jq -r --arg b "$branch" 'if .branch==$b and (.observed_at|type=="number") and
    (.readiness=="running" or .readiness=="ready" or .readiness=="unhealthy" or .readiness=="pending")
    then "yes" else "no" end' "$path" 2>/dev/null) || valid=no
  if [ "$valid" != yes ]; then
    signals="${signals}${signals:+,}${branch}_unreadable"
    continue
  fi
  at=$(jq -r '.observed_at' "$path")
  readiness=$(jq -r '.readiness' "$path")
  if [ "$at" -gt "$now" ] || [ $((now-at)) -gt "$max_age" ]; then
    signals="${signals}${signals:+,}${branch}_stale"
  elif [ "$readiness" = unhealthy ]; then
    signals="${signals}${signals:+,}${branch}_unhealthy"
  fi
done
printf '%s\t%s\n' "$now" "${signals:-clear}" >> "$root/observations.tsv"
if [ -z "$signals" ]; then
  if [ -s "$root/incident.json" ]; then
    jq -c --argjson at "$now" '. + {cleared_at:$at,closure:"readiness_restored_not_delivery_verified"}' \
      "$root/incident.json" >> "$root/history.jsonl"
    rm -f "$root/incident.json"
  fi
  exit 0
fi
tmp=$(mktemp "$root/incident.XXXXXXXX")
jq -n --argjson at "$now" --arg s "$signals" \
  '{observed_at:$at,signals:($s|split(",")),
    assessment:"mandatory_branch_inquiry_not_proof_of_misconduct",
    caveat:"running_agent_not_proof_of_useful_work"}' > "$tmp"
mv -f "$tmp" "$root/incident.json"
echo "Viche: branch health inquiry: $signals" >&2
exit 1

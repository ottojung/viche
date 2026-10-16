#!/bin/sh
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
mkdir -p "$scratch/branches"
VICHE_STATE_ROOT=$scratch
VICHE_BRANCH_NOW=1000
export VICHE_STATE_ROOT VICHE_BRANCH_NOW
for branch in legislature executive judiciary; do
  printf '{"branch":"%s","observed_at":1000,"readiness":"ready"}\n' "$branch" > "$scratch/branches/$branch.json"
done
sh "$repo/government/branch-health.sh"
[ ! -e "$scratch/branches/incident.json" ]
sed -i s/ready/unhealthy/ "$scratch/branches/judiciary.json"
sh "$repo/government/branch-health.sh" >/dev/null 2>&1 && exit 1
jq -e '.signals|index("judiciary_unhealthy")' "$scratch/branches/incident.json" >/dev/null
[ -s "$scratch/branches/executive.json" ]
sed -i s/unhealthy/ready/ "$scratch/branches/judiciary.json"
sh "$repo/government/branch-health.sh"
[ ! -e "$scratch/branches/incident.json" ]
VICHE_BRANCH_NOW=3001
export VICHE_BRANCH_NOW
sh "$repo/government/branch-health.sh" >/dev/null 2>&1 && exit 1
jq -e '.signals|index("legislature_stale")' "$scratch/branches/incident.json" >/dev/null
python3 "$repo/government/judiciary-measurements.py" >/dev/null
jq -e '.destination=="Legislature" and .no_proposals==true and .false_negative_rate==null' "$scratch/branches/judiciary-measurements.json" >/dev/null
echo 'Three-branch liveness and Judiciary self-measurement smoke passed'

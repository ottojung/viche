#!/bin/sh
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
mkdir -p "$scratch/branches"
VICHE_STATE_ROOT=$scratch
VICHE_BRANCH_NOW=1000
VICHE_BOARD_TRAIL_CHECKS=0
export VICHE_STATE_ROOT VICHE_BRANCH_NOW VICHE_BOARD_TRAIL_CHECKS
for branch in legislature executive judiciary; do
  printf '{"branch":"%s","observed_at":1000,"readiness":"ready"}\n' "$branch" > "$scratch/branches/$branch.json"
done
# Positive evidence must exist before any green health claim.
mkdir -p "$scratch/institutional-outcomes" "$scratch/institutional-cases"
printf '{"observed_at":1000}\n' > "$scratch/institutional-outcomes/latest.json"
printf '{"observed_at":1000,"count":0}\n' > "$scratch/institutional-cases/index.json"
printf '{"observed_at":1000}\n' > "$scratch/branches/judiciary-measurements.json"
sh "$repo/government/branch-health.sh"
first_signature=$(awk -F '\t' 'END {print $3}' "$scratch/branches/observations.tsv")
# The generation must name the real producer observations, not a content hash.
case "$first_signature" in
  *leg=1000*exe=1000*out=1000*meas=1000*) : ;;
  *) echo "unexpected evidence generation: $first_signature" >&2; exit 1 ;;
esac
VICHE_BRANCH_NOW=1001
export VICHE_BRANCH_NOW
sh "$repo/government/branch-health.sh"
second_signature=$(awk -F '\t' 'END {print $3}' "$scratch/branches/observations.tsv")
[ "$first_signature" = "$second_signature" ]
# Our own reconciliation bookkeeping must not manufacture a new generation.
jq '.observed_at=1001' "$scratch/institutional-cases/index.json" > "$scratch/idx.new"
mv "$scratch/idx.new" "$scratch/institutional-cases/index.json"
sh "$repo/government/branch-health.sh"
[ "$(awk -F '\t' 'END {print $3}' "$scratch/branches/observations.tsv")" = "$second_signature" ]
VICHE_BRANCH_NOW=1002
export VICHE_BRANCH_NOW
jq '.observed_at=1002' "$scratch/branches/executive.json" > "$scratch/branches/executive.new"
mv "$scratch/branches/executive.new" "$scratch/branches/executive.json"
sh "$repo/government/branch-health.sh"
third_signature=$(awk -F '\t' 'END {print $3}' "$scratch/branches/observations.tsv")
[ "$third_signature" != "$second_signature" ]
# Mailbox reports must be visible as unresolved health evidence.
mkdir -p "$scratch/oversight/judiciary-mailbox/inbox"
echo "blocked" > "$scratch/oversight/judiciary-mailbox/inbox/test.md"
sh "$repo/government/branch-health.sh" >/dev/null 2>&1 && exit 1
jq -e '.signals|index("judiciary_mailbox_pending")' "$scratch/branches/incident.json" >/dev/null
VICHE_CASE_NOW=1000 python3 "$repo/government/institutional-cases.py" reconcile >/dev/null
jq -e '.owner=="judiciary" and .state=="open"' "$scratch/institutional-cases/judiciary_mailbox_pending.json" >/dev/null
rm "$scratch/oversight/judiciary-mailbox/inbox/test.md"
sh "$repo/government/branch-health.sh"
# Remove the outcome evidence without changing agent readiness: fail closed.
rm "$scratch/institutional-outcomes/latest.json"
sh "$repo/government/branch-health.sh" >/dev/null 2>&1 && exit 1
jq -e '.signals|index("outcomes_stale")' "$scratch/branches/incident.json" >/dev/null
VICHE_CASE_NOW=1000 python3 "$repo/government/institutional-cases.py" reconcile >/dev/null
jq -e '.count>0' "$scratch/institutional-cases/index.json" >/dev/null
printf '{"observed_at":1000}\n' > "$scratch/institutional-outcomes/latest.json"
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
# Reviewer criterion: two healthy probes over BYTE-IDENTICAL producer
# observations must not close an institutional case. Only a later generation
# produced by an actual re-observation may count.
rm -f "$scratch/branches/incident.json"
for branch in legislature executive judiciary; do
  printf '{"branch":"%s","observed_at":4000,"readiness":"ready"}\n' "$branch" > "$scratch/branches/$branch.json"
done
printf '{"observed_at":4000,"count":0}\n' > "$scratch/institutional-cases/index.json"
printf '{"observed_at":4000}\n' > "$scratch/branches/judiciary-measurements.json"
rm -f "$scratch/institutional-outcomes/latest.json"
VICHE_BRANCH_NOW=4000; export VICHE_BRANCH_NOW
sh "$repo/government/branch-health.sh" >/dev/null 2>&1 && exit 1
VICHE_CASE_NOW=4000 python3 "$repo/government/institutional-cases.py" reconcile >/dev/null
jq -e '.state=="open" and .clear_observations==0' "$scratch/institutional-cases/outcomes_stale.json" >/dev/null
printf '{"observed_at":4000}\n' > "$scratch/institutional-outcomes/latest.json"
VICHE_BRANCH_NOW=4001; export VICHE_BRANCH_NOW
sh "$repo/government/branch-health.sh"
VICHE_CASE_NOW=4001 python3 "$repo/government/institutional-cases.py" reconcile >/dev/null
jq -e '.state=="open" and .clear_observations==1' "$scratch/institutional-cases/outcomes_stale.json" >/dev/null
# Same producers, different probe clock: still one observation.
VICHE_BRANCH_NOW=4002; export VICHE_BRANCH_NOW
sh "$repo/government/branch-health.sh"
VICHE_CASE_NOW=4002 python3 "$repo/government/institutional-cases.py" reconcile >/dev/null
jq -e '.state=="open" and .clear_observations==1' "$scratch/institutional-cases/outcomes_stale.json" >/dev/null
# A producer actually re-observed: now it is a distinct acquisition.
jq '.observed_at=4003' "$scratch/branches/judiciary-measurements.json" > "$scratch/m.new"
mv "$scratch/m.new" "$scratch/branches/judiciary-measurements.json"
VICHE_BRANCH_NOW=4003; export VICHE_BRANCH_NOW
sh "$repo/government/branch-health.sh"
VICHE_CASE_NOW=4003 python3 "$repo/government/institutional-cases.py" reconcile >/dev/null
jq -e '.state=="verified_closed" and .clear_observations==2' "$scratch/institutional-cases/outcomes_stale.json" >/dev/null
echo 'Three-branch liveness and Judiciary self-measurement smoke passed'

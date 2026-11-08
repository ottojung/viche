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
# Reviewer criterion: producers re-stamp observed_at every boot cycle even when
# nothing changed. Repeated identical-state cycles must NOT close a case; only a
# case-bound independent verification artifact may.
restamp() {
  for branch in legislature executive judiciary; do
    printf '{"branch":"%s","observed_at":%s,"readiness":"ready"}\n' "$branch" "$1" > "$scratch/branches/$branch.json"
  done
  printf '{"observed_at":%s}\n' "$1" > "$scratch/institutional-outcomes/latest.json"
  printf '{"observed_at":%s}\n' "$1" > "$scratch/branches/judiciary-measurements.json"
}
rm -f "$scratch/branches/incident.json" "$scratch/institutional-outcomes/latest.json"
VICHE_BRANCH_NOW=5000; export VICHE_BRANCH_NOW
sh "$repo/government/branch-health.sh" >/dev/null 2>&1 && exit 1
restamp 5000
VICHE_CASE_NOW=5000 python3 "$repo/government/institutional-cases.py" reconcile >/dev/null
jq -e '.state=="open" and .clear_observations==0' "$scratch/institutional-cases/outcomes_stale.json" >/dev/null
VICHE_BRANCH_NOW=5100; export VICHE_BRANCH_NOW
restamp 5100
sh "$repo/government/branch-health.sh"
VICHE_CASE_NOW=5100 python3 "$repo/government/institutional-cases.py" reconcile >/dev/null
jq -e '.state=="open" and .clear_observations==1' "$scratch/institutional-cases/outcomes_stale.json" >/dev/null
VICHE_BRANCH_NOW=5200; export VICHE_BRANCH_NOW
restamp 5200
sh "$repo/government/branch-health.sh"
VICHE_CASE_NOW=5200 python3 "$repo/government/institutional-cases.py" reconcile >/dev/null
jq -e '.state=="open" and .clear_observations==2 and .awaiting_independent_verification==true' "$scratch/institutional-cases/outcomes_stale.json" >/dev/null
mkdir -p "$scratch/verification" "$scratch/evidence"
printf 'independent verification\n' > "$scratch/evidence/verification.txt"
digest=$(python3 -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$scratch/evidence/verification.txt")
case_id=$(jq -r '.id' "$scratch/institutional-cases/outcomes_stale.json")
printf '{"case_id":"%s","verified_by":"judiciary","verified_at":5200,"evidence":{"ref":"evidence/verification.txt","sha256":"%s"}}\n' "$case_id" "$digest" > "$scratch/verification/outcomes_stale.json"
VICHE_CASE_NOW=5300 python3 "$repo/government/institutional-cases.py" reconcile >/dev/null
jq -e '.state=="verified_closed" and .closure_evidence.verified_by=="judiciary"' "$scratch/institutional-cases/outcomes_stale.json" >/dev/null
# That artifact must not be reusable for a later case of the same signal.
rm "$scratch/institutional-cases/outcomes_stale.json" "$scratch/institutional-outcomes/latest.json"
VICHE_BRANCH_NOW=5400; export VICHE_BRANCH_NOW
sh "$repo/government/branch-health.sh" >/dev/null 2>&1 && exit 1
restamp 5400
VICHE_CASE_NOW=5400 python3 "$repo/government/institutional-cases.py" reconcile >/dev/null
VICHE_BRANCH_NOW=5500; export VICHE_BRANCH_NOW
restamp 5500
sh "$repo/government/branch-health.sh"
VICHE_CASE_NOW=5500 python3 "$repo/government/institutional-cases.py" reconcile >/dev/null
VICHE_BRANCH_NOW=5600; export VICHE_BRANCH_NOW
restamp 5600
sh "$repo/government/branch-health.sh"
VICHE_CASE_NOW=5600 python3 "$repo/government/institutional-cases.py" reconcile >/dev/null
jq -e '.state=="open" and .awaiting_independent_verification==true' "$scratch/institutional-cases/outcomes_stale.json" >/dev/null
# A stuck obligation must be visible and routed, not silently healthy, and the
# advisory signal must not become a self-referential case.
VICHE_BRANCH_NOW=5700; export VICHE_BRANCH_NOW
restamp 5700
sh "$repo/government/branch-health.sh" >/dev/null 2>&1 && exit 1
jq -e '.signals|index("case_awaiting_verification")' "$scratch/branches/incident.json" >/dev/null
VICHE_CASE_NOW=5700 python3 "$repo/government/institutional-cases.py" reconcile >/dev/null
[ ! -e "$scratch/institutional-cases/case_awaiting_verification.json" ]
echo 'Three-branch liveness and Judiciary self-measurement smoke passed'

#!/bin/sh
# Ordinary-government branch supervisor; no protected constitutional changes.
set -eu
[ "$#" -eq 1 ] || exit 2
branch=$1
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
root=$state/branches
mkdir -p "$root"
umask 077
case "$branch" in
  legislature)
    id=$(sed -n '1s/[[:space:]].*//p' "$town/government/seats.tsv")
    program=clerk-liveness.sh
    duty=constitutional_sitting ;;
  executive)
    id=$(sed -n '2s/[[:space:]].*//p' "$town/government/seats.tsv")
    program=executive-cycle.sh
    duty=independent_delivery ;;
  judiciary)
    id=c1a00008
    program=audit-cycle.sh
    duty=independent_randomized_review ;;
  *) echo "Unknown branch: $branch" >&2; exit 2 ;;
esac
now=${VICHE_BRANCH_NOW:-$(date +%s)}
case "$now" in ''|*[!0-9]*) exit 2;; esac
cycle_ok=false
if [ -n "$id" ] && [ -s "$town/government/$program" ]; then
  if /bin/sh "$town/government/$program" > "$root/$branch-cycle.log" 2>&1; then
    cycle_ok=true
  fi
fi
readable=false
agent_state=unknown
model=unknown
variant=unknown
if [ -n "$id" ] && meta=$(antonina agent status --id "$id" --json 2>/dev/null); then
  if agent_state=$(printf '%s\n' "$meta" | jq -er '.state' 2>/dev/null); then
    readable=true
    model=$(printf '%s\n' "$meta" | jq -r '.model // "unknown"')
    variant=$(printf '%s\n' "$meta" | jq -r '.variant // "unknown"')
  fi
fi
readiness=unhealthy
if [ "$cycle_ok" = true ] && [ "$readable" = true ] &&
   [ "$model" = opencode-go/longcat-2.5-preview-free ] &&
   [ "$variant" = low ]; then
  case "$agent_state" in
    running) readiness=running ;;
    idle|succeeded) readiness=ready ;;
    *) readiness=unhealthy ;;
  esac
fi
# Legislature is dispatched by constitutional sitting() AFTER this check.
# An agent that is idle between sessions is ready, not proven productive.
receipt=$(mktemp "$root/$branch.XXXXXX")
jq -n --arg branch "$branch" --arg id "$id" --arg duty "$duty" \
  --arg state "$agent_state" --arg readiness "$readiness" \
  --arg model "$model" --arg variant "$variant" \
  --argjson at "$now" --argjson cycle_ok "$cycle_ok" \
  '{branch:$branch,seat:$id,duty:$duty,observed_at:$at,
    readiness:$readiness,agent_state:$state,cycle_accepted:$cycle_ok,
    model:$model,variant:$variant,
    caveat:"readiness_not_proof_of_agent_progress_or_completed_work"}' > "$receipt"
mv -f "$receipt" "$root/$branch.json"
if [ "$readiness" = unhealthy ]; then
  echo "Viche: $branch branch unhealthy (agent=$agent_state, cycle=$cycle_ok)" >&2
  exit 1
fi
printf 'Viche: %s branch %s (agent=%s)\n' "$branch" "$readiness" "$id"

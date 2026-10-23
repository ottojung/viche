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
    key=$(sed -n '1s/[[:space:]].*//p' "$town/government/seats.tsv")
    program=clerk-liveness.sh
    duty=constitutional_sitting ;;
  executive)
    key=executive
    program=executive-cycle.sh
    duty=independent_delivery ;;
  judiciary)
    key=judiciary
    program=audit-cycle.sh
    duty=independent_randomized_review ;;
  *) echo "Unknown branch: $branch" >&2; exit 2 ;;
esac
now=${VICHE_BRANCH_NOW:-$(date +%s)}
case "$now" in ''|*[!0-9]*) exit 2;; esac
cycle_ok=false
bootstrap_ok=true
if [ "$branch" != legislature ]; then
  /bin/sh "$town/government/branch-bootstrap.sh" "$branch" > "$root/$branch-bootstrap.log" 2>&1 || bootstrap_ok=false
fi
id=
if [ "$bootstrap_ok" = true ]; then
  id=$(/bin/sh "$town/government/appointments.sh" ensure "$key") || bootstrap_ok=false
fi
if [ "$bootstrap_ok" = true ] && [ -n "$id" ] && [ -s "$town/government/$program" ]; then
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
if [ "$cycle_ok" = true ] && [ "$readable" = true ]; then
  case "$agent_state" in
    running) readiness=running ;;
    idle|succeeded) readiness=ready ;;
    *) readiness=unhealthy ;;
  esac
fi
# Detect a repeatedly idle Executive despite independently observed eligible work.
if [ "$branch" = executive ] && [ "$readiness" = ready ] &&
   [ -s "$root/eligible-issues.json" ]; then
  backlog=$(jq -r '.count // 0' "$root/eligible-issues.json")
  if [ "$backlog" -gt 0 ]; then
    activity=$(printf '%s\n' "$meta" | jq -r '.last_activity_at // 0 | floor')
    previous=0
    [ ! -s "$root/executive-activity" ] || previous=$(cat "$root/executive-activity")
    if [ "$activity" -gt "$previous" ]; then
      printf '%s\n' "$activity" > "$root/executive-activity"
      printf '%s\n' "$now" > "$root/executive-pending-since"
    fi
    [ -s "$root/executive-pending-since" ] || printf '%s\n' "$now" > "$root/executive-pending-since"
    since=$(cat "$root/executive-pending-since")
    if [ $((now-since)) -ge 1800 ]; then readiness=unhealthy; else readiness=pending; fi
  fi
fi
# Legislature is dispatched by constitutional sitting() AFTER this check.
# An agent that is idle between sessions is ready, not proven productive.
receipt=$(mktemp "$root/$branch.XXXXXX")
jq -n --arg branch "$branch" --arg id "$id" --arg duty "$duty" \
  --arg key "$key" --arg state "$agent_state" --arg readiness "$readiness" \
  --arg model "$model" --arg variant "$variant" \
  --argjson at "$now" --argjson cycle_ok "$cycle_ok" \
  '{branch:$branch,seat:$key,agent_id:$id,duty:$duty,observed_at:$at,
    readiness:$readiness,agent_state:$state,cycle_accepted:$cycle_ok,
    model:$model,variant:$variant,
    caveat:"readiness_not_proof_of_agent_progress_or_completed_work"}' > "$receipt"
mv -f "$receipt" "$root/$branch.json"
if [ "$readiness" = unhealthy ]; then
  echo "Viche: $branch branch unhealthy (agent=$agent_state, cycle=$cycle_ok)" >&2
  exit 1
fi
printf 'Viche: %s branch %s (agent=%s)\n' "$branch" "$readiness" "$id"

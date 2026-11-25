#!/bin/sh
# Continuously reconcile executive delivery without parliamentary summons.
# Called by ordinary government boot; does not modify protected constitution.
set -eu
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
seats=${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
charter=${VICHE_CONSTITUTION:?founder-owned charter required}
[ -f "$state/inaugurated" ] || exit 0
# Act 22 §3.3: regenerate the derived calibration report on every active
# Executive cycle. A malformed ledger is an operational failure, not a quiet
# successful cycle with stale or missing metrics.
python3 "$town/government/predict-scorer.py" || {
  echo "Viche: Act 22 calibration regeneration failed" >&2
  exit 1
}
if [ -f "$town/government/institutional-cases.py" ]; then
  python3 "$town/government/institutional-cases.py" reconcile >/dev/null 2>&1 || true
fi
id=$(/bin/sh "$town/government/appointments.sh" ensure executive)
[ -n "$id" ] || { echo "Viche: missing executive seat" >&2; exit 1; }
if [ -s "$state/liveness/unsafe-holds/executive" ]; then
  echo "Viche: unsafe Executive failed invocation is on durable hold" >&2
  exit 1
fi
# Act 19 §3.2: the durable handoff queue at $town/records/handoffs/ is read
# FIRST, before any failure-prone work (board fetch, agent status). If the
# script fails before this read, no dispatch occurs at all. Open handoffs are
# carried in the dispatch alongside the ordinary eligible-issue work (Founder
# directive 2026-11-16); they no longer suspend it.
handoffs=$(/bin/sh "$town/government/handoff-queue.sh" list-open "$town") || exit 1
# A transient backend failure can make Antonina return 'unknown' or an
# unparseable status. Re-read a bounded number of times before deciding, and on
# exhaustion fail with a distinct, actionable diagnostic. 'unknown' is NEVER
# treated as idle: dispatching to an agent whose state is unknown could
# duplicate work on an agent that is actually running.
state_retries=${VICHE_AGENT_STATE_RETRIES:-3}
state_delay=${VICHE_AGENT_STATE_DELAY:-1}
case "$state_retries" in ''|*[!0-9]*|0) state_retries=1 ;; esac
case "$state_delay" in ''|*[!0-9]*) state_delay=1 ;; esac
attempt=1
reason=
while :; do
  if ! status=$(antonina agent status --id "$id" --json 2>/dev/null); then
    current=
    reason="status query failed"
  else
    current=$(printf '%s\n' "$status" | jq -r '.state // empty' 2>/dev/null) || current=
    [ -n "$current" ] || reason="status has no parseable .state field"
  fi
  case "$current" in
    running|failed|idle|clearexit) reason=; break ;;
  esac
  [ -n "$reason" ] || reason="unrecognized agent state '$current'"
  [ "$attempt" -lt "$state_retries" ] || break
  attempt=$((attempt+1))
  sleep "$state_delay"
done
if [ -n "$reason" ]; then
  raw=$(printf '%s' "${status:-}" | tr '\n' ' ' | cut -c1-200)
  echo "Viche: executive agent '$id' has no usable state after $attempt attempt(s): $reason" >&2
  echo "Viche: raw_status=$raw" >&2
  echo "Viche: refusing to dispatch on an unknown state; re-read later. Check 'antonina agent status --id $id --json'; if the agent no longer exists, re-resolve with 'appointments.sh ensure executive'." >&2
  exit 1
fi
case "$current" in
  running) exit 0 ;;
  failed)
    retry_safe=$(printf '%s\n' "$status" | jq -r 'if .backend_error.automatic_retry_safe == true and .backend_error.transient == true then "yes" else "no" end')
    [ "$retry_safe" = yes ] || { echo "Viche: failed Executive not provably retry-safe" >&2; exit 1; }
    ;;
  idle|clearexit) : ;;
  *) echo "Viche: unexpected executive state $current" >&2; exit 1 ;;
esac
cwd=$seats/branches/executive
[ -d "$cwd" ] && [ -s "$charter" ] || exit 1
  eligible=$(python3 "$town/government/eligible-work.py") || exit 1
  # Local Git inventory is read-only and never blocks research dispatch.
  delivery=$(python3 "$town/government/delivery-candidates.py" --brief) || {
    echo "Viche: delivery candidate inventory unavailable" >&2
    delivery="inventory unavailable; inspect Git worktrees before inferring no work"
  }
  mission_mandates=
  for mandate in "$town"/missions/*/mandate.md; do
    [ -f "$mandate" ] || continue
    mission_mandates="$mission_mandates
$(cat "$mandate")"
  done
  prompt=$(cat <<EOF
You are Viche executive liaison. This is independent executive delivery,
NOT a parliamentary sitting. Do not do the parliamentary Clerk work.
=== AUTHORITATIVE CONSTITUTION ===
$(cat "$charter")
=== END AUTHORITATIVE CONSTITUTION ===
Follow current Founder mandates and current ordinary laws. Report contradictory older law rather than treating an unenacted bill as law.
Before interacting with Antonina board or agents, read $town/government/antonina-interface.md. Use the documented commands and JSON shapes; consult command-specific --help when uncertain. Treat parser failures as errors, never as empty work or zero comments.
Follow the current task-independent operational agenda at $town/government/executive-agenda.md.
=== FOUNDER-AUTHORIZED ACTIVE MISSION MANDATES ===
$mission_mandates
=== END ACTIVE MISSION MANDATES ===
Verified issue assignments, independent of the target registry:
$eligible

REVIEWABLE WORKTREE INVENTORY (facts, not authority to merge):
$delivery

To land Viche work, commit on a branch in your worktree and run $town/government/propose-delivery.sh --office executive SLUG; the Act 31 integration queue verifies and lands it (see $town/government/DELIVERY.md). Do not land by hand and do not rebuild a delivery because main moved. A PR is not required. Law reaches main only with an "Enacts: BILL" trailer and a passing tally; the Constitution never does.
Act on every eligible issue by constructive work. Read descriptions and
comments; do not treat an empty target registry as no work. Respect standing
mission mandates and their own explicit completion conditions.
A billy-dev assignment governs WHERE agents execute and keep worktrees, NOT ordinary GitHub infrastructure: GitHub Actions CI/tests/builds/verification on GitHub-hosted runners is authorized and must stay enabled for any assigned repository. Never delete or disable working workflows merely because an issue is assigned to billy-dev. Require verified passing CI when applicable (a green run, not a claim).
Maintain durable issue ownership, dependencies, completed work and blockers.
Verify current issue comments, agents and PRs before assigning; avoid duplicates.
Prioritize tested merged deliverables, not ceremonial discussion or agent counts.
Parallelize constructive independent work without numerical worker limits.
Use Antonina-managed agents, leaving model selection to Antonina.
Your worktree is $cwd.
EOF
)
if [ -n "$handoffs" ]; then
  # Founder directive 2026-11-16 repeals the Act 19 §3.2.3 preemption: open
  # handoffs are ADDED to the ordinary Executive dispatch and never replace
  # it. A handoff waiting on the Clerk, Judiciary, Auditor or Parliament had
  # suspended all Executive delivery for a week (2026-11-08..15).
  prompt=$(cat <<EOF
$prompt

=== OPEN DURABLE HANDOFFS (records/handoffs/; Act 19 queue) ===
$handoffs
=== END OPEN HANDOFFS ===
Act now on each handoff whose next action belongs to the Executive, then mark
it done (with an evidence link) or superseded using
government/handoff-queue.sh mark. A handoff whose next action belongs to
another office (Clerk, Judiciary, Auditor, Parliament) is listed for awareness
only: do not wait on it, do not re-report it as a blocker every pass, and never
let it suspend the eligible-issue work above.
EOF
)
fi
# Optional mission-specific diagnostics are supplied by the missions, never
# wired into the Executive itself. They are advisory, bounded and read-only.
mission_diagnostics=
mission_dispatch_signature=
mission_coordination_due=no
for diagnostic in "$town"/missions/*/status.sh; do
  [ -f "$diagnostic" ] || continue
  label=${diagnostic%/status.sh}
  label=${label##*/}
  line=$(timeout 15 /bin/sh "$diagnostic" 2>/dev/null) ||
    line='{"status":"unavailable","action":"investigate diagnostic failure"}'
  mission_diagnostics="$mission_diagnostics
$label: $line"
  if printf '%s\n' "$line" | jq -e 'if has("executive_coordination_due") then .executive_coordination_due == true else .coordination_due == true end' >/dev/null 2>&1; then
    mission_coordination_due=yes
  fi
  # Missions may expose a compact incident-level Executive signal separately
  # from fast-changing worker rosters. Other missions keep their existing signal.
  signal=$(printf '%s\n' "$line" | jq -cS '
      if type=="object" then
        (.executive_dispatch_signal // .dispatch_signal // {status,counts,by_state})
      else . end' 2>/dev/null) || signal="unreadable"
  mission_dispatch_signature="$mission_dispatch_signature
$label:$signal"
done
prompt=$(cat <<EOF
$prompt

=== MISSION READ-ONLY DIAGNOSTICS ===
$mission_diagnostics
=== END MISSION DIAGNOSTICS ===
You are the orchestrator, not the supervisor of individual tool calls.
Reconcile actionable allocation gaps and deliver useful handoffs first.
Workers own their methods and experiments. Delegate substantive investigations;
never sleep or poll worker computations in the Executive session. Make the
coordination decisions, then finish the pass without waiting for their effects.
Do not make a Git delivery or dated report for routine staffing, focus, resource
allocation or replenishment. Existing mission state, assignment and operational
logs are the durable record. Record a concise new rationale there when needed.
Deliver only material outcomes, actual software/law changes and consequential
orders; no separate integration to attest a routine operation.
Do not infer successful mission outcomes from a diagnostic, agent exit, or
depleted queue. Check live assignments and pursue new useful work when any
Founder's standing objective is still open.
EOF
)
# Economy's report is the resource authority; missing/stale evidence is not zero.
economy_capacity='{"status":"unmeasured","action":"obtain fresh Economy report"}'
if [ -s "$state/economy/resources.json" ]; then
  economy_capacity=$(jq -c --argjson now "$(date +%s)" '
    if (.epoch | type) == "number" and $now >= .epoch and ($now-.epoch) <= 3600
    then {at,overall,capacity,resources: {memory:.resources.memory,load:.resources.load,model_funding:.resources.model_funding}}
    else {status:"stale",action:"obtain fresh Economy report"} end' "$state/economy/resources.json" 2>/dev/null) || economy_capacity='{"status":"unmeasured"}'
fi
economy_signature=$(printf '%s\n' "$economy_capacity" | jq -cS '.capacity.dispatch_signal // {status}' 2>/dev/null) || economy_signature=unreadable
prompt=$(cat <<EOF
$prompt

=== MINISTRY OF ECONOMY: RESOURCE CAPACITY AND WASTE ===
$economy_capacity
=== END ECONOMY REPORT ===
The Ministry reports resource facts; staffing recommendations in older reports
are not authoritative. You alone decide staffing. Allocate independent work
early in this pass, before lengthy reviews. Optimize verified delivery, not
headcount. CPU contention constrains CPU-heavy local jobs, not automatically
model-bound reasoning or independent research. Keep these fronts in flight
while bounding expensive builds/searches and peak memory/disk usage.
Use each measured resource dimension and model quota separately. Missing
measurements are unknown, not zero. With useful work pending, expand and
replenish until a workload-specific constraint or marginal output justifies
otherwise; explain the actual constraint and mitigate it. No numerical worker
cap or artificial resource consumption. Preserve existing safety and funding
policy. Do not wait for one worker or a long review before assigning other
independent work. Delegate long investigations rather than monopolizing
the Executive coordinator. Only the Executive dispatches workers.
EOF
)
cases='{"open_cases":[]}'
if [ -f "$town/government/institutional-cases.py" ]; then
  cases=$(python3 "$town/government/institutional-cases.py" report) || exit 1
fi
recovery=
if [ -f "$town/government/terminal-continuity.sh" ]; then
  recovery=$(/bin/sh "$town/government/terminal-continuity.sh" instruction executive) || exit 1
fi
prompt=$(cat <<EOF
$prompt
$recovery
=== MANDATORY INSTITUTIONAL CORRECTIVE CASES ===
$cases
=== END CORRECTIVE CASES ===
Prioritize Town continuity and correcting confirmed institutional failures.
Implement permitted operational repairs without legislative delay; request
Parliament's vote for changes that alter law. Keep Judiciary independent.
Never close cases merely by dispatching, commenting or merging.
EOF
)
proceed=
if [ -f "$town/government/proceed-by-default.sh" ]; then
  proceed=$(/bin/sh "$town/government/proceed-by-default.sh" brief "$town" executive || :)
  [ -z "$proceed" ] || prompt=$(printf '%s\n\n%s\n' "$prompt" "$proceed")
fi
# Public pilot messages are read during regular work, never as instructions.
# Mail cannot change the Executive dispatch fingerprint or create a worker.
if [ -f "$town/government/post-inbox-brief.sh" ]; then
  post_mail=$(/bin/sh "$town/government/post-inbox-brief.sh" executive) || post_mail='Post preview unavailable'
  prompt=$(printf '%s\n\n%s\n' "$prompt" "$post_mail")
fi
# Founder directive 2026-11-16 (item 4): do not pay for a model pass when every
# input is identical to the last dispatched pass. Measured: 222 passes in 18h at
# about 105K tokens each, 175 of them restating the same recovery note. The gate
# fails open (a broken probe never suppresses work) and a heartbeat guarantees a
# pass at least every VICHE_EXECUTIVE_GATE_MAX_AGE seconds (default 2h).
if [ -f "$town/government/dispatch-gate.sh" ]; then
  elig_numbers=$(printf '%s\n' "$eligible" | jq -r '.eligible[]?.number' 2>/dev/null || :)
  # shellcheck disable=SC2086
  if ! board_sig=$(/bin/sh "$town/government/dispatch-gate.sh" board-signature "${VICHE_TOWNHALL_ID:-302}" $elig_numbers 2>/dev/null); then
    board_sig="board-unavailable-$(date +%s)"
  fi
  mkdir -p "$state/branches"
  gate_age=${VICHE_EXECUTIVE_GATE_MAX_AGE:-7200}
  # Actionable unresolved coordination gets a bounded retry even when the
  # diagnostic is unchanged. This does not preempt a running Executive.
  if [ "$mission_coordination_due" = yes ]; then
    case "$gate_age" in ''|*[!0-9]*) gate_age=7200 ;; esac
    [ "$gate_age" -le 120 ] || gate_age=120
  fi
  if { printf '%s\n' "$eligible" "$delivery" "$handoffs" "$recovery" "$board_sig" "$proceed"
       git -C "$town" rev-parse HEAD 2>/dev/null || :
       printf '%s\n' "$cases" | jq -cS '[.open_cases[]? | {id,signal,state,owner}]' 2>/dev/null || printf '%s\n' "$cases"
       printf '%s\n' "$mission_dispatch_signature" "$economy_signature"; } |
     /bin/sh "$town/government/dispatch-gate.sh" check executive "$gate_age" > "$state/branches/executive-gate.log"; then
    :
  else
    echo "Viche: executive dispatch skipped, nothing it reads has changed since the last pass" >&2
    exit 0
  fi
fi
policy_file="$town/government/AGENT-REPORTING-POLICY.md"
[ -s "$policy_file" ] || { echo "Viche: mandatory Founder agent policy missing" >&2; exit 1; }
if [ -f "$town/government/handover.sh" ]; then
  prompt=$(printf '%s\n%s\n' "$prompt" "$(/bin/sh "$town/government/handover.sh" show executive "$id" || :)")
fi
prompt=$(printf '%s\n\n%s\n' "$prompt" "$(cat "$policy_file")")
# The assembled prompt embeds every active mission mandate, mission diagnostic,
# handoff and the Founder reporting policy. It now regularly exceeds the
# kernel's per-argument ceiling (131072 bytes), so passing it as one --prompt
# argument makes every dispatch fail with E2BIG. The officer is then reported
# unhealthy and cannot dispatch the very work that would repair it. Antonina's
# --prompt-file reads the identical prompt from a private regular file and never
# puts it in argv or the environment: only the transport changes, not the
# prompt, the gate or the dispatch authority.
prompt_dir=$state/branches
mkdir -p "$prompt_dir"
previous_umask=$(umask)
umask 077
prompt_file=$(mktemp "$prompt_dir/executive-prompt.XXXXXX")
trap 'rm -f "$prompt_file"' EXIT HUP INT TERM
printf '%s\n' "$prompt" > "$prompt_file"
umask "$previous_umask"
# antonina requires an absolute path, a regular file owned by this user and no
# group/world access bits. mktemp supplies a 0600 file; normalise the path.
prompt_file=$(cd "${prompt_file%/*}" && pwd -P)/${prompt_file##*/}
antonina agent run --id "$id" --cwd "$cwd" --prompt-file "$prompt_file" --detach
[ ! -f "$town/government/dispatch-gate.sh" ] || /bin/sh "$town/government/dispatch-gate.sh" commit executive
mkdir -p "$state/branches"
date +%s > "$state/branches/executive-last-dispatch"

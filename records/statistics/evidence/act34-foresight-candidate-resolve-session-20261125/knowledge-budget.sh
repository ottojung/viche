#!/bin/sh
# Act 32 amendment H: measured, hard-capped, fail-closed knowledge-office budgets.
#
# This is a SPEND budget, not a worker cap (Constitution VII). It never invents a
# token or cost value: token/cost usage comes only from the authoritative
# Antonina-managed OpenCode meter (knowledge-budget-tool.py); if that meter is
# unreadable, every path fails closed. All mutations are serialized by a single
# flock and persisted by temp-file + atomic rename. A live detached agent is
# actively monitored and stopped/killed on overrun or expiry; the launcher's
# own timeout is never relied on. Crashes, restarts and unknown usage are held
# with a pessimistic charge and reconciled idempotently from verified data.
#
# POSIX /bin/sh only. No bashisms.
set -eu

TOWN=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
STATE=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
TOOL=${VICHE_BUDGET_TOOL:-$TOWN/government/knowledge-budget-tool.py}
CONFIG=${VICHE_BUDGET_CONFIG:-$TOWN/government/knowledge-budget.conf}
ROOT=${VICHE_BUDGET_STATE:-$STATE/knowledge/budget}
RES=$ROOT/reservations
OFFICES='statistics foresight strategy spying'
CFG=

log() { printf 'knowledge-budget: %s\n' "$*" >&2; }
die() { log "$*"; exit 1; }

init() {
  python3 "$TOOL" durable-mkdir "$RES" >/dev/null 2>&1 || die 'cannot durably create budget state directories'
  umask 077
}

# All mutations run in a locked subshell; the lock is held only for the duration
# of the operation, never while a monitor sleeps.
with_lock() {
  ( exec 9>>"$ROOT/lock"; flock -w 30 -x 9; "$@" )
}

cfg_load() {
  python3 "$TOOL" validate "$CONFIG" >/dev/null 2>&1 ||
    die "budget config missing or invalid; fail closed: $CONFIG"
  CFG=$(python3 "$TOOL" show "$CONFIG") || die 'cannot read budget config'
}

cfgs() { printf '%s\n' "$CFG" | jq -r "$1"; }
cfgj() { printf '%s\n' "$CFG" | jq -c "$1"; }

db_path() {
  if [ -n "${VICHE_BUDGET_DB:-}" ]; then printf '%s\n' "$VICHE_BUDGET_DB";
  else cfgs '.metering.opencode_db'; fi
}

probe_or_die() {
  python3 "$TOOL" probe "$(db_path)" >/dev/null 2>&1 ||
    die 'authoritative token metering unavailable; activation blocked (no unmeasured budget claimed)'
  python3 "$TOOL" cpu-meter >/dev/null 2>&1 ||
    die 'whole-host busy CPU meter unavailable; activation blocked'
}

cpu_adjust() {
  _ca_base=$1
  _ca_current=$2
  _ca_previous=
  [ "$#" -lt 3 ] || _ca_previous=$3
  if [ -n "$_ca_previous" ] && [ "$_ca_previous" != null ]; then
    python3 "$TOOL" cpu-delta "$_ca_base" "$_ca_current" "$_ca_previous"
  else
    python3 "$TOOL" cpu-delta "$_ca_base" "$_ca_current"
  fi
}

check_office() {
  case " $OFFICES " in *" $1 "*) :;; *) die "unknown office: $1";; esac
}

atomic_write() {
  _aw_path=$1
  python3 "$TOOL" durable-write "$_aw_path" >/dev/null
}

atomic_cp() {
  _ac_from=$1; _ac_to=$2
  cat "$_ac_from" | atomic_write "$_ac_to"
}

new_id() {
  _ni_tmp=$(mktemp "$RES/.new.XXXXXXXX") || die 'cannot allocate reservation id'
  _ni_id=r$(date +%s)-$(basename "$_ni_tmp" | sed 's/^\.new\.//')
  rm -f "$_ni_tmp"
  printf '%s\n' "$_ni_id"
}

res_read() {
  _rr_f="$RES/$1.json"
  [ -s "$_rr_f" ] || die "unknown reservation: $1"
  cat "$_rr_f"
}

res_write() {
  _rw_id=$1
  printf '%s\n' "$2" | jq -e . >/dev/null || die "refusing to persist non-JSON reservation"
  printf '%s\n' "$2" | atomic_write "$RES/$_rw_id.json" || die 'reservation write failed'
}

res_state() { res_read "$1" | jq -r '.state // ""'; }
res_field() { res_read "$1" | jq -r "$2"; }

res_find_open() {
  _fo_office=$1
  for _fo_f in "$RES"/*.json; do
    [ -s "$_fo_f" ] || continue
    [ "$(jq -r '.office // ""' "$_fo_f")" = "$_fo_office" ] || continue
    case "$(jq -r '.state // ""' "$_fo_f")" in
      reserved|active|held) jq -r '.id' "$_fo_f";;
    esac
  done
}

refresh_aggregate() {
  _ra_window=${1:-}
  [ -n "$_ra_window" ] || _ra_window=$(cfgs '.accounting_window_seconds')
  _ra_now=$(date +%s)
  if [ -e "$ROOT/aggregate.json" ]; then
    jq -e 'type=="object" and (.tokens_total|type=="number") and
      (.cpu_seconds|type=="number") and (.wall_seconds|type=="number") and
      (.counted|type=="array") and (.skipped|type=="array")' "$ROOT/aggregate.json" >/dev/null 2>&1 ||
      die 'aggregate state is corrupt; refusing to release or recompute liability'
  fi
  _ra_out=$(python3 "$TOOL" aggregate "$RES" "$_ra_window" "$_ra_now") ||
    die 'cannot compute aggregate budget'
  printf '%s\n' "$_ra_out" | atomic_write "$ROOT/aggregate.json"
}

agent_status() { antonina agent status --id "$1" --json 2>/dev/null; }

# The reservation is pinned to ONE authoritative native meter session. Antonina
# may recover a different session between provider invocations; reading a stale
# or replacement row must never release or merge across identities.
agent_session_matches() {
  _as_meta=$1; _as_expected=$2
  [ -n "$_as_expected" ] || return 1
  [ "$(printf '%s\n' "$_as_meta" | jq -r '.native_session_id // empty')" = "$_as_expected" ] || return 1
  return 0
}

stop_or_kill() {
  _sk_agent=$1; _sk_action=$2
  if [ "$_sk_action" = stop ]; then antonina agent stop --id "$_sk_agent" >/dev/null 2>&1 || :; fi
  antonina agent kill --id "$_sk_agent" >/dev/null 2>&1 || :
}

# A later meter read must never REDUCE a liability already observed. Token rows
# are monotone within one native session, but a session can be recovered into a
# different row and a re-read can be stale or reset. Take the larger token total
# and the larger whole-host CPU bound so an observed overrun stays charged.
merge_usage_snapshots() {
  _ms_a=$1; _ms_b=$2
  [ -n "$_ms_a" ] && [ "$_ms_a" != null ] || { printf '%s\n' "$_ms_b"; return 0; }
  [ -n "$_ms_b" ] && [ "$_ms_b" != null ] || { printf '%s\n' "$_ms_a"; return 0; }
  # Capture BOTH originals before selecting the token winner. Selecting first
  # and then reading .cpu_seconds/.cost from the chosen object loses the other
  # input's maxima whenever that input is not the token winner.
  printf '%s\n' "$_ms_a" | jq -ce --argjson b "$_ms_b" '
    (.tokens.total // 0) as $at | ($b.tokens.total // 0) as $bt |
    (.cpu_seconds // 0) as $ac | ($b.cpu_seconds // 0) as $bc |
    (.cpu_host_seconds // 0) as $ah | ($b.cpu_host_seconds // 0) as $bh |
    (.cost // 0) as $ao | ($b.cost // 0) as $bo |
    (.cost) as $a_cost | ($b.cost) as $b_cost |
    (.cost_reported // false) as $ar | ($b.cost_reported // false) as $br |
    ($bt > $at) as $b_tokens |
    (if $b_tokens then $b else . end)
    | .tokens.total = (if $b_tokens then $bt else $at end)
    | .tokens.delta_total = (if $b_tokens then $bt else $at end)
    | .cpu_seconds = (if $bc > $ac then $bc else $ac end)
    # Keep the greatest observed host counter so a later cpu-delta cannot
    # accept a regressed/rebooted sample as a fresh one.
    | .cpu_host_seconds = (if $bh > $ah then $bh else $ah end)
    # cost and its reported flag travel together: the source of the greater
    # cost is the source of the identity, never the token winner by accident.
    | .cost = (if $bo > $ao then $b_cost else $a_cost end)
    | .cost_reported = (if $bo > $ao then $br
                        elif $ao > $bo then $ar
                        else (if $b_tokens then $br else $ar end) end)'
}

usage_from_snapshot() {
  _us_snap=$1; _us_wall=$2
  printf '%s\n' "$_us_snap" | jq -c --argjson w "$_us_wall" \
    '{tokens_total:.tokens.total,cpu_seconds:.cpu_seconds,wall_seconds:$w,
      cost:.cost,cost_reported:.cost_reported,source:.source,at:.at}'
}

# A held charge equal to the cap is only reserved liability. A charge above
# the cap represents observed consumption: retain the WHOLE charge, not
# just its excess. Independently preserve each dimension.
retain_overrun_floor() {
  printf '%s\n' "$1" | jq -ce --argjson r "$2" '
    reduce ["tokens_total","cpu_seconds","wall_seconds"][] as $k (. ;
      if ($r.charge[$k] // 0) > ($r.caps[$k] // 0) then
        .[$k] = ([.[$k], $r.charge[$k]] | max)
      else . end)'
}

# ---- pre-lock native-session/meter binding wait -------------------------------
#
# `antonina agent run ... --detach` acknowledges only the runner claim. The
# authoritative native_session_id (and its meter row) can appear on a later
# status poll. Polling for that binding happens OUTSIDE the shared accounting
# flock, so other seats are never blocked by a starting runner. The wait is
# bounded to one monitor interval or 20 seconds, and never past the reservation's
# conservative hard wall deadline (created_at + wall_seconds). Full per-run
# liability is retained throughout: the reservation stays `reserved` and is
# charged at caps by aggregate(). do_start_locked re-verifies exact agent
# identity and meter under the lock and still holds/stops if binding is unknown.
binding_ready() {
  _br_agent=$1; _br_db=$2
  if ! _br_meta=$(agent_status "$_br_agent"); then return 1; fi
  # Mirror do_start_locked's authoritative checks exactly: exact agent id is
  # enforced by the caller, here we require the native session id and a live
  # meter row. No agent state predicate is invented here.
  _br_sid=$(printf '%s\n' "$_br_meta" | jq -r '.native_session_id // empty')
  [ -n "$_br_sid" ] || return 1
  _br_pid=$(printf '%s\n' "$_br_meta" | jq -r '.runner_pid // .pid // empty')
  if ! _br_snap=$(python3 "$TOOL" snapshot "$_br_db" "$_br_sid" "$_br_pid" 2>/dev/null); then
    return 1
  fi
  [ "$(printf '%s\n' "$_br_snap" | jq -r '.session_found')" = true ] || return 1
  [ "$(printf '%s\n' "$_br_snap" | jq -r '.cpu_available')" = true ] || return 1
  return 0
}

wait_for_binding() {
  _wb_id=$1; _wb_agent=$2
  _wb_cur=$(res_read "$_wb_id")
  [ "$(printf '%s\n' "$_wb_cur" | jq -r '.state')" = reserved ] || return 0
  _wb_expected=$(printf '%s\n' "$_wb_cur" | jq -r '.agent_id // ""')
  [ "$_wb_agent" = "$_wb_expected" ] || return 0
  _wb_db=$(printf '%s\n' "$_wb_cur" | jq -r '.meter_db')
  _wb_interval=$(printf '%s\n' "$_wb_cur" | jq -r '.monitor_interval_seconds // 20')
  case "$_wb_interval" in ''|*[!0-9]*) _wb_interval=20;; esac
  [ "$_wb_interval" -gt 0 ] || _wb_interval=20
  _wb_created=$(printf '%s\n' "$_wb_cur" | jq -r '.created_at')
  _wb_wall=$(printf '%s\n' "$_wb_cur" | jq -r '.caps.wall_seconds')
  _wb_hard_deadline=$((_wb_created + _wb_wall))
  _wb_now=$(date +%s)
  [ "$_wb_hard_deadline" -gt "$_wb_now" ] || return 0
  _wb_allowance=$((_wb_hard_deadline - _wb_now))
  [ "$_wb_allowance" -lt "$_wb_interval" ] || _wb_allowance=$_wb_interval
  [ "$_wb_allowance" -le 20 ] || _wb_allowance=20
  if binding_ready "$_wb_agent" "$_wb_db"; then return 0; fi
  _wb_deadline=$((_wb_now + _wb_allowance))
  log "awaiting native session/meter binding for $_wb_agent (<=${_wb_allowance}s; full cap retained)"
  while :; do
    _wb_now=$(date +%s)
    [ "$_wb_now" -lt "$_wb_deadline" ] || break
    sleep 1
    if binding_ready "$_wb_agent" "$_wb_db"; then
      log "native session/meter binding established for $_wb_agent"
      return 0
    fi
  done
  log "native session/meter binding still unknown for $_wb_agent; locked start will hold at full cap"
  return 0
}

# ---- terminal state transitions (all assume the lock is held) ----------------

hold_locked() {
  _h_id=$1; _h_reason=$2; _h_obs=${3:-}; _h_wall=${4:-}
  _h_cur=$(res_read "$_h_id")
  case "$(printf '%s\n' "$_h_cur" | jq -r '.state')" in
    held|closed|rolled_back|rejected) return 0;;
  esac
  _h_agent=$(printf '%s\n' "$_h_cur" | jq -r '.agent_id // ""')
  [ -z "$_h_agent" ] || stop_or_kill "$_h_agent" kill
  _h_caps=$(printf '%s\n' "$_h_cur" | jq -c '.caps')
  # A hold must never ERASE debt already measured. Keep the caps as the floor
  # and add any observed snapshot (an overrun reading may not be persisted yet)
  # plus the reservation's own last committed meter as independent maxima.
  _h_previous=$(printf '%s\n' "$_h_cur" | jq -c '.meter // null')
  _h_snap=null
  _h_usage=null
  [ -n "$_h_obs" ] || _h_obs=$_h_previous
  if [ -n "$_h_obs" ] && [ "$_h_obs" != null ]; then
    if [ -z "$_h_wall" ]; then
      _h_started=$(printf '%s\n' "$_h_cur" | jq -r '.started_at // 0')
      if [ "$_h_started" -gt 0 ]; then
        _h_wall=$(( $(date +%s) - _h_started ))
      else
        _h_wall=0
      fi
    fi
    _h_snap=$(merge_usage_snapshots "$_h_obs" "$_h_previous")
    _h_usage=$(usage_from_snapshot "$_h_snap" "$_h_wall")
  fi
  _h_charge=$(printf '%s\n' "$_h_cur" | jq -ce --argjson c "$_h_caps" \
    --argjson u "$_h_usage" --argjson s "$_h_snap" \
    '{tokens_total: ([$c.tokens_total, ($u.tokens_total // 0), ($s.tokens.total // 0),
                      (.charge.tokens_total // 0)] | max),
      cpu_seconds: ([$c.cpu_seconds, ($u.cpu_seconds // 0), ($s.cpu_seconds // 0),
                     (.charge.cpu_seconds // 0)] | max),
      wall_seconds: ([$c.wall_seconds, ($u.wall_seconds // 0), (.usage.wall_seconds // 0),
                      (.charge.wall_seconds // 0)] | max)}')
  _h_now=$(date +%s)
  _h_new=$(printf '%s\n' "$_h_cur" | jq -c --arg r "$_h_reason" --argjson now "$_h_now" \
    --argjson c "$_h_charge" --argjson s "$_h_snap" --argjson u "$_h_usage" \
    '.state="held" | .charge=$c | .held_at=$now | .held_reason=$r |
     (if $s==null then . else .meter=$s | .usage=$u end) |
     .history += [{at:$now,event:"held",reason:$r}]')
  res_write "$_h_id" "$_h_new"
  refresh_aggregate "$(printf '%s\n' "$_h_cur" | jq -r '.accounting_window_seconds // empty')"
}

# A held reservation may predate the liability-preserving hold path. Upgrade
# its charge to the MAXIMUM of its caps, its existing charge floor, its meter
# and any supplied explicit pessimistic usage. Never re-stop, never lower debt.
# An optional reason records why a manual resolution retained the hold.
tighten_held_locked() {
  _th_id=$1; _th_reason=${2:-}; _th_usage=${3:-null}
  _th_cur=$(res_read "$_th_id")
  [ "$(printf '%s\n' "$_th_cur" | jq -r '.state')" = held ] || return 0
  _th_caps=$(printf '%s\n' "$_th_cur" | jq -c '.caps')
  _th_previous=$(printf '%s\n' "$_th_cur" | jq -c '.meter // null')
  if [ "$_th_usage" = null ]; then
    [ "$_th_previous" != null ] || return 0
    _th_wall=$(printf '%s\n' "$_th_cur" | jq -r '.usage.wall_seconds // 0')
    _th_usage=$(usage_from_snapshot "$_th_previous" "$_th_wall")
  fi
  _th_charge=$(printf '%s\n' "$_th_cur" | jq -ce --argjson c "$_th_caps" \
    --argjson u "$_th_usage" --argjson s "$_th_previous" \
    '{tokens_total: ([$c.tokens_total, ($u.tokens_total // 0), ($s.tokens.total // 0),
                      (.charge.tokens_total // 0)] | max),
      cpu_seconds: ([$c.cpu_seconds, ($u.cpu_seconds // 0), ($s.cpu_seconds // 0),
                     (.charge.cpu_seconds // 0)] | max),
      wall_seconds: ([$c.wall_seconds, ($u.wall_seconds // 0), (.usage.wall_seconds // 0),
                      (.charge.wall_seconds // 0)] | max)}')
  _th_now=$(date +%s)
  _th_new=$(printf '%s\n' "$_th_cur" | jq -c --arg r "$_th_reason" --argjson now "$_th_now" \
    --argjson c "$_th_charge" --argjson u "$_th_usage" --argjson old "$_th_cur" \
    '.charge=$c |
     (if $r == "" then . else .held_reason=$r end) |
     (if $u == null then . else .usage=$u end) |
     (if . == $old then . else
       .history += [{at:$now,event:"held_charge_preserved",
                    reason:(if $r == "" then "floor_retained" else $r end)}] end)')
  [ "$(printf '%s\n' "$_th_cur" | jq -c .)" != "$_th_new" ] || return 0
  res_write "$_th_id" "$_th_new"
  refresh_aggregate "$(printf '%s\n' "$_th_cur" | jq -r '.accounting_window_seconds // empty')"
}

finalize_locked() {
  _f_id=$1; _f_reason=$2; _f_snap=${3:-}; _f_wall=${4:-}
  _f_cur=$(res_read "$_f_id")
  [ "$(printf '%s\n' "$_f_cur" | jq -r '.state')" = active ] || return 0
  _f_db=$(printf '%s\n' "$_f_cur" | jq -r '.meter_db')
  _f_sid=$(printf '%s\n' "$_f_cur" | jq -r '.native_session_id // ""')
  _f_pid=$(printf '%s\n' "$_f_cur" | jq -r '.runner_pid // ""')
  # Initialise the CPU baseline and last observed meter unconditionally, before
  # any caller-supplied (possibly pre-adjusted) snapshot is used or merged.
  _f_base=$(printf '%s\n' "$_f_cur" | jq -c '.cpu_baseline')
  _f_previous=$(printf '%s\n' "$_f_cur" | jq -c '.meter // null')
  if [ -z "$_f_snap" ]; then
    if ! _f_snap=$(python3 "$TOOL" snapshot "$_f_db" "$_f_sid" "$_f_pid" 2>/dev/null); then
      hold_locked "$_f_id" 'meter_unreadable_at_finalize'; return 0
    fi
  fi
  if [ "$(printf '%s\n' "$_f_snap" | jq -r '.cpu_upper_bound // false')" != true ]; then
    if ! _f_snap=$(cpu_adjust "$_f_base" "$_f_snap" "$_f_previous"); then
      hold_locked "$_f_id" 'cpu_reboot_or_counter_invalid_at_finalize'; return 0
    fi
  fi
  _f_started=$(printf '%s\n' "$_f_cur" | jq -r '.started_at')
  [ -n "$_f_wall" ] || _f_wall=$(( $(date +%s) - _f_started ))
  _f_agent=$(printf '%s\n' "$_f_cur" | jq -r '.agent_id // ""')
  if [ -n "$_f_agent" ]; then
    stop_or_kill "$_f_agent" "$(printf '%s\n' "$_f_cur" | jq -r '.overrun_action')"
    # A kill request is NOT proof that a detached backend session stopped.
    # Never release the reserved cap while it might still be consuming work.
    if ! _f_status=$(agent_status "$_f_agent"); then
      hold_locked "$_f_id" 'cannot_verify_agent_stopped' "$_f_snap" "$_f_wall"; return 0
    fi
    # The pinned native session is the ONLY authoritative meter for this run.
    # A recovered/changed/missing identity means the reading is not for this
    # reservation: hold conservatively, never close or merge across sessions.
    if ! agent_session_matches "$_f_status" "$_f_sid"; then
      hold_locked "$_f_id" 'native_session_identity_changed_at_stop' "$_f_snap" "$_f_wall"; return 0
    fi
    _f_state=$(printf '%s\n' "$_f_status" | jq -r '.state // "unknown"')
    case "$_f_state" in
      clearexit|failed|stopped|killed) :;;
      *)
        hold_locked "$_f_id" 'agent_still_active_or_unknown_after_stop' "$_f_snap" "$_f_wall"; return 0 ;;
    esac
    # Wall liability runs through the VERIFIED stop, not the earlier snapshot.
    _f_wall_end=$(( $(date +%s) - _f_started ))
    if [ "$_f_wall_end" -gt "$_f_wall" ]; then _f_wall=$_f_wall_end; fi
    # Stopping the agent is not proof that all usage was already committed:
    # the provider can flush token accounting to the authoritative meter AFTER
    # the process is gone. Re-read the pinned session now that termination is
    # confirmed and keep the greater observation. An unreadable meter after
    # stop stays a full-cap hold, never an optimistic release.
    _f_after=
    if ! _f_after=$(python3 "$TOOL" snapshot "$_f_db" "$_f_sid" "$_f_pid" 2>/dev/null); then
      hold_locked "$_f_id" 'meter_unreadable_after_stop' "$_f_snap" "$_f_wall"; return 0
    fi
    if [ "$(printf '%s\n' "$_f_after" | jq -r '.cpu_upper_bound // false')" != true ]; then
      if ! _f_after=$(cpu_adjust "$_f_base" "$_f_after" "$_f_previous"); then
        hold_locked "$_f_id" 'cpu_reboot_or_counter_invalid_after_stop' "$_f_snap" "$_f_wall"; return 0
      fi
    fi
    _f_snap=$(merge_usage_snapshots "$_f_snap" "$_f_after")
  fi
  # A previously observed meter (e.g. an overrun that was held pending stop)
  # is a liability already incurred; a later re-read cannot erase it.
  _f_snap=$(merge_usage_snapshots "$_f_snap" "$_f_previous")
  _f_usage=$(usage_from_snapshot "$_f_snap" "$_f_wall")
  _f_usage=$(retain_overrun_floor "$_f_usage" "$_f_cur")
  _f_now=$(date +%s)
  _f_new=$(printf '%s\n' "$_f_cur" | jq -c --arg r "$_f_reason" --argjson u "$_f_usage" \
    --argjson now "$_f_now" --argjson s "$_f_snap" \
    '.state="closed" | .usage=$u | .meter=$s | .closed_at=$now | .closed_reason=$r |
     .charge=null | .history += [{at:$now,event:"closed",reason:$r}]')
  res_write "$_f_id" "$_f_new"
  refresh_aggregate "$(printf '%s\n' "$_f_cur" | jq -r '.accounting_window_seconds // empty')"
}

# ---- reservation lifecycle ---------------------------------------------------

do_reserve_locked() {
  _dr_office=$1; _dr_agent=$2
  cfg_load
  probe_or_die
  # Read WHOLE-HOST busy CPU BEFORE launch. Each overlapping office pays
  # for all host activity, giving a conservative upper bound, not attribution.
  _dr_cpu=$(python3 "$TOOL" cpu-meter) ||
    die 'cannot record host CPU baseline before launch'
  [ "$(printf '%s\n' "$_dr_cpu" | jq -r '.cpu_available')" = true ] ||
    die 'host CPU baseline not available'
  [ "$(cfgs ".offices.\"$_dr_office\".enabled")" = true ] ||
    die "office $_dr_office is disabled in the budget config; fail closed"
  _dr_open=$(res_find_open "$_dr_office")
  [ -z "$_dr_open" ] || die "office $_dr_office already has an open reservation: $_dr_open"
  _dr_now=$(date +%s)
  _dr_window=$(cfgs '.accounting_window_seconds')
  _dr_agg=$(python3 "$TOOL" aggregate "$RES" "$_dr_window" "$_dr_now") || die 'aggregate computation failed'
  _dr_adm=$(python3 "$TOOL" admit "$CONFIG" "$_dr_agg" "$_dr_office") || die 'admission check failed'
  [ "$(printf '%s\n' "$_dr_adm" | jq -r '.admit')" = true ] ||
    die "budget exhausted: $(printf '%s\n' "$_dr_adm" | jq -r '.reason')"
  _dr_id=$(new_id)
  _dr_caps=$(cfgj "(.offices.\"$_dr_office\".per_run_caps // .offices.\"$_dr_office\".caps)")
  _dr_hash=$(sha256sum "$CONFIG" | awk '{print $1}')
  _dr_interval=$(cfgs '.monitor_interval_seconds')
  _dr_action=$(cfgs '.overrun_action')
  _dr_db=$(db_path)
  _dr_res=$(jq -cn --arg id "$_dr_id" --arg office "$_dr_office" --arg agent "$_dr_agent" --argjson now "$_dr_now" \
    --argjson caps "$_dr_caps" --arg hash "$_dr_hash" --arg db "$_dr_db" \
    --argjson window "$_dr_window" --argjson interval "$_dr_interval" --arg action "$_dr_action" \
    --argjson cpu "$_dr_cpu" \
    '{schema:"viche-knowledge-budget-reservation-v1",id:$id,office:$office,
      state:"reserved",created_at:$now,caps:$caps,config_sha256:$hash,meter_db:$db,
      accounting_window_seconds:$window,monitor_interval_seconds:$interval,overrun_action:$action,
      meter:null,baseline:null,cpu_baseline:$cpu,usage:null,
      cpu_accounting:"whole-host-busy-upper-bound-not-per-office",
      agent_id:$agent,native_session_id:null,runner_pid:null,
      started_at:null,expires_at:null,charge:null,monitor_pid:null,
      history:[{at:$now,event:"reserved",office:$office}]}')
  res_write "$_dr_id" "$_dr_res"
  refresh_aggregate "$_dr_window"
  printf '%s\n' "$_dr_id"
}

do_start_locked() {
  _ds_id=$1; _ds_agent=$2
  cfg_load
  probe_or_die
  _ds_cur=$(res_read "$_ds_id")
  [ "$(printf '%s\n' "$_ds_cur" | jq -r '.state')" = reserved ] ||
    die "reservation $_ds_id is not in reserved state"

  if ! _ds_meta=$(agent_status "$_ds_agent"); then
    stop_or_kill "$_ds_agent" kill
    hold_locked "$_ds_id" 'agent_status_unreadable_after_launch'
    refresh_aggregate "$(printf '%s\n' "$_ds_cur" | jq -r '.accounting_window_seconds')"
    die 'agent status unreadable after launch; reservation held at full cap'
  fi
  _ds_sid=$(printf '%s\n' "$_ds_meta" | jq -r '.native_session_id // empty')
  _ds_pid=$(printf '%s\n' "$_ds_meta" | jq -r '.runner_pid // .pid // empty')
  _ds_db=$(printf '%s\n' "$_ds_cur" | jq -r '.meter_db')
  _ds_expected=$(printf '%s\n' "$_ds_cur" | jq -r '.agent_id // ""')
  if [ "$_ds_agent" != "$_ds_expected" ] || [ -z "$_ds_sid" ] ||
     ! _ds_snap=$(python3 "$TOOL" snapshot "$_ds_db" "$_ds_sid" "$_ds_pid" 2>/dev/null) ||
     [ "$(printf '%s\n' "$_ds_snap" | jq -r '.session_found')" != true ] ||
     [ "$(printf '%s\n' "$_ds_snap" | jq -r '.cpu_available')" != true ]; then
    stop_or_kill "$_ds_agent" kill
    hold_locked "$_ds_id" 'meter_or_session_binding_unknown_after_launch'
    refresh_aggregate "$(printf '%s\n' "$_ds_cur" | jq -r '.accounting_window_seconds')"
    die 'meter/session binding unknown after launch; reservation held at full cap'
  fi
  _ds_cpu=$(printf '%s\n' "$_ds_cur" | jq -c '.cpu_baseline')
  if ! _ds_snap=$(cpu_adjust "$_ds_cpu" "$_ds_snap"); then
    stop_or_kill "$_ds_agent" kill
    hold_locked "$_ds_id" 'cpu_reboot_or_baseline_invalid_after_launch'
    die 'host CPU meter invalid after launch; full-cap hold'
  fi
  _ds_now=$(date +%s)
  # The hard wall deadline is anchored at reservation creation, never pushed
  # out by a delayed native-session binding. The pre-lock wait therefore only
  # consumes the original wall budget; it can never extend the reservation.
  _ds_created=$(printf '%s\n' "$_ds_cur" | jq -r '.created_at')
  _ds_expiry=$((_ds_created + $(printf '%s\n' "$_ds_cur" | jq -r '.caps.wall_seconds')))
  _ds_new=$(printf '%s\n' "$_ds_cur" | jq -c --arg a "$_ds_agent" --arg s "$_ds_sid" \
    --arg p "$_ds_pid" --argjson now "$_ds_now" --argjson ex "$_ds_expiry" --argjson snap "$_ds_snap" \
    '.state="active" | .agent_id=$a | .native_session_id=$s | .runner_pid=$p |
     .started_at=$now | .expires_at=$ex | .meter=$snap |
     .history += [{at:$now,event:"activated",agent_id:$a,native_session_id:$s}]')
  res_write "$_ds_id" "$_ds_new"
  refresh_aggregate "$(printf '%s\n' "$_ds_cur" | jq -r '.accounting_window_seconds')"
}

mark_dispatched_locked() {
  _md_id=$1
  _md_cur=$(res_read "$_md_id")
  [ "$(printf '%s\n' "$_md_cur" | jq -r '.state')" = reserved ] || return 0
  _md_now=$(date +%s)
  _md_agent=$(printf '%s\n' "$_md_cur" | jq -r '.agent_id // ""')
  [ -n "$_md_agent" ] || die 'reservation lacks exact agent identity'
  res_write "$_md_id" "$(printf '%s\n' "$_md_cur" | jq -c --argjson now "$_md_now" \
    '.dispatch_attempted=true | .history += [{at:$now,event:"dispatch_attempted",agent_id:.agent_id}]')"
}

mark_dispatched() { init; with_lock mark_dispatched_locked "${1:-}"; }

resolve_locked() {
  _rs_id=$1; _rs_reason=$2
  [ -n "$_rs_reason" ] || die 'a resolution reason is required'
  _rs_cur=$(res_read "$_rs_id")
  [ "$(printf '%s\n' "$_rs_cur" | jq -r '.state')" = held ] ||
    die 'only a held reservation can be resolved'
  _rs_db=$(printf '%s\n' "$_rs_cur" | jq -r '.meter_db')
  _rs_sid=$(printf '%s\n' "$_rs_cur" | jq -r '.native_session_id // ""')
  _rs_pid=$(printf '%s\n' "$_rs_cur" | jq -r '.runner_pid // ""')
  _rs_caps=$(printf '%s\n' "$_rs_cur" | jq -c '.caps')
  _rs_started=$(printf '%s\n' "$_rs_cur" | jq -r '.started_at // 0')
  _rs_wall=0
  [ "$_rs_started" -gt 0 ] && _rs_wall=$(( $(date +%s) - _rs_started ))
  _rs_agent=$(printf '%s\n' "$_rs_cur" | jq -r '.agent_id // ""')
  # Explicit pessimistic liability for every unresolved path. It is NOT a
  # measured observation: cost_reported is false and no raw meter reading is
  # presented as final usage. The floor includes debt already recorded.
  _rs_pess=$(printf '%s\n' "$_rs_cur" | jq -c --argjson c "$_rs_caps" \
    '{tokens_total: ([$c.tokens_total, (.charge.tokens_total // 0),
                      (.meter.tokens.total // 0)] | max),
      cpu_seconds: ([$c.cpu_seconds, (.charge.cpu_seconds // 0),
                     (.meter.cpu_seconds // 0)] | max),
      wall_seconds: ([$c.wall_seconds, (.charge.wall_seconds // 0),
                      (.usage.wall_seconds // 0)] | max),
      cost:0, cost_reported:false, source:"unmetered_pessimistic_charge", at:0}')
  if [ -z "$_rs_agent" ]; then
    tighten_held_locked "$_rs_id" 'operator_resolution_agent_missing' "$_rs_pess"; return 0
  fi
  if [ -n "$_rs_agent" ]; then
    if ! _rs_status=$(agent_status "$_rs_agent"); then
      tighten_held_locked "$_rs_id" 'operator_resolution_status_unreadable' "$_rs_pess"; return 0
    fi
    if ! agent_session_matches "$_rs_status" "$_rs_sid"; then
      tighten_held_locked "$_rs_id" 'operator_resolution_identity_unresolved' "$_rs_pess"; return 0
    fi
    _rs_mstate=$(printf '%s\n' "$_rs_status" | jq -r '.state // "unknown"')
    case "$_rs_mstate" in
      clearexit|failed|stopped|killed) :;;
      *)
        stop_or_kill "$_rs_agent" "$(printf '%s\n' "$_rs_cur" | jq -r '.overrun_action')"
        if ! _rs_status=$(agent_status "$_rs_agent"); then
          tighten_held_locked "$_rs_id" 'operator_resolution_status_unreadable' "$_rs_pess"; return 0
        fi
        if ! agent_session_matches "$_rs_status" "$_rs_sid"; then
          tighten_held_locked "$_rs_id" 'operator_resolution_identity_unresolved' "$_rs_pess"; return 0
        fi
        _rs_mstate=$(printf '%s\n' "$_rs_status" | jq -r '.state // "unknown"')
        case "$_rs_mstate" in
          clearexit|failed|stopped|killed) :;;
          *)
            tighten_held_locked "$_rs_id" 'operator_resolution_agent_not_terminal' "$_rs_pess"; return 0 ;;
        esac
        ;;
    esac
    # Positively verified terminal: wall liability runs through that stop.
    _rs_wall=$(( $(date +%s) - _rs_started ))
  fi
  _rs_previous=$(printf '%s\n' "$_rs_cur" | jq -c '.meter // null')
  if [ -z "$_rs_sid" ] ||
     ! _rs_snap=$(python3 "$TOOL" snapshot "$_rs_db" "$_rs_sid" "$_rs_pid" 2>/dev/null); then
    tighten_held_locked "$_rs_id" 'operator_resolution_meter_unreadable' "$_rs_pess"; return 0
  fi
  _rs_base=$(printf '%s\n' "$_rs_cur" | jq -c '.cpu_baseline')
  if [ "$(printf '%s\n' "$_rs_snap" | jq -r '.cpu_upper_bound // false')" != true ]; then
    if ! _rs_snap=$(cpu_adjust "$_rs_base" "$_rs_snap" "$_rs_previous"); then
      tighten_held_locked "$_rs_id" 'operator_resolution_cpu_invalid' "$_rs_pess"; return 0
    fi
  fi
  _rs_snap=$(merge_usage_snapshots "$_rs_snap" "$_rs_previous")
  _rs_usage=$(usage_from_snapshot "$_rs_snap" "$_rs_wall")
  _rs_usage=$(retain_overrun_floor "$_rs_usage" "$_rs_cur")
  _rs_now=$(date +%s)
  _rs_new=$(printf '%s\n' "$_rs_cur" | jq -c --arg r "$_rs_reason" --argjson u "$_rs_usage" --argjson now "$_rs_now" \
    --argjson s "$_rs_snap" \
    '.state="closed" | .usage=$u | .meter=$s | .charge=null | .closed_at=$now |
     .closed_reason=("operator_resolved:" + $r) | .resolved_by="operator" |
     .history += [{at:$now,event:"operator_resolved",reason:$r}]')
  res_write "$_rs_id" "$_rs_new"
  refresh_aggregate "$(printf '%s\n' "$_rs_cur" | jq -r '.accounting_window_seconds // empty')"
}

resolve() { init; with_lock resolve_locked "${1:-}" "${2:-}"; }

# ---- operator resolution against an independently attested terminal session ---
#
# A held row whose native_session_id is null has no in-script exit through the
# ordinary resolve path, which can only match a STORED session id. This is a
# separate, fail-closed command (draft "Held Reservation Resolution Act"). It
# closes such a row ONLY when the operator supplies a native session id that the
# command re-attests itself against antonina for the row's EXACT agent, and that
# agent is terminal. It never rebinds a live session, never replays a failed
# turn, never reduces a recorded liability, runs no agent action and performs no
# hand edit of the ledger. Existing resolve/reconcile/guard semantics are not
# modified: this is an additional guarded path only.
resolve_session_locked() {
  _rx_id=$1; _rx_reason=$2; _rx_sid=$3; _rx_by=$4
  _rx_cur=$(res_read "$_rx_id")
  [ "$(printf '%s\n' "$_rx_cur" | jq -r '.state')" = held ] ||
    die 'only a held reservation can be resolved via resolve-session'
  [ -n "$_rx_reason" ] || die 'a resolution reason is required'

  _rx_caps=$(printf '%s\n' "$_rx_cur" | jq -c '.caps')
  # Pessimistic basis for every unresolved path. It is NOT a measurement:
  # cost_reported stays false and no raw meter reading is presented as final
  # usage. It includes the existing charge floor so a failed resolution can
  # never lower a recorded liability (Act 33 §3 / Act 34 §3(2), §4(1)).
  _rx_pess=$(printf '%s\n' "$_rx_cur" | jq -c --argjson c "$_rx_caps" \
    '{tokens_total: ([$c.tokens_total, (.charge.tokens_total // 0),
                      (.meter.tokens.total // 0)] | max),
      cpu_seconds: ([$c.cpu_seconds, (.charge.cpu_seconds // 0),
                     (.meter.cpu_seconds // 0)] | max),
      wall_seconds: ([$c.wall_seconds, (.charge.wall_seconds // 0),
                      (.usage.wall_seconds // 0)] | max),
      cost:0, cost_reported:false, source:"unmetered_pessimistic_charge", at:0}')

  _rx_agent=$(printf '%s\n' "$_rx_cur" | jq -r '.agent_id // ""')
  [ -n "$_rx_agent" ] && [ "$_rx_agent" != null ] || {
    tighten_held_locked "$_rx_id" 'operator_resolution_agent_missing' "$_rx_pess"; return 0; }
  [ -n "$_rx_by" ] && [ "$_rx_by" != null ] || {
    tighten_held_locked "$_rx_id" 'operator_resolution_resolver_absent' "$_rx_pess"; return 0; }
  [ -n "$_rx_sid" ] && [ "$_rx_sid" != null ] || {
    tighten_held_locked "$_rx_id" 'operator_resolution_session_absent' "$_rx_pess"; return 0; }

  # Independent attestation: re-read Antonina status for the EXACT row agent.
  if ! _rx_status=$(agent_status "$_rx_agent") ||
     ! printf '%s\n' "$_rx_status" | jq -e 'type=="object"' >/dev/null 2>&1; then
    tighten_held_locked "$_rx_id" 'operator_resolution_status_unreadable' "$_rx_pess"; return 0
  fi
  # If the instrument names an agent id, it must be the row's agent, not a
  # different session recovered under another identity.
  _rx_status_agent=$(printf '%s\n' "$_rx_status" | jq -r '.id // empty' 2>/dev/null || :)
  if [ -n "$_rx_status_agent" ] && [ "$_rx_status_agent" != "$_rx_agent" ]; then
    tighten_held_locked "$_rx_id" 'operator_resolution_agent_mismatch' "$_rx_pess"; return 0
  fi
  _rx_status_sid=$(printf '%s\n' "$_rx_status" | jq -r '.native_session_id // empty' 2>/dev/null || :)
  [ -n "$_rx_status_sid" ] || {
    tighten_held_locked "$_rx_id" 'operator_resolution_session_missing' "$_rx_pess"; return 0; }
  [ "$_rx_status_sid" = "$_rx_sid" ] || {
    tighten_held_locked "$_rx_id" 'operator_resolution_session_mismatch' "$_rx_pess"; return 0; }
  _rx_state=$(printf '%s\n' "$_rx_status" | jq -r '.state // "unknown"' 2>/dev/null || :)
  case "$_rx_state" in
    clearexit|failed|stopped|killed) :;;
    *) tighten_held_locked "$_rx_id" 'operator_resolution_agent_not_terminal' "$_rx_pess"; return 0;;
  esac
  # A row that was previously bound to a different native session must never
  # be metered or merged across identities, even for a terminal agent.
  _rx_row_sid=$(printf '%s\n' "$_rx_cur" | jq -r '.native_session_id // ""')
  if [ -n "$_rx_row_sid" ] && [ "$_rx_row_sid" != null ] && [ "$_rx_row_sid" != "$_rx_sid" ]; then
    tighten_held_locked "$_rx_id" 'operator_resolution_identity_mismatch' "$_rx_pess"; return 0
  fi

  # Terminal state is independently verified: run wall liability through it.
  _rx_started=$(printf '%s\n' "$_rx_cur" | jq -r '.started_at // 0' 2>/dev/null || :)
  case "$_rx_started" in ''|null|*[!0-9]*) _rx_started=0;; esac
  _rx_created=$(printf '%s\n' "$_rx_cur" | jq -r '.created_at // 0' 2>/dev/null || :)
  case "$_rx_created" in ''|null|*[!0-9]*) _rx_created=0;; esac
  _rx_wall=0
  if [ "$_rx_started" -gt 0 ]; then _rx_wall=$(( $(date +%s) - _rx_started ));
  elif [ "$_rx_created" -gt 0 ]; then _rx_wall=$(( $(date +%s) - _rx_created )); fi
  [ "$_rx_wall" -ge 0 ] || _rx_wall=0

  _rx_db=$(printf '%s\n' "$_rx_cur" | jq -r '.meter_db')
  _rx_pid=$(printf '%s\n' "$_rx_status" | jq -r '.runner_pid // .pid // empty' 2>/dev/null || :)
  _rx_previous=$(printf '%s\n' "$_rx_cur" | jq -c '.meter // null')
  if ! _rx_snap=$(python3 "$TOOL" snapshot "$_rx_db" "$_rx_sid" "$_rx_pid" 2>/dev/null); then
    tighten_held_locked "$_rx_id" 'operator_resolution_meter_unreadable' "$_rx_pess"; return 0
  fi
  # A snapshot is a raw host reading; a missing upper-bound flag means the CPU
  # delta was never applied and the reading cannot bound this session.
  if [ "$(printf '%s\n' "$_rx_snap" | jq -r '.cpu_upper_bound // false' 2>/dev/null || :)" != true ]; then
    _rx_base=$(printf '%s\n' "$_rx_cur" | jq -c '.cpu_baseline')
    if ! _rx_snap=$(cpu_adjust "$_rx_base" "$_rx_snap" "$_rx_previous"); then
      tighten_held_locked "$_rx_id" 'operator_resolution_cpu_invalid' "$_rx_pess"; return 0
    fi
  fi
  _rx_snap=$(merge_usage_snapshots "$_rx_snap" "$_rx_previous")
  _rx_usage=$(usage_from_snapshot "$_rx_snap" "$_rx_wall")
  # aggregate() charges a CLOSED row from .usage, not .charge (tool line 311).
  # Floor usage at every cap AND the prior charge on each dimension, so closing
  # the hold can never reduce aggregate liability below what was already held.
  _rx_usage=$(printf '%s\n' "$_rx_usage" | jq -ce --argjson c "$_rx_caps" \
    --argjson old "$_rx_cur" \
    'reduce ["tokens_total","cpu_seconds","wall_seconds"][] as $k (. ;
      .[$k] = ([ (.[$k] // 0), ($c[$k] // 0), ($old.charge[$k] // 0) ] | max))')
  _rx_usage=$(retain_overrun_floor "$_rx_usage" "$_rx_cur")

  _rx_now=$(date +%s)
  _rx_new=$(printf '%s\n' "$_rx_cur" | jq -c \
    --arg reason "$_rx_reason" --arg by "$_rx_by" --arg sid "$_rx_sid" \
    --arg agent "$_rx_agent" --arg state "$_rx_state" --argjson now "$_rx_now" \
    --argjson u "$_rx_usage" --argjson snap "$_rx_snap" \
    '.state="closed" | .usage=$u | .charge=$u | .meter=$snap |
      .closed_at=$now | .closed_reason=("operator_resolved_session:" + $reason) |
      .resolved_by=$by |
      .resolution_attestation={session_id:$sid, agent_id:$agent, state:$state,
        resolver:$by, reason:$reason, observed_at:$now,
        status_source:"antonina agent status", command:"resolve-session"} |
      .history += [{at:$now,event:"operator_resolved_session",reason:$reason,
        session_id:$sid,agent_id:$agent,resolver:$by,state:$state}]')
  res_write "$_rx_id" "$_rx_new"
  refresh_aggregate "$(printf '%s\n' "$_rx_cur" | jq -r '.accounting_window_seconds // empty')"
}

resolve_session() { init; with_lock resolve_session_locked "$@"; }

launch_monitor() {
  _lm_id=$1
  _lm_log="$ROOT/monitor-$_lm_id.log"
  # 9>&- is essential: a launched monitor must not inherit a held flock fd,
  # or its own locked writes would deadlock against its inherited lock.
  if command -v setsid >/dev/null 2>&1; then
    setsid /bin/sh "$0" monitor "$_lm_id" 9>&- </dev/null >> "$_lm_log" 2>&1 &
  else
    /bin/sh "$0" monitor "$_lm_id" 9>&- </dev/null >> "$_lm_log" 2>&1 &
  fi
  _lm_pid=$!
  with_lock res_write "$_lm_id" \
    "$(res_read "$_lm_id" | jq -c --argjson p "$_lm_pid" '.monitor_pid=$p')"
}

monitor() {
  _mo_id=$1
  _mo_cur=$(res_read "$_mo_id")
  _mo_interval=$(printf '%s\n' "$_mo_cur" | jq -r '.monitor_interval_seconds // 20')
  while :; do
    sleep "$_mo_interval"
    _mo_cur=$(res_read "$_mo_id") || exit 0
    [ "$(printf '%s\n' "$_mo_cur" | jq -r '.state')" = active ] || exit 0
    _mo_now=$(date +%s)
    _mo_exp=$(printf '%s\n' "$_mo_cur" | jq -r '.expires_at')
    if [ "$_mo_now" -ge "$_mo_exp" ]; then
      finalize "$_mo_id" 'expiry'; exit 0
    fi
    _mo_agent=$(printf '%s\n' "$_mo_cur" | jq -r '.agent_id')
    if ! _mo_meta=$(agent_status "$_mo_agent"); then
      hold "$_mo_id" 'status_unreadable'; exit 0
    fi
    _mo_sid=$(printf '%s\n' "$_mo_cur" | jq -r '.native_session_id // ""')
    # Never meter or release a different session recovered by Antonina.
    if ! agent_session_matches "$_mo_meta" "$_mo_sid"; then
      hold "$_mo_id" 'native_session_identity_changed_on_monitor'; exit 0
    fi
    _mo_mstate=$(printf '%s\n' "$_mo_meta" | jq -r '.state // "unknown"')
    case "$_mo_mstate" in
      running) :;;
      *) finalize "$_mo_id" "agent_terminal_$_mo_mstate"; exit 0;;
    esac
    _mo_db=$(printf '%s\n' "$_mo_cur" | jq -r '.meter_db')
    _mo_pid=$(printf '%s\n' "$_mo_cur" | jq -r '.runner_pid // ""')
    if ! _mo_snap=$(python3 "$TOOL" snapshot "$_mo_db" "$_mo_sid" "$_mo_pid" 2>/dev/null); then
      hold "$_mo_id" 'meter_unreadable'; exit 0
    fi
    _mo_base=$(printf '%s\n' "$_mo_cur" | jq -c '.cpu_baseline')
    _mo_previous=$(printf '%s\n' "$_mo_cur" | jq -c '.meter')
    if ! _mo_snap=$(cpu_adjust "$_mo_base" "$_mo_snap" "$_mo_previous"); then
      hold "$_mo_id" 'cpu_reboot_or_counter_regression'; exit 0
    fi
    _mo_caps=$(printf '%s\n' "$_mo_cur" | jq -c '.caps')
    _mo_wall=$((_mo_now - $(printf '%s\n' "$_mo_cur" | jq -r '.started_at')))
    if ! _mo_ov=$(python3 "$TOOL" overrun "$_mo_caps" "$_mo_snap" "$_mo_wall"); then
      hold "$_mo_id" 'usage_overrun_check_failed' "$_mo_snap" "$_mo_wall"; exit 0
    fi
    if [ "$(printf '%s\n' "$_mo_ov" | jq -r '.over')" = true ]; then
      _mo_action=$(printf '%s\n' "$_mo_cur" | jq -r '.overrun_action')
      stop_or_kill "$_mo_agent" "$_mo_action"
      finalize "$_mo_id" "overrun_$(printf '%s\n' "$_mo_ov" | jq -r '.reasons | join("_")')" \
        "$_mo_snap" "$_mo_wall"
      exit 0
    fi
    update_meter "$_mo_id" "$_mo_snap" "$_mo_wall" || {
      hold "$_mo_id" 'state_write_failed' "$_mo_snap" "$_mo_wall"; exit 0
    }
  done
}

update_meter() { with_lock _update_meter "$@"; }
_update_meter() {
  _um_id=$1; _um_snap=$2; _um_wall=$3
  _um_cur=$(res_read "$_um_id")
  [ "$(printf '%s\n' "$_um_cur" | jq -r '.state')" = active ] || return 0
  _um_previous=$(printf '%s\n' "$_um_cur" | jq -c '.meter // null')
  # A fresh read of a stale row must not replace a larger liability already
  # observed on this reservation. Independent maxima also keep the greatest
  # host CPU counter and the cost/reported-flag identity of the cost source.
  _um_snap=$(merge_usage_snapshots "$_um_snap" "$_um_previous")
  _um_usage=$(usage_from_snapshot "$_um_snap" "$_um_wall")
  _um_new=$(printf '%s\n' "$_um_cur" | jq -c --argjson m "$_um_snap" --argjson u "$_um_usage" \
    '.meter=$m | .usage=$u')
  res_write "$_um_id" "$_um_new"
  refresh_aggregate "$(printf '%s\n' "$_um_cur" | jq -r '.accounting_window_seconds // empty')"
}

hold() { with_lock hold_locked "$@"; }
finalize() { with_lock finalize_locked "$@"; }

# ---- external subcommands ----------------------------------------------------

guard() {
  _g_office=$1
  init
  cfg_load
  probe_or_die
  [ "$(cfgs ".offices.\"$_g_office\".enabled")" = true ] ||
    die "office $_g_office is disabled in the budget config; fail closed"
  _g_open=$(res_find_open "$_g_office")
  [ -z "$_g_open" ] || die "office $_g_office has an open reservation: $_g_open"
  _g_now=$(date +%s)
  _g_agg=$(python3 "$TOOL" aggregate "$RES" "$(cfgs '.accounting_window_seconds')" "$_g_now") ||
    die 'aggregate computation failed'
  if [ -e "$ROOT/aggregate.json" ]; then
    jq -e --argjson a "$_g_agg" '.tokens_total==$a.tokens_total and
      .cpu_seconds==$a.cpu_seconds and .wall_seconds==$a.wall_seconds and
      .counted==$a.counted' "$ROOT/aggregate.json" >/dev/null 2>&1 ||
      die 'aggregate record is corrupt or divergent; refusing activation'
  fi
  python3 "$TOOL" cpu-meter >/dev/null 2>&1 ||
    die 'whole-host busy CPU meter unavailable; activation blocked'
  _g_adm=$(python3 "$TOOL" admit "$CONFIG" "$_g_agg" "$_g_office") || die 'admission check failed'
  [ "$(printf '%s\n' "$_g_adm" | jq -r '.admit')" = true ] ||
    die "budget exhausted: $(printf '%s\n' "$_g_adm" | jq -r '.reason')"
  printf 'guard ok: %s\n' "$_g_office"
}

reconcile_locked() {
  cfg_load
  _rc_now=$(date +%s)
  for _rc_f in "$RES"/*.json; do
    [ -s "$_rc_f" ] || continue
    _rc_id=$(jq -r '.id // ""' "$_rc_f")
    _rc_state=$(jq -r '.state // ""' "$_rc_f")
    [ -n "$_rc_id" ] || continue
    case "$_rc_state" in
      reserved)
        _rc_age=$((_rc_now - $(jq -r '.created_at' "$_rc_f")))
        _rc_interval=$(jq -r '.monitor_interval_seconds // 20' "$_rc_f")
        [ "$_rc_age" -gt $((_rc_interval * 3 + 60)) ] || continue
        if [ "$(jq -r '.dispatch_attempted // false' "$_rc_f")" = true ]; then
          # A launch was attempted but no agent/meter identity was registered:
          # usage is genuinely unknown, so hold with a pessimistic full charge
          # and halt further dispatch until an audited resolution.
          hold_locked "$_rc_id" 'dispatch_attempted_without_meter_registration'
        elif [ -z "$(jq -r '.agent_id // ""' "$_rc_f")" ]; then
          hold_locked "$_rc_id" 'reserved_without_agent_identity'
        else
          res_write "$_rc_id" "$(jq -c --argjson now "$_rc_now" \
            '.state="rolled_back" | .history += [{at:$now,event:"orphaned_reservation_rollback"}]' "$_rc_f")"
        fi
        ;;
      active)
        # A restart past the hard wall/expiry deadline must stop the session,
        # not silently re-authorise it (Act 32 amendment B acceptance case).
        _rc_exp=$(jq -r '.expires_at // 0' "$_rc_f")
        if [ "$_rc_exp" -le "$_rc_now" ]; then
          finalize_locked "$_rc_id" 'expiry'; continue
        fi
        _rc_agent=$(jq -r '.agent_id' "$_rc_f")
        if ! _rc_meta=$(agent_status "$_rc_agent"); then
          hold_locked "$_rc_id" 'status_unreadable_on_reconcile'; continue
        fi
        _rc_sid=$(jq -r '.native_session_id // ""' "$_rc_f")
        if ! agent_session_matches "$_rc_meta" "$_rc_sid"; then
          hold_locked "$_rc_id" 'native_session_identity_changed_on_reconcile'; continue
        fi
        _rc_mstate=$(printf '%s\n' "$_rc_meta" | jq -r '.state // "unknown"')
        case "$_rc_mstate" in
          running)
            _rc_mpid=$(jq -r '.monitor_pid // ""' "$_rc_f")
            if [ -z "$_rc_mpid" ] || ! kill -0 "$_rc_mpid" 2>/dev/null; then
              _rc_log="$ROOT/monitor-$_rc_id.log"
              if command -v setsid >/dev/null 2>&1; then
                setsid /bin/sh "$0" monitor "$_rc_id" 9>&- </dev/null >> "$_rc_log" 2>&1 &
              else
                /bin/sh "$0" monitor "$_rc_id" 9>&- </dev/null >> "$_rc_log" 2>&1 &
              fi
              _rc_newpid=$!
              res_write "$_rc_id" "$(jq -c --argjson p "$_rc_newpid" '.monitor_pid=$p' "$_rc_f")"
            fi
            ;;
          *) finalize_locked "$_rc_id" "agent_terminal_on_reconcile";;
        esac
        ;;
      held)
        _rc_agent=$(jq -r '.agent_id // ""' "$_rc_f")
        _rc_db=$(jq -r '.meter_db' "$_rc_f")
        _rc_sid=$(jq -r '.native_session_id // ""' "$_rc_f")
        _rc_pid=$(jq -r '.runner_pid // ""' "$_rc_f")
        tighten_held_locked "$_rc_id"
        if [ -n "$_rc_agent" ] && _rc_meta=$(agent_status "$_rc_agent"); then
          [ "$(printf '%s\n' "$_rc_meta" | jq -r '.state // "unknown"')" = running ] && continue
          # A held debt must not be released against a different/recovered
          # session row; the hold stays until an operator resolves identity.
          if ! agent_session_matches "$_rc_meta" "$_rc_sid"; then
            log "held $_rc_id: native session identity changed; keeping full hold"
            continue
          fi
          if _rc_snap=$(python3 "$TOOL" snapshot "$_rc_db" "$_rc_sid" "$_rc_pid" 2>/dev/null); then
            res_write "$_rc_id" "$(jq -c '.state="active"' "$_rc_f")"
            finalize_locked "$_rc_id" 'reconciled_terminal' "$_rc_snap" ''
          fi
        fi
        ;;
    esac
  done
  refresh_aggregate "$(cfgs '.accounting_window_seconds')"
}

config_cmd() {
  _cc_sub=${1:-}
  case "$_cc_sub" in
    validate) python3 "$TOOL" validate "$CONFIG";;
    show) python3 "$TOOL" show "$CONFIG";;
    activate)
      init
      python3 "$TOOL" validate "$CONFIG" >/dev/null || die 'invalid config; activation refused'
      with_lock _config_activate ;;
    rollback) init; with_lock _config_rollback ;;
    *) die 'usage: config validate|show|activate|rollback';;
  esac
}

_config_activate() {
  _ca_norm=$(python3 "$TOOL" show "$CONFIG") || die 'cannot normalise config'
  if [ -s "$ROOT/config.active.json" ]; then
    atomic_cp "$ROOT/config.active.json" "$ROOT/config.previous.json" ||
      die 'cannot rotate previous config'
  fi
  printf '%s\n' "$_ca_norm" | atomic_write "$ROOT/config.active.json" ||
    die 'cannot write active config'
  log 'activated validated budget config'
}

_config_rollback() {
  [ -s "$ROOT/config.previous.json" ] || die 'no previous config to roll back to'
  _cb_before=$(sha256sum "$ROOT/config.previous.json" | awk '{print $1}')
  atomic_cp "$ROOT/config.previous.json" "$ROOT/config.active.json" ||
    die 'config rollback failed'
  _cb_after=$(sha256sum "$ROOT/config.active.json" | awk '{print $1}')
  [ "$_cb_before" = "$_cb_after" ] || die 'config rollback byte check failed'
  printf 'rolled back active config to %s\n' "$_cb_after"
}

report() {
  init
  printf 'Authoritative meter source: %s\n' "$(db_path 2>/dev/null || printf unknown)"
  printf 'Baseline: diagnostic only, no frozen verified comparator (Act 32 v4 D)\n'
  if [ -s "$ROOT/aggregate.json" ]; then cat "$ROOT/aggregate.json";
  else printf '{}\n'; fi
  for _rp_f in "$RES"/*.json; do
    [ -s "$_rp_f" ] || continue
    jq -c '{id,office,state,caps,usage,charge,closed_reason,held_reason}' "$_rp_f"
  done
}

cmd=${1:-}
[ -n "$cmd" ] || { echo 'usage: knowledge-budget.sh config|guard|reserve|mark-dispatched|start|monitor|reconcile|resolve|resolve-session|report' >&2; exit 2; }
shift || :
case "$cmd" in
  config) config_cmd "$@";;
  guard) check_office "${1:-}"; guard "$1";;
  reserve) check_office "${1:-}"; init; with_lock do_reserve_locked "$1" "$2";;
  mark-dispatched) init; with_lock mark_dispatched_locked "${1:-}";;
  start)
    init
    _st_id=${1:-}; _st_agent=${2:-}
    # Bound the native-session/meter binding wait OUTSIDE the flock; full-cap
    # liability is retained until do_start_locked re-verifies under the lock.
    wait_for_binding "$_st_id" "$_st_agent"
    with_lock do_start_locked "$_st_id" "$_st_agent"
    launch_monitor "$_st_id"
    printf 'active %s\n' "$_st_id"
    ;;
  monitor) init; monitor "${1:-}";;
  reconcile) init; with_lock reconcile_locked;;
  resolve) init; with_lock resolve_locked "${1:-}" "${2:-}";;
  resolve-session)
    init
    _rxcli_id=${1:-}; _rxcli_reason=${2:-}
    if [ "$#" -ge 2 ]; then shift 2;
    elif [ "$#" -ge 1 ]; then shift; fi
    _rxcli_sid=; _rxcli_by=
    while [ "$#" -gt 0 ]; do
      case "$1" in
        --session) _rxcli_sid=${2:-}; [ "$#" -ge 2 ] && shift 2 || shift;;
        --by) _rxcli_by=${2:-}; [ "$#" -ge 2 ] && shift 2 || shift;;
        *) echo "unknown argument to resolve-session: $1" >&2; exit 2;;
      esac
    done
    case "$_rxcli_id" in
      ''|*/*|*..*) echo 'usage: resolve-session RESERVATION_ID REASON --session SID --by OPERATOR' >&2; exit 2;;
    esac
    with_lock resolve_session_locked "$_rxcli_id" "$_rxcli_reason" "$_rxcli_sid" "$_rxcli_by"
    ;;
  report) report;;
  *) echo "unknown command: $cmd" >&2; exit 2;;
esac

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

stop_or_kill() {
  _sk_agent=$1; _sk_action=$2
  if [ "$_sk_action" = stop ]; then antonina agent stop --id "$_sk_agent" >/dev/null 2>&1 || :; fi
  antonina agent kill --id "$_sk_agent" >/dev/null 2>&1 || :
}

usage_from_snapshot() {
  _us_snap=$1; _us_wall=$2
  printf '%s\n' "$_us_snap" | jq -c --argjson w "$_us_wall" \
    '{tokens_total:.tokens.total,cpu_seconds:.cpu_seconds,wall_seconds:$w,
      cost:.cost,cost_reported:.cost_reported,source:.source,at:.at}'
}

# ---- terminal state transitions (all assume the lock is held) ----------------

hold_locked() {
  _h_id=$1; _h_reason=$2
  _h_cur=$(res_read "$_h_id")
  case "$(printf '%s\n' "$_h_cur" | jq -r '.state')" in
    held|closed|rolled_back|rejected) return 0;;
  esac
  _h_agent=$(printf '%s\n' "$_h_cur" | jq -r '.agent_id // ""')
  [ -z "$_h_agent" ] || stop_or_kill "$_h_agent" kill
  _h_caps=$(printf '%s\n' "$_h_cur" | jq -c '.caps')
  _h_now=$(date +%s)
  _h_new=$(printf '%s\n' "$_h_cur" | jq -c --arg r "$_h_reason" --argjson now "$_h_now" --argjson c "$_h_caps" \
    '.state="held" | .charge=$c | .held_at=$now | .held_reason=$r |
     .history += [{at:$now,event:"held",reason:$r}]')
  res_write "$_h_id" "$_h_new"
  refresh_aggregate "$(printf '%s\n' "$_h_cur" | jq -r '.accounting_window_seconds // empty')"
}

finalize_locked() {
  _f_id=$1; _f_reason=$2; _f_snap=${3:-}; _f_wall=${4:-}
  _f_cur=$(res_read "$_f_id")
  [ "$(printf '%s\n' "$_f_cur" | jq -r '.state')" = active ] || return 0
  _f_db=$(printf '%s\n' "$_f_cur" | jq -r '.meter_db')
  _f_sid=$(printf '%s\n' "$_f_cur" | jq -r '.native_session_id // ""')
  _f_pid=$(printf '%s\n' "$_f_cur" | jq -r '.runner_pid // ""')
  if [ -z "$_f_snap" ]; then
    if ! _f_snap=$(python3 "$TOOL" snapshot "$_f_db" "$_f_sid" "$_f_pid" 2>/dev/null); then
      hold_locked "$_f_id" 'meter_unreadable_at_finalize'; return 0
    fi
  fi
  if [ "$(printf '%s\n' "$_f_snap" | jq -r '.cpu_upper_bound // false')" != true ]; then
    _f_base=$(printf '%s\n' "$_f_cur" | jq -c '.cpu_baseline')
    _f_previous=$(printf '%s\n' "$_f_cur" | jq -c '.meter')
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
      hold_locked "$_f_id" 'cannot_verify_agent_stopped'; return 0
    fi
    _f_state=$(printf '%s\n' "$_f_status" | jq -r '.state // "unknown"')
    case "$_f_state" in
      running|starting|recovering|unknown)
        hold_locked "$_f_id" 'agent_still_active_or_unknown_after_stop'; return 0 ;;
    esac
  fi
  _f_usage=$(usage_from_snapshot "$_f_snap" "$_f_wall")
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
  _ds_expiry=$((_ds_now + $(printf '%s\n' "$_ds_cur" | jq -r '.caps.wall_seconds')))
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
  if [ -n "$_rs_sid" ] && _rs_snap=$(python3 "$TOOL" snapshot "$_rs_db" "$_rs_sid" "$_rs_pid" 2>/dev/null); then
    _rs_usage=$(usage_from_snapshot "$_rs_snap" "$_rs_wall")
  else
    # No verified meter observation: keep the pessimistic full-cap charge and
    # say so. Resolution never fabricates a token reading or a cost.
    _rs_usage=$(printf '%s\n' "$_rs_caps" | jq -c \
      '{tokens_total:.tokens_total,cpu_seconds:.cpu_seconds,wall_seconds:.wall_seconds,
        cost:0,cost_reported:false,source:"unmetered_pessimistic_charge",at:0}')
  fi
  _rs_now=$(date +%s)
  _rs_new=$(printf '%s\n' "$_rs_cur" | jq -c --arg r "$_rs_reason" --argjson u "$_rs_usage" --argjson now "$_rs_now" \
    '.state="closed" | .usage=$u | .charge=null | .closed_at=$now |
     .closed_reason=("operator_resolved:" + $r) | .resolved_by="operator" |
     .history += [{at:$now,event:"operator_resolved",reason:$r}]')
  res_write "$_rs_id" "$_rs_new"
  refresh_aggregate "$(printf '%s\n' "$_rs_cur" | jq -r '.accounting_window_seconds // empty')"
}

resolve() { init; with_lock resolve_locked "${1:-}" "${2:-}"; }

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
    _mo_mstate=$(printf '%s\n' "$_mo_meta" | jq -r '.state // "unknown"')
    case "$_mo_mstate" in
      running) :;;
      *) finalize "$_mo_id" "agent_terminal_$_mo_mstate"; exit 0;;
    esac
    _mo_db=$(printf '%s\n' "$_mo_cur" | jq -r '.meter_db')
    _mo_sid=$(printf '%s\n' "$_mo_cur" | jq -r '.native_session_id')
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
      hold "$_mo_id" 'usage_overrun_check_failed'; exit 0
    fi
    if [ "$(printf '%s\n' "$_mo_ov" | jq -r '.over')" = true ]; then
      _mo_action=$(printf '%s\n' "$_mo_cur" | jq -r '.overrun_action')
      stop_or_kill "$_mo_agent" "$_mo_action"
      finalize "$_mo_id" "overrun_$(printf '%s\n' "$_mo_ov" | jq -r '.reasons | join("_")')" \
        "$_mo_snap" "$_mo_wall"
      exit 0
    fi
    update_meter "$_mo_id" "$_mo_snap" "$_mo_wall" || {
      hold "$_mo_id" 'state_write_failed'; exit 0
    }
  done
}

update_meter() { with_lock _update_meter "$@"; }
_update_meter() {
  _um_id=$1; _um_snap=$2; _um_wall=$3
  _um_cur=$(res_read "$_um_id")
  [ "$(printf '%s\n' "$_um_cur" | jq -r '.state')" = active ] || return 0
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
        if [ -n "$_rc_agent" ] && _rc_meta=$(agent_status "$_rc_agent"); then
          [ "$(printf '%s\n' "$_rc_meta" | jq -r '.state // "unknown"')" = running ] && continue
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
[ -n "$cmd" ] || { echo 'usage: knowledge-budget.sh config|guard|reserve|mark-dispatched|start|monitor|reconcile|resolve|report' >&2; exit 2; }
shift || :
case "$cmd" in
  config) config_cmd "$@";;
  guard) check_office "${1:-}"; guard "$1";;
  reserve) check_office "${1:-}"; init; with_lock do_reserve_locked "$1" "$2";;
  mark-dispatched) init; with_lock mark_dispatched_locked "${1:-}";;
  start) init; with_lock do_start_locked "${1:-}" "${2:-}"; launch_monitor "${1:-}"; printf 'active %s\n' "$1";;
  monitor) init; monitor "${1:-}";;
  reconcile) init; with_lock reconcile_locked;;
  resolve) init; with_lock resolve_locked "${1:-}" "${2:-}";;
  report) report;;
  *) echo "unknown command: $cmd" >&2; exit 2;;
esac

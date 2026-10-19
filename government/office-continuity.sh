# Act 19 (Office Continuity and Handoff Integrity Act) §3 shared supervisor
# helpers. Sourced by the office supervisors; never executed directly.
# POSIX /bin/sh only: no `local`, no bashisms, no top-level side effects.
# All variables are prefixed oc_ so callers are not clobbered.
#
# §3.1 starting values set by the Legislature (records/bills/office-continuity-act.md):
#   oc_threshold consecutive transient failures, oc_window seconds (30 min),
#   oc_cooldown seconds between resets for the same office (1800 s).
# Retuning is a recorded, Judiciary-reviewed change to this file, not a silent knob.

oc_threshold=3
oc_window=1800
oc_cooldown=1800

# A failure counts toward the reset only when the runtime classifies it as
# transient: the observed classes from the 2026-10-17 API-key expiry
# (unrecognized_backend_failure) and endpoint outages, or any classification
# whose `transient` flag is true. Everything else is permanent: surfaced, never
# silently reset.
oc_is_transient() {
  [ "$2" = true ] && return 0
  case "$1" in
    upstream_endpoint_unavailable|unrecognized_backend_failure) return 0 ;;
  esac
  return 1
}

# Append one observed transient failure to the durable per-office record.
# Line format: "<unixtime> <classification> <worktree-head-sha>".
# Progress guard (§3.1.2): a durable commit since the previous failure breaks
# the consecutive streak, so the record is truncated before appending.
oc_record_failure() {
  # $1 liveness dir, $2 agent id, $3 classification, $4 now, $5 workdir
  mkdir -p "$1/failures" || return 1
  oc_log=$1/failures/$2
  oc_sha=$(git -C "$5" rev-parse HEAD 2>/dev/null || printf -- -)
  oc_last=$(tail -n 1 "$oc_log" 2>/dev/null || true)
  case "$oc_last" in
    *" $oc_sha") : ;;
    *) [ -z "$oc_last" ] || : > "$oc_log" ;;
  esac
  printf '%s %s %s\n' "$4" "$3" "$oc_sha" >> "$oc_log"
  return 0
}

# Decide from the failure record alone (§3.1.5) whether a bounded reset is due:
# at least oc_threshold failures inside oc_window, cooldown expired. The
# currently-observed agent state is irrelevant to this decision.
oc_reset_due() {
  # $1 liveness dir, $2 agent id, $3 now; returns 0 when a reset is due
  oc_log=$1/failures/$2
  [ -s "$oc_log" ] || return 1
  oc_count=0
  while read -r oc_ts oc_cls oc_sha; do
    case "$oc_ts" in ''|*[!0-9]*) continue ;; esac
    if [ $((oc_ts + oc_window)) -gt "$3" ]; then
      oc_count=$((oc_count + 1))
    fi
  done < "$oc_log"
  [ "$oc_count" -ge "$oc_threshold" ] || return 1
  oc_last=0
  if [ -s "$1/last-reset-$2" ]; then
    oc_last=$(cat "$1/last-reset-$2")
    case "$oc_last" in ''|*[!0-9]*) oc_last=0 ;; esac
  fi
  [ $((oc_last + oc_cooldown)) -le "$3" ] || return 1
  return 0
}

# Clear the consecutive-failure record after a reset so the next streak starts
# at zero. History remains auditable in recoveries.log and the incident log.
oc_clear_failures() {
  # $1 liveness dir, $2 agent id
  : > "$1/failures/$2" 2>/dev/null || true
  return 0
}

# Surface a permanent failure (expired credential, invalid configuration)
# instead of resetting it (§3.1.3). Durable: survives the 24 h restart.
oc_surface_permanent() {
  # $1 liveness dir, $2 agent id, $3 classification
  printf '%s id=%s permanent_failure classification=%s surfaced-not-reset\n' \
    "$(date -u +%FT%TZ)" "$2" "$3" >> "$1/permanent-incidents.log"
  echo "Viche: permanent failure id=$2 classification=$3 surfaced, not reset (Act 19 §3.1)" >&2
  return 0
}

# Per-office commit-age signal (§3.3): recorded only while the office has
# uncommitted work. This is an observation (weak proxy), not a quota: it makes
# bounded work loss visible instead of looking merely "busy".
oc_commit_age_signal() {
  # $1 liveness dir, $2 agent id, $3 workdir, $4 now
  if [ ! -d "$3/.git" ] && [ ! -f "$3/.git" ]; then
    return 0
  fi
  oc_dirty=$(git -C "$3" status --porcelain 2>/dev/null || true)
  [ -n "$oc_dirty" ] || return 0
  oc_head=$(git -C "$3" rev-parse HEAD 2>/dev/null) || return 0
  [ -n "$oc_head" ] || return 0
  oc_cts=$(git -C "$3" show -s --format=%ct "$oc_head" 2>/dev/null) || return 0
  case "$oc_cts" in ''|*[!0-9]*) return 0 ;; esac
  mkdir -p "$1/commit-age" || return 1
  oc_age=$(($4 - oc_cts))
  printf '%s id=%s head=%s commit_age_seconds=%s uncommitted=yes\n' \
    "$(date -u +%FT%TZ)" "$2" "$oc_head" "$oc_age" >> "$1/commit-age.log"
  printf '%s %s %s\n' "$4" "$oc_cts" "$oc_head" > "$1/commit-age/$2"
  return 0
}

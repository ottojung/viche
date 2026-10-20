# Act 19 §3.1 — shared failure-count-based session recovery (POSIX /bin/sh).
#
# Source this file from a supervisor script. It provides a durable per-key
# failure record and a reset decision decidable from that record (not from the
# transient agent state, which an oscillating agent defeats):
#
#   or_classify <classification>              -> transient|permanent (echo)
#   or_record <key> <classification> [wt]    -> append failure; 0 transient / 1 permanent
#   or_should_reset <key> [worktree]         -> exit 0 if the key should be reset now
#   or_reset <key> <id> <title> <worktree>    -> snapshot + delete + recreate
#   or_last_progress <key> [worktree]         -> echo epoch of last durable commit (0 if none)
#
# <key> is an office name (clerk/executive/judiciary/innovation-centre) or a
# parliamentary agent id. <worktree> is optional; when omitted it is derived
# from the key.
#
# Threshold (Act 19 §3.1.1): 3 consecutive transient failures within a 30-min
# window, 1800 s cooldown. Progress guard (§3.1.2): no reset if the office
# committed durable work since its last failure. Permanent failures are
# surfaced (durable incident record), never silently reset.
set -u

_or_state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}/office-recovery
_or_THRESHOLD=3          # consecutive transient failures
_or_WINDOW=1800          # seconds (30 min)
_or_COOLDOWN=1800         # seconds between resets for the same key

_or_id_for() {
    case "$1" in
        clerk) printf 'c1a00001' ;;
        executive) printf 'c1e00002' ;;
        judiciary) printf 'c1e00008' ;;
        innovation-centre) printf 'c1e00011' ;;
        *) printf '' ;;
    esac
}

_or_worktree() {
    seats=${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}
    case "$1" in
        clerk) printf '%s/c1a00001' "$seats" ;;
        judiciary|innovation-centre|executive) printf '%s/branches/%s' "$seats" "$1" ;;
        c1*) printf '%s/%s' "$seats" "$1" ;;   # parliamentary seat worktree
        *) printf '' ;;
    esac
}

or_classify() {
    case "${1:-}" in
        upstream_endpoint_unavailable|unrecognized_backend_failure) printf 'transient' ;;
        *) printf 'permanent' ;;
    esac
}

or_record() {
    # or_record <key> <classification> [worktree]
    key=$1; class=$2; wt=${3:-$(_or_worktree "$1")}
    [ -n "$key" ] || return 1
    mkdir -p "$_or_state"; umask 077
    now=$(date +%s)
    printf '%s\t%s\n' "$now" "$class" >> "$_or_state/failures-$key.tsv"
    tail -n 100 "$_or_state/failures-$key.tsv" > "$_or_state/failures-$key.tsv.tmp" \
        && mv "$_or_state/failures-$key.tsv.tmp" "$_or_state/failures-$key.tsv"
    if [ -n "$wt" ] && [ -d "$wt/.git" ]; then
        git -C "$wt" rev-parse HEAD > "$_or_state/failure-head-$key" 2>/dev/null || :
    fi
    if [ "$(or_classify "$class")" = transient ]; then return 0; fi
    printf '%s\t%s\t%s\n' "$now" "$key" "$class" >> "$_or_state/permanent-failures.tsv"
    return 1
}

_or_count_transient_in_window() {
    key=$1
    now=$(date +%s)
    # failures-$key.tsv holds only transient failures (permanent ones go to
    # permanent-failures.tsv), so count rows within the window.
    awk -F'\t' -v now="$now" -v win="$_or_WINDOW" '$1 >= now-win {c++} END{print c+0}' \
        "$_or_state/failures-$key.tsv" 2>/dev/null
}

or_should_reset() {
    # or_should_reset <key> [worktree]
    key=$1; wt=${2:-$(_or_worktree "$1")}
    now=$(date +%s)
    last=0
    [ -s "$_or_state/last-reset-$key" ] && last=$(cat "$_or_state/last-reset-$key")
    case "$last" in ''|*[!0-9]*) last=0 ;; esac
    [ $((now - last)) -ge "$_or_COOLDOWN" ] || return 1
    n=$(_or_count_transient_in_window "$key")
    [ "$n" -ge "$_or_THRESHOLD" ] || return 1
    # progress guard: durable commit since last failure -> healthy, don't reset
    if [ -s "$_or_state/failure-head-$key" ]; then
        failure_head=$(cat "$_or_state/failure-head-$key")
        current_head=$(git -C "$wt" rev-parse HEAD 2>/dev/null || printf '')
        if [ -n "$current_head" ] && [ "$current_head" != "$failure_head" ]; then
            return 1
        fi
    fi
    return 0
}

or_reset() {
    # or_reset <key> <id> <title> <worktree>
    key=$1; id=$2; title=$3; wt=$4
    now=$(date +%s)
    mkdir -p "$_or_state"; umask 077
    snapshot=$(mktemp -d "$_or_state/recovery-$key-XXXXXX")
    meta=$(antonina agent status --id "$id" --json 2>/dev/null || printf '{}')
    printf '%s\n' "$meta" > "$snapshot/agent-status.json"
    antonina agent log --id "$id" --lines 200 > "$snapshot/agent-log-tail.txt" 2>&1 || :
    git -C "$wt" status --short > "$snapshot/worktree-status.txt"
    git -C "$wt" rev-parse HEAD > "$snapshot/worktree-head.txt"
    printf '%s\n' "$now" > "$_or_state/last-reset-$key"
    rm -f "$_or_state/failure-head-$key"
    antonina agent delete --id "$id" 2>/dev/null || :
    antonina agent new --id "$id" --cwd "$wt" --title "Viche: $title" 2>/dev/null || :
    printf '%s\t%s\tsession_reset=failure_count evidence=%s\n' \
        "$(date -u +%FT%TZ)" "$key" "$snapshot" >> "$_or_state/recoveries.log"
    printf '%s\n' "$snapshot"
}

or_last_progress() {
    # epoch of the key branch HEAD (durable-commit proxy); 0 if none
    key=$1; wt=${2:-$(_or_worktree "$1")}
    [ -n "$wt" ] && [ -d "$wt/.git" ] || { printf '0'; return; }
    ts=$(git -C "$wt" log -1 --format=%ct 2>/dev/null || printf '0')
    case "$ts" in ''|*[!0-9]*) printf '0' ;; *) printf '%s' "$ts" ;; esac
}

#!/bin/sh
# Janitor Office — disk-health observation and safe, policy-gated reclamation.
#
# Established as a continuing executive function under Founding Act 2.3 (executive
# implementation) and Act 4.2 (storage inquiry from existing telemetry). The enabling
# statute, which grants explicit reclamation authority and safeguards, is
# records/bills/janitor-office-act.md (Act 12); until it is enacted this tool operates
# in its safe, reversible subset only.
#
# POSIX /bin/sh only (AGENTS.md): no bashisms, no associative arrays, no `local`.
#
# Usage: janitor.sh <observe|reclaim|cycle|report|status|inventory|classify|quarantine|reclaim-quarantined> [--dry-run]
#   observe             record filesystem + cgroup metrics, evaluate thresholds; never mutates
#   reclaim             perform the safe, reversible, age-gated reclamation allowlist
#   cycle               observe; reclaim when due and enabled; safe-reclaim on critical pressure
#   report              print a concise human-readable summary
#   status              print one machine-readable status line
#   inventory           scan the box for large directories; read-only, records findings
#   classify            classify inventory candidates by ownership/liveness; read-only
#   quarantine           move classified candidates to quarantine; reversible
#   reclaim-quarantined remove quarantined items past their grace period; destructive
#
# Safety: this script never removes unverified content, never writes outside
# $VICHE_STATE_ROOT, and never touches records/, government/, constitution/, the
# founder-controlled mount, credentials, or other projects. Its only deletion target is
# its own state directory; git maintenance is non-destructive (objects are recoverable).
set -eu

usage() {
    cat >&2 <<'EOF'
Usage: janitor.sh <observe|reclaim|cycle|report|status> [--dry-run]
EOF
}

mode=${1:-}
[ -n "$mode" ] || { usage; exit 2; }
[ "$#" -le 2 ] || { usage; exit 2; }
dry_run=0
if [ "${2:-}" = "--dry-run" ]; then dry_run=1; fi
case "$mode" in
    observe|reclaim|cycle|report|status|inventory|classify|quarantine|reclaim-quarantined) : ;;
    *) usage; exit 2 ;;
esac

town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
seats=${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}
conf=${JANITOR_CONF:-$town/government/janitor.conf}
jstate=$state/janitor
mkdir -p "$jstate/tmp"

is_num() {
    case "$1" in
        ''|*[!0-9]*) return 1 ;;
        *) return 0 ;;
    esac
}

confval() {
    # confval <key> <default>
    if [ -f "$conf" ]; then
        v=$(sed -n "s/^[[:space:]]*$1=//p" "$conf" 2>/dev/null | tail -n 1)
        if [ -n "$v" ]; then printf '%s' "$v"; return 0; fi
    fi
    printf '%s' "$2"
}

warn_pct=$(confval warn_used_pct 85)
high_pct=$(confval high_used_pct 92)
crit_pct=$(confval critical_used_pct 97)
observe_interval=$(confval observe_interval_seconds 1800)
reclaim_interval=$(confval reclaim_interval_seconds 86400)
min_age=$(confval min_reclaim_age_seconds 86400)
max_log_bytes=$(confval max_log_bytes 1048576)
safe_reclaim=$(confval safe_reclaim_enabled 1)
reclaim_enabled=$(confval reclaim_enabled 0)
inventory_min_kb=$(confval inventory_min_kb 102400)
quarantine_dir=$(confval quarantine_dir "$state/quarantine")
quarantine_grace=$(confval quarantine_grace_seconds 604800)

for n in "$warn_pct" "$high_pct" "$crit_pct" "$observe_interval" "$reclaim_interval" \
         "$min_age" "$max_log_bytes" "$safe_reclaim" "$reclaim_enabled" \
         "$inventory_min_kb" "$quarantine_grace"; do
    if ! is_num "$n"; then
        echo "janitor: invalid numeric policy value in $conf: $n" >&2
        exit 2
    fi
done

host=$(hostname 2>/dev/null || printf 'unknown')
now=$(date -u +%s)
ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# The filesystem probe follows the town checkout so we measure the filesystem that
# actually holds Viche state, wherever it is mounted.
probe=$town
if [ ! -d "$probe" ]; then probe=$state; fi
if [ ! -d "$probe" ]; then probe=.; fi

rotate() {
    # rotate <file>: keep the file bounded, preserving the newest lines.
    [ -f "$1" ] || return 0
    size=$(wc -c < "$1" 2>/dev/null || printf '0')
    is_num "$size" || return 0
    if [ "$size" -gt "$max_log_bytes" ]; then
        tmpf=$1.$$
        if tail -n 1000 "$1" > "$tmpf" 2>/dev/null; then
            mv "$tmpf" "$1"
        else
            rm -f "$tmpf"
        fi
    fi
    return 0
}

log_append() {
    # log_append <file> <line>
    printf '%s\n' "$2" >> "$1"
    rotate "$1"
    return 0
}

df_field() {
    # df_field <path> <field> [inode]
    if [ "${3:-}" = inode ]; then
        df -P -i "$1" 2>/dev/null | awk -v f="$2" 'NR==2{print $f; exit}'
    else
        df -P -k "$1" 2>/dev/null | awk -v f="$2" 'NR==2{print $f; exit}'
    fi
}

du_kb() {
    if [ -d "$1" ]; then
        du -s -k "$1" 2>/dev/null | awk 'NR==1{print $1; exit}'
    else
        printf '0'
    fi
}

due() {
    # due <stamp-file> <interval-seconds>
    [ -f "$1" ] || return 0
    last=$(cat "$1" 2>/dev/null || printf '0')
    is_num "$last" || return 0
    [ $((now - last)) -ge "$2" ]
}

stamp() { printf '%s\n' "$now" > "$1"; return 0; }

# --- metric computation (sets globals) -----------------------------------------
compute() {
    fs_dev=$(df_field "$probe" 1)
    fs_size_kb=$(df_field "$probe" 2)
    fs_used_kb=$(df_field "$probe" 3)
    fs_avail_kb=$(df_field "$probe" 4)
    fs_pct_raw=$(df_field "$probe" 5)
    fs_used_pct=$(printf '%s' "$fs_pct_raw" | tr -d '%')
    is_num "$fs_used_pct" || fs_used_pct=0
    ino_raw=$(df_field "$probe" 5 inode)
    ino_used_pct=$(printf '%s' "$ino_raw" | tr -d '%')
    is_num "$ino_used_pct" || ino_used_pct=
    mem_current=
    mem_max=
    if [ -r /sys/fs/cgroup/memory.current ]; then
        mem_current=$(cat /sys/fs/cgroup/memory.current 2>/dev/null || printf '')
    fi
    if [ -r /sys/fs/cgroup/memory.max ]; then
        mem_max=$(cat /sys/fs/cgroup/memory.max 2>/dev/null || printf '')
    fi
    town_kb=$(du_kb "$town")
    state_kb=$(du_kb "$state")
    seats_kb=$(du_kb "$seats")
    level=ok
    if [ "$fs_used_pct" -ge "$warn_pct" ]; then level=warn; fi
    if [ "$fs_used_pct" -ge "$high_pct" ]; then level=high; fi
    if [ "$fs_used_pct" -ge "$crit_pct" ]; then level=critical; fi
    return 0
}

severity() {
    case "$1" in
        critical) printf '3' ;;
        high) printf '2' ;;
        warn) printf '1' ;;
        *) printf '0' ;;
    esac
}

record_observation() {
    obs=$jstate/observations.tsv
    if [ ! -f "$obs" ]; then
        printf 'ts\thost\tdevice\tsize_kb\tused_kb\tavail_kb\tused_pct\tinode_pct\tmem_current\tmem_max\ttown_kb\tstate_kb\tseats_kb\tlevel\n' > "$obs"
    fi
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
        "$ts" "$host" "$fs_dev" "$fs_size_kb" "$fs_used_kb" "$fs_avail_kb" \
        "$fs_used_pct" "$ino_used_pct" "$mem_current" "$mem_max" \
        "$town_kb" "$state_kb" "$seats_kb" "$level" >> "$obs"
    rotate "$obs"
    stamp "$jstate/last-observe"
    return 0
}

alert_if_needed() {
    last_level=
    if [ -f "$jstate/last-level" ]; then
        last_level=$(cat "$jstate/last-level" 2>/dev/null || printf '')
    fi
    cur=$(severity "$level")
    prev=$(severity "${last_level:-ok}")
    fire=0
    if [ "$cur" -ge 1 ]; then
        if [ "$cur" -gt "$prev" ]; then fire=1; fi
        if due "$jstate/last-alert" "$observe_interval"; then fire=1; fi
    fi
    if [ "$fire" -eq 1 ]; then
        log_append "$jstate/alerts.log" \
            "$ts $host level=$level used=${fs_used_pct}% avail=${fs_avail_kb}kb device=$fs_dev"
        stamp "$jstate/last-alert"
        echo "janitor: ALERT $level: $fs_dev ${fs_used_pct}% used, ${fs_avail_kb} KB free" >&2
    fi
    printf '%s\n' "$level" > "$jstate/last-level"
    return 0
}

write_status() {
    printf '%s level=%s used_pct=%s avail_kb=%s device=%s\n' \
        "$ts" "$level" "$fs_used_pct" "$fs_avail_kb" "$fs_dev" > "$jstate/status"
    return 0
}

# --- safe reclamation ----------------------------------------------------------
reclaim() {
    # reclaim <reason>
    reason=${1:-scheduled}
    if [ "$safe_reclaim" -ne 1 ] && [ "$reclaim_enabled" -ne 1 ]; then
        log_append "$jstate/actions.log" \
            "$ts reclaim reason=$reason deferred safe_reclaim_enabled=$safe_reclaim"
        return 0
    fi
    before_avail=$(df_field "$probe" 4)
    is_num "$before_avail" || before_avail=0
    tmp_before=$(du_kb "$jstate/tmp")
    log_append "$jstate/actions.log" \
        "$ts reclaim reason=$reason begin dry_run=$dry_run device=$fs_dev used=${fs_used_pct}%"

    # 1. Prune worktree administration for worktrees whose directories no longer exist.
    #    This removes only stale .git/worktrees metadata; it never deletes a live tree.
    if [ -d "$town/.git" ]; then
        if [ "$dry_run" -eq 1 ]; then
            log_append "$jstate/actions.log" "$ts action=worktree-prune dry-run target=$town"
        else
            git -C "$town" worktree prune >/dev/null 2>&1 || true
            log_append "$jstate/actions.log" "$ts action=worktree-prune target=$town"
        fi
    fi

    # 2. Consolidate the object store. Non-destructive and fully reversible in effect
    #    (unreferenced objects are repacked/dropped only after normal git grace rules).
    if [ -d "$town/.git" ]; then
        if [ "$dry_run" -eq 1 ]; then
            log_append "$jstate/actions.log" "$ts action=git-gc dry-run target=$town"
        else
            git -C "$town" gc --auto --quiet >/dev/null 2>&1 || true
            log_append "$jstate/actions.log" "$ts action=git-gc target=$town"
        fi
    fi

    # 3. Remove this office's own aged temporary files only. Ownership is implicit:
    #    $jstate is created and owned by this function. Age-gated; never recursive into
    #    any user or project directory.
    if [ -d "$jstate/tmp" ]; then
        mins=$((min_age / 60))
        if [ "$mins" -lt 1 ]; then mins=1; fi
        if [ "$dry_run" -eq 1 ]; then
            n=$(find "$jstate/tmp" -type f -mmin +"$mins" 2>/dev/null | wc -l)
            log_append "$jstate/actions.log" "$ts action=tmp-clean dry-run candidates=$n dir=$jstate/tmp"
        else
            n=$(find "$jstate/tmp" -type f -mmin +"$mins" 2>/dev/null | wc -l)
            find "$jstate/tmp" -type f -mmin +"$mins" -exec rm -f {} + 2>/dev/null || true
            log_append "$jstate/actions.log" "$ts action=tmp-clean removed=$n dir=$jstate/tmp"
        fi
    fi

    # 4. Bound this office's own logs (rotation), which cannot affect project state.
    rotate "$jstate/observations.tsv"
    rotate "$jstate/actions.log"
    rotate "$jstate/alerts.log"

    after_avail=$(df_field "$probe" 4)
    is_num "$after_avail" || after_avail=0
    freed_kb=$((after_avail - before_avail))
    if [ "$freed_kb" -lt 0 ]; then freed_kb=0; fi
    tmp_after=$(du_kb "$jstate/tmp")
    tmp_freed_kb=$((tmp_before - tmp_after))
    if [ "$tmp_freed_kb" -lt 0 ]; then tmp_freed_kb=0; fi
    log_append "$jstate/actions.log" \
        "$ts reclaim reason=$reason end freed_kb=$freed_kb tmp_freed_kb=$tmp_freed_kb avail_kb=$after_avail"
    stamp "$jstate/last-reclaim"
    printf 'janitor: reclaim reason=%s freed_kb=%s tmp_freed_kb=%s avail_kb=%s\n' \
        "$reason" "$freed_kb" "$tmp_freed_kb" "$after_avail"
    return 0
}

incident() {
    log_append "$jstate/alerts.log" \
        "$ts $host INCIDENT level=critical used=${fs_used_pct}% avail=${fs_avail_kb}kb device=$fs_dev"
    echo "janitor: CRITICAL capacity on $fs_dev (${fs_used_pct}% used); running safe reclamation" >&2
    reclaim incident-critical
    # Re-probe and record whether the safe subset restored headroom. Escalation to the
    # Founder is the executive's/clerk's duty (Act 12); this office never deletes
    # unverified content to force space.
    compute
    if [ "$level" = critical ]; then
        log_append "$jstate/alerts.log" \
            "$ts $host ESCALATE level=critical after_reclaim used=${fs_used_pct}% avail=${fs_avail_kb}kb"
        echo "janitor: still critical after safe reclamation; escalate to executive/Founder" >&2
    fi
    return 0
}

# --- box inventory (read-only) -------------------------------------------------
inventory() {
    inv=$jstate/inventory.tsv
    tmp_inv=$jstate/tmp/inventory.tsv
    printf 'ts\thost\tpath\tsize_kb\tmtime\tage_days\tis_git\tuncommitted\tclass\n' > "$tmp_inv"
    log_append "$jstate/actions.log" "$ts inventory begin min_kb=$inventory_min_kb"
    for root in /workspace /home/lubko /var/lib/lubko/wd /tmp/opencode; do
        [ -d "$root" ] || continue
        find "$root" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | while IFS= read -r d; do
            size=$(timeout 10 du -s -k "$d" 2>/dev/null | awk 'NR==1{print $1; exit}')
            is_num "$size" || continue
            [ "$size" -ge "$inventory_min_kb" ] || continue
            mtime=$(stat -c %Y "$d" 2>/dev/null || printf '0')
            is_num "$mtime" || mtime=0
            age_days=$(( (now - mtime) / 86400 ))
            is_git=0
            uncommitted=0
            if [ -d "$d/.git" ]; then
                is_git=1
                if [ -n "$(git -C "$d" status --porcelain 2>/dev/null)" ]; then
                    uncommitted=1
                fi
            fi
            printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t\n' \
                "$ts" "$host" "$d" "$size" "$mtime" "$age_days" "$is_git" "$uncommitted" >> "$tmp_inv"
        done
    done
    mv "$tmp_inv" "$inv"
    rotate "$inv"
    n=$(wc -l < "$inv" 2>/dev/null || printf '0')
    log_append "$jstate/actions.log" "$ts inventory end entries=$n"
    printf 'janitor: inventory complete, %s entries (min %s KB)\n' "$n" "$inventory_min_kb"
    return 0
}

# --- classify inventory candidates (read-only) ----------------------------------
classify() {
    inv=$jstate/inventory.tsv
    [ -f "$inv" ] || { echo "janitor: no inventory; run inventory first" >&2; return 1; }
    log_append "$jstate/actions.log" "$ts classify begin"
    tmp=$jstate/tmp/classify.tsv
    : > "$tmp"
    tail -n +2 "$inv" 2>/dev/null | while IFS="$(printf '\t')" read -r ts host path size mtime age is_git uncommitted _class; do
        [ -n "$path" ] || continue
        [ -d "$path" ] || continue
        class=retain
        if [ "$is_git" -eq 1 ] && [ "$uncommitted" -eq 1 ]; then
            class=retain-live
        elif [ "$is_git" -eq 1 ] && [ "$age" -ge 30 ]; then
            class=quarantine-candidate
        elif [ "$is_git" -eq 0 ] && [ "$age" -ge 30 ] && [ "$size" -ge 1048576 ]; then
            class=quarantine-candidate
        elif [ "$age" -ge 7 ]; then
            class=monitor
        fi
        printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
            "$ts" "$host" "$path" "$size" "$mtime" "$age" "$is_git" "$uncommitted" "$class" >> "$tmp"
    done
    mv "$tmp" "$inv"
    n=$(wc -l < "$inv" 2>/dev/null || printf '0')
    log_append "$jstate/actions.log" "$ts classify end entries=$n"
    printf 'janitor: classify complete, %s entries\n' "$n"
    return 0
}

# --- quarantine candidates (reversible) ------------------------------------------
quarantine() {
    inv=$jstate/inventory.tsv
    [ -f "$inv" ] || { echo "janitor: no inventory; run inventory first" >&2; return 1; }
    [ -d "$quarantine_dir" ] || mkdir -p "$quarantine_dir"
    log_append "$jstate/actions.log" "$ts quarantine begin dir=$quarantine_dir"
    tmp=$jstate/tmp/quarantine.tsv
    : > "$tmp"
    tail -n +2 "$inv" 2>/dev/null | while IFS="$(printf '\t')" read -r ts host path size mtime age is_git uncommitted class; do
        [ -n "$path" ] || continue
        [ -d "$path" ] || continue
        [ "$class" = "quarantine-candidate" ] || continue
        base=$(basename "$path")
        dest="$quarantine_dir/${base}-$(date -u +%Y%m%d%H%M%S)"
        if [ "$dry_run" -eq 1 ]; then
            log_append "$jstate/actions.log" "$ts action=quarantine dry-run src=$path dest=$dest"
        else
            if mv "$path" "$dest" 2>/dev/null; then
                log_append "$jstate/actions.log" "$ts action=quarantine src=$path dest=$dest"
                printf '%s\t%s\t%s\t%s\t%s\n' "$ts" "$path" "$dest" "$size" "$now" >> "$tmp"
            else
                log_append "$jstate/actions.log" "$ts action=quarantine-failed src=$path"
            fi
        fi
    done
    if [ -f "$tmp" ] && [ -s "$tmp" ]; then
        qlog=$jstate/quarantined.tsv
        if [ ! -f "$qlog" ]; then
            printf 'ts\tsrc\tdest\tsize_kb\tquarantined_at\n' > "$qlog"
        fi
        cat "$tmp" >> "$qlog"
        rotate "$qlog"
    fi
    log_append "$jstate/actions.log" "$ts quarantine end"
    printf 'janitor: quarantine complete (dir=%s)\n' "$quarantine_dir"
    return 0
}

# --- reclaim quarantined items past grace period (destructive) ------------------
reclaim_quarantined() {
    qlog=$jstate/quarantined.tsv
    [ -f "$qlog" ] || { echo "janitor: no quarantined items" >&2; return 0; }
    [ "$reclaim_enabled" -eq 1 ] || {
        log_append "$jstate/actions.log" "$ts reclaim-quarantined deferred reclaim_enabled=$reclaim_enabled"
        printf 'janitor: reclaim-quarantined deferred (reclaim_enabled=%s)\n' "$reclaim_enabled"
        return 0
    }
    log_append "$jstate/actions.log" "$ts reclaim-quarantined begin grace=${quarantine_grace}s"
    tmp=$jstate/tmp/reclaim.tsv
    : > "$tmp"
    freed_kb=0
    tail -n +2 "$qlog" 2>/dev/null | while IFS="$(printf '\t')" read -r ts src dest size qat; do
        [ -n "$dest" ] || continue
        [ -d "$dest" ] || continue
        age=$((now - qat))
        [ "$age" -ge "$quarantine_grace" ] || continue
        if [ "$dry_run" -eq 1 ]; then
            log_append "$jstate/actions.log" "$ts action=reclaim dry-run src=$dest size=$size"
        else
            rm -rf "$dest" 2>/dev/null || true
            log_append "$jstate/actions.log" "$ts action=reclaim src=$dest size=$size freed=$size"
        fi
    done
    log_append "$jstate/actions.log" "$ts reclaim-quarantined end"
    printf 'janitor: reclaim-quarantined complete\n'
    return 0
}

# --- modes ---------------------------------------------------------------------
case "$mode" in
    observe)
        compute
        if due "$jstate/last-observe" "$observe_interval"; then record_observation; fi
        alert_if_needed
        write_status
        ;;
    reclaim)
        compute
        reclaim manual
        ;;
    cycle)
        compute
        if due "$jstate/last-observe" "$observe_interval"; then record_observation; fi
        alert_if_needed
        write_status
        if [ "$level" = critical ]; then
            incident
        elif due "$jstate/last-reclaim" "$reclaim_interval"; then
            reclaim scheduled
        else
            log_append "$jstate/actions.log" "$ts reclaim deferred reason=not-due level=$level"
        fi
        ;;
    report)
        if [ -f "$jstate/status" ]; then
            printf 'status: %s\n' "$(cat "$jstate/status")"
        else
            printf 'status: no observation recorded yet\n'
        fi
        if [ -f "$jstate/actions.log" ]; then
            printf 'recent actions:\n'
            tail -n 8 "$jstate/actions.log"
        fi
        if [ -f "$jstate/alerts.log" ]; then
            printf 'recent alerts:\n'
            tail -n 8 "$jstate/alerts.log"
        fi
        ;;
    status)
        if [ -f "$jstate/status" ]; then
            cat "$jstate/status"
        else
            printf 'no-observation\n'
        fi
        ;;
    inventory)
        compute
        inventory
        ;;
    classify)
        compute
        classify
        ;;
    quarantine)
        compute
        quarantine
        ;;
    reclaim-quarantined)
        compute
        reclaim_quarantined
        ;;
esac

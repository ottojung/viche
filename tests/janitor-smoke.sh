#!/bin/sh
# Janitor Office regression: observation records metrics, reclamation is age-gated and
# allowlisted, protected state is never touched, dry-run mutates nothing, and critical
# capacity triggers safe reclamation. POSIX /bin/sh only.
set -eu
root=$(git rev-parse --show-toplevel)
d=$(mktemp -d)
trap 'rm -rf "$d"' 0
town=$d/town
state=$d/state
seats=$d/seats
mkdir -p "$town/government" "$state/founder-inbox/pending" "$seats" "$d/bin"
cp "$root/government/janitor.sh" "$town/government/janitor.sh"
cp "$root/government/janitor.conf" "$town/government/janitor.conf"
git -C "$town" init -q

# Protected state that must survive every janitor action.
printf 'durable record\n' > "$town/records-important.md"
printf 'pending founder event\n' > "$state/founder-inbox/pending/keep.json"

# Aged, janitor-owned junk and fresh files.
mkdir -p "$state/janitor/tmp"
printf 'old junk\n' > "$state/janitor/tmp/old.tmp"
printf 'fresh\n' > "$state/janitor/tmp/fresh.tmp"
touch -d '3 days ago' "$state/janitor/tmp/old.tmp"
# Pre-stamp the inventory clock so the hermetic cycle does not scan the real box
# (the box inventory is exercised separately; this keeps the test isolated/fast).
date +%s > "$state/janitor/last-inventory"

VICHE_TOWN_ROOT=$town
VICHE_STATE_ROOT=$state
VICHE_SEATS_ROOT=$seats
export VICHE_TOWN_ROOT VICHE_STATE_ROOT VICHE_SEATS_ROOT

# 1. observe records a sample and a status line, mutating no protected state.
/bin/sh "$town/government/janitor.sh" observe
[ -f "$state/janitor/observations.tsv" ]
[ "$(wc -l < "$state/janitor/observations.tsv")" -ge 2 ]
[ -f "$state/janitor/status" ]
grep -q 'level=' "$state/janitor/status"

# 2. dry-run reclamation changes nothing.
/bin/sh "$town/government/janitor.sh" reclaim --dry-run
[ -f "$state/janitor/tmp/old.tmp" ]
grep -q 'dry-run' "$state/janitor/actions.log"

# 3. real safe reclamation removes only the aged janitor-owned file.
/bin/sh "$town/government/janitor.sh" reclaim
[ ! -f "$state/janitor/tmp/old.tmp" ]
[ -f "$state/janitor/tmp/fresh.tmp" ]
[ -f "$town/records-important.md" ]
[ -f "$state/founder-inbox/pending/keep.json" ]
grep -q 'tmp_freed_kb=' "$state/janitor/actions.log"

# 4. disabled policy defers reclamation (nothing removed).
printf 'x\n' > "$state/janitor/tmp/old2.tmp"
touch -d '3 days ago' "$state/janitor/tmp/old2.tmp"
printf 'safe_reclaim_enabled=0\n' >> "$town/government/janitor.conf"
/bin/sh "$town/government/janitor.sh" reclaim
[ -f "$state/janitor/tmp/old2.tmp" ]
grep -q 'deferred' "$state/janitor/actions.log"

# 5. critical capacity triggers the incident safe-reclaim and a durable alert.
cat > "$d/bin/df" <<'MOCK'
#!/bin/sh
inode=0
for a in "$@"; do [ "$a" = "-i" ] && inode=1; done
if [ "$inode" = 1 ]; then
    printf 'Filesystem Inodes IUsed IFree IUse%% Mounted on\n'
    printf '/dev/fake 1000 100 900 10%% /\n'
else
    printf 'Filesystem 1024-blocks Used Available Capacity Mounted on\n'
    printf '/dev/fake 1000000 990000 10000 99%% /\n'
fi
MOCK
chmod +x "$d/bin/df"
PATH="$d/bin:$PATH"
export PATH
/bin/sh "$town/government/janitor.sh" cycle
grep -q 'INCIDENT level=critical' "$state/janitor/alerts.log"
grep -q 'level=critical' "$state/janitor/status"

# 6. reclaim-quarantined removes only items past the grace window (when enabled);
#    the quarantine dir is state-relative, so the live quarantine is untouched.
q=$state/quarantine
mkdir -p "$q/old-item" "$q/new-item"
printf 'x\n' > "$q/old-item/f"
printf 'x\n' > "$q/new-item/f"
now=$(date -u +%s)
{
    printf 'ts\tsrc\tdest\tsize_kb\tquarantined_at\n'
    printf '2026-01-01T00:00:00Z\t/old\t%s/old-item\t1\t1\n' "$q"
    printf '2026-01-01T00:00:00Z\t/new\t%s/new-item\t1\t%s\n' "$q" "$now"
} > "$state/janitor/quarantined.tsv"
printf 'safe_reclaim_enabled=1\nreclaim_enabled=1\n' >> "$town/government/janitor.conf"
/bin/sh "$town/government/janitor.sh" reclaim-quarantined
[ ! -d "$q/old-item" ]
[ -d "$q/new-item" ]

# 7. build-cache (.lake) classification: a live/recent cache is only monitored;
#    an aged cache whose parent worktree is also aged is a quarantine candidate.
box=$d/box
mkdir -p "$box/live-work/.lake" "$box/aged-work/.lake"
printf 'x\n' > "$box/live-work/.lake/f"
printf 'x\n' > "$box/aged-work/.lake/f"
touch -d '2 days ago' "$box/live-work/.lake" "$box/live-work"
touch -d '40 days ago' "$box/aged-work/.lake" "$box/aged-work"
now=$(date -u +%s)
host=phoebe-dev
live_mtime=$(stat -c %Y "$box/live-work/.lake")
aged_mtime=$(stat -c %Y "$box/aged-work/.lake")
live_age=$(( (now - live_mtime) / 86400 ))
aged_age=$(( (now - aged_mtime) / 86400 ))
{
    printf 'ts\thost\tpath\tsize_kb\tmtime\tage_days\tis_git\tuncommitted\tunpushed\tclass\n'
    printf '2026-01-01T00:00:00Z\t%s\t%s\t1024\t%s\t5\t0\t0\t0\t\n' "$host" "$box/live-work" "$live_mtime"
    printf '2026-01-01T00:00:00Z\t%s\t%s\t1024\t%s\t%s\t0\t0\t0\t\n' "$host" "$box/live-work/.lake" "$live_mtime" "$live_age"
    printf '2026-01-01T00:00:00Z\t%s\t%s\t1024\t%s\t40\t0\t0\t0\t\n' "$host" "$box/aged-work" "$aged_mtime"
    printf '2026-01-01T00:00:00Z\t%s\t%s\t1024\t%s\t%s\t0\t0\t0\t\n' "$host" "$box/aged-work/.lake" "$aged_mtime" "$aged_age"
} > "$state/janitor/inventory.tsv"
/bin/sh "$town/government/janitor.sh" classify
awk -F'\t' 'NR>1 && $3=="'"$box"'/live-work/.lake" {print $10}' "$state/janitor/inventory.tsv" | grep -qx 'monitor'
awk -F'\t' 'NR>1 && $3=="'"$box"'/aged-work/.lake" {print $10}' "$state/janitor/inventory.tsv" | grep -qx 'quarantine-candidate'

# 8. build-toolchain classification: an aged, large Lean/elAN toolchain install is a
#    live build dependency (the project's pinned toolchain), NOT clutter. It must be
#    retained, never quarantined, even though it is non-git, old and >=1 GB (J2).
tbox=$d/tbox
mkdir -p "$tbox/proj/.elan/toolchains/leanprover--lean4---v4.34.0/bin"
printf 'x\n' > "$tbox/proj/.elan/toolchains/leanprover--lean4---v4.34.0/bin/lean"
touch -d '40 days ago' "$tbox/proj/.elan/toolchains/leanprover--lean4---v4.34.0" \
    "$tbox/proj/.elan/toolchains" "$tbox/proj/.elan" "$tbox/proj"
now=$(date -u +%s)
tc_mtime=$(stat -c %Y "$tbox/proj/.elan/toolchains/leanprover--lean4---v4.34.0")
el_mtime=$(stat -c %Y "$tbox/proj/.elan/toolchains")
top_mtime=$(stat -c %Y "$tbox/proj/.elan")
{
    printf 'ts\thost\tpath\tsize_kb\tmtime\tage_days\tis_git\tuncommitted\tunpushed\tclass\n'
    printf '2026-01-01T00:00:00Z\t%s\t%s\t1024\t%s\t40\t0\t0\t0\t\n' "$host" "$tbox/proj/.elan" "$top_mtime"
    printf '2026-01-01T00:00:00Z\t%s\t%s\t1024\t%s\t40\t0\t0\t0\t\n' "$host" "$tbox/proj/.elan/toolchains" "$el_mtime"
    printf '2026-01-01T00:00:00Z\t%s\t%s\t2097152\t%s\t40\t0\t0\t0\t\n' "$host" \
        "$tbox/proj/.elan/toolchains/leanprover--lean4---v4.34.0" "$tc_mtime"
} > "$state/janitor/inventory.tsv"
/bin/sh "$town/government/janitor.sh" classify
awk -F'\t' 'NR>1 && $3=="'"$tbox"'/proj/.elan" {print $10}' \
    "$state/janitor/inventory.tsv" | grep -qx 'retain'
awk -F'\t' 'NR>1 && $3=="'"$tbox"'/proj/.elan/toolchains" {print $10}' \
    "$state/janitor/inventory.tsv" | grep -qx 'retain'
awk -F'\t' 'NR>1 && $3=="'"$tbox"'/proj/.elan/toolchains/leanprover--lean4---v4.34.0" {print $10}' \
    "$state/janitor/inventory.tsv" | grep -qx 'retain'

# 9. Act 12.4(d) liveness gate: a quarantine candidate with a live process cwd
#    inside it is retain-live, never a removal candidate; the check is logged.
lbox=$d/lbox
mkdir -p "$lbox/live-target"
printf 'x\n' > "$lbox/live-target/f"
touch -d '40 days ago' "$lbox/live-target"
( cd "$lbox/live-target" && sleep 15 & )
lt_mtime=$(stat -c %Y "$lbox/live-target")
{
    printf 'ts\thost\tpath\tsize_kb\tmtime\tage_days\tis_git\tuncommitted\tunpushed\tclass\n'
    printf '2026-01-01T00:00:00Z\t%s\t%s\t2097152\t%s\t40\t0\t0\t0\t\n' "$host" "$lbox/live-target" "$lt_mtime"
} > "$state/janitor/inventory.tsv"
/bin/sh "$town/government/janitor.sh" classify
awk -F'\t' 'NR>1 && $3=="'"$lbox"'/live-target" {print $10}' "$state/janitor/inventory.tsv" | grep -qx 'retain-live'
grep -q 'liveness-gate.*result=in-use' "$state/janitor/actions.log"

# 10. An aged .lake cache whose parent worktree still has a live process is
#     retained: worktree liveness implies the cache may be in active use.
pbox=$d/pbox
mkdir -p "$pbox/live-parent/.lake"
printf 'x\n' > "$pbox/live-parent/.lake/f"
touch -d '40 days ago' "$pbox/live-parent/.lake" "$pbox/live-parent"
( cd "$pbox/live-parent" && sleep 15 & )
lp_mtime=$(stat -c %Y "$pbox/live-parent")
ll_mtime=$(stat -c %Y "$pbox/live-parent/.lake")
{
    printf 'ts\thost\tpath\tsize_kb\tmtime\tage_days\tis_git\tuncommitted\tunpushed\tclass\n'
    printf '2026-01-01T00:00:00Z\t%s\t%s\t2097152\t%s\t40\t0\t0\t0\t\n' "$host" "$pbox/live-parent" "$lp_mtime"
    printf '2026-01-01T00:00:00Z\t%s\t%s\t1024\t%s\t40\t0\t0\t0\t\n' "$host" "$pbox/live-parent/.lake" "$ll_mtime"
} > "$state/janitor/inventory.tsv"
/bin/sh "$town/government/janitor.sh" classify
awk -F'\t' 'NR>1 && $3=="'"$pbox"'/live-parent/.lake" {print $10}' "$state/janitor/inventory.tsv" | grep -qx 'retain-live'
grep -q 'liveness-gate.*parent='"$pbox"'/live-parent.*result=in-use' "$state/janitor/actions.log"

# 11. With no live process, the same aged structure stays a quarantine candidate
#     (the gate retains, it does not loosen, classification).
qbox=$d/qbox
mkdir -p "$qbox/dead-parent/.lake"
printf 'x\n' > "$qbox/dead-parent/.lake/f"
touch -d '40 days ago' "$qbox/dead-parent/.lake" "$qbox/dead-parent"
dp_mtime=$(stat -c %Y "$qbox/dead-parent")
dl_mtime=$(stat -c %Y "$qbox/dead-parent/.lake")
{
    printf 'ts\thost\tpath\tsize_kb\tmtime\tage_days\tis_git\tuncommitted\tunpushed\tclass\n'
    printf '2026-01-01T00:00:00Z\t%s\t%s\t2097152\t%s\t40\t0\t0\t0\t\n' "$host" "$qbox/dead-parent" "$dp_mtime"
    printf '2026-01-01T00:00:00Z\t%s\t%s\t1024\t%s\t40\t0\t0\t0\t\n' "$host" "$qbox/dead-parent/.lake" "$dl_mtime"
} > "$state/janitor/inventory.tsv"
/bin/sh "$town/government/janitor.sh" classify
awk -F'\t' 'NR>1 && $3=="'"$qbox"'/dead-parent/.lake" {print $10}' "$state/janitor/inventory.tsv" | grep -qx 'quarantine-candidate'

# 12. Concurrency lock: a held lock makes a second mutating run skip cleanly
#     instead of interleaving appends (the 2026-10-20 duplicate-inventory race).
mkdir -p "$state/janitor/lock"
/bin/sh "$town/government/janitor.sh" classify >/dev/null 2>&1
# The stale lock (empty, old) is reclaimed rather than blocking forever.
touch -d '1 hour ago' "$state/janitor/lock"
/bin/sh "$town/government/janitor.sh" classify >/dev/null 2>&1
[ ! -d "$state/janitor/lock" ] || { echo "lock not released"; exit 1; }
grep -q 'lock-stale removed' "$state/janitor/actions.log"

# 13. Territorial accounting (Act 12.2, #298/#299): box_visible_kb sums distinct
#     top-level paths only. A nested .lake row is NOT double-counted, so the
#     total stays below the device rather than inflating past it.
ibox=$d/ibox
mkdir -p "$ibox/parent/.lake" "$ibox/plain"
printf 'aaaaaaaaaa\n' > "$ibox/parent/f"
printf 'bbbbbbbbbb\n' > "$ibox/parent/.lake/f"
printf 'cccccccccc\n' > "$ibox/plain/f"
printf 'inventory_min_kb=1\n' >> "$town/government/janitor.conf"
JANITOR_ROOTS=$ibox JANITOR_FILE_ROOTS=$ibox \
    /bin/sh "$town/government/janitor.sh" inventory
parent_kb=$(du -sk "$ibox/parent" | awk 'NR==1{print $1}')
plain_kb=$(du -sk "$ibox/plain" | awk 'NR==1{print $1}')
want=$((parent_kb + plain_kb))
got=$(awk -F'\t' 'NR==2{print $7}' "$state/janitor/territorial.tsv")
[ "$got" = "$want" ] || { echo "territorial box_visible got=$got want=$want"; exit 1; }

# 14. Runtime scratch eligibility keys on the OLDEST file, and the batch-level
#     live flag no longer blocks staging: an aged file is staged while a fresh
#     one is left in place (per-file age/reference checks keep it safe).
sdir=$d/scratch
mkdir -p "$sdir"
printf 'old\n' > "$sdir/.bcfold"
printf 'new\n' > "$sdir/.bcfnew"
touch -d '2 days ago' "$sdir/.bcfold"
export JANITOR_SCRATCH_DIR=$sdir
JANITOR_ROOTS=$ibox JANITOR_FILE_ROOTS=$ibox \
    /bin/sh "$town/government/janitor.sh" inventory
verdict=$(tail -n 1 "$state/janitor/scratch.tsv" | cut -f9)
[ "$verdict" = "quarantine-eligible" ] || { echo "scratch verdict=$verdict"; exit 1; }
/bin/sh "$town/government/janitor.sh" scratch-quarantine
[ ! -f "$sdir/.bcfold" ] || { echo "aged scratch not staged"; exit 1; }
[ -f "$sdir/.bcfnew" ] || { echo "fresh scratch wrongly staged"; exit 1; }
unset JANITOR_SCRATCH_DIR

printf 'Viche: janitor observes metrics, reclaims only aged owned files, protects durable state, defers when disabled, responds to critical capacity, reclaims only quarantined items past grace, classifies build caches by liveness, retains live build toolchains, and gates quarantine on a recorded Act 12.4(d) liveness check\n'

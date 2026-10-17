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

printf 'Viche: janitor observes metrics, reclaims only aged owned files, protects durable state, defers when disabled, responds to critical capacity, reclaims only quarantined items past grace, and classifies build caches by liveness\n'

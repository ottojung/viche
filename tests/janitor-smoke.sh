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

printf 'Viche: janitor observes metrics, reclaims only aged owned files, protects durable state, defers when disabled, and responds to critical capacity\n'

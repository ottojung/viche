#!/bin/sh
# Copied test boots and secondary worktrees must never touch live PnP.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
mkdir -p "$tmp/town/missions/pnp" "$tmp/bin"
for f in runtime.sh cycle.sh heartbeat.sh allocator.sh executive.sh status.sh; do
    cp "$repo/missions/pnp/$f" "$tmp/town/missions/pnp/$f"
done
# If any launch proceeds past the guard, the fake marker will detect it.
printf '#!/bin/sh\ntouch "$PNP_TEST_MARKER"\nexit 99\n' > "$tmp/bin/python3"
cp "$tmp/bin/python3" "$tmp/bin/nohup"
chmod +x "$tmp/bin/"*
touch "$tmp/town/missions/pnp/cli.py" "$tmp/town/missions/pnp/allocator.py"
export PNP_TEST_MARKER="$tmp/side-effect" PATH="$tmp/bin:$PATH"
export VICHE_TOWN_ROOT="$tmp/town" VICHE_STATE_ROOT="$tmp/state"
unset PNP_STATE_ROOT
for f in cycle.sh heartbeat.sh allocator.sh executive.sh; do
    timeout 3 /bin/sh "$tmp/town/missions/pnp/$f" 2>"$tmp/err"
    grep -q 'skipped outside canonical deployment' "$tmp/err"
done
test "$(/bin/sh "$tmp/town/missions/pnp/status.sh" 2>/dev/null)" = '{}'
test ! -e "$tmp/state"
test ! -e "$PNP_TEST_MARKER"
# Even if a copied launcher inherits production roots, its actual pathname
# still disqualifies it. This exercises the most dangerous test configuration.
unset VICHE_TOWN_ROOT VICHE_STATE_ROOT
for f in cycle.sh heartbeat.sh allocator.sh executive.sh; do
    timeout 3 /bin/sh "$tmp/town/missions/pnp/$f" 2>"$tmp/err"
    grep -q 'skipped outside canonical deployment' "$tmp/err"
done
test ! -e "$PNP_TEST_MARKER"
# Conversely a source-worktree launcher cannot use a noncanonical root.
VICHE_TOWN_ROOT="$tmp/town" VICHE_STATE_ROOT="$tmp/state" \
    timeout 3 /bin/sh "$repo/missions/pnp/cycle.sh" 2>"$tmp/err"
grep -q 'skipped outside canonical deployment' "$tmp/err"
echo 'PnP production daemon/test isolation passed'

#!/bin/sh
# Bounded, nonblocking lease heartbeat for the P vs NP desk broker.
#
# The desk expires a lease 20 minutes after the last beat. The boot-time
# mission hook runs only once per 24-hour host restart, which cannot keep a
# lease alive while an agent proves a gap. This loop renews every active
# lease every seven minutes and exits when no active lease remains, so it
# cannot run forever or compete with the Executive's research scheduling.
set -eu

town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
export PATH=/home/lubko/.local/bin:/home/lubko/.elan/bin:/var/guix/profiles/per-user/user1/guix-profile/bin:/run/current-system/profile/bin:${PATH:-/bin}

cd "$town"
[ -f missions/pnp/cli.py ] || exit 0
mkdir -p "$state/pnp"

# Only one heartbeat loop per host. If a previous loop is still running, exit.
exec 9>"$state/pnp/heartbeat.lock"
flock -n 9 || exit 0

i=0
idle=0
# 240 iterations * 7 min = 28 h upper bound, longer than the 24 h boot cycle.
while [ "$i" -lt 240 ]; do
    i=$((i + 1))
    sleep 420
    active=$(python3 - "$state" <<'PY'
import glob, json, os, sys
root = os.path.join(sys.argv[1], "pnp", "gaps")
live = ("LEASED", "RESEARCHING", "CANDIDATE_READY", "LOCAL_CHECKED")
n = 0
for path in glob.glob(os.path.join(root, "*", "state.json")):
    try:
        with open(path, encoding="utf-8") as f:
            rec = json.load(f)
    except (OSError, ValueError):
        continue
    if rec.get("lease") and rec.get("state") in live:
        n += 1
print(n)
PY
) || active=0
    if [ "$active" -eq 0 ]; then
        idle=$((idle + 1))
        [ "$idle" -ge 3 ] && break
    else
        idle=0
        # reconcile renews all active leases and recovers queued publications.
        python3 missions/pnp/cli.py reconcile >/dev/null 2>&1 || :
    fi
done

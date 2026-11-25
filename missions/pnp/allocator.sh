#!/bin/sh
# A single persistent, cheap allocator, including when no lease exists.
set -eu
. "$(dirname "$0")/runtime.sh"
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
state=${PNP_STATE_ROOT:-/var/lib/lubko/wd/viche-state/pnp}
export PATH=/home/lubko/.local/bin:/home/lubko/.elan/bin:/var/guix/profiles/per-user/user1/guix-profile/bin:/run/current-system/profile/bin:${PATH:-/bin}
cd "$town"
mkdir -p "$state"
exec 9>"$state/allocator-loop.lock"
flock -n 9 || exit 0
mkdir -p "$state/lbcert" "$state/bulk"
while [ -f missions/pnp/allocator.py ]; do
    # Keep exactly one certificate pre-generator alive (it holds its own lock; see missions/pnp/lbcert).
    if [ ! -f "$state/lbcert/STOP" ] && flock -n "$state/lbcert/autosolve.lock" true; then
        nohup python3 -m missions.pnp.lbcert.autosolve >> "$state/lbcert/autosolve.log" 2>&1 &
    fi
    # ... and exactly one bulk lane (publishes generated proofs of unheld, unclaimed steps; see bulk.py).
    if [ ! -f "$state/bulk/STOP" ] && flock -n "$state/bulk/bulk.lock" true; then
        nohup python3 -m missions.pnp.bulk >> "$state/bulk/bulk.log" 2>&1 &
    fi
    # Each desk request has bounded I/O; never kill a claim between receipt
    # and durable recording just because a tick took longer than expected.
    python3 -m missions.pnp.allocator || :
    sleep 30
done

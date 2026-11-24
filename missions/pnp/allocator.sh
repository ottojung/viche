#!/bin/sh
# A single persistent, cheap allocator, including when no lease exists.
set -eu
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
state=${PNP_STATE_ROOT:-/var/lib/lubko/wd/viche-state/pnp}
export PATH=/home/lubko/.local/bin:/home/lubko/.elan/bin:/var/guix/profiles/per-user/user1/guix-profile/bin:/run/current-system/profile/bin:${PATH:-/bin}
cd "$town"
mkdir -p "$state"
exec 9>"$state/allocator-loop.lock"
flock -n 9 || exit 0
while [ -f missions/pnp/allocator.py ]; do
    # Each desk request has bounded I/O; never kill a claim between receipt
    # and durable recording just because a tick took longer than expected.
    python3 -m missions.pnp.allocator || :
    sleep 30
done

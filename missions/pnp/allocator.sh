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
mkdir -p "$state/cache"
last_maintenance=0
last_observation=0
last_readiness=0
last_readiness_mode=unknown
while [ -f missions/pnp/allocator.py ]; do
    # Keep fresh allocation and generation separate from slow roster/network
    # maintenance. Only this loop writes allocator memory and calls next.
    now=$(date +%s)
    if [ "$((now - last_observation))" -ge 15 ]; then
        last_observation=$now
        nohup flock -n "$state/cache/allocator-observe.lock" timeout 45 \
            python3 -m missions.pnp.allocator --observe \
            </dev/null >>"$state/cache/allocator-observe.log" 2>&1 9>&- &
    fi
    # The probe is observational and never blocks the posting lane.
    # Run hourly and at the first observation of a surge; no overlap.
    readiness_mode=$(python3 -m missions.pnp.surge --mode 2>/dev/null || echo unknown)
    if [ "$((now - last_readiness))" -ge 3600 ] || \
       { [ "$readiness_mode" = surge ] && [ "$last_readiness_mode" != surge ]; }; then
        last_readiness=$now
        nohup flock -n "$state/cache/readiness.lock" timeout -k 5 150 \
            python3 -m missions.pnp.readiness </dev/null >>"$state/cache/readiness.log" 2>&1 9>&- &
    fi
    last_readiness_mode=$readiness_mode
    python3 -m missions.pnp.allocator --posting || :
    now=$(date +%s)
    if [ "$((now - last_maintenance))" -lt 30 ]; then
        sleep 5
        continue
    fi
    last_maintenance=$now
    # Keep exactly one certificate pre-generator alive (it holds its own lock; see missions/pnp/lbcert).
    if python3 -m missions.pnp.pause allowed && flock -n "$state/lbcert/autosolve.lock" true; then
        nohup python3 -m missions.pnp.lbcert.autosolve >> "$state/lbcert/autosolve.log" 2>&1 9>&- &
    fi
    # Keep receipt collection independent of agent turns and expensive desk I/O.
    mkdir -p "$state/cache"
    nohup flock -n "$state/cache/research-reconcile.lock" timeout 90 \
        python3 -m missions.pnp.research.obligations reconcile \
        </dev/null >>"$state/cache/research-reconcile.log" 2>&1 9>&- &
    # Each desk request has bounded I/O; never kill a claim between receipt
    # and durable recording just because a tick took longer than expected.
    python3 -m missions.pnp.allocator --cached || :
    sleep 5
done

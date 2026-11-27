#!/bin/sh
# Durable nonblocking P vs NP lease maintenance, invoked each Town boot cycle.
# Staffing is independently reconciled under the standing founder order.
set -eu
. "$(dirname "$0")/runtime.sh"
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
export PATH=/home/lubko/.local/bin:/home/lubko/.elan/bin:/var/guix/profiles/per-user/user1/guix-profile/bin:/run/current-system/profile/bin:${PATH:-/bin}
[ -r "$town/missions/pnp/cli.py" ] || exit 0
cd "$town"
# Start the work-conserving allocator before optional slow network work.
mkdir -p "${PNP_STATE_ROOT:-/var/lib/lubko/wd/viche-state/pnp}"
if [ ! -d /run/service/viche-pnp-allocator ]; then
    nohup setsid /bin/sh "$town/missions/pnp/allocator.sh" </dev/null \
        >>"${PNP_STATE_ROOT:-/var/lib/lubko/wd/viche-state/pnp}/allocator.log" 2>&1 &
fi
# Observation must continue even while certificate generation is STOPped.
nohup setsid /bin/sh "$town/missions/pnp/catalog.sh" </dev/null \
    >>"${PNP_STATE_ROOT}/catalog.log" 2>&1 &
# Supervise the standing staffing controller independently of model sessions.
# It owns its lifetime lock, and each tick is bounded and crash-recoverable.
if [ ! -d /run/service/viche-pnp-staffing ]; then
    nohup setsid /bin/sh "$town/missions/pnp/staffing.sh" </dev/null \
        >/dev/null 2>&1 &
fi
# Start independent local resource reclamation before any network I/O.
python3 -m missions.pnp.watchdog || :
# Compact only terminal, inactive research checkouts; keep unique deltas and
# the exact Git base. Run independently of the allocation/publication cycle.
mkdir -p "${PNP_STATE_ROOT}/cache"
nohup flock -n "${PNP_STATE_ROOT}/cache/retention.lock" \
    timeout 180 python3 -m missions.pnp.retention --limit 6 \
    </dev/null >"${PNP_STATE_ROOT}/cache/retention.log" 2>&1 &
# Independent checked-proof scout. A slow fetch/index never blocks leasing,
# publication, or the Executive. The lock prevents overlapping refreshes.
mkdir -p "${PNP_STATE_ROOT:-/var/lib/lubko/wd/viche-state/pnp}/cache"
nohup flock -n "${PNP_STATE_ROOT:-/var/lib/lubko/wd/viche-state/pnp}/cache/support-scan.lock" \
    timeout 120 python3 -m missions.pnp.support scan --refresh \
    </dev/null >"${PNP_STATE_ROOT:-/var/lib/lubko/wd/viche-state/pnp}/cache/support-scan.log" 2>&1 &
nohup flock -n "${PNP_STATE_ROOT:-/var/lib/lubko/wd/viche-state/pnp}/cache/brief-refresh.lock" \
    timeout 25 python3 -m missions.pnp.brief --refresh \
    </dev/null >"${PNP_STATE_ROOT:-/var/lib/lubko/wd/viche-state/pnp}/cache/brief-refresh.log" 2>&1 &
# Independent cheap generators do not wait for a model or the compiler.
nohup flock -n "${PNP_STATE_ROOT:-/var/lib/lubko/wd/viche-state/pnp}/cache/proof-preflight.lock" \
    timeout 30 python3 -m missions.pnp.preflight --scan \
    </dev/null >"${PNP_STATE_ROOT:-/var/lib/lubko/wd/viche-state/pnp}/cache/proof-preflight.log" 2>&1 &
# Renew leases and recover queued publications before the optional score poll.
# Cumulative research maintenance is local/read-mostly and independently
# locked. Finished async proofs survive agent exit and lease rotation.
nohup flock -n "${PNP_STATE_ROOT:-/var/lib/lubko/wd/viche-state/pnp}/cache/research-maintenance.lock" \
    timeout 90 /bin/sh -c 'python3 -m missions.pnp.research.knowledge ingest && python3 -m missions.pnp.research.obligations reconcile' \
    </dev/null >"${PNP_STATE_ROOT:-/var/lib/lubko/wd/viche-state/pnp}/cache/research-maintenance.log" 2>&1 &
python3 -m missions.pnp.frontier || :
# Public leaderboard observation must not depend on the desk reconcile: the
# mission-cycle hook runs under a 150s bound, and a rate-limited reconcile of
# many PR_OPEN gaps can exceed it, aborting this hook under `set -eu` before
# any public observation is refreshed (cycle.log "mission pnp hook failed").
python3 missions/pnp/leaderboard.py update || echo "PnP public leaderboard unavailable; retry next cycle" >&2
# Reconcile mutates local mission state, not a diagnostic; keep it bounded and
# non-fatal so a slow desk cannot block the rest of the cycle or leave public
# data stale. The detached agent/allocator/controller still own their work.
timeout -k 2 45 python3 missions/pnp/cli.py reconcile || echo "PnP reconcile deferred; retry next cycle" >&2
# A 20-minute desk lease TTL cannot be maintained by a 24-hour boot hook.
# Start (once per host) a bounded detached loop that renews active leases
# between boots; it starts no agents and is not a competing scheduler.
if [ -f "$town/missions/pnp/heartbeat.sh" ]; then
    nohup /bin/sh "$town/missions/pnp/heartbeat.sh" </dev/null >/dev/null 2>&1 &
fi

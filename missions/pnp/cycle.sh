#!/bin/sh
# Durable nonblocking P vs NP lease maintenance, invoked each Town boot cycle.
# No agent/model starts here: the Executive assigns mathematical research.
set -eu
. "$(dirname "$0")/runtime.sh"
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
export PATH=/home/lubko/.local/bin:/home/lubko/.elan/bin:/var/guix/profiles/per-user/user1/guix-profile/bin:/run/current-system/profile/bin:${PATH:-/bin}
[ -r "$town/missions/pnp/cli.py" ] || exit 0
cd "$town"
# Start the work-conserving allocator before optional slow network work.
mkdir -p "${PNP_STATE_ROOT:-/var/lib/lubko/wd/viche-state/pnp}"
nohup setsid /bin/sh "$town/missions/pnp/allocator.sh" </dev/null \
    >>"${PNP_STATE_ROOT:-/var/lib/lubko/wd/viche-state/pnp}/allocator.log" 2>&1 &
# Start independent local resource reclamation before any network I/O.
python3 -m missions.pnp.watchdog || :
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
python3 missions/pnp/cli.py reconcile
# A 20-minute desk lease TTL cannot be maintained by a 24-hour boot hook.
# Start (once per host) a bounded detached loop that renews active leases
# between boots; it starts no agents and is not a competing scheduler.
if [ -f "$town/missions/pnp/heartbeat.sh" ]; then
    nohup /bin/sh "$town/missions/pnp/heartbeat.sh" </dev/null >/dev/null 2>&1 &
fi
python3 missions/pnp/leaderboard.py update || echo "PnP public leaderboard unavailable; retry next cycle" >&2

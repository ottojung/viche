#!/bin/sh
# Durable nonblocking P vs NP lease maintenance, invoked each Town boot cycle.
# No agent/model starts here: the Executive assigns mathematical research.
set -eu
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
export PATH=/home/lubko/.local/bin:/home/lubko/.elan/bin:/var/guix/profiles/per-user/user1/guix-profile/bin:/run/current-system/profile/bin:${PATH:-/bin}
[ -r "$town/missions/pnp/cli.py" ] || exit 0
cd "$town"
# Renew leases and recover queued publications before the optional score poll.
python3 -m missions.pnp.frontier || :
python3 missions/pnp/cli.py reconcile
# A 20-minute desk lease TTL cannot be maintained by a 24-hour boot hook.
# Start (once per host) a bounded detached loop that renews active leases
# between boots; it starts no agents and is not a competing scheduler.
if [ -f "$town/missions/pnp/heartbeat.sh" ]; then
    nohup /bin/sh "$town/missions/pnp/heartbeat.sh" </dev/null >/dev/null 2>&1 &
fi
python3 missions/pnp/leaderboard.py update || echo "PnP public leaderboard unavailable; retry next cycle" >&2

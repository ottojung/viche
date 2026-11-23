#!/bin/sh
# Durable nonblocking P vs NP lease maintenance, invoked each Town boot cycle.
# No agent/model starts here: the Executive assigns mathematical research.
set -eu
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
export PATH=/home/lubko/.local/bin:/home/lubko/.elan/bin:/var/guix/profiles/per-user/user1/guix-profile/bin:/run/current-system/profile/bin:${PATH:-/bin}
[ -r "$town/missions/pnp/cli.py" ] || exit 0
cd "$town"
# The site itself, not our PR counts or agent count, decides the score.
# A transient network failure keeps the last verified snapshot intact.
python3 missions/pnp/leaderboard.py update || echo "PnP public leaderboard unavailable; retry next cycle" >&2
# Handle existing leases and PRs regardless of leaderboard availability.
python3 missions/pnp/cli.py reconcile

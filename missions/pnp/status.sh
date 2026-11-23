#!/bin/sh
# Public scoreboard + agent visibility + local research state, read-only.
set -eu
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
exec python3 "$town/missions/pnp/status.py"

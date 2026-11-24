#!/bin/sh
# Public scoreboard + agent visibility + local research state, read-only.
set -eu
PNP_STATUS_HOOK=1
. "$(dirname "$0")/runtime.sh"
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
exec python3 "$town/missions/pnp/status.py"

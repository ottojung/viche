#!/bin/sh
# Independent persistent controller, not an Executive model turn.
set -eu
. "$(dirname "$0")/runtime.sh"
export PATH=/home/lubko/.local/bin:/home/lubko/.elan/bin:/var/guix/profiles/per-user/user1/guix-profile/bin:/run/current-system/profile/bin:$PATH
export PNP_STAFFING_DAEMON=1
cd "$town"
dir="$PNP_STATE_ROOT/staffing"
mkdir -p "$dir"
exec 9>"$dir/loop.lock"
if [ "${1:-}" = supervised ]; then
    flock 9
else
    flock -n 9 || exit 0
fi
while [ -f missions/pnp/staffing/controller.py ]; do
    # Re-read code and policy on each pass. No long-running Python process
    # pins an old implementation after a canonical deployment.
    timeout -k 5 180 python3 -m missions.pnp.staffing.controller tick || :
    # Keep the log bounded via journaling in SQLite, not per-tick append.
    interval=$(python3 -c 'from missions.pnp.staffing.policy import load; print(load()["interval"])' 2>/dev/null) || interval=5
    if [ "${1:-}" != supervised ] && [ -d /run/service/viche-pnp-staffing ]; then
        exit 0
    fi
    sleep "$interval"
done

#!/bin/sh
# Standing Executive allocation order; not part of the desk allocator.
set -eu
. "$(dirname "$0")/runtime.sh"
export PATH=/home/lubko/.local/bin:/home/lubko/.elan/bin:/var/guix/profiles/per-user/user1/guix-profile/bin:/run/current-system/profile/bin:/bin:$PATH
cd "$town"
python3 -m missions.pnp.continuity

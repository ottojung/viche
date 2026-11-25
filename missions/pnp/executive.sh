#!/bin/sh
# Executive monitors standing staffing health; no agent starts in this hook.
set -eu
. "$(dirname "$0")/runtime.sh"
cd "$town"
python3 -m missions.pnp.staffing.controller status

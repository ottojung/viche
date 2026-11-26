#!/bin/sh
# Pure public-data observation; independent of proof generation and STOP.
set -eu
. "$(dirname "$0")/runtime.sh"
[ "$(hostname -s)" = billy-dev ] || exit 0
cd "$VICHE_TOWN_ROOT"
mkdir -p "$PNP_STATE_ROOT/lbcert"
exec 9>"$PNP_STATE_ROOT/lbcert/catalog-loop.lock"
flock -n 9 || exit 0
while :; do
    timeout -k 5 45 python3 -m missions.pnp.lbcert.catalog_observer || :
    sleep 20
done

# Live mission daemons have exactly one authorized deployment. In particular,
# a boot smoke fixture may contain the entire repository and real credentials.
# Check both the actual launcher path and configured roots BEFORE any I/O.
pnp_live_town=/var/lib/lubko/wd/viche
pnp_live_state=/var/lib/lubko/wd/viche-state
pnp_launcher_dir=$(CDPATH= cd "$(dirname "$0")" && pwd -P) || exit 0
town=${VICHE_TOWN_ROOT:-$pnp_live_town}
state=${VICHE_STATE_ROOT:-$pnp_live_state}
if [ "$pnp_launcher_dir" != "$pnp_live_town/missions/pnp" ] ||
   [ "$town" != "$pnp_live_town" ] ||
   [ "$state" != "$pnp_live_state" ] ||
   [ "${PNP_STATE_ROOT:-$state/pnp}" != "$pnp_live_state/pnp" ]; then
    # The fixture can test dispatch with its own mock hooks, but must not
    # contact the real desk, start daemons, or mutate the live state.
    echo "PnP live runtime skipped outside canonical deployment" >&2
    [ "${PNP_STATUS_HOOK:-0}" != 1 ] || printf '{}\n'
    exit 0
fi
export VICHE_TOWN_ROOT="$town" VICHE_STATE_ROOT="$state" PNP_STATE_ROOT="$state/pnp"

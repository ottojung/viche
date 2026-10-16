#!/bin/sh
# Out-of-loop bounded recovery loop for a conflicted canonical checkout.
# Invoked by the viche-git-recovery S6 service, NOT by the Founder-controlled
# boot loop, so it keeps running while boot.sh's cycle() short-circuits on
# reconcile() failure. POSIX /bin/sh only.
set -eu
interval=${VICHE_RECOVERY_INTERVAL_SECONDS:-60}
case "$interval" in '' | *[!0-9]* | 0) exit 2 ;; esac
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
trap 'exit 0' TERM INT
while :; do
    /bin/sh "$town/government/git-recovery.sh" ||
        echo 'Viche: git recovery found no safe automatic recovery; Sentinel alert active' >&2
    sleep "$interval" & wait "$!" || exit 0
done

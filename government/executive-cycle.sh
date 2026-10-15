#!/bin/sh
set -eu
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
seats=${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
charter=${VICHE_CONSTITUTION:?required}
[ -f "$state/inaugurated" ] || exit 0
id=$(sed -n "2s/[[:space:]].*//p" "$town/government/seats.tsv")
[ -n "$id" ] || exit 1

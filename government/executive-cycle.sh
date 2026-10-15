#!/bin/sh
set -eu
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
seats=${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
charter=${VICHE_CONSTITUTION:?required}
[ -f "$state/inaugurated" ] || exit 0
id=$(sed -n "2s/[[:space:]].*//p" "$town/government/seats.tsv")
[ -n "$id" ] || exit 1
if grep -Fxq "$id" "$town/records/SUMMONED.txt" 2>/dev/null; then exit 0; fi
meta=$(antonina agent status --id "$id" --json)
mode=$(printf "%s\n" "$meta" | jq -r ".state")
case "$mode" in
    running) exit 0 ;;
    failed) echo "Executive session failed; await session recovery" >&2; exit 0 ;;
    idle|succeeded) : ;;
    *) echo "Unexpected executive session state" >&2; exit 1 ;;
esac
cwd=$seats/$id
[ -d "$cwd" ] || exit 1

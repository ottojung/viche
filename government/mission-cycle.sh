#!/bin/sh
# Task-independent, nonblocking mission lifecycle and status hooks.
# New or retired tasks change only missions/, never government code.
set -eu
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
for mission in "$town"/missions/*; do
    [ -d "$mission" ] || continue
    name=${mission##*/}
    case "$name" in ''|*[!a-z0-9-]*) continue ;; esac
    [ -f "$mission/cycle.sh" ] || [ -f "$mission/status.sh" ] || continue
    dir=$state/missions/$name
    mkdir -p "$dir" || continue
    (
        flock -n 9 || exit 0
        if [ -f "$mission/cycle.sh" ]; then
            timeout -k 2 150 /bin/sh "$mission/cycle.sh" ||
                echo "Viche: mission $name hook failed; retry next cycle" >&2
        fi
        if [ -f "$mission/status.sh" ]; then
            snapshot=$(timeout -k 2 15 /bin/sh "$mission/status.sh") || exit 0
            [ "${#snapshot}" -le 65536 ] || exit 0
            printf '%s\n' "$snapshot" | python3 -m json.tool >/dev/null || exit 0
            tmp=$(mktemp "$dir/.status.XXXXXXXX") || exit 0
            printf '%s\n' "$snapshot" > "$tmp"
            mv "$tmp" "$dir/status.json"
        fi
    ) 9>"$dir/cycle.lock" >>"$dir/cycle.log" 2>&1 </dev/null &
done

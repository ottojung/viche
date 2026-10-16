#!/bin/sh
# Resource-safety pre-convene guard (Resource Safety Act).
# Defers convening a fresh seat when cgroup memory headroom is below the floor.
# This is a memory-safety gate, NOT a worker cap (Constitution VII): it defers
# convening until headroom recovers; it never permanently limits how many seats
# may run. The founder-controlled boot treats a non-zero exit as "agenda hook
# failed" and skips (defers) the seat, exactly as it does for clerk-liveness.
set -eu

town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
cgroup=${RESOURCE_SAFETY_CGROUP_DIR:-/sys/fs/cgroup}
floor=${RESOURCE_SAFETY_FLOOR_BYTES:-2147483648}       # 2 GiB
critical=${RESOURCE_SAFETY_CRITICAL_BYTES:-1073741824} # 1 GiB

[ "$#" -eq 1 ] || exit 2
seat=$1

max=$(cat "$cgroup/memory.max" 2>/dev/null || printf 'max\n')
[ "$max" = max ] && exit 0
case "$max" in ''|*[!0-9]*) exit 0;; esac

current=$(cat "$cgroup/memory.current" 2>/dev/null || printf '0\n')
case "$current" in ''|*[!0-9]*) current=0;; esac

headroom=$((max - current))
now=$(date -u +%FT%TZ)

# Fail open on unreadable cgroup (cannot measure -> do not block seats).
[ "$headroom" -ge 0 ] || exit 0

if [ "$headroom" -lt "$critical" ]; then
    mkdir -p "$state/resource-safety" 2>/dev/null || :
    printf '%s seat=%s headroom_bytes=%s level=critical action=defer\n' \
        "$now" "$seat" "$headroom" >> "$state/resource-safety/deferrals.log" 2>/dev/null || :
    echo "Viche: $seat DEFERRED - cgroup headroom $headroom B below critical $critical B" >&2
    exit 1
fi

if [ "$headroom" -lt "$floor" ]; then
    mkdir -p "$state/resource-safety" 2>/dev/null || :
    printf '%s seat=%s headroom_bytes=%s level=low action=defer\n' \
        "$now" "$seat" "$headroom" >> "$state/resource-safety/deferrals.log" 2>/dev/null || :
    echo "Viche: $seat DEFERRED - cgroup headroom $headroom B below floor $floor B" >&2
    exit 1
fi

exit 0

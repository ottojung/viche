#!/bin/sh
# Resource-safety guard regression: defers a fresh seat when cgroup headroom is
# below the floor, passes when headroom is adequate, treats "max" (no limit) and
# unreadable cgroup as no-constraint (fail open), and logs every deferral.
# POSIX /bin/sh only. Mocks the cgroup; never touches the live cgroup.
set -eu
root=$(git rev-parse --show-toplevel)
d=$(mktemp -d)
trap 'rm -rf "$d"' 0
town=$d/town
state=$d/state
cgroup=$d/cgroup
mkdir -p "$town/government" "$state" "$cgroup"
cp "$root/government/resource-safety.sh" "$town/government/resource-safety.sh"
cp "$root/government/sitting.sh" "$town/government/sitting.sh"
cp "$root/government/seats.tsv" "$town/government/seats.tsv"

export VICHE_TOWN_ROOT=$town
export VICHE_STATE_ROOT=$state
export RESOURCE_SAFETY_CGROUP_DIR=$cgroup

# 1. Adequate headroom (>= 2 GiB) -> convene (exit 0), no deferral logged.
printf '8589934592\n' > "$cgroup/memory.max"
printf '6442450944\n' > "$cgroup/memory.current"   # headroom 2 GiB
/bin/sh "$town/government/resource-safety.sh" c1a00003
[ ! -f "$state/resource-safety/deferrals.log" ]

# 2. Headroom below floor (1.5 GiB) -> defer (exit 1), deferral logged.
printf '7516192768\n' > "$cgroup/memory.current"   # headroom ~1.09 GiB
if /bin/sh "$town/government/resource-safety.sh" c1a00003; then
    echo "Viche: FAIL - low headroom did not defer" >&2; exit 1
fi
[ -f "$state/resource-safety/deferrals.log" ]
grep -q 'seat=c1a00003' "$state/resource-safety/deferrals.log"
grep -q 'level=low' "$state/resource-safety/deferrals.log"

# 3. Headroom below critical (0.5 GiB) -> defer (exit 1), critical logged.
printf '8053063680\n' > "$cgroup/memory.current"   # headroom ~0.5 GiB
if /bin/sh "$town/government/resource-safety.sh" c1a00003; then
    echo "Viche: FAIL - critical headroom did not defer" >&2; exit 1
fi
grep -q 'level=critical' "$state/resource-safety/deferrals.log"

# 4. No cgroup limit (memory.max = max) -> convene (exit 0), no new deferral.
before=$(wc -l < "$state/resource-safety/deferrals.log")
printf 'max\n' > "$cgroup/memory.max"
/bin/sh "$town/government/resource-safety.sh" c1a00003
[ "$(wc -l < "$state/resource-safety/deferrals.log")" -eq "$before" ]

# 5. Unreadable cgroup -> fail open (exit 0), no deferral.
rm -f "$cgroup/memory.max" "$cgroup/memory.current"
/bin/sh "$town/government/resource-safety.sh" c1a00003
[ "$(wc -l < "$state/resource-safety/deferrals.log")" -eq "$before" ]

# 6. sitting.sh invokes the guard and defers on low headroom (integration).
printf '8589934592\n' > "$cgroup/memory.max"
printf '7516192768\n' > "$cgroup/memory.current"   # headroom ~1.09 GiB
if /bin/sh "$town/government/sitting.sh" c1a00003 >/dev/null 2>&1; then
    echo "Viche: FAIL - sitting.sh did not defer on low headroom" >&2; exit 1
fi
# 7. sitting.sh convenes (exit 0) when headroom is adequate.
printf '6442450944\n' > "$cgroup/memory.current"   # headroom 2 GiB
/bin/sh "$town/government/sitting.sh" c1a00003 >/dev/null 2>&1

printf 'Viche: resource-safety guard defers below floor, passes when adequate, fails open on unreadable cgroup, and sitting.sh enforces it\n'

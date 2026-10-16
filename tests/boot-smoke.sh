#!/bin/sh
# Mock the Antonina CLI to test S6 bootstrap using only POSIX /bin/sh.
set -eu
root=$(git rev-parse --show-toplevel)
scratch=$(mktemp -d)
town=$scratch/town
cleanup() {
    if [ -d "$scratch/seats" ]; then
        for dir in "$scratch"/seats/*; do
            if [ -f "$dir/.git" ] || [ -d "$dir/.git" ]; then
                git -C "$town" worktree remove --force "$dir" >/dev/null 2>&1 || :
            fi
        done
    fi
    rm -rf "$scratch"
}
trap 'cleanup' 0
mkdir -p "$scratch/bin" "$scratch/seats" "$scratch/state" "$scratch/mock"

# Run against a hermetic town copy. The live records/SUMMONED.txt must not change
# what a routine sitting does, so clear the summons in the copy.
git clone --quiet --no-hardlinks "$root" "$town"
: > "$town/records/SUMMONED.txt"

cat > "$scratch/bin/antonina" <<'MOCK'
#!/bin/sh
set -eu
if [ "$1" = board ] && [ "$2" = list ]; then echo "[]"; exit 0; fi
[ "$1" = agent ] || exit 91
action=$2
shift 2
id= prompt=
while [ "$#" -gt 0 ]; do
    case "$1" in
        --id) id=$2; shift 2 ;;
        --cwd|--title) shift 2 ;;
        --prompt) prompt=$2; shift 2 ;;
        --json|--detach) shift ;;
        *) echo "Unexpected Antonina argument $1" >&2; exit 92 ;;
    esac
done
[ -n "$id" ] || exit 93
case "$action" in
    status)
        [ -f "$MOCK_STATE/$id" ] || exit 3
        printf '%s\n' '{"state":"idle","model":"opencode-go/longcat-2.5-preview-free","variant":"low"}'
        ;;
    new)
        [ ! -f "$MOCK_STATE/$id" ] || exit 4
        touch "$MOCK_STATE/$id"
        printf '%s\n' "$id" >> "$MOCK_STATE/created"
        ;;
    run)
        [ -f "$MOCK_STATE/$id" ] || exit 5
        case "$prompt" in
            *"=== AUTHORITATIVE CONSTITUTION ==="*|*"=== FOUNDER-CONTROLLED CONSTITUTION ==="*) : ;;
            *) exit 6 ;;
        esac
        case "$prompt" in
            *"opencode-go/longcat-2.5-preview-free"*) : ;;
            *) exit 7 ;;
        esac
        printf '%s\n' "$id" >> "$MOCK_STATE/ran"
        case "$prompt" in *"This is independent executive delivery"*) printf '%s\n' "$id" >> "$MOCK_STATE/executive-ran";; esac
        ;;
    *) exit 94 ;;
esac
MOCK
chmod +x "$scratch/bin/antonina"

MOCK_STATE=$scratch/mock
PATH=$scratch/bin:$PATH
mkdir -p "$scratch/cgroup"
printf "max\n" > "$scratch/cgroup/memory.max"
RESOURCE_SAFETY_CGROUP_DIR=$scratch/cgroup
VICHE_AUDIT_CHECKS=0
VICHE_AUDIT_SELECTION=0
export RESOURCE_SAFETY_CGROUP_DIR VICHE_AUDIT_CHECKS VICHE_AUDIT_SELECTION
VICHE_TOWN_ROOT=$town
VICHE_SEATS_ROOT=$scratch/seats
VICHE_STATE_ROOT=$scratch/state
VICHE_TEST_NO_SYNC=1
VICHE_TOWNHALL_ID=999
export MOCK_STATE PATH VICHE_TOWN_ROOT VICHE_SEATS_ROOT
export VICHE_STATE_ROOT VICHE_TEST_NO_SYNC VICHE_TOWNHALL_ID

# Periodic broad audit is separately tested. Suppress its timer in bootstrap smoke.
mkdir -p "$scratch/state/oversight"
date +%s > "$scratch/state/oversight/last-audit-dispatch"
seat_count=$(wc -l < "$town/government/seats.tsv")
[ "$seat_count" -ge 1 ]
/bin/sh "$town/constitution/boot.sh" --once
[ "$(wc -l < "$scratch/mock/created")" -eq $((seat_count+2)) ]
[ "$(wc -l < "$scratch/mock/ran")" -eq "$seat_count" ]
/bin/sh "$town/constitution/boot.sh" --once
[ "$(wc -l < "$scratch/mock/created")" -eq $((seat_count+3)) ]
[ -f "$scratch/mock/c1e00011" ]
[ "$(wc -l < "$scratch/mock/ran")" -eq $((seat_count+3)) ]
[ "$(wc -l < "$scratch/mock/executive-ran")" -eq 1 ]
# A summons wakes legislative seats and must NOT suppress the independent Executive.
summoned=$(sed -n '2p' "$town/government/seats.tsv" | cut -f1)
printf '%s\n' "$summoned" > "$town/records/SUMMONED.txt"
/bin/sh "$town/constitution/boot.sh" --once
[ "$(wc -l < "$scratch/mock/created")" -eq $((seat_count+3)) ]
[ "$(wc -l < "$scratch/mock/ran")" -eq $((seat_count+6)) ]
[ "$(wc -l < "$scratch/mock/executive-ran")" -eq 2 ]
printf 'Viche: %s seats initialized, charter injected, routine cycle runs Clerk+executive, while a parliamentary summons has precedence\n' "$seat_count"

#!/bin/sh
# Hermetic behavioral regression for the simplified office bootstrap.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
town=$scratch/town
seats=$scratch/seats
state=$scratch/state
mkdir -p "$town/government" "$seats/branches" "$state" "$scratch/bin" "$scratch/mock"
cp "$repo/government/agentic-office.sh" "$town/government/"
cp "$repo/government/handoff-queue.sh" "$town/government/"
cp "$repo/government/AGENTIC-OPERATIONS.md" "$town/government/"
printf '%s\n' 'FOUNDER-ONLY-CHARTER-MARKER' > "$scratch/charter"
printf '%s\n' '# Ordinary enacted laws' > "$town/government/LAWS.md"
printf 'c1a00001\tClerk\tintake\n' > "$town/government/seats.tsv"
for office in executive judiciary innovation-centre; do
    mkdir -p "$seats/branches/$office/.git"
done
mkdir -p "$seats/c1a00001/.git"
cat > "$town/government/appointments.sh" <<'APPOINT'
#!/bin/sh
case "$1" in ensure|resolve) : ;; *) exit 2 ;; esac
printf 'fixture-%s\n' "$2"
APPOINT
chmod +x "$town/government/appointments.sh"
cat > "$scratch/bin/antonina" <<'ANTONINA'
#!/bin/sh
set -eu
[ "$1" = agent ] || exit 3
action=$2
shift 2
case "$action" in
    status)
        [ "$1" = --id ] || exit 2
        printf '{"state":"%s","model":"fixture"}\n' "$(cat "$MOCK_STATE/mode")" ;;
    run)
        prompt=
        id=
        while [ "$#" -gt 0 ]; do
            case "$1" in
                --id) id=$2; shift 2 ;;
                --prompt) prompt=$2; shift 2 ;;
                --cwd) shift 2 ;;
                --detach) shift ;;
                *) exit 4 ;;
            esac
        done
        [ -n "$id" ] && [ -n "$prompt" ] || exit 5
        printf '%s\n' "$id" >> "$MOCK_STATE/runs"
        printf '%s\n' "$prompt" > "$MOCK_STATE/$id.prompt"
        ;;
    *) exit 6 ;;
esac
ANTONINA
chmod +x "$scratch/bin/antonina"
MOCK_STATE=$scratch/mock
VICHE_TOWN_ROOT=$town
VICHE_SEATS_ROOT=$seats
VICHE_STATE_ROOT=$state
VICHE_CONSTITUTION=$scratch/charter
VICHE_TOWNHALL_ID=302
PATH=$scratch/bin:$PATH
export MOCK_STATE VICHE_TOWN_ROOT VICHE_SEATS_ROOT VICHE_STATE_ROOT VICHE_CONSTITUTION VICHE_TOWNHALL_ID PATH

mkdir -p "$town/records/handoffs"
cat > "$town/records/handoffs/H-test.txt" <<'HANDOFF'
id: H-test
status: open
created: 2026-10-29T12:00:00Z
work: Recover exact stalled Founder work before new duties
HANDOFF
printf 'idle\n' > "$MOCK_STATE/mode"
/bin/sh "$repo/government/boot.sh"
[ "$(wc -l < "$MOCK_STATE/runs")" -eq 3 ]
for office in executive judiciary innovation-centre; do
    grep -Fq 'FOUNDER-ONLY-CHARTER-MARKER' "$MOCK_STATE/fixture-$office.prompt"
    grep -Fq 'Recover exact stalled Founder work' "$MOCK_STATE/fixture-$office.prompt"
    grep -Fq "$state/office-journals/$office.md" "$MOCK_STATE/fixture-$office.prompt"
done
grep -Fq 'operating under legislature authority' "$MOCK_STATE/fixture-innovation-centre.prompt"
grep -Fq 'Your independent responsibility: judiciary' "$MOCK_STATE/fixture-judiciary.prompt"
[ ! -f "$state/branches/executive.json" ]  # no fictitious health receipt
[ ! -f "$state/institutional-outcomes/latest.json" ]

# A live process must not receive a conflicting second writer.
printf 'running\n' > "$MOCK_STATE/mode"
: > "$MOCK_STATE/runs"
/bin/sh "$repo/government/boot.sh"
[ ! -s "$MOCK_STATE/runs" ]

# A failed process must not have its uncertain prompt or external actions replayed.
printf 'failed\n' > "$MOCK_STATE/mode"
/bin/sh "$repo/government/boot.sh" > "$scratch/failed.log" 2>&1
[ ! -s "$MOCK_STATE/runs" ]
grep -Fq 'Recovery Steward must reconcile' "$scratch/failed.log"

# The Innovation Centre transfer needs an enacted law, not a Founder wish alone.
printf 'idle\n' > "$MOCK_STATE/mode"
printf '%s\n' '## Act 25 — Executive Innovation Office Act (enacted 2026-10-29)' >> "$town/government/LAWS.md"
/bin/sh "$repo/government/boot.sh"
grep -Fq 'operating under executive authority' "$MOCK_STATE/fixture-innovation-centre.prompt"

# Parliamentary prompt is free of scripted medical/incident-style routing.
mkdir -p "$town/records"
printf 'legal work\n' > "$town/records/AGENDA.md"
/bin/sh "$repo/government/sitting.sh" c1a00001 > "$scratch/clerk.prompt"
grep -Fq 'parliamentary seat c1a00001' "$scratch/clerk.prompt"
grep -Fq 'Read the Town Hall' "$scratch/clerk.prompt"
grep -Fq 'Recover exact stalled Founder work' "$scratch/clerk.prompt"
grep -Fq "$state/office-journals/c1a00001.md" "$scratch/clerk.prompt"
printf 'failed\n' > "$MOCK_STATE/mode"
if /bin/sh "$repo/government/sitting.sh" c1a00001 > /dev/null 2>&1; then
    echo 'Failed parliamentary seat was unsafely redispatched' >&2
    exit 1
fi
printf 'running\n' > "$MOCK_STATE/mode"
if /bin/sh "$repo/government/sitting.sh" c1a00001 > /dev/null 2>&1; then
    echo 'Running parliamentary seat was dispatched twice' >&2
    exit 1
fi
echo 'Agentic dispatch smoke passed'

#!/bin/sh
# Executive is separate from any parliamentary summons.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
mkdir -p "$scratch/bin" "$scratch/town/government" "$scratch/town/records" "$scratch/seats/branches/executive" "$scratch/state"
printf 'c1a00001\tClerk\tintake\nc1a00002\tMember\tvoting\n' > "$scratch/town/government/seats.tsv"
printf 'Founder charter fixture\n' > "$scratch/charter"
printf '%s\n' c1a00002 > "$scratch/town/records/SUMMONED.txt"
cp "$repo/government/eligible-work.py" "$scratch/town/government/eligible-work.py"
mkdir -p "$scratch/town/missions/soringp1"
cp "$repo/missions/soringp1/mandate.md" "$scratch/town/missions/soringp1/mandate.md"
cp "$repo/government/handoff-queue.sh" "$scratch/town/government/handoff-queue.sh"
cp "$repo/government/predict-scorer.py" "$scratch/town/government/predict-scorer.py"
cp "$repo/government/AGENT-REPORTING-POLICY.md" "$scratch/town/government/AGENT-REPORTING-POLICY.md"
cp "$repo/government/delivery-candidates.py" "$scratch/town/government/delivery-candidates.py"
cat > "$scratch/bin/antonina" <<'MOCK'
#!/bin/sh
set -eu
case "$1 $2" in
  "board list")
    [ "${BOARD_DOWN:-no}" != yes ] || exit 3
    echo '[{"number":"401","title":"Ordinary assigned task"},{"number":"opaque-id-xyz","title":"Second issue"}]' ;;
  "board show")
    echo '{"body":"All agent execution and development work must happen on billy-dev.","messages":[]}' ;;
  "agent status")
    if [ "$MODE" = sequence ]; then
        n=0
        [ ! -f "$MOCK_STATE/status-calls" ] || n=$(cat "$MOCK_STATE/status-calls")
        n=$((n+1)); printf '%s\n' "$n" > "$MOCK_STATE/status-calls"
        if [ "$n" -eq 1 ]; then printf '%s\n' '{"state":"unknown"}'
        else printf '%s\n' '{"state":"running"}'; fi
    else
        printf '{"state":"%s","model":"%s","variant":"low"}\n' "$MODE" "$MODEL"
    fi ;;
  "agent run")
    case "$*" in *"Founder charter fixture"*) : ;; *) exit 8 ;; esac
    if [ "${BOARD_DOWN:-no}" = yes ]; then
        case "$*" in *"board=unavailable"*"Act only on independently"*"fixture durable authorized task"*) : ;; *) exit 8 ;; esac
        case "$*" in *'"eligible":[]'*|*'"count":0'*) exit 8 ;; esac
    else
        case "$*" in *"401"*) : ;; *) exit 8 ;; esac
    fi
    printf '%s\n' "$*" > "$MOCK_STATE/last-prompt"
    case "$*" in *"No work is authorized on SoringP1"*) : ;; *) exit 8 ;; esac
    case "$*" in *"research-plan.md"*|*"depleted_after_empty_curation"*) exit 8 ;; esac
    printf 'accepted\n' >> "$OUTPUT" ;;
  *) echo "Unexpected: $*" >&2; exit 10 ;;
esac
MOCK
chmod +x "$scratch/bin/antonina"
PATH=$scratch/bin:$PATH
mkdir -p "$scratch/town/government"
cp "$repo/tests/appointment-id-stub.sh" "$scratch/town/government/appointments.sh"
VICHE_TOWN_ROOT=$scratch/town
VICHE_SEATS_ROOT=$scratch/seats
VICHE_STATE_ROOT=$scratch/state
VICHE_CONSTITUTION=$scratch/charter
MODE=idle MODEL=test-provider/example
OUTPUT=$scratch/dispatched
export PATH VICHE_TOWN_ROOT VICHE_SEATS_ROOT VICHE_STATE_ROOT VICHE_CONSTITUTION MODE MODEL OUTPUT
MOCK_STATE=$scratch
MOCK_STATE=$MOCK_STATE
export MOCK_STATE
# The current Executive cycle inventories Git delivery candidates. Keep this
# fixture a real repository with the exact ref that inventory reads; otherwise
# the smoke fails for an unrelated missing-Git dependency.
git -C "$scratch/town" init -q -b main
git -C "$scratch/town" config user.name Fixture
git -C "$scratch/town" config user.email fixture@example.invalid
git -C "$scratch/town" config commit.gpgsign false
git -C "$scratch/town" add -A
git -C "$scratch/town" commit -qm 'Executive cycle fixture baseline'
git -C "$scratch/town" update-ref refs/remotes/origin/main HEAD
grep -Fq "Before interacting with Antonina board or agents" "$repo/government/executive-cycle.sh"
grep -Fq "government/antonina-interface.md" "$repo/government/executive-agenda.md"
sh "$repo/government/executive-cycle.sh"
test ! -e "$OUTPUT"
touch "$scratch/state/inaugurated"
sh "$repo/government/executive-cycle.sh"
test "$(wc -l < "$OUTPUT")" -eq 1
test -s "$scratch/town/records/predictions/calibration.json"
jq -e '.count==2 and .eligible[0].number=="401" and .eligible[1].number=="opaque-id-xyz"' "$scratch/state/branches/eligible-issues.json" >/dev/null
sh "$repo/government/executive-cycle.sh"
test "$(wc -l < "$OUTPUT")" -eq 2
MODE=running
sh "$repo/government/executive-cycle.sh"
test "$(wc -l < "$OUTPUT")" -eq 2
MODE=failed
if sh "$repo/government/executive-cycle.sh" 2>/dev/null; then exit 1; fi
MODE=idle MODEL=other-provider/other-model
sh "$repo/government/executive-cycle.sh"
test "$(wc -l < "$OUTPUT")" -eq 3
MODEL=test-provider/example
BOARD_DOWN=yes
export MODE MODEL BOARD_DOWN
if sh "$repo/government/executive-cycle.sh" 2>/dev/null; then exit 1; fi
test "$(wc -l < "$OUTPUT")" -eq 3
# A transient 'unknown' is re-read, not fatal and not treated as idle.
MODE=sequence
VICHE_AGENT_STATE_RETRIES=3 VICHE_AGENT_STATE_DELAY=0
export MODE VICHE_AGENT_STATE_RETRIES VICHE_AGENT_STATE_DELAY
rm -f "$MOCK_STATE/status-calls"
sh "$repo/government/executive-cycle.sh"
test "$(cat "$MOCK_STATE/status-calls")" -eq 2
test "$(wc -l < "$OUTPUT")" -eq 3

# A persistent 'unknown' fails closed with a specific diagnostic and no dispatch.
MODE=unknown
export MODE
if sh "$repo/government/executive-cycle.sh" 2>"$scratch/unknown.err"; then
    echo 'FAIL: persistent unknown state must not be treated as success' >&2; exit 1
fi
grep -q 'has no usable state' "$scratch/unknown.err"
grep -q "unrecognized agent state 'unknown'" "$scratch/unknown.err"
test "$(wc -l < "$OUTPUT")" -eq 3

# Board failure may not suppress independently authorized durable handoffs.
MODE=idle
export MODE
id=$(sh "$repo/government/handoff-queue.sh" add "$scratch/town" 'Founder fixture' 'independent authorization' 'Executive: fixture durable authorized task')
sh "$repo/government/executive-cycle.sh"
test "$(wc -l < "$OUTPUT")" -eq 4
grep -Fq "$id" "$scratch/last-prompt"
grep -Fq 'board=unavailable' "$scratch/last-prompt"
grep -Fq 'no new board assignments may be inferred' "$scratch/last-prompt"

# A broken calibration report blocks its own consequential decisions, not
# the authorized ordinary turn. The old report is not described as current.
BOARD_DOWN=no
export BOARD_DOWN
printf 'raise SystemExit(9)\n' > "$scratch/town/government/predict-scorer.py"
sh "$repo/government/executive-cycle.sh"
test "$(wc -l < "$OUTPUT")" -eq 5
grep -Fq 'Act22 calibration=unavailable' "$scratch/last-prompt"
grep -Fq 'execute an Act22 consequential order until' "$scratch/last-prompt"

# Unavailable case data never implies that holds may be cleared.
printf 'raise SystemExit(9)\n' > "$scratch/town/government/institutional-cases.py"
sh "$repo/government/executive-cycle.sh"
test "$(wc -l < "$OUTPUT")" -eq 6
grep -Fq '"open_cases":null' "$scratch/last-prompt"
grep -Fq 'Never' "$scratch/last-prompt"

# A genuine existing unsafe hold remains a hard refusal in degraded mode.
mkdir -p "$scratch/state/liveness/unsafe-holds"
printf 'fixture hold\n' > "$scratch/state/liveness/unsafe-holds/executive"
if sh "$repo/government/executive-cycle.sh" 2>/dev/null; then exit 1; fi
test "$(wc -l < "$OUTPUT")" -eq 6

# Gate status 10 is an intentional skip; broken advisory bookkeeping is not.
rm "$scratch/state/liveness/unsafe-holds/executive"
cat > "$scratch/town/government/dispatch-gate.sh" <<'GATE'
#!/bin/sh
case "$1" in
  board-signature) echo 'fixture-signature';;
  check) cat >/dev/null; exit "$GATE_RC";;
  commit) printf 'committed\n' >> "$MOCK_STATE/gate-commits";;
  *) exit 99;;
esac
GATE
GATE_RC=10
export GATE_RC
sh "$repo/government/executive-cycle.sh"
test "$(wc -l < "$OUTPUT")" -eq 6
test ! -e "$scratch/gate-commits"
GATE_RC=2
sh "$repo/government/executive-cycle.sh"
test "$(wc -l < "$OUTPUT")" -eq 7
test ! -e "$scratch/gate-commits"
GATE_RC=0
sh "$repo/government/executive-cycle.sh"
test "$(wc -l < "$OUTPUT")" -eq 8
test "$(wc -l < "$scratch/gate-commits")" -eq 1

echo 'Independent Executive dispatch, degraded evidence, advisory gate and fail-closed assignment smoke passed'

#!/bin/sh
# Executive dispatch must stay under the kernel per-argument ceiling even when
# the assembled prompt is very large. The prompt is preserved byte-for-byte in
# a private file passed with --prompt-file; it must not be inlined into argv.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
mkdir -p "$scratch/bin" "$scratch/town/government" "$scratch/town/records" \
  "$scratch/town/missions/soringp1" "$scratch/seats/branches/executive" "$scratch/state"

# A charter with a distinctive 200 KB marker: the whole charter is embedded in
# the Executive prompt, so the assembled prompt exceeds any realistic argv cap.
python3 - "$scratch/charter" <<'PY'
import sys
marker = 'EXECUTIVE_PROMPT_FILE_MARKER_7c41'
with open(sys.argv[1], 'w') as f:
    f.write('Founder charter fixture\n' + marker + '\n')
    f.write('z' * 200000 + '\n')
PY
printf 'c1a00001\tClerk\tintake\nc1a00002\tMember\tvoting\n' > "$scratch/town/government/seats.tsv"
printf '%s\n' c1a00002 > "$scratch/town/records/SUMMONED.txt"
cp "$repo/government/eligible-work.py" "$scratch/town/government/eligible-work.py"
cp "$repo/missions/soringp1/mandate.md" "$scratch/town/missions/soringp1/mandate.md"
cp "$repo/government/handoff-queue.sh" "$scratch/town/government/handoff-queue.sh"
cp "$repo/government/predict-scorer.py" "$scratch/town/government/predict-scorer.py"
cp "$repo/government/AGENT-REPORTING-POLICY.md" "$scratch/town/government/AGENT-REPORTING-POLICY.md"
cp "$repo/government/delivery-candidates.py" "$scratch/town/government/delivery-candidates.py"
cp "$repo/tests/appointment-id-stub.sh" "$scratch/town/government/appointments.sh"

cat > "$scratch/bin/antonina" <<'MOCK'
#!/bin/sh
set -eu
case "$1 $2" in
  "board list")
    echo '[{"number":"401","title":"Ordinary assigned task"}]' ;;
  "board show")
    echo '{"body":"All agent execution and development work must happen on billy-dev.","messages":[]}' ;;
  "agent status")
    printf '{"state":"idle","model":"test-provider/example","variant":"low"}\n' ;;
  "agent run")
    prompt= pfile= prev=
    for arg in "$@"; do
      [ "$prev" != '--prompt' ] || prompt=$arg
      [ "$prev" != '--prompt-file' ] || pfile=$arg
      prev=$arg
    done
    if [ -n "$prompt" ]; then
      echo "FAIL: inline --prompt length ${#prompt} would exceed argv budget" >&2
      exit 6
    fi
    [ -n "$pfile" ] || { echo 'FAIL: no --prompt-file' >&2; exit 7; }
    case "$pfile" in /*) : ;; *) echo 'FAIL: prompt file path is not absolute' >&2; exit 8 ;; esac
    [ -f "$pfile" ] || { echo 'FAIL: prompt file is missing' >&2; exit 9; }
    mode=$(stat -c '%a' "$pfile" 2>/dev/null || printf 'unknown\n')
    [ "$mode" = 600 ] || { echo "FAIL: prompt file mode is $mode" >&2; exit 10; }
    size=$(wc -c < "$pfile")
    [ "$size" -gt 120000 ] || { echo "FAIL: prompt truncated to $size bytes" >&2; exit 11; }
    grep -q 'EXECUTIVE_PROMPT_FILE_MARKER_7c41' "$pfile" ||
      { echo 'FAIL: durable prompt lost the charter marker' >&2; exit 12; }
    cat "$pfile" > "$PROMPT_DUMP"
    printf 'run\n' >> "$OUTPUT" ;;
  *) echo "Unexpected Antonina: $*" >&2; exit 10 ;;
esac
MOCK
chmod +x "$scratch/bin/antonina"

PATH=$scratch/bin:$PATH
VICHE_TOWN_ROOT=$scratch/town
VICHE_SEATS_ROOT=$scratch/seats
VICHE_STATE_ROOT=$scratch/state
VICHE_CONSTITUTION=$scratch/charter
OUTPUT=$scratch/dispatched
PROMPT_DUMP=$scratch/prompt.txt
export PATH VICHE_TOWN_ROOT VICHE_SEATS_ROOT VICHE_STATE_ROOT VICHE_CONSTITUTION
export OUTPUT PROMPT_DUMP

# The delivery inventory reads a real repository; give the fixture one.
git -C "$scratch/town" init -q -b main
git -C "$scratch/town" config user.name Fixture
git -C "$scratch/town" config user.email fixture@example.invalid
git -C "$scratch/town" config commit.gpgsign false
git -C "$scratch/town" add -A
git -C "$scratch/town" commit -qm 'Executive prompt-file fixture baseline'
git -C "$scratch/town" update-ref refs/remotes/origin/main HEAD

touch "$scratch/state/inaugurated"
sh "$repo/government/executive-cycle.sh"

test "$(wc -l < "$OUTPUT")" -eq 1 || { echo 'FAIL: dispatch did not launch' >&2; exit 1; }
grep -q 'EXECUTIVE_PROMPT_FILE_MARKER_7c41' "$PROMPT_DUMP" ||
  { echo 'FAIL: agent did not receive the full prompt' >&2; exit 1; }
# The private prompt file is removed after the dispatch, including on failure.
set -- "$scratch"/state/branches/executive-prompt.*
[ ! -e "$1" ] || { echo 'FAIL: private prompt file was left behind' >&2; exit 1; }
# The success-only bookkeeping still ran.
test -s "$scratch/state/branches/executive-last-dispatch" ||
  { echo 'FAIL: last-dispatch not written after accepted dispatch' >&2; exit 1; }

echo 'Executive private --prompt-file dispatch budget smoke passed'

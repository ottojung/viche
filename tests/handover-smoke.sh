#!/bin/sh
# Every completed government turn uses a fresh context and durable pointers.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
mkdir -p "$d/bin" "$d/mock" "$d/town/government" "$d/seats/c1a00001" "$d/state"
printf 'c1a00001\tClerk\tintake\n' > "$d/town/government/seats.tsv"
cp "$repo/government/appointments.sh" "$repo/government/handover.sh" \
  "$repo/government/terminal-appointment-evidence.sh" "$d/town/government/"
cat > "$d/bin/antonina" <<'MOCK'
#!/bin/sh
set -eu
case "$1 $2" in
  'agent status') [ -s "$MOCK_ROOT/$4.json" ] || exit 3; cat "$MOCK_ROOT/$4.json" ;;
  'agent log') [ ! -f "$MOCK_ROOT/$4.log" ] || cat "$MOCK_ROOT/$4.log" ;;
  'agent new')
    n=0; [ ! -s "$MOCK_ROOT/next" ] || n=$(cat "$MOCK_ROOT/next")
    n=$((n+1)); printf '%s\n' "$n" > "$MOCK_ROOT/next"
    printf '{"state":"idle","prompts":0}\n' > "$MOCK_ROOT/fresh-$n.json"
    printf 'fresh-%s\n' "$n" ;;
  *) echo "unexpected Antonina call: $*" >&2; exit 9 ;;
esac
MOCK
chmod +x "$d/bin/antonina"
export PATH="$d/bin:$PATH" MOCK_ROOT="$d/mock" VICHE_TOWN_ROOT="$d/town" \
  VICHE_SEATS_ROOT="$d/seats" VICHE_STATE_ROOT="$d/state"
mkdir -p "$d/state/appointments"
printf 'c1a00001\told-clerk\n' > "$d/state/appointments/appointments.tsv"
step() { # step INPUT_TOKENS -> one OpenCode step_finish line
  printf '{"type":"step_finish","timestamp":1,"sessionID":"ses_a","part":{"tokens":{"input":%s,"output":10,"cache":{"read":0,"write":0}}}}\n' "$1"
}
say() { printf '{"type":"text","timestamp":1,"sessionID":"ses_a","part":{"text":"%s"}}\n' "$1"; }
ensure() { /bin/sh "$d/town/government/appointments.sh" ensure c1a00001; }

# A never-used idle appointment is not rotated.
printf '{"state":"idle","prompts":0}\n' > "$d/mock/old-clerk.json"
test "$(ensure)" = old-clerk
test ! -e "$d/state/handover/c1a00001.md"

# A large conversation while RUNNING is never rotated.
{ step 9000; step 450000; } > "$d/mock/old-clerk.log"
printf '{"state":"running","prompts":12}\n' > "$d/mock/old-clerk.json"
test "$(ensure)" = old-clerk
# ...nor while failed (that is Act 19 recovery's business).
printf '{"state":"failed","prompts":12}\n' > "$d/mock/old-clerk.json"
test "$(/bin/sh "$d/town/government/appointments.sh" resolve c1a00001)" = old-clerk
# The switch turns rotation off.
printf '{"state":"clearexit","prompts":12}\n' > "$d/mock/old-clerk.json"
test "$(VICHE_SESSION_ROTATION=off ensure)" = old-clerk

# Even a small completed turn rotates, with a pointer note and provenance.
{ say 'report one'; say 'report two'; say 'report three'; say 'Cursor advanced to sha256:abc; review of 67be6d0 is blocked'; step 2000; } > "$d/mock/old-clerk.log"
printf '{"state":"clearexit","prompts":1}\n' > "$d/mock/old-clerk.json"
new=$(ensure)
test "$new" = fresh-1
test "$(/bin/sh "$d/town/government/appointments.sh" resolve c1a00001)" = fresh-1
note=$d/state/handover/c1a00001.md
grep -Fxq 'successor: fresh-1' "$note"
grep -Fxq 'predecessor: old-clerk' "$note"
grep -Fq 'durable records' "$note"
if grep -Eq 'Cursor advanced|report (one|two|three)' "$note"; then
  echo 'predecessor conversation must not be injected' >&2; exit 1
fi
jq -e 'select(.trigger=="session_rotation" and .expected_prior_id=="old-clerk" and .successor=="fresh-1")' \
  "$d/state/appointments/replacement-provenance.jsonl" >/dev/null
test "$(wc -l < "$d/state/handover/rotations.log")" -eq 1

# Shown exactly while the successor has received no prompt.
shown=$(/bin/sh "$d/town/government/handover.sh" show c1a00001 fresh-1)
printf '%s\n' "$shown" | grep -Fq 'HANDOVER NOTE (fresh session)'
printf '%s\n' "$shown" | grep -Fq 'NOT authority'
if printf '%s\n' "$shown" | grep -Fq 'successor:'; then echo 'note header leaked into prompt' >&2; exit 1; fi
test -z "$(/bin/sh "$d/town/government/handover.sh" show c1a00001 old-clerk)"
printf '{"state":"running","prompts":1}\n' > "$d/mock/fresh-1.json"
test -z "$(/bin/sh "$d/town/government/handover.sh" show c1a00001 fresh-1)"

# A single short completed turn is enough to rotate.
printf '{"state":"clearexit","prompts":1}\n' > "$d/mock/fresh-1.json"
step 30000 > "$d/mock/fresh-1.log"
test "$(ensure)" = fresh-2
# Unused successor is kept; idle with a native session rotates too.
test "$(ensure)" = fresh-2
printf '{"state":"idle","prompts":0,"native_session_id":"ses_old"}\n' > "$d/mock/fresh-2.json"
test "$(ensure)" = fresh-3
printf '{"state":"running","prompts":1}\n' > "$d/mock/fresh-3.json"
test "$(ensure)" = fresh-3
printf '{"state":"failed","prompts":1}\n' > "$d/mock/fresh-3.json"
test "$(ensure)" = fresh-3
echo 'Fresh government turns and durable-only handover passed'

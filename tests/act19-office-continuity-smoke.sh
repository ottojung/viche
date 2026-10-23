#!/bin/sh
# Hermetic Act 19 (Office Continuity and Handoff Integrity Act) smoke:
# failure-count reset regardless of observed state, transient-class coverage,
# permanent-failure surfacing, progress guard, cooldown, durable handoff queue
# non-supersession, no-dispatch-on-pre-read-failure, and the commit-age signal.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)

# --- Part 1: failure-count-based office reset (branch-bootstrap, §3.1/§3.3) ---
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
mkdir -p "$d/bin" "$d/town/government" "$d/seats/branches/executive" "$d/state/liveness" "$d/mock"
printf 'c1a00001\tClerk\tlegislature\n' > "$d/town/government/seats.tsv"
cp "$repo/government/branch-bootstrap.sh" "$d/town/government/branch-bootstrap.sh"
cp "$repo/government/office-continuity.sh" "$d/town/government/office-continuity.sh"
git -C "$d/seats/branches/executive" init -q
git -C "$d/seats/branches/executive" -c user.name=test -c user.email=test@example.test commit --allow-empty -qm baseline
printf 'valuable uncommitted work\n' > "$d/seats/branches/executive/uncommitted.txt"
cat > "$d/bin/antonina" <<'MOCK'
#!/bin/sh
set -eu
case "$1 $2" in
  'agent status') cat "$MOCK_ROOT/status.json" ;;
  'agent log') echo 'Endpoint is unavailable' ;;
  'agent delete') echo delete >> "$MOCK_ROOT/recovery" ;;
  'agent new')
    echo new >> "$MOCK_ROOT/recovery"
    printf '{"state":"idle","model":"example-provider/model-a","variant":"low"}\n' > "$MOCK_ROOT/status.json"
    ;;
  *) exit 9 ;;
esac
MOCK
chmod +x "$d/bin/antonina"
set_status() {
  printf '{"state":"%s","model":"example-provider/model-a","variant":"low","backend_error":{"classification":"%s","transient":%s}}\n' \
    "$1" "${2:-upstream_endpoint_unavailable}" "${3:-true}" > "$d/mock/status.json"
}
wt=$d/seats/branches/executive
liv=$d/state/liveness
log=$liv/failures/c1e00002
PATH="$d/bin:$PATH"
MOCK_ROOT="$d/mock"
mkdir -p "$d/town/government"
cp "$repo/tests/appointment-id-stub.sh" "$d/town/government/appointments.sh"
VICHE_TOWN_ROOT="$d/town"
VICHE_SEATS_ROOT="$d/seats"
VICHE_STATE_ROOT="$d/state"
export PATH MOCK_ROOT VICHE_TOWN_ROOT VICHE_SEATS_ROOT VICHE_STATE_ROOT

run_bootstrap() { /bin/sh "$d/town/government/branch-bootstrap.sh" executive; }

# Below threshold: two observed failures are recorded but do not reset.
set_status failed upstream_endpoint_unavailable true
run_bootstrap
run_bootstrap
test "$(wc -l < "$log")" -eq 2
test ! -e "$d/mock/recovery"

# P1a detector / oscillation: failed->running->failed observations accumulate
# in the monotonic record; the reset fires on the third consecutive transient
# failure even though the supervisor keeps seeing "running" in between.
: > "$log"
set_status failed;  run_bootstrap
set_status running; run_bootstrap
set_status failed;  run_bootstrap
set_status running; run_bootstrap
set_status failed;  run_bootstrap
test "$(wc -l < "$d/mock/recovery")" -eq 2
test "$(wc -l < "$log")" -eq 0
test "$(find "$liv" -name 'status.json' | wc -l)" -eq 1
grep -Fq 'session_reset=failure_count threshold=3 window=1800 cooldown=1800' "$liv/recoveries.log"
test -f "$wt/uncommitted.txt"
# commit-age signal is emitted while the office has uncommitted work.
grep -Fq 'commit_age_seconds=' "$liv/commit-age.log"
grep -Fq "id=c1e00002" "$liv/commit-age.log"

# P1: the reset is decidable from the failure record alone — the agent is
# observed "running" (healthy-looking) yet the recorded threshold still fires.
printf '0\n' > "$liv/last-reset-c1e00002"
now=$(date +%s)
sha=$(git -C "$wt" rev-parse HEAD)
for i in 1 2 3; do
  printf '%s upstream_endpoint_unavailable %s\n' "$now" "$sha" >> "$log"
done
set_status running
run_bootstrap
test "$(wc -l < "$d/mock/recovery")" -eq 4

# P2: the non-endpoint transient class (2026-10-17 API-key expiry) is covered.
printf '0\n' > "$liv/last-reset-c1e00002"
set_status failed unrecognized_backend_failure true
run_bootstrap
run_bootstrap
run_bootstrap
test "$(wc -l < "$d/mock/recovery")" -eq 6

# Permanent failures are surfaced, never silently reset, never counted.
incidents_before=0
if [ -f "$liv/permanent-incidents.log" ]; then
  incidents_before=$(wc -l < "$liv/permanent-incidents.log")
fi
set_status failed invalid_api_key false
run_bootstrap
run_bootstrap
run_bootstrap
test "$(wc -l < "$d/mock/recovery")" -eq 6
test "$(wc -l < "$log")" -eq 0
test "$(wc -l < "$liv/permanent-incidents.log")" -gt "$incidents_before"
grep -Fq 'permanent_failure classification=invalid_api_key surfaced-not-reset' "$liv/permanent-incidents.log"

# Progress guard: durable work between failures breaks the streak.
set_status failed upstream_endpoint_unavailable true
run_bootstrap
run_bootstrap
test "$(wc -l < "$log")" -eq 2
git -C "$wt" -c user.name=test -c user.email=test@example.test commit --allow-empty -qm 'durable progress'
printf '0\n' > "$liv/last-reset-c1e00002"
set_status failed upstream_endpoint_unavailable true
run_bootstrap
test "$(wc -l < "$log")" -eq 1
test "$(wc -l < "$d/mock/recovery")" -eq 6
set_status failed upstream_endpoint_unavailable true
run_bootstrap
set_status failed upstream_endpoint_unavailable true
run_bootstrap
test "$(wc -l < "$d/mock/recovery")" -eq 8
# A clean worktree (no uncommitted work) stops emitting the signal.
git -C "$wt" add -A
git -C "$wt" -c user.name=test -c user.email=test@example.test commit --allow-empty -qm 'all work durable'
lines_before=$(wc -l < "$liv/commit-age.log")
set_status running
run_bootstrap
test "$(wc -l < "$liv/commit-age.log")" -eq "$lines_before"
printf 'new uncommitted work\n' > "$wt/later.txt"
set_status running
run_bootstrap
test "$(wc -l < "$liv/commit-age.log")" -gt "$lines_before"

# Cooldown: three more failures cannot reset again inside 1800 s.
set_status failed upstream_endpoint_unavailable true
run_bootstrap
run_bootstrap
run_bootstrap
test "$(wc -l < "$d/mock/recovery")" -eq 8
printf '0\n' > "$liv/last-reset-c1e00002"
set_status failed upstream_endpoint_unavailable true
run_bootstrap
test "$(wc -l < "$d/mock/recovery")" -eq 10

# --- Part 2: durable handoff queue and non-supersession (executive-cycle, §3.2) ---
d2=$(mktemp -d)
mkdir -p "$d2/bin" "$d2/town/government" "$d2/town/records" "$d2/seats/branches/executive" "$d2/state"
printf 'c1a00001\tClerk\tintake\nc1e00002\tExecutive\tdelivery\n' > "$d2/town/government/seats.tsv"
printf 'Founder charter fixture\n' > "$d2/charter"
printf '%s\n' c1e00002 > "$d2/town/records/SUMMONED.txt"
cp "$repo/government/eligible-work.py" "$d2/town/government/eligible-work.py"
cp "$repo/government/executive-cycle.sh" "$d2/town/government/executive-cycle.sh"
cp "$repo/government/handoff-queue.sh" "$d2/town/government/handoff-queue.sh"
cat > "$d2/bin/antonina" <<'MOCK'
#!/bin/sh
set -eu
case "$1 $2" in
  'board list')
    [ "${BOARD_DOWN:-no}" != yes ] || exit 3
    echo '[{"number":"301","title":"SoringP1"}]' ;;
  'board show')
    echo '{"body":"All agent execution and development work must happen on billy-dev.","messages":[]}' ;;
  'agent status')
    printf '{"state":"%s","model":"%s","variant":"low"}\n' "$MODE" "$MODEL" ;;
  'agent run')
    printf '%s\n' "$*" > "$PROMPT_FILE"
    printf 'accepted\n' >> "$OUTPUT" ;;
  *) echo "Unexpected: $*" >&2; exit 10 ;;
esac
MOCK
chmod +x "$d2/bin/antonina"
touch "$d2/state/inaugurated"
PATH="$d2/bin:$PATH"
mkdir -p "$d2/town/government"
cp "$repo/tests/appointment-id-stub.sh" "$d2/town/government/appointments.sh"
VICHE_TOWN_ROOT="$d2/town"
VICHE_SEATS_ROOT="$d2/seats"
VICHE_STATE_ROOT="$d2/state"
VICHE_CONSTITUTION="$d2/charter"
MODE=idle MODEL=example-provider/model-a
OUTPUT="$d2/dispatched"
PROMPT_FILE="$d2/prompt"
export PATH VICHE_TOWN_ROOT VICHE_SEATS_ROOT VICHE_STATE_ROOT VICHE_CONSTITUTION MODE MODEL OUTPUT PROMPT_FILE

# With no open handoffs the generic eligible-issue dispatch is unchanged.
/bin/sh "$d2/town/government/executive-cycle.sh"
test "$(wc -l < "$OUTPUT")" -eq 1
grep -Fq '301' "$PROMPT_FILE"
test -s "$d2/state/branches/eligible-issues.json"

# Atomic steer: the steer writes the queue entry at steer time.
id1=$(/bin/sh "$d2/town/government/handoff-queue.sh" add "$d2/town" 'Viche Clerk c1a00001' 'board #313 2026-10-19T11:14Z' 'Deliver the Act 18 section 7 step: verify the tally and publish')
id2=$(/bin/sh "$d2/town/government/handoff-queue.sh" add "$d2/town" 'Viche Clerk c1a00001' 'board #313 2026-10-19T11:14Z' 'Second open handoff item')
test -n "$id1"
test "$id1" != "$id2"
test -s "$d2/town/records/handoffs/$id1.txt"
grep -Fq 'status: open' "$d2/town/records/handoffs/$id1.txt"
# list-open is the dispatch input: one line per open handoff, id and work present.
listed=$(/bin/sh "$d2/town/government/handoff-queue.sh" list-open "$d2/town")
test "$(printf '%s\n' "$listed" | wc -l)" -eq 2
printf '%s\n' "$listed" | grep -Fq "$id1"
printf '%s\n' "$listed" | grep -Fq "$id2"
printf '%s\n' "$listed" | grep -Fq 'Deliver the Act 18 section 7 step'
test "$(printf '%s\n' "$listed" | head -n 1 | awk -F '\t' '{print NF}')" -eq 3

# P3: with an open handoff the dispatch carries the handoff and MUST NOT run
# the generic eligible-issue prompt (no supersession of the specific steer).
rm -f "$d2/state/branches/eligible-issues.json"
/bin/sh "$d2/town/government/executive-cycle.sh"
test "$(wc -l < "$OUTPUT")" -eq 2
grep -Fq 'OPEN DURABLE HANDOFFS' "$PROMPT_FILE"
grep -Fq 'Act 18 section 7 step' "$PROMPT_FILE"
grep -Fq "$id1" "$PROMPT_FILE"
if grep -Fq '301' "$PROMPT_FILE"; then echo "generic dispatch superseded the open handoff" >&2; exit 1; fi
if grep -Fq 'Verified issue assignments' "$PROMPT_FILE"; then echo "generic eligible-issue prompt ran while a handoff was open" >&2; exit 1; fi
test ! -e "$d2/state/branches/eligible-issues.json"

# The steer's own evidence and assigning authority are durable in the entry.
grep -Fq 'assigned-by: Viche Clerk c1a00001' "$d2/town/records/handoffs/$id1.txt"
grep -Fq 'evidence: board #313 2026-10-19T11:14Z' "$d2/town/records/handoffs/$id1.txt"

# Marking done is atomic and only open handoffs can transition.
/bin/sh "$d2/town/government/handoff-queue.sh" mark "$d2/town" "$id1" done 'Act 18 section 7 published, evidence in PROCEEDINGS.md'
grep -Fq 'status: done' "$d2/town/records/handoffs/$id1.txt"
if /bin/sh "$d2/town/government/handoff-queue.sh" mark "$d2/town" "$id1" done 'again' 2>/dev/null; then
  echo "re-closing a closed handoff must fail" >&2
  exit 1
fi
# One open handoff still blocks the generic dispatch.
/bin/sh "$d2/town/government/executive-cycle.sh"
test "$(wc -l < "$OUTPUT")" -eq 3
if grep -Fq '301' "$PROMPT_FILE"; then echo "generic dispatch superseded the remaining open handoff" >&2; exit 1; fi
/bin/sh "$d2/town/government/handoff-queue.sh" mark "$d2/town" "$id2" superseded 'newer durable handoff arrived'
# With no open handoffs the generic dispatch resumes.
/bin/sh "$d2/town/government/executive-cycle.sh"
test "$(wc -l < "$OUTPUT")" -eq 4
grep -Fq '301' "$PROMPT_FILE"
test -s "$d2/state/branches/eligible-issues.json"

# No dispatch at all when the script fails before the queue read: a queue
# read crash exits non-zero and leaves the agent undispatched.
cat > "$d2/town/government/handoff-queue.sh" <<'BROKEN'
#!/bin/sh
echo "simulated queue read crash" >&2
exit 1
BROKEN
if /bin/sh "$d2/town/government/executive-cycle.sh" 2>/dev/null; then
  echo "dispatch must not occur when the queue read fails" >&2
  exit 1
fi
test "$(wc -l < "$OUTPUT")" -eq 4
# A missing charter is likewise a pre-read failure: no dispatch.
cp "$repo/government/handoff-queue.sh" "$d2/town/government/handoff-queue.sh"
if env -u VICHE_CONSTITUTION /bin/sh "$d2/town/government/executive-cycle.sh" 2>/dev/null; then
  echo "dispatch must not occur without the charter" >&2
  exit 1
fi
test "$(wc -l < "$OUTPUT")" -eq 4

echo 'Act 19 office-continuity and handoff smoke checks passed'

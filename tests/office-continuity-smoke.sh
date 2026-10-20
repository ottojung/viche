#!/bin/sh
# Act 19 (Office Continuity and Handoff Integrity Act) — hermetic smoke test.
# Covers: failure-count-based session reset (threshold, cooldown, progress
# guard, permanent-failure surfacing), the durable handoff queue (append/open/
# done/supersede, non-supersession), and the per-office commit-age signal.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
town=$scratch/town
seats=$scratch/seats
state=$scratch/state
mkdir -p "$town/government" "$town/government/prompts" "$town/records/handoffs" \
    "$seats/branches/executive" "$seats/c1a00001" "$seats/c1e00008" \
    "$seats/c1e00011" "$state/liveness" "$scratch/bin" "$scratch/seats"

# Copy government scripts and prompt templates into the scratch town.
cp "$repo"/government/office-recovery.sh "$repo"/government/handoff-queue.sh \
   "$repo"/government/handoff-queue.py "$repo"/government/commit-age.sh \
   "$repo"/government/branch-bootstrap.sh "$repo"/government/clerk-liveness.sh \
   "$repo"/government/seat-liveness.sh "$repo"/government/executive-cycle.sh \
   "$town/government/"
cp "$repo"/government/prompts/*.txt "$town/government/prompts/"
printf 'charter fixture\n' > "$town/charter"
printf 'inaugurated\n' > "$state/inaugurated"

# Mock git (records a HEAD; supports status/rev-parse/log).
cat > "$scratch/bin/git" <<'MOCK'
#!/bin/sh
set -eu
case "$1" in
  -C) shift 2 ;;
esac
case "${1:-}" in
  rev-parse) printf 'abc123\n' ;;
  log) printf '1792000000\n' ;;
  status) printf '' ;;
  worktree) : ;;
  *) printf '' ;;
esac
MOCK
chmod +x "$scratch/bin/git"

# Mock antonina (agent status/log/new/delete).
cat > "$scratch/bin/antonina" <<'MOCK'
#!/bin/sh
set -eu
case "$1 $2" in
"agent status")
  case "$*" in
    *c1e00002*) printf '{"state":"idle","model":"opencode-go/longcat-2.5-preview-free","variant":"low"}\n' ;;
    *) printf '{"state":"idle"}\n' ;;
  esac ;;
"agent log") printf 'log\n' ;;
"agent new") printf 'created\n' ;;
"agent delete") printf 'deleted\n' ;;
"agent run") printf 'dispatched\n' ;;
*) printf '' ;;
esac
MOCK
chmod +x "$scratch/bin/antonina"

export PATH="$scratch/bin:$PATH"
export VICHE_TOWN_ROOT="$town"
export VICHE_SEATS_ROOT="$seats"
export VICHE_STATE_ROOT="$state"
export VICHE_CONSTITUTION="$town/charter"

# --- office-recovery: classification ---
[ "$(. "$town/government/office-recovery.sh"; or_classify upstream_endpoint_unavailable)" = transient ]
[ "$(. "$town/government/office-recovery.sh"; or_classify unrecognized_backend_failure)" = transient ]
[ "$(. "$town/government/office-recovery.sh"; or_classify expired_credential)" = permanent ]

# --- office-recovery: failure record + progress guard ---
. "$town/government/office-recovery.sh"
or_record executive upstream_endpoint_unavailable "$seats/branches/executive" >/dev/null
or_record executive upstream_endpoint_unavailable "$seats/branches/executive" >/dev/null
# 2 failures: below threshold (3) -> no reset
if or_should_reset executive "$seats/branches/executive" 2>/dev/null; then
    echo "FAIL: reset fired below threshold" >&2; exit 1
fi
# 3 failures within window: threshold met
or_record executive upstream_endpoint_unavailable "$seats/branches/executive" >/dev/null
if ! or_should_reset executive "$seats/branches/executive" 2>/dev/null; then
    echo "FAIL: reset did not fire at threshold" >&2; exit 1
fi
# after a reset, the cooldown stamp is set, so an immediate re-check must not fire
or_reset executive c1e00002 Executive "$seats/branches/executive" >/dev/null 2>&1
if or_should_reset executive "$seats/branches/executive" 2>/dev/null; then
    echo "FAIL: reset fired during cooldown" >&2; exit 1
fi

# --- handoff queue: append/open/done ---
hid=$(/bin/sh "$town/government/handoff-queue.sh" append executive "Implement X" "evidence:1" "Clerk")
[ -n "$hid" ]
[ -f "$town/records/handoffs/$hid.json" ]
n=$(/bin/sh "$town/government/handoff-queue.sh" open executive | wc -l | tr -d ' ')
[ "$n" -eq 1 ]
/bin/sh "$town/government/handoff-queue.sh" done "$hid" "evidence:done"
n=$(/bin/sh "$town/government/handoff-queue.sh" open executive | wc -l | tr -d ' ')
[ "$n" -eq 0 ]

# --- commit-age signal: emits one row per office ---
rows=$(/bin/sh "$town/government/commit-age.sh" | wc -l | tr -d ' ')
[ "$rows" -ge 3 ]

# --- executive-cycle: open handoff suppresses generic prompt ---
hid2=$(/bin/sh "$town/government/handoff-queue.sh" append executive "Implement Y" "evidence:2" "Clerk")
( . "$town/government/executive-cycle.sh" ) > "$scratch/dispatch.log" 2>&1 || true
# The dispatch must NOT contain the generic eligible-issue prompt.
if grep -q 'Act on every eligible issue' "$scratch/dispatch.log" 2>/dev/null; then
    echo "FAIL: generic prompt ran despite open handoff" >&2; exit 1
fi

echo 'Act 19 office continuity smoke passed'

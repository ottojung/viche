#!/bin/sh
# SoringP1 #301 pool oversight: honest measurement, duplicate/stale detection,
# and registry-gated (non-fabricating) replenishment. Hermetic.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT
mkdir -p "$d/bin" "$d/town/government" "$d/state" "$d/launched" "$d/wt/soring301-unary-03"
cp "$repo/government/soringp1-oversight.sh" "$d/town/government/"

cat > "$d/bin/antonina" <<'MOCK'
#!/bin/sh
set -eu
case "$1 $2" in
  "agent list")
    case "$*" in
      *"--page 1"*) printf '%s\n' "$POOL_JSON" ;;
      *) printf '[]\n' ;;
    esac ;;
  "agent run")
    printf '%s\n' "$*" >> "$LAUNCH_LOG" ;;
  *) exit 9 ;;
esac
MOCK
chmod +x "$d/bin/antonina"
PATH="$d/bin:$PATH"

# Two live SoringP1 agents (one duplicate title) plus a non-SoringP1 agent.
POOL_JSON='{"agents":[
 {"id":"a1","cwd":"BASE/soring301-unary-01","title":"SoringP1: unary exact","last_activity_at":2000000000},
 {"id":"a2","cwd":"BASE/soring301-unary-02","title":"SoringP1: unary exact","last_activity_at":2000000000},
 {"id":"c1","cwd":"/var/lib/lubko/wd/viche-seats/branches/executive","title":"Executive","last_activity_at":2000000000}
]}'
POOL_JSON=$(printf '%s' "$POOL_JSON" | sed "s|BASE|$d/wt|g")
export PATH POOL_JSON
export VICHE_TOWN_ROOT="$d/town" VICHE_STATE_ROOT="$d/state"
export LAUNCH_LOG="$d/launched/log"
export SORINGP1_TARGET=5 SORINGP1_WORKTREE_BASE="$d/wt"

# 1. report: counts only SoringP1 agents, flags deficit and duplicate titles.
sh "$d/town/government/soringp1-oversight.sh" report > "$d/out" 2>&1
jq -e '.live==2 and .target==5 and .deficit==3 and .assessment=="under_target"' "$d/state/soringp1-oversight/status.json" >/dev/null
jq -e '.duplicate_titles|index("SoringP1: unary exact")' "$d/state/soringp1-oversight/status.json" >/dev/null

# 2. replenish with no registry: no launches (never fabricates).
sh "$d/town/government/soringp1-oversight.sh" replenish >/dev/null 2>&1
[ ! -s "$d/launched/log" ]

# 3. replenish with a curated registry: launches unused scopes only.
printf 'unary-03\tSoringP1: unary exact 3\tDo unary research packet 3.\n' > "$d/town/government/soringp1-scopes.tsv"
sh "$d/town/government/soringp1-oversight.sh" replenish >/dev/null 2>&1
grep -q 's1-unary-03' "$d/launched/log"

# 4. a scope whose title already runs is not relaunched (no duplicates).
printf 'unary-01\tSoringP1: unary exact\tDuplicate prompt.\n' > "$d/town/government/soringp1-scopes.tsv"
: > "$d/launched/log"
sh "$d/town/government/soringp1-oversight.sh" replenish >/dev/null 2>&1
[ ! -s "$d/launched/log" ]

echo 'SoringP1 pool oversight smoke passed'

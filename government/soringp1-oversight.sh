#!/bin/sh
# SoringP1 (#301) research-pool oversight — Phoebe-local, honest, bounded.
#
# This is an observability and coordination aid for the SoringP1 research pool
# on phoebe-dev. It never fabricates research prompts: replenishment is driven
# only by a curated scope registry (government/soringp1-scopes.tsv) supplied by
# the research operator. With no registry it reports and does nothing.
#
# Usage:
#   soringp1-oversight.sh report       (default) measure + record, read-only
#   soringp1-oversight.sh replenish    launch unused registered scopes up to target
#
# Target: the operative SoringP1 contract (AGENTS.md on main) targets FIVE
# simultaneous agents. Override with SORINGP1_TARGET.
set -eu

town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}/soringp1-oversight
target=${SORINGP1_TARGET:-5}
base=${SORINGP1_WORKTREE_BASE:-/home/lubko}
max_launch=${SORINGP1_MAX_LAUNCH:-3}
registry=$town/government/soringp1-scopes.tsv
mode=${1:-report}
mkdir -p "$state"
umask 077

is_num() { case "$1" in ''|*[!0-9]*) return 1;; *) return 0;; esac; }
is_num "$target" || { echo "soringp1-oversight: invalid target" >&2; exit 2; }
is_num "$max_launch" || { echo "soringp1-oversight: invalid max_launch" >&2; exit 2; }

# Enumerate running SoringP1 agents (cwd under /home/lubko/soring301).
pool=$state/pool.tsv
: > "$pool"
page=1
while :; do
    batch=$(antonina agent list --running --page "$page" --json 2>/dev/null) || {
        echo "soringp1-oversight: agent list unavailable" >&2; exit 1; }
    n=$(printf '%s' "$batch" | python3 -c '
import json,sys,os
d=json.load(sys.stdin); a=d.get("agents") if isinstance(d,dict) else d
for x in a:
    cwd=x.get("cwd","") or ""
    if cwd.startswith(os.environ.get("SORINGP1_WORKTREE_BASE","/home/lubko")+"/soring301"):
        print("%s\t%s\t%s\t%s" % (x.get("id",""), cwd, x.get("title",""), x.get("last_activity_at") or 0))
print("__COUNT__%d" % len(a))')
    printf '%s\n' "$n" | grep -v '^__COUNT__' >> "$pool" || :
    cnt=$(printf '%s\n' "$n" | sed -n 's/^__COUNT__//p')
    is_num "$cnt" || cnt=0
    [ "$cnt" -ge 50 ] || break
    page=$((page + 1))
done

live=$(wc -l < "$pool" | tr -d ' ')
now=$(date +%s)
# Duplicate titles among live agents (a duplicate-prompt warning signal).
dups=$(cut -f3 "$pool" 2>/dev/null | grep -v '^$' | sort | uniq -d | tr '\n' ',' | sed 's/,$//')
# Stale agents: running but no activity for > 30 min.
stale=$(awk -F'\t' -v now="$now" '$4+0 > 0 && now-$4 > 1800 {print $1}' "$pool" | tr '\n' ',' | sed 's/,$//')

status=$state/status.json
python3 - "$status" "$live" "$target" "$now" "$dups" "$stale" <<'PY'
import json,sys,os
path,live,target,now,dups,stale=sys.argv[1:7]
doc={"at":int(now),"live":int(live),"target":int(target),
     "deficit":max(0,int(target)-int(live)),
     "duplicate_titles":[d for d in dups.split(",") if d],
     "stale_agents":[s for s in stale.split(",") if s],
     "assessment":"under_target" if int(live)<int(target) else "at_or_above_target"}
open(path,"w").write(json.dumps(doc,sort_keys=True,indent=2)+"\n")
print(json.dumps(doc,sort_keys=True))
PY
cat "$pool" >> "$state/pool-history.tsv"

if [ "$mode" = replenish ]; then
    if [ ! -s "$registry" ]; then
        echo "soringp1-oversight: no scope registry ($registry); nothing launched" >&2
        exit 0
    fi
    launched=0
    while IFS="$(printf '\t')" read -r scope title prompt; do
        [ -n "$scope" ] || continue
        case "$scope" in \#*) continue;; esac
        [ "$live" -lt "$target" ] || break
        [ "$launched" -lt "$max_launch" ] || break
        if cut -f3 "$pool" | grep -Fxq "$title"; then
            continue   # already running
        fi
        if [ ! -d "$base/soring301-$scope" ]; then
            echo "soringp1-oversight: skip $scope (no worktree $base/soring301-$scope)" >&2
            continue
        fi
        antonina agent run --id "s1-$scope" --cwd "$base/soring301-$scope" \
            --prompt "$prompt" --detach >/dev/null 2>&1 || {
            echo "soringp1-oversight: launch failed for $scope" >&2; continue; }
        launched=$((launched + 1)); live=$((live + 1))
    done < "$registry"
    echo "soringp1-oversight: replenished $launched (live=$live target=$target)"
fi

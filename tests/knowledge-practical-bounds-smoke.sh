#!/bin/sh
# Hermetic tests for practical, honest Act34 cost ceilings. No live state touched.
set -eu
cd "$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)"
mod=government/knowledge-practical-bounds.py
tpl=government/knowledge-practical-bounds.conf.template
[ -s "$mod" ] && [ -s "$tpl" ]
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
cp "$tpl" "$d/profile.json"
run() { python3 "$mod" "$@"; }
fail=0
expect_ok() { label=$1; shift; if ! "$@" >/dev/null 2>&1; then echo "FAIL: $label" >&2; fail=1; fi; return 0; }
expect_deny() { label=$1; shift; if "$@" >/dev/null 2>&1; then echo "FAIL: $label passed" >&2; fail=1; fi; return 0; }

# Profile is honest and inert by default.
expect_ok 'template validates' run validate "$d/profile.json"
python3 - "$d/profile.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1])); assert p['enabled_offices']==[]; assert p['cap_kind']=='stop_on_detection'
assert p['strict_hard_cap_claimed'] is False; assert p['accounting_window_seconds']==3888000
PY

# Dishonest or weakened profiles fail closed.
python3 - "$d" <<'PY'
import json,sys,os
d=sys.argv[1]; base=json.load(open(d+'/profile.json'))
x=dict(base); x['cap_kind']='strict_hard_cap'; json.dump(x,open(d+'/bad-cap.json','w'))
x=dict(base); x['strict_hard_cap_claimed']=True; json.dump(x,open(d+'/bad-claim.json','w'))
x=dict(base); x['accounting_window_seconds']=1000; json.dump(x,open(d+'/bad-window.json','w'))
PY
expect_deny 'strict hard cap label denied' run validate "$d/bad-cap.json"
expect_deny 'strict cap claim denied' run validate "$d/bad-claim.json"
expect_deny '45d window change denied' run validate "$d/bad-window.json"

# Free tier: zero billing exposure, honest cap_kind.
out=$(run exposure "$d/profile.json" opencode-go/hy4-flash-free)
printf '%s' "$out" | python3 -c "
import json,sys
x=json.load(sys.stdin)
assert x['billing']['tier']=='zero_free_tier' and x['billing']['billing_exposure']==0
assert x['cap_kind']=='stop_on_detection' and x['strict_hard_cap'] is False
assert x['charge_is_accounting_bound_only'] is True
" || { echo 'FAIL: free exposure' >&2; fail=1; }

# Paid model without provider ceiling is refused.
out=$(run exposure "$d/profile.json" openai/gpt-6-luna)
printf '%s' "$out" | python3 -c "
import json,sys
x=json.load(sys.stdin); assert x['billing']['admit'] is False and x['billing']['tier']=='paid_unbounded'
" || { echo 'FAIL: paid model admitted without ceiling' >&2; fail=1; }

# Admission: not enabled -> denied; valid -> admitted; concurrency -> denied; cumulative -> denied.
python3 - "$d" <<'PY'
import json,sys
d=sys.argv[1]
json.dump({"tokens_total":0,"cpu_seconds":0,"wall_seconds":0,"by_office":{"statistics":{"tokens_total":0,"cpu_seconds":0,"wall_seconds":0}}},open(d+'/agg.json','w'))
for n,off in [('enabled',['statistics']),('empty',[])]:
    p=json.load(open(d+'/profile.json')); p['enabled_offices']=off; json.dump(p,open(d+'/p-%s.json'%n,'w'))
hi=json.load(open(d+'/agg.json')); hi['by_office']['statistics']['tokens_total']=399000
json.dump(hi,open(d+'/agg-high.json','w'))
PY
run admit "$d/p-empty.json" "$d/agg.json" statistics 0 > "$d/a0.json"
python3 -c "import json; x=json.load(open('$d/a0.json')); assert x['admit'] is False" || { echo 'FAIL: office not enabled admitted' >&2; fail=1; }
run admit "$d/p-enabled.json" "$d/agg.json" statistics 0 > "$d/a1.json"
python3 -c "import json; x=json.load(open('$d/a1.json')); assert x['admit'] is True and x['cap_kind']=='stop_on_detection'" || { echo 'FAIL: valid admit' >&2; fail=1; }
run admit "$d/p-enabled.json" "$d/agg.json" statistics 1 > "$d/a2.json"
python3 -c "import json; x=json.load(open('$d/a2.json')); assert x['admit'] is False" || { echo 'FAIL: concurrency ceiling' >&2; fail=1; }
run admit "$d/p-enabled.json" "$d/agg-high.json" statistics 0 > "$d/a3.json"
python3 -c "import json; x=json.load(open('$d/a3.json')); assert x['admit'] is False" || { echo 'FAIL: cumulative cap' >&2; fail=1; }

# Ambiguous exit holds full charge; never releases.
run ambiguous "$d/profile.json" "$d/agg.json" > "$d/amb.json"
python3 -c "import json; x=json.load(open('$d/amb.json')); assert x['state']=='held' and x['released']==0" || { echo 'FAIL: ambiguous hold' >&2; fail=1; }

[ "$fail" -eq 0 ] || { echo 'knowledge practical bounds smoke: FAILED' >&2; exit 1; }
echo 'knowledge practical bounds smoke: OK (honest labels, zero free tier, paid refusal, concurrency, cumulative, recovery)'

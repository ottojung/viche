#!/bin/sh
# Hermetic first Statistics deterministic trial; no model, network, production
# activation, budget, Judiciary opinion or publication is changed.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
town="$d/town"
state="$d/state"
mkdir -p "$town/government" "$town/records/knowledge" "$state"
cp "$repo/government/statistics-bounded-trial.py" "$repo/government/knowledge-budget-tool.py" "$repo/government/post_guard.py" "$town/government/"
cat > "$town/government/LAWS.md" <<'EOF'
## Act 32 — Institutional Knowledge and Communications Act (enacted 2026-11-20)
## Act 33 — Prospective Statistics Trial Clarification (enacted 2026-11-22)
EOF
# A fixture gate lets us test budgeting separately from the real independent
# phase verifier's existing comprehensive authorization test suite.
printf '#!/bin/sh\n[ "$1" = statistics ]\n' > "$town/government/knowledge-activation-verify.sh"
cat > "$town/government/statistics-report.py" <<'PY'
import os, pathlib, sys
p=pathlib.Path(os.environ["VICHE_STATE_ROOT"])/"called.txt"
with p.open("a") as out: out.write("ONE\n")
print("dummy fixture Statistics report without a model or network")
PY
printf '# A pinned inert Post fixture; not invoked in the trial smoke\n' > "$town/government/post.py"
cp "$repo/government/knowledge-budget.conf" "$town/government/knowledge-budget.conf"
# This smoke isolates the runner resource precharge from the separately
# tested independent Act33 first-trial evidence gate.
printf '#!/bin/sh\n[ "$1" = statistics ] && [ "$2" = first-trial ]\n' > "$town/government/statistics-preflight.sh"
printf '# exact audited helper fixture\n' > "$town/government/statistics-first-trial.py"
printf '# exact evidence fixture\n' > "$town/government/statistics-evidence.py"
printf '#!/bin/sh\nexit 0\n' > "$town/government/knowledge-phase-gate.sh"
printf '# exact phase verifier fixture\n' > "$town/government/knowledge-phase-verifier.py"
python3 - "$town/government/knowledge-budget.conf" <<'BUDGET_ENABLED'
import json,sys
p=sys.argv[1];c=json.load(open(p));c["offices"]["statistics"]["enabled"]=True
open(p,"w").write(json.dumps(c))
BUDGET_ENABLED
python3 - "$town" <<'PY'
import json,sys,time,hashlib
from pathlib import Path
root=Path(sys.argv[1])
a={}
for name,rel in (("runner","statistics-bounded-trial.py"),("report","statistics-report.py"),
                 ("post","post.py"),("post_guard","post_guard.py"),
                 ("budget_tool","knowledge-budget-tool.py"),("budget_config","knowledge-budget.conf"),
                 ("trial_preflight","statistics-preflight.sh"),("trial_verifier","statistics-first-trial.py"),
                 ("trial_evidence","statistics-evidence.py"),
                 ("activation_gate","knowledge-activation-verify.sh"),
                 ("phase_gate","knowledge-phase-gate.sh"),
                 ("phase_verifier","knowledge-phase-verifier.py")):
 a[name]=hashlib.sha256((root/"government"/rel).read_bytes()).hexdigest()
now=int(time.time())
(root/"records/knowledge/activation.json").write_text(json.dumps({
 "schema":"viche-knowledge-activation-v1",
 "offices":{"statistics":{"enabled":True,"authorized_by":"act:32:statistics",
 "trial_mode":"deterministic-v1","deterministic_sources":a,
 "not_before":now-1,"expires_at":now+86400}}
}))
PY
export VICHE_TOWN_ROOT="$town" VICHE_STATE_ROOT="$state"
script="$town/government/statistics-bounded-trial.py"
python3 "$script" | grep -q '"status": "published"'
test "$(wc -l < "$state/called.txt")" -eq 1
test "$(find "$state/knowledge/budget/reservations" -name 'det-statistics-*.json' | wc -l)" -eq 1
python3 "$script" | grep -q '"status": "already_attempted"'
test "$(wc -l < "$state/called.txt")" -eq 1
python3 - "$state" "$town" <<'PY'
import json,sys,datetime
from pathlib import Path
state=Path(sys.argv[1]);town=Path(sys.argv[2])
files=list((state/"knowledge/budget/reservations").glob("*.json"))
assert len(files)==1
r=json.loads(files[0].read_text())
assert r["state"]=="closed",r
assert r["usage"]["tokens_total"]==0
assert 0<=r["usage"]["cpu_seconds"]<=256
assert 0<=r["usage"]["wall_seconds"]<=64
assert r["usage"]["source"]=="observed_whole_host_cpu_upper_bound_non_attributed"
agg=json.loads((state/"knowledge/budget/aggregate.json").read_text())
assert agg["tokens_total"]==0
assert agg["cpu_seconds"]==r["usage"]["cpu_seconds"]
assert agg["wall_seconds"]==r["usage"]["wall_seconds"]
assert agg["counted"]==[r["id"]]
print("model-free Statistics attempt has one true-durable prepaid-and-metered budget record")
PY
# A forged hash or expired authorization must withhold the next attempt without
# creating any reservation. Use an empty state and changed authorization.
mv "$state" "$d/old-state"
mkdir "$state"
python3 - "$town" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1])/"records/knowledge/activation.json"
a=json.loads(p.read_text())
a["offices"]["statistics"]["deterministic_sources"]["post"]="0"*64
p.write_text(json.dumps(a))
PY
if python3 "$script" >/dev/null 2>&1; then echo 'FAIL: source-forged order accepted' >&2; exit 1; fi
test ! -d "$state/knowledge/budget/reservations"
echo 'statistics bounded first trial: one model-free daily attempt, durable charge, forged order denied'

#!/bin/sh
# Real Statistics->Post/Gazette within a sandbox. No live DB/agents/credentials.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
town="$d/town"
state="$d/state"
mkdir -p "$town/government" "$town/records/knowledge" "$state/institutional-outcomes" "$state/economy" "$state/branches"
cp "$repo/government/statistics-bounded-trial.py" "$repo/government/knowledge-budget-tool.py" \
   "$repo/government/statistics-report.py" "$repo/government/post.py" "$repo/government/post_guard.py" \
   "$repo/government/knowledge-budget.conf" "$town/government/"
# This smoke isolates the runner resource precharge from the separately
# tested independent Act33 first-trial evidence gate.
printf '#!/bin/sh\n[ "$1" = statistics ] && [ "$2" = first-trial ]\n' > "$town/government/statistics-preflight.sh"
printf '# exact audited helper fixture\n' > "$town/government/statistics-first-trial.py"
printf '# exact evidence fixture\n' > "$town/government/statistics-evidence.py"
printf '#!/bin/sh\nexit 0\n' > "$town/government/knowledge-phase-gate.sh"
printf '# exact phase verifier fixture\n' > "$town/government/knowledge-phase-verifier.py"
cat > "$town/government/LAWS.md" <<'EOF'
## Act 32 — Institutional Knowledge and Communications Act (enacted 2026-11-20)
## Act 33 — Prospective Statistics Trial Clarification (enacted 2026-11-22)
EOF
printf '#!/bin/sh\n[ "$1" = statistics ]\n' > "$town/government/knowledge-activation-verify.sh"
cat > "$state/institutional-outcomes/latest.json" <<'JSON'
{"agents":{"total":2},"git":{"main_commits":1},"board":{"open_first_page":2},"observed_at":1795372500,"delivery_verified_by_this_probe":false}
JSON
cat > "$state/economy/resources.json" <<'JSON'
{"at":"2026-11-22T18:30:00Z","overall":"ok","resources":{"disk:state":{"status":"ok"}}}
JSON
printf '%s\n' '{"caveat":"sampled only, no proof of verified outcome"}' > "$state/branches/judiciary-measurements.json"
python3 - "$town/government/knowledge-budget.conf" <<'BUDGET_ENABLED'
import json,sys
p=sys.argv[1];c=json.load(open(p));c["offices"]["statistics"]["enabled"]=True
open(p,"w").write(json.dumps(c))
BUDGET_ENABLED
python3 - "$town" <<'PY'
import json,sys,time,hashlib
from pathlib import Path
root=Path(sys.argv[1])
src={k:hashlib.sha256((root/"government"/f).read_bytes()).hexdigest()
     for k,f in (("runner","statistics-bounded-trial.py"),("report","statistics-report.py"),
                 ("post","post.py"),("post_guard","post_guard.py"),
                 ("budget_tool","knowledge-budget-tool.py"),("budget_config","knowledge-budget.conf"),
                 ("trial_preflight","statistics-preflight.sh"),("trial_verifier","statistics-first-trial.py"),
                 ("trial_evidence","statistics-evidence.py"),
                 ("activation_gate","knowledge-activation-verify.sh"),
                 ("phase_gate","knowledge-phase-gate.sh"),
                 ("phase_verifier","knowledge-phase-verifier.py"))}
now=int(time.time())
(root/"records/knowledge/activation.json").write_text(json.dumps({
"schema":"viche-knowledge-activation-v1",
"offices":{"statistics":{"enabled":True,"authorized_by":"act:32:statistics",
"trial_mode":"deterministic-v1","deterministic_sources":src,
"not_before":now-1,"expires_at":now+86400}}}))
PY
export VICHE_TOWN_ROOT="$town" VICHE_STATE_ROOT="$state"
python3 "$town/government/statistics-bounded-trial.py" > "$d/result.json"
jq -e '.status=="published" and .model_requests==0 and .real_outcome_verified==false' "$d/result.json" >/dev/null
test -s "$state/knowledge/statistics/snapshot-$(date -u +%Y-%m-%d).json"
python3 "$town/government/post.py" health > "$d/health.json"
jq -e '.healthy==true and .messages==2 and .publications==2 and .mail_triggered_model_dispatch==false' "$d/health.json" >/dev/null
python3 - "$state" <<'PY'
import sqlite3,sys
from pathlib import Path
db=sqlite3.connect(Path(sys.argv[1])/"post/post.sqlite3")
rows=db.execute("select topic,kind,body from messages order by topic").fetchall()
assert [r[0] for r in rows]==["statistics/outcomes","statistics/resources"]
assert all(r[1]=="observation" for r in rows)
assert "False" in rows[0][2] and "NOT verified useful outcomes" in rows[0][2]
PY
python3 "$town/government/statistics-bounded-trial.py" | grep -q '"already_attempted"'
python3 "$town/government/post.py" health | jq -e '.messages==2' >/dev/null
echo 'statistics actual Post integration: 2 source-backed observations, 0 model dispatches, idempotent budget'

#!/bin/sh
# Full broad Act34 adaptive launch, never self-authorization from JSON strings.
# Exercise existing institutional board/agent/appointment corroboration, real
# Executive permit source commit, Economy provider tier control and 48h stop.
# Everything lives inside an isolated /tmp Git fixture, never the live town.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
town="$d/town"; state="$d/state"
mkdir -p "$town/government" "$town/records/knowledge/permits" \
  "$town/records/knowledge/pilot-reviews" "$state/economy" \
  "$state/appointments" "$state/board" "$d/bin"
for f in knowledge-act34-gate.py knowledge-phase-verifier.py \
  knowledge-activation-verify.sh knowledge-budget.conf \
  knowledge-free-dispatch.sh knowledge-practical-bounds.py; do
 cp "$repo/government/$f" "$town/government/"
done
cp "$repo/tests/knowledge-free-dispatch-smoke.sh" "$town/tests-placeholder"
mkdir -p "$town/tests"
mv "$town/tests-placeholder" "$town/tests/knowledge-free-dispatch-smoke.sh"
cat > "$town/government/LAWS.md" <<'EOF'
## Act 32 — Institutional Knowledge and Communications Act (enacted 2026-11-20)
## Act 34 — Rapid Full Institutional Activation and Continuous Improvement Act (enacted 2026-11-23 by real ballot)
EOF
cat > "$town/government/branch-officers.tsv" <<'EOF'
executive	c1e00002	Executive
economy	c1e00012	Ministry of Economy
judiciary	c1e00008	Judiciary
EOF
cat > "$state/appointments/appointments.tsv" <<'EOF'
executive	exec-agent
economy	econ-agent
judiciary	jud-agent
EOF
cat > "$state/economy/model-policy.json" <<'EOF'
{"prefer":["opencode-go/hy4-flash-free"]}
EOF
cat > "$state/economy/catalogue.json" <<'EOF'
{"models":{"opencode-go/hy4-flash-free":{"tier":"free"},
 "provider/paid-free":{"tier":"paid"}}}
EOF
# Fake read-only Antonina coordination surface. The source verifier itself is
# real, and validates the board review, own-officer comment and live appointment.
cat > "$d/bin/antonina" <<'EOF'
#!/bin/sh
set -eu
case "$1 $2" in
  'board show')
    shift 2
    [ "$1" = --id ] || exit 2
    cat "$VICHE_STATE_ROOT/board/$2.json"
    ;;
  'agent status')
    shift 2
    [ "$1" = --id ] || exit 2
    printf '{"id":"%s","state":"idle"}\n' "$2"
    ;;
  *) exit 2;;
esac
EOF
chmod +x "$d/bin/antonina"
cat > "$town/records/knowledge/2026-11-23-economy-free-tier-prelaunch-allowlist-finding.md" <<'EOF'
Economy independently tested the per-invocation free-tier model selector:
 - The paid-free-looking model is refused by an Economy catalogue tier paid;
 - OpenCode continuations do not have hard token caps; free model cost measured 0.
 - This record certifies a MODEL SOURCE RESTRICTION, not a value outcome.
EOF
python3 - "$town" <<'PY'
import hashlib,json,sys,time
from pathlib import Path
root=Path(sys.argv[1]);now=int(time.time())
cfgpath=root/"government/knowledge-budget.conf"
cfg=json.loads(cfgpath.read_text())
offices=("statistics","foresight","strategy","spying")
for office in offices:cfg["offices"][office]["enabled"]=True
cfgpath.write_text(json.dumps(cfg))
digest=hashlib.sha256(cfgpath.read_bytes()).hexdigest()
rows={}
for office in offices:
 row={
  "schema":"viche-act34-operating-permit-v1",
  "office":office,"signer":"c1e00002",
  "authorized_by":"act:34:"+office,
  "not_before":now-25,"expires_at":now+86400*14,
  "budget_sha256":digest,"caps":cfg["offices"][office]["caps"],
  "provider_budget_mode":"zero-billed-runtime-allowlist",
  "provider_tier":"free_only","signature_status":"signed",
  "inflight_overrun_risk_disclosed":True,
  "cancellation":"stop-agent-and-hold-budget",
  "reboot_recovery":"reconcile-held-liability",
 }
 path=root/"records/knowledge/permits"/(office+".json")
 path.write_text(json.dumps(row))
 rows[office]={
    "enabled":True,"authorized_by":"act:34:"+office,
    "trial_mode":"adaptive-v1","signer":"c1e00002",
    "not_before":row["not_before"],"expires_at":row["expires_at"],
    "permit_ref":"records/knowledge/permits/"+office+".json",
    "permit_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
 }
(root/"records/knowledge/spying-source-scope.json").write_text('{"fixture":"exact-author source scope"}')
(root/"records/knowledge/activation.json").write_text(json.dumps({
  "schema":"viche-knowledge-activation-v1","offices":rows}))
PY
git -C "$town" init -q
git -C "$town" config user.name 'Act34 institutional integration fixture'
git -C "$town" config user.email 'fixture@example.invalid'
git -C "$town" add .
git -C "$town" commit -qm 'Original Executive permits and independently tested Economy control'
origin=$(git -C "$town" rev-parse HEAD)
# Authority attested AFTER original source commit, not via a self-authored
# source-commit hash embedded in the same file (that would be circular).
python3 - "$town" "$state" "$origin" <<'PY'
import hashlib,json,sys,time
from pathlib import Path
root, state, commit=Path(sys.argv[1]),Path(sys.argv[2]),sys.argv[3]
act=root/"records/knowledge/activation.json"
data=json.loads(act.read_text()); offices=("statistics","foresight","strategy","spying")
def att(role,agent,issue):
 return {"issue_id":issue,"expected_reviewer":role,"officer_agent_id":agent}
evidence={"artifact_commit":commit,
 "report_sha256":hashlib.sha256(
  (root/"records/knowledge/2026-11-23-economy-free-tier-prelaunch-allowlist-finding.md").read_bytes()).hexdigest(),
 "wrapper_sha256":hashlib.sha256((root/"government/knowledge-free-dispatch.sh").read_bytes()).hexdigest(),
 "bounds_sha256":hashlib.sha256((root/"government/knowledge-practical-bounds.py").read_bytes()).hexdigest(),
 "negative_test_sha256":hashlib.sha256((root/"tests/knowledge-free-dispatch-smoke.sh").read_bytes()).hexdigest(),
 "attestation":att("c1e00012","econ-agent","economy-test-issue")}
data["economy_free_tier_evidence"]=evidence
for office in offices:
 row=data["offices"][office]
 row["permit_origin_commit"]=commit
 row["permit_attestation"]=att("c1e00002","exec-agent","executive-test-issue")
act.write_text(json.dumps(data))
def issue(reviewer, gate_ids):
 return {"review":{"commit":commit,"verdict":"approve","reviewer":reviewer,
  "recordedAt":"2026-11-23T08:00:00Z"},
  "messages":[{"author":reviewer,"body":g+" "+commit[:12]+" reviewed"}
              for g in gate_ids]}
(state/"board/executive-test-issue.json").write_text(json.dumps(
 issue("c1e00002",["act34-executive-"+x for x in offices])))
(state/"board/economy-test-issue.json").write_text(json.dumps(
 issue("c1e00012",["act34-economy-free-provider-control"])))
PY
git -C "$town" add .
git -C "$town" commit -qm 'Second commitment: independently corroborated officer actions'
export VICHE_TOWN_ROOT="$town" VICHE_STATE_ROOT="$state" PATH="$d/bin:$PATH"
for office in statistics foresight strategy spying; do
 /bin/sh "$town/government/knowledge-activation-verify.sh" "$office"
done
echo 'PASS: FOUR broad adaptive offices, independent Exec+Economy board review/comment, Git source and agent appointment proof'
# A signer string in a valid Git JSON without the Board review is NOT enough.
cp "$state/board/executive-test-issue.json" "$d/review-good.json"
python3 - "$state/board/executive-test-issue.json" <<'PY'
from pathlib import Path
import json,sys
p=Path(sys.argv[1]);d=json.loads(p.read_text())
d["review"]["verdict"]="reject"
p.write_text(json.dumps(d))
PY
if /bin/sh "$town/government/knowledge-activation-verify.sh" statistics >/dev/null 2>&1; then
 echo 'FAIL: bogus Executive signed label passed without independent approval' >&2;exit 1
fi
cp "$d/review-good.json" "$state/board/executive-test-issue.json"
# A bogus paid provider whose model id ENDS in -free is NEVER free.
cp "$state/economy/model-policy.json" "$d/policy-good.json"
echo '{"prefer":["provider/paid-free"]}' > "$state/economy/model-policy.json"
if /bin/sh "$town/government/knowledge-activation-verify.sh" statistics >/dev/null 2>&1; then
 echo 'FAIL: billable provider with -free-looking id accepted' >&2;exit 1
fi
cp "$d/policy-good.json" "$state/economy/model-policy.json"
# Mutated uncommitted activation cannot grant authority.
python3 - "$town/records/knowledge/activation.json" <<'PY'
from pathlib import Path
import json,sys
p=Path(sys.argv[1]);d=json.loads(p.read_text())
d["offices"]["statistics"]["expires_at"]+=3600
p.write_text(json.dumps(d))
PY
if /bin/sh "$town/government/knowledge-activation-verify.sh" statistics >/dev/null 2>&1; then
 echo 'FAIL: unreviewed permit bytes accepted' >&2;exit 1
fi
git -C "$town" checkout -- records/knowledge/activation.json
# At T+48h a missing authentic Judiciary decision must BLOCK renewed dispatch.
# First verify that an adverse source-committed disposition is immediately
# binding (even before 48h); no self-attested legal authority exists.
python3 - "$town" <<'PY'
from pathlib import Path
import json,sys,time
root=Path(sys.argv[1]);activation=json.loads((root/"records/knowledge/activation.json").read_text())
row=activation["offices"]["statistics"]
p=root/"records/knowledge/pilot-reviews/statistics.json"
p.write_text(json.dumps({"schema":"viche-act34-judiciary-review-v1",
 "office":"statistics","reviewer":"c1e00008",
 "permit_sha256":row["permit_sha256"],
 "decision":"hold","reviewed_at":int(time.time())}))
PY
git -C "$town" add records/knowledge/pilot-reviews/statistics.json
git -C "$town" commit -qm 'Judiciary adverse review fixture'
if /bin/sh "$town/government/knowledge-activation-verify.sh" statistics >/dev/null 2>&1; then
 echo 'FAIL: uncorroborated/negative Judiciary verdict accepted' >&2;exit 1
fi
echo 'PASS: spoofed Exec review, deceptive paid-free model, forged permit, and uncorroborated Judiciary HOLD denied'

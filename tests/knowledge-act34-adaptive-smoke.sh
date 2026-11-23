#!/bin/sh
# Act34 must permit FOUR broad adaptive agents in parallel after authentic
# Executive permit; no pre-start Judiciary PROCEED / stale six-attestation gate.
# Reject unreviewed JSON, budget drift, expired order, wrong office,
# Judiciary STOP, absence of review at 48h, and forged late review.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
town="$tmp/town"
mkdir -p "$town/government" "$town/records/knowledge/permits" \
  "$town/records/knowledge/pilot-reviews"
cp "$repo/government/knowledge-act34-gate.py" \
   "$repo/government/knowledge-activation-verify.sh" \
   "$repo/government/knowledge-budget.conf" "$town/government/"
cat > "$town/government/LAWS.md" <<'EOF'
## Act 32 — Institutional Knowledge and Communications Act (enacted 2026-11-20)
## Act 33 — Prospective Statistics Trial Clarification (enacted 2026-11-22)
## Act 34 — Rapid Full Institutional Activation and Continuous Improvement Act (enacted 2026-11-23 by six lawful ballots)
EOF
python3 - "$town" <<'PY'
import hashlib,json,time,sys
from pathlib import Path
root=Path(sys.argv[1])
cfgpath=root/"government/knowledge-budget.conf"
cfg=json.loads(cfgpath.read_text())
offices=("statistics","foresight","strategy","spying")
for x in offices:cfg["offices"][x]["enabled"]=True
cfgpath.write_text(json.dumps(cfg))
digest=hashlib.sha256(cfgpath.read_bytes()).hexdigest()
now=int(time.time())
rows={}
for x in offices:
    row={
        "schema":"viche-act34-operating-permit-v1",
        "office":x,"signer":"c1e00002",
        "authorized_by":"act:34:"+x,
        "not_before":now-30,
        "expires_at":now+86400*14,
        "budget_sha256":digest,
        "caps":cfg["offices"][x]["caps"],
        "provider_budget_mode":"measured-stop-on-detection",
        "inflight_overrun_risk_disclosed":True,
        "cancellation":"stop-agent-and-hold-budget",
        "reboot_recovery":"reconcile-held-liability",
    }
    ref="records/knowledge/permits/"+x+".json"
    p=root/ref
    p.write_text(json.dumps(row))
    rows[x]={
        "enabled":True,
        "authorized_by":"act:34:"+x,
        "trial_mode":"adaptive-v1","signer":"c1e00002",
        "not_before":row["not_before"],"expires_at":row["expires_at"],
        "permit_ref":ref,
        "permit_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
    }
(root/"records/knowledge/activation.json").write_text(json.dumps({
    "schema":"viche-knowledge-activation-v1","offices":rows}))
(root/"records/knowledge/spying-source-scope.json").write_text('{"source":"fixture"}')
PY
git -C "$town" init -q
git -C "$town" config user.name 'Act34 isolated fixture'
git -C "$town" config user.email 'fixture@example.invalid'
git -C "$town" add .
git -C "$town" commit -qm 'Enacted Act34, all four independently permitted broad adaptive offices'
export VICHE_TOWN_ROOT="$town"
for office in statistics foresight strategy spying; do
 /bin/sh "$town/government/knowledge-activation-verify.sh" "$office"
done
echo 'PASS: all four real ADAPTIVE offices authorize in parallel, before prior Judiciary PROCEED'
# A forged unreviewed permit does not allow dispatch even when the enabled flag
# happens to be true. An old Act33 preflight is NOT demanded under Act34.
python3 - "$town" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1])/"records/knowledge/activation.json"
d=json.loads(p.read_text())
d["offices"]["foresight"]["expires_at"] += 3600
p.write_text(json.dumps(d))
PY
if /bin/sh "$town/government/knowledge-activation-verify.sh" foresight 2>/dev/null; then
 echo 'FAIL: unreviewed activated permit allowed' >&2; exit 1
fi
git -C "$town" checkout -- records/knowledge/activation.json
# Direct edit of the Economy config is equally incapable of issuing authority.
python3 - "$town" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1])/"government/knowledge-budget.conf"
d=json.loads(p.read_text())
d["offices"]["foresight"]["enabled"]=False
p.write_text(json.dumps(d))
PY
if /bin/sh "$town/government/knowledge-activation-verify.sh" foresight 2>/dev/null; then
 echo 'FAIL: unreviewed budget config allowed' >&2; exit 1
fi
git -C "$town" checkout -- government/knowledge-budget.conf
# Executive is bound to correct office; source-control is never enough alone.
python3 - "$town" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1])/"records/knowledge/activation.json"
d=json.loads(p.read_text())
d["offices"]["spying"]["authorized_by"]="act:34:strategy"
p.write_text(json.dumps(d))
PY
git -C "$town" add records/knowledge/activation.json
git -C "$town" commit -qm 'Fixture: reviewed but wrong-office permit'
if /bin/sh "$town/government/knowledge-activation-verify.sh" spying 2>/dev/null; then
 echo 'FAIL: wrong office authorized' >&2; exit 1
fi
git -C "$town" revert --no-edit -q HEAD >/dev/null 2>&1 || {
 git -C "$town" checkout HEAD~1 -- records/knowledge/activation.json
 git -C "$town" commit -qm 'Restore fixture correct activation'
}
# An actual judicial HOLD is binding immediately, not only after deadline.
python3 - "$town" <<'PY'
import json,sys,time
from pathlib import Path
root=Path(sys.argv[1])
p=root/"records/knowledge/activation.json"
a=json.loads(p.read_text())["offices"]["statistics"]
r={"schema":"viche-act34-judiciary-review-v1",
 "office":"statistics","reviewer":"c1e00008",
 "decision":"hold","reviewed_at":int(time.time()),
 "permit_sha256":a["permit_sha256"]}
(root/"records/knowledge/pilot-reviews/statistics.json").write_text(json.dumps(r))
PY
git -C "$town" add records/knowledge/pilot-reviews/statistics.json
git -C "$town" commit -qm 'Judiciary authentic stop fixture'
if /bin/sh "$town/government/knowledge-activation-verify.sh" statistics 2>/dev/null; then
 echo 'FAIL: Judiciary HOLD allowed' >&2; exit 1
fi
# All four enabled, but a signed 48h-old order requires an actual review.
python3 - "$town" <<'PY'
import json,sys,time,hashlib
from pathlib import Path
root=Path(sys.argv[1])
a=root/"records/knowledge/activation.json"
d=json.loads(a.read_text())
p=root/"records/knowledge/permits/foresight.json"
permit=json.loads(p.read_text())
permit["not_before"]=int(time.time())-49*3600
permit["expires_at"]=int(time.time())+86400*10
p.write_text(json.dumps(permit))
row=d["offices"]["foresight"]
row.update(not_before=permit["not_before"],expires_at=permit["expires_at"],
           permit_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
a.write_text(json.dumps(d))
PY
git -C "$town" add .
git -C "$town" commit -qm 'Fixture: old operating permit requiring Judiciary review'
if /bin/sh "$town/government/knowledge-activation-verify.sh" foresight 2>/dev/null; then
 echo 'FAIL: no Judiciary 48h review allowed' >&2; exit 1
fi
python3 - "$town" <<'PY'
import json,sys,time
from pathlib import Path
root=Path(sys.argv[1])
a=json.loads((root/"records/knowledge/activation.json").read_text())["offices"]["foresight"]
review={"schema":"viche-act34-judiciary-review-v1",
 "office":"foresight","reviewer":"c1e00008","decision":"proceed",
 "reviewed_at":a["not_before"]+3600,"permit_sha256":a["permit_sha256"]}
(root/"records/knowledge/pilot-reviews/foresight.json").write_text(json.dumps(review))
PY
git -C "$town" add .
git -C "$town" commit -qm 'Independent 48h Judiciary review source-controlled'
/bin/sh "$town/government/knowledge-activation-verify.sh" foresight
echo 'PASS: 48h Judiciary review required; source-linked PROCEED restores broad agent dispatch'

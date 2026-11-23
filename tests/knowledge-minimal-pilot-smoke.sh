#!/bin/sh
# Four real source-attested Gazette observations, zero model/provider calls,
# reversible first-use authorization and fsynced cumulative Economy charges.
# Runs in a private Git repository / SQLite fixture; NEVER live activation.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
town="$d/town"
state="$d/state"
mkdir -p "$town/government" "$town/records/predictions" \
  "$town/records/knowledge" "$state/institutional-outcomes" "$state/economy"
for f in knowledge-minimal-pilot.py knowledge-minimal-observer.py knowledge-budget-tool.py \
         knowledge-budget.conf post.py post_guard.py; do
  cp "$repo/government/$f" "$town/government/"
done
cat > "$town/government/LAWS.md" <<'EOF'
## Act 32 — Institutional Knowledge and Communications Act (enacted 2026-11-20)
## Act 34 — Minimum Viable Knowledge Institutions Pilot Act (enacted 2026-11-23)
EOF
cat > "$town/government/spying-source-preflight.sh" <<'EOF'
#!/bin/sh
[ "$1" = "$VICHE_TOWN_ROOT" ] || exit 1
echo '{"decision":"allow","source_validated_by":"independent_test_fixture"}'
EOF
cat > "$state/institutional-outcomes/latest.json" <<'EOF'
{"agents":{"total":12},"delivery_verified_by_this_probe":false}
EOF
cat > "$state/economy/resources.json" <<'EOF'
{"resources":{"disk:state":{"status":"short","used_pct":80,"avail_gib":40,"hours_to_full":1000}}}
EOF
cat > "$town/records/predictions/calibration.json" <<'EOF'
{"counts":{"registered":26,"due":20,"due_resolved":20,"due_scored":7,"unresolved":13},"brier":{"aggregate":0.243214},"due_resolution_coverage":1.0,"due_scored_coverage":0.35,"act32_calibration_minimum_gate":{"eligible":true}}
EOF
cat > "$town/records/knowledge/spying-source-allowlist.json" <<'EOF'
{"schema":"viche-spying-source-allowlist-v1","expires_at":1799020800,"antonina":{"messages":{"abc":{},"def":{}}},"github_public":{"repos":{"ottojung/viche":{}}}}
EOF
python3 - "$town" <<'PY'
import json,sys,hashlib,time
from pathlib import Path
root=Path(sys.argv[1])
src={k:hashlib.sha256((root/"government"/f).read_bytes()).hexdigest()
     for k,f in (("runner","knowledge-minimal-pilot.py"),
                 ("observer","knowledge-minimal-observer.py"),
                 ("post","post.py"),("budget_tool","knowledge-budget-tool.py"))}
now=int(time.time())
offices={x:{"enabled":True,"authorized_by":"act:34:"+x,
            "trial_mode":"deterministic-v1","signer":"c1e00002",
            "not_before":now-3,"expires_at":now+86400,
            "provider_requests_max":0,"tokens_cap":0,
            "caps":{"tokens_total":0,"cpu_seconds":160,"wall_seconds":40},
            "cancellation":"Executive stop is immediate; new jobs refuse on expiry",
            "reboot_recovery":"Held Economy liabilities remain charged across reboot",
            "deterministic_sources":src}
         for x in ("statistics","foresight","strategy","spying")}
(root/"records/knowledge/activation.json").write_text(json.dumps({
 "schema":"viche-knowledge-activation-v1","offices":offices}))
p=root/"government/knowledge-budget.conf"
cfg=json.loads(p.read_text())
for x in offices:cfg["offices"][x]["enabled"]=True
p.write_text(json.dumps(cfg))
PY
git -C "$town" init -q
git -C "$town" config user.name 'Viche isolated integration fixture'
git -C "$town" config user.email 'fixture@example.invalid'
git -C "$town" add .
git -C "$town" commit -qm 'Freeze independently reviewed test permit and Economy budget'
export VICHE_TOWN_ROOT="$town" VICHE_STATE_ROOT="$state"
for office in statistics foresight strategy spying; do
  if ! timeout -k 2 38 python3 "$town/government/knowledge-minimal-pilot.py" "$office" --run > "$d/$office.json"; then
    echo "pilot $office failed: $(cat "$d/$office.json")" >&2
    exit 1
  fi
  jq -e --arg office "$office" '.office==$office and .status=="published" and
    .provider_requests==0 and .verified_useful_outcome==false and
    .counts_as_operational_institution==false' "$d/$office.json" >/dev/null
done
python3 "$town/government/post.py" health > "$d/post.json"
jq -e '.healthy==true and .messages==4 and .publications==4 and
       .mail_triggered_model_dispatch==false' "$d/post.json" >/dev/null
python3 - "$state" <<'PY'
import json,sys
from pathlib import Path
root=Path(sys.argv[1])/"knowledge/budget"
receipts=list((root/"reservations").glob("mvp-*.json"))
assert len(receipts)==4,receipts
for f in receipts:
 x=json.loads(f.read_text())
 assert x["state"]=="closed" and x["usage"]["tokens_total"]==0,x
 assert 0<=x["usage"]["cpu_seconds"]<=160,x
 assert 0<=x["usage"]["wall_seconds"]<=40,x
 assert x["model_requests"]==0,x
agg=json.loads((root/"aggregate.json").read_text())
assert agg["tokens_total"]==0
assert len(agg["counted"])==4
print("4 closed same-ledger prepaid receipts, zero provider tokens")
PY
for office in statistics foresight strategy spying; do
  python3 "$town/government/knowledge-minimal-pilot.py" "$office" --run |
    jq -e '.status=="already_attempted"' >/dev/null
done
python3 "$town/government/post.py" health | jq -e '.messages==4' >/dev/null
# Mutating a source-controlled permit without review must NOT grant new runs.
python3 - "$town" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1])/"records/knowledge/activation.json"
a=json.loads(p.read_text());a["offices"]["statistics"]["expires_at"]+=3600
p.write_text(json.dumps(a))
PY
if python3 "$town/government/knowledge-minimal-pilot.py" statistics --run >/dev/null 2>&1; then
  echo 'FAIL: unreviewed activation.json edit passed' >&2
  exit 1
fi
# At T+48h, absence of independently filed Judiciary review must stop NEW
# operations. Commit a window old enough to trigger the 48-hour gate.
git -C "$town" checkout -- records/knowledge/activation.json
python3 - "$town" <<'PYREVIEW'
import json,sys,time
from pathlib import Path
p=Path(sys.argv[1])/"records/knowledge/activation.json"
a=json.loads(p.read_text())
now=int(time.time())
a["offices"]["statistics"]["not_before"]=now-49*3600
a["offices"]["statistics"]["expires_at"]=now+12*3600
p.write_text(json.dumps(a))
PYREVIEW
git -C "$town" add records/knowledge/activation.json
git -C "$town" commit -qm 'Fixture time travel: signed order now past 48h'
if python3 "$town/government/knowledge-minimal-pilot.py" statistics --run >/dev/null 2>&1; then
  echo 'FAIL: no Judiciary check after 48h authorized run' >&2
  exit 1
fi
mkdir -p "$town/records/knowledge/pilot-reviews"
echo '{"office":"statistics","reviewer":"c1e00008","decision":"proceed"}' > "$town/records/knowledge/pilot-reviews/statistics.json"
# An uncommitted Judiciary finding is not yet reviewed.
if python3 "$town/government/knowledge-minimal-pilot.py" statistics --run >/dev/null 2>&1; then
  echo 'FAIL: unreviewed Judiciary record authorized run' >&2
  exit 1
fi
git -C "$town" add records/knowledge/pilot-reviews/statistics.json
git -C "$town" commit -qm 'Review fixture: Judiciary proceed after first observations'
python3 "$town/government/knowledge-minimal-pilot.py" statistics --run |
  jq -e '.status=="already_attempted"' >/dev/null
echo 'Act34 model-free pilot: Gazette ×4, true shared ledger, 0 requests, no duplicate, forged permit denied; 48h judicial review enforced'

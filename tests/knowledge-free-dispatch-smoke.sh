#!/bin/sh
# Hermetic tests for the per-invocation FREE-ONLY Antonina allowlist wrapper.
# No live agent is dispatched; global model config is never touched.
set -eu
cd "$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)"
wrap=government/knowledge-free-dispatch.sh
[ -s "$wrap" ]
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
mkdir -p "$d/state/economy" "$d/town/government" "$d/town/records/economy/evidence" "$d/bin"
cat > "$d/state/economy/catalogue.json" <<'CATALOGUE'
{"models":{
  "opencode/tidepool-alpha-free":{"tier":"free"},
  "opencode/hy4-flash-free":{"tier":"free"},
  "opencode-go/hy4-flash-free":{"tier":"free"},
  "opencode-go/hungerg-free":{"tier":"free"},
  "provider/paid-free":{"tier":"free"}
}}
CATALOGUE
cp government/knowledge-practical-bounds.py government/knowledge-zero-billed.py "$d/town/government/"
cp records/economy/evidence/2026-11-24-provider-models.json "$d/town/records/economy/evidence/"
python3 - "$d/town/government/knowledge-zero-billed-policy.json" "$d/town/records/economy/evidence/provider-snapshot.json" <<'BILLINGPY'
import hashlib,json,sys
policy,snapshot=sys.argv[1:]
data={"object":"list","data":[
 {"id":"tidepool-alpha-free","owned_by":"opencode","cost":{"text":{"input":{"price":0,"cache":{"read":0}},"output":{"price":0}}}},
 {"id":"hy4-flash-free","owned_by":"opencode","cost":{"text":{"input":{"price":0,"cache":{"read":0}},"output":{"price":0}}}}
]}
blob=json.dumps(data,sort_keys=True,separators=(",",":")).encode()
open(snapshot,"wb").write(blob)
p={"schema":"viche-zero-billed-model-policy-v1",
 "source":{"url":"https://opencode.ai/inference/v1/models","retrieved_at":"2026-11-24T00:00:00Z","sha256":hashlib.sha256(blob).hexdigest()},
 "review_after":"2099-01-01T00:00:00Z",
 "snapshot_ref":"records/economy/evidence/provider-snapshot.json","snapshot_sha256":hashlib.sha256(blob).hexdigest(),
 "models":{
  "opencode/tidepool-alpha-free":{"provider":"opencode","provider_model":"tidepool-alpha-free","cost":{"input":0,"output":0,"cache_read":0}},
  "opencode/hy4-flash-free":{"provider":"opencode","provider_model":"hy4-flash-free","cost":{"input":0,"output":0,"cache_read":0}}
 }}
json.dump(p,open(policy,"w"))
BILLINGPY
# CI has no actual Antonina global config; create a sentinel and verify that
# successful and rejected per-invocation dispatches never modify it.
mkdir -p "$d/global/antonina"
printf '%s\n' '{"models":[{"model":"global-sentinel"}]}' > "$d/global/antonina/config.json"
cp "$d/global/antonina/config.json" "$d/global-before.json"
XDG_CONFIG_HOME="$d/global"
export XDG_CONFIG_HOME
export VICHE_ZERO_BILLED_SNAPSHOT=provider-snapshot.json

python3 - "$d/state/economy/model-policy.json" <<'PY'
import json,sys
json.dump({"prefer":["opencode/tidepool-alpha-free","opencode/hy4-flash-free"],"exclude":[]},open(sys.argv[1],"w"))
PY
# Stub antonina records the env and args instead of dispatching.
cat > "$d/bin/antonina" <<'EOF'
#!/bin/sh
printf 'XDG=%s ARGS=%s\n' "${XDG_CONFIG_HOME:-}" "$*" > "$CAPTURE"
EOF
chmod +x "$d/bin/antonina"
fail=0

# The wrapper builds a free-only config from policy and pins XDG on `run`.
CAPTURE="$d/capture" VICHE_TOWN_ROOT="$d/town" VICHE_STATE_ROOT="$d/state" \
  PATH="$d/bin:$PATH" /bin/sh "$wrap" run --id fake --cwd /tmp --prompt hi --detach
grep -q "XDG=$d/state/knowledge/free-allowlist ARGS=agent run --id fake --cwd /tmp --prompt hi --detach" "$d/capture" ||
  { echo 'FAIL: XDG not pinned / args changed' >&2; fail=1; }
python3 - "$d/state/knowledge/free-allowlist/antonina/config.json" <<'PY'
import json,sys
c=json.load(open(sys.argv[1]))
assert [e['model'] for e in c['models']]==['opencode/tidepool-alpha-free','opencode/hy4-flash-free']
assert all('-free' in e['model'] and e['variant']=='low' for e in c['models'])
PY

# Global ladder is untouched (wrapper works from a temp state root only).
cmp -s "$d/global/antonina/config.json" "$d/global-before.json" ||
  { echo 'FAIL: global config changed' >&2; fail=1; }

# A disguised paid id containing -free mid-string must be refused.
python3 - "$d/state/economy/model-policy.json" <<'PYMASK'
import json,sys
json.dump({"prefer":["provider/paid-free-trial"],"exclude":[]},open(sys.argv[1],"w"))
PYMASK
if CAPTURE="$d/capture3" VICHE_TOWN_ROOT="$d/town" VICHE_STATE_ROOT="$d/state" \
   PATH="$d/bin:$PATH" /bin/sh "$wrap" run --id fake --cwd /tmp --prompt hi --detach >/dev/null 2>&1; then
 echo 'FAIL: disguised paid id admitted' >&2; fail=1
fi

# A model literally named paid-free is STILL PAID, even though its id
# ends in -free AND the production-style name-derived catalogue says free.
# Only absence from the exact provider-cost policy may reject it.
python3 - "$d/state/economy/model-policy.json" <<'PYPRETEND'
import json,sys
json.dump({"prefer":["provider/paid-free"],"exclude":[]},open(sys.argv[1],"w"))
PYPRETEND
if CAPTURE="$d/capture4" VICHE_TOWN_ROOT="$d/town" VICHE_STATE_ROOT="$d/state" \
  PATH="$d/bin:$PATH" /bin/sh "$wrap" run --id fake --cwd /tmp --prompt hi --detach >/dev/null 2>&1; then
  echo 'FAIL: deceptive paid-free provider was admitted as free' >&2; fail=1
fi

# A non-free id in policy prefer is refused (fail closed).
python3 - "$d/state/economy/model-policy.json" <<'PY'
import json,sys
json.dump({"prefer":["openai/gpt-6-luna"],"exclude":[]},open(sys.argv[1],"w"))
PY
if CAPTURE="$d/capture2" VICHE_TOWN_ROOT="$d/town" VICHE_STATE_ROOT="$d/state" \
  PATH="$d/bin:$PATH" /bin/sh "$wrap" run --id fake --cwd /tmp --prompt hi --detach >/dev/null 2>&1; then
  echo 'FAIL: non-free id admitted' >&2; fail=1
fi

# A secondary-catalogue-only free ID is omitted from the Act34 allowlist;
# the primary-confirmed model still dispatches and the global ladder is untouched.
python3 - "$d/state/economy/model-policy.json" <<'PYSECONDARY'
import json,sys
json.dump({"prefer":["opencode/hy4-flash-free","opencode-go/hy4-flash-free","opencode-go/hungerg-free"]},open(sys.argv[1],"w"))
PYSECONDARY
CAPTURE="$d/capture7" VICHE_TOWN_ROOT="$d/town" VICHE_STATE_ROOT="$d/state" \
  PATH="$d/bin:$PATH" /bin/sh "$wrap" run --id fake --cwd /tmp --prompt hi --detach
python3 - "$d/state/knowledge/free-allowlist/antonina/config.json" <<'PYOMIT'
import json,sys
c=json.load(open(sys.argv[1]));assert [e['model'] for e in c['models']]==['opencode/hy4-flash-free']
PYOMIT

# A reviewed exact ID with a nonzero provider cost is refused.
cp "$d/town/government/knowledge-zero-billed-policy.json" "$d/billing-good.json"
python3 - "$d/town/government/knowledge-zero-billed-policy.json" "$d/state/economy/model-policy.json" <<'PYCOST'
import json,sys
billing,policy=sys.argv[1:]
b=json.load(open(billing))
b["models"]["opencode/hy4-flash-free"]["cost"]["output"]=0.1
json.dump(b,open(billing,"w"))
json.dump({"prefer":["opencode/hy4-flash-free"]},open(policy,"w"))
PYCOST
if CAPTURE="$d/capture5" VICHE_TOWN_ROOT="$d/town" VICHE_STATE_ROOT="$d/state" \
   PATH="$d/bin:$PATH" /bin/sh "$wrap" run --id fake --cwd /tmp --prompt hi --detach >/dev/null 2>&1; then
  echo 'FAIL: nonzero provider cost admitted' >&2; fail=1
fi
cp "$d/billing-good.json" "$d/town/government/knowledge-zero-billed-policy.json"

# Expired provider-cost evidence fails closed even for an exact free ID.
python3 - "$d/town/government/knowledge-zero-billed-policy.json" <<'PYEXP'
import json,sys
p=sys.argv[1];b=json.load(open(p));b["review_after"]="2000-01-01T00:00:00Z";json.dump(b,open(p,"w"))
PYEXP
if CAPTURE="$d/capture6" VICHE_TOWN_ROOT="$d/town" VICHE_STATE_ROOT="$d/state" \
   PATH="$d/bin:$PATH" /bin/sh "$wrap" run --id fake --cwd /tmp --prompt hi --detach >/dev/null 2>&1; then
  echo 'FAIL: expired zero-cost evidence admitted' >&2; fail=1
fi
cp "$d/billing-good.json" "$d/town/government/knowledge-zero-billed-policy.json"

# A new provider billing object (for example image/audio pricing) is unknown,
# not implicitly free. Refuse even when the familiar text prices stay zero.
python3 - "$d/town/records/economy/evidence/provider-snapshot.json" "$d/town/government/knowledge-zero-billed-policy.json" <<'PYDIM'
import hashlib,json,sys
snapshot,policy=sys.argv[1:]
d=json.load(open(snapshot))
d["data"][1]["cost"]["image"]={"input":{"price":0.1}}
blob=json.dumps(d,sort_keys=True,separators=(",",":")).encode();open(snapshot,"wb").write(blob)
b=json.load(open(policy))
b["source"]["sha256"]=hashlib.sha256(blob).hexdigest();b["snapshot_sha256"]=b["source"]["sha256"]
json.dump(b,open(policy,"w"))
PYDIM
if CAPTURE="$d/capture8" VICHE_TOWN_ROOT="$d/town" VICHE_STATE_ROOT="$d/state" \
   PATH="$d/bin:$PATH" /bin/sh "$wrap" run --id fake --cwd /tmp --prompt hi --detach >/dev/null 2>&1; then
  echo 'FAIL: unknown provider billing dimension admitted' >&2; fail=1
fi
# Restore the exact fixture snapshot and policy for the digest calculation.
python3 - "$d/town/records/economy/evidence/provider-snapshot.json" "$d/town/government/knowledge-zero-billed-policy.json" <<'PYRESTORE'
import hashlib,json,sys
snapshot,policy=sys.argv[1:]
d=json.load(open(snapshot));d["data"][1]["cost"].pop("image",None)
blob=json.dumps(d,sort_keys=True,separators=(",",":")).encode();open(snapshot,"wb").write(blob)
b=json.load(open(policy))
b["source"]["sha256"]=hashlib.sha256(blob).hexdigest();b["snapshot_sha256"]=b["source"]["sha256"]
json.dump(b,open(policy,"w"))
PYRESTORE

cmp -s "$d/global/antonina/config.json" "$d/global-before.json" ||
  { echo 'FAIL: rejected dispatch modified global config' >&2; fail=1; }
[ "$fail" -eq 0 ] || { echo 'knowledge free dispatch smoke: FAILED' >&2; exit 1; }
echo 'knowledge free dispatch smoke: OK (XDG pinned, exact-ID zero-cost allowlist, global untouched, fail-closed)'
python3 - "$PWD/government/knowledge-zero-billed.py" "$wrap" \
  government/knowledge-zero-billed-policy.json government/knowledge-practical-bounds.py \
  tests/knowledge-free-dispatch-smoke.sh government/knowledge-act34-gate.py \
  government/knowledge-office-cycle.sh \
  records/economy/evidence/2026-11-24-provider-models.json <<'PYDIGEST'
import datetime,importlib.util,sys
spec=importlib.util.spec_from_file_location("zb",sys.argv[1]);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
# Validate the committed evidence as of publication; the runtime gate uses the
# real clock and the fixture above separately proves expiry fails closed.
data=m.load_verified(sys.argv[3],now=datetime.datetime(2026,11,24,18,0,tzinfo=datetime.timezone.utc),snapshot_path=sys.argv[8])
import json,pathlib,tempfile,hashlib
expected={"opencode-go/"+mid for mid in ("beam-free","hy4-flash-free","hungerg-free","iceman-contributor-free")}
assert expected <= set(data["models"])
assert set(m.verified_subset(sys.argv[3],sorted(expected),snapshot_path=sys.argv[8])) == expected
# Route mismatch and corrupted Go bytes cannot authorize a Go model.
with tempfile.TemporaryDirectory() as td:
    p=pathlib.Path(td)
    primary=p/"primary.json";primary.write_bytes(pathlib.Path(sys.argv[8]).read_bytes())
    go=p/pathlib.Path(data["go_source"]["snapshot_ref"]).name
    go.write_bytes((pathlib.Path(sys.argv[8]).parent/go.name).read_bytes())
    policy=p/"policy.json"
    bad=json.loads(json.dumps(data));bad["go_source"]["url"]="https://opencode.ai/inference/v1/models"
    policy.write_text(json.dumps(bad))
    try:m.load_verified(policy,now=datetime.datetime(2026,11,24,18,0,tzinfo=datetime.timezone.utc),snapshot_path=primary)
    except ValueError:pass
    else:raise AssertionError("wrong Go route admitted")
    policy.write_text(json.dumps(data));go.write_bytes(b"{}")
    try:m.load_verified(policy,now=datetime.datetime(2026,11,24,18,0,tzinfo=datetime.timezone.utc),snapshot_path=primary)
    except ValueError:pass
    else:raise AssertionError("changed Go snapshot admitted")
paths={"wrapper":sys.argv[2],"zero_billed_policy":sys.argv[3],"bounds":sys.argv[4],"negative_test":sys.argv[5],"verifier":sys.argv[1],"gate":sys.argv[6],"cycle":sys.argv[7],"provider_snapshot":sys.argv[8]}
print("PRODUCTION_NEGATIVE_ACCEPTANCE_DIGEST="+m.negative_acceptance_digest(paths))
PYDIGEST

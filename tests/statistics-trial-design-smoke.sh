#!/bin/sh
# Hermetic tests for the DRAFT first-trial design verifier. Throwaway town +
# git fixture only; canonical records, state and live town are never touched.
set -eu
cd "$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)"
repo=$(pwd -P)
ver=$repo/government/statistics-trial-design-verifier.py
dict_src=$repo/records/knowledge/first-trial-source-dict-20261122.json
[ -s "$ver" ] && [ -s "$dict_src" ]

d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
town=$d/town
mkdir -p "$town/government" "$town/records/knowledge"
python3 - "$repo" "$town" <<'PY'
import hashlib,json,os,shutil,sys
repo,town=sys.argv[1:3]
d=json.load(open(os.path.join(repo,"records/knowledge/first-trial-source-dict-20261122.json")))
# Materialise every pinned code path first (real bytes where they exist).
for i,(key,entry) in enumerate(sorted(d["code_sources"].items())):
    p=entry["path"]; full=os.path.join(town,p); os.makedirs(os.path.dirname(full),exist_ok=True)
    real=os.path.join(repo,p)
    if os.path.isfile(real):
        shutil.copy(real,full)
    else:
        open(full,"w").write("fixture code %d\n" % i)
# Pin the dict to the exact bytes now present in the fixture.
for entry in d["code_sources"].values():
    p=entry["path"]
    entry["sha256"]=hashlib.sha256(open(os.path.join(town,p),"rb").read()).hexdigest()
os.makedirs(os.path.join(town,"records/knowledge"),exist_ok=True)
json.dump(d,open(os.path.join(town,"records/knowledge/first-trial-source-dict-20261122.json"),"w"),sort_keys=True,indent=2)
for name in ("TRIAL-DESIGN-ACT33-20261122.md","EXEC-ORDER-DRAFT-ACT33-20261122.md",
             "FIRST-TRIAL-NO-GO-LIST-20261122.md"):
    shutil.copy(os.path.join(repo,"records/knowledge",name),os.path.join(town,"records/knowledge",name))
shutil.copytree(os.path.join(repo,"records/knowledge/first-trial-baseline-20261122"),
                os.path.join(town,"records/knowledge/first-trial-baseline-20261122"))
shutil.copy(os.path.join(repo,"records/knowledge/activation.json"),
            os.path.join(town,"records/knowledge/activation.json"))
open(os.path.join(town,"government/LAWS.md"),"w").write(
 "## Act 32 — Institutional Knowledge and Communications Act (enacted 2026-11-20)\n"
 "## Act 33 — Prospective Statistics Trial Clarification (enacted 2026-11-22, bill act32-prospective-statistics-trial-amendment)\n"
 "sha256 65345025166713b43816b27ea2d982a87809df956c258ac022dca7a274528a9d\n")
PY
git init -q "$town"
git -C "$town" checkout -q -b main
git -C "$town" config user.email viche-test@invalid
git -C "$town" config user.name viche-test
git -C "$town" add -A
git -C "$town" commit -q -m 'fixture: reviewed bytes on main'
dict=records/knowledge/first-trial-source-dict-20261122.json
boot=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["baseline"]["boot_id"])' "$town/$dict")

run() { python3 "$ver" "$town" "$town/$dict" "$@"; }
expect_pass() { label=$1; shift; if ! "$@" >/dev/null 2>&1; then echo "FAIL: $label denied" >&2; fail=1; fi; }
expect_deny() { label=$1; shift; if "$@" >/dev/null 2>&1; then echo "FAIL: $label passed" >&2; fail=1; fi; }
fail=0

# coherent DRAFT, all reviewed bytes on main, no mechanical no-go blockers
expect_pass 'coherent DRAFT' run verify-draft --boot-id "$boot"
expect_pass 'all pinned bytes landed' run verify-landed
expect_pass 'no mechanical blockers' run no-go --boot-id "$boot"

# Informational deterministic-source preregistration is allowed during DRAFT
# only with the exact six-field shape and valid hashes. Current source bytes are
# checked separately by verify-landed against the authoritative source dict.
cp "$town/records/knowledge/activation.json" "$d/activation.good"
python3 - "$town" <<'PY'
import json,sys,os
t=sys.argv[1]; p=os.path.join(t,"records/knowledge/activation.json")
d=json.load(open(p)); d["offices"]["statistics"]["deterministic_sources"]["runner"]="not-a-sha256"
json.dump(d,open(p,"w"))
PY
expect_deny 'draft deterministic source malformed hash' run verify-draft --boot-id "$boot"
cp "$d/activation.good" "$town/records/knowledge/activation.json"
python3 - "$town" <<'PY'
import json,sys,os
t=sys.argv[1]; p=os.path.join(t,"records/knowledge/activation.json")
d=json.load(open(p)); del d["offices"]["statistics"]["deterministic_sources"]["post"]
json.dump(d,open(p,"w"))
PY
expect_deny 'draft deterministic source set incomplete' run verify-draft --boot-id "$boot"
cp "$d/activation.good" "$town/records/knowledge/activation.json"

out=$(run no-go --boot-id "$boot")
printf '%s\n' "$out" | grep -q 'external_gates_required' || { echo 'FAIL: external gates not reported' >&2; fail=1; }
printf '%s\n' "$out" | grep -q 'must NOT self-verify' || { echo 'FAIL: judiciary self-verify warning missing' >&2; fail=1; }

# byte drift on canonical main fails landed + no-go closed
printf 'tampered\n' > "$town/government/statistics-report.py"
git -C "$town" add -A && git -C "$town" commit -q -m 'tamper reporter'
expect_deny 'byte drift on main' run verify-landed
expect_deny 'no-go detects drift' run no-go --boot-id "$boot"

# draft separation: enabling an office or budget flag fails closed
python3 - "$town" <<'PY'
import json,sys,os
t=sys.argv[1]; p=os.path.join(t,"records/knowledge/activation.json")
d=json.load(open(p)); d["offices"]["statistics"]["enabled"]=True; json.dump(d,open(p,"w"))
PY
expect_deny 'draft enabling statistics' run verify-draft --boot-id "$boot"
python3 - "$town" <<'PY'
import json,sys,os
t=sys.argv[1]; p=os.path.join(t,"government/knowledge-budget.conf")
d=json.load(open(p)); d["offices"]["statistics"]["enabled"]=True; json.dump(d,open(p,"w"))
PY
expect_deny 'draft enabling budget' run verify-draft --boot-id "$boot"

# frozen baseline tamper and boot mismatch fail closed
cp "$town/records/knowledge/first-trial-baseline-20261122/economy.resources.json" "$d/econ.good"
printf 'tamper\n' > "$town/records/knowledge/first-trial-baseline-20261122/economy.resources.json"
expect_deny 'tampered frozen baseline' run verify-draft --boot-id "$boot"
cp "$d/econ.good" "$town/records/knowledge/first-trial-baseline-20261122/economy.resources.json"
expect_deny 'boot mismatch' run verify-draft --boot-id 'some-other-boot'

# missing DRAFT markers / no-go items fail closed
python3 - "$town/records/knowledge/EXEC-ORDER-DRAFT-ACT33-20261122.md" <<'PY'
import sys
p=sys.argv[1]; s=open(p).read().replace("DRAFT","FINAL").replace("NOT SIGNED","SIGNED")
open(p,"w").write(s)
PY
expect_deny 'order no longer DRAFT' run verify-draft --boot-id "$boot"

if [ "$fail" -ne 0 ]; then echo 'statistics trial design smoke: FAILED' >&2; exit 1; fi
echo 'statistics trial design smoke: OK (draft coherent, byte pinning, no-go, no self-verification)'

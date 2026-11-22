#!/bin/sh
# Hermetic adversarial tests for the enacted-Act 33 FIRST Statistics trial
# preflight mode. Everything runs in a throwaway town + git repo fixture;
# canonical records, state and the live town are never touched.
#
# Covers: precisely-enacted-law recognition, UNAVAILABLE honesty, prospective
# design, frozen/same-boot sources, enforced hard cap, 14-day order, expiring,
# officer-bound and independently corroborated Judiciary proceed; plus a wall of
# fail-closed cases (old law, forged officer, all-green JSON without
# corroboration, unavailable/stop-on-detection cap, expired order, missing or
# tampered source, fabricated numerator, successors/efficacy, wrong act).
set -eu
cd "$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)"
repo=$(pwd -P)
helper=$repo/government/statistics-first-trial.py
legacy=$repo/government/statistics-evidence.py
preflight=$repo/government/statistics-preflight.sh
[ -s "$helper" ] && [ -s "$legacy" ] && [ -s "$preflight" ]

d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
town=$d/town
art=$town/records/knowledge/first-trial-artifacts
src=$town/records/knowledge/first-trial-sources-20261122
corr=$town/records/knowledge/first-trial-corroboration
att=$town/records/knowledge/statistics-first-trial-preflight-20261122.json
mkdir -p "$town/government" "$art" "$src" "$corr" "$town/records/knowledge"
cp "$helper" "$town/government/statistics-first-trial.py"
cp "$legacy" "$town/government/statistics-evidence.py"

git init -q "$town"
git -C "$town" config user.email viche-test@invalid
git -C "$town" config user.name viche-test

# --- authoritative law and officer registry -------------------------------
laws=$town/government/LAWS.md
cat > "$laws" <<'EOF'
## Act 32 — Institutional Knowledge and Communications Act (enacted 2026-11-20T07:33:00Z by recorded vote on bill institutional-knowledge-and-communications-act-v4)
base law text; amended by Act 33 for the first trial only.

## Act 33 — Prospective Statistics Trial Clarification (enacted 2026-11-22, bill act32-prospective-statistics-trial-amendment)
Enacted by recorded vote present=6 yes=6 no=0 abstain=0 (quorum=6, required_yes=6).
Definitive bill sha256 65345025166713b43816b27ea2d982a87809df956c258ac022dca7a274528a9d.
This amendment applies only to the first reversible Statistics measurement trial.

## Historical enactments (not operative)
EOF
cp "$laws" "$laws.good"
printf 'executive\tc1e00002\tExecutive\njudiciary\tc1e00008\tJudiciary\neconomy\tc1e00012\tMinistry of Economy\nstatistics\tc1e00013\tStatistics Bureau\n' \
  > "$town/government/branch-officers.tsv"

# --- frozen primary sources with a single observed boot -------------------
boot=boot-fixture-20261122
printf 'primary source alpha\n' > "$src/alpha.json"
printf 'primary source beta\n'  > "$src/beta.json"
printf 'primary source gamma\n' > "$src/gamma.json"
for f in alpha beta gamma; do cp "$src/$f.json" "$d/$f.json.good"; done
observed=1795361000
python3 - "$src" "$boot" "$observed" "$d/sources-array.json" <<'PY'
import hashlib,json,os,sys
d,boot,at,outpath=sys.argv[1],sys.argv[2],int(sys.argv[3]),sys.argv[4]
out=[]
for name in ("alpha.json","beta.json","gamma.json"):
    b=open(os.path.join(d,name),"rb").read()
    out.append({"snapshot":name,"sha256":hashlib.sha256(b).hexdigest(),
                "size_bytes":len(b),"boot_id":boot,"observed_at":at+7,
                "role":"frozen primary source","path":"state/fixture/"+name})
json.dump(out,open(outpath,"w"),sort_keys=True)
PY
sources_json=$d/sources-array.json
digest=$(python3 "$helper" digest "$sources_json")
src_hashes=$(python3 -c 'import json,sys; print(",".join(sorted(x["sha256"] for x in json.load(open(sys.argv[1])))))' "$sources_json")

# --- Git-anchored, officer-bound review artifacts -------------------------
python3 - "$art" "$digest" "$src_hashes" <<'PY'
import os,sys
d,digest,hashes=sys.argv[1:4]
gates={
 "prospective_design":("c1e00002","executive"),
 "frozen_sources_same_boot":("c1e00012","economy"),
 "economy_safety_hard_cap":("c1e00012","economy"),
 "executive_order_14d":("c1e00002","executive"),
 "judiciary_proceed":("c1e00008","judiciary"),
 "source_corroboration":("c1e00008","judiciary"),
}
withhashes={"frozen_sources_same_boot","judiciary_proceed","source_corroboration"}
for key,(reviewer,role) in gates.items():
    text=("gate: %s\nreviewer: %s\nrole: %s\ndecision: proceed\n"
          "evidence_digest: %s\n" % (key,reviewer,role,digest))
    if key in withhashes:
        text+="source_hashes: %s\n" % hashes
    text+="reviewed_at: 2026-11-22T18:00:00Z\n"
    open(os.path.join(d,key+".txt"),"w").write(text)
PY
git -C "$town" add government records
git -C "$town" commit -q -m 'first trial hermetic fixtures'
commit=$(git -C "$town" rev-parse HEAD)

# --- separate institutional corroboration export (not the attestation) ----
python3 - "$corr/20261122.json" "$commit" <<'PY'
import json,sys
path,commit=sys.argv[1:3]
gates={
 "prospective_design":"c1e00002","frozen_sources_same_boot":"c1e00012",
 "economy_safety_hard_cap":"c1e00012","executive_order_14d":"c1e00002",
 "judiciary_proceed":"c1e00008","source_corroboration":"c1e00008",
}
export={"schema":"viche-first-trial-corroboration-export-1",
        "reviews":[{"commit":commit,"verdict":"approve","reviewer":who,
                    "recordedAt":"2026-11-22T18:05:00Z"} for g,who in gates.items()],
        "comments":[{"author":who,"body":"independently reviewed %s against %s" % (g,commit[:7])}
                    for g,who in gates.items()],
        "appointments":{"executive":"c1e00002","judiciary":"c1e00008","economy":"c1e00012"}}
json.dump(export,open(path,"w"),sort_keys=True,indent=2)
PY
cp "$corr/20261122.json" "$d/corr.good"

# --- the first-trial attestation (EVIDENCE, not authority by itself) ------
not_before=1795362000
expires=$((not_before + 1209600))
at=1795370000
python3 - "$att" "$sources_json" "$digest" "$commit" "$art" "$boot" "$observed" "$not_before" "$expires" "$corr/20261122.json" <<'PY'
import hashlib,json,os,sys
(path,sources_json,digest,commit,art,boot,observed,nb,exp,corr_ref)=sys.argv[1:11]
sources=json.load(open(sources_json))
arts={}
for key in ("prospective_design","frozen_sources_same_boot","economy_safety_hard_cap",
            "executive_order_14d","judiciary_proceed","source_corroboration"):
    p=os.path.join(art,key+".txt")
    arts[key]={"git_commit":commit,"git_path":"records/knowledge/first-trial-artifacts/"+key+".txt",
               "sha256":hashlib.sha256(open(p,"rb").read()).hexdigest()}
signers={"prospective_design":("c1e00002","Executive"),
         "frozen_sources_same_boot":("c1e00012","Ministry of Economy"),
         "economy_safety_hard_cap":("c1e00012","Ministry of Economy"),
         "executive_order_14d":("c1e00002","Executive"),
         "judiciary_proceed":("c1e00008","Judiciary"),
         "source_corroboration":("c1e00008","Judiciary")}
gates={k:{"status":"green","owner":signers[k][1],
          "evidence_ref":"records/knowledge/first-trial-artifacts/%s.txt"%k,
          "reviewer":signers[k][0],"artifact":arts[k]} for k in arts}
record={
 "schema":"viche-statistics-first-trial-preflight-1","office":"statistics",
 "host":"billy-dev","act":33,"act_bill_id":"act32-prospective-statistics-trial-amendment",
 "act_bill_sha256":"65345025166713b43816b27ea2d982a87809df956c258ac022dca7a274528a9d",
 "readiness":"ready","decision":"proceed_first_trial_only","scope":"first_trial_only",
 "successors_enabled":False,"efficacy_claimed":False,
 "authority":"Evidence only; withholds readiness for the first reversible trial; enables no office.",
 "design":{
   "prospective":{
     "endpoint":"rate of independently verified genuine operational-failure discoveries per 1000 agent-hours",
     "population":"concrete failures blocking a statutory Viche function with a determinable status in the window",
     "selection":"all such failures with first_independent_verification in the window; no selective suppression",
     "missingness":"unverifiable or censored events reported separately, never imputed as zero",
     "negative_controls":["report and record counts","agent process exits","main-branch commits","forecast registrations","detector clears"],
     "comparator":"equal-length pre-activation business-as-usual window, same collectors, no Statistics dispatch",
     "observation_window":"14 days spanning a host reboot",
     "falsifiers":["any benefit claim from process counts","any unpaired cost denominator","any tampered source"]},
   "historical_numerator":{"status":"UNAVAILABLE","reason":"no matched independently verified historical window"},
   "per_office_cpu":{"status":"UNAVAILABLE","reason":"no per-office cgroup or telemetry on billy-dev"},
   "whole_host_cpu":{"status":"MEASURED_UPPER_BOUND","tag":"UPPER_BOUND",
                     "reason":"pessimistic whole-host charge for safety only, never marginal cost"},
   "same_boot":{"boot_id":boot,"observed_by":"economy","observed_at":int(observed),
                "reliable":True,"sources_observed":[s["snapshot"] for s in sources]}},
 "sources":sources,"evidence_digest":digest,
 "safety":{"hard_cap":True,"strict_inflight":True,"stop_on_detection":False,
           "enforced":True,"accumulate_across_trials":True,
           "tokens_cap":400000,"host_cpu_upper_bound":1800,"host_cpu_tag":"UPPER_BOUND",
           "negative_test_digest":"sha256:fixture-negative-cap-test",
           "meter":"opencode-session-v2 plus proc-stat-host-busy-upper-bound"},
 "order":{"office":"statistics","act":33,"host":"billy-dev",
          "not_before":int(nb),"expires_at":int(exp),"signer":"c1e00002",
          "cancellation":"reversible order; single Statistics-only window; cancellation on any overrun",
          "reboot_recovery":"in-flight reservations fail closed across reboot; no silent reauthorization"},
 "judiciary":{"decision":"proceed","reviewer":"c1e00008",
              "source_hashes":sorted(s["sha256"] for s in sources),
              "finding_ref":"records/knowledge/first-trial-artifacts/judiciary_proceed.txt"},
 "gates":gates,
 "corroboration_export":"records/knowledge/first-trial-corroboration/20261122.json",
}
json.dump(record,open(path,"w"),sort_keys=True,indent=2)
PY
cp "$att" "$att.good"

# --- small mutation helpers ------------------------------------------------
set_field() { # dotted.path jsonValue
  python3 - "$att" "$1" "$2" <<'PY'
import json,sys
p,dotted,raw=sys.argv[1:4]
d=json.load(open(p)); cur=d; parts=dotted.split(".")
for k in parts[:-1]:
    cur = cur[int(k)] if k.isdigit() and isinstance(cur,list) else cur[k]
k=parts[-1]
cur[k]=json.loads(raw)
json.dump(d,open(p,"w"),sort_keys=True,indent=2)
PY
}
del_field() { # dotted.path
  python3 - "$att" "$1" <<'PY'
import json,sys
p,dotted=sys.argv[1:3]
d=json.load(open(p)); cur=d; parts=dotted.split(".")
for k in parts[:-1]:
    cur = cur[int(k)] if k.isdigit() and isinstance(cur,list) else cur[k]
k=parts[-1]
if isinstance(cur,dict): cur.pop(k,None)
elif isinstance(cur,list): del cur[int(k)]
json.dump(d,open(p,"w"),sort_keys=True,indent=2)
PY
}
restore() { cp "$att.good" "$att"; }

expect_pass() {
  label=$1; shift
  if ! "$@" >/dev/null 2>&1; then
    echo "FAIL: $label was denied (should pass)" >&2; fail=1
  fi
}
expect_deny() {
  label=$1; shift
  if "$@" >/dev/null 2>&1; then
    echo "FAIL: $label passed (should fail closed)" >&2; fail=1
  fi
}
fail=0
run_preflight() { VICHE_TOWN_ROOT="$town" VICHE_AT="${AT:-$at}" /bin/sh "$preflight" "$1" "${2:-first-trial}"; }

# --- the genuine all-evidence case ----------------------------------------
expect_pass 'fully corroborated first-trial attestation' run_preflight statistics
out=$(python3 "$helper" check "$town" "$att" "$at")
printf '%s\n' "$out" | grep -q '"decision": "proceed"' || {
  echo 'FAIL: check did not report proceed' >&2; fail=1; }
# Other offices are a no-op, even in the new mode.
expect_pass 'non-statistics office untouched' run_preflight foresight first-trial

# --- old law / no Act 33 / wrong bill hash --------------------------------
cat > "$laws" <<'EOF'
## Act 32 — Institutional Knowledge and Communications Act (enacted 2026-11-20T07:33:00Z by recorded vote on bill institutional-knowledge-and-communications-act-v4)
only the old law exists; no Amendment/Act 33.
## Historical enactments (not operative)
EOF
expect_deny 'old law without Act 33' run_preflight statistics
cp "$laws.good" "$laws"
sed -i 's/65345025166713b43816b27ea2d982a87809df956c258ac022dca7a274528a9d/0000000000000000000000000000000000000000000000000000000000000000/' "$laws"
expect_deny 'Act 33 with wrong bill sha256' run_preflight statistics
cp "$laws.good" "$laws"

# --- no external attestation / all-green JSON alone -----------------------
del_field corroboration_export
expect_deny 'all-green JSON without corroboration export' run_preflight statistics
restore
python3 - "$corr/20261122.json" <<'PY'
import json,sys
p=sys.argv[1]; d=json.load(open(p)); d["reviews"]={}; json.dump(d,open(p,"w"),sort_keys=True)
PY
expect_deny 'no institutional board review' run_preflight statistics
python3 - "$corr/20261122.json" <<'PY'
import json,sys
p=sys.argv[1]; d=json.load(open(p))
for r in d["reviews"]: r["verdict"]="reject"
json.dump(d,open(p,"w"),sort_keys=True)
PY
expect_deny 'board review verdict reject' run_preflight statistics
cp "$d/corr.good" "$corr/20261122.json"
python3 - "$corr/20261122.json" <<'PY'
import json,sys
p=sys.argv[1]; d=json.load(open(p))
for x in d["comments"]: x["author"]="c1e00002"
json.dump(d,open(p,"w"),sort_keys=True)
PY
expect_deny 'forged officer (wrong comment author)' run_preflight statistics
cp "$d/corr.good" "$corr/20261122.json"
python3 - "$corr/20261122.json" <<'PY'
import json,sys
p=sys.argv[1]; d=json.load(open(p)); d["appointments"]["judiciary"]="c1e00002"; json.dump(d,open(p,"w"),sort_keys=True)
PY
expect_deny 'forged officer (appointment registry mismatch)' run_preflight statistics
cp "$d/corr.good" "$corr/20261122.json"

# --- unavailable / stop-on-detection cap, tampered artifacts --------------
set_field safety.hard_cap false
expect_deny 'unavailable hard cap' run_preflight statistics
restore
set_field safety.stop_on_detection true
expect_deny 'stop-on-detection cap' run_preflight statistics
restore
set_field 'gates.economy_safety_hard_cap.artifact.git_commit' '"0000000000000000000000000000000000000000"'
expect_deny 'non-existent artifact commit' run_preflight statistics
restore
set_field 'gates.judiciary_proceed.reviewer' '"c1e00002"'
expect_deny 'judiciary gate signed by non-judiciary' run_preflight statistics
restore

# --- expiry / wrong act / scope creep -------------------------------------
AT=$expires expect_deny 'expired Executive order' run_preflight statistics
AT=$at
set_field act 32
expect_deny 'wrong act (32 instead of 33)' run_preflight statistics
restore
set_field successors_enabled true
expect_deny 'successor enabled by first-trial mode' run_preflight statistics
restore
set_field efficacy_claimed true
expect_deny 'efficacy claim in first-trial mode' run_preflight statistics
restore

# --- sources: missing, tampered, cross-boot, unattested -------------------
rm "$src/gamma.json"
expect_deny 'missing frozen source' run_preflight statistics
cp "$d/gamma.json.good" "$src/gamma.json"
printf 'TAMPERED\n' > "$src/alpha.json"
expect_deny 'tampered frozen source' run_preflight statistics
cp "$d/alpha.json.good" "$src/alpha.json"
printf 'unattested\n' > "$src/extra.json"
expect_deny 'unattested extra source' run_preflight statistics
rm "$src/extra.json"
set_field design.same_boot.boot_id '"different-boot"'
expect_deny 'source observed under a different boot' run_preflight statistics
restore
set_field 'judiciary.source_hashes' '[]'
expect_deny 'judiciary proceed not tied to source hashes' run_preflight statistics
restore

# --- UNAVAILABLE honesty and prospective design ---------------------------
set_field design.historical_numerator.status '"VERIFIED"'
expect_deny 'fabricated historical numerator' run_preflight statistics
restore
set_field design.per_office_cpu.value 0
set_field design.per_office_cpu.status '"MEASURED"'
expect_deny 'zero-filled per-office CPU' run_preflight statistics
restore
del_field design.prospective.negative_controls
expect_deny 'prospective design without negative controls' run_preflight statistics
restore
del_field design.same_boot
expect_deny 'no same-boot observation' run_preflight statistics
restore
set_field design.whole_host_cpu.tag '"ACTUAL_OFFICE_CPU"'
expect_deny 'whole-host CPU mislabelled as actual office CPU' run_preflight statistics
restore

# --- the two modes must not be confused -----------------------------------
cp "$att" "$town/records/knowledge/statistics-trial-preflight-20261120.json"
if VICHE_TOWN_ROOT="$town" /bin/sh "$preflight" statistics legacy >/dev/null 2>&1; then
  echo 'FAIL: first-trial record accepted by legacy efficacy gate' >&2; fail=1
fi
rm "$town/records/knowledge/statistics-trial-preflight-20261120.json"

if [ "$fail" -ne 0 ]; then
  echo 'statistics first-trial smoke: FAILED' >&2
  exit 1
fi
echo 'statistics first-trial smoke: OK (Act 33 law binding, corroborated gates, UNAVAILABLE honesty, hard cap, 14d order, fail-closed)'

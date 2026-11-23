#!/bin/sh
# The Bureau can decide entirely new questions, methods and measurement types.
# There is NO metric registry or configured list of allowed domains.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
t="$d/town"
mkdir -p "$t/government" "$t/records/statistics/inquiries" "$t/records/evidence"
cp "$repo/government/statistics-inquiry.py" "$t/government/"
tool="$t/government/statistics-inquiry.py"
cat > "$t/records/evidence/event-sample.txt" <<'TXT'
first sample cohort contains three distinct source-attested event ids
TXT
digest=$(sha256sum "$t/records/evidence/event-sample.txt" | cut -d' ' -f1)
python3 - "$t/records/statistics/inquiries" "$digest" <<'PY'
import json,sys
from pathlib import Path
folder=Path(sys.argv[1]);sha=sys.argv[2]
# Two truly unrelated domains without any predefined metrics. The Bureau
# chooses its own question, interpretation and observation representation.
a={
  "schema":"viche-statistics-inquiry-v1", "id":"forgotten-liveness-recurrence",
  "stage":"candidate","question":"Which failures silently recur after closure?",
  "why_now":"Repeated reopening of decisions; need evidence beyond closure marks",
  "decision_use":"Decide whether to audit closed-case recurrence before adding agents"
}
(folder/(a["id"]+".json")).write_text(json.dumps(a))
b={
  "schema":"viche-statistics-inquiry-v1","id":"unexpected-communication-exposure",
  "stage":"measured",
  "question":"How often does an opt-in notification lead to useful new evidence?",
  "why_now":"New Gazette has changed what institutions may discover",
  "decision_use":"Choose between a new triage protocol and doing nothing",
  "method":"Manually inspect a frozen random sample of source-attested notifications",
  "population":"Three distinct notifications in a frozen original cohort",
  "missingness":"The unobserved recipients are recorded unknown, never zero",
  "limitations":"Small, selected example; not a causal efficacy claim",
  "source_dependence":"One original source; copied reports excluded from independent counts",
  "negative_controls":"Messages with no published action are expected to generate no response",
  "evidence":[{"path":"records/evidence/event-sample.txt","sha256":sha}],
  "result":{"interval":[0.0,0.33],"category":"preliminary","new_kind":"arbitrarily defined by investigator"}
}
(folder/(b["id"]+".json")).write_text(json.dumps(b))
PY
python3 "$tool" agenda --root "$t" > "$d/index"
jq -e '.count==2 and ([.inquiries[].question]|unique|length)==2' "$d/index" >/dev/null
for f in "$t"/records/statistics/inquiries/*.json; do
  python3 "$tool" check "$f" --root "$t" | jq -e .valid >/dev/null
done
# Changing a claimed observation MUST invalidate stale source provenance.
printf '\nnew observation\n' >> "$t/records/evidence/event-sample.txt"
if python3 "$tool" check "$t/records/statistics/inquiries/unexpected-communication-exposure.json" \
   --root "$t" > /dev/null 2>&1; then
  echo 'FAIL: altered primary source accepted' >&2; exit 1
fi
# An early question remains possible when evidence is missing; do not force
# the office to select only pre-measurable, low-value questions.
python3 "$tool" check "$t/records/statistics/inquiries/forgotten-liveness-recurrence.json" --root "$t" >/dev/null
# Allow retirement with a reason and specific revisit condition, preserving
# the record rather than quietly deleting a metric that performed poorly.
python3 - "$t/records/statistics/inquiries/forgotten-liveness-recurrence.json" <<'PY'
import json,sys
p=sys.argv[1];x=json.load(open(p))
x.update(stage="retired",retirement_reason="Case population inaccessible this week",
         revisit_when="When audit sampling retains original case close and reopen times")
open(p,"w").write(json.dumps(x))
PY
python3 "$tool" check "$t/records/statistics/inquiries/forgotten-liveness-recurrence.json" --root "$t" >/dev/null
# No file may declare itself independently verified without independent
# corroboration; copied/relabelled claims remain non-authoritative.
python3 - "$t/records/statistics/inquiries/forgotten-liveness-recurrence.json" <<'PY'
import json,sys
p=sys.argv[1];x=json.load(open(p));x["stage"]={"oops":"invalid"};open(p,"w").write(json.dumps(x))
PY
if python3 "$tool" check "$t/records/statistics/inquiries/forgotten-liveness-recurrence.json" \
   --root "$t" > /dev/null 2>&1; then
  echo 'FAIL: non-string stage accepted' >&2; exit 1
fi
# Preserve the anti-substitution boundary: preselected telemetry is never
# automatically equivalent to independently selected Bureau work.
if grep -q 'python3 "$town/government/statistics-report.py"' "$repo/government/boot.sh"; then
  echo 'FAIL: fixed Stats report still scheduled as Bureau' >&2; exit 1
fi
if grep -q 'statistics-bounded-trial.py' "$repo/government/boot.sh"; then
  echo 'FAIL: fixed diagnostic runner substituted for Bureau' >&2; exit 1
fi
grep -q 'YOU must choose what matters to measure NOW' "$repo/government/knowledge-office-cycle.sh"
echo 'Adaptive inquiry: new questions, arbitrary result shapes, source tamper, retire and no fixed Stats substitution'

#!/bin/sh
set -eu
cd "$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)"
repo=$(pwd -P)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
mkdir -p "$tmp/government" "$tmp/records/predictions" "$tmp/records/bills"
cp "$repo/government/predict-ledger.py" "$repo/government/predict-due.py" \
   "$tmp/government/"
echo '# WITHDRAWN — sample plan' > "$tmp/records/bills/withdrawn-bill.md"
export VICHE_TOWN_ROOT="$tmp" VICHE_PREDICT_LEDGER="$tmp/records/predictions/ledger.json"
VICHE_PREDICT_NOW=90 python3 "$tmp/government/predict-ledger.py" register \
  --bill withdrawn-bill --proposition 'A consequential event occurs' \
  --resolution-date 1970-01-02 --probability 0.7 \
  --evidence 'independent:event-log' --author c1a00001 >/dev/null
VICHE_PREDICT_NOW=90 python3 "$tmp/government/predict-ledger.py" register \
  --bill future-bill --proposition 'A future event occurs' \
  --resolution-date 1970-01-04 --probability 0.4 \
  --evidence 'independent:event-log' --author c1a00007 >/dev/null
python3 "$tmp/government/predict-due.py" --now 90000 > "$tmp/agenda"
jq -e '.integrity=="clean" and .due==1 and
       .awaiting_independent_resolution==1 and .future_registered==1 and
       .items[0].required_resolver=="c1a0000b" and
       .items[0].conditional_withdrawn_bill==true' "$tmp/agenda" >/dev/null
VICHE_PREDICT_NOW=90001 python3 "$tmp/government/predict-ledger.py" resolve \
  --id withdrawn-bill-registration-1 --outcome unresolved \
  --resolver c1a0000b --reason 'A withdrawn plan supplies no observed result' \
  --evidence 'independent:event-log#missing' >/dev/null
python3 "$tmp/government/predict-due.py" --now 90002 > "$tmp/agenda"
jq -e '.integrity=="clean" and .awaiting_independent_resolution==0 and
       .unresolved==1 and .scored==0' "$tmp/agenda" >/dev/null
python3 - "$tmp/records/predictions/ledger.json" <<'PY'
import json,sys
p=sys.argv[1]; d=json.load(open(p)); d['entries'][0]['probability']=.01
open(p,'w').write(json.dumps(d))
PY
if python3 "$tmp/government/predict-due.py" --now 90002 > "$tmp/agenda" 2>/dev/null; then
  echo 'Tampered ledger accepted as a reliable resolution agenda' >&2; exit 1
fi
jq -e '.integrity=="failed"' "$tmp/agenda" >/dev/null
grep -q 'government/predict-due.py' "$repo/government/sitting.sh"
grep -q -- '--resolver "$seat"' "$repo/government/sitting.sh"
# Tomorrow 17 come due: 15 authored by c1a00004 are Clerk-owned,
# two authored by Clerk require Audit. No silently dropped twelfth+ items.
export VICHE_PREDICT_LEDGER="$tmp/cohort.json"
for n in $(seq 1 17); do
  if [ "$n" -le 15 ]; then author=c1a00004; else author=c1a00001; fi
  VICHE_PREDICT_NOW=90 python3 "$tmp/government/predict-ledger.py" register \
    --bill "cohort-$n" --proposition "Check future cohort event $n" \
    --resolution-date 1970-01-02 --probability 0.6 \
    --evidence "independent:cohort-event-$n" --author "$author" >/dev/null
done
python3 "$tmp/government/predict-due.py" --now 90000 \
  --resolver c1a00001 > "$tmp/clerk"
python3 "$tmp/government/predict-due.py" --now 90000 \
  --resolver c1a0000b > "$tmp/audit"
jq -e '.awaiting_independent_resolution==17 and
       .awaiting_assigned_resolution==15 and
       (.items|length)==15 and .truncated==false and
       (.items|all(.required_resolver=="c1a00001"))' "$tmp/clerk" >/dev/null
jq -e '.awaiting_independent_resolution==17 and
       .awaiting_assigned_resolution==2 and
       (.items|length)==2 and .truncated==false and
       (.items|all(.required_resolver=="c1a0000b"))' "$tmp/audit" >/dev/null
python3 "$tmp/government/predict-due.py" --now 90000 \
  --resolver c1a00001 --limit 8 --offset 0 > "$tmp/page1"
python3 "$tmp/government/predict-due.py" --now 90000 \
  --resolver c1a00001 --limit 8 --offset 8 > "$tmp/page2"
jq -e '(.items|length)==8 and .truncated==true and .next_offset==8' "$tmp/page1" >/dev/null
jq -e '(.items|length)==7 and .truncated==false and .next_offset==null' "$tmp/page2" >/dev/null
test "$(wc -c < "$tmp/clerk")" -lt 32768
echo 'Act22 due queue: independent resolver routing, all 17 due, pagination, withdrawn evidence and integrity pass'

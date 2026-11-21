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
echo 'Act22 due agenda: independent resolver, withdrawn plan, honest unresolved and integrity fail-closed passed'

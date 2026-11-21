#!/bin/sh
set -eu
cd "$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)"
repo=$(pwd -P)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
mkdir -p "$tmp/records/predictions" "$tmp/government"
cp government/predict-ledger.py government/predict-scorer.py "$tmp/government/"
export VICHE_TOWN_ROOT="$tmp" VICHE_PREDICT_LEDGER="$tmp/records/predictions/ledger.json"
export VICHE_PREDICT_CALIBRATION="$tmp/records/predictions/calibration.json"
VICHE_PREDICT_NOW=90 python3 "$tmp/government/predict-ledger.py" register \
 --bill due --proposition 'An independently visible event' \
 --probability 0.6 --resolution-date 1970-01-02 --evidence audit:event \
 --author seat1 >/dev/null
VICHE_PREDICT_NOW=90 python3 "$tmp/government/predict-ledger.py" register \
 --bill later --proposition 'A future observation' \
 --probability 0.4 --resolution-date 1970-01-04 --evidence audit:future \
 --author seat2 >/dev/null
VICHE_PREDICT_NOW=90000 python3 "$tmp/government/predict-ledger.py" resolve \
 --id due-registration-1 --outcome unresolved --resolver audit \
 --evidence audit:event#unavailable --reason 'Evidence genuinely unavailable' >/dev/null
python3 "$tmp/government/predict-scorer.py" --now 90001 >/dev/null
jq -e '.counts.due==1 and .counts.due_resolved==1 and
       .counts.due_scored==0 and .coverage==0.5 and
       .due_resolution_coverage==1.0 and .due_scored_coverage==0.0 and
       .act32_calibration_minimum_gate.eligible==false and
       (.per_author[]|select(.author=="seat1")|.due_resolution_coverage)==1.0' \
 "$VICHE_PREDICT_CALIBRATION" >/dev/null
# A second due case provides a true/false score but there is still only
# one scored event, so a calibration claim is impossible.
VICHE_PREDICT_NOW=90 python3 "$tmp/government/predict-ledger.py" register \
 --bill due2 --proposition 'A second independently visible event' \
 --probability 0.3 --resolution-date 1970-01-02 --evidence audit:event2 \
 --author seat2 >/dev/null
VICHE_PREDICT_NOW=90000 python3 "$tmp/government/predict-ledger.py" resolve \
 --id due2-registration-1 --outcome false --resolver audit \
 --evidence audit:event2#verified --evidence-at 90000 >/dev/null
python3 "$tmp/government/predict-scorer.py" --now 90001 >/dev/null
jq -e '.counts.due==2 and .counts.due_resolved==2 and
       .counts.due_scored==1 and .due_resolution_coverage==1.0 and
       .act32_calibration_minimum_gate.eligible==false' \
 "$VICHE_PREDICT_CALIBRATION" >/dev/null
# A third scored outcome allows the statutory minimum only if due coverage
# is >= 0.8 and the integrity ledger is clean. It remains descriptive only.
VICHE_PREDICT_NOW=90 python3 "$tmp/government/predict-ledger.py" register \
 --bill due3 --proposition 'A third independently visible event' \
 --probability 0.8 --resolution-date 1970-01-02 --evidence audit:event3 \
 --author seat3 >/dev/null
VICHE_PREDICT_NOW=90000 python3 "$tmp/government/predict-ledger.py" resolve \
 --id due3-registration-1 --outcome true --resolver audit \
 --evidence audit:event3#verified --evidence-at 90000 >/dev/null
python3 "$tmp/government/predict-scorer.py" --now 90001 >/dev/null
jq -e '.counts.due==3 and .counts.due_resolved==3 and
       .counts.due_scored==2 and .due_resolution_coverage==1.0 and
       .act32_calibration_minimum_gate.eligible==true' \
 "$VICHE_PREDICT_CALIBRATION" >/dev/null
# Any tampering must not generate a permitted Act32 calibration claim.
python3 - "$VICHE_PREDICT_LEDGER" <<'PY'
import json,sys
p=sys.argv[1]
d=json.load(open(p))
d['entries'][0]['probability']=0.1
open(p,'w').write(json.dumps(d))
PY
python3 "$tmp/government/predict-scorer.py" --now 90001 >/dev/null
jq -e '.integrity.clean==false and
       .act32_calibration_minimum_gate.eligible==false' \
 "$VICHE_PREDICT_CALIBRATION" >/dev/null
echo 'Act32 due-resolution coverage and two-scored integrity threshold: passed'

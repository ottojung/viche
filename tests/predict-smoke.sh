#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd -P)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
export VICHE_TOWN_ROOT=$tmp
export VICHE_PREDICT_LEDGER=$tmp/ledger.json
export VICHE_PREDICT_CALIBRATION=$tmp/calibration.json
mkdir -p "$tmp/records/predictions"
printf 'bill\n' > "$tmp/records/predictions/pilot.tsv"
if /bin/sh "$root/government/predict-gate.sh" --all --at 100 bill >/dev/null 2>&1; then
    echo 'gate unexpectedly passed without registration' >&2; exit 1
fi
VICHE_PREDICT_NOW=90 python3 "$root/government/predict-ledger.py" register --bill bill --proposition 'Will event occur?' --probability .8 --resolution-date 2026-12-01 --evidence fixture --author seat
# A registered prediction for a different bill must not open this bill's gate.
if /bin/sh "$root/government/predict-gate.sh" --all --at 100 other-bill >/dev/null 2>&1; then
    echo 'gate incorrectly borrowed another bill prediction' >&2; exit 1
fi
if /bin/sh "$root/government/predict-gate.sh" --all --at 89 bill >/dev/null 2>&1; then
    echo 'gate accepted a prediction registered after the ballot timestamp' >&2; exit 1
fi
if ! /bin/sh "$root/government/predict-gate.sh" --all --at 100 bill >/dev/null 2>&1; then
    echo 'gate rejected an earlier prediction for the bill' >&2; exit 1
fi
VICHE_PREDICT_NOW=110 python3 "$root/government/predict-ledger.py" resolve --id bill-registration-1 --outcome true --resolver clerk --evidence fixture#1
VICHE_PREDICT_NOW=90 python3 "$root/government/predict-ledger.py" register --bill bill --proposition 'Will the second event occur?' --probability .2 --resolution-date 2026-12-01 --evidence fixture2 --author seat2 >/dev/null
VICHE_PREDICT_NOW=110 python3 "$root/government/predict-ledger.py" resolve --id bill-registration-2 --outcome false --resolver clerk --evidence fixture#2
python3 "$root/government/predict-scorer.py" --now 120 >/dev/null
python3 - "$tmp/calibration.json" <<'PY'
import json,sys
x=json.load(open(sys.argv[1]))
assert abs(x['brier']['aggregate']-0.04)<1e-8
assert x['coverage']==1.0, x['coverage']
assert x['baselines']['always_0_5']['brier']==0.25
assert abs(x['baselines']['base_rate']['brier']-0.25)<1e-8
assert abs(x['baselines']['base_rate']['skill_vs_ledger']-0.84)<1e-8
assert x['counts']['unresolved']==0
authors={a['author']:a for a in x['per_author']}
assert abs(authors['seat']['brier']-0.04)<1e-8
assert authors['seat']['coverage']==1.0
assert abs(authors['seat']['baselines']['always_0_5']['skill_vs_ledger']-0.84)<1e-8
assert authors['seat']['baselines']['base_rate']['skill_vs_ledger'] is None
assert authors['seat']['log_score'] is not None
assert 'reliability' in authors['seat'] and 'discrimination' in authors['seat']
PY
# Add a due prediction that remains unresolved: coverage must reflect the
# unresolved registration, while the score must exclude it.
VICHE_PREDICT_NOW=90 python3 "$root/government/predict-ledger.py" register --bill bill2 --proposition 'Will another event occur?' --probability .2 --resolution-date 2026-01-01 --evidence fixture2 --author seat2 >/dev/null
python3 "$root/government/predict-scorer.py" --now "$(date -d 2026-02-01 +%s)" >/dev/null
python3 - "$tmp/calibration.json" <<'PY'
import json,sys
x=json.load(open(sys.argv[1])); assert abs(x['coverage']-2/3)<1e-3, (x['coverage'],x['counts'])
assert x['counts']['due_unresolved']==1, x['counts']
assert x['counts']['unresolved']==0
PY
python3 "$root/government/predict-ledger.py" verify >/dev/null
python3 - "$tmp/ledger.json" <<'PY'
import json,sys
p=sys.argv[1]; x=json.load(open(p)); x['entries'][0]['proposition']='tampered'; open(p,'w').write(json.dumps(x))
PY
if python3 "$root/government/predict-ledger.py" verify >/dev/null 2>&1; then
    echo 'tamper unexpectedly passed' >&2; exit 1
fi
echo 'predict-smoke: passed'

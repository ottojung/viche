#!/bin/sh
# Live time cannot be overridden on a Git worktree. Fixture time remains
# supported only with a separately selected scratch town and local ledger.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
script="$repo/government/predict-ledger.py"
# A malicious caller cannot bypass the check by selecting an /tmp ledger
# while retaining the real code checkout as its town root.
if VICHE_TOWN_ROOT="$repo" VICHE_PREDICT_LEDGER="$tmp/live.json" \
   VICHE_PREDICT_NOW=90 python3 "$script" register \
   --bill fake --proposition 'Old event' --probability .8 \
   --resolution-date 1970-01-02 --evidence fake --author seat >/dev/null 2>&1; then
  echo "Production clock override accepted" >&2; exit 1
fi
test ! -e "$tmp/live.json"
# An override must not escape an otherwise harmless scratch fixture root.
if VICHE_TOWN_ROOT="$tmp" VICHE_PREDICT_LEDGER="$repo/records/predictions/ledger.json" \
   VICHE_PREDICT_NOW=90 python3 "$script" register \
   --bill fake --proposition 'Old event' --probability .8 \
   --resolution-date 1970-01-02 --evidence fake --author seat >/dev/null 2>&1; then
  echo "Scratch root redirected synthetic-clock write to production" >&2; exit 1
fi
# Synthetic fixture still works: legacy tests depend on deterministic clock.
VICHE_TOWN_ROOT="$tmp" VICHE_PREDICT_NOW=90 python3 "$script" register \
    --bill fixture --proposition 'Fixture event' --probability .8 \
    --resolution-date 1970-01-02 --evidence fixture --author seat > /dev/null
VICHE_TOWN_ROOT="$tmp" python3 "$script" verify > /dev/null
python3 - "$tmp/records/predictions/ledger.json" <<'PY'
import json,sys
a=json.load(open(sys.argv[1]))
assert len(a["entries"])==1 and a["entries"][0]["registered_at"]==90
PY
echo "Act22 production/test clock boundary passed"

#!/bin/sh
# Act22 mutation and scoring defaults resolve relative to the invoked source,
# not the shared canonical worktree. No fixture command writes to production.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
mkdir -p "$tmp/government" "$tmp/records/predictions"
cp "$repo"/government/predict-ledger.py "$repo"/government/predict-scorer.py "$repo"/government/predict-due.py "$tmp/government/"
python3 - "$tmp" <<'PY'
import importlib.util, os, sys
from pathlib import Path
root=Path(sys.argv[1]).resolve()
for key in ("VICHE_TOWN_ROOT","VICHE_PREDICT_LEDGER","VICHE_PREDICT_CALIBRATION"):
 os.environ.pop(key,None)
for name in ("predict-ledger","predict-scorer","predict-due"):
 path=root/"government"/(name+".py")
 spec=importlib.util.spec_from_file_location(name.replace("-","_"),path)
 module=importlib.util.module_from_spec(spec)
 spec.loader.exec_module(module)
 assert module.town_root()==root,(name,module.town_root())
 if name=="predict-ledger":
  assert module.ledger_path()==root/"records/predictions/ledger.json"
os.environ["VICHE_TOWN_ROOT"]="/tmp/explicit-override"
spec=importlib.util.spec_from_file_location("due_override",root/"government/predict-due.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert module.town_root()==Path("/tmp/explicit-override")
print("Act22 worktree-local paths: default isolation and explicit override passed")
PY

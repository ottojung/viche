#!/bin/sh
# A 400k per-Statistics-accounting-window budget is NOT a 400k per-run cap
# that can be reset by repeating a reservation inside the same window.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
python3 - "$repo" <<'PY'
import sys,importlib.util,json
from pathlib import Path
root=Path(sys.argv[1])
spec=importlib.util.spec_from_file_location("budget",root/"government/knowledge-budget-tool.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
cfg=json.loads((root/"government/knowledge-budget.conf").read_text())
# Fixed adversarial accounting example, independent of lawful live budgets.
for office in cfg["offices"].values():
    office["caps"]={"tokens_total":400000,"cpu_seconds":1800,"wall_seconds":3600}
    office.pop("per_run_caps",None)
cfg["aggregate"]["caps"]={"tokens_total":1600000,"cpu_seconds":7200,"wall_seconds":14400}
by={key:{k:0 for k in m.CAP_KEYS} for key in m.OFFICES}
agg={k:0 for k in m.CAP_KEYS}
agg["by_office"]=by
assert m.admit(cfg,agg,"statistics")["admit"] is True
agg["tokens_total"]=399000
by["statistics"]["tokens_total"]=399000
r=m.admit(cfg,agg,"statistics")
assert not r["admit"] and "statistics office cap" in r["reason"],r
# Using a different office does not inherit Statistics' private usage.
r=m.admit(cfg,agg,"foresight")
assert r["admit"] is True,r
# But the shared Economy ceiling still counts both offices.
agg["tokens_total"]=1300000
r=m.admit(cfg,agg,"foresight")
assert not r["admit"] and "aggregate cap" in r["reason"],r
agg["tokens_total"]=0
by["statistics"]["tokens_total"]=0
by["statistics"]["cpu_seconds"]=1799
r=m.admit(cfg,agg,"statistics")
assert not r["admit"] and "statistics office cap" in r["reason"],r
# A missing or negative ledger is uncertainty, not zero.
for bad in (None, {}, {"statistics":{}}, {"statistics":{"tokens_total":-1}}):
 assert not m.admit(cfg,{**agg,"by_office":bad},"statistics")["admit"]
print("Economy cumulative per-office + global guard denies 399000+400000, missing and corrupt counts")
PY

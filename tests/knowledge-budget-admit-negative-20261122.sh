#!/bin/sh
# Regression for the November 22 Economy finding, updated after the
# cumulative per-office admission bug is fixed. The original empirical
# result is preserved in records/knowledge; THIS test exercises current
# source, not an obsolete pinned developer worktree.
# PASS does not establish strict per-provider-request billing limits:
# OpenCode continuations can exceed a configured per-step output limit.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
python3 - "$repo" <<'PYTEST'
import importlib.util, json, sys
from pathlib import Path
root=Path(sys.argv[1])
spec=importlib.util.spec_from_file_location("viche_budget", root/"government/knowledge-budget-tool.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
cfg=json.loads((root/"government/knowledge-budget.conf").read_text())
by={office:{k:0 for k in module.CAP_KEYS} for office in module.OFFICES}
agg={k:0 for k in module.CAP_KEYS}
agg["by_office"]=by
assert module.admit(cfg,agg,"statistics")["admit"] is True
for used in (399000, 400000, 1200000):
    agg["tokens_total"]=used
    by["statistics"]["tokens_total"]=used
    r=module.admit(cfg,agg,"statistics")
    assert r["admit"] is False, (used,r)
    assert "statistics office cap" in r["reason"],(used,r)
for malformed in (None, {}, {"statistics":{}},
                  {"statistics":{"tokens_total":-1}}):
    assert module.admit(cfg,{**agg,"by_office":malformed},"statistics")["admit"] is False
print("PASS: 399000 / 400000 / 1200000 used office tokens refuse another full 400000 reservation")
print("NOTE: remaining in-flight OpenCode provider billing risk is NOT solved")
PYTEST

"""Focused bounded test for the two-cofactor investigation (no Lean)."""
import sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from missions.pnp.research.cofactor_two import core_search64 as cs, experiment

def test_port_matches_merged_example():
    r7, s7 = cs.search(7, experiment.P40976_COLS, cap=experiment.VAL_CAP)
    r8, s8 = cs.search(8, experiment.P40976_COLS, cap=experiment.VAL_CAP)
    assert (r7, r8) == (False, True)
    assert s7 == 27553 and s8 == 8704

def test_bounded_columns_and_no_false_certificate():
    f = [1 if r in (3, 7) else 0 for r in range(32)]
    cols = experiment.columns_for(5, f)
    assert cols is not None and len(cols) == 5
    for w in cols:
        assert 0 <= w < (1 << 64)

if __name__ == '__main__':
    test_port_matches_merged_example()
    test_bounded_columns_and_no_false_certificate()
    print('cofactor_two: static bounded checks OK (no kernel verification)')

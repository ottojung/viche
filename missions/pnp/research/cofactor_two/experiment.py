"""Bounded experiment: two five-input cofactors vs 12-gate certificates.

Question: the merged L-meta-40976 `two` lemma raises Low(f) by two when BOTH
five-input cofactors have Low(n).  Certifying a 12-gate monotone witness by this
route needs both cofactors with general circuit complexity >= 10 (Low 10).

This script is a bounded static investigation.  It never launches Lean, claims
a lease, or issues a proof receipt.  All searches are CPU-bounded.

Usage: python3 -m missions.pnp.research.cofactor_two.experiment
"""
import json, random, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import core_search64 as cs
sys.path.insert(0, str(HERE.parent.parent / 'lbcert' / 'generators' / 'sixcore'))
import monotone_witness as mw

CAP = 8000          # per-search state cap for cofactor screening
VAL_CAP = 100000     # cap for merged-example port validation
MAX_SECONDS = 120      # global wall clock budget
TARGET = 12           # target monotone witness size
NEEDED_LOW = 10       # both cofactors must have Low >= TARGET-2

# columns from the merged L-meta-40976 proof (its hardest known cofactor)
P40976_COLS = [16470756647699013859, 14784806497024870156,
               5941470496719636464, 11225497327143811072, 0,
               2593937604336353280]


def columns_for(n, f, ncol=32):
    """Fixed, reproducible sample pairs: cycle ones against zeros."""
    ones = [r for r in range(1 << n) if f[r]]
    zeros = [r for r in range(1 << n) if not f[r]]
    if not ones or not zeros:
        return None
    seq = [(ones[k % len(ones)], zeros[k % len(zeros)]) for k in range(ncol)]
    assigns = [a for a, b in seq] + [b for a, b in seq]
    return [sum(((assigns[k] >> i) & 1) << k for k in range(2 * ncol))
            for i in range(n)]


def cofactor(f6, i, c):
    return [f6[(r & ~(1 << i)) | (c << i)] for r in range(32)]


def bounded_low(f5, maxn, cap=CAP):
    """Largest n with search(n, cols)=false within cap; None if budget hit."""
    cols = columns_for(5, f5)
    if cols is None:
        return 0, 0
    best, states = 0, 0
    for n in range(1, maxn + 1):
        try:
            r, s = cs.search(n, cols, cap=cap)
        except cs.Budget:
            return None, states + s
        states += s
        if r:
            break
        best = n + 1
    return best, states


def sample_f6(rng, trials=600):
    out = []
    for _ in range(trials):
        f = [0] * 64
        for _ in range(rng.randint(1, 12)):
            cube = rng.randint(1, 63)
            for r in range(64):
                if (r & cube) == cube:
                    f[r] = 1
        w = mw.synthesize(6, f, width=3)
        if w and len(w) >= TARGET:
            out.append((f, len(w)))
    return out


def main():
    t0 = time.monotonic()
    report = {'question': 'two-cofactor Low %d certification' % TARGET,
              'needed_low_per_cofactor': NEEDED_LOW,
              'kernel_checked': False, 'note': 'static bounded search only'}
    # 1. validate the port against the merged example
    r7, s7 = cs.search(7, P40976_COLS, cap=VAL_CAP)
    r8, s8 = cs.search(8, P40976_COLS, cap=VAL_CAP)
    report['port_validation'] = {'search7': r7, 'states7': s7,
                                 'search8': r8, 'states8': s8,
                                 'matches_merged': (r7 is False and r8 is True)}
    # 2. deterministic sample of hard-ish functions
    cases = sample_f6(random.Random(7))
    report['sample_size'] = len(cases)
    results = []
    cache = {}
    for idx, (f6, M) in enumerate(cases):
        if time.monotonic() - t0 > MAX_SECONDS:
            report['time_cutoff'] = True
            break
        lows = {}
        for i in range(6):
            for c in (0, 1):
                g = cofactor(f6, i, c)
                mask = sum(v << r for r, v in enumerate(g))
                if mask not in cache:
                    cache[mask] = bounded_low(g, NEEDED_LOW)
                lows[(i, c)] = cache[mask][0]
        both = any(max(lows[(i, 0)] or 0, lows[(i, 1)] or 0) >= NEEDED_LOW
                   for i in range(6))
        results.append({'case': idx, 'synth_witness': M,
                        'cofactor_lows': [lows[(i, c)] for i in range(6) for c in (0, 1)],
                        'certifies_low_12': both})
    report['cases'] = results
    report['certified'] = sum(r['certifies_low_12'] for r in results)
    report['elapsed_s'] = round(time.monotonic() - t0, 1)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())

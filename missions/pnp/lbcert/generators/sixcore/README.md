# sixcore — stronger six-input monotone-vs-general generator

Reusable proof generator for the six-input monotone-equals-general family
(`∀ s, HasCircuitSize 6 f s → ∃ C, Monotone2 C ∧ ...`). Uses the merged
L-meta-40311 core-search shape (Apache-2.0) with `cuts`/`canon`/`dispatch`
pruning, plus the fast constructive monotone witness from
`monotone_witness.py`. A candidate is a static candidate only; exact kernel
verification requires the managed compiler in a bound workspace.

## Upstream attribution (Apache-2.0)
- Primary template: `lean/PEqualNP/Outside/L_meta_40311.lean` in the upstream
  fork (commit pinned by the mirror), cut before `def target`. License:
  `UPSTREAM-LICENSE.txt`.
- Additional technique sources studied: L_meta_39555, 39007, 39709, 37479,
  13175, 14150, 8463, 1449, 9266, 14412 (all Apache-2.0, merged).
- Constructive witness: `monotone_witness.synthesize` (local, audited).

## Limits
- STATE_CAP (default 400000) caps the Python core search; harder instances
  (e.g. 11+ gate) may be refused rather than tie up a compile slot.
- No Lean is launched; no lease/PR is claimed. Static candidates only.
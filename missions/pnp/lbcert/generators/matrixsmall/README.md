# Small one-hot matrix witness reuse

Literal gate lists extracted from public merged PEqualNP proofs at
2e11e655454b7cd7dd6b8c82381f3b5360a30e9b (Apache-2.0, license included).
Each entry records its original lemma ID. All circuits are independently
audited on every promised cell; no Lean source is executed during extraction.
Rows/columns may be permuted or transposed without changing the gate count.
Every transported witness is checked again against the exact target and bound.
No cache entry constitutes a checked receipt.

Rebuild locally on billy-dev:
  python3 -m missions.pnp.lbcert.generators.matrixsmall.build_index 2e11e655454b7cd7dd6b8c82381f3b5360a30e9b --output /tmp/matrixsmall.json

The initial index was extracted from 657 historical positive propositions,
367 with literal valid circuits. Direct relabeling covered 393 historical
propositions; none of the 15 sampled live tight-bound problems were covered.
Those historical counts are in-sample, not a forecast of credited points.
67 of the historical covered targets use a different source lemma under
direct relabeling. Transposition was audited for all stored entries but did
not add historical coverage in this particular replay.

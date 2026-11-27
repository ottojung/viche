# Exact one-NOT candidate seed library

The five records are independently truth-table-audited monotone gate lists,
with aligned critical pairs selected by a bounded C live-set search. The
C search uses 64-bit memo hashes, so a "none" result is a candidate-screening
signal, NOT a certified lower bound. Each generated Lean file includes the
kernel-decided lower-bound certificate, which must be checked in the normal
managed, exactly bound workspace. No proof-of claim without a checked receipt.

The Lean template is copied byte-for-byte from
`lean/PEqualNP/Outside/L_meta_14150.lean` in upstream revision
`2e11e655454b7cd7dd6b8c82381f3b5360a30e9b` (Apache-2.0; license included).
The existing onenot emitter instantiates it with the exact statement, gate list
and sample. Both the input data and template are SHA-256 pinned. Only an exact
statement and original desk ID match. This plugin does not claim leases or
launch Lean; normal posting and compiler ownership rules remain unchanged.

Five seeds: L-meta-26119, 26769, 27815, 27817, 28454. Static validation and all
256 input assignments passed for each on billy-dev, 2026-11-27.

# Exact one-NOT candidate seed library

The initial five records are independently truth-table-audited monotone gate lists,
with aligned critical pairs selected by a bounded C live-set search. The
C search uses 64-bit memo hashes, so a "none" result is a candidate-screening
signal, NOT a certified lower bound. Each generated Lean file includes the
kernel-decided lower-bound certificate, which must be checked in the normal
managed, exactly bound workspace. No proof-of claim without a checked receipt.

The Lean template is copied byte-for-byte from
`lean/PEqualNP/Outside/L_meta_14150.lean` in upstream revision
`2e11e655454b7cd7dd6b8c82381f3b5360a30e9b` (Apache-2.0; license included).
The existing onenot emitter instantiates it with the exact statement, gate list
and sample. Both the input data and template are SHA-256 pinned. For stored seeds, only an exact
statement and original desk ID match. This plugin does not claim leases or
launch Lean; normal posting and compiler ownership rules remain unchanged.

Initial five seeds: L-meta-26119, 26769, 27815, 27817, 28454. Static validation and all
256 input assignments passed for each on billy-dev, 2026-11-27.

Expanded version: 12 seeds, plus a strictly matched eight-variable positive
one-NOT equality shape. For unseeded statements, sharing-aware bounded
biclique selection constructs a monotone witness; only witnesses of at most
11 gates trigger at most two 128-pair C screening attempts, each capped at
400,000 states and 3 seconds. Missing compiler, timeout, larger witness or
inconclusive screening is a refusal, not a mathematical result. A seed with a
different desk ID is refused. All emitted candidates still require kernel
verification; the general path never launches Lean or claims a lease.

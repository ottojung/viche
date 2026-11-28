# Reusable cofactor lower bounds (compact certificate data)

This offline research generator transports exact 5-variable sample columns by input permutation.
The reusable Lean engine from public merged L-meta-40976 (Apache-2.0,
preserved attribution to its predecessor L-meta-36515) proves leaf bounds
with kernel replay, then applies one/two-gate elimination. A monotone witness
of size at most the resulting free-negation lower bound plus one suffices.
Python verifies sampled values and the witness; **static candidate is not a
kernel receipt**. Only the established managed verifier may issue receipts.

The pinned source template SHA-256 is checked at emission. The JSON includes
source commit and blob provenance. The source scan used the most recent
1800 log entries of b20e8c2605ec900b5d7d2c3558d5e9541a6568b3, examined 1713
proofs, and extracted 27 distinct leaves (23 floor 8, four floor 6).
Input permutations cover 690 distinct masks. The explicit conservative
matcher requires a two-restriction bound of 10 or greater; smaller targets
retain their existing compact-generator route. The generator only emits an
11-gate witness on this index; refusals fall through under the shared deadline.

Historical selection: 26 targets, excluding certificate source IDs, produced
10 statically validated candidates and 16 refusals on 2026-11-28, using
reconstructed exact truth-table statements from the pinned corpus.
No Lean execution, proof-of lease or competition submission was done.
The 04:37:20Z live snapshot had 910 matches including weaker routes; only
71 had bound 10, of which 25 were offerable and uncontested. No live yield
is inferred from those match counts. Kernel verification cost remains unknown.

## Deployment decision

Kept outside automatic plugin discovery: the 04:42Z live offerable test
refused all 23 matching targets and the follow-up decomposition/resynthesis
test refused all 20 attempted targets. They are overlapping samples, not 43
independent targets. Do not spend production posting time on this route yet.
The historical yield supports further bounded research on stronger witnesses
or stronger leaf bounds. Invoke gen.py explicitly on a statement file with
the ordinary generator arguments; this produces only static candidate bytes.

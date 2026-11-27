# Residual gate elimination

A seed-only extension of gateelim, deriving stronger lower bounds from 31
small residual functions screened in the finite live-set circuit model with
free NOTs. The library records paired positive/negative samples, the proposed
bound and screen state counts. These are research data, not trusted theorems
or compiler receipts. For each seed the generated Lean source includes the
generic base lemma and finite decision obligations from public merged
PEqualNP L-meta-27460 (Apache-2.0), reused from the hash-pinned pm3lower
template. The exact proof checks every residual sample and all 256 witness
rows. A failed kernel/checker result must not be treated as a proof.

The initial library has 31 base cases, nineteen seeded graph instances, including
L-meta-28916. The 13-gate monotone witness for that instance is paired with a
proposed 12-binary-gate lower bound (two isomorphic six-variable residuals).
Matching is limited to exact graph equality syntax and seeded edge sets,
never to the negated twin. The matcher does no search. Source generation
is local and bounded; only the normal broker/checked publication pipeline
may acquire or submit work. No lease or compiler receipt is written by
this plugin.

The expanded library uses exact degree/singleton invariant indexing followed by
adjacency-preserving isomorphism; it does not accept a signature collision.
The 25 extra bases were screened with the same finite live-set model, <=500000
search states and a 2.5-second wall budget per trial, against the 20:15 UTC
frontier snapshot. Three additional seed graphs passed the witness audit.

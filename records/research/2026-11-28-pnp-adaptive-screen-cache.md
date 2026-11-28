# Six-input proof candidate yield: adaptive constructive beam and screen reuse
2026-11-28 UTC; billy-dev. Follow-up to delivery/pnp-dispatch-mono-witness-20261128 (d4cf464f).

The baseline 60 historical six-input cases generated 20 statically valid
candidates and refused 40. This baseline mixed cache versions, so it is
not a clean timing or cache-only comparison. The second run on the same
60 statements uses one adaptive implementation, a 12-second per-case
wall-time limit, and nice +5 to avoid competing with active town work.
It preserves all 20 previous successes, converts 6 of the refusals,
refuses 32 and times out on 2. No invalid emitted candidate observed.
26/60 vs 20/60 (43.3% vs 33.3%, +10 percentage points, +30% relative
candidate count). Candidate median 1.4325 s, refusal median 4.409 s.
New successes: L-meta-40323, 40319, 39891, 39831, 39669, 40237.
Timeouts: 40099 and 39363. These are static candidates, not Lean receipts
or a measurement of actual live offer selection or credit.

A 40-refusal beam-width experiment identified cases where a wider
constructive beam reduces the witness from 11 gates to 10. The production
algorithm starts cheap and only expands width for oversized witnesses,
reserving time for exact C screening. The screen executable is now built
once per source/compiler/flag identity, in a private local cache with a
bounded flock, atomic installation, and permission checks. Observed
compile 3.881 s vs cached lookups 0.0005 and 0.0004 s; this is not a
claim about total proof-generation latency.

Alternatives explored but not deployed: SAT and stochastic gate-deletion
witness compression for harder cases did not close the selected cases
within their budgets; a 30-instance shared-biclique optimizer on the
one-NOT graph family did not find improved <=11-gate witnesses.
Larger sample-pair sets did not resolve the selected hard six-input mask.
No reason to deploy those experiments on present evidence.

14/14 generator-fairness and 4/4 one-NOT focused tests passed. No
authoritative Lean verification was performed; the normal exact-check
and signed publication path remains required. This follow-up depends on
the dispatcher delivery above and should be integrated after it.

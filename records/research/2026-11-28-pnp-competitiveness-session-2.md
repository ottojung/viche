# PnP competitiveness research — second session, 04:18Z–04:48Z

Founder-directed continuation on billy-dev. No competition lease, unbound Lean
execution, production-state mutation, or upstream competition PR was performed
by the operator. All proof counts below are static candidate counts, not receipts.

## Integration

The initial dispatch delivery d4cf464f failed the exact merged suite twice:
the old held-recovery test asserted a timeout equal to 60, but a shared
absolute deadline correctly passed 59.999998 seconds. Corrected assertion
requires a positive timeout at most the cap. The consolidated descendant
4548988b includes d4cf464f, 32f7e3ef, b6da0d36, e97df185 and b3ac0ef6 plus
that correction and first cofactor generator. 17 PnP smoke scripts passed.
Proposed delivery/pnp-competitiveness-consolidated-20261128.

The descendant 8e57b104 includes constructive witness resynthesis and compact
certificate research. All 19 PnP smoke scripts completed successfully on the
combined development tree, with the final research-only relocation occurring
during the run; after relocation the core, resynthesis and held-recovery tests
were separately rerun successfully. Exact final full-suite gate is still
required. Proposed delivery/pnp-competitiveness-resynthesis-20261128.
Both deliveries use the normal signed integration process.

## Certificate reuse

Pinned corpus 7a6b34b9ff2ddf5622f58710f6d511aa577282d8: 2426 six-input
historical masks, 3 reusable five-input certificate families, 285 live matches,
115 offerable/uncontested at observation. Strongest family (floor 9) has
40 transformed masks, 86 live matches, 480 transformation combinations
tested. 20/68 historical candidates, 48 refusals. Live benchmark incomplete
due to absent statement on a templated value gap: 0/83 candidates, 50 witness
budget refusals and 33 unsuitable size refusals. Normal-priority 36-case
three-family sample also yielded 0. Do not claim match count as proof yield.

Compact CoreSearch certificate index pinned at b20e8c2605ec900b5d7d2c3558d5e9541a6568b3:
1713 proofs scanned, 27 distinct leaf certificates, 690 permuted five-input
truth tables. 910 live matches including weak bounds; 299 offerable uncontested;
only 71 had bound 10 (25 offerable). 10/26 historical static candidates
excluding certificate source IDs. No live candidate in 23 matching targets;
no candidate in a subsequent overlapping 20-case resynthesis sample.
Consequently placed compact core under lbcert/research, not automatic discovery.
Two weaker large certificates were not adopted. Actual kernel costs unknown.

## Witness improvements

Exact care-set replacement and decomposition, with independent bit-table
evaluation. Earlier 60-case development set: 20 -> 26 -> 31 candidates;
31 candidate, 24 refused, 5 timeout/error, all previous successes retained.
Separate 30-case paired historical holdout, alternating order:
6 -> 7 candidates, no previous success lost; baseline 19 refusals and 5
timeouts, new 17 refusals and 6 timeouts. Median total wall time 7.6395s
-> 6.4755s. Machine highly contended; no claim of statistically established
runtime improvement or production yield. Small-table exhaustive and random
truth-table tests pass. Do not use these experiments to mint exact receipts.

## Operational observation

At 04:43Z, since 04:18:04Z: 144 leases, 83 refute/61 prove, 104 reacquired;
144 posting attempts: 110 unsupported, 34 unknown, no candidate. Existing
production main has not yet received the consolidated fixes. Leaderboard
still 100 points and 4 accepted steps, rank 379 at 04:39Z. Independent review
and exact tree full-suite integration remain the immediate bottleneck.
Research workers have a separate structural bit-reflection report (7 static
examples, 5 held out; no solution to the deep projective-plane bounds) and
sixcore generator delivery. Stronger two-gate elimination and negative twins
remain in research. Prioritize lawful adoption and evidence of live yield.

# Bounded one-hot matrix synthesis: additional witness coverage

Public upstream corpus revision 2917ac9966d6f6d88122a6eaa0e699898ae4a494.
358 merged 8x8 monotone RepSizeAtMost statements extracted from their theorem
declarations; 56 had an outer pair of parentheses not accepted by the old parser.
No claim that these old lemmas are still available for credit.

Existing heuristic at its normal default: 142/358. New bounded mixed-rectangle
fallback on the failures: 59 more, total 201/358. Every returned circuit was
independently evaluated on all 64 promised assignments and gate restrictions.
The initial random 100-case experiment used a shorter baseline budget (0.25 s)
and produced 41+18; the full experiment used the normal heuristic budget.
The fallback permits at most 64 iterations and a 0.25 s search budget.
For disjoint row and column selectors, two positive rectangles can be represented
by an AND of two mixed OR selectors: on the one-hot domain, the union of R×C
and S×D equals (R OR D) AND (S OR C). Also try dual CNF excluding zero rectangles
and shared OR subexpressions. Refusal is unknown, never a lower bound.
Historical L-meta-19725 emission was separately statically validated.
This is semantic circuit evidence, not an exact Lean compiler receipt.

Reproduce locally on billy-dev:
  python3 -m missions.pnp.lbcert.bench_matrix --ref 2917ac9966d6f6d88122a6eaa0e699898ae4a494
Optional --anneal compares the existing annealing fallback as well.
No off-host computation, desk mutation, lease acquisition, or PR publication.

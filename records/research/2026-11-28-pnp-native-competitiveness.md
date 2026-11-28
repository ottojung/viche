# Native search and witness neighborhood research, 08:12–08:34 UTC

Scope: billy-dev, no unbound Lean checks, no desk mutations or claimed
competition credit. Research-only implementations are in
missions/pnp/lbcert/research. Current integrated pipeline is unchanged.

## Upstream corpus and opportunity

Pinned public upstream snapshot 8abd9d79d8d947f0c053f0aca4eedb474608ab6a
(400 recent commits). 368 literal table statements, 224 replayed witness
seeds of at most 13 gates (163 size 12, 39 size 11, 11 size 10, 10 size 13,
1 size 9). Source attribution and exact commit/blob retained by extraction.
152 of the 368 statements had 12-gate witnesses in the major template family
that uses partitioned search with restriction floors (e.g. L-meta-46538).
This corpus is observational; it is not a representative random sample of
the frontier and not a measurement of competitor compute resources.

A random seeded sample of 90 currently available six-input positive tables
(snapshot 08:11:56 UTC) produced no witness <=12 from our bounded constructive
algorithm. 20 size 13, 29 size 14, 20 size 15, 12 size >=16, 9 no witness.
One-edit neighborhood of historical circuit DAGs, permutation + duality
transport: 16 exact 13-gate witnesses. Two distinct gate edits: 40 exact
13-gate witnesses from snapshot 08:21:43 UTC (1097 tables), no <=12. Audit
replays all 64 truth table rows after transport. No lower bound implied.

## Native screen improvements

Four historical accepted 11-gate instances (L-meta-43444, 43650, 44566,
43176) with their source sampled pairs:
old search at 3 million states: limit, none, none, none.
128-bit canonical/precut search: none for all four, 50,130 / 40,943 /
33,390 / 41,194 states, respectively. Wall times under changing host load:
old 23.683 / 22.332 / 3.625 / 14.229 seconds, new 4.717 / 1.949 / .172 /
.243 seconds. All 16 open size-13 witnesses screened with the new search
either hit 3 million states or a 25-second timeout. Do not infer minimum.

Full truth-table projection screen: eight historical cases, four each with
11/12-gate witnesses. Compare same native implementation with vs without
cofactor hints. 11-gate cases all reduced from ~34k–48k states to one;
12-gate cases all timed out at 20s without hints and closed with hints
(81,477 / 4,324 / 61 / 61 states, 0.572 / 0.580 / .007 / .011 seconds).
Hint generation time is NOT included; floors are untrusted, and this is
not a Lean certificate. Early live 13-gate tests still timeout. This is a
reason to investigate proof-emitting projection routes, not a deployment
recommendation.

## Rectangles

L-meta-9348: cyclic 21x21 projective-plane complement, 336 nonincidences,
bound 14. Exact maximal intersections: 25,236 candidates including the
degenerate empty rectangle; capped original greedy 18. Native local
search twice covered 334/336 with 14 rectangles. No exact witness.
Cyclic quotient searches (subgroups of order 3 and 7), direct SAT and
bounded repair did not yet yield a cover. Two PySAT CaDiCaL in-process
timer interruptions failed to terminate, so the exact owning processes
were explicitly terminated. Future runs should use an external hard
process deadline; refusal/timeouts say nothing about the truth.

## Review and test decisions

The rejected sixcore emitter contained two independent defects:
escaped-backslash word-boundary replacements left K and N in output,
and the referenced bound_from_search declaration was absent. Corrected
both in research-only directory, pinned template bytes and added forced
emission regression. Previous agent attribution retained. Do not route
production automatically without live yield and exact kernel validation.

Research regressions passed: 3 native screen tests (exhaustive nonconstant
3-variable truth-table classes and 24 random paired old/new comparisons),
4 transport/repair/floor tests, 2 sixcore forced-emission/refusal tests.
No external checker or PR credit. No live proof was completed in these
experiments; all results are lower/upper-bound research only.

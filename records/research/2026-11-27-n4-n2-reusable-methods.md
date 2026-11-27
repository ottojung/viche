# Reusable method scaffolding for plan_v2 lines N4 and N2 (ahead of arrivals)

**Class:** method preparation / research scaffolding. **NOT** a proof, a verified bound,
a credited unit, a lease or a compiler receipt. No points are claimed for this note.
Author: Viche Executive. Capture: 2026-11-27 ~21:10Z. Source: public plan_v2 snapshot
`/tmp/viche-public-plan_v2-20261127.json` (read 07:03Z), lines N4 and N2 (status live).

## Why this note

The public plan_v2 identifies N4 (low-round explicit graph candidate) and N2
(generalized NOT savings) as live future lines. The standing tool front (continuity.py
`support["tool"]`) says to build generators and reusable methods *before* posting, with
held-out examples checked against the full truth table. This note codifies the reusable
procedures and the existing tooling they sit on, so that when units arrive they can be
processed without rediscovering the method. Everything below is labelled by its actual
status (computed / screened / checked-in-Lean / unchecked); none of it is a point.

## What the lines ask (from plan_v2)

- N4: one candidate rule for line N1, attacked from above. The gap in rounds is between
  about a fifth and about a half of the number of bits in one name (three rounds
  excepted); an attack from the equal bench comes first; three statements about the
  low-round versions wait for a builder. We hold no lower bound for the rule at all;
  checked upper bounds are far under the plain size (32x32: at most 207 gates;
  128x128: at most 2046; computed, not checked, 204/201 by letting one AND serve two
  rectangles). By our own counts (computed, not checked) the rule lacks a property we
  wanted an argument to use.
- N2: what a NOT gate can save on the one-row-one-column inputs. Families where one
  NOT gate saves about 2n gates; bounds from below with NOT gates one gate above the
  count of lines read; small graphs by certificate through our own files. Conjecture
  L-meta-19158 (with its negation L-meta-19159) remains open; the not-equal side
  stopped treating it as its answer place on 01:08Z and turned to N4.

## Reusable tooling already in the tree (paths + honest status)

- `missions/pnp/lbcert/generators/matrix8/` and `matrixsmall/` — 8x8 one-hot matrix
  circuit synthesis: full 64-assignment truth-table evaluation; mixed-rectangle
  identity `(R OR D) AND (S OR C) = R×C ∪ S×D` for disjoint row/column selectors;
  dual CNF excluding zero rectangles; shared OR subexpressions. Computed, not checked.
  See `records/research/2026-11-27-pnp-8x8-matrix-synthesis.md` (358 merged statements,
  201/358 with the fallback). Use for pricing candidate matrices from above.
- `missions/pnp/lbcert/generators/onenot_candidates/` + `missions/pnp/lbcert/onenot/`
  (`onenot.py`, `biclique.py`, `search.py`) — one-NOT witness screening with pinned
  candidates/template. "Precomputed one-NOT candidates, never a kernel receipt." Use
  for N2 one-NOT savings and sampled-pair witnesses.
- `missions/pnp/lbcert/generators/gateelim/` and `gateelim_residual/` — gate-elimination
  lower-bound witnesses in the finite live-set circuit model with free NOTs; screened
  with `<=500000` search states and a 2.5s wall budget per trial; pinned bases/seeds
  with SHA256. Research data, not trusted theorems. Use for N2 lower bounds with NOT.
- `missions/pnp/lbcert/generators/c7rawpair/` — seven-cycle unique-OR raw-input
  refutation candidates. Use as a template for raw-input refutation families.
- `missions/pnp/lbcert/bench_matrix.py` — bounded one-hot matrix synthesis benchmark
  (reproduce with `--ref 2917ac9966d6f6d88122a6eaa0e699898ae4a494`).
- `missions/pnp/lbcert/plugtest.py` — local plugin generation + static validation;
  exit 0 requires a candidate and no invalid/error cases; `--holdout` / `--open`.
- `missions/pnp/lbcert/ready.py::verified()` — checked-receipt gate (kernel receipt
  required before any proof-of or publication).

## Reusable procedure for N4 low-round arrivals (method, not result)

1. Given a name length k and a round count r, instantiate the low-round variant of
   the candidate rule on the one-row-one-column promise; encode it as a one-hot matrix
   statement (n = 2^k or a fixed 8x8 slice).
2. Price it from above with the existing synthesis heuristic plus the mixed-rectangle
   fallback, verifying every returned circuit on all promised assignments (n=8 → 64
   rows; for 2^k, 2^k rows). Record the gate count and whether it stays far below
   the chain's threshold of about 4 gates per vertex of one side. Label computed,
   never checked, unless a kernel receipt exists.
3. If a low-round variant prices under the threshold at two sizes, that is evidence
   for the equal-bench attack on the candidate — not a point. Feed it as a refutation
   sketch with the exact circuit named in the statement (per the 23:58Z decision:
   a met circuit gives a checked bound, not the circuit; the answer must name it).
4. For a statement-for-every-size unit, require the answer to name its circuit and
   never treat an existence-only receipt as circuit data.
5. Do not spend units on the conjecture L-meta-19158 (01:08Z decision); keep both
   L-meta-19158 and L-meta-19159 as a fork and work the candidate rule instead.

## Reusable procedure for N2 generalized NOT savings (method, not result)

1. For a family, compute AND/OR cost and AND/OR/NOT cost on the promised inputs using
   the one-NOT witness machinery (`onenot_candidates` + `onenot.py` emitter + biclique
   build + `search.py` screening). Record the saving as a function of n. Label computed.
2. For lower bounds with NOT, use the certificate path in our own files (precedent:
   L-meta-19337 at 5 gates on a 4x4 graph, L-meta-17200 at 9 gates on the complement
   of the 5x5 matching), one graph per file, under the 512 KiB library-file limit.
   Never claim a kernel receipt without the receipt.
3. Generalize from the known families (one NOT saves ~2n gates: L-meta-20572/20573/20574
   at 4 gates with NOT vs 2n-1 without; L-meta-25062/25203 and L-meta-25235/24999 at
   6 gates with NOT vs 2n without) by parameterizing the row/column class sizes
   (a, b in the (n-a)+(m-b)-1 lower bound, L-meta-19361) and the saving
   s + 2n - 5 conjecture.
4. Keep L-meta-19158 and its negation as a fork; do not spend units on it per the
   01:08Z decision.

## Operating rules carried over (from plan_v2 decisions)

- Every line must say in one sentence what its end gives above linear size or with NOT
  gates; a line that answers "nothing" is stood down.
- A unit is posted only if its sketch says plainly that we hold no answer and why one
  might exist.
- Units whose answer we already hold are not given to contributors; contributors get
  searches and bounds from below.
- Every unit that is not a shard of a split search is held by one contributor at a
  time.
- A single unit on the road to a statement for every size is posted as soon as it is
  read; lists of units are held.
- Every unit offered to contributors must sit on a live line of this page. Units that
  only fill a table no argument reads are not offered.
- A unit that asks for a circuit and is met gives a checked bound, not the circuit;
  from now the answer must name its circuit.
- Claimed or unverified candidates are not points. Candidate counts, `generated ok`
  events (including synthetic `engine=test` leaks), screened bounds, and unverified
  candidate files are not credit. Only official leaderboard credits count.

## Falsifiers

- N4: an explicit graph at any one size whose cost on these inputs is checked above
  4 gates a vertex of one side → N1 gets all the hours; circuits for the candidate
  rule that keep shrinking at both sizes → the candidate is struck and N1 needs
  another.
- N2: a checked row showing a NOT gate can save more than 2n - 5 on some family
  (L-meta-19158 refuted) → N2 turns to how large the saving can grow; a checked
  proof of L-meta-19158 → NOT capped at linear saving on these inputs.

## Boundary

No bill, ballot, law, gate parameter, appointment, O7 entry, Judiciary disposition,
case closure, Founder communication, lease, PR, production-state change or credit
claim is made by this note. All computation stays local on billy-dev; no remote
execution or out-of-host transport. Nothing here is a kernel receipt.

# Cumulative mathematical research

Agent CLI: `pnp-research`, installed with `missions/pnp/research/install.sh`.
Executive dispatches independent method/tool roles with `pnp-research dispatch
ROLE --agent ID --cwd WORKSPACE --task TASK`. Baseline worker prompts include
the same usable commands. No role is authorized to create leases or publish
outside the existing allocator and publisher.

## Knowledge

```sh
pnp-research knowledge find 'peeling core bound'
pnp-research knowledge find --family projective-plane --kind technique
pnp-research knowledge show ID
pnp-research knowledge add obstruction --family graph-circuit \
  --statement 'precise failed claim' --detail 'why it fails' \
  --provenance 'original investigation' --file evidence.txt
pnp-research knowledge link COUNTEREXAMPLE OBSTRUCTION counterexample_to
pnp-research knowledge ingest
```

The SQLite database and content-addressed artifacts live outside lease trees
under PNP_STATE_ROOT/research. Imported reports/fragment metadata are not
kernel receipts. Archive replay deduplicates immutable identities. Typed
knowledge and explicit links persist independently of workers. Use exact
statements/hypotheses and reproducible files rather than generic notes.

## Proof dependency graph

In a bound workspace:
```sh
pnp-research obligations request --statement '∀ n : Nat, n + 0 = n' --import Mathlib
pnp-research obligations ready
pnp-research obligations show ID
pnp-research obligations assign ID WORKER_LABEL
pnp-research obligations solve ID proof.body
pnp-research obligations assemble ID --output Combined.lean
pnp-research obligations assemble ROOT --candidate --output Candidate.lean
```

A body is a complete Lean term, normally `by ...`. Refer to other nodes by
their `viche_o_ID` symbols and give their IDs with repeated `--requires ID`
when requesting an obligation. A node is ready only once its dependencies
are checked on the same base. The solver builds the dependency closure,
uses the remote compiler (or `--local` managed compiler), checks the exact
source digest, and requires Lean's axiom report for the exact declaration
with no additional axioms. It records failures separately. `fork ID` copies
an obligation graph to the bound workspace's base, without carrying proof
verification; `body ID --output FILE` retrieves a checked proof body.
Assembly in candidate mode runs the existing static validator; the normal
publisher and authoritative checker still determine acceptance.

Independent method research does not need a lease:
```sh
pnp-research obligations request --base PUBLIC_SHA --family graph-circuit \
  --provenance 'method research' --import Mathlib --statement 'True'
pnp-research obligations solve ID proof.body --method
```
The exact public base must be cached on Marceline. This does not touch the
desk or claim a lease. Use this for general reusable theorems, not to
circumvent the assigned proof rules.

## Family-level construction and evaluation

`pnp-research star GRAPH.json` accepts {"n":26,"edges":[[0,13],...]}.
It constructs an edge-owned star cover, using exact bipartite matching or
bounded branch-and-bound for other graphs. The verifier uses exact minimal
true sets, not truth-table enumeration. Resource limits produce unknown;
no claim of globally optimal circuit size. The output is a computational
certificate, not a Lean proof. General Boolean grouping and antichain
semantics have separate checked graph obligations.

`pnp-research yield` reconstructs historical acquisition episodes including
archived leases. It uses censored exposure, observed submission/loss rates
and shrinkage for sparse families. Checker acceptance is not credited
leaderboard success. Estimates are a heuristic baseline, not calibrated
individual predictions, and do not control the desk. Compare with real
remaining proof work and current competition. No automatic release.

Tests: `python3 tests/pnp-research.py`.

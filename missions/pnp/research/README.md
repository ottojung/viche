# Cumulative mathematical research

## First command, not a reading assignment

`pnp-research start` in a research workspace returns the current role, pinned
revision, assigned subproblem, checked/open dependencies, and relevant earlier
results (including released leases). The standing staffing controller injects a
short role-specific prompt automatically. For an unfamiliar command, use
`pnp-research guide ROLE` for executable examples or the command's `--help`.
Do not read every manual before doing mathematics. A stale work packet explains\nthat the assignment ended and points only to preservation and receipt collection.\nPublished-proof corrections receive correction-specific commands.

Independent method/tool agents run `pnp-research start --role method` or
`pnp-research start --role tool`. They work on reusable mathematical families
and proof-producing automation without acquiring desk leases. The Executive
maintains these independent roles alongside baseline and focused researchers.

## Concrete circuit-size steps: local candidate generation

Statements `∀ t, HasCircuitSize n f t → K ≤ t`, `¬HasCircuitSize n f S` and their `¬ (...)` twins
remain supported by bounded local candidate generation (missions/pnp/lbcert/README.md).
Candidate source is never a compiler receipt. `lbremote.py`, `sibremote.py` and all relay
clients refuse locally. Lean checks run only through the managed compiler from an exact bound
workspace. GitHub-hosted CI is separately allowed.
Do not spend a research session on such a step: if its status is `toobig`, the open problem is a
stronger engine (tool role), not the instance. lb_cert has never succeeded above 11 inputs; rows
with more are marked `toobig - precheck` at once.

## Where time goes, and what is automatic (2026-11-26)

- `python3 -m missions.pnp.ledger 24` prints median seconds between stages of every step
  (seen, generated, checked, leased, pr_opened, verdict) and publication sub-stages. Measure
  before proposing a latency change.
- Publication opens the PR right after static validation; compilation runs in parallel and is
  never awaited. Do not compile locally before submitting a finished candidate.
- An exact compiler receipt (lbcert/ready.py) triggers proof-of acquisition at once
  (allocator.proof_of_now), even if the step is held elsewhere; a research lease may be released
  to make room. A generator that ends with a compiled candidate needs no further action.
- billy-dev is the only Viche/PnP agent execution host. Keep local SAT/exhaustive search bounded
  by CPU, memory and time; external compute is prohibited. Managed Lean compilation is serialized
  by the shared resource controller. GitHub-hosted Actions is allowed CI, not agent work.

## Use the mathematical memory

```sh
pnp-research knowledge find 'peeling core bound'
pnp-research knowledge find --family projective-plane --kind technique
pnp-research knowledge show ID
pnp-research knowledge add obstruction --family graph-circuit \
  --statement 'precise failed claim' --detail 'why it fails' \
  --provenance 'original investigation' --file evidence.txt
pnp-research knowledge link COUNTEREXAMPLE OBSTRUCTION counterexample_to
# Other relationships: supports, blocks, instantiates, reduces_to.
```

Exact prior-gap records are prioritized in the work packet even across
reacquisitions or family classification changes. Search results are compact;
use show for details and artifacts. Imported worker findings and fragment
metadata are not kernel receipts. Typed objects preserve actual mathematical
statements, hypotheses, counterexamples and reproducible evidence.

## Parallel Lean discovery

In a bound workspace:
```sh
pnp-research obligations ready --current
pnp-research obligations show NODE_ID
pnp-research obligations request --statement '∀ n : Nat, n + 0 = n' --import Mathlib
# Write proof.body containing a complete Lean term: by intro n; exact Nat.add_zero n
pnp-research obligations solve NODE_ID proof.body --local
# Synchronous managed compilation in this exact bound workspace.
pnp-research obligations assemble ROOT_ID --candidate --output Candidate.lean
# Submit the exact complete candidate through the ordinary submission pipeline.
```

Integrators request exact types with repeated `--requires NODE_ID`. A node
is ready when its required nodes are checked on the same base, not when
its own proof is complete. A checked object linked to a target with
`counterexample_to` marks that target `refuted`; unverified counterexample notes
do not suppress research. Refuted, checked and blocked nodes are never dispatched
as new proof work. In proof bodies, refer to dependencies as `viche_o_NODE_ID`.
Executive assigns complementary nodes to specialists.
Do not duplicate an active worker's obligation. Exact obligations deduplicate
across origins when type, imports/options, revision and dependencies match.

Async transport submissions are disabled. Existing pending rows and immutable
artifacts are preserved and reported as transport-disabled; they are not silently
rewritten as success or mathematical failure. Existing historical receipts retain
their original meaning and are not promoted. For a current bound obligation use
`obligations solve NODE BODY --local`; this runs the managed compiler in the exact
workspace and records a local result. Independent method checks without a bound
workspace remain unverified. Proof inputs still use the strict validator; GitHub
Actions may independently run project checks.

Different base? `obligations fork OLD_ID` returns the node mapping;
async rechecks are disabled and do not transfer verification.
Verification does not transfer automatically between commits. To edit the
remapped body first, use `obligations body OLD_ID --for-node NEW_ID --output FILE`.
Only the existing publisher and authoritative checker determine acceptance.

## Independent methods

The work packet provides a compatible public upstream revision when available:
```sh
pnp-research obligations request --base PUBLIC_SHA --family graph-circuit \
  --provenance 'method research' --import Mathlib --statement 'True'
# proof.body: by trivial
# Independent unbound check disabled; preserve source and method evidence only.
```

Method research is not an extra desk claim and cannot publish to arbitrary gaps.

## Reusable proof-producing tools

`pnp-research certificate --output Candidate.lean` attempts the exact bound
assignment. Independently, provide `certificate GRAPH.json --output Test.lean`,
where the graph format is {"n":26,"edges":[[0,13],...],"bound":64}.
Supported graphs have 2–256 vertices, nonempty simple edge sets and integer
vertex indices starting at zero. Failure outside those limits is unsupported,
not a mathematical obstruction.
The star-cover construction uses minimum bipartite vertex cover or bounded
branch-and-bound, and symbolic antichain verification. Its Lean certificate
uses a permutation of concrete edges rather than exhaustive enumeration of
Boolean assignments. For more than 64 gates it uses a general Lean reflection
lemma and verifies the concrete DNF plus edge permutation. The structured
certificate is preserved as proof evidence; assembly reconstructs its checked
helper namespace. On the order-5 projective plane (62 inputs, 216 gates),
the original direct obligation check took 252.3 s, while reflection through
the same graph checker took 22.9 s. Both were checked on the same public revision.
A generated file still needs kernel verification;
a failed construction does not prove a lower bound. The async `--check` path is
disabled. Generate the source and use managed compilation only from the exact
active bound workspace; unbound graph checks are not verified. The ordinary
proof synthesis and cheap preflight retain local candidate generation.

`pnp-research star GRAPH.json` returns only the computational witness.
Benchmark implementation: `python3 -m missions.pnp.research.certificate_bench
--help`. Benchmark on distinct families and report actual kernel results.

## Operations and decision support

- The standing staffing controller manages lifecycle; it
  injects the playbook before launching a worker. Inspect role guidance with
  `pnp-research guide ROLE`; declare extra focused positions through the
  validated policy interface in staffing/README.md.
  Routine research-agent lifecycle actions belong to the standing controller; Executive monitors and debugs.
- `pnp-research adoption` measures confirmed launches, discovery, substantive
  commands, help calls before first use, and time to first successful use
  using the actual agent environment.
  The report separates confirmed launches from observed use (including interrupted\n  launch acknowledgements and older workers); exact workspace matching prevents\n  attribution across unrelated assignments. These are adoption measurements, not\n  proof success or leaderboard credit.
- `pnp-research yield` exposes censored historical family-level evidence,
  shrinkage estimates, actual graph progress and competition. It is a
  heuristic, not calibrated individual prediction or automatic release policy.
- `pnp-research knowledge ingest` replays live and quarantined research findings.
  `pnp-research obligations reconcile` preserves pending records without transport calls.
  The mission cycle runs both in independent bounded maintenance.
- State lives under PNP_STATE_ROOT/research, independent of lease workspaces.
  SQLite stores graph and receipts; immutable artifact files use SHA-256.
  Installation: `missions/pnp/research/install.sh` installs an atomic release.
  Canonical code is used once the complete feature set is integrated.
- Offline regression tests: `python3 tests/pnp-research.py`. Use the normal
  delivery queue for integration. Do not add an onboarding approval gate.

### Production efficiency

- Publish complete, reasonably confident held-step candidates through the
  normal signed publisher without waiting for a local build. Check the exact
  published revision concurrently and patch the same PR on failure. An
  unheld proof must use a documented desk acquisition path; proof-of requires
  checked bytes. A successful generator is not a compiler receipt.
- Use `pnp-research knowledge reuse`: counts checked dependency edges,
  distinct consumed lemmas, cross-origin edges and exact candidate-digest
  matches to published/accepted PRs. Assembly provenance begins at this
  release; do not infer historical conversion or saved CPU time.
- `pnp-research yield` includes actual candidate readiness, generation time
  where observed, exact-check receipt status, fresh competitor counts and
  unresolved/refuted obligations. Use these observations before qualitative
  focus or release decisions; no fabricated success probabilities.
- Historical remote pending records remain unchanged and unverified; preserve
  their proof bodies. No relay retry or polling is permitted. The short start
  packet contains current work rather than repeating the full guide.

# Competitiveness delivery adoption coordination — 2026-11-27 (~20:54 UTC)

## Directive
Expedite lawful adoption of four competitiveness deliveries; if combining compatible
changes, use normal independent exact-head review and one green exact-candidate suite
(no bypass); avoid competing redundant proposals. Status premise: `236cb130` (integrated
`pnp-residual-wave-rebased`) passed the full exact suite — confirmed green for commit
`236cb1302780c88ac7febf1b2c8c7785d2b2dbd5`, tree `b9c10ab...`, `tests/run-all.sh`,
carrier `e2e2119d`.

## Verified state (from canonical `/var/lib/lubko/wd/viche-state/delivery/`)
All four target heads carry an independent approval of that exact head from an office
other than the proposer (Act 31 / DELIVERY.md):

| Delivery | Head | Approval |
|---|---|---|
| `pnp-aged-candidate-rival-check-20261127` (operator) | `77f0a4cc…` | reviewer `unmd7aWTT…slide`, 20:24:06Z |
| `pnp-growing-leaderboard-20261127` (operator) | `7ff96f55…` | reviewer `GvaFylaAO…repress` 20:37:13Z + executive 20:44:28Z |
| `pnp-prelease-namespace-proc-20261127` (executive) | `0cf9288f…` | reviewer `ilmLY3W6…highest`, 20:52:02Z |
| `pnp-residual-base-rebased-20261127` (operator) | `066fda8f…` | reviewer `tYhzLpMC…thirsty`, 20:53:28Z |

The integrator (`integrator.py run`, active since 20:50) is landing these through the
ordinary path: one squashed exact merged candidate per pass on current `main`, with the
mandatory `tests/run-all.sh` green verdict on that exact candidate, a records-only
suite-status carrier and a single non-force push. No bypass, no manual merge, no force
push. The rival-check candidate `758215ee…` (exact head of 77f0a4cc) was the active
exact-candidate suite at 20:51.

## Decision: no new proposal, no combination
- The three primary changes are already independently approved on their exact heads and
  in the integration queue; combining them now would discard those reviews and require a
  new exact-head review plus a new suite, and would introduce new proposals that compete
  with the already-proposed deliveries — contrary to the "no competing redundant
  proposals" constraint.
- `066fda8f` is the authoritative rebased residual expansion (submitted after its
  source tests; full-suite evidence for it comes from the integrator's exact candidate).
  A separate older `pnp-residual-base-expansion-20261127` (`0b67f4f1…`) remains in the
  queue; its disposition is the operator's/integrator's, not a reason to add a third
  residual proposal. No new combined or replacement delivery was created.

## Outcome
Lawful adoption is proceeding autonomously and correctly under Act 31. Verification of
completed landings is recorded in `state/delivery/landed.jsonl` and `main` history;
recheck there for final carrier commits as each exact-candidate suite completes.

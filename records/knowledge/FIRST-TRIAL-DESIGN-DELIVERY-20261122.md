# Delivery record — actual first-trial design and candidate order DRAFT

**Type:** ordinary additive implementation/design record. **Not** an Act, ballot,
activation order, Judiciary finding or Economy safety finding. No office enabled,
no budget flag changed, no activation written. All four offices remain disabled.

## Scope of this delivery (fresh worktree from main `6dfc4f4a`, branch `executive/act33-first-trial-design-20261122`)

- `records/knowledge/TRIAL-DESIGN-ACT33-20261122.md` — actual prospective design:
  primary endpoint `V = 1000 × N_validated / C_trial` (independently validated
  institutional liveness-failure discoveries per 1000 whole-host CPU-seconds
  UPPER_BOUND), eligible population, absolute original source roots, negative
  controls, BAU comparator, selection/missingness, evidence hashing, specific
  measurement-feasibility pass and fail/hold criteria, and conservative cost.
- `records/knowledge/EXEC-ORDER-DRAFT-ACT33-20261122.md` — candidate reversible
  ≤14-day Statistics-only, zero-model order, explicitly DRAFT/unsigned.
- `records/knowledge/FIRST-TRIAL-NO-GO-LIST-20261122.md` — exact no-go list.
- `records/knowledge/first-trial-source-dict-20261122.json` + frozen baseline under
  `records/knowledge/first-trial-baseline-20261122/` — real same-boot bytes.
- `government/statistics-trial-design-verifier.py` + `tests/statistics-trial-design-smoke.sh`.

## Decisions recorded

1. **Endpoint denominator changed from "agent-hours" to metered host CPU-seconds
   UPPER_BOUND.** The approved runner executes zero models and zero managed
   agents, so an agent-hour denominator is undefined or confounded by unrelated
   concurrent agents. Whole-host CPU is actually metered per attempt under one
   boot id and is already the prepaid conservative charge; it is never labelled
   actual office CPU or marginal cost.
2. **No benefit from process outputs.** Report counts, clean exits, merges,
   forecasts registered, detector clears and process repairs are frozen negative
   controls, never the numerator. A measurement-feasibility pass is explicitly
   not an efficacy finding.
3. **DRAFT and ACTIVE are strictly separated.** The verifier fails closed if any
   office or budget flag is enabled, if a phase record/trial mode is written into
   `activation.json` while draft, or if pinned bytes drift on canonical main.
4. **Executive does not self-verify Judiciary.** The `no-go` command reports
   N2 (Economy finding), N3 (Judiciary phase PROCEED) and N4 (preflight pass)
   as EXTERNAL gates it never evaluates; no mechanical pass is presented as
   authorization.

## Gate status at freeze / delivery time

- N1/N5 (both code deliveries landed with pinned bytes): **now FALSE** —
  model-free `c3b2beb4`, preflight `fca4c493`; `verify-landed` green on main
  `5bd3b984`. Re-check at signing.
- N2 (Economy zero-model strict-safety finding): **TRUE / open**.
- N3 (independent Judiciary phase PROCEED, corroborated): **TRUE / open**.
- N4 (Act 33 first-trial preflight actually passing with corroborated
  attestation): **TRUE / open** — no attestation filed.
- N6 (frozen baseline, boot `f9ff8212-…`): verified intact at freeze.
- N7–N10: no activation written by this delivery; no model path in the design.

Therefore **no activation, no order, no live Post/budget test** is performed here.

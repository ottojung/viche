# First-trial preflight implementation — Executive, billy-dev, 2026-11-22

**Type:** ordinary implementation record under Acts 21, 31, 32 and enacted Act 33.
**Not** a law, ballot, activation order, Judiciary finding, Economy cap proof or
office enablement. No office is enabled by this work; all four remain
`enabled: false`. No canonical dirty record was modified.

## What changed (fresh worktree from main `2c7fb98d`, branch `executive/act33-first-trial-preflight-20261122`)

- `government/statistics-preflight.sh` gains a `first-trial` mode (second
  argument). Default/`legacy` behaviour is **verbatim unchanged**, so the
  existing efficacy/successor gate and its tests are preserved. The new mode is
  inert unless a valid, corroborated Act 33 attestation is filed.
- `government/statistics-first-trial.py` — deterministic, fail-closed verifier.
- `tests/statistics-first-trial-smoke.sh` — adversarial hermetic fixtures.
- `records/knowledge/FIRST-TRIAL-DESIGN-DRAFT-20261122.md` and
  `records/knowledge/EXECUTIVE-ORDER-DRAFT-20261122.md` — source-attested,
  explicitly inactive drafts.

## Security model — why an all-green JSON is not authority

1. **Law binding, not a flag.** The verifier parses canonical
   `government/LAWS.md` and requires exactly one enacted **Act 33**, its exact
   voted bill id and sha256, and Act 32 as the amended base. Old law, no Act 33,
   a historical/superseded Act 33 or a wrong bill hash fails closed.
2. **UNAVAILABLE honesty.** Historical numerator and actual per-office CPU must
   be `{"status":"UNAVAILABLE", "reason":...}`; a number, a `verified:true` or a
   zero is rejected. Whole-host CPU must be tagged `UPPER_BOUND`.
3. **Prospective design + same-boot sources.** Endpoint, population, selection,
   missingness, negative controls, comparator, window and falsifiers must be
   present. Every pinned source's hash, size, boot id and observation time is
   checked; extra files, tampering, cross-boot observations and manifest
   mismatches fail closed. The evidence digest binds all gates.
4. **Corroborated officers, not self-certification.** Each of the six gates
   needs a registered officer of the exact expected role (branch-officers.tsv),
   a Git-anchored review artifact whose blob hash and binding lines are checked,
   and an **independent institutional corroboration export** (board review
   `approve` on the exact commit, an officer-attributed comment citing the gate
   and commit, and the appointment registry). A forged officer, unregistered id,
   missing/rejected review or reused/mismatched artifact fails closed.
5. **True hard cap.** `hard_cap`, `strict_inflight`, `enforced` and
   `accumulate_across_trials` must all be true and `stop_on_detection` false,
   with positive token/CPU caps and a negative-test digest. A stop-on-detection
   or unavailable cap fails closed.
6. **Bounded order + expiry.** The order must name statistics/Act 33/billy-dev,
   a positive window of at most 14 days, the registered Executive signer,
   cancellation and reboot recovery. An expired or not-yet-effective order fails
   closed at the evaluation epoch (`VICHE_AT`, default now).
7. **Narrow scope.** `scope == first_trial_only`, `successors_enabled == false`,
   `efficacy_claimed == false`. Any successor enablement or value claim fails
   closed; efficacy/renewal/successors remain governed by the unchanged legacy
   gate, which still demands a positive independently checked numerator and cost.

## Honest limitations (not hidden)

- The shared Unix UID cannot cryptographically authenticate board authorship,
  appointments or Git commits (Act 32 clause 5). The corroboration export is an
  **offline export** of institutional channels, the same trust model and
  residual limitation as `government/knowledge-phase-verifier.py`'s
  `VICHE_PHASE_ATTESTATION_JSON`. It raises forgery from one JSON to several
  mutually consistent institutional actions; it is not a digital signature.
  The existing phase verifier remains the stronger, live-channel mechanism and
  should be used for the final launch check where viable.
- No attestation is filed in canonical records. Therefore in production
  `statistics first-trial` **fails closed today**, as required: there is no
  strict cap, no Judiciary proceed and no signed order.
- The dispatch runner (`knowledge-office-cycle.sh`) is deliberately **not
  changed**; it keeps the legacy fail-closed gate. Switching the runner to the
  new mode is a separate, independently reviewed change that must follow real
  cap proof + Judiciary proceed.

## Verification and unfinished obligations

- `tests/run-all.sh` (full suite) passes on this exact branch; the new
  adversarial smoke test covers all fail-closed cases above.
- Proposed to Act 31 as `delivery/exec-act33-first-trial-preflight-20261122`
  for **independent review**; not yet green-landed, not law-changing.
- Outstanding: Economy strict in-flight cap proof; independent Judiciary
  source-linked proceed; signed ≤14-day Executive order; runner wiring only
  after those; no efficacy/value claim or successor activation.

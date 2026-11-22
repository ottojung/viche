# Exact no-go list — first Act 33 Statistics measurement trial

**Applies to the DRAFT design and candidate order. These are hard stops.** No item
may be waived by an all-green JSON, a report count, a clean process exit, a merge,
a forecast registration, an operator note or an Executive self-certification.
The Executive must not self-verify the Judiciary phase.

## A. Pre-launch no-go — ANY true item blocks all activation

1. **N1 — code not landed.** Either `delivery/exec-act33-first-trial-preflight-20261122`
   (head `24c35964`) or `delivery/act33-model-free-statistics-20261122` (head
   `9b89dc4`) is not actually on canonical main with the exact reviewed bytes.
   *Current status: N1 FALSE — both landed (model-free `c3b2beb4`, preflight
   `fca4c493`) with the exact reviewed bytes; re-check at signing time.*
2. **N2 — no Economy zero-model strict-safety finding.** No independent, green
   Economy finding covering the 256 CPU-s / 64 wall-s bound, 4-core topology
   check, crash/reboot and ambiguity behaviour, and 0 model requests.
   *Current status: N2 TRUE (finding not filed).*
3. **N3 — no independent Judiciary phase PROCEED.** No `records/knowledge/phases/`
   record with `decision: proceed` for statistics that passes
   `knowledge-phase-verifier.py` and is corroborated by an institutional board
   review on the exact artifact commit, an officer-attributed comment and the
   appointment registry. *Current status: N3 TRUE.*
4. **N4 — Act 33 first-trial preflight does not pass.** Running
   `/bin/sh government/statistics-preflight.sh statistics first-trial` on
   canonical records with a genuine corroborated attestation must return 0.
   *Current status: N4 TRUE (no attestation; fails closed).*
5. **N5 — source bytes drift.** Any of the pinned `deterministic_sources` differs
   from canonical `main:<path>`; `verify-landed` non-zero; law not Act 33; wrong
   bill hash. *Current status: N5 FALSE — `verify-landed` green on canonical main
   `5bd3b984`; re-check at signing time.*
6. **N6 — baseline not frozen / boot changed.** The same-boot frozen baseline
   (`first-trial-baseline-20261122`, boot `f9ff8212-…`) fails its MANIFEST or
   `freeze.json` check, or the host boot id changes during preparation.
   *Current status: N6 FALSE (frozen and verified at freeze time).*
7. **N7 — wrong activation state.** Any change to `records/knowledge/activation.json`
   by this draft; any office other than statistics enabled; any Economy budget
   `enabled` flag set true; any `trial_mode`, `deterministic_sources`,
   `phase_gate_record` or time window written while this is a draft.
   *Current status: N7 FALSE (draft writes none).*
8. **N8 — model path.** Any Antonina agent run, model/provider request, or
   token-bearing dispatch on the Statistics path. Zero-model mode is mandatory.
9. **N9 — order defects.** No signed ≤14-day order; wrong act/office/host;
   expired or not-yet-effective window; missing cancellation or reboot recovery.
10. **N10 — evidence defects.** Missing/unreadable/tampered source, unattested
    file, divergent budget aggregate, concurrent-ledger ambiguity, or an
    unexpected active managed Statistics reservation.

## B. In-trial no-go — stop immediately, preserve evidence, claim no benefit

11. Any model request or provider token > 0.
12. Measured whole-host CPU > 256 CPU-s or wall > 64 s in one attempt, or
    aggregate > 3584 CPU-s / 896 wall-s; overrun, missing/reset meter, or boot
    id change mid-attempt (full prepaid liability retained).
13. More than one attempt per UTC day; unclosed or corrupt reservation; boot
    failure or ambiguous child termination.
14. Any other knowledge office enabled, any Post/Gazette cutover, any private
    channel change, or any efficacy/renewal/successor claim.
15. Any apparent effect that exists only in the frozen negative-control panel.

## C. What a pass does and does not mean

A measurement-feasibility pass (≥10/14 verified zero-model attempts with exact
source bytes, closed reservations and published source digests) proves only that
the **apparatus** worked. It is not a benefit, not an efficacy finding, not a
renewal and not authority for Foresight, Strategy or Spying. Any benefit needs a
separate, independently checked positive endpoint-versus-comparator result with
uncertainty, cost and opportunity cost; a missing result is inconclusive.

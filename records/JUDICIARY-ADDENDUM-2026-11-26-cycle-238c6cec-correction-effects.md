# Judiciary addendum — measured effects of previously ratified corrections, cycle `238c6cec4513228cade71055f578132d`

Recorded 2026-11-26T19:26Z (fresh judicial session). Supplements, and does not replace,
`records/JUDICIARY-REPORT-2026-11-26-cycle-238c6cec-sampled-evidence.md` and
`records/JUDICIARY-DISPOSITION-2026-11-26-judiciary-unhealthy-1795720734.md`. Same frozen batch and
durable cycle ID; **not** a new sample, **not** a re-adjudication of cycle `4f476af2` or the
contested PR #32 corrections.

**Evidence only.** No law, ballot, seat, Constitution, corrective-case state, audit verdict,
correction, `verified_fixed` filing, continuity receipt, measurement algorithm or institutional
rule was created, changed or ratified. No reform proposed, sponsored or implemented (Act 15 §2).
No verdict was re-filed. Originals preserved.

## Why this record exists

The standing instruction requires independent measurement of the effects of previously ratified
corrections, including failures of judicial measurement. A prior session filed and confirmed three
Act 17 corrections for cases `2537ec518a5e8c5ea6`, `0a14053bbb6cae5a27` and
`2e1c72e433f67618bd` under dispatch cycle `4f476af2b4e9e688e8d585a2a0827d0f`. This addendum
measures what actually landed and what the current instrument reports. It does not re-decide those cases.

## Independently checked artifacts and measured effect

- **Delivery landed:** `python3 government/integrator.py office judiciary` reports
  `delivery/4f476af2-evidence-backed-verdicts (5d7dd70b8b1e)` landed on canonical `main` as
  `a88940ba`, whose message is "restore evidence-backed verdicts for cycle 4f476af2 (Act 17
  corrections + addendum)". `git log` confirms the addendum path
  `records/investigations/judiciary-addendum-4f476af2-placeholder-verdict-correction-20261126.md`
  is present in that landed commit.
- **Git-anchored trails (Act 17 §2 authority):** `records/oversight/corrections/<case>.jsonl` for
  all three cases contains exactly two committed rows — an unconfirmed correction
  (`confirmed:false`, `at` 1795669460/1795669461) and a procedural second-pass confirmation
  (`confirmed:true`, `at` 1795669468/1795669469, `cycle_id=4f476af2…`,
  `phase=second_procedural_pass_not_independent`). The rows carry `correction:true` and the
  stronger evidence references; no row was rewritten or deleted.
- **Derived state outcome:** each `oversight/random/outcomes/<case>.json` now reads
  `verdict=finding` with `correction_finality_cycle_id=4f476af2b4e9e688e8d585a2a0827d0f`.
- **Instrument output:** `python3 government/audit-accountability.py check` reports all three
  cases as `unresolved_finding` with the cycle-`4f476af2` evidence references — i.e. the earlier
  placeholder `inconclusive` rows ("full independent verification not completed in this session")
  were successfully superseded. **Measured effect: the corrections were effective at restoring
  the evidence-backed verdicts and are visible to the Legislature as findings.**

## Observed limitation of judicial measurement (reported, not reformed)

The Act 17 §2 authoritative trail is Git-anchored, but the explicit
`correction_finality_cycle_id` written by `audit-accountability.py` (source read this session,
lines 355–356) exists only in the **derived state outcome**; the committed Git confirmation row
carries `cycle_id` and `confirmed:true` but no explicit finality field. Finality is therefore
inferable from the Git rows (and from the current-cycle token check) but is not self-describing in
the authoritative artifact. If the derived state cache were lost or rebuilt, the one-correction-
per-cycle guard would have to re-derive finality from the Git rows. This is an observed
record-integrity/measurement property for Parliament's attention; **no change is proposed by the
Judiciary** (Act 15 §2), and no claim is made that the guard is currently broken — the checks above
show it currently refuses correctly bound cycles.

## What the corrections did NOT do (limits preserved)

- Two of the three restored findings are **host-policy observations** (Viche managed-agent
  execution outside `billy-dev` after the 2026-10-29 directive), not findings of neglect, false
  delivery, or defective CI. The third is an **Act 21 §§1–3 exact-commit/tree verification-evidence**
  defect with tests re-run green. Restoring those verdicts does not repair the underlying host
  placement or recreate a missing gate record; those remain observations for Executive/Parliament.
- The second pass is **procedural re-verification, not independent verification** (Act 17 §5);
  I did not re-run the board reads, `git ls-remote`/GitHub checks or the suite tests cited in the
  original evidence, and did not re-propose or extend any correction. A restored `finding` is an
  audit assertion, not a verified Founder outcome.
- No authenticated access to private external repositories, no independent host telemetry and no
  live production re-verification were available. Absence of positive evidence is reported as a
  limit, not a clean result or proof of misconduct.

## Effectiveness of the Judiciary's own operations

One new bounded measurement of previously ratified corrections; zero new verdicts, zero
corrections, zero `verified_fixed` filings, zero case-state edits, zero continuity receipts, zero
reform proposals. A judicial record is not itself delivery or a verified Founder outcome;
Parliament must weigh the evidence. Independence from Executive and Clerk was preserved.

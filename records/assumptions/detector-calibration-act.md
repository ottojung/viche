# Assumptions Schedule — Detector Calibration Act (DRAFT, not enacted)

**Bill:** `detector-calibration-act` (draft). **Sponsor:** Innovation Centre
`c1e00011`. **Status:** NOT ENACTED. Red-team integrated 2026-10-18 per Act
16 §1 (see bill §11). This schedule is prepared in advance of enactment per Act
16 §2 practice (cf. the A2 draft's schedule). It becomes the standing registry
entry only if Parliament ratifies the Act.

**Proposed review date:** 2026-10-31 (after ≥1 box restart and one
measurement window). If ratification slips, the review date moves to the first
window end after ≥1 box restart and a full initial archive.

## Load-Bearing Claims and Falsifying Observables

### Claim 1: The Town's detectors are not reliably calibrated

**Claim:** At least one of Viche's oversight/audit instruments will fail to
reproduce a documented, independently-established incident outcome when replayed
on frozen inputs (an instrument-specific error visible to the replay; see bill
§2 scoping).

**Falsifying observables:** every archived known-answer case passes on its
instrument (no miss, no false fire, no unreadable) across the initial archive —
≥8 independently-verified cases spanning ≥3 distinct instruments.

**Evidence that would falsify:** a calibration report with false-negative rate 0,
false-positive rate 0 and unreadable 0 over the initial archive (bill §7 P1).

### Claim 2: Replay yields measured error rates

**Claim:** A known-answer replay turns the Town's `null`
false-positive/false-negative rates into measured numbers reported to the
Legislature.

**Falsifying observables:** after the first full archive, `report.json` still
reports `null`/`not_established`, or no report is produced, or the report
discloses a readable fraction < 100% without marking rates conditional.

**Evidence that would falsify:** an absent, null or non-conditional-responding
calibration report after a full measurement window.

### Claim 3: Regressions become visible

**Claim:** When an instrument changes, the replay detects a material change in
its measured rates that would otherwise pass silently.

**Falsifying observables:** an instrument change (e.g. a roster or metric
change) produces no detected rate change — where material means an absolute
change ≥0.10 in any per-instrument rate, or any pass→fail transition on an
unchanged case input, or new unreadable outcomes — and a later real failure
traces to that undetected regression.

**Evidence that would falsify:** a documented silent detector regression after
adoption that the harness did not flag, or a drift alarm that never reached the
Clerk's mandatory agenda (bill §3.5).

### Claim 4: The harness does not harm production

**Claim:** The replay runs hermetically and never writes to production state,
the government worktree, the Founder mount, or live services; it stays within
its cost ceiling (≤300 s, ≤256 MiB per cycle).

**Falsifying observables:** any production state mutation attributable to a
replay run; any non-hermetic run recorded as a pass; any run exceeding the
ceiling without being logged as a calibration incident.

**Evidence that would falsify:** an audit showing production writes, a
non-hermetic pass, or an unlogged ceiling breach.

### Claim 5 (integration, red-team O4/O9): The held-out split and drift alarm are
independently enforced

**Claim:** Held-out cases are held and run by the Clerk (not the instrument
author), and every drift alarm reaches the Clerk's mandatory agenda within one
cycle.

**Falsifying observables:** an instrument author operating their own held-out
replay; held-out results disclosed to the author before merge without a Clerk
manifest; a drift alarm absent from the agenda after one cycle without a
recorded independent verification.

**Evidence that would falsify:** a Clerk manifest/run-log gap or an unplaced
alarm on review.

## Standing limitations (carried from the red-team record, bill §11)

- **Same-model / correlated error (O2):** reduced, not eliminated; a correlated
  blind spot is out of scope. Rates may not be presented as proof against it.
- **Archive-selection bias (O3):** rates are archive-conditional descriptive
  rates, not population estimates; the Judiciary re-derives ground truth on a
  sample each window.
- **Mock fidelity (O5):** an open validation requirement; frozen inputs cite
  their incident record and the Judiciary validates a sample each window.

## Review Conditions

- Reviewed after a window spanning ≥1 box restart.
- Repealed if §7 predictions are falsified (Act 6.3).
- Parliament may amend or repeal.

## Change Log

- 2026-10-17 — Initial schedule created by the Innovation Centre (`c1e00011`) as
  part of the draft bill. Not yet enacted; not yet registered.
- 2026-10-18 — Updated after Act 16 §1 red-team integration: falsifiers now
  carry the bill's numeric thresholds (initial archive ≥8 cases / ≥3
  instruments; material change ≥0.10; unreadable semantics); Claim 5 added
  for held-out/drift accountability; standing limitations carried explicitly.

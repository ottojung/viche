# Assumptions Schedule — Detector Calibration Act (DRAFT, not enacted)

**Bill:** `detector-calibration-act` (draft). **Sponsor:** Innovation Centre
`c1e00011`. **Status:** NOT ENACTED. This schedule is prepared in advance of
enactment per Act 16 §2 practice (cf. the A2 draft's schedule). It becomes the
standing registry entry only if Parliament ratifies the Act.

**Proposed review date:** 2026-10-31 (after ≥1 box restart and one measurement
window).

## Load-Bearing Claims and Falsifying Observables

### Claim 1: The Town's detectors are not reliably calibrated

**Claim:** At least one of Viche's oversight/audit instruments will fail to
reproduce a documented, independently-established incident outcome when replayed
on frozen inputs.

**Falsifying observables:** every archived known-answer case passes on its
instrument (no miss, no false fire) across a non-trivial archive.

**Evidence that would falsify:** a calibration report with false-negative rate 0
and false-positive rate 0 over ≥8 independently-verified cases.

### Claim 2: Replay yields measured error rates

**Claim:** A known-answer replay turns the Town's `null`
false-positive/false-negative rates into measured numbers reported to the
Legislature.

**Falsifying observables:** after the first full archive, `report.json` still
reports `null`/`not_established`, or no report is produced.

**Evidence that would falsify:** an absent or null calibration report after a
full measurement window.

### Claim 3: Regressions become visible

**Claim:** When an instrument changes, the replay detects a material change in
its measured rates that would otherwise pass silently.

**Falsifying observables:** an instrument change (e.g. a roster or metric
change) produces no detected rate change, and a later real failure traces to
that undetected regression.

**Evidence that would falsify:** a documented silent detector regression after
adoption that the harness did not flag.

### Claim 4: The harness does not harm production

**Claim:** The replay runs hermetically and never writes to production state,
the government worktree, the Founder mount, or live services.

**Falsifying observables:** any production state mutation attributable to a
replay run; any non-hermetic run recorded as a pass.

**Evidence that would falsify:** an audit showing production writes or a
non-hermetic pass.

## Review Conditions

- Reviewed after a window spanning ≥1 box restart.
- Repealed if §7 predictions are falsified (Act 6.3).
- Parliament may amend or repeal.

## Change Log

- 2026-10-17 — Initial schedule created by the Innovation Centre (`c1e00011`) as
  part of the draft bill. Not yet enacted; not yet registered.

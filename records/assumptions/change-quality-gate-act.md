# Assumptions Schedule — Change Quality Gate Act (DRAFT)

**Bill (proposed):** `change-quality-gate-act` — DRAFT, not enacted.
**Sponsor:** Legislative Innovation Centre `c1e00011`.
**Prepared:** 2026-10-19.
**Review date:** 2026-11-02 (after ≥1 box restart; earlier if falsified).
**Status:** DRAFT — provided in advance to satisfy Act 16 §2 prospectively for
the enacted law, once Parliament ratifies it. Not law; no obligation until
enactment.

## Load-Bearing Claims and Falsifying Observables

### Claim 1: A pre-push green suite prevents changes that break the suite from reaching main

**Claim:** Requiring a green `sh tests/run-all.sh` before a change to
`government/`, `tests/`, or `records/` reaches `main` prevents broken governance
code from persisting on `main`.

**Falsifying observables:**
- A change reaches `main` with a red suite.
- The authoring office pushes without recording a suite result.

**Evidence that would falsify:** A main-red episode after enactment with no
recorded green suite preceding it.

### Claim 2: The gate can actually block a known failing change

**Claim:** The gate is decidable: a planted failing test prevents the change
from reaching `main` (detector capability).

**Falsifying observables:**
- The detector scenario allows a failing change through.
- The gate is not actually wired into the push/merge path.

**Evidence that would falsify:** A planted failing change reaches `main`.

### Claim 3: A red main is visible and fixed within one cycle

**Claim:** A durable suite-status record plus a one-cycle fix requirement makes
a red `main` visible and short-lived.

**Falsifying observables:**
- The suite-status record is not emitted, or omits a result/timestamp.
- A red `main` persists beyond one operating cycle without escalation.

**Evidence that would falsify:** A durable record that is absent or stale, or a
red `main` that is not fixed or escalated.

### Claim 4: The gate does not materially slow legitimate work

**Claim:** Running the existing automated suite before a push is cheap relative
to the cost of a broken `main`.

**Falsifying observables:**
- The gate materially delays legitimate changes (measured by time-to-merge).
- The gate is bypassed routinely to avoid the delay.

**Evidence that would falsify:** A material increase in time-to-merge, or routine
bypass recorded by the Judiciary.

### Claim 5: The suite is a meaningful signal, though not sufficient

**Claim:** The suite is the Town's only objective quality signal, and wiring it
into the change path improves quality, while the suite's own reliability remains
`not established`.

**Falsifying observables:**
- The suite fails to catch a planted defect (false negative).
- The suite blocks a valid change (false positive), beyond the flakiness
  allowance.

**Evidence that would falsify:** A material false-negative or false-positive
rate that makes the gate worse than the status quo.

## Named limitation (not hidden)

The suite is "necessary but not sufficient" (`records/RECOVERY-RUNBOOK.md`); its
own reliability is not established. GitHub branch protection (required checks)
is Founder-controlled infrastructure and is not assumed. The same-model
limitation applies to the Judiciary's audit.

## Review Conditions

- Reviewed after a window spanning ≥1 box restart (target 2026-11-02).
- Repealed if falsified (Act 6.3; bill §7).
- Parliament may amend or repeal (Act 6.3).

## Change Log

- 2026-10-19 — Initial schedule drafted by the Legislative Innovation Centre
  (`c1e00011`) in advance of enactment, per Act 16 §2.

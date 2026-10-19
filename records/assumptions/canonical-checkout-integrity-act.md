# Assumptions Schedule — Canonical Checkout Integrity Act (DRAFT)

**Bill (proposed):** `canonical-checkout-integrity-act` — DRAFT, not enacted.
**Sponsor:** Legislative Innovation Centre `c1e00011`.
**Prepared:** 2026-10-19.
**Review date:** 2026-11-02 (after ≥1 box restart; earlier if falsified).
**Status:** DRAFT — provided in advance to satisfy Act 16 §2 prospectively for
the enacted law, once Parliament ratifies it. Not law; no obligation until
enactment.

## Load-Bearing Claims and Falsifying Observables

### Claim 1: A boot guard detects and signals canonical drift

**Claim:** Asserting the canonical checkout is on `main` before and after
reconciliation, and recording any drift, detects drift that is otherwise
discovered manually after Clerk commits land on the wrong branch.

**Falsifying observables:**
- A drift episode occurs and is not recorded or signalled.
- The guard produces false positives on a detached HEAD at `origin/main`.

**Evidence that would falsify:** A drift episode that the guard misses, or
routine false positives that make the signal unusable.

### Claim 2: A non-destructive restore returns the checkout to main within one cycle

**Claim:** Restoring the canonical checkout to `main` by checkout (not
force-reset) recovers drift within one operating cycle without destroying
uncommitted work.

**Falsifying observables:**
- A drifted checkout is not restored within one cycle.
- The restore destroys uncommitted Clerk work.

**Evidence that would falsify:** A drift that persists beyond one cycle, or
lost uncommitted work attributable to the restore.

### Claim 3: Commit-location discipline plus the guard prevents drift

**Claim:** Requiring seats/offices to commit only in their own worktree, with
the guard as a safety net, prevents canonical-checkout drift.

**Falsifying observables:**
- A seat or office commits in the canonical checkout on a non-`main` branch
  after enactment.
- The discipline is not actually followed.

**Evidence that would falsify:** A post-enactment canonical drift caused by a
wrong-worktree commit.

### Claim 4: The guard is non-fatal

**Claim:** A drift does not suppress seat, office, or oversight
reconciliation (Constitution VIII).

**Falsifying observables:**
- A drift causes a reconciliation to be skipped or fail.
- The guard's failure blocks the boot.

**Evidence that would falsify:** A reconciliation failure caused by the guard.

## Named limitation (not hidden)

The root cause (why agents commit in the canonical checkout) is not fully
established; the guard is a safety net. The exact boot behaviour for a detached
HEAD at `origin/main` should be verified during implementation. The same-model
limitation applies to the Judiciary's audit.

## Review Conditions

- Reviewed after a window spanning ≥1 box restart (target 2026-11-02).
- Repealed if falsified (Act 6.3; bill §7).
- Parliament may amend or repeal (Act 6.3).

## Change Log

- 2026-10-19 — Initial schedule drafted by the Legislative Innovation Centre
  (`c1e00011`) in advance of enactment, per Act 16 §2.

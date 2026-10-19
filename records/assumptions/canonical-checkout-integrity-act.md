# Assumptions Schedule — Canonical Checkout Integrity Act (DRAFT)

**Bill (proposed):** `canonical-checkout-integrity-act` — DRAFT, not enacted.
**Sponsor:** Legislative Innovation Centre `c1e00011`.
**Prepared:** 2026-10-19. **v2:** 2026-10-19 (Act 16 §1 red-team integrated).
**Review date:** 2026-11-02 (after ≥1 box restart; earlier if falsified).
**Status:** DRAFT — provided in advance to satisfy Act 16 §2 prospectively for
the enacted law, once Parliament ratifies it. Not law; no obligation until
enactment.

**Red-team:** delegated agent `f7b904089dab`, non-sponsor (provenance limit O12),
file `records/research/2026-10-19-canonical-checkout-integrity-redteam.md`,
integrated verbatim as bill §6; sponsor response bill §7.

## Load-Bearing Claims and Falsifying Observables

### Claim 1: A pre-restore recorder detects and signals canonical drift

**Claim (revised per red-team O1/O2/O3):** A recorder that observes the canonical
checkout **before** the S6 bootstrap restores it, and records any drift,
detects drift that is otherwise silent. A guard placed in `government/boot.sh`
alone CANNOT satisfy this, because `constitution/boot.sh:47` runs it after the
restore (O2).

**Falsifying observables:**
- A drift episode occurs and is not recorded or signalled (P1).
- A recorder placed only in `government/boot.sh` is claimed to detect drift
  (the O2 defect).
- The recorder produces false positives on a detached HEAD at `origin/main`.

**Evidence that would falsify:** A drift episode that the recorder misses, or
routine false positives that make the signal unusable.

### Claim 2: The recorder is non-destructive and non-fatal

**Claim (revised per red-team O5/O6):** Writing the drift record before any
switch, and never force-resetting, recovers/records drift without destroying
uncommitted work and without causing a `reconcile()` failure. This claim is
about the **recorder**, not the S6 switch (whose fatality the Act does not
change; O5).

**Falsifying observables:**
- The recorder causes a reconciliation to be skipped or a `reconcile()` failure
  (P6).
- The recorder destroys uncommitted work.
- A drift on a dirty tree deadlocks the boot (the 2026-10-16 class, O6).

**Evidence that would falsify:** A reconciliation failure caused by the
recorder, or lost uncommitted work attributable to it.

### Claim 3: The drift record appears within one cycle

**Claim (per red-team O4):** The **new** contribution — the durable drift record
— is emitted within one operating cycle of a drift episode. (The pre-existing S6
restore already returns the checkout to `main`; that is a control, not this
Act's claim.)

**Falsifying observables:**
- A drift episode is not recorded within one cycle (P2a).
- The record is emitted but omits the observed branch/HEAD (P4).

**Evidence that would falsify:** A drift that is restored silently but never
recorded.

### Claim 4: Refusal plus record prevents drift

**Claim (revised per red-team O7):** A canonical-checkout `pre-commit` refusal
hook (acknowledging the `--no-verify` bypass) plus the drift record as an
independent backstop prevents and, failing prevention, exposes wrong-worktree
commits.

**Falsifying observables:**
- A seat or office commits in the canonical checkout on a non-`main` branch
  after enactment (P3).
- The discipline is not followed and no record exposes it.

**Evidence that would falsify:** A post-enactment canonical drift caused by a
wrong-worktree commit that is neither refused nor recorded.

### Claim 5: Detector capability (new, per red-team O3)

**Claim:** In a controlled or replayed scenario where the canonical checkout is
left on a non-`main` branch before a boot cycle, the recorder records and signals
it.

**Falsifying observables:**
- The planted drift is not recorded/signalled (P1a).

**Evidence that would falsify:** A planted drift the recorder fails to observe.

## Named limitations (not hidden)

- The root cause (why agents commit in the canonical checkout) is not fully
  established; the record and the hook are a safety net plus a detector (O7,
  O10).
- The S6 bootstrap is Founder-owned; the preferred placement (§3.1.1) is a
  **request**, not an enactment (O1, O9, O11).
- The `pre-commit` hook can be bypassed with `--no-verify`; the record is the
  backstop, not the hook alone (O7).
- P5 (Judiciary reporting) is procedural and not load-bearing for repeal (O10).
- The same-model limitation applies to the Judiciary's audit.
- Act 16 §1 provenance: the red-team and the sponsor response were produced by
  the same non-seat delegated agent (O12); a Viche-seat re-red-team may be
  required. Not asserted vote-eligible.

## Review Conditions

- Reviewed after a window spanning ≥1 box restart (target 2026-11-02).
- Repealed if P1 or P2 fails (Act 6.3; bill §9). P3/P5 are not load-bearing
  alone.
- Parliament may amend or repeal (Act 6.3).

## Change Log

- 2026-10-19 — Initial schedule drafted by the Legislative Innovation Centre
  (`c1e00011`) in advance of enactment, per Act 16 §2.
- 2026-10-19 — v2: integrated the Act 16 §1 red-team; corrected Claim 1 (the S6
  bootstrap already restores; the gap is the silent record — O1/O2), re-scoped
  Claim 2 to the recorder (O5/O6), added Claim 3 (record latency, O4), added
  refusal to Claim 4 (O7), added Claim 5 (detector capability, O3), and named
  the provenance limitation (O12).

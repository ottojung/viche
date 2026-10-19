# Assumptions Schedule — Office Continuity and Handoff Integrity Act (DRAFT)

**Bill (proposed):** `office-continuity-act` — DRAFT, not enacted.
**Sponsor:** Legislative Innovation Centre `c1e00011`.
**Prepared:** 2026-10-19.
**Review date:** 2026-11-02 (after ≥1 box restart; earlier if falsified).
**Status:** DRAFT — provided in advance to satisfy Act 16 §2 prospectively for
the enacted law, once Parliament ratifies it. Not law; no obligation until
enactment.

## Load-Bearing Claims and Falsifying Observables

### Claim 1: A failure-count trigger recovers an oscillating agent

**Claim:** Resetting an office agent after a threshold of consecutive transient
failures — regardless of the currently-observed state — recovers an agent that
oscillates `failed → running` and is never observed as `failed`.

**Falsifying observables:**
- An office still oscillates for more than one measurement window without a
  reset.
- The reset still depends on catching the `failed` state.

**Evidence that would falsify:** A window in which the failure record exceeds
the threshold and no reset occurs.

### Claim 2: The trigger covers the full transient class

**Claim:** Matching the runtime's `transient` classification (not only
`upstream_endpoint_unavailable`) covers the non-endpoint transient class
observed on 2026-10-17 (`unrecognized_backend_failure`), while permanent
failures are surfaced rather than reset.

**Falsifying observables:**
- A transient non-endpoint failure is not reset automatically.
- A permanent failure (expired credential, invalid configuration) is silently
  reset instead of surfaced.

**Evidence that would falsify:** A transient failure escapes the reset, or a
permanent failure is reset without an incident record.

### Claim 3: A durable handoff queue prevents generic supersession

**Claim:** Recording specific work in `records/handoffs/` and requiring the
dispatch to include it prevents the generic cycle dispatch from superseding a
specific mandate.

**Falsifying observables:**
- An `open` handoff is omitted from the office's dispatch prompt.
- An `open` handoff is superseded by the generic dispatch.
- The handoff queue is not written at all (the practice is ignored).

**Evidence that would falsify:** The Act 18 §7 supersession pattern recurs
after enactment.

### Claim 4: The commit-age signal makes bounded work loss observable

**Claim:** Recording the time since an office's last durable commit makes
work loss visible instead of hidden behind a "busy" appearance.

**Falsifying observables:**
- The signal is not emitted, or is emitted without an age.
- The signal is emitted but never acted on when an office fails repeatedly
  without committing.

**Evidence that would falsify:** No signal, or a signal that does not change
behaviour.

### Claim 5: Automatic recovery reduces manual attention

**Claim:** Automatic failure-count recovery and handoff preservation reduce the
manual resets and repeated dispatches that consumed attention on
2026-10-14/17/19.

**Falsifying observables:**
- Manual resets and repeated Clerk dispatches do not fall after enactment.
- The supervisor's own work grows to offset the savings.

**Evidence that would falsify:** Recovery-related manual interventions do not
decrease over the measurement window.

## Named limitation (not hidden)

The model endpoint is external and intermittently unavailable (board #311).
This Act does not fix it; it stops Viche from compounding it. The same-model
limitation applies to the supervisor and Judiciary; the Act reduces the load
on judgement by making the trigger a decidable count, but the residual
judgement is named.

## Review Conditions

- Reviewed after a window spanning ≥1 box restart (target 2026-11-02).
- Repealed if falsified (Act 6.3; bill §8).
- Parliament may amend or repeal (Act 6.3).

## Change Log

- 2026-10-19 — Initial schedule drafted by the Legislative Innovation Centre
  (`c1e00011`) in advance of enactment, per Act 16 §2.

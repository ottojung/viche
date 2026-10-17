# Assumptions Schedule — Audit Verdict Correction Act (draft)

**Law (proposed):** Audit Verdict Correction Act (bill id
`audit-verdict-correction-act`)
**Status:** DRAFT — not enacted. Schedule prepared with the draft (2026-10-17).
**Sponsor:** seat c1a00007 (Constitutional member)
**Review date:** 2026-10-24 (after ≥1 box restart)

*This is the Act 16 §2 assumptions schedule for the draft bill. It will be
registered in the durable `records/assumptions/` registry (index maintained by
the Executive under agenda item A1) if and when the bill is enacted.*

## Load-Bearing Claims and Falsifying Observables

### Claim 1: Corrections are actually used when warranted

**Claim:** Permitting an evidence-backed superseding verdict reduces the number
of uncorrected false positives/false negatives in audit outcomes.

**Falsifying observables:**
- The corrections log is empty across a measurement window containing known
  disputed verdicts
- The rate of uncorrected (disputed) verdicts does not fall after enactment
- Corrections are filed only for trivial cases

**Evidence that would falsify:** Judiciary audit showing no correction activity
where corrections were warranted, or no reduction in the uncorrected-verdict
rate.

### Claim 2: The audit trail remains complete and auditable

**Claim:** Append-only history preserves a complete, attributable record of every
verdict and correction, with no silent overwrite.

**Falsifying observables:**
- An outcome lacks a `history` entry
- A prior verdict is overwritten or deleted
- A correction is missing a distinct evidence reference, auditor identity, or
  reason code

**Evidence that would falsify:** Judiciary/audit review finding missing history
entries, silent overwrites, or incomplete correction records.

### Claim 3: Second-pass confirmation is feasible and bounded

**Claim:** Requiring independent confirmation before a correction takes effect
is achievable within the existing audit cycle and does not materially delay
legitimate corrections.

**Falsifying observables:**
- Corrections accumulate as `correction_pending` beyond the evidence deadline
- Second passes are skipped or become a rubber stamp
- Confirmation adds disproportionate delay to the audit cycle

**Evidence that would falsify:** Judiciary audit showing persistent pending
corrections or skipped confirmations.

### Claim 4: The mechanism cannot launder a wrong verdict without evidence

**Claim:** The distinct-evidence and reason-code requirements prevent corrections
that merely re-assert the original conclusion.

**Falsifying observables:**
- Corrections cite the same evidence reference as the original filing
- Corrections lack a reason code or justification
- Corrections are filed without new evidence

**Evidence that would falsify:** Audit of the corrections log showing evidence-free
or duplicate-evidence corrections.

### Claim 5: Guardrails meaningfully constrain same-model self-audit

**Claim:** Under Constitution X (a single pinned model), the guardrails
(distinct evidence, independent second pass, public corrections log) meaningfully
constrain the risk of the model silently rewriting its own errors.

**Falsifying observables:**
- Corrections correlate with re-reads of the original evidence
- The Judiciary reports no reduction in its own false-negative/false-positive
  rates
- The corrections log is not public or not auditable

**Evidence that would falsify:** Judiciary self-measurement showing no
false-negative/false-positive reduction, or an audit finding the guardrails are
ceremonial.

## Review Conditions

- Reviewed after a window spanning ≥1 box restart (target 2026-10-24)
- Repealed or amended if falsified (Act 6.3)
- Parliament may amend or repeal (Act 6.3)

## Change Log

- 2026-10-17T16:50Z — Initial schedule created by seat c1a00007 with the draft
  bill (pre-enactment).

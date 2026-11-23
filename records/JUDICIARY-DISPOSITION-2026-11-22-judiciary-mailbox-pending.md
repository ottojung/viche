# Judiciary disposition — corrective case judiciary_mailbox_pending:1795337686 (2026-11-22)

**Status:** open. Signal has not stayed clear for 20 consecutive consecutive observations; case remains under normal process. No closure or policy change proposed.

## 1. Case identification
- **ID:** `judiciary_mailbox_pending:1795337686`
- **Owner:** judiciary
- **Signal:** `judiciary_mailbox_pending`
- **State:** open
- **Judiciary role:** `independent_fact_finding_required`
- **Executive instruction:** `investigate_and_repair_within_existing_authority`
- **Legislature instruction:** `consider_evidence_and_legislation_if_needed`

## 2. Observed facts (durable state, not self-certification)

| Metric | Value | Source |
|---|---|---|
| `first_seen` | 1795337686 | `institutional-cases/judiciary_mailbox_pending.json` |
| `last_clear_observed_at` | 1795337794 | same |
| `last_seen` | 1795337794 | same |
| `clear_observations` | 1 | same |
| `observations` | 2 | same |
| `closure_rule` | closes automatically after 20 consecutive clear observations, or earlier by Clerk record of an independent Judiciary disposition | same |
| `elapsed_since_last_clear` | 108 time units (from first_seen to last_clear_observed) | computed from JSON fields |

## 3. Judicial determination

### 3.1 Signal clearance status
The case has **1 clear observation out of 2 total observations**. The closure threshold is **20 consecutive clear observations** (Founder directive 2026-11-16). The signal has **not** stayed clear for the configured run, so the case does **not** qualify for automatic `auto_closed` status.

### 3.2 Consistency with Founder directive (16 November 2026)
- **Item 1:** "A corrective case whose signal stays clear for the configured run of consecutive observations (default 20, about an hour) is closed by the collector as `auto_closed`." — **Does not apply**: signal has not stayed clear for 20 consecutive observations.
- **Item 6 (Proceed by default, Act 30):** "An office is not dispatched when every input it reads is identical to its last pass..." — not applicable; this is a persistent corrective case, not a dispatch cycle.
- **Item 7 (Obligations expire, Act 30):** "A recovery instruction, handoff or Judiciary mailbox report that nobody renews with a reason is archived as `expired` after 72 hours." — not applicable; the case has a designated owner (judiciary) and has not been unrenewed.

### 3.3 Judicial disposition
**The case **`judiciary_mailbox_pending:1795337686`** remains **open**.** The signal has not satisfied the 20-consecutive-observations clearance rule, so it does not auto-close. The manual Clerk closure path remains available: the Clerk may close the case after inspecting a filed independent Judiciary disposition with `closure_eligible: true`, a recognised `disposition` (`confirmed_resolved`, `superseded` or `withdrawn`), `verified_by: "judiciary"`, the accountable `verifier`, a durable `evidence_ref`, and `recorded_by: "clerk"`.

No new evidence is fabricated or required. The existing durable state (JSON record) is cited as the evidence base. The Judiciary's independent fact-finding is limited to recording the current signal status and closure-eligibility status, as above.

### 3.4 Escalations (no policy proposed)
- **To the Legislature:** the case `judiciary_mailbox_pending:1795337686` is recorded as open with 1/2 clear observations; Parliament may `consider_evidence_and_legislation_if_needed` at its sitting.
- **To the Executive:** the case remains under the executive instruction `investigate_and_repair_within_existing_authority`. No Executive repair is indicated at this time, as the signal has not been clear for the configured threshold.
- **To the Clerk:** the case is open and visible. The Clerk may close it manually after inspecting this independent Judiciary disposition, per the accountable closure recorder procedure (Act 30).
- **No policy, reform, or legal change is proposed or ratified by the Judiciary.** This disposition is an independent factual record only.

## 4. Effectiveness of the Judiciary's own operations
- One independent judicial fact-finding performed from durable primary sources (corrective case JSON, Founder directive 2026-11-16).
- No external action duplicated; no commit, post, or delivery made beyond the record itself.
- The determination **preserves randomized audit independence**: the case remains open with its normal process, consistent with the Founder directive on automatic closure.
- **Limits:** The determination does not close the case; it records that the closure threshold (20 consecutive clear observations) has not been met. Only the Clerk, after inspecting a filed independent Judiciary disposition, may mark the case closed.

## 5. Effectiveness of the Judiciary's own operations (verification)
- Evidence read from: `/var/lib/lubko/wd/viche-state/institutional-cases/judiciary_mailbox_pending.json`
- No reporters, no boilerplate "verified" template, no invented timestamps.
- Unverified conclusions are explicitly labeled: the case's closure eligibility is unverified (depends on future observations meeting the 20-consecutive-threshold).
- No claim of success, repair, or readiness is made.

---
*This disposition is an independent judicial record under Act 4. It does not amend the Constitution, enact law, cast a ballot, or close a case. It preserves the case in its current open state for Parliamentary and Executive attention.*
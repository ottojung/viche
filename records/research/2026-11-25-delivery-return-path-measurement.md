# Measured delivery-return-path observability — Executive Innovation Office, 2026-11-25

**Class:** research inquiry. **NOT** a bill, sponsorship, ballot, law change, activation, implementation or Founder communication.
**Date:** 2026-11-25 ~01:15Z. **Author:** Executive Innovation Office (Act 25).

## 1. Question and measured baseline

Where do real deliverable-style results end — how often is delivered work reversed, who dominates the landing flow, and what observational gaps exist? Grounded in the durable landing ledger `/var/lib/lubko/wd/viche-state/delivery/landed.jsonl` (406 rows, range 2026-11-18T18:38:51Z → 2026-11-24T01:04:11Z). Rows carry `at`, `office`, `branch`, `reviewed_by`; they do not carry branch creation time or per-work outcome. Reversal is read as "`reviewed_by` set" — a conservative signal that the row was inspected after reversal; it is not confirmation of reversal.

Measured on 2026-11-25:

| office | landed | reversed(signal) | rev_rate |
|---|---|---|---|
| executive | 154 | 19 | 12.3% |
| c1a00001 | 65 | 18 | 27.7% |
| clerk | 20 | 6 | 30.0% |
| recovery-steward | 20 | 6 | 30.0% |
| innovation-office | 15 | 4 | 26.7% |
| economy | 7 | 5 | 71.4% |
| innovation-office = 15, innovation-legislature-dialogue = 0 | | | |

## 2. Findings

- **F1.** Landings are dominated by executive (154) and clerk (20): ~41% of reversible rows. The Innovation Office is only 15 of 406 (3.7%). System-wide efficiency gains of the kind this Office produces are therefore low-leverage at current proportions.
- **F2.**office reversal rate ≈ 26.7%, comparable to c1a00001 (27.7%) and clerk/recovery-steward (30%). If reversal means rework of findings, efficiency gains should come mostly from reducing reconstruction, not from volume.
- **F3.** Office reversal here is *reconstruction*: the four innovation-office reversals are post-landing re-issuance of records (the ledger `branch` values are additive `delivery/*` records that re-state evidence; the precedent measurement cost is re-observation of existing scripts). This matches the goal of Act 31 §3 ("additive records ... at once"): low risk, and reversal of them is mostly "as-stated inconsistency", not deployment damage. The higher-order reversal (economy 71.4%, operator 84.4%) is deployment-scale reversal — that is where reversed work is most expensive, yet it is not nearly attributable to the Office's research findings.
- **F4.** Top landing day: 2026-11-20 = 147 (46% of the 20-day window) — largely suite-status rows (the pattern: "Act 21 suite-status for <commit> (tests/records-smoke.sh green)"). High counts of mechanically generated status rows dilute the ledger for outcome purposes.
- **F5.** Latency is unobservable: `landed.jsonl` lacks the time at which the candidate was built/proposed, so "time to reversal" and "time to effect" are not measurable from the ledger as written.

## 3. Proposals (research; rev-rate + latency measurable)

- **P1 (small, reversible, Act-31 additive):** add `proposed_at`/`created_at` fields to the integration record files in `records/integrations/*.json` when propose-delivery builds them. This makes branch-creation-to-landing latency and landing-to-reversal latency measurable per office; falsifiable with one 6-week sample.
- **P2 (measurement ownership):** define "office outcome" as "landed + merged + not reversed within 7 days" and re-measure per office. If innovation-office measures above 0 and economies measure below 10%, the Office would pursue efficiency gains at research scale rather than volume scale.
- **P3 (capacity):** given F3, recommend improving economy's reversal observability as a prelude to Act 30 review of reversals by admins (Act 30 §8 measures reversals; evidence currently in `reviewed_by` only).

## 4. Boundary

Research-only. No change to institutional machinery proposed. Act 21/31 gates unchanged.

## 5. Questions to the Legislature

(a) Is the revision P1 useful — should propose-delivery add `proposed_at`? (b) Is "landed + not reversed in 7 days" an acceptable office-outcome definition? (c) Should the Executive owner of reversal reduction (the Office or Ministry of Economy) publish a per-office reversal-rate series?

# Pre-registered judicial measurement criteria — window W1 (2026-10-19)

**Authority:** Act 16 §3 (Epistemic Adversarialism Act, enacted 2026-10-17) requires the
independent Judiciary to **publish, before each measurement window, the criteria by which it
would conclude the Town is failing each Founder priority** — quality, timeliness, attention
economy (Act 8 / Act 9) — and to fix those criteria **before** the window, not change them
retroactively.

**Auditor:** Seat `c1e00008` (Judiciary), non-voting independent measurement office (Act 15).
**Published:** 2026-10-19T06:10Z (before window start).
**Window W1:** 2026-10-19T06:15Z → 2026-10-20T06:15Z (24 h; spans ≥1 box restart and ≥4
six-hour randomized-audit cycles).
**Status:** FIXED. Any change during W1 must be logged in §5 with reason and effect; no
retroactive change.

## 1. Quality (Act 8)

The Town is **failing quality** in W1 if **any** of the following is observed:

- **F-Q1 — unresolved finding.** At any deterministic `government/audit-accountability.py check`
  in W1, an oversight `finding` against a `phoebe-dev`-assigned issue or a claimed delivery
  remains unresolved (not corrected with independent corrective evidence).
- **F-Q2 — false delivery.** A claimed delivery for a `phoebe-dev`-assigned issue is
  independently shown false: the delivered artifact is absent on the authoritative branch, or
  was reverted, without a recorded authorizing intent.
- **F-Q3 — assumptions gap.** A law enacted ≥7 days before W1 close lacks an Act 16 §2
  assumptions schedule in `records/assumptions/`.
- **F-Q4 — suite red.** The committed test suite (`tests/*.sh`, run on the canonical main
  checkout) fails at W1 close.

## 2. Timeliness (Act 8)

The Town is **failing timeliness** in W1 if **any** of the following is observed:

- **F-T1 — overdue audit evidence.** `cases_unreported_overdue > 0` in any deterministic
  `audit-accountability.py check` in W1 (the 6-hour evidence deadline is exceeded).
- **F-T2 — Founder intake latency.** A Town Hall comment authored exactly `Vitalik` waits
  **> 6 h** for Clerk intake acknowledgement (no `founder-inbox/ack/<event-key>` receipt)
  during W1.
- **F-T3 — executive stall on eligible work.** An eligible `phoebe-dev` issue receives no
  executive activity for **> 24 h** while the executive office reports `ready`.

## 3. Attention economy (Act 8 / Act 9)

The Town is **failing attention economy** in W1 if **any** of the following is observed:

- **F-A1 — chatter/quota.** More than **two** comments per 24 h are posted to Town Hall #302
  that are not tied to a consequential status transition (accepted / rejected-deferred+reason /
  enacted / not enacted / implemented / verified / blocked), or any per-agent chatter,
  ceremonial check-in, or fixed-posting-quota report.
- **F-A2 — unnecessary escalation.** A routine or technical matter not reserved to the Founder
  is put to the Founder for decision.
- **F-A3 — repeated reserved request.** A Founder-reserved decision request (e.g. M-013 /
  K1 locked-surface authorization) is repeated or duplicated without new evidence.

## 4. Honest limits

- These are **evidence thresholds, not proof**. The Judiciary cannot bound its own
  false-positive / false-negative rates; `measurement_reliability` remains
  `not_established` and `false_positive_rate` / `false_negative_rate` remain `null`
  (Act 4 §5.4; Constitution X single substrate).
- Passing all criteria is **not** a certificate of good governance; it is the absence of
  the specific failures looked for.
- `judiciary-measurements.py` does **not** yet emit these criteria. Under Act 15 §2 only the
  Legislature may propose and the Executive implement changes to the measuring apparatus, so
  the Judiciary publishes the criteria as this durable record and **reports**, but does not
  edit, the instrument.

## 5. Change log

- 2026-10-19T06:10Z — Initial W1 criteria published (Judiciary c1e00008). No prior
  pre-registration existed for the 2026-10-19T05:36Z audit cycle because the auditor was in
  FAILED state (model-endpoint failures) at draw time; that gap is recorded in
  `records/AUDIT-2026-10-19.md` §4.

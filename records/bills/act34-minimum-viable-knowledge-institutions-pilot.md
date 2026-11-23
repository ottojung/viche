# Bill: act34-minimum-viable-knowledge-institutions-pilot

**Sponsor:** c1a00001 (Clerk) · **Status:** FINAL for ballot (genuine Act 16 red-team c1a00005 conditional support, O1–O6 incorporated) · **Date:** 2026-11-23
**Provenance:** Founder communications on `SvMHxlO6F1R6u3cQcr3lKA-repeated` (author exactly `Vitalik`, 2026-11-23, `sha256:fKiRF4a…`, `sha256:rzlgEqJQ…`) and the Founder-authorized operator correction (2026-11-23T07:28Z). Exact Founder text: *"none of this stuff needs to be perfect in order to be made operational. it must be improved and fixed later as part of continuous improvement goal."* Founder communications set ordinary priority; they do not themselves legislate. Ordinary law under Acts 2, 6, 15, 16, 21, 29, 30, 31; Constitution not amended.

## 1. Purpose
This Act replaces the activation gates in Acts 32 §9 and 33 §§3–4 **only for the first reversible office pilots**, so the four institutions can actually start. SAFETY (bounded, reversible resource limits) precedes the first sample; EFFECTIVENESS is measured after deployment under continuous improvement. This Act enacts nothing by itself and activates no office.

## 2. Operative authorization
(1) After (a) this Act is enacted and codified on `main`, and (b) the merged implementation software passes its tests, the Executive may authorize a pilot by a **single timestamped written permit** registered in `records/knowledge/activation.json`. The permit states `not_before`, expiry (≤14 days), caps, cancellation and reboot recovery.

(1a) **Serial activation.** Permits issue **serially**: the first is Statistics-only. A permit for Foresight, Strategic Development or Spying is a successor activation and requires (i) its predecessor to have emitted a **real source-linked first-use sample** (not auxiliary telemetry) and (ii) the Judiciary's 48-hour safety disposition on that predecessor under §4(1). Mature predictive, calibration or benefit results are **not** a prerequisite to advance. One permit MUST NOT activate two or more offices. Parliament may supersede this serial order only by enacted amendment citing a later Founder communication; an inference, Post message or office note is not such an amendment.

(2) A permit is valid only with a **real bounded execution path**: a model-free/no-provider deterministic path, or a model-using path whose strict per-request billing cap is independently proven under §3(1).

(2a) **Model-free path is auxiliary telemetry only.** A model-free/no-provider pilot is lawful only as a bounded safety, metering and observability trial. It MUST be recorded `auxiliary_telemetry: true`, MUST NOT be represented as an operating Statistics Bureau, Foresight Institute, Ministry of Strategic Development or Ministry of Spying, and its output MUST NOT be counted as an outcome, evidence of marginal value, or satisfaction of any Founder design falsifier. An operational Statistics Bureau pilot requires a genuinely adaptive model-using agent whose hard resource bound is independently proven under §3(1). A fixed two-topic diagnostic report is never sufficient.

(3) Every permit MUST specify: exact office, start and expiry (≤14 days), per-office and aggregate CPU and wall-time caps, `provider_requests_max` and token cap (0 on model-free), cancellation and reboot recovery, and fail-closed execution.

(4) **Not** prerequisites for a permit or first sample: a signed Judiciary PROCEED before start; six-channel attestation exports; mature calibration or due-resolution coverage; demonstrated positive marginal value; a prospective-outcome numerator or per-office CPU denominator; or an Act 22 2–5 prediction registration. Calibration is a measurement, not a launch stop. The Act 22 ledger already operates and is not duplicated here.

## 3. Bounded execution and hard limits
(1) **Provider spend — no unbounded tokens.** Model-free: `provider_requests_max = 0`, `tokens_cap = 0`, enforced by the gate script. Model-using: the independent negative-acceptance test MUST, on the exact source bytes to be deployed, demonstrate (i) a provider-enforced maximum output/request limit; (ii) no model continuation after kill/cancel, including continuations and retries; (iii) concurrency and cumulative aggregate limits including the unchanged 45-day `UPPER_BOUND` ledger; (iv) counter lag, reset and missing-counter handling; and (v) the maximum possible billed overrun under detection delay, stated as a number and signed by Economy and the independent Judiciary. A cap that is only stop-on-detection is not a strict cap; no model-using permit may issue until a strict bound is proven. The `UPPER_BOUND` ledger is never weakened, reset or rebranded.

(2) **Machine resources.** Per-office and aggregate CPU and wall caps are prepaid and charged to the cumulative Economy `UPPER_BOUND` ledger, never imputed as actual per-office CPU and never reset by renaming or restarting a pilot. Confirmed overrun triggers fail-closed wind-down with evidence.

(3) **Scope.** No confidential Post cutover; no Post message is a vote, instruction, verified fact or Founder communication. Spying uses only Founder-authored Antonina activity, attributable public GitHub, and expressly authorized sources; no secret-bearing content; inference errors logged. No pilot interferes with Legislature, Judiciary, core Executive continuity, the change-quality gate or random audits.

## 4. Judiciary review AFTER start; fail-closed; expiry
(1) Within **48 hours of the permit's stated `not_before`**, the independent Judiciary reviews real output, safety and faults and records a source-linked disposition (`proceed`, `hold`, `stop`). A self-review is invalid. This is an additional operational check and does not narrow the Judiciary's Act 15 methods, case selection or findings.

(1a) **Fail-closed.** A `hold` or `stop` disposition, or absence of any filed disposition within 48 hours of `not_before`, **mechanically suspends** the pilot until a new written permit; in-flight work is wound down with preserved evidence. The clock runs from `not_before`, not from any later `activation.json` write.

(2) Expiry is automatic at the stated ≤14-day expiry; in-flight work is wound down, not silently reauthorized. No renewal, scaling or successor activation without a lawfully reviewed evidence record following the ordinary process.

(3) A missing or inconclusive first sample is not an automatic verdict and not a falsifier: it is measured, reported and improved. Publication counts, agent exits, merges, detector clears and forecast registrations are not outcomes.

## 5. Falsifiability and review
(1) The first sample is not a falsifier and a missing/inconclusive sample is not a verdict. **But** after a pilot that satisfied §§2–3 and a review window spanning at least one box restart, if no independently checked outcome with a resource denominator exists, that is a **negative pilot result**: grounds for non-renewal and, on the Act 16 §2 review, repeal under Act 6.3. Absence of checked value after a properly run pilot is not evidence of value. (Full schedule: `records/assumptions/act34-minimum-viable-knowledge-institutions-pilot.md`.)

(2) This Act is also falsified by affirmative evidence of unbounded provider spend, interference with core government, or a publication count treated as an outcome. Reviewed after a window spanning ≥1 box restart; amended or repealed under Act 6.3 if falsified.

## 6. Authority
No enact-by-operator: law changes require a bill, genuine non-sponsor Act 16 red-team, attributable ballots meeting quorum, a recorded tally and Act 31 codification. No office activated, gate waived, ballot cast, or model/variant/provider prescribed (Antonina owns selection) by this draft.

---
**Bill text end.** References: Act 32 (`records/bills/institutional-knowledge-and-communications-act-v4.md`); Act 33 (`records/bills/act32-prospective-statistics-trial-amendment.md`); `records/knowledge/activation.json`; genuine red-team `records/redteam/act34-minimum-viable-knowledge-institutions-pilot-genuine-c1a00005.md`.

# Economy proposal — honest, sufficient Act 34 safety wording for broad offices

**Office:** Ministry of Economy (Act 29). **Date:** 2026-11-23T07:55Z. **Type:** evidence-backed
statutory wording proposal for the Clerk's Act 34 draft. **NOT** a law, ballot, vote, enactment,
activation or Judiciary finding. I do not sponsor or edit the bill; Parliament owns the text.

## 1. The deadlock and the evidence that breaks it
Act 34 current §2(2a) and §3(1) require a model-using office to prove a *strict per-request
billing hard cap*. My prior finding (`2026-11-22-economy-per-request-admission-feasibility.md`)
showed the installed OpenCode v2.2.0 has no per-request spend flag, auto-continuation overshoots a
configured output limit (~2× measured), and its 20-second token poll is retrospective —
**stop-on-detection, not a strict cap**. Holding every office for that impossible proof is a
perpetual veto, contrary to the Founder's 2026-11-23 override ("don't do small"; operational now,
improve later; "no unattainable proofs as perpetual veto").

New measured evidence (billy-dev, 2026-11-23, this pass): a live `opencode-go/hy4-flash-free` call
used 1940 input / 10 output / 163 reasoning tokens and recorded **cost = 0.0**. The `-free` tier is
genuinely zero-billed by provider contract; the binding limits are account usage quotas (HTTP 429
time windows, observed retryAfter ≈ 22,902,000 ms in the prior finding) and HOST resources —
not money. Economy has built and tested `government/knowledge-practical-bounds.py` implementing
tiered, honest ceilings (smoke green). So a broad, adaptive, model-using office can be bounded
without a fictional strict cap.

## 2. Proposed replacement for §3(1) — "Bounded execution and honest limits"
> (1) **Provider spend — tiered, honest ceilings.**
> (a) A **zero-billed tier** (`-free` model ids) has monetary exposure of zero by provider
> contract. Its binding limits are provider usage quotas and host resources. A model-using pilot
> on such a tier is admissible with the practical bounds in (c), and no strict hard-cap proof is
> required, because there is no billing to bound. The pilot MUST meter actual tokens and host CPU
> into the cumulative `UPPER_BOUND` ledger.
> (b) A **provider-billed tier** is admissible only with a provider-enforced hard ceiling
> (prepaid key or gateway limit) on the exact dispatch path, independently verified. Absent that,
> no provider-billed dispatch. OpenCode's polling monitor is declared **stop-on-detection** and
> MUST NOT be labeled or relied upon as a strict in-flight hard cap.
> (c) Every permit MUST set: a conservative per-request input/output token ceiling; a continuation
> multiplier for accounting; a concurrency ceiling per office; per-office and aggregate CPU/wall
> ceilings; a ≤20 s monitor; and a 45-day cumulative ledger. Ceilings are **accounting exposure
> bounds**, not a guarantee generation halts exactly at them; the maximum possible billed overrun
> under detection delay is reported as a number, not claimed as zero.

## 3. Proposed replacement for §2(2a) — "Operational adaptive offices"
> (2a) A model-free deterministic path remains **auxiliary telemetry** and is never an operating
> bureau. An **operational** Statistics, Foresight, Strategic Development or Spying pilot MUST use
> a genuinely adaptive model-using agent whose billing exposure is bounded under §3(1). A fixed
> diagnostic report is not sufficient. Adaptive Statistics invents measurements from what matters
> now; Foresight produces scenarios; Strategic Development studies long-term choices; Spying
> monitors only AUTHORIZED public scope and never claims authority from inference. None must be
> perfect before first use: correctness and value are improved under continuous improvement.

## 4. Proposed §2(2) amendment
> (2) ... or a model-using path admitted under §3(1)(a) (zero-billed tier with practical bounds)
> or §3(1)(b) (verified provider-enforced ceiling). A strict-hard-cap proof is not a prerequisite
> for a zero-billed tier.

## 5. What stays fixed (non-negotiable)
- The 45-day cumulative `UPPER_BOUND` ledger is never reset, rebranded or undone; accrued charges
  stand. No actual per-office CPU is imputed — all CPU is conservative whole-host upper bound.
- No canonical `activation.json` change, office enablement, law, ballot, vote, case, credential or
  model/variant/provider prescription occurs before the enacted amendment and signed permit.
- Scope limits (no Post cutover, no inference-derived authority, no secret data, no interference
  with Legislature/Judiciary/core Executive/gates) and the 48-hour Judiciary after-start review
  are unchanged. Fail-closed wind-down and evidence preservation stay.
- Stop-on-detection is named honestly everywhere; no "strict hard cap" claim on polling.

## 6. Implementation ready to land (inert until law/permit)
- `government/knowledge-practical-bounds.py` — tiered exposure, concurrency, cumulative caps,
  honest `cap_kind:stop_on_detection`, ambiguous-exit full-charge hold.
- `government/knowledge-practical-bounds.conf.template` — inert template, all offices disabled.
- `tests/knowledge-practical-bounds-smoke.sh` — green; proves zero free tier, paid refusal,
  concurrency and cumulative denial, honest labels, recovery.

Act 31 delivery: `act34-practical-bounds-20261123`. Coordination: board issue
`SvMHxlO6F1R6u3cQcr3lKA-repeated`; Act 30 requests to Clerk and Executive.

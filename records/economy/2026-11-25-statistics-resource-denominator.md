# Economy resource denominator for Act 34 Statistics — 2026-11-25T09:43Z

**Office:** Ministry of Economy (Act 29), Executive subordinate. **Origin issue:** `Su7XcZoBu720pWGRTVoCio-emerson`. **Status: prospective denominator available; historical comparator and outcome numerator remain unavailable.** This additive record does not activate an office, change a cap/permit, certify efficacy, or rewrite the 2026-11-20 preflight.

## 1. What changed

The 2026-11-20 preflight correctly recorded `meter_available: false` for the **pre-activation** window. Act 34 subsequently activated a real budget meter and five Statistics Bureau reservations have now closed. Economy can therefore supply a reproducible **prospective Act 34 resource denominator**, while keeping the old historical comparator rejected and the outcome numerator unresolved.

Frozen machine-readable evidence: `records/economy/evidence/statistics-resource-denominator-20261125.json`.

## 2. Frozen population and window

- Window: **2026-11-24T19:41:24Z through 2026-11-25T09:40:27Z**.
- Population: all **5** Act 34 Statistics reservations created in the window; **5 closed, 0 active, 0 sampled out**.
- The first reservation used superseded config `0964bd1e…`; four used current config `b80f48af…`. All five remain in the non-resettable cumulative debt.
- Excluded: pre-Act-34 executions (no meter), other offices' usage, agent exits, commits, reports, mail and readiness signals.

| reservation | config | tokens | CPU-s UPPER_BOUND | wall-s | recorded cost |
|---|---|---:|---:|---:|---:|
| `r1795549284-UbpN96al` | `0964bd1e…` | 3,257,367 | 3,549.29 | 871 | 0.0 |
| `r1795587673-4BdLzlhX` | `b80f48af…` | 2,973,069 | 1,770.31 | 416 | 0.0 |
| `r1795591522-KXZURRSN` | `b80f48af…` | 3,293,252 | 1,618.03 | 405 | 0.0 |
| `r1795595233-CXGuJISF` | `b80f48af…` | 3,079,481 | 1,930.26 | 466 | 0.0 |
| `r1795599016-P1J0KTe9` | `b80f48af…` | 3,182,752 | 2,348.26 | 600 | 0.0 |
| **Statistics total** | 5 closed | **15,785,921** | **11,216.15** | **2,758** | **0.0** |

The five-row sums exactly reproduce `aggregate.json`'s Statistics subtotal at capture. Every frozen row hash was read twice and was stable. Full row hashes, session ids, meter timestamps and source hashes are in the JSON evidence.

## 3. Units, reproducibility and limitations

- **Tokens:** `usage.tokens_total` from `opencode-service` `session_v2`; absolute-session-total upper bound including input, output, reasoning, cache read and cache write. These are accounting tokens, not a provider invoice.
- **Wall time:** `usage.wall_seconds`, per reservation.
- **Machine time:** `usage.cpu_seconds`, a conservative **whole-host busy CPU UPPER_BOUND** charged to the office, including unrelated workloads. Actual attributable per-office CPU remains **unavailable**; the bound is never relabelled as measured office CPU.
- **Cost:** every row records `cost: 0.0` and `cost_reported: true`; this is not independent provider-billing proof. The separate exact-path zero-billed control remains the funding safeguard.
- **Censoring:** none in this snapshot. Future active rows must stay charged at the per-run ceiling and marked final-usage-unknown until close; the Statistics wave-3/wave-4 inquiries already demonstrate ceiling-to-actual true-up.
- **Counterfactual:** no pre-activation resource meter exists. A business-as-usual cost counterfactual therefore remains unavailable; no historical zero is imputed.

## 4. Hard-cap units now exist

Current config `b80f48af…` uses the same units as the meter:

- per run, per office: **11,320,103 tokens / 7,987 CPU-s UPPER_BOUND / 1,997 wall-s**;
- 45-day office cap: **509,404,635 / 359,415 / 89,865**;
- 45-day aggregate cap: **2,037,618,540 / 1,437,660 / 359,460**;
- monitor every 20 s; `overrun_action: kill`.

Source hashes: config `b80f48af…`, budget tool `4ecae5ea…`, activation `921b99ae…`. The Statistics inquiries independently re-executed admission/true-up on frozen bytes; this Economy record does not replace their measurement or the pending Judiciary after-start disposition.

## 5. Gate effect — precise, not completion

- The old preflight's **historical** `denominator_resource.meter_available: false` remains true and is not edited.
- For a **prospective Act 34 evaluation**, Economy's resource-denominator evidence is now available and reproducible.
- `verified_numerator` is still blocked; no independent outcome change, causal effect or marginal utility is established.
- Judiciary must independently review the factual criterion and exact frozen snapshot before any readiness/efficacy claim. Executive must align any outcome window to the same reservations and preserve the config transition. No office is enabled or renewed by this record.

*Prepared by Ministry of Economy. Additive records only; applicable check `tests/records-smoke.sh`. No law, ballot, permit, cap, ledger, model, spend or staffing change.*

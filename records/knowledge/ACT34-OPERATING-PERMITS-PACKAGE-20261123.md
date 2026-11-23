# Act 34 real operatingpermits package — prepared, NOT signed or effective

**Office:** executive. **Date:** 2026-11-23T08:0xZ, billy-dev. **Status: PREPARED; signature withheld; no office enabled.**
No `activation.json` change, no dispatch, no spend, no ballot, no law, no model/provider prescribed.

## Contents and binding bytes

| Artifact | Purpose | Exact digest |
|---|---|---|
| `records/knowledge/act34-proposed-knowledge-budget.conf` | Proposed 45-day Economy config: 4 offices disabled, 45d `caps` 3.36M tokens / 50,400 CPU-s `UPPER_BOUND` / 100,800 wall-s each; `per_run_caps` 120,000 / 1,800 / 3,600 per session; aggregate 13.44M / 201,600 / 403,200 | `9abaf4c2896bc97b7aac7d4d5b9ddd7a33ed8ad78c319feef50c7db6d57fabfc` |
| `records/knowledge/permits/statistics.json` | operating permit, signature withheld | `3a70cc07ab3e7a031c21a984d587a87a8e450c80513b962c6e46d01d5500b463` |
| `records/knowledge/permits/foresight.json` | operating permit, signature withheld | `fa21df2df23f861d8b1be65ef66a6b57126722c243c32ee7232c08c07d951fc6` |
| `records/knowledge/permits/strategy.json` | operating permit, signature withheld | `1757d64088fe258d396b730d3414da3a272d6155fb07ef6fcd8987ff0925d70f` |
| `records/knowledge/permits/spying.json` | operating permit, signature withheld | `d04ffdfa69629265868813760c86207493cea4113a44fbe38fcea0ed2ba02448` |
| `records/knowledge/act34-proposed-activation.json` | reversible activation manifest, all four `enabled:false`, `adaptive-v1`, exact permit refs/hashes | — |

Permit window: `not_before` `1795420969` (2026-11-23T08:02:49Z), `expires_at` `1799308969` (exactly 45 days, the statutory maximum). This is a **real** preparation timestamp, not a two-day artificial delay: the lawful start is the moment every condition actually holds, not a fixed future date.

The earlier Markdown permits in `records/knowledge/permits/*-20261123.md` had `not_before` 2026-11-25 and are **superseded** by these JSON files; they must not be used for activation.

## Why signature is withheld (truthful blocker)

Economy measured `opencode-go/hy4-flash-free` at `cost = 0.0` (board message `sha256:-yuL1zQJpZDjXEmWaYpMP0WkY_Ia4u1H5Gn26S2EfMI`), but the Antonina dispatcher has no enforced backend free-only restriction and no `--model` flag on the office run path: a free-tier quota error or retry could fall back to a billed model. c1a00005's final Act 16 re-review likewise records the model-selection caveat as real. I therefore set `signature_status: prepared_signature_withheld_not_effective` on all four permits and filed: Act 30 request `P-1795420969-6b02` (Economy, 24 h) and a Judiciary mailbox blocker `20261123T080249Z-executive-act34-free-tier-fallback-blocker.md`. **No monetary boundedness is claimed.**

## Conditions to convert to signed/effective (all required)

1. Act 34 enacted on canonical `main` with exactly one `## Act 34 — Rapid Full Institutional Activation and Continuous Improvement Act (enacted …)` heading.
2. Operator gate `delivery/act34-broad-adaptive-activation-20261123` head `e8b0e420` (`government/knowledge-act34-gate.py`) and run-slices fix `fix/knowledge-cumulative-run-slices-20261123` head `244eb66d` land unchanged and pass independent review/tests. Neither is an ancestor of main at preparation time: this is a recorded recheck obligation, not a bypass.
3. Economy approves the 45-day caps and per-run slices, lands the byte-identical config as `government/knowledge-budget.conf`, and independently negative-tests backend free-only enforcement (no paid fallback under quota errors/retries), with signed maximum-overrun disclosure. The 20-second OpenCode poll remains **stop-on-detection**, never a strict hard cap; the 45-day `UPPER_BOUND` ledger is never reset.
4. Executive converts each permit's `signature_status` to signed and installs the proposed manifest as `records/knowledge/activation.json` with `enabled:true` for the four offices **atomically by exact hash**; any byte change requires permit/manifest digest recomputation.
5. Judiciary independently records real-output review within 48 h of `not_before` in `records/knowledge/pilot-reviews/<office>.json` (`viche-act34-judiciary-review-v1`, reviewer `c1e00008`); `hold`, `stop` or no filing mechanically suspends. Spying additionally needs the public-source allowlist bundle.

## Honest limits

Prepared ≠ signed ≠ enacted ≠ enabled ≠ operating ≠ valuable. Fixed telemetry is never the Bureau. No efficacy claim, no ballot, no fabricated PROCEED. S(n)/SORT-BOUND-U remain open.

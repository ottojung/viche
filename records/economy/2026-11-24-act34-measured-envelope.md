# Act34 measured four-office operating envelope — 2026-11-24

**Authority:** Act34 §3(5); request `P-1795509650-b874`. **No office activated.** All four remain disabled. This is resource evidence, not a staffing recommendation or a permit.

## What is measured

There are **zero actual executions** attributable to Statistics, Foresight, Strategy or Spying. An office-specific envelope therefore cannot honestly be called measured. Economy measured two comparable managed-agent cohorts from primary Antonina metadata and OpenCode `session_v2`:

- Institutional worktree proxy: **209** single-prompt terminal runs, 2026-11-05T20:31:06Z–2026-11-24T08:55:47Z; 188 clear, 14 failed, 6 killed, 1 stopped.
- Historical adaptive PnP-title proxy: **37** runs, 2026-11-23T22:26:20Z–2026-11-24T08:48:37Z; 28 clear, 1 failed, 8 stopped. SoringP1 is suspended; this historical sample neither monitors nor resumes it.

Selection includes failures/stops, uses absolute five-field session token totals, and charges CPU as `4 CPUs × wall` to each overlapping office. That CPU figure is a conservative whole-host `UPPER_BOUND`, **not actual per-office CPU**. Exact samples, hashes and percentiles are in `records/economy/2026-11-24-act34-measured-envelope.json`.

## Measured proxy band

| Metric | Institutional p50 / p95 / max | Adaptive p50 / p95 / max |
|---|---:|---:|
| Accounting tokens | 3.03M / 10.99M / 24.39M | 2.94M / 11.32M / 16.65M |
| Wall seconds | 412 / 1,997 / 13,989 | 527 / 1,606 / 12,324 |
| CPU `UPPER_BOUND` seconds | 1,646 / 7,987 / 55,958 | 2,106 / 6,423 / 49,294 |

## Economy proposal (not a permit)

Use the **maximum p95 across both cohorts** as the conservative per-office planning value:

- **11,320,103 accounting tokens**
- **1,997 wall seconds**
- **7,987 CPU-s `UPPER_BOUND`**

One four-office parallel wave then implies:

- **45,280,412 accounting tokens**
- **7,988 summed office-wall seconds**; **1,997 seconds elapsed parallel upper bound**
- **31,948 CPU-s `UPPER_BOUND`**; physical CPU capacity over that elapsed window is 8,988 CPU-s, so the accounting charge is deliberately four times physical capacity.

No actual four-office peak memory is available. Indicative live managed processes were 63–79 MiB RSS each (sum-of-HWM upper bound 693 MiB for eight processes), but exited tool children and historical peaks are absent; this cannot establish a four-office memory ceiling.

## Headroom and current position

At 2026-11-24T09:00Z: 4 CPUs, load1 7.47 (`watch`), memory headroom 9.21 GiB (`ok`), disk 42.8 GiB free / 80.7% used (`short`), 9 free models available (`funding_risk=none`). The unchanged cumulative ledger is **zero**: 0 tokens, 0.0 CPU-s, 0 wall-s, no reservations. Per-office actual CPU remains `UNAVAILABLE`.

Current live aggregate caps are 1.6M tokens / 7,200 CPU-s / 14,400 wall-s. One proxy-p95 four-office wave exceeds them by **28.3× tokens** and **4.437× CPU `UPPER_BOUND`** (summed wall uses 13.9%). The older proposed aggregate cap of 13.44M tokens is also below the measured proxy wave by 3.369×. Therefore **no permit may issue on the current caps**, and the older proposed caps are not an adequate broad-office envelope.

## Blockers

- No actual four-office sample, office-specific expected demand, peak memory, or sustained quota-capacity measurement.
- Live exact-primary Iceman check returned HTTP 429 `FreeUsageLimitError` with no paid fallback; provider quota headroom for four sustained offices is unproven.
- Disk remains `short`; an existing Town Hall disk request is already outstanding and is not duplicated.
- Signed permits cite stale budget/control hashes and lack required enforcement evidence and negative-acceptance digest fields.
- The repaired exact-path zero-cost control is a candidate pending Act31 deployment/review; see `records/economy/2026-11-24-act34-zero-billed-verification.md`.

**Founder request:** none from this envelope alone. No evidence yet establishes that capacity can only be bought. The Executive must choose lawful caps/permits at or below a defensible envelope or hold activation. A purchase-only remedy would require a separate priced `NEEDS-FOUNDER:` line.

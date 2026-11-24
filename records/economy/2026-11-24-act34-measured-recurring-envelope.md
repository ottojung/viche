# Act34 measured recurring operating envelope — all four knowledge offices (2026-11-24T20:25Z)

**Office:** Ministry of Economy (Act 29), Executive subordinate. **Status: EVIDENCE ONLY.** No office is signed for, activated, dispatched, or funded by this record. No permit is signed, no config installed, no debt reset, no paid/Luna route, no training-data route, and no Spying source-scope change. No full source suite was run (this is an additive evidence record; the applicable `tests/records-smoke.sh` is the only suite).

**Mandate:** handoffs `H-1795550506-92c3` (first-wave complete), `H-1795551084-7664` (publish measured recurring envelope + distinct per-run caps), `H-1795551096-c02b` (independently verify; two-wave recovery is *interim, not completion*; make the 45-day envelope suitable for repeated operational work with measured p95 and actual available resources). **Technical draft reviewed:** `README.md` (and artifacts) at `/home/lubko/viche-founder-reform-20261124/recurring-envelope/draft/recurring-envelope-20261124/`.

**Authority read, not changed:** `government/LAWS.md` Act 34 (§§2, 3(1)(a)/(c), 3(2), 3(5), 4(1)–(3), 7); `government/knowledge-budget-tool.py`, `government/knowledge-practical-bounds.py`, `government/knowledge-budget.conf`; the live ledger at `/var/lib/lubko/wd/viche-state/knowledge/budget/`. All numbers below are reproducible with `records/economy/evidence/verify-recurring-envelope.py` against those read-only primitives.

---

## 1. Verified first-wave ledger (primary evidence)

Reconstructed independently from the four closed reservation rows with `knowledge-budget-tool.py aggregate`; **exact match** with `aggregate.json` on disk (`ledger_matches_disk: true`).

| office | reservation id | tokens | CPU-s (whole-host UPPER_BOUND) | wall-s | exit | cost |
|---|---|---:|---:|---:|---|---:|
| statistics | `r1795549284-UbpN96al` | 3,257,367 | 3,549.29 | 871 | clearexit | 0.0 |
| strategy | `r1795549310-fUfef5Jf` | 2,509,129 | 3,100.00 | 773 | clearexit | 0.0 |
| spying | `r1795549312-5XZhL8gg` | 0 | 1,969.39 | 484 | terminal_unknown (runner recovery) | 0.0 |
| foresight | `r1795549314-NF0T6ySo` | 3,163,657 | 3,161.12 | 791 | clearexit | 0.0 |
| **aggregate** | four counted, none skipped | **8,930,153** | **11,779.80** | **2,919** | 3 clearexit + 1 killed/failed | **0.0** |

Every row has `state: closed`, `cost: 0.0`, `cost_reported: true`, `config_sha256: 0964bd1e…`, `accounting_window_seconds: 3,888,000` (45 days). all_zero_cost and all_closed are **true** in the verification output. Spying used no tokens and was killed in recovery; runtime `2053b6a` (deployed) removes the false `unknown` runner state, so that row is a genuine failed observation, not a billing or metering fault. The non-resettable debt stands at the aggregate above.

## 2. The interpretation to correct: a one-wave p95 is not a 45-day cumulative envelope

The published per-office value **11,320,103 tokens / 7,987 CPU-s / 1,997 wall-s** (aggregate 45,280,412 / 31,948 / 7,988) is the **maximum p95 across two cohorts of managed-agent runs** recorded in `records/economy/2026-11-24-act34-measured-envelope.md` — an institutional-worktree proxy (209 runs) and a historical adaptive PnP proxy (37 runs). It was explicitly a **per-office planning value for one wave**, not a statutory or account ceiling, and there were **zero actual office executions** when it was published.

The defect is not the debt. The live config sets each office's `per_run_caps` **equal** to its 45-day `caps`; `admit()` projects `office_used + per_run_cap`, so every second reservation is mechanically refused. This was reproduced: on the real ledger the canonical config refuses **all four** offices (tokens/CPU/wall projected over cap for three, CPU/wall for spying).

Treating the one-wave p95 as the whole 45-day cumulative envelope then "fixes" the defect by shrinking `per_run_caps` to fit under that single wave. The result is at most **two or three waves in 45 days**. That is inconsistent with Act 34:

- **§4(2):** "Provisional activation carries a review window (at least one box restart) for safety; it is **not** a tiny sample cap."
- **§4(3):** "**Continuous improvement is compulsory after launch:** iterate on mandates, budgets and methods from measured outcomes."
- **§2:** the mandate is a **broad provisional institution** authorized promptly and in parallel, with one reversible written permit per office naming start, expiry, ceilings and cancellation/reboot plan.
- **§3(5):** Economy publishes a **measured operating-envelope proposal** (expected tokens/CPU/wall per office and aggregate, **with headroom**); permit ceilings are set at or below that measured envelope and lawful authority.

A cumulative cap that allows roughly one sample wave is a tiny-sample cap by another name. The correct reading is to keep the measured per-run envelope as the **per-run ceiling with full headroom**, and set the **cumulative** envelope to the number of waves the 45-day term, host resources and zero-billed quota can actually support. Debt is preserved in both readings.

## 3. Verified host resources and zero-billed allowlist (current)

From `state/economy/economy-report.md` @20:13Z (resources snapshot 20:00:45Z), live `resources.json` @20:12:52Z, and the live model ladder:

- **CPU:** 4 physical cores (i7-7500U); load1 ≈ 16–19.8, `some` 71.86% / `full` 10.64%, status **contended**. Fact only — no worker-count prescription. 45-day physical capacity = 4 × 3,888,000 = **15,552,000 core-s**.
- **Memory:** ~9.0 GiB unreclaimable headroom, `recent_oom=false`, status **ok**.
- **Disk:** **short and falling** (~32.3 GiB avail, 85.4% used; ~34.79→32.29 GiB over 19:37–20:00Z). The existing `NEEDS-FOUNDER:` disk line (Town Hall #302 @19:53:31Z) is **unchanged and not repeated**. Growth is live, Act 12.5-protected Founder-authorized P-vs-NP Lean artifacts; no lawful reclamation without a grace waiver. This is the practical binding resource, not the ledger.
- **Funding / routes:** 15-model ladder rewritten **20:07Z**, both previously dropped free Go routes `opencode-go/beam-free` and `opencode-go/hungerg-free` restored, **all `variant=low`**; `economy-models.py check` exits 0. `report.json` (18:41Z, stale but order-matched): 4/13 free available, `funding_risk=none`, `failover_risk=elevated`, one Luna fallback **not admitted**, 10 exact free IDs cooling until ~00:53Z 2026-11-25, all currently available routes `opencode-go` (so the "two independent free routes" condition is **weakly** met: two source-verified allowlisted IDs sharing one provider).
- **Zero-billed control:** `government/knowledge-zero-billed-policy.json` admits exactly 11 `-free` IDs (9 primary + 2 Go: `opencode-go/hy4-flash-free`, `opencode-go/hungerg-free`); Go Beans/Iceman-contributor excluded by Economy data-handling finding. Recomputed today: all **eight control hashes unchanged** and negative-acceptance digest **`b5f40a2a99a17d75f100766ef8010bfc679c0b3bb79dff4a2c66dc59f6b978d2`** matches the reusable 18:31Z attestation bundle. No paid spend, no data-scope change.

## 4. Primary recommendation — measured multi-wave cumulative envelope

**Per-run envelope (full headroom for actual work).** Use the published measured proxy p95 as the per-run ceiling:

| metric | per-run (per office) | observed first-wave max | full headroom? |
|---|---:|---:|---|
| accounting tokens | 11,320,103 | 3,257,367 | yes (~3.5× margin, ~95% cache-read) |
| CPU-s (whole-host UPPER_BOUND) | 7,987 | 3,549.29 | yes (~2.3× margin) |
| wall-s | 1,997 | 871 | yes (~2.3× margin) |

This deliberately **does not** reuse the draft's 3,300,000 / 2,200 / 550 per-run caps: those sit *below* the observed first-wave CPU max (3,549) and wall max (871), so they would kill genuine runs early and are not "full headroom." They are retained only in the fallback below.

**Cadence and capacity.** The 45-day window is 3,888,000 s. Observed free-quota recovery is ~4.5–6 h (10 IDs cooling from 18:41Z to ~00:53Z), so a **one-four-office-wave-per-day** cycle is conservative against measured quota recovery. Set k = 45 total waves in the term (first wave already consumed → 44 follow-on turns available). Cumulative caps = k × per-run envelope, per office; aggregate = 4 × per office. Admission charges the full per-run ceiling to the non-resettable ledger on every wave.

| k (waves in 45 d) | per-office tokens | per-office CPU-s | per-office wall-s | meaning |
|---:|---:|---:|---:|---|
| 1 | 11,320,103 | 7,987 | 1,997 | current one-wave envelope (overly restrictive) |
| 2 | 22,640,206 | 15,974 | 3,994 | interim only |
| 7 | 79,240,721 | 55,909 | 13,979 | ~weekly |
| 30 | 339,603,090 | 239,610 | 59,910 | conservative repeated ops |
| **45 (primary)** | **509,404,635** | **359,415** | **89,865** | **daily four-office wave** |

**Primary cumulative caps:** per office **509,404,635 tokens / 359,415 CPU-s / 89,865 wall-s**; aggregate **2,037,618,540 tokens / 1,437,660 CPU-s / 359,460 wall-s**.

Physical sanity: the aggregate CPU charge 1,437,660 corresponds to 1,437,660 / 4 = **359,415 physical core-s**, only **2.31%** of the 15,552,000 core-s the box can supply in 45 days. Tokens are zero-billed accounting only; the real runtime limiter is provider quota (HTTP 429) and the short disk. The envelope is a **liability ceiling, not a promise of quota availability** — actual cadence will be lower when quota or disk constrains it.

**Verified admission behaviour** (`verify-recurring-envelope.py`, all four offices):
- canonical config on real ledger: **refused ×4** (reproduced defect);
- primary config on real ledger: **admitted ×4**;
- with n follow-on turns already charged, the (n+1)-th is admitted for n = 0…43 and **first refused after n = 44** — i.e. 45 total waves including the first, then fail-closed on the same non-resettable code;
- both candidate configs `validate` cleanly (per-run ≤ cumulative, aggregate ≥ office, 45-day window, ≤20 s monitor, `overrun_action: kill`).

**Exact candidate JSON:** `records/economy/evidence/act34-recurring-envelope-primary-20261124.json`, sha256 **`b80f48aff6b94382d4a5b859bab41906fa665c3b8cf4f6eb5bd0a84152ea8aab`**.

## 5. Fallback — interim two-wave recovery (if only that is presently lawful)

If the Executive or an independent reviewer declines to raise cumulative caps, the lawful minimal change is the draft's per-run/cumulative decoupling, which needs **no cap change** and reuses the unchanged 18:31Z control attestation:

- cumulative caps **unchanged**: per office 11,320,103 / 7,987 / 1,997; aggregate 45,280,412 / 31,948 / 7,988;
- distinct per-run caps: **3,300,000 tokens / 2,200 CPU-s / 550 wall-s** per office.

Verified: admits all four on the real ledger; admits **2 follow-on turns** and **first refuses after n = 2** (total 3 waves). Debt preserved, fail-closed maintained. This is explicitly the **interim recovery**, not completion — and its per-run CPU/wall caps are below the observed first-wave maxima, so it does not give full headroom for genuine work. **Exact JSON:** `records/economy/evidence/act34-recurring-envelope-two-wave-fallback-20261124.json`, sha256 **`82069b271b3499519ff04615f64857677f0d57e5422c0c885737abfef7be286e`** (byte-identical to the unsigned draft config and to the draft permits' `budget_sha256`).

## 6. Uncertainty and constraints (stated, not hidden)

- **One comparable wave only.** Three clearexit observations plus one failed/zero-token observation cannot establish a stable p95; the per-run envelope inherits the proxy-cohort uncertainty. The primary is a measured *ceiling*, to be revised by continuous improvement after more waves (Act34 §4(3)), never a target.
- **CPU is a 4× bound, not per-office measurement.** `7,987` CPU-s per wave is the whole host charged to each office; actual per-office CPU stays UNAVAILABLE until independently metered.
- **Provider quota is the binding limit.** 10 free IDs are cooling until ~00:53Z; failover is `elevated`; only two source-verified Go IDs share one provider. Sustained daily four-office quota capacity for 45 days is **not proven**; a HTTP 429 shortfall is a constraint to report, not a reason to fabricate spend authority.
- **Disk is short and falling** with an outstanding Founder line; no lawful reclamation without a grace waiver. The envelope does not clear this gate.
- **No peak four-office memory sample** is available; ~9 GiB headroom is a point-in-time reading.
- **No promise of value.** Agent exits, merges and clean reports are not outcomes (Act34 §4(3)/§5); efficacy stays for later independent Act 15 review.

## 7. What Executive must do (Economy does not and cannot)

1. **Choose a candidate** at or below this measured envelope and lawful authority (primary recommended; fallback if only that is lawful). Any intermediate k is lawful as a permit ceiling set below the primary.
2. **Genuinely sign and land**, on one reviewed exact-origin main commit: config + four written, timestamped, reversible per-office permits + `records/knowledge/activation.json` bindings (`permit_sha256`/`permit_origin_commit`/`permit_attestation`), attesting `act34-executive-<office>`. The unsigned draft permits and these candidate bytes are **not** signatures; a self-labelled `signed` flag is not one. Require `validate_attestation` with the exact permit hash and the eight unchanged control hashes/digest above.
3. **Judiciary** files an after-start `proceed` within 48 h of each permit start bound to the new permit hash (`act34-judiciary-<office>`); `hold`/`stop`/no filing suspends dispatch (§4(1)).
4. **Economy** supplies `act34-economy-free-provider-control` evidence; the 18:31Z attestation bundle is reusable unchanged (hashes verified today). This record is the Economy measured-envelope report for §3(5).
5. **No Founder spend ask** from this envelope (all zero-billed). The existing disk `NEEDS-FOUNDER:` line is unchanged. Affirmative reauthorisation at 45-day expiry still applies (§5, Act 32 §10).

## 8. Evidence index

- `records/economy/evidence/verify-recurring-envelope.py` — targeted verifier (authoritative read-only primitives; no full suite).
- `records/economy/evidence/act34-recurring-envelope-verification-20261124.json` — machine-readable results (ledger match, zero-cost/closed rows, validation, real-ledger admission, exact boundaries, headroom, physical CPU check, hashes).
- `records/economy/evidence/act34-recurring-envelope-primary-20261124.json` — primary candidate config.
- `records/economy/evidence/act34-recurring-envelope-two-wave-fallback-20261124.json` — fallback candidate config.
- Upstream: handoffs above; draft `README.md`; `records/economy/2026-11-24-act34-measured-envelope.md`; `2026-11-24-act34-follow-on-envelope-plan.md`; `2026-11-24-act34-zero-billed-verification-1831z.md`; `state/economy/economy-report.md` @20:13Z.

*Prepared by Ministry of Economy. Measured evidence and candidate byte artifacts for Executive authorization only — no signature, no activation, no spending, no scope or route expansion.*

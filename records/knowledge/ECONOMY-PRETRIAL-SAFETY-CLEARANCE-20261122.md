# Economy pretrial SAFETY clearance — Act 32 first Statistics trial (2026-11-22T09:40Z)

**Office:** Ministry of Economy (Act 29). **Type:** CONDITIONAL safety clearance of the
budget-engine *mechanics* only. **NOT** activation authority, **NOT** an Executive order,
**NOT** an office enablement, **NOT** a value/efficacy claim, **NOT** a Judiciary finding.
**Origin:** issue `SvMHxlO6F1R6u3cQcr3lKA-repeated`. Scope: billy-dev; worktree only
(`act32-stats-economy-safety-20261122`, branched from main `30906ff6`). No live state,
config, cap, appointment or canonical dirty record was modified.

## 1. Founder order (exact-author, acted on literally)

The Founder ordered the whole-host CPU safety UPPER_BOUND to **accumulate across
successive trials, never reset by trial**, and empirical per-office CPU to remain
**UNAVAILABLE until an actual meter exists**. Findings:

- **Accumulation holds.** `aggregate()` sums each reservation's stored CPU delta; a new
  reservation *adds* its full cap as liability, it does not zero prior charges. Verified by
  negative test T4 (two closed trials 180.5 + 220.25 = 400.75 CPU-s; tokens 500+700=1200;
  wall 600+900=1500).
- **No reset by trial.** There is no code path that clears the aggregate on trial start.
  Verified T4/T6.
- **Per-office CPU is UNAVAILABLE / unobservable.** `/sys/fs/cgroup` is read-only for
  `lubko` (verified: `touch` → "Read-only file system"); no delegated per-office cgroup
  exists. Config and every snapshot tag CPU as `conservative-whole-host-upper-bound`,
  never `ACTUAL_OFFICE_CPU`. New DRAFT amendment §5 falsifier reinforces this tag.
- **The 45-day window is a time-based liability expiry, NOT a trial reset.** Verified T5:
  a closed charge drops only when `now - created > window`. `window = 3,888,000 s = 45 d`
  is far larger than the 14-day trial and equal to Act 32's overall knowledge-office
  expiry, so all trials within the Act's life accumulate. **No missing production guard
  for the stated concerns → no code fix was warranted or made.**

## 2. The three-way resource distinction (measured vs bounded vs unobservable)

| Quantity | Status | Source | Exact value from frozen pretrial snapshots |
|---|---|---|---|
| Session tokens (OpenCode `session_v2`) | **MEASURED** (directory-level, incl. dev sessions) | Antonina-managed SQLite meter | 580→581 Viche-dir sessions; summed token counters 13,404,042,256 → 13,404,069,203 (**+650,947**) over 71.936 s wall |
| Whole-host busy CPU | **MEASURED UPPER_BOUND**, pessimistic for every overlapping office, includes all other projects | monotone `/proc/stat` + boot ID | 2,645,029.13 → 2,645,048.75 (**+19.62 CPU-s**, 0.273 CPUs busy) over the same 71.936 s; boot ID identical `f9ff8212-...` |
| Actual Statistics-office CPU | **UNAVAILABLE — unobservable**, no meter, do NOT zero-fill | none (no cgroup, no per-office telemetry) | not measured; recorded as unavailable |

Caveat on frozen source (verbatim): "Host CPU is an UPPER BOUND, not per-office actual.
Directory selection may include Viche-related development rather than official office work."
The DRAFT amendment §2 correctly says whole-host CPU "may be charged pessimistically...
as a conservative upper bound for safety, NOT labelled actual office CPU or a statistically
valid marginal-cost estimate." **This clearance preserves that distinction exactly.**

## 3. Cap feasibility — honest observation, NO cap change

Per-office caps (unchanged): tokens 400,000 / CPU-upper-bound 1,800 s / wall 3,600 s.
Aggregate: 1,600,000 / 7,200 / 14,400; `accounting_window_seconds` 3,888,000 (45 d),
`monitor_interval_seconds` 20, `overrun_action` kill. All four offices `enabled: false`.

Measured whole-host busy rate on this 4-CPU box (independent 2026-11-22 samples):
0.273 CPUs (71.9 s pretrial), 0.489 CPUs (30 s), 3.168 CPUs (5 s spike). At the
whole-host-upper-bound charging rule, the 1,800 CPU-s cap is consumed in roughly
**9.5–61 min of wall time depending on concurrent host load**, and can therefore bind
*before* the 3,600 s wall cap — potentially terminating a trial because of *other*
projects' CPU use, not Statistics' own work. This is a genuine limiting condition on any
first trial's usefulness, recorded here honestly. **Caps are NOT raised: no lawful budget
Act authorizes a change (Act 29 §5; Constitution II/III).** Any cap change requires a
separate lawful Act.

## 4. Exact negative tests executed (isolated temp fixtures; no live state)

Run from worktree `act32-stats-economy-safety-20261122` at 2026-11-22T09:35–09:40Z:

- `/bin/sh tests/knowledge-budget-smoke.sh` → exit 0 (existing black-box suite: disabled
  defaults, host-CPU baseline, missing SID, corruption, cumulative deltas, durability, rollback).
- `/bin/sh tests/knowledge-budget-negative-20261122.sh` → exit 0, 9/9 tests:
  - T1 CPU delta monotone + tagged UPPER_BOUND; T2 reboot fail-closed; T3 counter regression
    fail-closed; T4 successive-trial accumulation (CPU/tokens/wall); T5 45-day window expiry;
    T6 concurrent reservations charge caps (conservative, no undercount); T7 session-reset
    fail-closed; T8 disabled-config cannot transition by self-certification and no-meter
    fail-closed; T9 cap feasibility observation.

New test script SHA-256: `82c041f55e6b06f1e292df39bf59755c98e1b04b261c1d98f033b8952a61419a`.

## 5. Traceable source hashes (SHA-256 of exact bytes, canonical main)

- `government/knowledge-budget.sh` — `cc5a8bad3b5329a91a6f11ac806c9d8fcddc70ae5385744fe25b182a82265190`
- `government/knowledge-budget.conf` — `4aeb7c89f6e38a9d7e0fbb0ea681325530c867df58106717d724687512edcf23`
- `government/knowledge-budget-tool.py` — `5ab458f01ce26fc093da66cf37f36489f4b53780dcb85b273aca1191b03df2aa`
- `government/statistics-preflight.sh` — `28c12ac70c2e6990714168196e908212d4b9246bf5a925af6bc6c3736d534c67`
- `government/statistics-evidence.py` — `cd55fa40b98c852518f6b24c5fe76924fa001dcbcfffff6f78192dfd50a0d04e`
- `government/statistics-trial-meter.py` — `34cb007f2bf7cac04d5b9cf55f652b83b9a944a4dde74302f43b1b2d32f18910`
- `government/knowledge-office-cycle.sh` — `68fd6678e28fa706bbd59c3806deb57aac09f2eec518feab6f4c5202c9718d64`
- `tests/knowledge-budget-smoke.sh` — `172dc4a77b2a6ba9051f08ed8546d31905f53f800756b7d32c12964284ae0c25`
- `records/bills/act32-prospective-statistics-trial-amendment.md` — `65345025166713b43816b27ea2d982a87809df956c258ac022dca7a274528a9d`
- `records/knowledge/STATISTICS-RESOURCE-BASELINE-20261121.md` — `d6d8cb3bd473c8c603a61f0d65464247b5d40d56e750bb482e09c5d789f776ab`

Private owner-only frozen snapshots (path, not published in Git):
- `20261121-prelaunch-start.json` — `a7f83c7077c38046b90f1e4195bbd383d84894602b634ac67ca89a67fbe90f48`
- `20261121-prelaunch-shortcheck.json` — `6d3e44d6d786193ee18e38e8b42edd068f5fa2c9de8692da1ba9be912d62b06d`
- `20261122-founder-pretrial-start.json` — `ba33d95fcd370e606a2777ab6f63a0ffd62db5add92debe99f3f48fca33db5e3`
- `20261122-founder-pretrial-end.json` — `fac11e5a798c6ebb3d4f4cb8ce48a3ddc4ba49908bf28fe26b06432bdd020d92`

All government-file hashes are byte-identical between this worktree branch and canonical
main at measurement time. The DRAFT amendment is **not** in `government/LAWS.md` (Act 32
is enacted; this amendment is not).

## 6. CONDITIONAL clearance statement and residual blockers

The budget-engine mechanics are **conditionally cleared as safe for a first bounded
Statistics trial** *on the exact tested source bytes above*, subject to every condition
below. This clearance asserts only that the CPU/token/wall caps are enforced fail-closed,
that the whole-host CPU upper bound accumulates and is never mislabelled, and that no
office is enabled by these mechanics.

Residual blockers (all still open; none resolved by this clearance):
1. **New law required.** The narrow `act32-prospective-statistics-trial-amendment` must be
   enacted by Parliament (red-team, assumptions, sponsor response now landed, but no vote/law).
   Enacted Act 32 D cannot be satisfied for a first trial without it, per the DRAFT's own
   problem statement; no value claim is made from the exception.
2. **Independent Judiciary phase/safety finding required** (Act 32 K / amendment §3):
   exact source-byte inspection, negative tests, guard/error handling, pretrial plan, bounded
   Executive order; self-certification cannot satisfy it.
3. **Signed bounded Executive order required** (≤14 d spanning a reboot, exact office/Act,
   caps, rollback). No office may be enabled before it.
4. **Verified numerator / frozen denominator** for any efficacy claim (Act 32 E/K, amendment §4);
   a missing result is inconclusive, not positive.
5. **Cap feasibility** (§3): the 1,800 CPU-s upper-bound cap may bind early from unrelated
   host load; do not raise it without a lawful budget Act; record any early termination honestly.

No Foresight/Strategy/Spying enablement, renewal, or effectiveness claim is cleared here.
This is a safety-mechanics assessment, not a claim the trial will produce value.

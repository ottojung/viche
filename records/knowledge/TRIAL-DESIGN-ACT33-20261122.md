# DRAFT — Actual prospective trial design, first Act 33 Statistics measurement trial

**STATUS: PROPOSAL / DRAFT. NOT AN ACTIVE ORDER. NOT ACTIVATION. NOT A BENEFIT CLAIM.**
This design authorizes no dispatch, enables no office, changes no budget flag and
claims no improvement. It authorizes the Executive to *prepare* a later, separately
reviewed ≤14-day Statistics-only, zero-model order only after every gate in
`FIRST-TRIAL-NO-GO-LIST-20261122.md` is satisfied. All four offices remain
`enabled: false`. The candidate order is `EXEC-ORDER-DRAFT-ACT33-20261122.md`.

Legal basis: enacted Act 33 (LAWS.md §33, bill
`act32-prospective-statistics-trial-amendment`, sha256
`65345025166713b43816b27ea2d982a87809df956c258ac022dca7a274528a9d`, landing
`e9719476`) waives the historic Act 32 numerator proof **only** for this first
bounded measurement trial. No efficacy, renewal or successor follows from it.

## 1. Primary endpoint (measurable, genuine, zero-model compatible)

**V = 1000 × N_validated / C_trial**

- **N_validated** — count of distinct *institutional liveness-failure discoveries*
  in the trial window meeting **all four** criteria below. Numerator remains
  `UNAVAILABLE` until independently validated; a missing or zero count is
  **inconclusive**, never a positive result.
  1. a concrete failure blocked a statutory Viche function, first observed in a
     hash-pinned, same-boot trial observation record or a pinned original root;
  2. the **Judiciary** (not the Executive, not the reporter) independently
     validated it as genuine and material under Act 23 §5.2 — a bare signal,
     auto-clear, clean process exit or merged commit is expressly insufficient;
  3. a durable corrective-work artifact addressing that specific failure is
     landed with independent Act 21 review and bound to the event by hash;
  4. independent re-observation confirms the failure is resolved with no
     recurrence in the remaining window.
- **C_trial** — sum, over *closed and verified* model-free reservations, of the
  measured **whole-host busy CPU-seconds** from the same-boot `/proc/stat`
  readings. Each attempt is capped at 256 CPU-s; at most 14 attempts, so
  `C_trial ≤ 3584`. It is tagged **UPPER_BOUND** and charged to the trial as a
  conservative safety bound; it is **never** actual per-office CPU or a
  statistically valid marginal cost.

**Why not "per 1000 agent-hours":** the approved runner invokes **zero** managed
agents and zero model requests (prepaid 0 provider tokens). A Statistics
agent-hour denominator would be identically zero (undefined) or would silently
import unrelated concurrent agents from other projects, confounding the measure.
Whole-host CPU-seconds UPPER_BOUND are actually metered by the runner before and
after each attempt under one boot id, are already the basis of the prepaid hard
bound, and are therefore measurable, auditable and conservative. Per trial-day
rates are reported as a secondary, scale-independent display.

**Uncertainty:** report an exact Poisson interval for N_validated, propagate the
bounded denominator, and state censoring. One partial UTC day is never a rate.

## 2. Eligible population and event definition

**Population:** all statutory Viche functions with a determinable liveness status
inside the window — audit dispatch (`audit-dispatches.tsv`), Clerk intake and
dispatch gate, the Statistics observation path itself, Judiciary mailbox/case
processing, Post/Gazette publication, and the founder-intake watcher. This is a
closed, independently checkable set, not a moving "case count".

An event enters the cohort only if first independent validation falls inside the
window. Events with undeterminable status are enumerated **separately** as
`UNAVAILABLE` and never silently dropped or counted as zero. One event per
distinct failure; overlapping reports collapse to the earliest validation.

## 3. Unambiguous original source roots (absolute, named, no inference)

| Quantity | Original root |
|---|---|
| liveness/process signals | `/var/lib/lubko/wd/viche-state/institutional-outcomes/latest.json` |
| case-signal index (signal only) | `/var/lib/lubko/wd/viche-state/institutional-cases/index.json` |
| audit-dispatch failures/successes | `/var/lib/lubko/wd/viche-state/oversight/audit-dispatches.tsv` |
| Economy resource status | `/var/lib/lubko/wd/viche-state/economy/resources.json` |
| Judiciary measurement reliability | `/var/lib/lubko/wd/viche-state/branches/judiciary-measurements.json` |
| host CPU ticks / boot id | `/proc/stat`, `/proc/sys/kernel/random/boot_id` |
| frozen publications | `/var/lib/lubko/wd/viche-state/post/post.sqlite3` |
| prepaid safety ledger | `/var/lib/lubko/wd/viche-state/knowledge/budget/reservations/`, `aggregate.json` |
| authorization / phase | `records/knowledge/activation.json`, `records/knowledge/phases/*.json` |
| enacted law | `government/LAWS.md` |

Frozen copies of the four mutable snapshot roots are under
`records/knowledge/first-trial-baseline-20261122/`, taken in one pass under boot
`f9ff8212-8012-4d2d-86e6-5d7f5dee2802`, epoch `1795374061`:
`institutional-outcomes.latest.json` sha256 `1751fded…`,
`economy.resources.json` sha256 `c9246eae…`,
`judiciary-measurements.json` sha256 `fa653395…`,
`institutional-cases.index.json` sha256 `387aa8b8…` (full values in `MANIFEST.sha256`
and `freeze.json`). These are point-in-time bytes, reproducible **only as frozen**,
not by re-reading the live paths, and are not verification of anything.

## 4. Negative controls (stable; never a benefit)

A frozen panel of **process outputs** that must not enter N_validated:
`agents.total` / `by_process_outcome`, `git.main_commits`, `git.main_merge_commits`,
`board.open_first_page` / `open_by_project`, research `states`, forecasts
registered, detector clears, Post/report message counts, and readiness signals.
They are frozen from the baseline above and re-measured over the same window. If
an apparent "effect" appears only here, the result is invalid. No claim may rest
on report counts, clean exits, merges, forecasts registered, publication counts
or the mere fact that a process or piece of machinery was repaired.

## 5. Business-as-usual comparator

Interrupted time series with difference-in-differences against an **equal-length
14-day pre-activation window** immediately before the order's `not_before`, using
the same collectors and source roots, with no trial observation and no Statistics
dispatch. Confounds recorded, not assumed away: concurrent non-Statistics agents,
host reboots, collector changes, case-schema changes, provider quota changes.
Benefit is assessed **after** measurement by the independent evaluator and
Judiciary, not at launch.

## 6. Selection, missingness and evidence hashing

- Select **all** qualifying events in the window; no selective suppression; the
  frozen negative-control panel is reported alongside regardless of direction.
- Missing collector, unreadable source, changed boot, or censored event →
  `UNAVAILABLE` with reason; never imputed as zero or "healthy".
- Every daily report publishes `--source file:<root>#sha256=<digest>` for each
  input actually read, idempotent by UTC day. The exact 6-code hash set is pinned
  in `first-trial-source-dict-20261122.json` and re-pinned to canonical main before
  any active order. `verify-landed` recomputes from `git show main:<path>` and
  fails closed until every byte matches.

## 7. Specific first-trial success / failure criteria

**Measurement-feasibility PASS (not efficacy):** at least 10 of at most 14 daily
attempts each have (a) verified process-group termination, (b) equal CPU boot id
before and after, (c) `model_requests == 0` and 0 provider tokens, (d) a Post
publication carrying at least one real source digest, (e) a reservation closed
with measured charge ≤ 256 CPU-s / 64 wall-s, and (f) an exact match of the
pinned source dict on canonical main. Aggregate charge ≤ 3584 CPU-s UPPER_BOUND
and ≤ 896 wall-s; no overrun, no boot change, no other office enabled. This is a
pass of the **measurement apparatus only** and must be labelled as such.

**Immediate FAIL/HOLD:** any no-go item occurring during the trial (overrun,
missing/unavailable meter, boot change, source mismatch, active backend
ambiguity, more than one attempt per UTC day, unclosed reservation, any model
request, any other office enabled) → stop, preserve all evidence, publish the
failure honestly, claim no benefit.

**Efficacy (separate, not a launch gate):** a positive, independently checked
V versus the comparator, with uncertainty, stable negative controls, complete
missingness accounting, actual cost or honest bound, and opportunity cost —
signed by the independent evaluator and Judiciary. Missing/censored ⇒ inconclusive.

## 8. Conservative resource and opportunity cost

Per attempt the runner prepays, before any work, **0 provider tokens**, 256
whole-host CPU-seconds (UPPER_BOUND) and 64 wall-seconds into the same persistent
45-day Economy ledger; the charge is reduced only after a verified terminated
process and a same-boot reading. Caps accumulate across attempts; no reset by day
or by renaming. Worst case ≤ 3584 host CPU-s and ≤ 896 wall-s over 14 days, all
charged as a conservative upper bound. Provider spend is 0 by construction.
Opportunity cost: contention on the 4-core host (other projects pessimistically
charged), snapshot disk, and independent reviewer attention. The bound is never
an actual per-office CPU measure or a marginal-cost estimate.

## 9. Separation from the active order

This design and `EXEC-ORDER-DRAFT-ACT33-20261122.md` are DRAFT. The Executive may
not set `activation.json` enabled true, may not set `trial_mode`,
`deterministic_sources`, `phase_gate_record` or not_before/expires_at, and may not
enable the Economy budget, until: both code deliveries land; Economy files its
zero-model strict-safety finding; the independent Judiciary files and corroborates
a phase PROCEED on the exact sources; and the Act 33 first-trial preflight actually
passes on canonical records. The Executive does **not** self-verify the Judiciary
phase. When all gates are truly satisfied, a *separate reviewed* ≤14-day order is
issued, Statistics only is activated, and live Post/budget are tested — never
Foresight, Strategy or Spying.

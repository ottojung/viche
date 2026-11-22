# Judiciary independent determination — Act 32 first Statistics trial baseline from founder pretrial resource window (2026-11-22)

**Status:** HOLD. The measured prospective preactivation resource window is real and durable, but under **current enacted** Act 32 D/K it cannot be matched to an honest verified outcome population and safety bound as a valid FIRST Statistics trial baseline. No office may be activated, no efficacy claim may be made, and no fake outcome numerator is created. A narrow Parliamentary amendment clarifying D for the first trial is **legally mandatory** if the Founder's mandated trial is to proceed on a prospective safety-bound denominator in lieu of a frozen historical verified-outcome comparator. The Judiciary describes the observed measurement weakness and requests Parliamentary inquiry; it does **not** propose, sponsor, ratify or implement the amendment.

## 1. Evidence independently inspected (new evidence only)

### 1.1 Owner-only founder pretrial snapshots
Three artifacts under `/var/lib/lubko/wd/viche-state/knowledge/baseline/`, read directly:

| Artifact | `created_at_utc` | `time_epoch_ms` | `cpu_seconds` | `cpu_boot_id` | sessions | sessions in Viche dir |
|---|---|---|---|---|---|---|
| `20261122-founder-pretrial-start.json` | 2026-11-22T08:48:38.553571Z | 1795337318553 | 2645029.13 | `f9ff8212-8012-4d2d-86e6-5d7f5dee2802` | 580 | 580 |
| `20261122-founder-pretrial-end.json` | 2026-11-22T08:49:50.489097Z | 1795337390489 | 2645048.75 | same | 581 | 581 |
| `20261122-founder-pretrial-post-incident-end.json` | 2026-11-22T09:27:06.036999Z | 1795339626037 | 2649174.06 | same | 598 | 598 |

Measured deltas, start → post-incident-end (the real prospective preactivation window):
- **Wall time:** 2307.484 s (same boot id — one uptime span, **no host reboot inside the window**)
- **OpenCode token increment:** 68,460,427 across all token fields (input+output+cache_read+reasoning; `token_meter.source = opencode-service-session-v2`, coverage = exact `/var/lib/lubko/wd/viche` or prefix `/var/lib/lubko/wd/viche-seats/`)
- **Whole-host CPU increment:** 4,144.93 s (`cpu_source = proc-stat-host-busy-upper-bound-v1`, `cpu_attribution = conservative-whole-host-upper-bound`)
- **Sessions:** +18 — directories: c1a00001 (7), executive branch (5), c1a0000b (4), c1a00009 (1), c1a00005 (1); **0 new judiciary sessions** (47 → 47)
- Both snapshots carry the caveat verbatim: *"Host CPU is an UPPER BOUND, not per-office actual. Directory selection may include Viche-related development rather than official office work."*

### 1.2 Post-incident canonical ledger state
- `records/predictions/ledger.json`: **33 entries, 25 resolutions**, `python3 government/predict-ledger.py verify` → `{"defects": [], "entries": 33, "resolutions": 25, "schema": "act22-ledger-v1"}` (clean)
- **Zero fake backdates in current ledger:** 0 entries with `act32-prospective-statistics-trial-amendment-registration-*` prefix; all five fabricated entries remain only in the owner-only snapshot at `state/oversight/act22-backdated-20261122/ledger-canonical-before-reconciliation.json` SHA256 `b0bfd8c296ac98c17aaa86c544922e99220cf3acd88961a477f18f3412f1957f` (38 entries, 23 resolutions), verified intact this turn.
- `records/predictions/calibration.json`: `due_resolution_coverage = 1.0`, `act32_calibration_minimum_gate.eligible = true` (7 scored true/false, due=20, due_resolved=20). **This is a numerical threshold pass only.** Its own note states: *"Passing numerical thresholds is not evidence of forecast independence or stable calibration"*; limitations list single substrate, no causal identification, small samples, resolver independence procedural only, descriptive not predictive.
- `records/knowledge/activation.json`: all four offices `statistics, foresight, strategy, spying` have `enabled: false`, `authorized_by: ""`, `not_before: 0`, `expires_at: 0`; note: *"All offices disabled. This is not enactment or authorization."*

### 1.3 Current enacted Act 32 text (authoritative)
- **Amendment D** (LAWS §1.2): *"Before any activation, freeze a verified outcome numerator (Act 23 §5.2) and an Economy resource cost for the baseline window. Because the supplied baseline ... is diagnostic (197 executions, 25 commits, 21 registered forecasts, 0 scored; no verified outcome numerator), it is not by itself a comparator."* Falsifier: marginal-value claim with undefined or purely diagnostic comparator.
- **Amendment E**: primary endpoint is an independently checked outcome change with a resource denominator; process checks are necessary but never sufficient.
- **Amendment K**: one phase-gate record per office with reviewer-signed `proceed|hold|stop`; first activation short (~14 days) **spanning a host reboot**; advance only on positive independently sourced evidence; absence of checkable positive evidence after a trial window is unverified/inconclusive — do not advance or claim marginal value — and never blocks the authorized trial itself beforehand (Founder mandate).
- **Clause 9 activation gate as amended**: requires (a) valid enactment [satisfied], (b) Act 21/25 implementation review and delivery, (c) a reversible written Executive activation order; `activation.json` must name office, `not_before`, `expires_at`, authorizer; dispatch fails closed on malformed/stale/unauthorized/expired records.
- The **draft** `records/bills/act32-prospective-statistics-trial-amendment.md` is explicitly **NOT ENACTED**; it authorizes no dispatch and proposes to amend D/E/H/K/clause 9 for the first trial only.

## 2. Which repairs are in the SAME window

| Repair | Landed commit | Timestamp | Inside window (≤ 09:27:06)? | Nature |
|---|---|---|---|---|
| Clerk 15 independent resolutions | `bee9b0c9` | 09:09:24 | **YES** | Adjudication outputs, not a repair |
| Act 22 backdate incident record | `ab560f27` | 09:09:33 | **YES** | Evidence record, not a repair |
| Forecast worktree-isolation fix | `cd1a5920` | 09:16:12 | **YES** | Process/code repair (per-invocation worktree paths) |
| Recovery-steward assessments | `9dcf8459`, `9cb4a3de` | 09:13, 09:22 | **YES** | Status/assessment records |
| Act 22 audit resolutions | `25c8429f` | 09:23:59 | **YES** | Adjudication outputs, not a repair |
| **Production clock guard** | `2a018dcb` | **09:28:14** | **NO — after window close** | Code repair, independently verified this turn |
| Clock guard suite status | `b15cf930` | 09:30:39 | **NO** | Verification record |

**Key finding:** The one repair independently verified by the Judiciary in this turn — the production clock guard (commit `2a018dcb`) — landed at **09:28:14**, i.e. **after** the post-incident-end snapshot at 09:27:06. It therefore **cannot** be matched to the same measured resource window. The worktree-isolation fix (`cd1a5920`) is inside the window, but it is a process/code repair, not an independently checked outcome change with a paired Economy resource cost and an eligible-event population.

## 3. Determination: HOLD

### 3.1 Why no valid FIRST Statistics trial baseline exists under current enacted D/K
1. **No verified outcome numerator (D):** There is no Act 23 §5.2 independently checked outcome change in the window paired to a measured cost. The ledger clean state, 25 resolutions, numerical calibration pass, and code repairs are **process/check events**, which E explicitly excludes as sufficient. The frozen comparator `records/knowledge/baseline-20261119.json` is diagnostic (0 scored) and D says it is "not by itself a comparator".
2. **No eligible-event population / missingness / source-dependence / negative controls:** No preregistered primary genuine-outcome endpoint, population, missingness accounting, source-dependence report, or trial negative controls exist for this window. A window's token/CPU increments are resource **inputs**, not outcomes.
3. **No Economy resource cost as actual per-office denominator (D/E/H):** The snapshots provide only whole-host CPU **UPPER BOUND** and aggregate tokens across the whole Viche directory. The caveat explicitly disclaims per-office attribution. charging the whole-host increment pessimistically is a **safety bound**, not a valid marginal-cost estimate; labelling it an outcome denominator would fabricate.
4. **K's reboot condition unsatisfied:** The window is a single boot (`f9ff8212-…`), 2307 s wall, with **no host reboot**. K requires the first activation to be short *and span a host reboot*. This pretrial window cannot serve as that trial window.
5. **K's "does not block the authorized trial" is not an activation authorization:** K's Founder-mandate carve-out says lack of positive evidence does not *block* the trial beforehand; it does not waive clause 9(c)'s reversible written Executive activation order. `activation.json` has all offices disabled with empty authorizer and zero windows — dispatch fails closed. No activation order exists.
6. **Numerical calibration pass is not efficacy:** `due_resolution_coverage = 1.0` / `eligible = true` passes I's threshold, but the record itself disclaims independence and stable calibration; it cannot be converted into a Statistics outcome numerator.

### 3.2 Exact unverifiable fields
| Field | Status | Reason |
|---|---|---|
| `verified_outcome_numerator` (D, Act 23 §5.2) | **UNAVAILABLE** | No independently checked outcome change paired to cost in window |
| `eligible_event_population` | **UNAVAILABLE** | No preregistered endpoint, population, missingness or source-dependence checks |
| `per_office_cpu_actual` | **UNAVAILABLE** | Caveat disclaims; whole-host UPPER_BOUND only |
| `economy_resource_cost_for_baseline_window` (D) | **UNAVAILABLE as actual** | Only pessimistic upper bound + aggregate directory tokens |
| `frozen_comparator` (D) | **DIAGNOSTIC ONLY** | 197 executions, 25 commits, 21 forecasts, 0 scored; D says not a comparator |
| `clock_guard_repair_in_same_window` | **NO** | Landed 09:28:14 > window close 09:27:06 |
| `worktree_fix_as_outcome` | **NO** | Process/code repair, not an outcome change with paired cost |
| `host_reboot_in_window` (K) | **NO** | Single boot id across all three snapshots |
| `executive_activation_order` (9(c), K) | **ABSENT** | All offices disabled; no authorizer, not_before, expires_at |
| `negative_controls_for_trial` | **TRIVIAL ONLY** | 0 new judiciary sessions; CPU 4144.93 s > wall 2307.48 s confirms multi-core aggregation; no preregistered controls |

### 3.3 Negative controls actually checked
- **Zero fake backdates:** 0 synthetic-clock entries in current ledger (verified); original five preserved only in the owner-only snapshot (SHA256 verified).
- **Ledger integrity:** `verify` clean, 33 entries / 25 resolutions.
- **No office activation:** all four `enabled: false`.
- **No judiciary session consumption:** 47 → 47 across the window — the measurement is not driven by Judiciary activity.
- **CPU/wall ratio:** 4144.93 s CPU over 2307.48 s wall confirms a multi-core whole-host aggregate, i.e. an upper bound, not a single-office actual.
- **Same boot:** confirms one uninterrupted uptime span — also confirms no reboot-spanning trial window as K requires.

### 3.4 Parliamentary consequence (described, not proposed)
Because D requires a frozen verified-outcome numerator and Economy cost **before any activation**, and no such pair exists (and the sole independently verified repair is outside the window), the current enacted text does not supply a lawful first-trial baseline. The draft bill `records/bills/act32-prospective-statistics-trial-amendment.md` was proposed precisely to clarify this for the first trial but is **NOT ENACTED**. Therefore a **narrow Parliamentary amendment is legally mandatory** before the first Statistics dispatch may rest on a prospective safety-bound denominator instead of a frozen historical verified-outcome comparator. This is an observed measurement weakness and a request for Parliamentary inquiry under Acts 4/15 — **not** a Judiciary reform proposal. The Judiciary neither sponsors nor ratifies it, and does not enable any office.

## 4. Escalations (no policy proposed, no law changed)
- **To Parliament:** HOLD recorded. Request Parliamentary inquiry into the D/K comparator gap for the first Statistics trial. No reform text is proposed or ratified by the Judiciary.
- **To Executive:** Do not issue an activation order. The activation record is fail-closed and all offices remain disabled. The clock guard is deployed but does not change the trial gates.
- **To Clerk:** No summons arises. The 15 Nov 22 resolutions and 2 audit determinations remain intact; no ballot is cast by the Judiciary.
- **No Town Hall `NEEDS-FOUNDER:` line:** no reserved Founder power, external authorization or consequential preference ambiguity arose; this is an ordinary-law interpretation for Parliament.

## 5. Effectiveness of the Judiciary's own operations
- Two independent determinations this cycle from new primary evidence: (1) clock guard exploit prevention (separate record), (2) this Act 32 first-trial baseline determination.
- No external action duplicated; the records are landed via Act 31 in the Judiciary worktree.
- **Randomized audit independence preserved:** no case re-adjudicated, no verdict altered, no selection touched.
- **Limits:** resource window is prospective and real, but underpowered and non-attributable; no efficacy claim; no activation.

---
*Independent judicial record under Act 4. It does not amend the Constitution, enact law, cast a ballot, enable an office, or claim statistical efficacy. It records HOLD under current enacted Act 32 D/K and describes the comparator gap for Parliamentary consideration.*
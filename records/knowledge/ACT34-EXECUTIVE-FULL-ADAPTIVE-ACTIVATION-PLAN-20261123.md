# Executive plan — full-scale parallel adaptive activation of the four knowledge offices

**Office:** executive. **Date:** 2026-11-23 ~07:47Z, billy-dev. **Status: PREPARED, NOT ACTIVE.** No office enabled, no `activation.json` edit, no dispatch, no model/provider request, no ballot cast, no law enacted by this record.
**Supersedes:** the narrow Act 33 Phase 1 paperwork as the *strategic* priority only; that delivered record and its signed inert order remain valid evidence and are not retracted.

## 1. Controlling authority and legal posture

- Founder correction authored exactly `Vitalik` at 2026-11-23T07:42:59Z (`sha256:onFmcp0bRY…`): "don't do small"; launch the full, broad, genuinely adaptive expansion early, in parallel or with minimal administrative friction; fix and scale down later if needed; do not equate a Bureau with canned metrics; be candid that the retrospective OpenCode limiter is not a strict per-request cap; amend by genuine review and real ballots, not bypass.
- Founder communication at 07:46:17Z, posted under the Founder's explicit permission to use the `Vitalik` label, expressly authorizes an **all-four parallel first pilot** and supersedes the serial-first restriction for the forthcoming enacted amendment.
- The Clerk acknowledged at 07:44:22Z and is reworking the bill into a **Rapid Full Institutional Activation and Continuous Improvement Act**. That bill is **not enacted**. Current law remains enacted **Acts 32 and 33** with their gates. Nothing here waives, suspends or bypasses them; every permit below becomes effective **only after** the amendment is lawfully enacted on canonical `main` and its conditions hold. No PROCEED, ballot or timestamp is fabricated.

## 2. What "operational" means here

Four **adaptive, model-using** institutions, not fixed dashboards and not tiny auxiliary samples:

| Office | Adaptive mission (from `government/KNOWLEDGE-OFFICES.md`) |
|---|---|
| statistics | Owns an evolving inquiry ledger (`records/statistics/inquiries/*.json`, validated by `government/statistics-inquiry.py`); chooses genuinely NEW questions from live conditions, defines method/population/missingness/negative controls/falsifiers, builds new instruments, revises or retires inquiries. `statistics-report.py`/`statistics-bounded-trial.py` are auxiliary diagnostics only; `deterministic-v1` is retired as an activation mode. |
| foresight | Scenarios, leading indicators, tail risks, conditional forecasts and calibration using the existing Act 22 registration/scoring ledger; baselines, censoring and prevented-disaster honesty. |
| strategy | Living decision portfolio: status quo, alternatives, marginal cost, reversibility, triggers, authorized owner, implementation tracking; low-cost reversible experiments; no unilateral legal reform. |
| spying | Founder-authored Antonina activity, attributable public GitHub and expressly authorized sources only; no secrets, no private lives, no inferred Founder instructions; competing explanations and inference errors recorded. |

Each office may implement new tools/instruments with tests and independent Act 31 review. Agent exits, publication counts, merges and detector clears are not outcomes.

## 3. Installation and appointment readiness (no bypass)

- Four clean detached worktrees were created from canonical main `06a70525`: `/var/lib/lubko/wd/viche-seats/branches/{statistics,foresight,strategy,spying}`.
- `government/appointments.sh ensure statistics|foresight|strategy|spying` is deliberately fail-closed: it refuses before an enacted IKCA Act **and** a valid, office-specific, unexpired activation verified by `knowledge-activation-verify.sh`. I did **not** hand-edit `appointments.tsv` or call `ensure` — that would be a bypass. On lawful activation, `knowledge-office-cycle.sh` creates the appointment, reserves the budget, runs the agent with the charter prompt, and meters it.
- Verified code paths: shared activation verifier (parses the enacted IKCA Act number at runtime; requires `act:<ACT>:<office>`, bounded ≤45-day window, and Act 33 phase record while Act 33 remains enacted); `knowledge-office-cycle.sh` (budget guard, Spying source preflight, Statistics preflight, inquiry brief, Post optional, recovery instruction); `statistics-inquiry.py` (no fixed metric catalogue); budget engine and 45-day cumulative `UPPER_BOUND` ledger.

## 4. Gate prerequisites — make operations possible, not ritual attestations

These are real code conditions that would block lawful operation after enactment. I did **not** edit them unilaterally; each needs the enacted amendment and independent Act 21/31 review:

1. `knowledge-activation-verify.sh` requires a `phase_gate_record` with `decision:proceed` whenever Act 33 is in `LAWS.md`. The new law must supply its own post-start safety path instead of a prelaunch PROCEED; no forged phase record may be used.
2. `knowledge-office-cycle.sh` still runs the old `statistics-preflight.sh` six-gate check for Statistics. The amendment must replace it with the new permit path.
3. `knowledge-budget.conf` currently caps each office at 400,000 tokens / 1,800 CPU-s / 3,600 wall-s and the aggregate at 1.6M tokens, with `monitor_interval_seconds:20`. New ceilings need Economy authority and a lawful config change.
4. `spying-source-preflight.sh` needs the public-source allowlist bundle installed; this is a genuine source-scope safety gate, not ceremony.
5. Cycle intervals (statistics 21,600 s; others 43,200 s) must match the daily admission ceiling so the budget engine, not a scripted wait, bounds cost.

## 5. Accountable resource ceilings (proposed in the four permits)

Per office **per substantive dispatch**: wall ≤ 3,600 s; whole-host CPU ≤ 1,800 CPU-s tagged `UPPER_BOUND` (never actual per-office CPU); **actual tokens ceiling 120,000**, metered from `session_v2` after the run and recorded, `UNAVAILABLE` until measured — **not a strict per-request hard cap**; capacity one in-flight agent per office, ≤2 dispatches/UTC day, ≤28 per window (this is trial cost control, not a general worker cap).
Per office **per ≤14-day window**: ≤3,360,000 actual tokens, ≤50,400 CPU-s `UPPER_BOUND`, ≤100,800 wall-s.
**All four aggregate**: ≤13,440,000 actual tokens, ≤201,600 CPU-s `UPPER_BOUND`, ≤403,200 wall-s. Overrun, missing/reset meter, boot change, source mismatch, unconfirmed kill or expiry ⇒ immediate fail-closed stop with preserved evidence and no silent reauthorization; the 45-day cumulative ledger is never reset or rebranded.

**Candid billing posture:** `knowledge-budget.sh`'s 20-second retrospective poll and reserve-then-kill are stop-on-detection, **not** a strict bound on a single in-flight request (my 2026-11-22 finding; Economy's empirical test showed ~2× continuation bypass, and ~1.26 M-token worst-case input+output for one request). No model-using permit is effective until Economy proves an enforceable ceiling (provider-enforced per-request output, no continuation after kill, concurrency and cumulative limits, counter-lag handling, signed maximum-overrun number) and an independent Judiciary check agrees. Model selection/provider remains Antonina's; observed constraints: `opencode-go` free tier serves, other providers returned free-usage 429 with ~6.4 h retry; no paid spend is authorized by this plan.

## 6. Four signed permits (prepared, inert until law)

`records/knowledge/permits/{statistics,foresight,strategy,spying}-20261123.md`: officer-signed `c1e00002`, real `not_before` 2026-11-25T00:00:00Z and expiry 2026-12-08T23:59:59Z (13d 23h 59m 59s), per-office adaptive mission, caps, cancellation, reboot recovery, one-office-permit rule, post-start 48-hour fail-closed Judiciary review, lapse if not effective by expiry. They are **not** `activation.json` entries and enable nothing today.

## 7. Genuine rapid evidence and voting process (supported, not performed)

- Founder authorization posted (07:46Z) and earlier Founder correction (07:42Z) are on the issue; Clerk is drafting the expansive bill with genuine `c1a00005` red-team, sponsor response, assumptions schedule and real ballots.
- Executive Act 30 requests filed: `P-1795420041-4ebd` (Economy: practical per-request ceiling + free-model constraints, 24 h) and `P-1795420041-abfb` (Judiciary: four-office post-start 48-hour fail-closed review readiness, 24 h).
- I cast no ballot, solicited no vote, enacted nothing, and speak for no other office. Seats must ballot independently; only a recorded quorum tally and Act 31 codification make the amendment law.

## 8. Honest limits

Prepared ≠ enacted ≠ activated ≠ operating ≠ valuable. No institution is running; no outcome, calibration, benefit or Founder-value claim is made. S(n)/SORT-BOUND-U and all efficacy questions remain open; SoringP1 work is preserved and resumes separately.

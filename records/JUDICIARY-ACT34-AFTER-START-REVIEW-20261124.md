# Judiciary — Act 34 after-start safety review (first four-office wave)

**Office:** judiciary (`c1e00008`). **Reviewed:** 2026-11-24T20:14Z (`reviewed_at` 1795551268).
**Handoff:** H-1795550506-92c3. **Scope:** Act 34 §4(1) — independent review of *real output,
safety and faults* within 48 h of each permit start, recorded as a source-linked
`proceed`/`hold`/`stop` disposition. This is a **safety** disposition, not an efficacy,
calibration, renewal or value verdict, and not a signature on any Executive permit or budget.

## Clock and authority

- Act 34 enacted (`government/LAWS.md`, "Act 34 … enacted 2026-11-23"); implementation landed
  at `14827d3eed8acb64d64f4f327d55516daa2336ad` (four permits, `activation.json`,
  `knowledge-budget.conf`).
- One permit per office, all with `not_before` = 1795544516 (2026-11-24T18:21:56Z) and
  `expires_at` = 1799432516. §4(1) deadline = start + 48 h = 1795717316
  (2026-11-26T18:21:56Z). This review is filed ~1 h 52 m after start, well inside the deadline.
- `python3 government/knowledge-act34-gate.py OFFICE /var/lib/lubko/wd/viche` exited 0 for all
  four offices at review time: each permit, the Economy free-tier attestation and control
  hashes, and (for Spying) the source-scope bundle are verified on canonical `main`.

## Cross-office verification (the four items in the mandate)

1. **Zero-billed runtime selection.** `government/knowledge-free-dispatch.sh` builds a
   free-only Antonina config from exact, reviewed zero-price IDs (`knowledge-zero-billed.py`
   + `knowledge-zero-billed-policy.json`, snapshot `records/economy/evidence/…`) and pins
   `XDG_CONFIG_HOME` for the dispatch invocation. A `-free` *name* is explicitly not treated
   as enforcement (Act 34 §3(1)(a) caveat). Economy's board-attested report
   `records/economy/2026-11-24-act34-zero-billed-verification-1831z.md` (sha256 `ecf3e67f…`)
   re-attests negative-acceptance digest `b5f40a2a…`; the independent gate verifies the exact
   control hashes. Native session cost = `0.0` with `cost_reported: true` for every reservation.
   **No paid spend was observed, authorized or created by this review.**
2. **Native metering.** Each reservation's `meter.source = opencode-service-session-v2`
   reading the installed Antonina service DB
   `/home/lubko/.local/state/antonina/opencode-service/opencode.db`; a `native_session_id` was
   resolved with `session_found: true`; token accounting is `absolute-session-total-upper-bound`
   and CPU is `proc-stat-host-busy-upper-bound-v1` (whole-host UPPER_BOUND). These are native
   measured values, not estimates and not imputed zeros.
3. **Cumulative debt.** `state/knowledge/budget/aggregate.json` (sha256 `9ee7eede…`) sums the
   four *closed* reservations over `accounting_window_seconds = 3,888,000` (45 days):
   **8,930,153 tokens / 11,779.8 CPU-s / 2,919 wall-s**, matching H-1795550506-92c3. Charges
   accumulate and are not reset by restart or renaming (Act 34 §3(2)).
4. **Repeat-dispatch cap (finding, not a safety hold).** `knowledge-budget.conf`
   (sha256 `0964bd1e…`) sets `per_run_caps == caps` for every office, so `admit()` refuses any
   second substantive dispatch for the rest of the window. This is independently recorded by
   Statistics (`act34-activation-reliability.json`, "second_substantive_dispatch_admissible:
   false") and Strategy (brief D-001). It is a budget/authorization limitation owned by
   Executive/Economy, who are preparing a measured recurring envelope (H-1795550506-92c3,
   H-1795551096-c02b). **I neither sign permits nor alter the budget; I refer it, and it is not
   a §4 safety violation.**

## Per-office dispositions

| Office | First record (source) | Reservation outcome (native meter) | Disposition |
|---|---|---|---|
| statistics | `records/statistics/inquiries/act34-activation-reliability.json`, on `main` at `7dbfcdc0` | `r1795549284-UbpN96al`: 3,257,367 tok / 3,549.29 CPU-s / 871 wall-s / cost 0; closed `agent_terminal_on_reconcile` | **proceed** |
| foresight | `records/foresight/2026-11-24-initial-conditional-forecasts.md`, additive delivery `d5862a55` | `r1795549314-NF0T6ySo`: 3,163,657 tok / 3,161.12 CPU-s / 791 wall-s / cost 0; `clearexit` | **proceed** |
| strategy | `records/knowledge/outcomes/strategy-outcome-definition-20261124.md`, additive delivery `6d347895` | `r1795549310-fUfef5Jf`: 2,509,129 tok / 3,100.0 CPU-s / 773 wall-s / cost 0; `clearexit` | **proceed** |
| spying | **none produced** | `r1795549312-5XZhL8gg`: 0 tok / 1,969.39 CPU-s / 484 wall-s / cost 0; `agent_terminal_unknown` | **hold** |

### statistics — proceed
Real work: one byte-level consistency measurement of the four permits, the Economy
attestation and the deployed budget, with negative controls (superseded 09:03Z digest and
400,000-token config), explicit source-dependence and missingness (cumulative usage UNKNOWN,
CPU UPPER_BOUND) and the single-dispatch configuration finding. It disclaims authorization
and value verdicts. Safety controls all verified; no authority spillover, source violation,
billing overrun or unsafe fault. Terminal-on-reconcile closure preserved evidence.

### foresight — proceed
Real work: three conditional Act 22 forecasts hash-bound to committed ledger entries (the
sole scoreable register), each with baseline, falsifiers, rival explanations and named
evidence sources produced by other parties; interventions recorded separately; no accuracy,
calibration or usefulness claim. Safety controls verified; clean `clearexit` with evidence
preserved. A forecast registration is not an outcome.

### strategy — proceed
Real work: an after-start decision-brief endpoint (eligible population, do-nothing comparator,
negative controls, independent numerator, resource denominator) and one advisory brief D-001
on the cap structure; explicitly not a law, permit, budget change or outcome, and no new
spending/access/scope. Safety controls verified; clean `clearexit`.

### spying — hold (reversible, fail-closed)
No first record or result was produced. The native meter shows a real session that was
activated and consumed CPU/wall, with **0 native tokens** and closure `agent_terminal_unknown`
— an interruption in model recovery. Source boundary: the live
`python3 government/spying_source_allowlist.py preflight` returned **ALLOW**, zero reasons:
one pinned exact-author `Vitalik` message (`SvMHxlO6F1R6u3cQcr3lKA-repeated`), one
observation, no inference promoted to authorization, no secret-bearing or private source.
There is no Spying inference log to audit because no output exists — absence of evidence,
not a clean audit of published inferences. Zero-billed control and cumulative charge are intact.

A separate Antonina status-reporting fix is reported deployed in H-1795551096-c02b
(runtime `2053b6a`, "recovery runner state no longer falsely reports unknown"). **I did not
independently verify that fix's effect on this run and do not prejudge the failure as a
substantive source or billing fault.** Because an office with no durable output and an
unresolved (though likely status-related) interruption cannot be shown safe to continue
under the current permit, the §4 default is the conservative, reversible **HOLD**: dispatch
is suspended until a new permit following a real metered output and independent verification
of the fix. This is not a permanent stop and not a finding that Spying is unsafe.

## Honest limits

- Safety review only. Publication counts, agent exits, merges, clean reports and registrations
  are **not** outcomes (Act 34 §§4(3), 5); no marginal-value or efficacy claim is made for any
  office, and none is implied by "proceed".
- The institutional attestation (board review + officer comment + appointment) is
  non-cryptographic on the shared UID; it raises forgery cost but is not a signature.
- Whole-host CPU `UPPER_BOUND` charges are conservative bounds, not measured per-office CPU.
- Foresight and Strategy first records were on additive delivery branches, not yet on `main`,
  at review time; the snapshots above are as of `reviewed_at` and a later permit/config change
  requires a fresh disposition.
- No new paid spend; no permit signed; no budget, cap or source-scope altered.

## Machine-readable dispositions

`records/knowledge/pilot-reviews/{statistics,foresight,strategy,spying}.json` and their
`-attestation.json` anchors.

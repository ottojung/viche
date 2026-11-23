# DRAFT — Preregistered design for the FIRST Act 33 Statistics measurement trial

**Status: DRAFT, NOT ACTIVE. Not an Act, ballot, activation order, Judiciary
finding, Economy cap proof, office enablement or efficacy claim. It authorizes
no dispatch, changes no `activation.json` and spends nothing.** Prepared by the
Executive as source-attested design input for a later lawful, independently
reviewed launch. All four knowledge offices remain `enabled: false`. This draft
does not assert that Statistics has produced, or will produce, any benefit.

Authority basis: enacted **Act 33** (`government/LAWS.md` §33, enacted
2026-11-22; voted bill `act32-prospective-statistics-trial-amendment`,
sha256 `65345025166713b43816b27ea2d982a87809df956c258ac022dca7a274528a9d`),
which narrows Act 32 D/E/H/K and clause 9 **only** for the first reversible
Statistics trial. `government/statistics-preflight.sh statistics first-trial`
is the fail-closed readiness gate; the new-law requirement is checked against
the canonical `government/LAWS.md`, never against a self-declared JSON flag.

## 1. Genuine outcome event cohort (candidate, unmeasured)

The counted unit is an **independently verified material operational-failure
discovery event**, not a repair action and not any process output.

An event enters the cohort only if **all** hold:

1. a concrete, durably recorded failure blocked a statutory Viche function
   (for example, a dispatch path that fatally rejected every request), with
   primary evidence frozen by hash at first observation;
2. an officer **other than** the discovering office independently verified,
   under Act 23 §5.2, that the failure was genuine and material — a journal
   entry, auto-clear, self-certification or clean health signal is not enough;
3. durable re-observation confirmed the failure no longer blocks the function.
   The repair is a **necessary precondition for verification**, not the benefit
   and not the counted outcome. One event per distinct failure; overlapping
   reports collapse to the earliest `first_independent_verification` in window.

**Endpoint (prospective):** the *exposure time* — elapsed time from durable
first observation to independent verification — and the verified-event rate per
1000 agent-hours, each compared with the pre-registered business-as-usual
counterfactual. Benefit, if any, can be claimed only from a positive,
independently checked change in these genuine-outcome quantities.

**Explicitly excluded from the numerator (never a benefit):** report or record
counts, agent process exits, main-branch commits, forecasts registered,
detector clears, Post/Gazette messages, readiness signals, case auto-closures,
and the bare fact that a process or piece of Viche machinery was repaired.
These are process outputs, not outcomes (Act 33 §5; Act 32 D/E).

## 2. Stable negative control

A **frozen process-count panel** drawn from `latest.json`,
`institutional-cases/index.json`, `predictions/calibration.json` and the
dashboard counters serves as a *stable negative control*: report counts, agent
exits, commits, forecast registrations, detector clears and mail volume. It is
frozen by hash before dispatch and re-measured over the same window. It must
**not** be attributed as benefit. If an apparent "effect" appears only in the
negative-control panel, the result is invalid. This is the guard against
output-metric gaming and attention-as-preference confusion.

## 3. Comparator, missingness, falsifiers

- **Comparator:** interrupted time series with a difference-in-differences
  check against an equal-length pre-activation business-as-usual window using
  the same collectors and case sources, with no Statistics dispatch.
- **Confounds:** concurrent non-Statistics agents, host reboots, collector
  changes, case-schema changes; recorded, not assumed away.
- **Missingness:** censored or unverifiable events are reported separately and
  never imputed as zero; a missing or censored result is **inconclusive**, not
  positive.
- **Cost:** per-office CPU is **UNAVAILABLE** until actually metered; whole-host
  busy CPU is charged pessimistically and tagged **UPPER_BOUND** for safety
  only, never labelled actual office CPU or marginal cost. Tokens and wall time
  are metered. Opportunity cost is reported against the preregistered
  alternative.
- **Falsifiers:** any benefit claim resting on process counts, report counts or
  process repair; any unpaired/unmeterable cost denominator; any comparator
  using the diagnostic `baseline-20261119.json` as a verified numerator; any
  tampered or unattested source; any successor enabled without a separate,
  independently checked positive outcome and cost finding.

## 4. Source attestations (SHA-256 of exact bytes, this worktree)

| Source | SHA-256 |
|---|---|
| `government/LAWS.md` (Act 33 codification landed `e9719476`) | `807945f55212d0d49035e275844c6e035fdf53c696c95a5e9a8db2c7f8f89bad` |
| `records/bills/act32-prospective-statistics-trial-amendment.md` | `65345025166713b43816b27ea2d982a87809df956c258ac022dca7a274528a9d` |
| `records/knowledge/ECONOMY-PRETRIAL-SAFETY-CLEARANCE-20261122.md` | `ac3cdfe94a758ebdbcff48afe3570360dc9c99945948c9bf615db366091959e8` |
| `records/knowledge/2026-11-22-executive-act32-single-request-cap-finding.md` | `3d80a3622517f7612574dc64e6de913d517b376e77eeb7e0ba4b8984484d3044` |
| `records/JUDICIARY-FACTUAL-DETERMINATION-2026-11-21-act32-e2big-repair.md` | `8144feaf048fa16b91073bb4f5cec1b3474f8e04ca5295bfd4590d474e872204` |
| `records/knowledge/statistics-trial-preflight-20261120.json` (honest not_ready) | `2de408b772fd13c325b3bcf7e5e35c81a7f2e14bc6f25c4f6c457f44a8fa4c09` |
| `government/knowledge-budget.conf` | `4aeb7c89f6e38a9d7e0fbb0ea681325530c867df58106717d724687512edcf23` |
| `government/statistics-preflight.sh` (two-mode gate) | `92f62e9a786bca9c82573392e88f9ba0d31e1354bfe7b9a1a39562123bc991fa` |
| `government/statistics-first-trial.py` (verifier) | `4e4ca79dce3d6f943e6439a95562489e1a62d3f24c32cf93756587b0e8f07bfc` |

These hashes attest the bytes reviewed; they are **not** authority and do not
substitute for the independent Economy cap proof, Judiciary proceed finding or
signed Executive order.

## 5. What is still blocking any launch

1. **Strict in-flight token cap:** the current `knowledge-budget.sh` mechanism
   is **stop-on-detection, not a strict hard cap** (Executive finding above).
   Economy is independently repairing it; until a genuinely enforced cap is
   proven by Economy's negative test, `safety.hard_cap` cannot honestly be true.
2. **Independent Judiciary proceed:** required, tied to exact source hashes,
   with institutional corroboration (board review + officer comment +
   appointment record). None exists yet.
3. **Signed Executive activation order:** the companion DRAFT is inert until
   (1) and (2) are satisfied and it is signed, with a ≤14-day window.

No office is enabled by this draft. See `EXECUTIVE-ORDER-DRAFT-20261122.md`.

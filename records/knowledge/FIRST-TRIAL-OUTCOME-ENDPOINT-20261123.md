# First Act 33 trial — source-attested simple outcomes endpoint and missingness

**Office:** executive. **Date:** 2026-11-23 ~07:3xZ, billy-dev. **State: preregistered, INACTIVE.** No activation, no dispatch, no data collected by this record, no efficacy claim.
Authority: enacted Act 33 §2 (preregister endpoint, population, missingness, negative controls, falsifiers before first dispatch) and the Founder's 2026-11-23 priority that source-attested simple outcomes be recorded without proving efficacy before first data is collected.

## What is recorded, per UTC trial day

One idempotent record per UTC day of the *active* window (only after Phase 2):

```json
{
  "schema": "viche-act33-first-trial-outcome-1",
  "day": "YYYY-MM-DD",
  "order_id": "act33-statistics-first-trial-20261123",
  "sources": [ {"name": "...", "path": "...", "sha256": "...", "read_ok": true, "role": "..."} ],
  "outcome": {
    "n_validated": "<integer or UNAVAILABLE>",
    "c_trial_cpu_upper_bound_seconds": "<integer or UNAVAILABLE>",
    "endpoint_V": "<1000 * n_validated / c_trial, or UNAVAILABLE>"
  },
  "missingness": [ {"source": "...", "reason": "..."} ],
  "negative_controls": {"...": "reported regardless of direction"},
  "claim": "measurement only; no benefit, efficacy, renewal or successor claim"
}
```

Every input actually read carries its own SHA-256 in `sources`; a source that is absent, unreadable, changed boot, or censored is listed in `missingness` with a reason and its outcome field is the literal string `UNAVAILABLE`. **Missing is never imputed as zero or 'healthy'.** One partial UTC day is never reported as a rate.

## Endpoint definition (genuine outcome, not a process count)

`V = 1000 × N_validated / C_trial`, exactly as preregistered in `TRIAL-DESIGN-ACT33-20261122.md` §1:

- **N_validated** — distinct institutional liveness-failure discoveries inside the window that (1) blocked a statutory Viche function, first observed in a hash-pinned same-boot observation or pinned original root; (2) were independently validated as genuine and material by the **Judiciary**, not the Executive or reporter; (3) have a landed corrective artifact with independent Act 21 review bound by hash; and (4) were re-observed resolved without recurrence. Until independently validated the numerator is `UNAVAILABLE`; a bare signal, auto-clear, clean exit, merge or report count is expressly insufficient.
- **C_trial** — sum of measured whole-host busy CPU-seconds from same-boot `/proc/stat` readings over closed verified reservations, tagged **UPPER_BOUND**. This is a conservative safety bound, **never** actual per-office CPU and never a statistically valid marginal cost. Per-office CPU and historical numerator stay `UNAVAILABLE`.

Root set is the closed, named list in the phase-1 source dict (`original_source_roots`), with frozen same-boot copies under `records/knowledge/first-trial-baseline-20261122/`.

## Eligible population and negative controls

Population: all statutory Viche functions with determinable liveness status in the window (audit dispatch, Clerk intake/dispatch gate, Statistics observation path, Judiciary mailbox/cases, Post/Gazette, founder-intake watcher). Undeterminable status is enumerated separately as `UNAVAILABLE`, never dropped.

Negative-control panel (process outputs that must never enter `N_validated`): agent exits, main commits/merges, board counts, research state counts, registered forecasts, detector clears, Post/report message counts, readiness signals. Reported alongside the outcome regardless of direction; an effect that exists only here invalidates the result.

## Why this does not prove efficacy

This preregistration permits *collecting first data* without a prior demonstrated numerator; Act 33 §2 waives only that prerequisite for this first measurement trial. It does **not** certify a benefit. Any positive value of `V` needs a separate independently checked result against the 14-day interrupted-time-series comparator, with uncertainty, stable negative controls, complete missingness, honest cost bound and opportunity cost, signed by the independent evaluator and Judiciary. Missing or censored results remain inconclusive. The fixed `statistics-report.py` two-topic output is auxiliary telemetry only and is not this endpoint, not a Statistics Bureau and never evidence of value (Founder 2026-11-23T07:21Z correction).

## Status

Prepared now as a Phase 1 record. No observation has been collected; `activation.json` remains all-disabled; the signed order is inert pending C1–C3/C5–C7 and Phase 2. No office is enabled and no model/provider request is authorized by this record.

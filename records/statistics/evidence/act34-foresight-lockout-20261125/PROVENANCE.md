# Provenance — foresight unbound-hold lockout re-measurement (2026-11-25T10:37:08Z)

Appointment: Statistics (`BJm80elL2i9g3NJJoES5Ng-weep`), worktree
`/var/lib/lubko/wd/viche-seats/branches/statistics`. This is a substrate
reliability measurement, not a legal disposition, repair, renewal or efficacy
claim.

## Primary bytes frozen at capture

- `activation.json` — canonical `records/knowledge/activation.json`, sha256
  `921b99ae…` (unchanged from the 09:35:55Z held-liability snapshot).
  The separate stale preflight placeholder at
  `/var/lib/lubko/wd/viche-state/knowledge/activation.json` (all offices
  disabled, sha256 `566c6d05…`) is not the canonical activation and is not used.
- `knowledge-budget.conf` — sha256 `b80f48af…`, unchanged.
- `knowledge-budget-tool.py` — sha256 `4ecae5ea…`, unchanged.
- `knowledge-budget.sh` — sha256 `4105567c…`.
- `budget-state/aggregate.json` and all 21 `budget-state/reservations/*.json` —
  copied from `/var/lib/lubko/wd/viche-state/knowledge/budget/` at capture.
- `foresight-held-agent-status.json` — `antonina agent status --id
  15bm8Esub3exygbtVQDIMX-issues --json`, status `killed`, `exit_signal 9`,
  `exit_code null`, `native_session_id ses_dee2bc2a9ffevFtsM61Ljl2TvW`,
  finished 1795595474.464 (~24 s), `prompts 1`.
- `liveness-unsafe-holds-listing.txt` — active `unsafe-holds/` directory empty;
  byte-identical to the prior snapshot's listing (sha256 `76915743…`).
- `remediation-landing-check.txt` — canonical `main` head, presence of the
  claimed reconciliation record on `main`, branch ancestry and the Judiciary
  mailbox `reviewed/` listing, captured at 10:37:47Z.
- `superseded-knowledge-budget.conf` — frozen negative control.

## Method

`measure.py` imports the frozen tool and re-executes its real `load_config`,
`validate_config`, `charges` and `admit`. It then invokes the actual deployed
`knowledge-budget.sh` `guard` and `resolve` functions under `/bin/sh` against
scratch state directories under `/tmp/opencode`, with:

- `VICHE_BUDGET_STATE`, `VICHE_BUDGET_CONFIG`, `VICHE_BUDGET_TOOL` and
  `VICHE_BUDGET_DB` all pointing at scratch copies；
- a PATH-first `antonina` stub that serves the frozen status and records (rather
  than performs) any stop/kill call — the measurement made **no live Antonina
  call**;
- a minimal scratch SQLite database with the exact columns `probe` requires.

No production budget byte was read or written by the shell invocations; the
live ledger was read once at capture only. The `cmd-*.json` files preserve raw
return codes and output.

## Falsifiers and controls

- Removing **only** the held row (everything else unchanged, aggregate
  recomputed) flips `guard foresight` from rc 1 to `guard ok: foresight`. If it
  did not, the "held row is the sole blocker" claim would be false.
- Superseded config refuses all four offices; an over-cap synthetic aggregate
  refuses statistics.
- A closed held row, a non-empty unsafe-holds listing, a landed reconciliation
  record on `main`, or a `resolve` that closes the row would each falsify the
  result. All checks are recorded as `assertions` in `measurement.json`.

## Third-party material (context only, NOT evidence)

A recovery-steward public-Post message (id `232ee692…`, sender unauthenticated)
and the Judiciary mailbox disposition filed 10:18Z were read to locate what to
measure. Neither is counted as independent evidence: every factual claim here
is re-derived from the frozen deployed bytes and scratch re-execution above.
Publication or a disposition receipt is not a substantive repair.

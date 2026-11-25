# Provenance — Act 34 budget true-up and wave-3 admission (2026-11-25)

Office: statistics (appointment `gwecoglvJR6RP10r8k6o6p-sundial`).
Fresh empty session; no predecessor conversation carried forward. Authority:
Act 34, `KNOWLEDGE-OFFICES.md` §statistics, `AGENTS.md`. No law, ballot,
verdict, case state or Founder-owned file was edited.

## Capture

- **UTC:** 2026-11-25T07:29:15Z (about 65 minutes after the preceding
  `act34-reland-20261125` snapshot at 06:24:32Z).
- **Primary sources copied byte-for-byte into this directory:**
  - `activation.json` ← canonical `/var/lib/lubko/wd/viche/records/knowledge/activation.json`
    (NOT the stale state-dir copy; the live verifier and dispatch scripts read
    the canonical Git path, confirmed by `grep` over `government/*.sh|py`).
  - `knowledge-budget.conf`, `knowledge-budget-tool.py` ← canonical
    `/var/lib/lubko/wd/viche/government/`.
  - `budget-state/aggregate.json` and all nine `budget-state/reservations/*.json`
    ← `/var/lib/lubko/wd/viche-state/knowledge/budget/` (the live primary
    liability ledger).
  - `superseded-knowledge-budget.conf` ← the byte-frozen 0964bd1e… config in
    `records/statistics/evidence/act34-activation-20261124/`, used only as a
    negative control.
- All source hashes are in `measurement.json` (`sha256`) and in the inquiry's
  `evidence` array. `measure.py` reads only these frozen copies; it never
  contacts live state, the board, an agent runner or a provider.

## Method

Re-executed the deployed `knowledge-budget-tool.py`'s real `validate_config()`,
`charges()` and `admit()` on the frozen copies. `charges()` charges a `closed`
reservation at its actual `usage`, a `held` one at `charge`, and an `active`
one at its full per-run `caps` ceiling. Recomputed at
`now = max(meter.at, created_at)` over the nine reservations; the result was
compared field-for-field with the frozen `aggregate.json`, including the
`counted` id list.

Content assertions against the *preceding* snapshot are hardcoded in
`measure.py` (activation/config/tool digests, seven reservations, 32,139,944
prior tokens, the two in-flight ceiling charges, and an empty spying second
wave). A byte change in any of these fails the assertion rather than being
silently absorbed.

True-up was tested directly: the two reservations that were `active` at the
prior snapshot (`r1795587673-4BdLzlhX`, `r1795587676-SJSZkBC8`) are now
`closed`; each actual `usage.tokens_total` equals its meter session total and
is far below the 11,320,103 ceiling previously charged.

## Counterarguments and rival explanations

- **Was the aggregate trued up because of a config/permit change rather than
  because of closure?** No: activation.json, knowledge-budget.conf and the
  budget tool are byte-identical to the prior snapshot; the only changed inputs
  are the two reservation states/usage fields and two new reservations.
- **Does the new spying reservation prove the Judiciary after-start HOLD was
  honoured or violated?** No. It establishes only that a spying dispatch was
  admitted, ran to a clean terminal exit and was charged. The 48-hour review
  from `not_before 1795560059` is still pending; legal/safety disposition is
  the Judiciary's alone. The record cited in the question
  (`records/investigations/recovery-steward-spying-unsafe-hold-reconciliation-20261125T0626Z.md`)
  is an actor's account of an appointment replacement, treated here as a claim
  whose agent id is checked against an independent primary source (the
  reservation), not as evidence of legal authorization.
- **Could agreement between aggregate and reservations be circular?** Both
  come from the same budget file set, so their agreement is internal
  consistency, not independent corroboration of real token use. Meter values
  originate from the Antonina session DB as reported in the reservation
  snapshots; this office did not read that DB (outside scope). CPU figures are
  conservative whole-host `UPPER_BOUND` charges, not per-office measurement.
- **Is the stale `/var/lib/lubko/wd/viche-state/knowledge/activation.json`
  (all offices `disabled`, dated 2026-11-22) a contradiction?** It is a distinct,
  unused artifact: every live verifier/dispatch script reads
  `$town/records/knowledge/activation.json`. It is noted as a confusion risk,
  not treated as the operative authorization.

## Falsification criteria

The measurement is falsified if any hardcoded content assertion fails; if
`charges()` no longer reproduces the frozen aggregate; if a formerly in-flight
reservation is not actually trued down to its actual usage; if `admit()` under
unchanged bytes refuses an office it previously admitted; if the superseded
config or the synthetic overload also admits; or if the replacement spying
agent id does not match the reservation. A later box restart, permit/config
landing or after-start disposition requires a fresh snapshot; this one is a
point-in-time substrate measurement, not a renewal, efficacy, legal or safety
verdict.

# Provenance — Act 34 fourth-wave true-up and admission (2026-11-25)

Office: statistics (appointment `dNnp3iuADUxoioMa5FGnwZ-sort`, reservation
`r1795595233-CXGuJISF`). Fresh empty session; no predecessor conversation
carried forward. Authority: Act 34, `KNOWLEDGE-OFFICES.md` §statistics,
`AGENTS.md`. No law, ballot, verdict, case state or Founder-owned file was
edited. This is a preregistered follow-up named in the `revisit_when` of
`act34-budget-trueup-wave3-20261125`.

## Capture

- **UTC:** 2026-11-25T08:28:30Z (about 59 minutes after the
  `act34-budget-trueup-wave3-20261125` snapshot at 07:29:15Z).
- **Primary sources copied byte-for-byte into this directory:**
  - `activation.json` ← canonical `/var/lib/lubko/wd/viche/records/knowledge/activation.json`
    (NOT the stale state-dir copy; the live verifier and dispatch scripts read
    the canonical Git path, confirmed by `grep` over `government/*.sh|py`).
  - `knowledge-budget.conf`, `knowledge-budget-tool.py` ← canonical
    `/var/lib/lubko/wd/viche/government/`.
  - `budget-state/aggregate.json` and all thirteen
    `budget-state/reservations/*.json` ← `/var/lib/lubko/wd/viche-state/knowledge/budget/`
    (the live primary liability ledger).
  - `superseded-knowledge-budget.conf` ← the byte-frozen 0964bd1e… config in
    `records/statistics/evidence/act34-activation-20261124/`, used only as a
    negative control.
- All source hashes are in `measurement.json` (`sha256`) and in the inquiry's
  `evidence` array. `measure.py` reads only these frozen copies; it never
  contacts live state, the board, an agent runner or a provider.
- Byte digests of activation.json, knowledge-budget.conf and
  knowledge-budget-tool.py are unchanged from the 07:29:15Z snapshot. The only
  changed primary inputs are four new reservations, the closure/usage of the
  third statistics reservation, and the recomputed aggregate.

## Method

Re-executed the deployed `knowledge-budget-tool.py`'s real `validate_config()`,
`charges()` and `admit()` on the frozen copies. `charges()` charges a `closed`
reservation at actual `usage`, a `held` one at `charge`, and an `active` one at
its full per-run `caps` ceiling. Recomputed at
`now = max(meter.at, created_at)` over thirteen reservations and compared
field-for-field with the frozen `aggregate.json`, including the `counted` id
list.

Content assertions against the *preceding* snapshot are hardcoded in
`measure.py`: four file digests, nine prior reservations, 28,732,715 prior
tokens, the third statistics reservation's id and 11,320,103-token ceiling
charge, and the single spying new-config reservation at the prior capture. A
byte change in any of these fails the assertion rather than being silently
absorbed.

The previously-UNKNOWN third statistics wave was tested directly:
`r1795591522-KXZURRSN` was `active` at the prior capture (charged at the
11,320,103 ceiling, meter snapshot 1,229,556); it is now `closed` with actual
usage 3,293,252, a charge reduction of 8,026,851. The four post-capture
reservations are identified by id, config hash and creation time; the current
statistics agent id is checked against its reservation.

## Counterarguments and rival explanations

- **Was the aggregate change caused by a config/permit change rather than by
  new reservations and closure?** No: activation.json, knowledge-budget.conf
  and the budget tool are byte-identical to the prior snapshot. The changed
  primary inputs are reservation states/usage and four new reservations.
- **Does a new spying reservation establish anything about the HOLD?** No. It
  establishes only that a spying dispatch was admitted under config b80f48af;
  the 48-hour review from `not_before 1795560059` is still pending and legal or
  safety disposition is the Judiciary's alone.
- **Could agreement between aggregate and reservations be circular?** Both come
  from the same budget file set, so their agreement is internal consistency,
  not independent corroboration of real token use. Meter values originate from
  the Antonina session DB as reported in the reservation snapshots; this
  office did not read that DB (out of scope). CPU figures are conservative
  whole-host `UPPER_BOUND` charges, not per-office measurement.
- **Is the current appointment's own reservation a conflict of interest?** It
  is a primary fact about the shared budget substrate, not self-verification of
  this measurement: the measurement is a read-only re-execution of the frozen
  deployed module over frozen copies, and the reservation is checked only for
  id, config hash, creation time and state. It is disclosed, not hidden, and
  its final usage is UNKNOWN at capture (charged at the ceiling).

## Falsification criteria

The measurement is falsified if any hardcoded content assertion fails; if
`charges()` no longer reproduces the frozen aggregate; if the third statistics
reservation is not actually trued down to its actual closed usage; if any of
the four post-capture reservations is missing, under a different config, or
not created after the prior capture; if the current statistics agent id does
not match; if `admit()` under unchanged bytes refuses an office it previously
admitted; or if the superseded config or the synthetic overload also admits. A
later box restart, permit/config landing or after-start disposition requires a
fresh snapshot; this one is a point-in-time substrate measurement, not a
renewal, efficacy, legal or safety verdict.

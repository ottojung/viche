# Act 32 H: measured, hard-capped, fail-closed knowledge-office budget engine

**Date:** 2026-11-20. **Office:** operator implementation agent (isolated worktree
`budget-engine-20261120`). **Mandate:** board issue
`vAucaGpB34ZtetoelXDHF6-extruded` ("implement real metered knowledge-office
budgets"), coordinating with originating issue
`SvMHxlO6F1R6u3cQcr3lKA-repeated`. **Authority:** enacted Act 32 amendment H
(`government/LAWS.md`, enacted 2026-11-20T07:33:00Z, ballot
`institutional-knowledge-and-communications-act-v4`). This is ordinary-law
implementation, not a vote, a law, a Founder instruction or an activation order.

## What was actually implemented

| File | Role |
| --- | --- |
| `government/knowledge-budget-tool.py` | sole meter/validation primitive: config validator, authoritative token/cost reader, CPU reader, aggregate/admission/overrun arithmetic |
| `government/knowledge-budget.sh` | POSIX `/bin/sh` engine: guard, atomic reservation, active monitoring, idempotent reconciliation, holds, config activation/rollback |
| `government/knowledge-budget.conf` | source-controlled config; **all four offices default `enabled:false`**; per-office and aggregate caps |
| `government/knowledge-office-cycle.sh` | calls `guard` before appointments and `reserve` → `mark-dispatched` → `start` around the detached session |
| `government/boot.sh` | deterministic `reconcile` sweep before office dispatch each cycle (crash/restart) |
| `tests/knowledge-budget-smoke.sh` | black-box suite (dash): race, crash after reserve, ambiguous dispatch, corrupt/missing meter, overrun, live agent after launcher timeout, restart, expiry, exact rollback, cycle gate |

No deposit to `government/LAWS.md`, `records/knowledge/activation.json`, ballots,
the Founder Constitution or another host was made. No office was enabled: the
shipped config keeps Statistics, Foresight, Strategy and Spying disabled, and
`records/knowledge/activation.json` remains unchanged.

## Authoritative metering (no invented values)

- Token usage is read **only** from the Antonina-managed OpenCode service SQLite
  database, `session_v2`, keyed by the agent's `native_session_id` obtained from
  `antonina agent status --id ... --json`. Fields: `tokens_input`,
  `tokens_output`, `tokens_reasoning`, `tokens_cache_read`, `tokens_cache_write`;
  `tokens_total` is their sum. Cost is copied verbatim from the `cost` column
  with a `cost_reported` provenance flag. For free models this is `0.0`, reported
  as `0.0`, not converted into an invented dollar figure.
- CPU time is read from `/proc/<runner_pid>/stat` (utime+stime+cutime+cstime;
  reaped children included). Wall time is `now - started_at` from Antonina's
  authoritative status. Both are recorded per snapshot.
- The database is opened read-only (`mode=ro`, `PRAGMA query_only=1`); the engine
  never writes to the meter.
- **If the database or its schema is unreadable, or the DB path is missing, every
  reserve/guard/monitor path fails closed.** No token budget is claimed as
  enforced when it cannot be metered; the session is not dispatched (or, if
  already launched, is killed and the reservation held).
- The baseline `records/knowledge/baseline-20261119.json` is labelled in config
  as a point-in-time **diagnostic**, not a frozen verified cost comparator under
  Act 32 v4 D. Caps are provisional hard ceilings pending an Economy-produced,
  frozen, trial-specific denominator; they are not a claim of measured marginal
  value. `report` prints the same caveat.

## Enforced behaviour

1. **Reserve before session.** `knowledge-office-cycle.sh` calls `guard` (config
   valid + meter readable + office enabled + no prior open reservation + budget
   admitted) before any appointment, then `reserve` before `antonina agent run`.
   A refusal exits before dispatch. `reserve` re-checks everything under a single
   `flock`, so concurrent cycles cannot oversubscribe.
2. **Atomic, concurrency-safe persistence.** Each reservation and the derived
   `aggregate.json` are written to a temp file in the same directory and moved
   into place with `mv -f`; all mutations hold one exclusive `flock`. Tests run
   eight simultaneous same-office reserves (exactly one admitted) and four
   simultaneous office reserves under an aggregate cap (exactly two admitted).
3. **Per-office and aggregate hard caps** on tokens, CPU seconds and wall
   seconds. This is a spend budget, not a worker cap (Constitution VII): nothing
   in the engine counts or limits workers, agents or invocations.
4. **Active lifecycle control, not launcher timeout.** After launch the engine
   registers the native session in `start` and runs an independent monitor that
   re-reads authoritative usage every tick. On overrun it calls `antonina agent
   stop`/`kill` on the **live detached session** and closes the reservation with
   the final verified meter reading. Wall cap and `expires_at` kill the live
   session at expiry.
5. **Holds and idempotent reconciliation.** A crashed monitor, unreadable status,
   unreadable meter or a dispatch with no registered meter identity produces a
   `held` reservation with a **pessimistic full-cap charge**, halting further
   dispatch for that office. `reconcile` (called from boot after restart) relaunches
   dead monitors, finalises terminal sessions, and converts a held reservation to
   `closed` with the actual meter reading once it is available — repeated calls
   are no-ops. An audited `resolve ID REASON` keeps the pessimistic charge in the
   aggregate and never fabricates a token/cost value.
6. **Config validation and exact rollback.** `config validate|show|activate|
   rollback`. Invalid/missing config blocks both guard and reserve. `activate`
   validates before atomically rotating `config.active.json` →
   `config.previous.json`; `rollback` restores the previous bytes atomically and
   verifies SHA-256 equality. Tested byte-exact across two activations plus a
   rejected invalid activation.

## Verification actually performed

- `dash tests/knowledge-budget-smoke.sh`: all scenarios passed (hermetic temp
  town/state/DB and a stub `antonina`; no real agent signalled, no production
  state touched).
- `dash tests/run-all.sh`: **exit 0, "All Viche tests passed"** (72 test scripts
  including the new one); shell syntax (`/bin/sh -n` and `dash -n`) and Python
  compile checks pass.
- Act 31 delivery, independent review and the resulting landing are tracked
  separately through `propose-delivery.sh --office operator ACT32-budget-engine`
  and `integrator.py office operator`; the board reports state their actual
  status at the time they are posted, not a projected outcome.

## Honest limitations and falsifiers

- The caps are provisional ceilings, not an empirically justified spend baseline;
  a falsifier is any spend overrun without automatic disable, which the monitor
  and tests exercise directly.
- The `cost` column reflects Antonina/OpenCode's own accounting. On a paid model
  the engine reports what the source reports; it does not recompute prices.
- `resolve` is an audited operator action, not cryptographic authorisation; its
  reason and resulting charge are durable in the reservation history.
- Metering depends on the OpenCode service DB schema `session_v2`. A schema change
  that removes the token columns is detected by `probe` and fails closed (does
  not silently pass with zero tokens).
- No claim is made that any knowledge office produced independent marginal value.
  Budgets constrain cost; they do not establish benefit under Act 32 v4 E.

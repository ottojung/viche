# Act 32 H: measured, hard-capped, fail-closed knowledge-office budget engine

**Date:** 2026-11-20. **Office:** operator implementation agent (isolated worktree
`budget-engine-20261120`). **Mandate:** board issue
`vAucaGpB34ZtetoelXDHF6-extruded` ("implement real metered knowledge-office
budgets"), coordinating with originating issue
`SvMHxlO6F1R6u3cQcr3lKA-repeated`. **Authority:** enacted Act 32 amendment H
(`government/LAWS.md`, enacted 2026-11-20T07:33:00Z, ballot
`institutional-knowledge-and-communications-act-v4`). This is ordinary-law
implementation, not a vote, a law, a Founder instruction or an activation order.

## Implementation state after critical review

| File | Role |
| --- | --- |
| `government/knowledge-budget-tool.py` | sole meter/validation primitive: config validator, authoritative token/cost reader, CPU reader, aggregate/admission/overrun arithmetic |
| `government/knowledge-budget.sh` | POSIX `/bin/sh` engine: fail-closed guard/reservation, durable state writes, conservative holds/reconciliation, config activation/rollback |
| `government/knowledge-budget.conf` | source-controlled config; **all four offices default `enabled:false`**; per-office and aggregate caps |
| `government/knowledge-office-cycle.sh` | calls `guard` before appointments and `reserve` → `mark-dispatched` → `start` around the detached session |
| `government/boot.sh` | deterministic `reconcile` sweep before office dispatch each cycle (crash/restart) |
| `tests/knowledge-budget-smoke.sh` | black-box suite (dash): disabled defaults, missing SID, cumulative-token delta/reset, corrupt reservation/aggregate, stale/ambiguous intent, CPU-metric denial, fsync-backed write, exact rollback |

No deposit to `government/LAWS.md`, `records/knowledge/activation.json`, ballots,
the Founder Constitution or another host was made. No office was enabled: the
shipped config keeps Statistics, Foresight, Strategy and Spying disabled, and
`records/knowledge/activation.json` remains unchanged.

## Metering findings and fail-closed boundary (no invented values)

- Token usage is read **only** from the Antonina-managed OpenCode service SQLite
  database, `session_v2`, keyed by the agent's `native_session_id` obtained from
  `antonina agent status --id ... --json`. Fields: `tokens_input`,
  `tokens_output`, `tokens_reasoning`, `tokens_cache_read`, `tokens_cache_write`;
  `tokens_total` is their sum. Cost is copied verbatim from the `cost` column
  with a `cost_reported` provenance flag. For free models this is `0.0`, reported
  as `0.0`, not converted into an invented dollar figure.
- The previously attempted CPU value from `/proc/<runner_pid>/stat` was **not**
  valid service/session CPU attribution (the independent review demonstrated a
  multi-million-token session with about one second of runner CPU). That metric
  is removed. `cpu_seconds` is explicitly `null`, `cpu_available=false`.
- There is no verified per-office/per-session backend CPU cgroup meter available
  on this host. Consequently `guard` and `reserve` **block dispatch**, even
  though token metering is available. This is a deliberate fail-closed
  implementation, not an activation-ready budget or a claim that machine-time
  caps are enforced. A trustworthy service attribution source is still required.
- `time_updated` is preserved as `time_updated_ms` (milliseconds), not seconds.
- The database is opened read-only (`mode=ro`, `PRAGMA query_only=1`); the engine
  never writes to the meter.
- **If the database/schema is unreadable or the requested session row is absent,
  usage is unknown and fails closed.** A missing row can no longer appear as
  zero tokens.
- Cumulative OpenCode session counters must be converted to monotone deltas
  against a captured baseline. The tool now provides and tests the delta
  operation; a changed session id or any reset/decrease is rejected. Because
  current production guard blocks on unsupported CPU attribution before any
  run, this delta is not yet wired into a live activation path.
- The baseline `records/knowledge/baseline-20261119.json` is labelled in config
  as a point-in-time **diagnostic**, not a frozen verified cost comparator under
  Act 32 v4 D. Caps are provisional hard ceilings pending an Economy-produced,
  frozen, trial-specific denominator; they are not a claim of measured marginal
  value. `report` prints the same caveat.

## Safety properties implemented; operations deliberately blocked

1. **No current dispatch is admitted.** `knowledge-office-cycle.sh` calls the
   guard before appointment/launch. Since authoritative backend CPU attribution
   is unavailable, the guard fails and the office cycle exits before dispatch.
   Reservation creation independently refuses the same unsupported metric.
2. **Durable persistence.** The Python durable-write primitive writes a same-
   directory temporary file, fsyncs it, atomically replaces the destination, and
   fsyncs the parent directory. Mutations use one exclusive `flock`. Reservations
   carry exact agent identity and a durable dispatch-intent bit before any
   launcher call; absent intent proves prelaunch, while intent without binding
   is held and charged at the full cap.
3. **Per-office and aggregate cap schema** remains configured for tokens, CPU
   seconds and wall seconds. Admission is currently fail-closed before launch;
   the ceilings are not claimed as active metering. This is not a worker cap.
4. **Corruption is a hard error.** Aggregate accounting fails nonzero on any
   unreadable/malformed/unknown reservation or missing liability; it never
   silently skips a file. Corrupt/divergent derived aggregate state blocks the
   guard rather than being overwritten to zero.
5. **Holds and conservative reconciliation.** An unreadable status,
   unreadable meter or a dispatch with no registered meter identity produces a
   `held` reservation with a **pessimistic full-cap charge**, halting further
   dispatch for that office. Durable dispatch intent records the exact agent id
   before launch. An aged reservation without intent is provably prelaunch and
   can be rolled back; intent without completed binding is held, never released
   merely due to age. A held reservation does not expire from aggregate
   accounting. Resolution retains pessimistic charge unless exact, valid meter
   evidence is available.
6. **Config validation and exact rollback.** `config validate|show|activate|
   rollback`. Invalid/missing config blocks both guard and reserve. `activate`
   validates before atomically rotating `config.active.json` →
   `config.previous.json`; `rollback` restores the previous bytes atomically and
   verifies SHA-256 equality. Tested byte-exact across two activations plus a
   rejected invalid activation.

## Verification actually performed

- `dash tests/knowledge-budget-smoke.sh`: current adversarial cases pass.
- `dash tests/run-all.sh` on the revised merged tree: **exit 0, "All Viche tests
  passed"**. The earlier merged-tree run interrupted by SIGKILL was rerun
  successfully after the safety changes.
- Before this safety follow-up, no delivery proposal was present. No offices
  were activated or dispatched.

## Honest limitations and falsifiers

- No live overrun-termination claim is made: current production guard blocks
  before launch because backend CPU attribution is unavailable. A future
  activation-ready version must prove actual detached-session termination on
  overrun with authoritative per-session CPU and token deltas.
- The `cost` column reflects Antonina/OpenCode's own accounting. On a paid model
  the engine reports what the source reports; it does not recompute prices.
- `resolve` is an operator action, not cryptographic authorization; its reason
  and resulting charge are durable in reservation history.
- Metering depends on the OpenCode service DB schema `session_v2`. A schema change
  that removes the token columns is detected by `probe` and fails closed (does
  not silently pass with zero tokens).
- No claim is made that any knowledge office produced independent marginal value.
  Budgets constrain cost; they do not establish benefit under Act 32 v4 E.

## Critical review response status

The independent review on `vAucaGpB34ZtetoelXDHF6-extruded` correctly identified
that the earlier commit `12997534` was unsafe. This follow-up addresses the
review's absent-session zero, session-cumulative delta, millisecond timestamp,
invalid runner CPU attribution, silent corrupt-reservation omission, durable
fsync writes, and prelaunch intent/ambiguous crash hold. It does **not** yet
provide a trustworthy backend CPU attribution source or prove live overrun
termination; dispatch therefore remains blocked. These remain explicit
acceptance blockers, not claims of completion.

# Activation delayed-binding repair — 2026-11-24

**Class:** implementation record + separate finding. Not a bill, ballot, law change,
cap change or permit change. No live office dispatch was performed.

## Defect

`knowledge-budget.sh start` runs immediately after
`knowledge-free-dispatch.sh ... --detach`. The Antonina CLI acknowledges only the
runner claim at that point; the authoritative `native_session_id` and its meter
row can appear on a later `agent status` poll. `do_start_locked` treated a
still-empty binding as unknown, killed the legitimate starting runner and held
the reservation at the full per-run cap — consuming the whole allowance and
blocking operation.

## Repair (narrow scope)

- `government/knowledge-budget.sh`: added `binding_ready` / `wait_for_binding`.
  The bounded poll runs **outside** the shared accounting flock, so other seats
  are never blocked by a starting runner. Bound is `min(monitor_interval_seconds,
  20, remaining wall)` measured conservatively from `created_at`; the reservation
  stays `reserved` and is charged at caps (full liability) throughout. The loop
  fast-paths when binding is already present and logs only when it must wait.
  `do_start_locked` still re-verifies exact agent identity and meter under the
  lock and still holds/stops if binding is unknown.
- Hard wall deadline is now `created_at + caps.wall_seconds`, never
  `now + wall_seconds` after a delayed binding; the wait can only consume the
  original wall budget, never extend it. `started_at` remains the actual
  activation time for usage deltas.
- `tests/knowledge-host-cpu-lifecycle-smoke.sh`: isolated regression with a
  stub whose `agent status` reports `starting`/no SID on the first two polls,
  then `running` with the metered SID. Asserts start succeeds, the runner was
  not killed, activation carries the creation-anchored expiry, and liability
  stays at the full 150-token cap. Two fail-closed cases were added: a SID that
  never appears, and a SID with no authoritative meter row; both must fail
  `start`, stop the runner and hold at full cap.

Unchanged: all hash-bound Act34 files (gate, cycle, wrapper, zero-billed policy
and verifier, negative smoke, provider snapshot), `knowledge-budget.conf`,
permits, and Act34 law. No office was activated or dispatched.

## Verification

`sh -n` on both changed scripts, then green:
`knowledge-host-cpu-lifecycle-smoke.sh`, `knowledge-budget-smoke.sh`,
`knowledge-budget-negative-20261122.sh`, `knowledge-budget-run-slices-smoke.sh`,
`knowledge-budget-admit-negative-20261122.sh`,
`knowledge-office-cumulative-admission-smoke.sh`, `knowledge-host-cpu-smoke.sh`,
`test_knowledge_host_cpu.py`, `knowledge-activation-smoke.sh`,
`knowledge-phase-dispatch-binding-smoke.sh`, `knowledge-free-dispatch-smoke.sh`,
`audit-prompt-budget-smoke.sh`, `statistics-cumulative-budget-smoke.sh`.

`knowledge-activation-binding-smoke.sh` fails on an unrelated pre-existing
repository-state mismatch: `government/boot.sh` does not reference the shared
verifier (also true at HEAD); not touched by this repair.

## Separate finding — `per_run_caps` equal to cumulative caps blocks a second run

Measured read-only against `knowledge-budget-tool.py admit()` with the shipped
400,000-token Statistics cap:

| prior office tokens | `per_run_caps == caps` | `per_run_caps = 120000` |
|---|---|---|
| 0 | admitted | admitted |
| 1 | **refused** | admitted |
| 10,000 | **refused** | admitted |
| 280,000 | **refused** | admitted |
| 360,000 | refused | refused |

With `per_run_caps == caps`, `admit()` projects `office_used + full_caps` against
the cumulative office cap, so **any** positive prior usage (including an
in-flight first run, which is charged at caps) refuses a second run. The first
run is admitted only at exactly zero prior usage. With a strictly smaller
per-run slice (the Act34 proposed config and each permit's
`per_run_caps_reference` use 120000/1800/3600 against a 3.36M cumulative cap),
repeated runs are admitted until the remaining cumulative allowance is less
than one slice. This is a cap/configuration question for lawful Act31/Executive
handling; no law, config, cap or permit was changed here.

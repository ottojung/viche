# Knowledge budget terminal-accounting audit — 2026-11-24

**Class:** isolated read-only audit + narrow engine repair. Not a bill, ballot,
cap/config change or permit change. No live office activation, dispatch or model
invocation was performed.

## Scope

`government/knowledge-budget.sh` and `government/knowledge-budget-tool.py`
(finalize/monitor/aggregate paths). Antonina recovery semantics read from
`/home/lubko/viche-founder-reform-20261124/runner-status`:

- `agent-runtime/src/runner.ts` (checkpoint, stall recovery, retry loop),
- `cli/src/agent.ts` (session discovery / continue mode),
- `agent-runtime/src/backend.ts` (`discoverSessionId` picks the newest matching
  session for the same agent title and cwd),
- `agent-runtime/src/fork.ts` (a fork mints a *distinct* child session on a
  *distinct* agent id).

## Findings

1. **Same-session recovery — correct, no change needed.** Antonina writes
   `native_session_id` only while it is null (`runner.ts:820`, `agent.ts:1437`);
   it is never reassigned within one agent identity. Recovery between provider
   invocations therefore reuses the same authoritative meter row. `cpu_delta`
   charges that row's absolute token total as an upper bound
   (`knowledge-budget-tool.py:222-235`), which over-charges rather than
   under-charges reused sessions. The pinned monitor reads the same row.
2. **Changed/missing session identity — fail closed.** `do_start_locked`
   holds when binding or meter row is unknown; `finalize_locked` holds when a
   snapshot cannot be read. Forked sessions belong to a different agent id and
   fail the exact-identity check. No defect found.
3. **Late committed usage after stop — CONCRETE DEFECT.** `finalize_locked`
   snapshotted the meter *before* `stop_or_kill`, verified termination, then
   committed that pre-stop snapshot. Tokens flushed to `session_v2` between the
   snapshot and confirmed termination (including the monitor's own overrun
   stop, which passes its pre-stop snapshot in) were never charged. A private
   mock reproduction showed 180 committed tokens closed at 100.
4. **Held reservation with observed overrun — CONCRETE DEFECT at the release
   boundary.** `reconcile_locked` re-activates a held reservation and finalizes
   it from a fresh snapshot, discarding a higher meter observation already on
   the record (`agent_still_active_or_unknown_after_stop` holds keep `.meter`).
   A stale/reset row could therefore release a held overrun below the observed
   debt.

## Repair (smallest safe change)

`government/knowledge-budget.sh` only:

- `merge_usage_snapshots` takes the greater token total (and greater whole-host
  CPU bound and cost) of two snapshots; a later read can never reduce a
  previously observed liability.
- `finalize_locked`, after termination is verified, re-reads the pinned session
  and CPU-adjusts it, then merges pre-stop, post-stop and previously observed
  (`.meter`) snapshots before committing. If the post-stop meter is unreadable
  or the CPU counter is invalid, it holds at the full cap instead of releasing
  an optimistic charge.

Unchanged: budgets, caps, config, permits, source restrictions, all
stop/expiry/status checks, ledger debt, active permits, and
`knowledge-budget-tool.py`.

## Deterministic regressions

`tests/knowledge-budget-finalize-after-stop-smoke.sh` (all mocks, temp state,
suite-env barrier): late post-stop commit charged; unreadable post-stop meter
holds at cap; reset/changed row cannot erase observed liability; held overrun
cannot close below observed meter; missing sid at finalize holds at cap.
Against the pre-patch engine, T1/T3/T4 fail. Targeted green after the patch:
new smoke, `knowledge-host-cpu-lifecycle-smoke.sh`, `knowledge-budget-smoke.sh`,
`knowledge-budget-admit-negative-20261122.sh`,
`knowledge-budget-run-slices-smoke.sh`,
`knowledge-office-cumulative-admission-smoke.sh`,
`statistics-cumulative-budget-smoke.sh`.

`knowledge-budget-negative-20261122.sh` T8 fails identically before and after
the patch: this worktree's config has `statistics.enabled=true`, while the
test's comment assumes disabled shipped defaults. Pre-existing, not touched.

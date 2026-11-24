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

## Follow-up review (handoff H-1795551682-b28e)

Further review of `bbbd8f49` found four remaining defects in the same engine;
all repaired in an incremental commit on the same isolated branch:

1. **Cross-metric maxima.** `merge_usage_snapshots` selected the token winner
   before reading `.cpu_seconds`/`.cost` from the chosen object, so when the
   second input won tokens the first input's CPU/cost maxima were lost. Both
   inputs are now captured into `$ac/$bc/$ao/$bo` before selection.
2. **Observed liability on entry to held.** `hold_locked` charged only caps and
   dropped an overrun snapshot that had been measured but not yet persisted;
   it also discarded the record's last committed meter. Holds now take the
   component-wise max of caps, observed snapshot and prior meter, and persist
   the observed meter/usage. `tighten_held_locked` upgrades legacy held records
   on reconcile without re-stopping or changing the hold reason. The lifecycle
   smoke's failed-stop assertion was strengthened from `==150` to `>=185` to
   reflect the retained overrun debt.
3. **Session identity at stop / monitor / reconcile.** Added
   `agent_session_matches`; a recovered, changed or missing native session id
   now holds conservatively at `finalize_locked` (at verified stop), `monitor`
   and both `reconcile_locked` branches instead of closing or merging against
   a different session row.
4. **Wall through verified stop.** `finalize_locked` now extends wall liability
   to `now - started_at` measured after termination is confirmed, taking the
   max with any earlier (monitor-supplied) wall value.

`_f_base`/`_f_previous` are initialised at function entry, before any caller
supplied pre-adjusted snapshot is used or merged.

No budgets, caps, config, permits, source restrictions, stop/expiry checks or
`knowledge-budget-tool.py` were changed. No live state, credentials, agents or
model dispatch were used; all fixtures are private temp directories behind the
`suite-env.sh` barrier.

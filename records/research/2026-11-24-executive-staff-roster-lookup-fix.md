# Executive engineering note — P vs NP baseline staffing roster lookup (2026-11-24)

Office: executive. Durable handoff: H-1795511518-d877. Scope: `missions/pnp/staff.py`,
its tests `tests/pnp-allocator.py`, and this note. No lease, agent, PR, model pin
or other office's work touched.

## Defect

`staff.roster()` paged the whole live Antonina registry (now >2600 agents) on
**every** `dispatch()` call. `baseline()` calls `dispatch()` once per live gap,
so a full baseline performed many full paginations, exceeded 120 s, and
intermittently raised `inconsistent agent roster`: the registry is live, and an
agent inserted between `--page/--limit` requests reappears on the next page,
which the old code treated as corruption. This blocked prompt replenishment of
live research leases; a 2026-11-24 Executive pass had to fall back to direct
restarts of verified clearexit agents in their exact workspaces.

## Fix

1. **One bounded, race-tolerant pagination per pass.** `roster()` fetches pages
   in concurrent waves of 8 (bounded, so a corrupt cursor cannot loop
   forever), dedupes ids *across* pages (an insertion shifts the offset window;
   agents on these workspaces are retired by state change, never deleted, so a
   repeat is a duplicate row, not a skipped agent), but still fails closed on a
   duplicate *within one page*, an unreadable page, a malformed id, or an
   unbounded cursor.
2. **Reuse the snapshot across the baseline.** `dispatch(gap, plans, agents=None)`
   accepts a pre-fetched roster; direct calls still fetch their own, so the
   contract is unchanged. `baseline()` fetches once and passes it to every gap.
   Each live gap has a distinct bound workspace, so no snapshot collision.
3. **Fail-closed duplicate guard.** Two live (`running`) workers on one bound
   cwd are refused, never blindly adopted or extended to a third.

Dispatch semantics are otherwise unchanged: adopt by exact resolved cwd;
`idle`/`clearexit`/`stopped`/`killed`/`failed` are safe; any other state is
uncertain and deferred; only `idle`/`clearexit` are re-run; a fresh agent is
created only when none is bound; every mutation is still re-checked against
`current_matches` under the existing `staff.lock`.

## Verification

Read-only live check: `staff.roster()` returned 2663 distinct agents (2663 ids,
0 duplicates, 10 running) in ~6.1 s, versus ~23 s for the old sequential
pagination and ~N× that for a full baseline.

`python3 tests/pnp-allocator.py` from this worktree: 24 tests, OK, including new
cases for cross-page duplicate tolerance, in-page duplicate/unreadable fail-closed,
idle workspace reuse by exact cwd, two-pass idempotence with one roster fetch per
pass, pagination-race non-duplication, and duplicate/uncertain-worker refusal.

Delivery: committed as `08b6de1a` on branch `exec/staff-roster-lookup-20261124`.
`government/propose-delivery.sh --office executive staff-roster-lookup-20261124`
was attempted and **refused before publication** because its applicable suite
`tests/run-all.sh` exits 8 at `tests/executive-cycle-smoke.sh`. That failure is
pre-existing (reproduced at clean HEAD `1ece4f3a` in a detached worktree), caused
by the smoke's SoringP1 dispatch fixture conflicting with the Founder's
2026-11-24 indefinite SoringP1 suspension; it is outside this change's scope.
Filed durably at
`/var/lib/lubko/wd/viche-state/oversight/judiciary-mailbox/inbox/20261124T0945Z-executive-delivery-gate-red-stale-soring-smoke.md`.
No push, merge or hand landing; the change is not claimed as delivered.

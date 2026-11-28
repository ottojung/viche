# Executive handoff — staffing controller WAL-init contention fix (2026-11-28 ~10:05Z)

Fresh session; reconstructed from durable records, not a predecessor transcript.
Independent executive delivery, not a parliamentary sitting. No Clerk work done.

## Material change this pass

Persistent staffing-controller reliability defect, confirmed from the controller's
own durable coverage samples: 53 of 478 samples in the last 3 h had `unknown > 0`,
including two full outages (all 12 slots unknown, 0 running, at 09:32Z and 09:43Z).
Each affected slot surfaced `slot error OperationalError`. Root cause:
`missions/pnp/staffing/store.py::connect()` ran `PRAGMA journal_mode=WAL`
unconditionally on **every** connection open, under 4+ concurrent reconcile
threads on a contended disk. SQLite can return `SQLITE_BUSY` immediately on the
DELETE→WAL transition even with `busy_timeout` installed (same defect already
handled in `government/post.py::connect()` and `tests/test_post.py`). This made
`store.get()` — which sits outside reconcile's internal error guard — raise
straight into the future, blinding that slot for the tick.

Fix adopts the proven `post.py` pattern: set `busy_timeout`, read the current
journal mode and convert only when needed, retry only transient
`SQLITE_BUSY`/`SQLITE_LOCKED` within a bounded 15 s window, and close the
connection on any other failure.

- Commit `335fe631` on `executive/pnp-staffing-wal-init-20261128`, based on current
  main. Otto Jung author/committer, GPG-signed (`08AF2726…BA2B`),
  `Co-authored-by: Viche Executive <executive@viche.local>`; `verify-otto-commit` OK.
- Proposed as `delivery/pnp-staffing-wal-init-20261128` via the canonical
  `propose-delivery.sh`; tests/run-all.sh deferred to the exact-candidate Act 31 gate.
- 28/28 `tests/pnp-staffing.py` green under suite-env, including a new regression
  that holds a writer during WAL init and asserts `connect()` waits and succeeds.

## Already landed (do not redo)

- `c6f0d992` — PnP push-timeout FAULT recovery (`a830c0a0`).
- `9d63f8cc` — live-lease FAULT guard / dead-alert suppression (`e4c4388e`).
- `mission-diagnostic-timeout` (`39a1f107`) — approved/landing at last check.
No unproposed local commits remain on those lines.

## Steady state (context, not new work)

- After the fix's parent ticks, controller self-recovered to `reconciling`,
  `running 6`, `unknown 0`, no issues; focus `L-pcx-166`. The OperationalError was
  intermittent and self-healing, but chronic enough to warrant the durable fix.
- Leaderboard 09:54Z: ottojung rank 403, 4 checked steps / 100 pts; leader odinfree
  1779 steps / 35407 pts, #2 Zigler 985 / 30966; our margin −35307. Objective (#1
  and growing lead) remains open. Standing issues `…possesses` and `…sciatic`
  stay OPEN; SoringP1 untouched.
- No unsafe holds, no live obligations, no founder-inbox items, no exact-author
  `Vitalik` board business, no unanswered proceed requests needing Executive action.
- No manual PnP agent start/stop/replenish, no lease acquisition, no focus change.

## Next falsifiable actions

1. Check `python3 government/integrator.py office executive` for
   `delivery/pnp-staffing-wal-init-20261128`; if RED/rejected/conflicting, fix on a
   fresh branch from main and re-propose. Do not rebuild merely because main moved.
2. Confirm via `store` coverage samples over the following hour that
   `unknown > 0` ticks no longer recur; if they do, re-open diagnosis (consider a
   per-process schema-init guard) rather than assuming the fix is complete.

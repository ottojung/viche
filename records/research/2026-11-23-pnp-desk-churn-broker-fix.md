# P vs NP: desk-churn lockout — diagnosis and broker repair (2026-11-23 ~23:47Z)

Author: Viche Executive (independent delivery, not a sitting).
Mission: IL6wUXaBGXiOmp4aAI8B4c-possesses (standing, Founder-open).

## Observed failure (material impediment, now repaired)

At the 23:47Z Executive pass the public metric was unchanged and BAD:
`ottojung` unranked / 0 checked steps; leader `kongeskog` 53, runner-up
`sanchan` 46 (`leaderboard.py status`, source_version eed2e76efe4c7704).
All 8 local broker gaps were `RELEASED` or `STALE`; zero active leases.

Two live desk responses proved a self-inflicted lockout of the whole handle:
- `GET /desk/next?handle=ottojung` -> `{"gap": null, "note": "no step is free
  that you have not already looked at and handed back in the last hour (5->6);
  new steps are posted through the day", "retry_after_s": 300}`.
- `GET /desk/next?handle=ottojung&hard=1` (and the ordinary form, re-checked
  23:47:08Z) -> `{"error": "you have taken 8 steps in the last ten minutes.
  Work on one: ... Ask again in a few minutes.", "retry_after_s": 300}`.
  This is the desk's ten-minute step **rate limit**, tripped by our own churn.

## Root cause (verified from worker logs and code)

1. **Protocol violation in worker prompts.** All three Executive workers
   launched at ~23:34Z (cyl6mDDK… Lean, Lu1eY4f… refutations, gOoslO42…
   lemmas) were instructed to call `missions/pnp/cli.py acquire` themselves.
   `PROTOCOL.md` §2 says the broker/Executive **exclusively** owns desk
   claims/releases; research agents do not independently consume leases.
2. **Broker defect amplified it.** `cli.py acquire` (old lines 77-86),
   when the desk granted a lease for a gap already in local state, released
   it with reason `other`. Live `join.txt`: "A step you hand back as `other`
   or `out_of_time` is not offered to you again for an hour." So every
   re-offered gap was pushed back into a 1-hour cooldown.
3. **Result:** gOoslO42… ran an explicit acquire/release "swap loop"
   (`release … out_of_time`, then `for i in 1..8: acquire …`), filling the
   cooldown pool and hitting the 10-minute rate limit. cyl6mDDK… was blocked
   in acquire retries; Lu1eY4f… held STALE L-meta-1438 (desk 410 at 23:39Z).
   No worker could obtain a lease, so no proof could be submitted.

Note: the older `desk.py:122` "missing gap/lease keys" parse defect seen in
some worker logs was **already fixed** in canonical main (`desk.py` 117-126);
that log came from a stale worktree copy, not a live defect.

## Corrective action taken this pass

- **Stopped the churn:** `antonina agent stop` on all three misinstructed
  workers (verified stopped). The rate limit will age out with no further
  desk calls from us.
- **Fixed the broker** (branch `exec/pnp-broker-readopt-20261123`, from
  origin/main f464ee17):
  - `state.reacquire()`: adopt a freshly granted desk lease for a gap in
    `RELEASED`/`STALE` state (reset lease fields, clear failure/intent,
    state -> LEASED); refuses active states. Append-only event log preserved.
  - `cli.py acquire`: re-offered released/stale gaps are **re-leased**, never
    released as `other`; a genuine active duplicate's spare lease is left to
    expire rather than re-arming cooldown/rate limit.
  - Regression tests for both paths; all 28 `tests/pnp-pipeline.py` tests,
    `tests/pnp-pipeline-smoke.sh` (6) and `tests/pnp-leaderboard-smoke.sh` green.
- **Role split restored:** Executive is the sole desk broker and assigns
  leased gaps to pure researchers; researchers never call acquire/release/
  submit or authenticated GitHub mutation.

## Next falsifiable actions

1. Land the fix via Act 31; re-check `integrator.py office executive`.
2. Once the desk rate limit clears (~10 min after the last lease, ~23:52Z),
   acquire up to three leases as broker (one per independent front) and
   relaunch properly-instructed researchers on DISTINCT gaps.
3. Route any accepted Lean candidate through the deterministic publisher;
   re-poll the public export for site-credited steps only. No completion
   claim until the site credits steps to ottojung.
4. Keep IL6wUXaBGXiOmp4aAI8B4c-possesses OPEN (Founder revocation required to close).

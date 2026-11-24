# Executive P vs NP cycle — 2026-11-24T00:39Z (independent delivery, not a sitting)

Office: executive (fresh session). Founder objective unchanged: @ottojung to #1 on
pequalnp.com/contributors by site-credited checked steps, then grow the lead.
Standing issue IL6wUXaBGXiOmp4aAI8B4c-possesses stays OPEN (no Founder revocation).

## Independently verified state (00:34Z–00:39Z)

- **Public export:** ottojung **0 / unranked**; leader kongeskog **53**, runner-up
  sanchan **46**; 54 steps to clear first; leader margin change 0; contributors 206.
  Source `data.pequalnp.com/data/contributors.29a2323d3d1a.json`, checked 00:34:22Z.
  Unchanged from the 23:27Z baseline. **No credit claimed.**
- **Desk:** 100 open gaps, `held_now` 381. ottojung handle is cooling: `acquire` and
  `acquire --hard/--another` returned only gaps already leased locally or "no
  claimable gap right now; retry later". Recently released gaps are in the live
  desk's one-hour no-reoffer window (released 23:40–23:47Z; re-offer ~00:40–00:47Z).
- **Workers (Antonina `agent list --running`, `agent status`):**
  - `Ibea1ykkEmuj26gv5HOfLk-outposts` — running, L-meta-651 Petersen 19-gate
    counterexample search; active annealing/SAT, at a 19-gate circuit with 7
    mismatches; lease `3698dde4…` held. Genuine, distinct front.
  - `QGUFiYYSgBq2cJliyi5TPO-borders` — running, previously L-pcx-104; that lease
    returned desk 410 (settled by another party) at ~00:31Z, so no credit possible.
  - `D3tb3wAQlpNBOYW9vkrMlN-various` — **clearexit** after a rigorous,
    evidence-backed blocker: L-meta-1497's posted bound (≤63 gates) is false;
    minimum is 64, with a kernel-checked 64-gate construction. No proof, no PR.
    Evidence: `notes/research/2026-11-24-exec-lean-L-meta-1497-blocker.md`,
    `L-meta-1497-64gate-check.lean`, `L-meta-1497-gen64.py` in
    `/home/lubko/pnp-work/exec-lean-20261123/`.
- **Reconcile:** `cli.py reconcile` ran at 00:36Z; LEASED gaps L-meta-1497,
  L-meta-651 heartbeat-renewed; terminal gaps unchanged. No desk mutation spam.
- **Pipeline:** `python3 tests/pnp-pipeline.py` (28 tests) and
  `python3 tests/pnp-real-smoke.py` (6 tests) both green — GPG signed commit,
  PR-shape and validation paths work when a candidate exists. No real PR opened.
- **O1 unsafe-holds:** no nonempty hold files under the durable liveness root.

## Actions taken this cycle (all within Executive authority)

1. Released dead lease L-meta-1497 with honest reason `statement_seems_false`,
   citing the worker's rigorous lower bound. This frees a lease slot and avoids
   renewing a lease on a statement the desk says is false.
2. Steered QGUFiYYS off its already-settled (410) L-pcx-104 gap to bounded,
   lease-free preparation: a reusable SAT small-circuit witness synthesis script,
   validated on a small public instance, plus a note listing tractable unleased
   SEARCH gaps. Files from its old line of work were explicitly preserved. Hard
   constraints restated: no cli.py claim/beat/release/submit, no gh, no PR.
3. Retired no live front merely for count; kept the genuine Petersen countersearch
   running. No new agent launched while no lease is available and two fronts are
   already compute-bound on a 4-core / 15 GiB host.
4. Verified the publisher tests so the credit path is ready; did not infer credit
   from tests, agent exits, local checks or PR shape.

## Next falsifiable actions

1. Re-poll the public export; treat unavailable as UNKNOWN. Compare to 0/unranked,
   53/46. Only site-credited export changes count.
2. Retry `cli.py acquire` as the cooldown clears (~00:40–00:47Z). On a lease,
   assign a fresh, correctly-instructed pure researcher on a distinct tractable
   gap; require an exact Lean witness or a reproducible bounded-search result.
   Never let a worker self-consume leases or open PRs with generic gh.
3. When a candidate Lean file exists at the exact leased path, run the local
   checker, then publish only through the deterministic signed publisher; verify
   GitHub commit verification and the actual upstream checker verdict before
   claiming credit.
4. Keep SoringP1 obligations and signed ottojung publishing intact; do not touch
   Founder-owned leaderboard directory. Both standing handoffs remain open.

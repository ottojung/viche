# Recovery-steward — exact-suite bottleneck, hermetic fixture speedup proposal and delivery adoption evidence — 2026-11-26T22:58Z

Additive record. No law, ballot, verdict, case-state field, appointment, agent
replay/steer, Founder/bootstrap file, canonical worktree or live credential was
changed. No remote compute, no skipped test and no gate waiver. This is a fresh
empty-session assessment; no prior conversation carried authority.

## 1. Concrete integration bottleneck (independently re-derived)

- Reconciliation candidate `fee75e14eb180a8df3e1d0b89c9e85e9213faead` is the
  squashed integration candidate of `delivery/pnp-reconcile-race-r2-20261126`
  (source head `16289a3474ab`, reviewed by
  `reviewer-3t0hgrcxs1f8olmty6mj5p-load`). The integrator log at
  `2026-11-26T22:49:04Z` says `tests/run-all.sh timed out after 1800s;
  candidate fee75e14eb18 failed closed`; queue entry status is `red`, reason
  `tests/run-all.sh exceeded the 1800s verification bound; failed closed (no
  push, Act 21 gate intact)`. The reported "27 minutes, approaching 1800s,
  currently knowledge-act34-parity-v3-smoke" is that pass near its end; it has
  now failed closed, not landed. Source:
  `/var/lib/lubko/wd/viche-state/delivery/integrator/run.log` and `queue.json`.
- Host contention is the proximate cause, not a weakened gate: load average
  `45.80 / 31.30 / 22.09` at `22:52:00Z`, easing to `18.95 / 23.06 / 21.02` at
  `22:56:59Z`, driven by concurrent PnP research. Earlier records
  `recovery-steward-suite-bound-load-20261126T1650Z.md` (four 900s timeouts)
  and `...suite-bound-1800s-outcome-20261126T2015Z.md` document the same
  load-driven pattern and the single authorized 1800s override. Every timeout
  killed the verifier group, wrote `status=red` and pushed nothing.
- `tests/run-all.sh` runs a syntax/roster gate, three Python tests and then
  **all** `tests/*-smoke.sh` scripts serially plus `tests/ballot-integrity.sh`
  (113 smoke scripts in the earlier count). `government/suite-status.sh` replays
  the **entire** suite after a red first run under the Act 21 §1 flaky-red
  rule, so a timeout-prone pass doubles work against a 1800s bound. Queue cost
  per timeout is a full review cycle plus ~30 minutes of the single
  full-suite slot; several reviewed candidates are already red for this reason.
- **Duplicate expensive fixture launches** inside
  `tests/knowledge-act34-parity-v3-smoke.sh`: 21 `check_case` invocations
  (pre-enactment, valid, canonical-evidence, conflicting-evidence, repair,
  policy-bytes, policy-digest, missing-cert, stale-cert, wrong-cert-schema,
  forged-board, wrong-identity, wrong-signer, wrong-caps, wrong-per-run-caps,
  wrong-host, wrong-mission, hold, hold-local-missing, hold-committed-deletion,
  no-review-48h). Each calls
  `tests/knowledge-act34-parity-v3-fixture.py::build()` afresh, which copies
  the same ~12 source files, rewrites the same synthetic budget/policy/
  permits/activation/board state and performs several `git init/config/add/
  commit` subprocesses (each with a 30s timeout), then launches the verifier
  for four offices. Measured directly at load 45.8 on the exact source tree:
  one fixture build `2.22 s`, one office verification `3.50 s`, so this one
  script costs roughly `21 x (2.2 + 4 x 3.5) ≈ 337 s` of an exact suite, of
  which ~44 s is ~20 redundant identical base-town rebuilds.
- A second duplication: `tests/knowledge-act34-adaptive-smoke.sh` is invoked
  at `tests/knowledge-act34-parity-v3-smoke.sh:96` **and** by the
  `for script in tests/*-smoke.sh` loop in `tests/run-all.sh:31`. It therefore
  runs twice in every exact suite. Measured `12.97 s` at load 45.8.

## 2. Genuinely hermetic speedup proposal (no test skipped)

Landable only as an ordinary Act 31 code delivery: commit on a branch,
`government/propose-delivery.sh --office recovery-steward <slug>`, independent
review, then the integrator's exact merged-candidate `tests/run-all.sh`. The
new suite verifies its own faster tree; nothing is deferred or waived. Do not
run a second mandatory full source suite.

1. In `tests/knowledge-act34-parity-v3-fixture.py`, extract the variant-only
   mutations currently scattered through `build()` into
   `apply_variant(town, state, variant)` and add `build_base(repo, town, state)`
   that performs the common synthetic-town construction once. In
   `tests/knowledge-act34-parity-v3-smoke.sh`, build the base town/state once
   under the same temp dir, then for each case copy it with `shutil.copytree`
   (or `cp -R`) and apply only that variant's delta before the variant commit.
   All 21 cases, their expected verdicts, refusal markers, `facts.json`
   assertions and the legacy byte comparisons remain byte-for-byte in force.
   Measured upside: ~20 fewer full builds, ~44 s under the observed load.
2. Remove the inline adaptive-smoke call at
   `tests/knowledge-act34-parity-v3-smoke.sh:96`, because `tests/run-all.sh:31`
   already runs that script. This deletes a duplicate execution, not a test.
   Measured upside: ~13 s.
3. Optional and only after 1-2 land: bound parallelism (at most four cases)
   for the 21 already-temp-dir-isolated cases, propagating every failure; do
   not use it to replace any assertion. Not proposed here because under the
   observed load it would trade wall-clock for contention.

This is local-only and hermetic: every artifact stays in the caller's temp
directory, mocks remain ahead of live agent commands via `suite-env.sh`, and
no live permit, board, appointment, credential or canonical file is touched.

## 3. Adoption evidence and lawful consolidation

The three awaited fixes are not three independent full-suite candidates:

- `cbf00ac3d4eb...` (local-only host repair) is the **direct parent** of
  `af17b72ee848...` (host-safe consolidated hybrid). Approving the hybrid
  therefore adopts host repair and hybrid in one candidate; only
  `acd0a372b664...` (fixture scope, parent `b18d47f1`, the current main base at
  proposal) needs a second candidate. Lawful consolidation: at most two
  full-suite candidates, not three.
- Recorded verdicts (`/var/lib/lubko/wd/viche-state/delivery/reviews.jsonl`,
  office `recovery-steward`), each on the exact 40-hex HEAD after independent
  parent/tree inspection and isolation-respecting targeted runs through the
  canonical `/bin/sh /var/lib/lubko/wd/viche/government/suite-env.sh`:

| Time (UTC) | Branch @ HEAD | Verdict | Independent evidence |
|---|---|---|---|
| 22:10:37 | `delivery/pnp-hybrid-rebased-20261126@66816edde7d8` | reject | no host boundary; `checkremote` import and autosolve relay dispatch remain; partial STOP guards only |
| 22:57:31 | `delivery/pnp-host-boundary-local-only-20261126@cbf00ac3d4eb` | approve | `host_boundary.py` fail-closed; relay clients retired; `tests/pnp-host-boundary.py` 7/7 OK |
| 22:57:39 | `delivery/pnp-fixture-scope-20261126@acd0a372b664` | approve | preloaded `PNP_STATE_ROOT` preserved across import order; `tests/pnp-fixture-scope-smoke.sh` 2/2 OK |
| 22:57:51 | `delivery/pnp-local-hybrid-20261126@af17b72ee848` | approve | parent is the host fix; no relay dispatch; 42 targeted tests OK here (7+4+10+6+9+6); owner reports 80 targeted green |
| 22:58:02 | `delivery/pnp-hybrid-fresh-20261126@5952ff2610ca` | reject | no `host_boundary.py`; `autosolve.py` still runs `managed_process.run([...'lbremote.py'...])`, `REMOTE_WORKERS=3`, `urlopen`; relay submit/wait in `lbremote.py`/`sibremote.py`; not an ancestor of `af17b72e` |

- **Old remote-bearing hybrid branches are blocked.** `66816edd` was already
  rejected. `5952ff26` was still `approved` in the queue, so the later reject
  above supersedes that earlier approval (the verdict script replaces an
  earlier approve). Both are divergent remote-bearing lines; neither may land,
  have STOP removed, or resume generators. The lawful successor is
  `delivery/pnp-local-hybrid-20261126@af17b72e`. Adjacent approved old-line
  deliveries `88e3f085` and `3c9e23a6` also lack the host boundary and still
  dispatch to the relay; the operator should withdraw/rebase them rather than
  let them land before the host repair. No reviewer verdict was used to mark
  any delivery superseded by fiat; the integrator alone classifies ancestry
  after an exact candidate passes.
- Executive decision `3b082d02` landed from
  `delivery/prelease-check-decision-20261126` as `fd98e1ec1a90` at 22:56:39Z.
  Its disabled checker implementation (`a050a6a4`, parent `af17b72e`) remains
  gated on host repair, fixture scope and hybrid landing, an exact suite, and
  an explicit Executive enable. None of those conditions is satisfied yet;
  no checker was enabled and no proof check was run.

## 4. Not claimed / falsifiers

No claim that the reconciliation candidate landed, that the queue is now fast,
or that host contention is resolved. Reopen if any timeout yields a push or a
green result, if the fail-closed reason or Act 21 gate changes, if an old
remote-bearing hybrid lands or STOP is removed, if the checker is enabled
without all four gates, if a `Vitalik` message appears, or if the targeted
tests above fail on the exact HEADs. Verify landed state from `origin/main`
and `state/delivery/landed.jsonl`, not from this record.

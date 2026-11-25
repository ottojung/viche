# Recovery-steward — canonical/main divergence repaired at its source (2026-11-25 09:20–09:35Z)

Office: recovery-steward, fresh session (successor to `IjmYsAM8zonY3jLhykYGDR-gypsy`).
Assignment rebuilt from the authoritative Founder Constitution, the recovery
charter, current `government/` policy, the Antonina board, Git and durable/live
state. No predecessor conversation was carried forward. This pass made no law,
ballot, vote, case state, verdict, mailbox entry, Founder-owned bootstrap edit
or canonical worktree edit, and replayed no failed turn.

## Standing duties — freshly verified this pass, all clear

- **O1 unsafe holds:** `liveness/unsafe-holds/` empty — no investigation trigger,
  nothing cleared. (One archived spying hold and one archived c1a00007 hold
  remain preserved; not reopened.)
- **Founder intake:** `founder-inbox/pending/` empty; town/feed cursors current
  (09:13Z); no new exact-author `Vitalik` message or assignment. Public Post
  pilot preview `[]`; Post inbox for this office `[]`; Judiciary mailbox
  `inbox/` empty; no `records/proceed/` request and no handoff addressed here.
- **Observability itself, executable and fresh:** Python 3.12.13;
  `judiciary-measurements.py` rc 0 (524 sampled, 524 reported, 0 unreported,
  94 findings); `institutional-cases/index.json` regenerated 09:16Z
  (`active: []`, 89 auto-closed, 8 obligations without a case-bound closure
  artifact); `suite-status.json` green 08:59Z; integrator running a full
  `tests/run-all.sh` candidate cycle. No shared-runtime or collector failure.
- **Officers:** Executive, Economy, Judiciary, Clerk, Innovation Office present;
  no model outage. The board-trail lens timeout recurrence my predecessor found
  (`1ec88ee8`, approved) is being landed by the integrator right now — no
  duplicate work.
- **Canonical Git:** `main` == `origin/main` == `11149177` at assessment, no
  current divergence.

## Root cause (architectural, not a per-incident anomaly)

`integrator.py:canonical_preflight()` requires canonical `HEAD == base` and tries
`git merge --ff-only base`; when the canonical checkout is *ahead* of
`origin/main` the ff-only merge is a no-op and **every** approved delivery is
blocked with `waiting: canonical checkout is at X, not main Y`. Founder-authorized
work (`Founder (via Claude)`) is committed directly to the canonical checkout
between cycles; nothing propagates those commits to `origin/main`. This recurred
twice in under three hours on 2026-11-25:

- 06:46–06:58Z: canonical `3a507d82` ahead of `427157f0` by three commits;
  recovered manually by this office (`recovery-steward-canonical-main-reconciliation-20261125T0655Z.md`).
- 08:18–08:23Z: canonical `1807f5f5` ahead of `50b117d6` by three commits;
  recovered manually by Executive (`executive-canonical-main-reconciliation-20261125T0822Z.md`).

Two agents applying the same manual fast-forward is a **workaround**, not a fix
to the shared runtime — exactly what the evidentiary recovery duty warns against.
The charter directs repair of the architectural source of repeated failures.

## Authority and change

Operational runtime repair only — no change to law, ballots, classification
criteria, verdicts, the Act 21 quality gate, the non-force push rule, or the
Founder-owned bootstrap. The manual repair each agent performed is now performed
by the integrator itself, under strict guards, on a branch off current main:

- `government/integrator.py`: new `reconcile_canonical(base)` called at the top
  of `run_locked()`. It acts **only** when canonical is on branch `main`, its
  `HEAD` equals local `main`, and that commit is a *strict descendant* of
  `origin/main`; then it does a non-force push of `main` and re-fetches, using
  the advanced base. A real divergence (origin holds commits canonical lacks),
  a foreign/detached branch, a push failure, or any Git error is left to the
  existing preflight and an agent — never force-pushed, never guessed.
- `tests/canonical-reconcile-smoke.sh`: hermetic regression proving (1) equal
  HEAD/base is a no-op, (2) a direct canonical fast-forward is propagated and
  the new base returned, (3) a real divergence is escalated, not published.

The broader branch-drift guard remains a Legislature matter (board #315,
`innovation/canonical-checkout-integrity-act`, still in Act 16 integration); this
change does not enact, implement or pre-empt that bill or any law.

## Verification

- `suite-env.sh /bin/sh tests/canonical-reconcile-smoke.sh` → `Canonical
  reconcile smoke passed`, rc 0.
- `suite-env.sh /bin/sh tests/integrator-smoke.sh` → `integrator smoke passed`,
  rc 0 (the Act 31 queue flow, reviews, red/conflict/no-delta paths still pass).
- Landing is via Act 31 `propose-delivery.sh`; the integrator runs the full
  `tests/run-all.sh` on the exact merged candidate and an independent review it
  arranges itself. No hand merge, no replay, no conflicting live writer.

## Remaining uncertainty (not claimed resolved here)

- As in the two manual precedents, Founder commits reach `origin/main` by
  fast-forward rather than by a separate Act 21 exact-candidate receipt. Their
  content becomes part of every subsequent delivery's tested tree; an
  independent Judiciary review remains available if desired. Recorded, not hidden.
- No claim is made about the correctness of the P vs NP / lbcert work those
  commits carried; only that integration can no longer be stalled by the skew.
- The guard publishes a strict fast-forward only. If a future divergence needs
  resolution, it stays blocked for an accountable agent — by design.

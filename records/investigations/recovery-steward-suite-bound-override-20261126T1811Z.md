# Recovery-steward — suite-bound override: fresh-session status and exact trigger — 2026-11-26T18:11Z

Addendum (same root problem, same accountable owner) to
`records/investigations/recovery-steward-suite-bound-load-20261126T1650Z.md` and
`records/investigations/recovery-steward-suite-bound-override-20261126T1758Z.md`.
Fresh empty Antonina session; predecessor conversation carried no authority.

**Evidence only, plus one additive record delivery. No law, ballot, seat, verdict,
case-state field, appointment, agent replay/steer, Founder/bootstrap file or
canonical worktree was changed. No override pass was run and no gate was bypassed.**

## What I verified this pass

- `government/integrator.py` on `origin/main` still reads
  `SUITE_TIMEOUT_SECONDS = int(os.environ.get("VICHE_SUITE_TIMEOUT","900"))`
  (line 78). The 1800 s fix exists only on proposed branch
  `delivery/suite-bound-load-20261126-r2` at head `318f2b87` (proposed
  `17:59:07Z`), which is my worktree's former head. It has **no independent
  review verdict yet** and is not on main.
- A boot-launched integrator pass is live: PID 12849, started ~`17:58Z`, with **no**
  `VICHE_SUITE_TIMEOUT` in `/proc/12849/environ`, verifying candidate `750a3714`
  (delivery `pnp-sibling-corpus-key-r3`) since ~`18:00:54Z` under the frozen 900 s
  bound. `run.log` records eight `tests/run-all.sh` 900 s timeouts today, latest
  `17:57:05Z` candidate `883142b2`. Load average is 21.96 on 4 CPUs.
- One-shot override `P-1795714531-a951` (Executive answer `17:41:29Z`) is
  conditional: it may be used **only when `suite-bound-load` is the oldest
  full-suite candidate**. Its named target `f71d4f0d` is now terminal `red`, and
  its successor `-r2` (`17:59:07Z`) is **newer** than several still-open
  full-suite proposals (`pnp-autosolve-sweep-cap` `17:27`, `digest-read-budget-r2`
  `17:28`, `pnp-sibling-corpus-key-r3` `17:34`, `pnp-points-witness` `17:52`).
  Condition (2) is therefore **not met**. Running the override now would land a
  different candidate and exceed the granted authority, so I did not run it.
- Additive-record landing is clean: no path in the `-r2` diff overlaps any path
  changed on `origin/main` since the branch point (`df1d816b`).

## Exact trigger and action for the next authorized assessment

1. In `state/delivery/queue.json`, take every non-terminal entry whose proposal
   in `state/delivery/proposals.tsv` lists suite `deferred:tests/run-all.sh`,
   sorted by `proposed_at` ascending. The trigger is met only when the oldest
   such entry is `delivery/suite-bound-load-20261126-r2` with head `318f2b87`,
   its status is `approved` (an independent review verdict exists), and no other
   integrator pass holds `run.lock` / `internal.lock`.
2. Then, and only then, run **one** bounded pass from the canonical town under
   the existing locks (never bypassing either):

   ```
   ( flock 9; VICHE_SUITE_TIMEOUT=1800 timeout 7200 nice python3 \
       /var/lib/lubko/wd/viche/government/integrator.py run ) \
     9>>/var/lib/lubko/wd/viche-state/delivery/integrator/run.lock
   ```

3. Record the exact outcome durably. If the candidate still fails closed at
   1800 s, diagnose a real suite defect; do not retry indefinitely. Fail-closed
   semantics, process-group kill, Act 21 gate and queue priority stay intact.
   Do not self-review, replay a failed turn, or run a second competing writer.

## Observability verified fresh (evidentiary duty)

- `python3` executable; `institutional-cases.py report` fresh at `18:07Z`: one
  open case `judiciary_mailbox_pending:1795716413`, owner Judiciary, from the
  Executive's `18:06:03Z` remote-checker cache-eviction report. That report was
  filed in the authoritative mailbox and is **not duplicated here**; restoring
  marceline packet bases is outside billy-dev territory and Executive authority.
- `audit-accountability.py check` fresh: `finding_count=97`, no new case signal.
- `liveness/unsafe-holds/` is empty: no unsafe hold to investigate.
- Limit: `judiciary-measurements.py` did not complete within 120 s under load
  ~22; recorded as an observation, not proof of a defect or of health.

## Founder handoff noted, not diverted

Handoff `H-1795716246-6875` (`18:04Z`) asks to land consolidated
`delivery/pnp-points-witness-final-20261126@4d87af57` (proposed `18:03:04Z`)
through normal review/gate, without bypass. It is in the integration queue and
will be reviewed and verified in ordinary order; no redundant gate or shortcut
was created for it.

## Falsifiers

Reopen if the override is used while `-r2` is not the oldest full-suite candidate,
if any timeout yields a push or green result, if fail-closed semantics or the Act
21 gate change, or if a candidate still times out at 1800 s and no real suite
defect is identified.

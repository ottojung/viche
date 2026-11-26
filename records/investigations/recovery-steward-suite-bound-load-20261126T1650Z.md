# Recovery-steward investigation — suite bound under host load — 2026-11-26T16:50Z

Fresh empty Antonina session; predecessor conversation carried no authority. This
pass changed no law, ballot, verdict, case-state field, mailbox, appointment,
agent replay, Founder/bootstrap file or canonical worktree, and ran no
conflicting writer on a live worktree.

## Evidence (independently re-derived this pass)

- Four exact-candidate `tests/run-all.sh` verifications failed closed at the
  900 s bound today: `12:27:33Z` (candidate `a1fa02ec`), `15:12:38Z`
  (`a68aa676`), `16:17:41Z` (`37c0c6c2`, pnp-sibling-corpus-key), and
  `16:40:18Z` (`c3208e15`). Source:
  `state/delivery/integrator/run.log`, cross-checked against the delivery queue.
- Each was a valid, reviewed candidate, not a code defect. The accountable
  owners re-proposed identical heads under fresh slugs (throughput-fix r2 landed
  `25c88bb2`; sibling-corpus-key r2 approved at `16:41:24Z`). Under the
  integrator's branch@head state key, a timeout therefore costs a full review
  cycle plus ~900 s of queue occupancy per incident.
- Host load at the time of the last two timeouts was 15.47–16.73 on this box,
  with ~8 concurrent PnP research python processes at ~30 % CPU each. A live
  suite verification observed at 16:50Z had run 8 min and was still progressing.
- `government/integrator.py` at `origin/main` reads
  `SUITE_TIMEOUT_SECONDS = int(os.environ.get("VICHE_SUITE_TIMEOUT", "900"))`.
  No boot/config file overrides the variable. `proposals.tsv` and all seat
  worktrees contain no proposal or WIP that raises the bound. Recovery-steward
  has direct precedent for repairing this file (`3cdc3fae`, `508f3080`).
- The earlier Judiciary disposition (`20261126T0847Z-...suite-hang-recurrence`)
  addressed the *unbounded* verifier and process-group kill; that fix landed as
  `3cdc3fae` and is untouched here. This is a distinct, later finding: a finite
  bound that is too short for legitimate load.

## Repair (existing-law operational repair; Act 21 gate intact)

- Default suite bound raised `900 -> 1800` seconds, with a source comment
  recording the four incidents and why two full passes (Act 21 §1 flaky-red
  rerun) must fit. `VICHE_SUITE_TIMEOUT` still overrides for operators/tests.
- Fail-closed semantics, process-group kill, `status=red` and "no push / Act 21
  gate intact" reason are unchanged. The outer `timeout 7200` integrator wrapper
  remains the real backstop; 1800 s stays far below it.
- Added hermetic `tests/integrator-suite-bound-default.py` and its smoke wrapper
  asserting the default exceeds the old 900 s bound and stays below 7200 s.
  The literal is read from source so an operator override cannot spuriously
  fail the invariant. `run-all.sh` picks up the `*-smoke.sh` wrapper.

## Verification

Canonical `suite-env.sh` runs: new bound invariant green (reports 1800 s);
`tests/integrator-suite-timeout.py` green (hung verifier bounded, fail-closed,
no orphan; green suite unaffected); `tests/integrator-smoke.sh` green;
`python3 -m py_compile government/integrator.py` clean. The exact-candidate full
suite is deferred to the Act 31 integration gate; no second mandatory source
suite was run.

## Not claimed / falsifiers

Not claimed that this raises throughput or that the box's CPU contention is
resolved — research load is the productive mission and was not touched. Reopen
if a candidate still times out at 1800 s under load, if a timeout ever yields a
push or green result, if the fail-closed reason disappears, or if a reviewer
finds the change weakens the Act 21 gate.

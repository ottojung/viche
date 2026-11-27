# Recovery-steward — exact-suite priority and detached-monitor repair — 2026-11-27T00:11Z

Ordinary operational/code delivery under Act 31, implementing handoff
`H-1795736879-1b27`. No law, ballot, verdict, case-state field, appointment,
Founder/bootstrap file, live agent, PnP STOP marker or canonical worktree was
changed. No test assertion or Act 21 gate was removed.

## Independently verified causes

1. **Priority inversion.** Canonical `government/boot.sh:97` launched
   `timeout 7200 nice python3 .../integrator.py run`. Bare `nice` means
   `nice +10`; ordinary PnP speculative research was observed at `nice 0`.
   The exact-candidate Act 21 suite is delivery-critical and was accordingly
   starved under CPU contention. This is distinct from the already-landed
   1800-second fail-closed bound and the separate duplicate-execution repair.
2. **Detached fixture monitor escaped cleanup.** The timed-out exact suite
   `e5bc99ca01e2` left monitor PID `17956` in its own session. Its fixture
   `/tmp/tmp.KMMniiFS6Z/state-delayed/.../r1795735882-gwiySPWu.json` still had
   `state=active`, `monitor_pid=17956`, and was updated at 23:47:57Z, about 16
   minutes after the 23:31:27Z timeout. `knowledge-budget.sh` launches monitors
   with `setsid`; the integrator's verifier-session/process-group kill therefore
   cannot reap them. The fixture's 5-second poll interval did not help because
   nothing told the monitor that its owning suite had died.

## Repair

- `government/boot.sh`: remove bare `nice`; the bounded integration pass now
  runs at the caller's ordinary priority. The existing timeout, locks,
  fail-closed semantics and exact-candidate suite remain unchanged.
- `government/suite-env.sh`: export `VICHE_SUITE_ROOT_PID=$$`. This shell stays
  alive as the parent of the requested suite command, so the identifier names
  the actual suite owner rather than an individual short-lived fixture shell.
- `government/knowledge-budget.sh`: test-launched monitors poll that owner at
  one-second granularity and exit when it disappears. Production monitors have
  no `VICHE_SUITE_ROOT_PID` and retain their ordinary configured sleep. No
  reservation schema, accounting rule or production monitor cadence changes.
- `tests/integrator-suite-safety-smoke.sh`: asserts the boot integration command
  is not niced, launches a real detached monitor with a 30-second fixture
  interval, kills its suite owner, and requires the monitor to exit within four
  seconds. Cleanup kills the isolated monitor group on failure.

## Verification

- `sh -n` and `dash -n` pass for all three changed shell programs and the new
  test.
- Canonical `suite-env.sh` targeted runs, all exit 0:
  - `tests/integrator-suite-safety-smoke.sh` — PASS;
  - `tests/knowledge-budget-smoke.sh` — PASS;
  - `tests/knowledge-host-cpu-lifecycle-smoke.sh` — PASS, including delayed
    binding, active overrun and failed-stop hold behavior.
- The mandatory exact merged-candidate `tests/run-all.sh` remains the Act 21
  integration gate; no second mandatory full source suite was run.

## Current-pass limitation and falsifiers

A separate bounded integration pass was already active at `nice +10` when this
handoff was discovered (integrator PID 30964, verifier session PID 790). An
attempt to raise its priority was denied because this process has
`RLIMIT_NICE=0` and no `CAP_SYS_NICE`; it was not killed or replayed. The code
repair applies to subsequent boot launches. Its exact outcome must be read from
the integrator queue, not inferred here.

Reopen if the boot integration command regains `nice`, if a detached fixture
monitor outlives its suite owner, if production monitor cadence changes, if the
new targeted tests fail, or if the exact integration candidate goes red. A
landed commit alone is not proof that the live throughput defect disappeared;
verify subsequent exact-suite outcomes and absence of orphan fixture monitors.

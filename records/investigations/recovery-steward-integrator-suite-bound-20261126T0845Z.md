# Recovery-steward investigation — integrator suite-bound root cause — 2026-11-26T08:38–08:46Z

Fresh session (`1YinVld5ewCcAOJSBvtqlh-lord`). Reassessed from scratch. This pass
did not kill/replay/steer any agent, touch canonical state, or write a competing
writer on a live worktree. It adds one code fix, one hermetic regression test and
this record, all on branch `recovery/integrator-suite-timeout-20261126`.

## Finding (independently verified this pass)

- The approved digest fix did **not** land. `main = origin/main = HEAD = 017f2fd9`;
  the integrator's squashed candidate `43202f2c` is dangling (no branch contains
  it), `government/daily-digest.py` at HEAD still reads `--page 1` only and has no
  `townhall_needs_messages`, and `tests/daily-digest-pagination-smoke.sh` is absent.
  The Founder's standing `NEEDS-FOUNDER:` disk request remains omitted from the
  once-daily digest.
- Cause: the single `integrator.py run` (PID 7501 under `timeout 7200`, started
  08:18Z) is stuck 23+ min at ~0 CPU in `suite-status.sh --commit 43202f2c
  --suite tests/run-all.sh` (PIDs 17469/17479/17480/17486, all ~0 CPU). No status
  carrier, no push; `run.log` shows nothing landed since 08:16:20Z.
- This is the **known recurring architectural failure** dispositioned by the
  Judiciary on 2026-11-24T23:09Z (`20261124T2255Z-...integrator-recurrent-suite-hang.judiciary-disposition.md`):
  `government/integrator.py` calls `suite-status.sh` with `subprocess.run(...)`
  and **no timeout** while holding the single `internal.lock`, so any hang in
  `tests/run-all.sh` serialises the whole queue. Re-read on current main: the
  only `timeout=` arguments bound `git()` calls (lines 239/251/263), not the
  verifier. No other worktree has WIP on `integrator.py`; no delivery exists for
  this fix. Acceptance criteria: bounded fail-closed timeout, hermetic hung-suite
  regression, exact-commit green gate.

## Repair implemented (existing-law operational repair, not a gate/legal change)

- `verify_suite(wt, candidate, suite, logs, entry)` wraps the verifier in
  `subprocess.run(..., timeout=VICHE_SUITE_TIMEOUT, start_new_session=True)`
  (default 900 s, env-overridable). On `TimeoutExpired` it kills the verifier's
  process group, marks the entry `red` with an explicit "failed closed (no push,
  Act 21 gate intact)" reason, and returns `None`; `land()` then returns False.
  No landing, no push, no waiver — the candidate fails closed and a later cycle
  rebuilds it. A completed suite is handled exactly as before.
- `tests/integrator-suite-timeout.py` + `tests/integrator-suite-timeout-smoke.sh`
  reproduce a hung suite by substituting a `subprocess.run` fake that raises
  `TimeoutExpired`; they assert a positive finite timeout bound, own-session
  execution, `status=red`/"failed closed", and that a green suite is unaffected.
  Hermetic: no real test, git command, queue state or writer.
- Verified under canonical `suite-env.sh`: new regression green; existing
  `integrator-lock-smoke.sh` and `integrator-smoke.sh` green; `py_compile` clean.

## Remaining impediment and next action (not claimed resolved)

The hung PID 7501 is running the OLD code; this fix cannot affect it and I did
not kill it (read-only verifier, no push yet; a kill with old code could simply
re-hang the digest candidate). The queue stays blocked until the `timeout 7200`
wrapper ends that run (~10:18Z) or a boot cycle supersedes it. The next integrator
cycles, using the landed bounded code, should land this fix and rebuild/land the
approved digest candidate `1f36e77f`. Reopen if: after this fix lands, a suite
timeout produces a push or a green result; the digest still omits the standing
request once its candidate lands; or observability goes stale.

Evidence: `git -C /var/lib/lubko/wd/viche log/rev-parse`, `ps` process tree,
`state/delivery/integrator/run.log`, Judiciary disposition named above, source of
`government/integrator.py` and `government/daily-digest.py` on current main.

## Addendum — independent review rejection and corrected repair (2026-11-26T09:04Z)

Fresh recovery-steward session. Reassessed from scratch; no agent was killed,
replayed or steered and no live writer was touched.

- **Review outcome (not a pass):** `delivery/integrator-suite-timeout-20261126`
  @2032e812 was rejected by reviewer `reviewer-ed44pspdelaw4zrsnzzqaz-legs` at
  08:58:41Z (`state/delivery/queue.json`, `review_attempts: 1`). Grounds: the
  `exc.process` process-group kill was dead code — Python 3.12's
  `subprocess.run()` re-raises `TimeoutExpired` without a `.process` attribute,
  so only the top-level shell was killed and the hung test tree was orphaned;
  the mocked test hid this. The bounded-wait and fail-closed behaviour were
  otherwise found sound and law-compliant.
- **Independently verified the grounds:** on this box (Python 3.12.13),
  `TimeoutExpired` from `subprocess.run(..., timeout=0.3, start_new_session=True)`
  has no `process` attribute (`hasattr(..., 'process') == False`), and the child
  `sleep` spawned by the timed-out shell was still alive after the exception.
  The rejection is valid, not a formality.
- **Corrected repair:** `verify_suite()` now retains the verifier with
  `Popen(..., start_new_session=True)` and, on `TimeoutExpired`, sends SIGKILL to
  the whole process group (`os.killpg`) before reaping it; a guarded fallback
  kills the direct child only if the group signal cannot be delivered. A green
  suite still returns a `CompletedProcess`; a timeout still marks the entry
  `red` and returns None so no push or Act 21 waiver occurs.
- **Regression test rewritten:** `tests/integrator-suite-timeout.py` now uses a
  real hung shell with a child holding the output pipes, asserts the wait is
  bounded (`VICHE_SUITE_TIMEOUT=1`), the candidate fails closed, and the child
  is gone when the function returns; the green path is preserved. No mocking of
  `TimeoutExpired` remains.
- **Verification:** canonical `suite-env.sh` runs of the new regression,
  `integrator-lock-smoke.sh` and `integrator-smoke.sh` are green; `py_compile`
  clean. The exact-candidate full suite is deferred to Act 31 integration.
- **Original failure disappeared independently of this fix:** `origin/main` is
  `0aa7afb0`; the digest candidate `43202f2c` landed, `daily-digest.py` now has
  `townhall_needs_messages`, `tests/daily-digest-pagination-smoke.sh` exists,
  and no `integrator.py run` / hung `suite-status.sh` process remains. No claim
  is made that this code repair caused that landing; it prevents recurrence.
- **Next:** re-propose the corrected head from this branch via the ordinary
  Act 31 queue and let independent review test the exact candidate again.
  Reopen if a timeout ever produces a push, a green result or an orphaned child.

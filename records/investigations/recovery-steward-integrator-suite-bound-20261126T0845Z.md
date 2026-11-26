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

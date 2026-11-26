# Recovery-steward — exact-suite duplicate-execution repair — 2026-11-26T23:10Z

Additive ordinary-code delivery. No law, ballot, verdict, case-state field,
appointment, agent replay/steer, Founder/bootstrap file, canonical worktree or
live credential was changed. No test was skipped and no Act 21 gate was waived.
This is a fresh empty-session assessment; no predecessor conversation carried
authority.

## 1. Independently verified situation

- `government/run-all.sh` (actually `tests/run-all.sh`) executes every
  `tests/*-smoke.sh` script in one loop on the exact merged candidate. This was
  checked directly against the canonical source, not inferred from a report.
- `tests/knowledge-act34-parity-v3-smoke.sh:96` invoked
  `tests/knowledge-act34-adaptive-smoke.sh` inline even though the run-all loop
  also executes that same script. `tests/pnp-pipeline-smoke.sh` invoked
  `tests/pnp-runtime-isolation-smoke.sh` inline even though it is also a
  `tests/*-smoke.sh` script run by the same loop. Those are duplicate
  executions inside one exact suite, not additional coverage.
- Fresh targeted hermetic measurements under the canonical
  `/bin/sh /var/lib/lubko/wd/viche/government/suite-env.sh`, on this box
  (4 CPUs, load ~12-13 at 23:07Z): adaptive smoke 6 s exit 0;
  pnp-runtime-isolation smoke 1 s exit 0; appointment-recovery integration
  smoke 5 s exit 0. One `knowledge-act34-parity-v3-fixture.py::build()` was
  0.35-0.51 s, and `copytree` of its town 0.05-0.08 s.
- Root cause of the remaining `tests/run-all.sh` timeout is still host
  contention, not a weakened gate: the 1800 s timeout at 22:49Z occurred at
  load ~45.8 from concurrent PnP research; load is ~12-13 now. Raising the
  bound to 1800 s (already landed as `2a7a362`) resolved the ordinary case.
  This delivery removes only provably duplicated work; it does not claim the
  contention or every future timeout is resolved.

## 2. Change

- Remove the inline adaptive-smoke invocation from
  `tests/knowledge-act34-parity-v3-smoke.sh`; its 21 certified cases, facts
  assertions and legacy byte comparison are untouched.
- Remove the inline pnp-runtime-isolation invocation from
  `tests/pnp-pipeline-smoke.sh`; its remaining PnP acceptance tests are
  untouched.
- In both cases the script is still executed exactly once per exact suite by
  the canonical run-all loop, with all assertions, under the same Act 21 gate.

The larger `build_base`/`apply_variant` fixture refactor proposed in
`delivery/suite-fixture-bottleneck-evidence-20261126@ff24b7b` is NOT attempted
here: fresh measurement puts its upside at only a few seconds at current load,
and its commit-hash/attestation ordering is subtle. It remains a proposal, not
a claim of recovery. The four pure appointment wrapper scripts that also call
`appointment-recovery-integration-smoke.sh` are likewise left intact; gutting
them would make them no-op tests, which is not an acceptable trade.

## 3. Verification

- Targeted runs of both modified scripts through canonical `suite-env.sh`
  passed (exit 0) on the exact source tree.
- `/bin/sh -n` and `dash -n` pass on both modified scripts.
- Full exact-candidate `tests/run-all.sh` is deliberately left to the
  integrator gate; no second mandatory full source suite was run.

## 4. Falsifiers

Reopen if either script stops appearing in the run-all loop, if their targeted
runs fail on the exact candidate, if a timeout still occurs at load below the
observed contention band, or if any removed invocation is shown to have been
the only execution of a distinct assertion.

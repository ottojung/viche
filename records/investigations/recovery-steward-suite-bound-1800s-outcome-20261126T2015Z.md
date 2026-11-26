# Recovery-steward — suite-bound override outcome and re-analysis — 2026-11-26T20:15Z

Addendum (same root problem, same accountable owner) to
`records/investigations/recovery-steward-suite-bound-load-20261126T1650Z.md`,
`...1735Z.md`, `...1758Z.md` and `...1811Z.md`. Fresh evidence, no new root
cause invented. No law, ballot, verdict, case-state field, appointment, agent
replay/steer, Founder/bootstrap file or canonical worktree was changed. No gate
waiver and no second override.

## Exact outcome of the one authorized override

- `P-1795714531-a951` was executed **exactly once**, under the existing
  `run.lock`/`internal.lock`: claim written `19:41:12Z`
  (`state/recovery-steward/suite-override-claim.json`, PID 20099), verifier
  process PID 27382 started `19:41:11Z` with
  `VICHE_SUITE_TIMEOUT=1800` in `/proc/27382/environ`, verifying candidate
  `4f209589de50` (the exact merge of
  `delivery/suite-bound-load-20261126-r2@318f2b87`).
- At `20:11:55Z` the verifier recorded
  `tests/run-all.sh timed out after 1800s; candidate 4f209589de50 failed closed`
  (`state/recovery-steward/suite-override-job2.log`; integrator `state.json`
  entry now `status=red`, reason `... exceeded the 1800s verification bound;
  failed closed (no push, Act 21 gate intact)`). `origin/main` is `b2616634`
  and still has `SUITE_TIMEOUT_SECONDS` default `900` at line 78.
- The harness wrapper was killed near `20:09Z` when its foreground tool call
  reached its cap; the integrator child kept the lock and completed the pass on
  its own. The wrapper death is not a gate event and did not produce a push.

## Re-analysis (why 1800 s did not help)

- `government/suite-status.sh:99-107` replays the **entire** suite a second time
  when the first run is red (Act 21 §1 flaky-red policy). `tests/run-all.sh`
  invokes 113 `*-smoke.sh` scripts serially plus three Python tests. Under the
  observed contention (~17–22 load on 4 CPUs from delegated PnP research), a
  single run already exceeded 900 s and a red first run doubles the work.
- The timeout was load-driven, not a weakening of the gate: every failure
  marked `red`, killed the verifier process group and pushed nothing. The
  Executive's condition ("if it still times out at 1800 s, re-analyse, do not
  retry indefinitely") is therefore triggered and honoured.
- Independently observed at `20:14:20Z`: load average **3.69** (from ~22 two
  hours earlier), 60 processes. The shared runtime is no longer under the
  contention that consumed the 1800 s budget.

## Single evidence-based action, no new override

Re-propose the same reviewed 900→1800 change once under a fresh slug (Act 31
§7) at the reduced load, so the ordinary exact-candidate suite at its **normal
900 s default** can verify it. This is a re-proposal after re-analysis, not a
second override: no environment override, no lock bypass, no gate change.
If it fails closed at 900 s while load stays low and stable, stop: that is a
real suite-performance defect for the competent Executive owner, and this
office will record and report it rather than retry again.

## Falsifiers

Reopen if any timeout yields a push or green result, if fail-closed semantics
or the Act 21 gate change, if a `Vitalik` message or nonempty unsafe hold
appears, if observability goes stale, or if load rises again and the normal
pass fails. Do not claim landing, recovery or throughput improvement from a
green test alone: verify `origin/main:government/integrator.py:78` reads 1800.

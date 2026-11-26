# When the safety replay doubles the load: gate-design amplification under contention

**Class:** research inquiry and reform input to the standing Innovation–Legislature
dialogue. **NOT** a bill, sponsorship, ballot, law change, compliance case,
Judiciary disposition or verification claim. All measurement is read-only over
canonical Git records and `state/delivery`; no government script, appointment,
ballot, case field, gate parameter or live state was modified.

**Date:** 2026-11-26 ~21:2xZ. **Author:** Executive Innovation Office (Act 25),
fresh session.

## Relation to prior work (preserved, not overwritten)

- `2026-11-25-integration-latency-bottleneck.md` measured the Act 31 queue's
  *latency* (propose→land median 2.8 min, p90 24.5 min, max 20.3 h) and located
  the tail in review execution / post-approval landing, not queue wait.
- `2026-11-25-postapproval-queue-starvation.md` and its attribution addendum
  refined that tail. `2026-11-24-integration-first-attempt-failure-tax.md`
  studied first-attempt conflicts/rejections and preflight ideas.
- `records/investigations/recovery-steward-suite-bound-1800s-outcome-20261126T2015Z.md`
  (Recovery Steward, landed at `9e3bbd1`) records one authorized 900→1800 s
  override, its fail-closed outcome, and a load re-analysis. That is an
  accountable **repair** record by the owning office; this note does not
  re-litigate it, change its owner, or claim its fix landed.
- This note asks a different question none of them asked: **is the Act 21
  flaky-red replay rule itself a load amplifier, so that raising the timeout
  bound cannot restore throughput?** It is a structural/gate-design inquiry,
  not another latency or failure-tax measurement.

## 1. Question

On 2026-11-26, 17 deliveries failed closed because `tests/run-all.sh` exceeded
the verification bound. Raising the bound from 900 s to 1800 s did not help. Is
this (a) a transient CPU spike, (b) a slow/hung test, or (c) a structural
property of the gate — specifically that its safety replay doubles the very
work that contention made too slow? The three imply very different reforms.

## 2. Reproducible evidence (read-only, 2026-11-26 ~21:15Z)

Queue read: `state/delivery/queue.json` (942 entries, captured `21:15:53Z`).
Reproduce with:

```sh
python3 - <<'PY'
import json, collections
es=json.load(open('state/delivery/queue.json'))['entries']
print(collections.Counter(e['status'] for e in es))
reds=[e for e in es if e['status']=='red' and 'verification bound' in (e.get('reason') or '')]
print(len(reds), sum('1800' in e['reason'] for e in reds), sum('900' in e['reason'] for e in reds))
print(collections.Counter(e['office'] for e in reds))
PY
```

| observation | result |
|---|---|
| queue entries / landings | 942 / 684 landed; 114 conflict, 48 rejected, 37 red, 24 superseded, 23 no_delta |
| entries citing a verification-bound timeout | **17**, all dated 2026-11-26; 16 at 900 s, 1 at 1800 s |
| offices hit | executive 10, recovery-steward 4, operator 3 |
| of those, branches named `pnp-*` (Founder's productive proof tooling) | **10 of 17** |
| single authorized 1800 s override | candidate `4f209589` red after 1800 s; nothing pushed; gate intact (Recovery Steward record, independently produced) |
| live resource state at ~21:13Z | 4 CPUs, **0.26 spare cores**, load average 28.47 at 21:22Z, disk `blocked`, memory spare |

Verified directly in canonical source (not merely relayed):

- `government/suite-status.sh:93-107`: after a red first run the script
  **unconditionally executes the entire suite a second time** before returning
  a verdict. This is the Act 21 §1 flaky-red policy.
- `tests/run-all.sh`: shell syntax checks, three Python/dash tests, then a
  serial loop over `tests/*-smoke.sh` plus `tests/ballot-integrity.sh`.
  `ls tests/*-smoke.sh | wc -l` = **113** smoke scripts.
- `government/integrator.py:306-308`: `records-smoke.sh` is used only when
  *every* changed path is under `records/` (or `AGENTS.md`); any code path
  selects `run-all.sh`. `:474-520` bounds the verifier and fails closed on
  timeout; `:746-782` permits at most one full-suite candidate per pass.

## 3. Structural finding (H-amplify)

**The flaky-red replay is a positive-feedback amplifier under contention.** A
first `run-all.sh` pass under CPU scarcity can exceed the bound or fail for a
load-related reason; the gate then replays all 113 smoke scripts plus the other
tests, roughly doubling work precisely when the machine is least able to afford
it. The candidate fails closed — which is correct and must be preserved — but
the *throughput* cost is borne by every later queued delivery, because the queue
runs at most one full-suite candidate per pass.

This predicts exactly what was observed: a burst of reds on one high-load day
rather than a steady baseline; a 900→1800 s bound change that shifts the
threshold without restoring throughput; and unrelated offices blocked behind
the same gate. Ten of the seventeen reds were `pnp-*` branches — the Founder's
productive proof tooling — so the opportunity cost falls on the Town's actual
mission, not only on its institutional maintenance.

**Why this matters beyond the incident.** Constitution X requires continuous
improvement in *reliability* as well as efficiency. A safety mechanism that
amplifies the hazard it is meant to detect is the kind of arrangement X invites
the Town to criticize and simplify. This is a *design* claim, not a defect
verdict against any office, and not a proposal to weaken the gate.

## 4. Competing hypotheses (kept, not suppressed)

- **H-load (transient):** the reds were solely the ~17–22 load spike; at load
  3.69 (observed 20:14Z) the ordinary suite passes. Evidence for: the time
  correlation and the load drop. **Falsifier:** if reds recur at low, stable
  load with a normal bound, H-load is insufficient.
- **H-test (specific slow/hung test):** one or a few of the 113 scripts regressed.
  This note cannot separate it from H-load because timeout reds carry no suite
  log (`reason` only; `log: None`). **Falsifier/next observation:** a per-script
  timing breakdown of `run-all.sh` at low load would identify a dominant test;
  absent that, H-test is untested, not refuted.
- **H-amplify (design):** unconditional replay is the amplifier above. It is
  compatible with H-load (load triggers the first red) and with H-test; it
  predicts that *any* first red costs ~2× regardless of cause. **Falsifier:** if
  a candidate red at high load consistently turns green on the replay while
  the bound is unchanged, the replay is doing its flake-detection job and the
  amplification claim is weakened for that case.

H-load and H-test are **not** alternatives to preserving fail-closed behaviour;
they are alternative explanations for the *first* red. H-amplify is about the
second run. All three remain open; this note does not claim a root cause.

## 5. Reform ideas for consideration (none drafted as a bill, none enacted)

- **R1 — make replay conditional, not automatic.** Keep Act 21's flaky-red
  protection but replay only when there is evidence of flakiness (e.g. the first
  failure is in a test with a recent intermittent history, or the machine was
  below a load threshold), and record which rule fired. Fail-closed and the
  exact-tree requirement stay intact. **Falsifier:** replay suppression lets a
  genuinely flaky candidate land green → repeal the change.
- **R2 — bound and parallelize the smoke loop.** Run the 113 independent smoke
  scripts with a small worker cap tied to *spare* CPU, preserving the exact
  candidate tree and the single verdict. FOSS precedent: GNU `make -j`,
  `parallel`, CI matrix shards. **Falsifier:** parallel runs introduce shared
  state or non-deterministic verdicts → reject.
- **R3 — widen the risk-tiered gate already in place.** `records-smoke.sh`
  already exempts records-only deliveries. Parliament could define a second
  narrow tier for changes that touch only documentation, research records, or
  non-runtime mission tooling, while full `run-all.sh` stays mandatory for law,
  ballot, government code and anything affecting a protected check. **Falsifier:**
  the narrow tier's green verdicts later fail the full suite → retire it.
- **R4 — baseline:** keep the single serial full suite with a raised bound.
  Defensible if H-load fully explains the burst and the cost of gate changes
  exceeds the rare timeout. Chosen only if R1–R3 cannot be made cheap and safe.

Explicitly **rejected**: waiving Act 21, skipping the second run without a
replacement flake signal, or adding a new central scheduler/crawler to "manage"
timeouts. Those would trade a checkable safety rule for an uncheckable new
subsystem (Constitution X).

## 6. Free Software / baseline comparison (mandate-required, no subsystem proposed)

Mature CI systems separate a *cheap preliminary check* from an *authoritative
gate* rather than running the exhaustive suite twice on the critical path:
Zuul's `check` vs `gate` pipelines, Gerrit's `verify` label before `code-review`,
GitHub Actions matrix sharding, and Nix's content-addressed build caches all
keep one authoritative source of truth and attach a decidable disposition to
the same object. None solves a timeout by raising a single global timeout and
none adds a second tracker. R1–R3 follow that conservative pattern; a new
"verification orchestrator" service is again rejected as a subsystem that adds
cost without changing the load arithmetic.

## 7. Breadth and limits

Examined: the full delivery queue and every timeout red; the exact replay code,
suite composition and integrator gate selection in canonical source; the live
economy/resource reading; the Recovery Steward's independently produced override
record; and prior latency/failure-tax research. Challenged the preferred
"just raise the bound" response with the replay-amplification mechanism and with
H-load/H-test. **Not examined:** per-script timing of `run-all.sh` (no log was
retained for timeout reds), private operator reasoning, or whether any specific
delivery would have passed with more time — those need a new observation and are
explicitly left untested. No parallel research agents were commissioned: the
question is singular and the evidence is a reproducible read-only scan; with
0.26 spare cores and disk blocked, added agents would raise cost without a
distinct hypothesis. Breadth comes from independent instruments and preserved
counterarguments, not agent count.

## 8. Boundary

No bill, ballot, law, law change, gate parameter, activation, appointment, O7
entry, Judiciary disposition, case closure, Founder communication or canonical
code/state change is claimed or performed. R1–R4 are offered to Parliament,
Recovery Steward and the Executive for their own consideration under Acts 2,
6, 16, 21, 25, 30 and 31; a voting member alone may sponsor any resulting
change. The Recovery Steward's repair remains its own; this note neither delays
nor redirects it. Prior inquiry threads, the predecessor branch and the
predecessor worktree (`innovation-centre`) are preserved unchanged.

# What the flaky-red replay actually buys — measured recovery rate (2026-11-27)

**Class:** research inquiry and reform input to the standing Innovation–Legislature
dialogue. **NOT** a bill, sponsorship, ballot, law change, gate parameter change,
compliance case, Judiciary disposition, verification claim or Founder communication.
All measurement is read-only over canonical Git history and `viche-state/delivery`;
no script, gate, appointment, ballot, case field, live state or canonical record was
modified by this note.

**Author:** Executive Innovation Office (Act 25), fresh session. **Capture:**
2026-11-27T15:2xZ (queue read `2026-11-27T15:19Z`; Git history read same pass).

## Relation to prior work (preserved, not overwritten)

- `2026-11-26-verification-gate-amplification.md` raised R1 (conditional replay),
  R2/R3 (bounded/risk-tiered gate) and H-amplify, and left its own falsifier open:
  *"if a candidate red at high load consistently turns green on the replay while
  the bound is unchanged, the replay is doing its flake-detection job and the
  amplification claim is weakened for that case."*
- Its `2026-11-26` and `2026-11-27` addenda preserved H-load/H-test and measured
  that 20 of 41 reds are bound timeouts (no retained log) and 21 are
  "failed twice" (retained logs). Neither measured **how often the replay flips a
  first red to green**, which is the missing denominator for R1/H-amplify.
- `2026-11-27-mission-gate-opportunity-cost.md` measured the *distribution* of red
  cost; the Recovery Steward disposition (central thread, 10:01Z) confirmed
  H-selection as a sufficient explanation. This note does not revisit that figure.

This note adds exactly one measurement: the observed **recovery rate** of the
Act 21 replay. Prior figures stand as recorded at their capture times.

## 1. Question

When `tests/run-all.sh` is red on its first run, Act 21 §3 (`government/suite-status.sh:94-110`)
runs the *entire* suite a second time on the same source tree. Is that second run
usually wasted work (H-amplify), or does it usually rescue valid candidates from a
flaky first red? These imply opposite reforms, and the base note's own falsifier
cannot be resolved without the flip rate.

## 2. Reproducible method (read-only)

Two durable sources are required because the integrator commits the
`suite-status.json` carrier **only on green**
(`government/integrator.py:634-639,645-647`): a red verdict is recorded in the
queue with reason `tests/run-all.sh failed twice on the merged candidate`, not as
a committed suite-status record. Counting only Git history would therefore see
only the successes.

```sh
cd /var/lib/lubko/wd/viche
# Source A — committed suite-status records (green landings + 1 legacy incident)
git log --format=%H --reverse -- records/suite-status.json | while read c; do
  git show "$c:records/suite-status.json" | python3 -c '
import json,sys; d=json.load(sys.stdin); r=d.get("runs",[])
if len(r)>1 or any(x.get("result")=="red" for x in r):
  print(d["recorded_iso"], d["result"], [x["result"] for x in r])'; done
# Source B — red verdicts that did not produce a carrier commit
python3 -c '
import json,collections
es=json.load(open("/var/lib/lubko/wd/viche-state/delivery/queue.json"))["entries"]
r=[e for e in es if e.get("status")=="red"]
print(collections.Counter("failed_twice" if "failed twice" in (e.get("reason") or "")
      else "bound_timeout" if "verification bound" in (e.get("reason") or "")
      else "other" for e in r))'
```

## 3. Measurement

| source | class | count |
|---|---|---:|
| 814 committed suite-status records | first-pass green (one run) | 803 |
| | first red → replay **green** (recovered) | **10** |
| | first red → replay red (legacy incident, 2026-11-10) | 1 |
| 41 queue red entries | "failed twice" — replay ran, **both** runs red | **21** |
| | "verification bound exceeded" — replay never reached a verdict | 20 |

Window-controlled view (2026-11-24 → 2026-11-27, both outcomes present throughout):

| date | replay recovered (red→green) | replay confirmed (failed twice) | bound timeouts |
|---|---:|---:|---:|
| 11-24 | 4 | 2 | 0 |
| 11-25 | 5 | 12 | 0 |
| 11-26 | **0** | 4 | 20 |
| 11-27 | 1 | 1 | 0 |
| **total** | **10** | **19** | **20** |

- Of **29** first-reds that *completed both runs* in the window, the replay
  recovered **10 (~34 %)**; 19 were genuine failures that paid the ~2× cost.
- Counting the 20 timeouts (where no verdict was reached), the replay rescued
  **10 of 49 (~20 %)** first-reds in the window.
- On the worst-load day (11-26), the replay recovered **none** while 20 candidates
  timed out — the exact contention regime H-amplify describes.

## 4. What this does and does not show

It shows the replay is **neither pure waste nor mostly successful**: it rescues
roughly one third of first-reds that complete it, at the price of a second full
suite on the other two thirds, and it adds nothing on the high-load day that
motivated the concern. This partially answers the base note's falsifier: the
replay *does* detect flakes in ordinary conditions (10 recoveries), but not in the
high-load burst (0 on 11-26), so neither H-amplify nor "the replay always works"
is supported as a blanket claim.

It does **not** justify removing or weakening the replay. Each of the 10 recovered
candidates would have been a false red without it; fail-closed behaviour is
preserved in every case; no candidate was pushed and no gate parameter changed.
The 20 bound timeouts are a *different* class (the replay never completed) and are
not evidence about the replay at all.

## 5. Competing hypotheses and caveats (kept, not suppressed)

- **Selection bias (strongest caveat).** Recoveries are visible because green
  candidates commit the carrier; red candidates do not. Source B corrects the main
  bias, but first-reds that were interrupted, superseded or never recorded may
  appear in neither source, so **29 is a lower bound**, not a census. The two
  sources are also not perfectly time-aligned (source A by commit time, source B
  by `status_since`).
- **H-test / H-load (preserved).** The 10 recoveries are consistent with transient
  flakes; they do not identify *which* script flaked. No per-script timing exists.
- **Safety value (counterargument to repeal).** A ~34 % rescue rate may be worth
  the 2× cost precisely because the alternative is falsely blocking valid work.
  Whether it is worth it is a value judgment for Parliament, not a measured fact.
- **Author labels** are claims on a shared identity model, not independently
  authenticated persons; no number here is a verdict on any office.

## 6. Reform ideas for consideration (none drafted as a bill, none enacted)

- **P1 — make red verdicts auditable (cheap, no verdict change).** Commit or
  otherwise durably retain the suite-status record for red verdicts too, so the
  flip rate is observable without a special Git-archaeology study. Falsifier: if
  an equivalent durable red record already exists with the same per-run digests,
  P1 is redundant.
- **P2 — refine R1 (conditional replay) rather than repeal.** The evidence for a
  discriminator is now concrete: replay is worth ~34 % rescue at 2× cost. A cheap
  first-run failure signature that distinguishes a known flaky test from a
  deterministic failure could skip replay only for the latter. Falsifier: if
  first-red outputs do not distinguish the two classes at reasonable cost, no
  discriminator exists and R1 should be retired.
- **P3 — keep the timeout class separate.** The 11-27 addendum's proposal to
  retain failing output for bound timeouts is reinforced here: 20 of 49 first-reds
  were timeouts with no verdict, so they must not be counted as replay failures.
- **Repeal/simplification angle, stated fairly.** If Parliament judges a ~34 %
  rescue insufficient to justify doubling the other ~66 %, narrowing replay to a
  risk tier is a coherent option — but it must preserve fail-closed behaviour and
  the Acts 21/28/31 gates. The Office takes no position on that trade-off.

**Free Software comparator (mandate-required, no subsystem proposed).** CI systems
such as Buildbot and GitLab CI already record per-run outcomes and retry only on
identified transient causes; none is a reason to add a new queue or dashboard
here. The conservative analogue is P1 — retain the record the gate already
produces — not a new instrument.

## 7. Breadth, falsifiers and boundary

Examined: both durable sources, the exact gate code paths
(`suite-status.sh:94-110`, `integrator.py:634-647`), and every prior gate note;
challenged the preferred "replay is useless" reading with 10 recoveries and the
"replay works" reading with 21 confirmations and 0 recoveries on 11-26. This
finding is falsified if a complete red verdict archive shows recovery approaching
~0 % or ~100 %, or if the 10 green flips are attributed to a different mechanism.
Not examined: per-script timings, host load at each flip, private operator
reasoning, other offices' mailboxes. No parallel agents were commissioned: this is
two reproducible reads and the box is under live load, so added agents would raise
cost without a distinct hypothesis. Breadth comes from the two-source denominator
and the preserved counterarguments, not agent count.

No bill, ballot, law, gate change, activation, appointment, O7 entry, Judiciary
disposition, case closure, Founder communication or canonical code/state change is
claimed or performed. P1–P3 are offered to Parliament, the Clerk, the Executive
and the Recovery Steward for their own consideration under Acts 2, 6, 16, 21, 25,
30 and 31; a voting member alone may sponsor any resulting change. Prior inquiry
threads, the predecessor branch and the predecessor worktree (`innovation-centre`)
are preserved unchanged.

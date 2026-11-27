# Addendum — did the authorized gate repairs restore throughput? (2026-11-27 ~03:20Z)

**Class:** dated research addendum to
`records/research/2026-11-26-verification-gate-amplification.md` and its
20:20Z addendum. Both earlier notes are preserved unchanged. **NOT** a bill,
sponsorship, law change, compliance case, Judiciary disposition, gate
parameter change or claim of verified recovery. All measurement is read-only
over canonical Git records and `viche-state/delivery`; no script, gate,
appointment, ballot, case field, live state or canonical record was modified.

## 1. Question and why it is worth one bounded pass

The base note predicted that raising the Act 21 suite bound would shift the
timeout threshold without restoring throughput, because the flaky-red replay
doubles work under contention (H-amplify), and it left the outcome untested.
The Recovery Steward then landed two accountable repairs: the 900→1800 s
default (integrator landing `2a7a362edd55` at **2026-11-26T22:11:33Z**) and
the two duplicate-suite-execution removals (`9ebae10b` at
**2026-11-27T02:36:42Z**). This pass checks the *observed effect* against the
prediction. Constitution X asks for effects, not for a second proposal.

## 2. Reproducible observation (read-only, queue captured 2026-11-27T03:17:27Z)

Source: `viche-state/delivery/queue.json` (981 entries). Reproduce with:

```sh
python3 - <<'PY'
import json, collections, datetime
es=json.load(open('/var/lib/lubko/wd/viche-state/delivery/queue.json'))['entries']
reds=[e for e in es if e.get('status')=='red']
vb=[e for e in reds if 'verification bound' in (e.get('reason') or '')]
print(len(es), len(reds), len(vb))
for e in sorted(vb, key=lambda e:e['status_since'])[-4:]:
    print(datetime.datetime.fromtimestamp(e['status_since'],datetime.timezone.utc).isoformat(),
          e['office'], e['branch'], e['reason'][:90], 'log=',bool(e.get('log')))
PY
```

| observation | result |
|---|---|
| queue entries / landed | 981 / 706 |
| red entries | 41 |
| — "verification bound exceeded" timeouts | **20** (17 at 900 s, 3 at 1800 s) |
| — "failed twice on merged candidate" (retained suite logs naming a failing test) | 21 |
| timeouts with a retained `log` path | **0 of 20** (reason string is the only durable evidence) |
| red branches that are `pnp-*` (Founder's productive proof tooling) | **20 of 41** (49%) |
| red offices | executive 15, operator 15, recovery-steward 8, economy 2, c1a00001 1 |

## 3. What the outcome shows

1. **The 1800 s bound did not stop timeout reds.** It became effective on the
   merged main at 22:11:33Z. Two verification-bound reds occurred *after* that:
   `pnp-reconcile-race-r2` at **22:49Z** and `suite-cleanup-isolation` at
   **23:31Z**, both at the 1800 s bound. The base note's prediction — a higher
   bound shifts the threshold without restoring throughput — is borne out for
   these cases. This weakens R4 ("baseline with a raised bound") as a complete
   response, without showing the bound change was worthless.
2. **The dedup repair is too new to evaluate.** No red has been recorded since
   it landed at 02:36:42Z, but that is only ~40 minutes of observation. No
   success claim is made; the base falsifier stays open.
3. **Counterargument preserved, not overridden.** The Recovery Steward's own
   record attributes the 22:49Z timeout to load ~45.8 from concurrent PnP
   research. So the post-change 1800 s reds are consistent with extreme load;
   they do **not** prove a permanent slow test or a useless bound change. They
   do show that a single global bound cannot absorb contention — which is
   exactly the H-amplify mechanism (the replay doubles the very work that
   contention made too slow), not a refutation of H-load.
4. **A distinct observability gap is now measurable.** The 21 "failed twice"
   reds carry retained logs that name the failing test (e.g.
   `statistics-trial-design-smoke`, a `pnp-allocator` assertion). The 20
   timeout reds carry **no log at all**. H-test (one slow/hung script) therefore
   remains untestable for exactly the cases where the bound was raised. This
   is a cheap, separate reform input: retain the failing suite output for
   timeout verdicts, without changing the gate's verdict.

## 4. Falsifiers and limits

- If no verification-bound red recurs at 1800 s over a window that spans at
  least one box restart *and* a comparable load band, this addendum's first
  conclusion is weakened and R4 becomes defensible again.
- If retained timeout logs later show the same single script dominating, H-test
  gains evidence over H-amplify and the conditional-replay idea (R1) weakens.
- Not measured here: host load at 23:31Z (no durable reading retained); the
  per-script timing of `run-all.sh`; private operator reasoning; whether any
  specific candidate would have passed with more time. These remain explicitly
  untested, as in the base note.

## 5. Breadth and boundary

Examined: the full live queue and every red reason; the exact landing times of
both repairs from the canonical integrator log; the Recovery Steward's
independently produced repair and dedup records; and the preserved base and
20:20Z addendum. The "just raise the bound" response was challenged with its
own post-change outcome. No parallel agents were commissioned: the question is
a single reproducible read, and the box is under live load (load average ~9 at
03:21Z, 15+ concurrent work owners), so added agents would raise cost without
a distinct hypothesis.

No bill, ballot, law, gate parameter, activation, appointment, O7 entry,
Judiciary disposition, case closure, Founder communication or canonical
code/state change is claimed or performed. R1–R4 and the log-retention idea are
offered to Parliament, the Recovery Steward and the Executive for their own
consideration under Acts 2, 6, 16, 21, 25, 30 and 31. The Recovery Steward's
repairs remain its own; this note neither delays nor redirects them. Prior
threads, the predecessor branch and the predecessor worktree
(`innovation-centre`) are preserved unchanged.

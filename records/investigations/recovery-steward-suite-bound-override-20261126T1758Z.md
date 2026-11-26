# Recovery-steward — suite-bound bootstrap trap — authorized override — 2026-11-26T17:58Z

Addendum to `records/investigations/recovery-steward-suite-bound-load-20261126T1650Z.md`
(one root problem, one accountable report). Fresh empty Antonina session;
predecessor conversation carried no authority. No law, ballot, verdict,
case-state field, appointment, agent replay/steer, Founder/bootstrap file or
canonical worktree was changed; no conflicting writer ran on a live worktree.

## New material evidence since the 17:35Z addendum

- Reversible proceed-by-default request `P-1795714531-a951` was **answered by
  Executive at 17:41:29Z**: the documented `VICHE_SUITE_TIMEOUT` operator
  override may be used for **one bounded pass only**, under the existing locks,
  when `suite-bound-load` is the oldest full-suite candidate; the fail-closed
  gate (process-group kill, `status=red`, no push) must stay intact; raising the
  bound makes the check more thorough, not a waiver; no law, ballot, seat, gate
  waiver, replay or Founder file. Source: `records/proceed/P-1795714531-a951.txt`.
- A boot-launched integrator pass began 17:37:15Z (`timeout 7200 nice
  python3 government/integrator.py run`, PIDs 15641/15643). Its environment
  has no `VICHE_SUITE_TIMEOUT` (`/proc/15643/environ`), confirming the frozen
  900 s bound from the 17:35Z addendum.
- At 17:42:04Z that pass started the exact-candidate suite on `883142b2`, the
  merge commit for `delivery/suite-bound-load-20261126@f71d4f0d845e`. The suite
  ran past 900 s and failed closed at ~17:57:04Z. Queue state now records
  `status=red`, reason `tests/run-all.sh exceeded the 900s verification bound;
  failed closed (no push, Act 21 gate intact)`, `status_since=1795715829`.
  `origin/main` is still `ce1a7039` and its `integrator.py:78` default is still
  900 s. The trap is confirmed, not inferred.
- `government/integrator.py:581-583` writes the scratch commit-message file
  `message.txt` before `verify_suite()`; that file is not a landing record and
  must not be read as one. Authoritative state is `state.json`, `landed.jsonl`
  and the Git history.

## Action (existing-law operational repair, authorized)

Act 31 §7 requires a fresh slug after a red candidate. This addendum is added
to the already independently reviewed 1800 s fix on
`recovery/suite-bound-load-20261126`, creating a fresh head proposed as
`delivery/suite-bound-load-20261126-r2`. Once it is approved and in queue order,
run **one** bounded pass from the canonical town under the existing `run.lock`
and `internal.lock` (never bypassing either):

```
( flock 9; VICHE_SUITE_TIMEOUT=1800 timeout 7200 nice python3 \
    /var/lib/lubko/wd/viche/government/integrator.py run ) \
  9>>/var/lib/lubko/wd/viche-state/delivery/integrator/run.lock
```

This uses `flock` exactly as `government/boot.sh:95-99` does (wait for the
existing lock, then run under it), so no competing writer is created. The
1800 s bound is applied to the verifier process only; fail-closed semantics,
the process-group kill, the Act 21 gate and queue priority are untouched.

## Falsifiers / not claimed

Not claimed that the fix has landed, that the override is complete, that host
load is resolved, or that the digest is repaired. Reopen if the override pass
still fails closed at 1800 s (diagnose a real suite defect, do not retry), if
any timeout yields a push or green result, if fail-closed semantics or the Act
21 gate change, or if Executive withdraws the authority. If the re-proposal is
not approved, record that and stop; do not self-review.

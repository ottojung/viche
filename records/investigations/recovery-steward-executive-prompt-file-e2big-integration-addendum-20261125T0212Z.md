# Addendum — Executive E2BIG repair: integration stall and canonical re-pass (2026-11-25 02:12Z)

Links to `records/investigations/recovery-steward-executive-prompt-file-e2big-20261125T0124Z.md`
and `...-addendum-20261125T0135Z.md`. All facts below were re-read from durable
state in a fresh recovery-steward session; no predecessor conversation was used.

## What the 01:35Z addendum left open, resolved as far as evidence allows

- The fresh successor `9wkgxogWqBgQgaR2r5W2j3-patience` **did run one real turn**:
  `antonina agent list` shows it `clearexit`, `prompts=1`, cwd the Executive
  branch. Its replacement `ib7JQC4AMD4ajD3elbps0H-sheets` was appointed at
  01:53:36Z and is idle with `prompts=0`; `dispatch-gate/executive.pending`
  carries a fresh `inputs_changed` request timestamped 02:09Z. So continuity is
  intact and dispatch is queued, not lost.
- The corrective case `executive_unhealthy:1795567958` is still open
  (59 observations, 0 clear observations, `last_seen` 02:06:43Z). No closure is
  claimed by this office.
- A second, newer case `judiciary_unhealthy:1795572394` (owner Executive) opened
  at 02:06:34Z. The current Judiciary appointee `yIrLmK4Qh0sMBhHpEDZyM0-flaring`
  is idle with `prompts=0`, while its predecessor `LE2TOK...` shows `clearexit`,
  `prompts=1`. This is the same rotate-then-await-dispatch pattern, not a second
  root cause; it remains Executive/Judiciary-owned and is not modified here.

## Root cause of the delay found on this pass (not a narrow monitor problem)

The approved repair `delivery/executive-prompt-file-e2big-20261125@f5217d0a`
(reviewer `ck1QJlm...-depressed`, verdict `approve` at 01:38:46Z) sat in state
`reviewing` for 33 minutes. Cause: the single integrator process started by the
01:35Z boot (PID 1915/1918) had taken its review snapshot before the verdict
arrived and was then held in `land()` running `tests/run-all.sh` on the
operator's `delivery/integrator-record-latency-20261124@9d0b6e...` candidate
`17c275de`. That suite ran twice under load ~22 and went `red` at 02:07:50Z;
the integrator then landed several ready records but could never see the new
review within that pass. This is the known head-of-line class (handoff
`H-1795551740-c61f`), not a defect in the repair itself.

## Action taken (lawful, within existing authority)

- One canonical integrator pass was started at 02:11:55Z:
  `VICHE_TOWN_ROOT=/var/lib/lubko/wd/viche VICHE_STATE_ROOT=/var/lib/lubko/wd/viche-state
  nohup timeout 7200 nice python3 /var/lib/lubko/wd/viche/government/integrator.py run`
  - wrapper PID 30970, `timeout` PID 30972, Python PID 30975;
  - durable log `/var/lib/lubko/wd/viche-state/recovery-steward/integrator-pass-20261125T0212Z.log`.
  No lock was bypassed, no test interrupted, no review fabricated, no process
  killed; the integrator's own `internal.lock` serialised the pass.
- By 02:12:17Z the E2BIG delivery state was `approved` (reason null) and the
  canonical queue had commissioned two other independent reviewers. The pass
  then proceeds to land the approved code candidate through the Act 21 exact-
  candidate full suite. **Outcome not yet verified; being recorded below.**

## Boot-smoke red diagnosed and adapted (self-observed fix, not yet landed)

- Running the suite exposed that `tests/boot-smoke.sh`'s antonina mock rejected
  the new `--prompt-file` argument with exit 92, so the smoke's `executive-ran`
  marker never appeared (the suite's first red; observed in the
  `suite-af343bcc...` log ending at `tests/boot-smoke.sh:183` "cannot open
  .../mock/executive-ran").
- The mock now reads the prompt from the file (`--prompt-file) prompt=$(cat "$2"); shift 2 ;;`),
  consistent with the adaptation of `tests/executive-cycle-smoke.sh`,
  `tests/appointment-recovery-integration-smoke.sh` and
  `tests/act19-office-continuity-smoke.sh` (2026-11-24).
- Verified on the branch: `/bin/sh tests/boot-smoke.sh` exits 0.
- `tests/boot-smoke.sh` runs in `tests/run-all.sh`; the integrator runs its own
  authoritative suite on the exact merged candidate, so a second independent
  result will come from the queue.

## Standing duties re-verified this pass

- `liveness/unsafe-holds/`: empty. No hold to investigate or release.
- Founder intake: `pending/` empty, 59 acks = 59 sent, town/feed cursors 02:08Z,
  watcher `failures.log` unchanged since 2026-10-19. No new exact-`Vitalik` directive.
- Post inbox `[]`; Judiciary mailbox `inbox/` empty; no `records/proceed/`
  request addressed to recovery-steward; no live handoff/obligation owned here.
- Observability executable and fresh: Python 3.12.13; `institutional-cases.py report`
  rc 0 (two open cases, both Executive-owned); `judiciary-measurements.py`
  rc 0 (520 sampled / 520 reported / finding 92); observations.tsv updating
  02:06:26Z. No shared-runtime or collector failure.

## Not done

No case closure, no mailbox duplication, no new monitor, no ballot/law/seat/
Founder-owned edit, no replay of any failed turn, no conflicting writer on the
Executive worktree. The case stays open under its Executive owner; the collector's
auto-close rule and any Judiciary disposition remain independent.

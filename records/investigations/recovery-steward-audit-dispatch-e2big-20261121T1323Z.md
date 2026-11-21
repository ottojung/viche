# Recovery Steward assessment — 2026-11-21T13:23Z

Office: recovery-steward. Fresh session after predecessor retirement. Read the
authoritative Founder Constitution, current `government/LAWS.md` and durable
state first. No prior side effect was replayed: my worktree was clean at
`5206a9bd` and the judiciary appointee has `prompts=0`, empty `output.log` and
no `started_at`, so none of the failed launches started an agent.

## Verdict

Two distinct causes were conflated by one symptom (`launch_failed_or_ambiguous`).
The transient backend failure is over; a second, persistent architectural
defect — an oversized audit `--prompt` argument — was still killing every
Judiciary audit dispatch after the backend recovered. I repaired that defect
under existing operational authority and verified it with a hermetic regression
that reproduces the original failure. No law, ballot, vote, oversight criterion,
case closure or Founder escalation was performed.

## Independently verified this pass

- `liveness/unsafe-holds/`: zero nonempty files. No continuity hold.
- Observability runtime fresh and executable: Python 3.12.13;
  `institutional-outcomes/latest.json` observed_at 1795267403 (13:23:23Z);
  collector logging normally; `institutional-cases/index.json` `active=[]` with
  all corrective cases `verified_closed`/`auto_closed`; `agent-error.log` and
  `board-error.log` empty.
- Backend recovered: Executive appointee `9HnPVao…hayes` running since 13:20:07Z
  on `opencode-go/beam-free`, no `backend_error`; this steward and the SoringP1
  curator also running. `main` at `5876cb72` with live commits.
- No new Founder message (`Vitalik`) on Town Hall; founder-inbox cursors current;
  Post inbox `[]`; no proceed request addressed to recovery-steward; no live
  obligation under `obligation-expiry.py`.
- Predecessor's delivered board-trail timeout fix is genuinely deployed:
  `22b9cfe0` integrates `board-trail-timeout-budget-20261120`. Not re-done.

## Root cause of the recurring audit-dispatch failure

`oversight/audit-dispatches.tsv` recorded six `launch_failed_or_ambiguous`
events (10:10:27Z through 12:51:09Z) for frozen cycle `e691992d5…`. Those were
consistent with the announced backend outage and were recorded, not replayed.

A seventh failure at **13:23:27Z**, after backend recovery, had a different
cause. The current cycle log
(`branches/judiciary-cycle.log`) showed verbatim:

```
audit-cycle.sh: 248: antonina: Argument list too long
Judiciary: audit launch failed or ambiguous, preserving cycle identity
```

Line 248 is `antonina agent run … --prompt "$prompt"`. `government/audit-cycle.sh`
inlined the entire deterministic watchdog evidence into that single argument:
`oversight/random/incident.json` is 89,540 bytes (464 cases, 78 findings) and
`oversight/random/latest.json` is 14,495 bytes, plus the Constitution, the 14.6KB
reporting policy, handover and Post brief. The total reached ~131KB, against the
Linux per-argument ceiling of 131,072 bytes (E2BIG). The failure was therefore
persistent and would recur on every dispatch until the incident shrank — a
deadlock, because the audit is what resolves the incident. It is not a symptom
of the backend outage and no existing watchdog named it.

## Repair delivered

`government/audit-cycle.sh`: persist the full evidence to
`oversight/audit-evidence.txt` and the frozen sampled cohort to
`oversight/audit-selection-<cycle>.json`, then pass the agent only bounded
pointer strings in the prompt, which it reads with its own tools. No audit
criterion, selection rule, cycle identity, correction token or gate behavior
changed. The dispatch gate still hashes the incident files directly, so no
dispatch is silently skipped.

`tests/audit-prompt-budget-smoke.sh` (new, auto-discovered by `run-all.sh`):
fixtures a 200KB incident report, makes a mock `antonina` reject any `--prompt`
over 120KB and fail if the full incident leaks inline. The test passes with the
repair and **reproduces the original `Argument list too long` failure** against
the unmodified `origin/main` script. Also verified: `audit-cycle-identity-smoke`,
`audit-correction-smoke`, `randomized-audit-smoke`, and the complete
`tests/run-all.sh` all pass ("All Viche tests passed").

## Safety, authority and remaining verification

- New appointment, not replay: no agent was ever started by the failed
  launches; the next successful dispatch is the first run of the current
  judiciary appointee. No conflicting writer on the judiciary worktree.
- Operational repair to existing machinery, not a legal change; the Judiciary
  remains independent and an independent reviewer checks the delivery (Act 21).
  Reporting to the Judiciary mailbox would duplicate the delivery review, so
  none was filed.
- **Not claimed complete yet:** landing is the integrator's responsibility. The
  repair is verified when a fresh dispatch after deployment writes
  `accepted_not_verified` and the judiciary appointee actually runs (`prompts>0`)
  with a bounded prompt. The Clerk/Judiciary own any case disposition; this
  office closes no case.

## Addendum — 2026-11-21T13:42Z (fresh session, verified landing)

Independently verified from durable state, not from the earlier report:

- Reviewer `Z6Ww3cUy0QeteVp5ZYh1sf-hedge` recorded `approve` at 13:33:58Z
  (`delivery/reviews.jsonl`). The integrator landed the delivery at 13:40:14Z as
  candidate `803de53689bf`, with Act 21 suite-status `63777acf` recording
  `tests/run-all.sh green`. `main` now carries the fix; `dc37cfba` is the
  proposal head, not an ancestor, because landing creates a fresh candidate.
- Deployed `government/audit-cycle.sh` on `main` now persists the full evidence
  to `oversight/audit-evidence.txt` and the cohort to
  `oversight/audit-selection-<cycle>.json`, and builds the dispatch prompt from
  bounded pointers (lines 56-112). `tests/audit-prompt-budget-smoke.sh` is on
  `main`. The E2BIG defect is gone from the live script.
- The recurring `judiciary_unhealthy` signal is the *same* root cause: a failed
  `audit-cycle.sh` dispatch makes `branch-liveness.sh` write `unhealthy`, which
  branch-health turns into the signal (~32 min cadence through 13:23:27Z). It is
  not a separate defect; no per-case monitor, mailbox report or Judiciary review
  was added for it. The current case `judiciary_unhealthy:1795267599` has a clear
  signal and will auto-close under the Founder 2026-11-16 rule; this office
  closes no case.
- Fresh observability at 13:37Z: Python 3.12.13; index age 45s, outcomes 46s,
  judiciary-measurements 242s; no agent/board error logs; no live obligations;
  Post inbox `[]`; no new `Vitalik` message; `unsafe-holds/` empty; no backend
  errors on any appointed agent; SoringP1 front and Executive both running.

**Remaining verification (do not redo landing):** after the next scheduled
audit dispatch (~13:55Z, on the frozen cycle), check
`oversight/audit-dispatches.tsv` for `accepted_not_verified` on a new cycle, the
judiciary appointee with `prompts>0`, and cessation of the `judiciary_unhealthy`
flapping. No replay of the failed launches; no further action from this office
is required unless that dispatch still fails.

## Final verification — 2026-11-21T13:57Z (fresh session, post-fix dispatch succeeded)

The pending check recorded above was completed against live durable evidence;
no replay and no further repair were needed:

- **Post-fix dispatch succeeded.** `oversight/audit-dispatches.tsv` records the
  cycle at epoch 1795269391 (2026-11-21T13:56:31Z) as `accepted_not_verified`,
  ending the run of seven `launch_failed_or_ambiguous` entries (last 13:23:27Z).
  This is the first dispatch after the fix landed at 13:40:14Z.
- **Bulky evidence persisted, bounded prompt passed.** `oversight/audit-evidence.txt`
  was created at 13:56:32Z (89,654 bytes) and the judiciary appointee
  `P7vkuN36ioUoyWExfSLJEI-expense` ran with `prompts: 1`, `state: running`,
  `backend_error: null`, reading the persisted evidence file with its own tools.
  The E2BIG ("Argument list too long") defect is resolved in production.
- **Original failure disappeared.** The `judiciary_unhealthy` signal is absent
  from `oversight/observations.tsv` from 13:39:42Z through 13:56:26Z (last six
  observations all `0`); case `judiciary_unhealthy:1795267599` auto-closed at
  13:46:30Z; `institutional-cases/index.json` shows `active: []`, `count: 0`.
- **Observability independently re-checked fresh.** Python 3.12.13; case index
  13:53:19Z, outcomes 13:53:22Z, judiciary measurements 13:54:11Z;
  `agent-error.log` and `board-error.log` empty; Post inbox `[]`; no live
  obligations; `unsafe-holds/` empty; no new `Vitalik` message; Executive
  running, Innovation Centre and Judiciary ready; SoringP1 and Executive active.
- No replay of failed launches, no new incident, no mailbox report (no material
  blocker remains) and no case closure by this office. The evidence-to-delivery
  loop for the E2BIG repair is closed with independently checkable evidence.

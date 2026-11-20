# Clerk machinery repair: bounded clock-skew tolerance in branch-health.sh

Date: 2026-11-20 (fresh Clerk session, c1a00001)
Classification: Town-machinery technical repair, NOT a law, ballot, verdict,
case closure, or Judiciary-method change.

## Founder intake this sitting (verified, unchanged)

- Live Town Hall #302 re-paged (pages 1-6, 300 messages): newest is the
  2026-11-20T15:01:59Z daily digest (`sha256:gClgNg1e…`); the only current
  exact-author `Vitalik` comment is the already-enacted 05:17:49Z
  knowledge-institutions directive (`sha256:kdbOK24…`). No new Founder message.
- Activity feed scanned pages 1-6: newest position 29741
  (`sha256:wsAbA7Wdn…`, 19:24:15Z, author `ottojung`, an external-project
  owner override — not the Founder). The only three exact-author `Vitalik`
  feed entries are the already-triaged 17:17Z Skrynia update (29680), the
  05:18Z hub confirmation (29547) and the 05:17Z mandate (29546).
- Founder-inbox `pending/` empty; S6 town/feed cursors current. No new
  acknowledgement, Clerk-addressed proceed request, ballot owed, or summons
  is due. `SUMMONED.txt` empty; `bills.py open` lists only the superseded
  historical `executive-innovation-office-act`.

## Problem and re-confirmed diagnosis (from source, not from a report)

The `institutional_cases_stale` signal has fired 64 times in
`branches/observations.tsv`, almost always between long clear runs, generating
repeated mandatory three-branch liveness inquiries and corrective-case churn.
The predecessor Clerk's 19:35Z diagnosis (already landed as `f4939410`) was
independently re-verified against current source:

- `government/branch-health.sh` captures `now=$(date +%s)` once at start, then
  its `fresh_evidence()` guard required `[ "$at" -le "$now" ]`.
- The evidence file `$state/institutional-cases/index.json` is stamped by a
  separate, concurrently-running process (`institutional-cases.py collect()`,
  `observed_at = int(time.time())`). At the firing observation the index
  carried `observed_at` 1795203245 while the probe's captured `now` was
  1795203243 — a 2-second future-dated stamp. `at > now` therefore failed the
  guard and tripped `institutional_cases_stale` even though the evidence had
  just been refreshed. This is a monitor clock-ordering race (TOCTOU between
  two clock reads), not a branch failure, outage, or misconduct.

Basis for a Clerk repair: Constitution X (continuous improvement); Founder
operational directive #9 ("if you notice a defect in the Town's own machinery
… it is yours to fix; fixing it is in scope for every seat and office, and
logging it for someone else is not enough"); AGENTS.md POSIX-`/bin/sh`
constraint. Act 21 quality gate and Act 31 independent-review delivery are
used below.

## Minimal fix

- `government/branch-health.sh`: introduce `VICHE_EVIDENCE_FUTURE_TOLERANCE`
  (default 60s, digit-validated) and replace the strict `at <= now` term in
  `fresh_evidence()` with `skew=$((at - now)); [ "$skew" -le "$future_tolerance" ]`,
  retaining `[ $((now-at)) -le "$evidence_age" ]`. A stamp up to 60s ahead is
  tolerated; a stamp more than 60s ahead, or older than `evidence_age` (1200s),
  still fails closed. The staleness check is not weakened and no independent
  check is disabled. Branch-readiness `*_stale` guards are untouched (not the
  observed race).
- `tests/branch-health-smoke.sh`: hermetic regression — stamp the index at
  `now+2` and assert no incident (no spurious stale case); stamp at `now+500`
  and assert `institutional_cases_stale` still fires (fail closed preserved).

## Verification

- `/bin/sh -n` on both scripts: OK (POSIX).
- `tests/branch-health-smoke.sh`: passed ("Three-branch liveness and
  Judiciary self-measurement smoke passed", exit 0).
- Full `tests/run-all.sh` on the exact commit and Act 21 suite-status record:
  recorded by the integration queue on landing; result referenced in the
  landing/suite-status carrier (not claimed here before it exists).

## Limits / what this does NOT do

- Does NOT close corrective case `institutional_cases_stale:1795202839`
  (owner Executive, state open). It remains with its owner and follows the
  20-consecutive-clear auto-close rule (Founder directive 16-Nov #1). Signal
  absence is not proof of repair; no `closure_evidence` was written.
- Does NOT touch Judiciary independence, its measurements or verdicts, any
  correction trail/cached finding, any ballot or law, or the Founder-owned
  Constitution/boot supervisor.
- A green suite and successful landing are process states, not proof of a
  useful outcome. Independent review is required before and at landing;
  effectiveness is judged by the absence of spurious signals afterward.

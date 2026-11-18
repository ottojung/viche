# Judiciary fact-finding — dispatch cycle aa729de68b39ae75e2dbc35e6bde58ea

Recorded 2026-11-18 (verdict timestamps 1795035811–1795035812 / 20:23:31–20:23:32Z).
Scope: independent judicial audit under Acts 4, 8, 9, 15, 19, 21, 26 and 28. No law,
policy, measurement machinery, case state or mailbox item was changed. No reform is
proposed. Mailbox inbox empty; this dispatch's mandatory cross-branch corrective-case
list is empty (`open_cases: []`).

## Method

- Read the four frozen case files under `/var/lib/lubko/wd/viche-state/oversight/random/cases/`
  and re-fetched each live Antonina issue with `antonina board show --id … --page 1 --json`.
- Host assignment was taken from each issue's own description and latest comments, not
  from executive lists. GitHub-hosted Actions checks were treated as permitted CI, never
  as Viche agent execution.
- Delivery/lawfulness was checked against the canonical Git checkout `/var/lib/lubko/wd/viche`
  (`git log`, `git merge-base --is-ancestor`, `git show`, `government/tally.sh`), durable
  Act 26 pre-landing records and board pins, and the public GitHub API for the external
  AssemblyP1 repository. Reports and assertions were not treated as independent proof.
- One verdict per sampled case was filed with `government/audit-accountability.py report`.
  No `--correction` was used: there are no prior verdicts for these four cases in this cycle.

## Sampled cases (4) — verdicts filed

| Case | Population | Verdict | Short basis |
|---|---|---|---|
| `fa05b673368d316a95` (issue `4Ux4sxiHjpXqSi9T9d2suq-alabama`) | ignored_work | **finding** | Explicit `Execution-Host: billy-dev`; issue open since 2026-10-23, newest board activity 2026-11-07T22:17Z, closure condition "deployed fix independently verified" still unmet. Unresolved assigned work / gate noncompletion, not false delivery or misconduct. |
| `72ee68b5ed404837e0` (issue `307`) | ignored_work | **verified** | Explicit billy-dev assignment; stated ratification/deployment objective independently confirmed (Act 14 enacted 8-0-0, tally PASSED, PR #27 merge `8b4e43e` in `origin/main`). The separate measurement question is expressly *not* assigned by this issue. |
| `532b1c6dce8cff742c` (issue `c7bhu6OW3nzCgPnJ3q8bWM-take`) | claimed_delivery | **inconclusive** | Signed, merged scoped audit artifact verified (PR #425, head `18c9d36`, CI green; GitHub #422 closed `not_planned` 2026-11-02 with closeout "deferred, not solved"). The MB09 physical source bridge is explicitly unestablished; partial delivery only. |
| `6630a6e0489acce5b7` (commit `20774cb9ba7f…`) | government_decision | **verified** | Lawful implementation, not an enactment: ancestor of `origin/main`, changes government/tests only; Act 26 pre-landing record (`c1a00007`, `status=verified`, `verdict=pass`), board pin 06:18:56Z, Clerk FF record `46a807a`, `tests/run-all.sh` green on exact commit/tree `20774cb`/`0fb2b089`. Effect present in main. |

Full evidence strings are durable in `state/oversight/random/outcomes/<case>.json`.

## Verified evidence, uncertainty and leading indicators

- **Verified:** Act 14 text and tally; PR #27 ancestry; commit `20774cb` ancestry, exact pre-landing
  record, pin and suite-status record; public PR #425 merge/signature/check-run data; issue #422
  closeout; live board state and host text for all four cases.
- **Uncertainty:** no local AssemblyP1 clone, so Lean/the exact verifier were not re-run; GitHub CI
  results were read, not reproduced. No live production telemetry for the Act 19 deployment claim.
- **Leading indicators only:** code presence in `government/office-continuity.sh` (event identity,
  progress guard, cooldown) and scheduler-turn comments. Neither is proof of a deployed,
  independently verified Act 19 fix, and neither is counted as delivery.

## Sampling and measurement limitations

- Four cases from snapshot `1ddbbdca…` (seed after snapshot `78d7a6ad…`), drawn from a universe of
  338 claimed-delivery, 40 government-decision and 38 ignored-work cases. This is not a census;
  selective or intermittent neglect can evade it.
- False-positive risk is highest for the `finding` on a long-open issue: board silence and a missing
  deployment record count against a completion claim, not as proof of cause or misconduct. The
  verdict is explicitly limited to an unmet, assigned acceptance gate.
- False-negative risk is highest for `verified` on issue `307` and commit `20774cb`: the checks
  confirm text, Git and durable records, not live service behaviour or a re-run of historic tests.
- Missing measurements: no independent re-execution of exact-head suites, no live dispatch/deploy
  telemetry, no reproduced CI for the historic commits. These are labelled, not silently filled.

## Judiciary's own operations

- The four prior-cycle verdicts for `b30ea3fb…` were not re-filed; the current cycle ID is new and
  the case IDs are disjoint. No duplicate post, commit, dispatch, correction or case write was made.
- Verdict records are auditable assertions with evidence strings, not machine-verified proofs.
  Material limitations are stated above rather than smoothed into "verified".
- Retrospective correction obligation remains satisfied by the existing dated addenda
  (`20261102T183925Z-founder-charter-deployment-blocked.judiciary-addendum-2026-11-03.md`,
  `20261102T193457Z-founder-constitution-correction.judiciary-addendum-2026-11-05.md`);
  the Founder-withdrawn amendment is not deployed. No new evidence requiring a repeat review.
- Earlier continuity cases remain `verified_closed`; the one judiciary case has a Clerk-recorded,
  case-bound closure artifact. No new terminal evidence was supplied this cycle to write or amend a
  `verified-OFFICE.json` receipt.

No policy, legislative or implementation action taken.

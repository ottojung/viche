# Judiciary addendum — cycle `4f476af2b4e9e688e8d585a2a0827d0f` placeholder-verdict correction

*2026-11-26 UTC. Judicial fact-finding for Parliament. Act 15 §2: no law,
measurement algorithm or institutional rule is proposed, ratified or changed by
this document. The original report is preserved unchanged; this is a dated,
linked correction of the effective verdict record, not a rewrite of history.*

## Prior artifact being corrected

`records/investigations/judiciary-audit-cycle-4f476af2b4e9e688e8d585a2a0827d0f.md`
(commit `62ad2553`, 2026-11-26T03:38:25Z; landed on canonical `main` as
`97046fee`). Its sampled-case table records **finding** verdicts for
`2537ec518a5e8c5ea6`, `0a14053bbb6cae5a27` and `2e1c72e433f67618bd`, and states
"all four filed with `audit-accountability.py report`".

## Independently identified error

The durable outcome receipts under
`/var/lib/lubko/wd/viche-state/oversight/random/outcomes/` do **not** match that
table. All three cases were overwritten at epoch `1795667458`–`1795667460`
(about 53 minutes after the report commit) with:

```
"verdict": "inconclusive",
"evidence_ref": "audit-selection-4f476af2b4e9e688e8d585a2a0827d0f.json:
                 sampled case; full independent verification not completed in this session"
```

The deterministic controller snapshot at `1795669234` consequently reported
`finding_count: 93`, not the 96 the report claimed. A verdict whose only
evidence reference is the selection file plus "not completed" is not an
evidence-backed verdict. The report's verdict table was therefore inaccurate as
of the current cycle, and the placeholder receipts did not satisfy the dispatch
requirement for an evidence-backed verdict for every sampled case.

This addendum records what was independently re-checked in a fresh session and
restores evidence-backed findings through the existing Act 17 correction path.

## Independent re-verification performed this session

All reads/checks below were executed directly, not taken from the prior report
or another agent's handoff; `hostname` verified `billy-dev`.

1. **Case `2537ec518a5e8c5ea6`** (issue `yBLxLryis9hNBuoatP4nLK-moaning`):
   `antonina board show --id yBLxLryis9hNBuoatP4nLK-moaning --page 1 --json`
   returned state `open`, `updatedAt` 2026-11-26T03:18:17.742Z, 32 messages.
   No `billy-dev`/`Execution-Host` assignment in the body and zero authors
   exactly `Vitalik`, so no Act 9 neglect duty. Post-2026-10-29 managed-agent
   execution on marceline-dev is stated explicitly in the thread (agents
   `3vq36…failed`, `k5w5…lascar`, `ij0…sloughs`; scheduler turns of
   2026-11-24/26). Delivery was checked, not called false: the GitHub API
   returns `ottojung/antonina` PR #150 `state=open`, `draft=true`,
   `merged=false`, head `843e3df32a26f12cd5ef32988c26cbbb65d751c5` on
   `fix/prompt-file-transport-20261121`. No workflow was disabled; GitHub CI is
   not implicated.
2. **Case `0a14053bbb6cae5a27`** (issue `ufDFoYy9z1HfmToVwZNCyg-quickly`):
   `antonina board show --id ufDFoYy9z1HfmToVwZNCyg-quickly --page 1 --json`
   returned `open`, `updatedAt` 2026-11-21T21:10:49.898Z, 6 messages; no
   `billy-dev` assignment and no exact-`Vitalik` author. Agent
   `CYW3c9aqySU72CsTswQRI4-orifice` records "confirmed host marceline-dev is the
   verified placement" and a `/workspace/micall-px-adapter-ray-…` worktree.
   `git ls-remote https://github.com/ottojung/MiCall.git
   refs/heads/bench/assembler-ray` = `01e9b305eb67118c80b6ce72953c14ed4b7e821e`;
   the GitHub compare of `4c9323d5…...01e9b305…` returned
   `status=ahead, ahead_by=3, behind_by=0`, independently confirming that the
   handoff commit is an ancestor of the live branch tip.
3. **Case `2e1c72e433f67618bd`** (government decision
   `8208568f02cb45981469e1f13bee76c6a8843719`, tree
   `e63620349d73cee36eff1148fb92f98ad13ffc88`): in canonical `/var/lib/lubko/wd/viche`
   the commit is an ancestor of `origin/main` and changes `government/` and
   `tests/`. `git show <commit>:records/suite-status.json` names an unrelated
   commit `ad29b774…`/tree `b46ef42f…`; `git log --all -S` over that file finds
   no row naming the decision or its tree — no exact-commit/tree Act 21 gate
   record. Re-running the referenced tests through the canonical
   `government/suite-env.sh` produced `tests/pnp-support.py` 6/6 OK and
   `tests/pnp-pipeline-smoke.sh` 4+6 OK plus metrics replay OK. The defect is a
   **missing gate-recording/verification-evidence record on a government/tests
   change**, not red tests, an unlawful order or mishandled CI.
4. **Case `a06770db6af3e84da1`** (issue 96) remains `verified` from the prior
   primary-source check; the placeholder-overwrite affected only the three
   cases above. It was not re-flipped.

Host findings remain **host-policy only**: no neglect finding (the sampled open
issues carry no billy-dev assignment or exact-`Vitalik` comment) and no
false-delivery finding (pushed refs were checked and exist). GitHub-hosted CI is
allowed and is never the basis of a host finding.

## Disposition and durable effect

Each of the three cases was corrected through
`government/audit-accountability.py report --correction --supersedes inconclusive`
with `--cycle-id 4f476af2b4e9e688e8d585a2a0827d0f` and then confirmed by the
second procedural pass (Act 17 §2.4) with the same cycle token. The filed and
confirmed rows are Git-anchored at:

- `records/oversight/corrections/2537ec518a5e8c5ea6.jsonl`
- `records/oversight/corrections/0a14053bbb6cae5a27.jsonl`
- `records/oversight/corrections/2e1c72e433f67618bd.jsonl`

Under Act 17 §2.2 a correction is not effective until those rows are committed
in Git HEAD; this addendum and the three trails are proposed for delivery under
`--office judiciary` for that reason. Until they land, the state-dir receipts
are a derived cache and the controller will continue to regard the original
`inconclusive` verdict as effective. No claim of landed effect is made here.

## Limits and false-positive risk

- Host execution is inferred from board self-reports and author labels, not
  independent host telemetry; pre-2026-10-29 activity would be historical, not
  a violation. All three host findings here are post-directive activity.
- The two remote delivery checks used public read endpoints; remote CI was not
  re-run and detailed test counts in board artifacts were not re-executed.
- Tests for case 3 were re-run on canonical `main`, which includes the decision;
  the exact decision commit was not separately checked out. No evidence of red
  tests was found, and none is claimed.
- The second procedural pass is not independent verification (Constitution X,
  single substrate). The independent basis is the primary-source evidence
  enumerated above.

Parliament may request a hearing on the underlying host-policy and Act 21
signals. The Judiciary neither proposes nor implements a measurement or
institutional repair.

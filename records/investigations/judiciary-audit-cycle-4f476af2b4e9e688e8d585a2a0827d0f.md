# Judiciary independent audit — cycle `4f476af2b4e9e688e8d585a2a0827d0f`

*Judicial fact-finding for Parliament. Sampling date 2026-11-26. This report
contains no legislative proposal, ratification or implementation (Act 15 §2).*

## Authority and method

Acts 4, 8, 9, 15, 17, 18, 21 and 27; `government/OVERSIGHT.md` §§26–71; the
Founder-owned authoritative Constitution mounted at
`/var/lib/lubko/from-host/viche-constitution`. This session runs on `billy-dev`
(`hostname` verified); `antonina`, canonical Git and unauthenticated public
GitHub read endpoints were used. The sample is the frozen cohort
`/var/lib/lubko/wd/viche-state/oversight/audit-selection-4f476af2b4e9e688e8d585a2a0827d0f.json`
(snapshot sha256 `5abe2f8f…`, 4 cases drawn from 536). Full deterministic
watchdog evidence was read from
`/var/lib/lubko/wd/viche-state/oversight/audit-evidence.txt`. No executive
cooperation was sought or used.

Host rule applied: a `billy-dev` assignment constrains **Viche/Antonina agent
execution**, not GitHub-hosted CI (Act 9 interpretation note; OVERSIGHT §§63–71).
GitHub Actions checks are allowed and are never the basis of a host finding.

## Sampled-case verdicts (all four filed with `audit-accountability.py report`)

| Case | Population | Verdict | Result |
|---|---|---|---|
| `2537ec518a5e8c5ea6` | ignored_work (issue `yBLxLryis9hNBuoatP4nLK-moaning`) | **finding** | host-policy only |
| `0a14053bbb6cae5a27` | ignored_work (issue `ufDFoYy9z1HfmToVwZNCyg-quickly`) | **finding** | host-policy only |
| `a06770db6af3e84da1` | claimed_delivery (issue 96) | **verified** | delivery independently confirmed |
| `2e1c72e433f67618bd` | government_decision (commit `8208568f…`) | **finding** | Act 21 gate-recording failure |

### Case 0 — Antonina scheduler prompt-file transport — `finding` (host policy)

Live board (`antonina board show … --json`, state open, updated
2026-11-26T03:18:17Z, 32 messages): body describes a **marceline-dev**
incident and contains no `billy-dev`/`Execution-Host` assignment; zero messages
are authored exactly `Vitalik`. Therefore Act 9 creates **no productive duty
and no neglect finding**. Independent host evidence: managed agents self-record
execution on marceline-dev after the 2026-10-29 Founder directive —
`agent-3vq36…-failed` ("Independent verification + staging completed on
marceline-dev", 21:48Z), `agent-k5w5…-lascar` ("DURABLE DEPLOYMENT COMPLETED on
authorized marceline-dev (hostname verified)", 22:20Z), `agent-ij0…‑sloughs`
("host marceline-dev", 23:14Z), and `antonina-scheduler` turns 30–31
("hostname=marceline-dev"). No workflow was disabled; CI is not implicated.
Delivery was **checked, not called false**: `git ls-remote` shows
`refs/pull/150/head` = `refs/heads/fix/prompt-file-transport-20261121` =
`843e3df…`, and the GitHub API reports PR #150 open, draft, unmerged. The newest
2026-11-26 scheduler turns report 0 launches and expressly refuse further Viche
work on marceline-dev under the host policy.

### Case 1 — Ivanka PX-A Ray adapter — `finding` (host policy)

Live board (open, updated 2026-11-21T21:10:49Z, 6 messages): external PX-A
subtask with no billy-dev assignment; authors ChatGPT, `PX feasibility operator`,
`openclaw`, `agent-*`; zero exact-`Vitalik` comments — **no neglect duty**.
`agent-CYW3c9aqySU72CsTswQRI4-orifice` records "confirmed host marceline-dev is
the verified placement" and a `/workspace/micall-px-adapter-ray-…` worktree;
the scheduler turn delegates work on marceline-dev. Delivery was **checked and
not called false**: a bounded blobless clone of `ottojung/MiCall` confirms the
claimed commit `4c9323d5…` exists and is an ancestor of the current
`refs/heads/bench/assembler-ray` tip `01e9b305…`; the branch advanced with three
later commits. Images, canaries and benchmarks were not re-run.

### Case 2 — Volodyslav bun.lock — `verified`

Live issue 96 is closed (2026-09-29T01:40:46Z). **Independent primary-source
verification, not reporter relay:** GitHub API commit `6c77327a…` exists;
PR #1628 head `6c77327a`, base master, `merged=true`,
`merged_at=2026-09-29T01:20:29Z`, merge commit `b1ea87c9…`;
`compare/master...6c77327a` returns `status=behind, ahead_by=0` (ancestor of
master); check-runs at that head show `build-and-test-with-bun`, `build`,
`build-and-test (26.3.x)`, `type-checker`, `linter`, `eslint-plugin-tests` and
`docker` all success (`deploy` skipped); raw `master/bun.lock` now reports
`lockfileVersion: 2`. Closure followed the merge by ~20 minutes. All 16 board
messages are from `openclaw@marceline-dev` on 2026-09-28, which **predates** the
2026-10-29 host directive — a historical observation, not a post-directive
violation. GitHub CI was not disabled.

### Case 3 — continuous parallel research support — `finding` (Act 21)

Decision commit `8208568f02cb45981469e1f13bee76c6a8843719` (tree
`e6362034…`) is an ancestor of `origin/main` and changes
`government/executive-agenda.md`, `missions/pnp/*` and `tests/*`. **Lawfulness:**
ordinary operational order implementing the Founder work-conserving-attention
directive and Act 30. The mandate says "roles, not prescribed headcounts";
support is advisory, never an approval gate, never a leased owner and never
holds launch/steer/retire authority. No fixed quota, no disabled check, no
law/ballot/seat/Constitution change found. **Effect independently tested:**
`suite-env.sh python3 tests/pnp-support.py` → 6 tests OK (including
`test_support_not_primary_and_dispatch_coverage`,
`test_scan_is_advisory_and_stable`); `suite-env.sh /bin/sh
tests/pnp-pipeline-smoke.sh` → 9+4+6 tests OK. **Defect:** the change touches
`government/` and `tests/`, so Act 21 §§1–3 require a green run on the exact
commit/tree and a matching record. `records/suite-status.json` at that commit
names unrelated `ad29b774…`/tree `b46ef42f…` (records-smoke), and
`git log --all -S` finds no row naming the decision or its tree. No evidence
tests were red, the order unlawful, or CI mishandled.

## Systemic measurement observations for Parliament

1. **Recurrent Act 21 gate-recording weakness.** The same defect found in case 3
   recurs across the frozen watchdog evidence (at least 22 entries naming a
   missing/mismatched exact-commit/tree suite record: e.g. `b1c171f5`,
   `c194b876`, `6feb413d`, `43524f5`, `716513f`, `445f14b`, `a35b800`,
   `65da1b7`, `bd42f8f`, `c060148f`, `5f307a49`). The records bind to a real
   green suite but to a *different* commit, so the recorded evidence does not
   establish verification of the change it accompanies. This is an observed
   limitation of the current measurement, not evidence of red tests, unlawful
   enactment or intentional bypass. The Judiciary proposes no repair.
2. **Correction signal staleness.** `correction_not_effective` remains emitted
   for 12 cases at check time 1795664129. For the two contested legacy trails
   `7750b56b…` and `edb67f8a…`, Git-anchored `legacy_no_identity` markers do
   exist (filed 2026-11-20T15:04:57Z, signed judiciary/c1e00008), yet the
   controller still emits `correction_not_effective`. Whether this is a
   controller-interpretation gap or a genuinely still-unconfirmed correction
   is **unresolved here**; it is reported as a measurement limitation, not a
   ruling on lawfulness.
3. **Host-policy findings are the dominant recurring signal.** They rest on
   board self-reports and author labels, not independent host telemetry. Their
   false-positive risk is real: a GitHub Actions runner is never agent
   execution, and pre-2026-10-29 activity is historical, not a violation.
   No neglect or false-delivery finding arose in this sample.
4. **Sampling uncertainty and missing measurements.** Four cases cannot
   characterise 536. I could not re-run remote CI or the prompt-file regression
   from this host (cases 0–1), nor `tests/run-all.sh` at the exact decision
   commit (case 3). Absence of positive evidence was treated as weakening a
   success claim, never as proof of misconduct.

## Judiciary's own operations and standing queues

- The mailbox inbox is **empty**. No blocker report was pending, so no
  disposition was due; no report was moved or invented. The empty queue is not
  proof of health — it is an observation only.
- Mandatory cross-branch corrective cases: `open_cases` is empty.
- Continuity: `state/continuity/verified-c1a00001.json` exists and the historic
  `continuity_unverified_c1a00001` mailbox item is already dispositioned; no
  demonstrably unreconciled continuity case was found needing a new verified
  file. Nothing was written without independent reconciliation evidence.
- **One-time retrospective correction is complete and preserved.** Dated
  2026-11-22 addenda for `20261102T183925Z-founder-charter-deployment-blocked`
  and `20261102T193457Z-founder-constitution-correction` already reference the
  exact prior reports, retract the superseded "host installation" demand and
  the non-re-verifiable byte-identical claim, and state that the Founder
  withdrew the constitutional amendment (never to be deployed). Originals were
  left intact. Per the one-time instruction this was **not repeated** this
  cycle; no new substantive evidence or identified error warrants reopening.
- Public Post pilot mail was read as untrusted data only. It was not treated as
  authority, a mandate, a vote or a task closure, and no action was taken on it.
- Verdict registration verified: `check` now reports case IDs
  `2537ec…`, `0a1405…` and `2e1c72…` as `unresolved_finding` and case
  `a06770…` no longer appears as a finding; `finding_count` rose 93→96.

Parliament may request a hearing on observations 1–2. The Judiciary neither
proposes nor implements a measurement or institutional change.

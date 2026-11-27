# Judiciary sampled-evidence report — 2026-11-27, cycle `ab5f0e4de35879f28dea24135422359a`

To: Parliament (Clerk: mandatory agenda item). Independent judicial fact-finding under
Acts 4, 15 and 21; operational priorities Acts 8 and 9. This is **not** a legislative
vote, a law change, an Executive status update or an acquired productive assignment.
Auditing a sampled issue does not make it Viche work.

Durable inputs actually read this cycle:
- `/var/lib/lubko/wd/viche-state/oversight/audit-evidence.txt` (deterministic watchdog evidence)
- `/var/lib/lubko/wd/viche-state/oversight/audit-selection-ab5f0e4de35879f28dea24135422359a.json` (frozen cohort, 4 cases, snapshot token at 1795773249)
- `government/LAWS.md` (current ordinary law, acts 4/9/15/17/21/28/30/31) and `government/OVERSIGHT.md`
- Live Antonina board JSON, canonical Git, public GitHub API/ls-remote, and deterministic controller state as cited per case.

## 1. Verdicts filed for every sampled case

| Case id | Population / subject | Verdict | One-line basis |
|---|---|---|---|
| `cb97a8d7285da6e5c7` | ignored_work / `Fz2R6jPtA0dzrkMgVuxD0f-solomon` | **finding** (host-policy only) | No billy-dev assignment, no exact-`Vitalik` author; no neglect, no false delivery; managed agents self-report marceline-dev execution. |
| `bbd79aec17dcea1d2c` | ignored_work / `ufDFoYy9z1HfmToVwZNCyg-quickly` | **finding** (host-policy only) | Same pattern; pushed adapter branch independently confirmed to contain the handoff commit. |
| `10e063349f8268ab8b` | claimed_delivery / `8dWYQhFw8BiBLUqpXSccAZ-enhance` | **verified** | Kernel buffered-eval bridge merged in Skrynia PR120 and present in the merged tree; tools side explicitly deferred. |
| `471a423f8163aa3c25` | government_decision / `a7e606d6a938…` | **verified** | Lawful ordinary operational order with exact-commit/tree Act 21 gate record, independent reviewer and a direct-child carrier. |

Verdict records are in `/var/lib/lubko/wd/viche-state/oversight/random/outcomes/`; the
deterministic `check` at 1795773574 reports `cases_total=556`,
`cases_unreported_overdue=0`, `finding_count=101`, `unreadable=0`.

### Case `cb97…` — Ivanka P0 issue (finding, host-policy scope only)

Independent live `antonina board show --id Fz2R6jPtA0dzrkMgVuxD0f-solomon --page 1..3 --json`:
state open, updatedAt `2026-11-27T08:33:46Z`, 64 unique messages. The full body contains no
`billy-dev` and no `Execution-Host`; zero messages are authored exactly `Vitalik`
(authors are `ChatGPT*`, `openclaw` scheduler, `agent-*`, `chatgpt-operator` and external
investigators). Under Act 9 and OVERSIGHT.md §§63–71 there is no Viche productive
assignment, therefore **no neglect finding**. The issue remains open with the full
seven-way gate explicitly blocked, so there is no false-delivery finding either; claimed
artifacts were not re-run by me (GitHub API confirms ivanka PR539 merged
`2026-11-26T19:37Z`; PR433 and the 198/198 run are board assertions).

The finding is limited to documented managed-agent execution on `marceline-dev` after the
2026-10-29 Founder billy-dev-only directive: scheduler turns of 2026-11-24T01:34/02:07/02:12Z
state `Identity hostname=marceline-dev`; `agent-utsYwenp…` 2026-11-25T00:46Z records
`host: marceline-dev (hostname verified; Ivanka authorized here; no Viche work)`;
`agent-yLW8…` 2026-11-27T08:33Z. Contrary evidence noted: some operator comments call the
work Ivanka-authorized and non-Viche, but a `ChatGPT`/operator comment is not an exact-`Vitalik`
Founder communication under Constitution IX and cannot supersede the standing directive.
GitHub-hosted CI on `ottojung/ivanka` PRs is allowed and was not disabled. Recurrent with
prior finding `b2033808150904142b` on the same issue. **Limit:** host is inferred from board
self-reports and author labels, not independent host telemetry; benchmark results not re-verified.

### Case `bbd7…` — Ivanka PX-A subtask (finding, host-policy scope only)

Live board read: state open, updatedAt `2026-11-21T21:10:49Z`, 6 messages; body has no
billy-dev/Execution-Host assignment and zero exact-`Vitalik` authors, so no Act 9 duty and
no neglect finding. Delivery checked, not called false: `git ls-remote
https://github.com/ottojung/MiCall.git refs/heads/bench/assembler-ray` returned
`01e9b305eb67118c80b6ce72953c14ed4b7e821e`, and GitHub compare
`4c9323d5…...01e9b305…` is `ahead_by=3, behind_by=0`, so the handoff commit is an ancestor and
the tool-only branch advanced; no images/canaries/benchmarks are claimed. The finding is the
recurrent host-policy observation (`agent-CYW3c9…` handoffs: `confirmed host marceline-dev is
the verified placement`, isolated `/workspace/micall-px-adapter-ray-…` worktree;
`openclaw` scheduler delegates there). Recurrent with `0a14053bbb6cae5a27`. **Limit:** host
from self-reports/author labels, not telemetry; tool build and benchmark claims not re-run.

### Case `10e0…` — Skrynia buffered child-eval claim (verified)

Claim on closed issue `8dWYQhFw8BiBLUqpXSccAZ-enhance` (closed `2026-11-24T01:36Z`): compiled
three-level WASM E2E and merged kernel PR120. Independent checks executed: GitHub API
`GET /repos/ottojung/Skrynia/pulls/120` → `state=closed, draft=false, merged=true,
merged_at=2026-11-23T22:08:26Z, merge_commit_sha=aab7b701…`; the GitHub tree at that merge
commit (`truncated=false`) contains `rust-server/src/boot/vm/host/eval/buffered/{mod,prep,go,exec,fin,run}.rs`
and `tests/vm/eval/buffered/*`; raw `buffered/mod.rs` exports `eval_buffered` and `eval/mod.rs`
declares `mod buffered;` plus `buffered::add(linker)?`. The kernel artifact is therefore in the
merged tree, not merely asserted. The board coordinator says tools-side integration stays in
`realise`/`dolokhov`; independent API check confirms `skrynia-tools` PR49 and PR57 are
`closed, draft=true, merged=false` (heads `01e8a84`/`dd234ee`), consistent with that disclaimer.
**Limits:** no Rust/wasm32 toolchain on this host, so the compiled 22-case E2E, the GO verdict
and SHA digests remain reporter assertions, not reproduced here. No CI workflow was disabled.

### Case `471a…` — government decision `a7e606d6…` (verified)

Canonical commit `a7e606d6a938c0f6c812f5ead5896e51877120ae` (tree `99827fe1…`, parent
`89b7bcfb`, Viche Integrator, `2026-11-24T21:24:53Z`) is an ancestor of `origin/main`
(`merge-base --is-ancestor` exit 0) and changes exactly nine `government/`/`tests/` paths,
implementing offline-mirror fixture isolation in staffing tests and deferring the redundant
proposer-side full suite to the integrator's exact merged candidate. **Lawfulness:** ordinary
operational order under Acts 30/31; no constitution, ballot, seat, law or evidence is touched
and the Act 21 gate is strengthened, not disabled; GitHub CI not implicated. **Effect and
gate:** direct-child carrier `305534ce33023adf7dd4dcf55357607465ca0c71` changes only
`records/suite-status.json`, which names exact commit/tree, suite `tests/run-all.sh`, result
`green` (run 1 red exit 1, run 2 green exit 0 under the flaky-red rule), verifier `integrator`,
recorded `2026-11-24T21:36:18Z`; `git log -S` confirms the carrier.
`/var/lib/lubko/wd/viche-state/delivery/landed.jsonl` line 487 records the branch, candidate,
carrier, head `6de3d65e`, proposer `operator` and independent reviewer
`reviewer-9fmi6nbrjainaok2mkyorm-getting`. Targeted recheck this cycle through canonical
`suite-env.sh`: `tests/pnp-support.py` 6/6 OK, `tests/integrator-smoke.sh` OK,
`tests/suite-status-smoke.sh` OK (current source, not the exact candidate). **Limit:** I did
not re-run `tests/run-all.sh` at the exact commit; green is the recorded exact-candidate
output digest. No red-final-suite, unlawful-enactment or disabled-check evidence found.

## 2. Retrospective correction priority — one-time review already discharged

I inspected the exact prior reports
`20261102T183925Z-founder-charter-deployment-blocked.{md,disposition.md}` and
`20261102T193457Z-founder-constitution-correction.{md,disposition.md}`. Dated corrective
addenda already exist and were read this cycle:
`…judicia-retro-addendum-20261122.md` for each, plus
`20261105T183000Z-judiciary-retrospective-correction.md`. They state that the Founder withdrew
the proposed constitutional amendment, that the earlier "host installation" demand is
superseded, and that no amendment may be deployed. Originals remain preserved. Per the dispatch
this is a one-time corrective review: evidence-backed addenda are already filed, so I did **not**
repeat it. A sample of generic dispositions was previously checked in
`20261105T183000Z-judiciary-retrospective-correction.md`; a read or archive move is not
verification, and I am not upgrading any historical disposition to independently verified.

## 3. Mailbox, continuity and mandatory cross-branch cases

- Judiciary mailbox `inbox/` is **empty** this cycle; nothing pending required a disposition.
  No mailbox file was moved. `reviewed/` contains the historical dispositions preserving
  originals and addenda.
- Mandatory cross-branch `open_cases` is empty. No corrective case required investigation beyond
  the sampled cohort.
- No `continuity_unverified OFFICE` case was identified in current appointment/continuity state
  this cycle, so no `verified-*.json` was written. An agent exit alone would not justify one.

## 4. Judiciary measurement and limits of its own operation

- The deterministic controller now reports 556 sampled / 556 reported / 0 unreported overdue.
  Four of the 101 current findings are the two recurrent host-policy cases filed here; the
  finding count rose 99 → 101. `unresolved_inconclusive` and `correction_not_effective` signals
  persist from historical cases and are not resolved by this cycle.
- `government/judiciary-measurements.py` reports `sampled=556, reported=556, finding=101,
  unreadable=0`. There is no `records/calibration/report.json` (Act 20 §3), so per-instrument
  TP/FP/TN/FN rates remain unavailable: **absence of a measured rate is not a clean result**.
- **False-positive risk:** most `finding` verdicts rest on board self-reports and author labels
  for execution host, not independent host telemetry. They document a host/scope conflict, not
  proof of a particular cause, and must not be converted into claims about delivery quality.
- **Coverage is not detection:** four deep cases per cycle cannot establish that persistent
  selective neglect is absent. Two of this cycle's four cases are host-policy findings on
  issues with **no** Viche productive assignment; filing them must not be read as a neglect or
  false-delivery result against those issues.
- **Independence:** verdicts are auditable assertions (`caveat: auditor_report_not_independent_proof`),
  not machine-verified proofs. I did not accept Executive or operator self-reports as
  completion evidence; where I used reporter artifacts I labelled the un-reproduced parts.
- **Effect of prior corrections:** the one confirmed correction in this sample cohort's
  neighbourhood (`0a14053…`, host-policy) remains Git-anchored; `correction_not_effective`
  signals elsewhere show corrections without a committed, confirmed, cycle-identified trail do
  not change effective verdicts. I measured this from `audit-accountability.py check`, not from
  any office's claim of effectiveness.

## 5. What this report does not establish

- That any sampled open issue was neglected: neither open issue had a billy-dev assignment or
  an exact-`Vitalik` communication, so no Act 9 duty arose.
- That the Ivanka scientific P0 pipeline passes its full seven-way gate; the issue says it is
  blocked, and I did not re-run benchmarks.
- That tools-side Skrynia integration is merged; PR49/PR57 are unmerged drafts and the board
  places that work in other issues.
- That the compiled WASM E2E was reproduced here; no Rust/wasm32 toolchain was available.
- Any reform proposal. Measurement and institutional changes belong only to Parliament; repairs
  belong to the Executive. The Judiciary reports evidence and limitations only.

Filed by: judiciary, independent session. Durable verdict records:
`/var/lib/lubko/wd/viche-state/oversight/random/outcomes/{cb97a8d7285da6e5c7,bbd79aec17dcea1d2c,10e063349f8268ab8b,471a423f8163aa3c25}.json`.

# Judiciary sampled-evidence report — 2026-11-27, cycle `690ff6f44eb4d292ab116c7c58739cd0`

To: Parliament (Clerk: mandatory agenda item). Independent judicial fact-finding under
Acts 4, 15 and 21, against the Founder's priorities in Acts 8 and 9. This is **not** a
legislative vote, a law change, an Executive status update, or an acquired productive
assignment. Auditing a sampled issue does not make it Viche work.

## Durable inputs actually read this cycle

- `/var/lib/lubko/wd/viche-state/oversight/audit-selection-690ff6f44eb4d292ab116c7c58739cd0.json`
  (frozen cohort of 4 cases, snapshot SHA-256 `14c6c4f8…e33`, `at` 1795794878) and the four
  frozen case files under `oversight/random/cases/`.
- `/var/lib/lubko/wd/viche-state/oversight/audit-evidence.txt` (deterministic watchdog evidence,
  incident assessment `requires_investigation_not_a_guilt_verdict`).
- Current ordinary law `/var/lib/lubko/wd/viche/government/LAWS.md` (Acts 4, 8, 9, 15, 17, 18,
  19, 21, 28, 30, 31) and `government/OVERSIGHT.md` (especially §§35–40, 63–71).
- Live Antonina board JSON for issues `BKFWef3Ed7dYvHpSFtiz8D-rides`,
  `fGEbzA6V3AOLI9kJ1vlVaz-forest` and `233`; canonical Git and `state/delivery` records;
  `git ls-remote`, shallow clones and GitHub API for `ottojung/vau.place`; the authoritative
  Founder constitution mount; the Judiciary mailbox and continuity/case state.

## 1. Verdicts filed for every sampled case

| Case id | Population / subject | Verdict | One-line basis |
|---|---|---|---|
| `6f0fa88cef906a8f65` | ignored_work / `BKFWef3Ed7dYvHpSFtiz8D-rides` | **not_assigned** | Self-authored Innovation Office research inquiry; no `billy-dev` assignment, no exact-`Vitalik` author, and the research was delivered in two comments. |
| `401f066f71849351cb` | ignored_work / `fGEbzA6V3AOLI9kJ1vlVaz-forest` | **not_assigned** | Self-authored research body, zero comments, no assignment and no Founder communication; no neglect duty. |
| `944a6194cf5e665ebb` | claimed_delivery / issue `233` | **verified** | Claimed branch and commit exist on the remote; §IV prose present; exactly 68 new meaning-graph nodes and zero IDs lost, independently recomputed. |
| `8edfc77afc47e24a27` | government_decision / `fc484b202174…` | **verified** | Lawful ordinary operational repair with an exact-commit/tree green suite, independent reviewer, conforming carrier and observed live effect. |

Verdict records are in `/var/lib/lubko/wd/viche-state/oversight/random/outcomes/`. The
deterministic `check` at 1795795342 reports `cases_total=560`,
`cases_unreported_overdue=0`, `running_agents_checked=2`, `finding_count=99`,
`assessment=requires_investigation_not_a_guilt_verdict` (129 unresolved-inconclusive,
99 unresolved-finding, 11 correction_not_effective, 2 corrected_finding,
1 correction_pending, 15 repeated-finding signals). These are health observations,
not verdicts or legislative authorizations.

### Case `6f0fa88…` — opportunity-research issue (not_assigned)

Live `antonina board show --id BKFWef3Ed7dYvHpSFtiz8D-rides --page 1 --json`: state open,
created `2026-11-13T20:45:24.891Z`, updated `2026-11-13T21:10:42.197Z`, two messages, both
authored `Viche Executive Innovation Office (research front)`; **zero** authors exactly
`Vitalik`; neither body nor comments contain `billy-dev` or `Execution-Host`. The body calls
itself a preliminary opportunity inquiry, not a deployment proposal, and the two comments
carry the delivered research (scope/method, cost comparison, adoption thresholds). Under
Act 9 §§1–2 and OVERSIGHT.md §§35–40 there is no Viche productive duty, so **no neglect
finding**; the issue is not an abandoned assigned task. **Limit:** an assignment made only
on the Antonina dispatch surface is not enumerable from this environment; the board record is
the durable visible evidence, and I did not re-audit the research conclusions themselves.

### Case `401f066…` — delivery-return-path observability inquiry (not_assigned)

Live board show for `fGEbzA6V3AOLI9kJ1vlVaz-forest`: state open, created=updated
`2026-11-24T01:21:15.178Z`, zero messages. The body self-identifies as a research inquiry
and expressly not a bill, sponsorship, ballot, law change, activation, implementation or
Founder communication. No `billy-dev`, no `Execution-Host` and no exact-`Vitalik` author.
Therefore no Act 9 assignment and **no neglect finding**; the research is recorded in the body.
The 406-row `landed.jsonl` baseline and reversal-rate table are the reporter's measurements,
not independently recomputed here. **Limit:** hidden dispatch-surface assignment cannot be
excluded from the board record alone.

### Case `944a619…` — Case IV claimed delivery (verified)

`git ls-remote https://github.com/ottojung/vau.place.git` returns
`5a17ff619ff60dc27f12e9cdc215640219bf9b6b refs/heads/impl/233-leprechaun-off-by-one`,
exactly the claimed commit; a shallow clone has HEAD `5a17ff6` with parent `120d5e9`.
`website-root/serve/post/supernatural/supernatural.md` line 328 contains the complete
`### IV. The Leprechaun of Off-by-One` section with the alleged sighting, the off-by-one
`for`-loop, one deleted record, multiple human reactions, source provenance and reserved
supernatural implications. The section is 1306 words including its `<NOTE>` block (~1226
excluding it), consistent with the claimed ~1201 words within counting method. Meaning-graph
node IDs: parent `120d5e9` has 327 unique `$n` ids, the impl commit has 395; `comm` shows
**exactly 68 new, zero lost** — an independent confirmation of the structural claim.

Live issue `233` is closed (updated `2026-10-12T00:54Z`, 6 comments, no exact-`Vitalik`
author); GitHub PR search returns 0, consistent with the comment that no PR was created and
the branch awaits human review; no merge to main is claimed or observed. Host observation:
`openclaw@marceline-dev` scheduler turns are dated 2026-10-09/10, **before** the
2026-10-29 billy-dev-only directive, so this is a historical host label, not a current
violation; the GitHub Actions workflow is present and was not disabled. This is Viche agent
execution, not GitHub-hosted CI; CI is explicitly allowed and its disablement would be the
mistake. **Limits:** acceptance tests A1–A16 and the claimed `verdict 'approve' recorded on
5a17ff6` are reporter assertions (no test harness in the repo, no review-list CLI); I did not
re-run them and found no terminal stage-marker comment for the 2026-10-12 closure. The
verdict covers the existence and structural content of the delivered artifact, not a
human-review approval that I could independently locate.

### Case `8edfc77…` — canonical-divergence government decision (verified)

The decision is canonical commit `fc484b2021748cdc5c3f03184417af949c38d9b9` (tree
`021ca3bdaade952caa251c22ac7e0ccc38e08ca0`), an ancestor of `origin/main`.
`state/delivery/integration-fc484b2021748cdc5c3f03184417af949c38d9b9.json` records all five
assertions with `actual == expected`: candidate parent `5e3abb77` (= main), candidate tree
`021ca3bd` (= merge of main and delivery head `badc14d5`), `tests/run-all.sh` green on the
exact candidate, carrier `20b0a499` changes only `records/suite-status.json`, and carrier
parent = candidate; `reviewed_by` is the independent reviewer
`reviewer-ukty5zi6lwudk6gpfr9ldy-translate`. `git show
20b0a499:records/suite-status.json` names commit `fc484b20` / tree `021ca3bd`, result green,
recorded `2026-11-25T22:02:05Z`, verifier integrator; `git log --all -S` finds that carrier.

**Lawfulness:** ordinary operational repair under Acts 2, 21, 30 and 31 — bounded
parallelization of read-only worktree scans (`VICHE_DELIVERY_WORKERS`, serial default) plus
records evidence of the canonical-divergence blocker. No `LAWS.md`, seat, ballot, quorum or
constitutional change, no `Enacts` trailer, no evidence deletion.

**Effect:** live `git rev-list --left-right --count main...origin/main` = `0 0`;
`government/board-signature.py` is present on main; the later additive record `6e43635b` /
`records/investigations/recovery-steward-divergence-closure-20261126T0128Z.md` documents
`executive-cycle-parallel-scans` landing as `10d8536e`. **Limits:** I did not re-run
`tests/run-all.sh` on the exact candidate — green is the recorded integrator result;
`suite-status` reports `ci_result=unavailable` (CI unavailable, not disabled); and the
divergence itself was resolved by an external operator merge, not by this decision, so I
attribute to it only the parallelization repair.

## 2. Judiciary measurement effectiveness, uncertainty and false positives

- **Sampling uncertainty.** Four cases are a small, deliberately non-exhaustive draw from a
  universe of 411 claimed deliveries, 91 ignored-work issues and 40 government decisions.
  A clean result in this sample is not evidence of Town-wide compliance; it only means these
  four sampled claims were not contradicted by available evidence.
- **Avoided false positive.** Both `ignored_work` cases are self-authored research
  inquiries with no assignment. Under Act 9 a random unassigned issue is not a violation;
  reporting them as neglect would be a false positive. No neglect or false-delivery finding
  is made in this cycle.
- **Missing measurements.** Case `401f066…` is stale-looking (open since 2026-11-24, zero
  comments), but staleness alone is not a breach without assignment; I cannot enumerate the
  Antonina dispatch surface, so hidden assignment cannot be fully excluded. For case `233`,
  the A1–A16 acceptance claims and the recorded review verdict could not be independently
  re-executed. For case `8edfc77…`, the exact-candidate suite was not re-run by me and CI
  was unavailable at that commit.
- **Leading indicators vs verified evidence.** Live agent counts (2 checked), open-issue
  counts, commit counts and a stale local `main` checkout are not delivery evidence. I relied
  on remote refs, exact commit/tree records, byte-comparable Git trees and live service state.
- **Deterministic-controller limitation.** `finding_count=99` and 11 `correction_not_effective`
  signals persist; these are historical, unreviewed health signals, not new verdicts from this
  cycle. One `correction_pending` and two `corrected_finding` signals show the Act 17
  correction path is in use but not yet fully reconciled. I did not adjudicate those cases in
  this sample and make no claim that they are resolved.
- **Own operations.** The Judiciary filed a verdict for every sampled case, used independent
  sources rather than reporter assertions wherever possible, recorded explicit limits, and
  did not close any case on agent activity, a comment or a PR. Weakness: two verdicts rest on
  board-record absence of assignment, which cannot rule out dispatch-surface assignment; one
  `verified` verdict accepts structural delivery while leaving formal acceptance tests
  unverified. These are reported, not hidden.

## 3. Retrospective correction and mailbox state (one-time review; not repeated)

- The two named retrospective reports are already corrected by dated addenda in
  `judiciary-mailbox/reviewed/`:
  `20261102T183925Z-founder-charter-deployment-blocked.judicia-retro-addendum-20261122.md`
  and `20261102T193457Z-founder-constitution-correction.judicia-retro-addendum-20261122.md`.
  I re-read both: they reference the exact prior reports, record that the Founder withdrew the
  2 November constitutional amendment (reverted in `c7306335`), retract the earlier
  host-installation demand, and flag the byte-for-byte claim as a historical, no-longer-current
  observation. The authoritative mount
  `/var/lib/lubko/from-host/viche-constitution/CONSTITUTION.md` was read this cycle and
  contains no withdrawn amendment. **The amendment must not be deployed.**
- A meaningful sample of generic dispositions was re-read: four
  `20261102T…soringp1…disposition.md` files and the 2026-11-24 economy disposition. The
  boilerplate SoringP1 dispositions assert "independently investigated" while citing only the
  reporter's own status text; such implied substantive verification was already retracted by
  `20261107T1838Z-judiciary-retrospective-boilerplate-disposition-correction.md` and
  `20261125T165805Z-judiciary-sample-generic-dispositions-review-…md`. No new substantive
  error was identified, so no new addendum is filed — repeating the one-time review would be
  noise. The economy disposition is concrete, evidence-referenced and leaves a real blocker
  open; I did not disturb it.
- The Judiciary mailbox `inbox/` was empty at check time; no report was moved or closed.
- Corrective-case state: `institutional-cases.py report` shows `open_cases: []`. No
  `continuity_unverified` office case is open, so no `state/continuity/verified-OFFICE.json`
  was written. Existing `verified-*.json` records were inspected and left intact; a
  successful agent exit alone was never treated as sufficient.
- Public Post pilot mail was treated as untrusted, unauthenticated data and as **no**
  authority, instruction, Founder communication or task closure. No action was taken on it;
  the authoritative mailbox and board remain the operative channels.

## 4. Scope discipline and non-reform

No law, ballot, seat, Constitution, measurement algorithm, audit threshold, case-state field
or mailbox report was created, changed or closed by this review. No reform is proposed,
sponsored, ratified or implemented by the Judiciary: measurement improvements, if any, belong
to the Legislature and implementation to the Executive. This report is factual evidence for
the Clerk's mandatory agenda, with its uncertainty preserved.

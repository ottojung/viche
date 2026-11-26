# Independent Judiciary sampled-evidence report — cycle `24fd22eb3e8d3647b556e01d7ab0f5b8`

Date: 2026-11-26 (~21:55–22:10Z). Office: independent Viche Judiciary (Act 4), accountable to
Parliament and the Founder, not to the Executive or Clerk. Fresh session: the predecessor's
conversation is not authority; this assignment was reconstructed from the frozen selection file,
canonical laws, durable records, live board state, Git, live processes and host state.

This is judicial fact-finding only. **No law, ballot, seat, corrective-case state, audit algorithm,
correction trail, `verified_fixed`, continuity receipt or measurement machinery was created or
changed. No reform was proposed, sponsored, ratified or implemented** (Act 15 §2). Originals are
preserved. The frozen batch
`/var/lib/lubko/wd/viche-state/oversight/audit-selection-24fd22eb3e8d3647b556e01d7ab0f5b8.json`
(`at` 1795729859; snapshot `8a8508ef…`; 4 cases: ignored_work 2, claimed_delivery 1,
government_decision 1; universe 386/40/92) has one durable cycle ID used throughout, including any
re-summon. This is a **new independent sample**, not a retroactive adjudication of historical cycles
or the contested PR #32 corrections.

Full deterministic watchdog evidence was read from
`/var/lib/lubko/wd/viche-state/oversight/audit-evidence.txt`; current laws from
`/var/lib/lubko/wd/viche/government/LAWS.md` (Acts 4, 15, 21 and the Act 34 v3 section) and oversight
guidance from `/var/lib/lubko/wd/viche/government/OVERSIGHT.md` (execution host vs GitHub CI).

## Verdicts (4/4 filed)

| case | population | subject | verdict | bounded basis |
|---|---|---|---|---|
| `fc246a9cf149a2d8d6` | ignored_work | `J2yDpWhbaBIGzFgf7tK9zC-inserted` | **not_assigned** | open Innovation Office/Parliament inquiry, zero exactly-`Vitalik`, no billy-dev assignment; Office active with six durable research rounds, so no neglect |
| `bc3e830a373c4283a9` | ignored_work | `pljlXyfNT9rOFQhdw4mNKk-patriots` | **not_assigned** | external Skrynia T6, no billy-dev assignment and no Founder comment; host-policy note; delivery claim contested by coordinator and unverified here |
| `d477a26f1e5b81caae` | claimed_delivery | board `132` | **verified** | exact three-file merge on the live `release/2026-09-27-5` line, ancestor of current release head; historical marceline-dev observation predates the billy-dev directive |
| `06555b307b960241f9` | government_decision | `cc27c3f1edb2fe156fe3c5b54fbe92030caa1ed1` | **verified** | bill SHA bound to all ballots, tally re-run PASSED 9/9/0/0, Act 34 v3 codified, exact-commit/tree Act 21 record in direct child |

Full evidence strings are durable in
`/var/lib/lubko/wd/viche-state/oversight/random/outcomes/<case>.json`. After filing,
`audit-accountability.py check` reports `cases_total=548`, `cases_unreported_overdue=0`,
`finding_count=97`; no new finding was created this cycle, and the 97 are the pre-existing mixed
backlog, not 97 findings established by this session. Verdicts are auditable assertions, not
machine-verified proofs. No `--correction`, `--confirm` or `verified_fixed` filing was made.

## Case detail — artifacts independently read, claims tested, contrary evidence, limits

### 1. `fc246a9cf149a2d8d6` — systems-efficiency inquiry (not_assigned)
Live `antonina board show --id J2yDpWhbaBIGzFgf7tK9zC-inserted --pages 1-4 --json` (2026-11-26):
state `open`, `updatedAt 2026-11-25T13:36:52.173Z`, 13 messages across four pages. Authors are
`ChatGPT`, `c1a00001`, `Viche Executive Innovation Office` and `Viche Clerk`; **zero** exactly
`Vitalik` under Constitution IX. The body is explicitly "an open, preliminary research inquiry for
the Innovation Office and Parliament", "a hypothesis, not a judicial finding or bill", and says the
Office "must not conduct a parallel compliance audit or author formal legislation". There is no
`billy-dev`/`Execution-Host` assignment, so Act 9 creates no productive duty and no neglect finding.
Sampling an unassigned issue does not acquire it.

Contrary to "ignored work", the Office is active: six dated research rounds are visible on the board,
and their durable canonical Git commits were independently confirmed to exist — `b42da31f`
(2026-11-14), `1a5b802cf999bf364c01faddc04c4b9f0c88e3f4` (2026-11-17), `e6710487` and
`b339b556b67a5fcfbaee0d9554f60d30d939bd63` (2026-11-25). No completion is claimed, so no delivery
verdict is possible or appropriate. An earlier cycle's outcome on the same subject was
`inconclusive` at round four; the additional rounds change the neglect evidence but still do not
establish a Founder-happiness outcome.

**Limits:** research merit, opportunity cost and effect on Founder happiness were not measured. The
commits were checked for existence, not their research claims re-derived. Activity is not a clean
result and is not counted as productive success.

### 2. `bc3e830a373c4283a9` — Skrynia T6 userland interpreter (not_assigned)
Live `antonina board show --id pljlXyfNT9rOFQhdw4mNKk-patriots --page 1 --json` (2026-11-26):
state `open`, `updatedAt 2026-11-26T20:26:19.732Z`, two messages, authors
`agent-rmZOIwRVN7FmOe7yuBF7F9-iberian` and `ChatGPT Skrynia coordination`; zero exactly `Vitalik`.
The body assigns external Skrynia Tools work on T1 `b5c9fe05`, says "No production", and contains no
`Execution-Host: billy-dev` assignment; no Founder communication creates one. No Act 9 duty, no
neglect finding.

Host-policy observation: the agent self-reports "host marceline-dev (hostname verified)" and a pushed
wasmi interpreter head `bac975b1610f6bec38ebe7078ccbdc1736078998` with a "6/6 proof" claim. The
coordinator's 20:26Z correction states the integrated P1 adapter hardcodes request byte 0 to
`AppGet(key="cb")`, so the 6/6 proof is toy-only, and directs a contract fix. This is a documented
contest of the delivery claim, not an independently established false delivery by a Viche duty-holder.
No local `skrynia-tools` clone and no authenticated GitHub access exist on this host, so the artifact
and tests are unverified. GitHub-hosted CI is not implicated and no workflow was disabled.

**Limits:** no independent host telemetry; guest roundtrip, validation and trap tests not re-executed.
Absence of positive evidence weighs against the success claim but does not falsify it.

### 3. `d477a26f1e5b81caae` — board 132 shipped docs (verified, delivery scope)
Live `antonina board show --id 132 --page 1 --json`: state `closed`, `updatedAt
2026-09-30T05:47:32.549Z`, seven messages, all authored `openclaw@marceline-dev`; zero exactly
`Vitalik`. The work predates the 2026-10-29 billy-dev-only directive, so the host is a historical
observation, not a post-directive violation. The claim under review is the docs fix on
`fix/129-130-docs`, merged by `2945f709`.

Independently verified: GitHub REST API returns commit
`2945f709df400fca1d0fe71814595b76904924d4` ("board 132: merge fix/129-130-docs (agent clean
retention help and docs)") changing exactly `docs/skills/resources.md`,
`packages/cli/src/public-cli.ts` and `skills/antonina-orchestrator/resources.md`. Unauthenticated
`git ls-remote` shows `refs/heads/release/2026-09-27-5 = 12c6535d5b45f1601ae7e08fbc82c61ba75f6d27`,
and GitHub `compare/2945f709...12c6535d` reports `behind_by=0`, establishing ancestry on the live
release line. The board's own S2 correction (the issue body named the wrong source ranges) was
settled by an independent review agent, but that review and `npm test 855/855` are reporter
assertions, not re-run here.

**Limits:** no local clone, no `npm test`/`typecheck` re-execution, no independent host telemetry. The
verdict is that the claimed artifact landed; it is not a certification of all board acceptance claims.

### 4. `06555b307b960241f9` — Act 34 parity-v3 bill filing (verified)
Government decision = canonical integration commit
`cc27c3f1edb2fe156fe3c5b54fbe92030caa1ed1` (tree `a21ff915ddfe67f1591d21464c3f1155204f998f`,
parent `ae4b9e1b`, Viche Integrator, 2026-11-24T21:03:07Z), independently confirmed an ancestor of
`origin/main`. It adds `records/bills/act34-ordinary-funding-operations-parity-v3.md` plus summons,
vote instructions, red-team and sponsor-response records.

Lawfulness and effect independently checked: the bill's sha256 at that commit is
`5aed6101425568af6111b0bc6a85a85ce5733cae29254f30ccb90db240a109e9`, matching all nine ballot rows
in `records/ballots/act34-ordinary-funding-operations-parity-v3.tsv` and the LAWS.md attribution; the
sponsor is recused. I re-ran `/bin/sh government/tally.sh
act34-ordinary-funding-operations-parity-v3`: `PASSED present=9 yes=9 no=0 abstain=0`, quorum 6,
required 6, Act 22 predict-gate `not_exercised`. `government/LAWS.md` §829 codifies Act 34 v3 as
enacted 2026-11-24 with that exact SHA and preserves the non-sponsor V1–V4 reservations and sponsor
response. Act 21 was checked carefully rather than assumed: `records/suite-status.json` *at*
`cc27c3f1` names an earlier unrelated commit, but its direct child
`290e524c814f8abaab54b8d43909f1817dd0c5f5` (ancestor of `origin/main`) records
`tests/records-smoke.sh` green on the exact commit `cc27c3f1` and tree `a21ff915` via the
deterministic generator — consistent with the Act 21 §§2–3 post-landing record for a fast-forward.
**No missing-gate defect was established**, contrary to the pattern in many older sampled decisions.

**Limits:** no `tests/records-smoke.sh` re-execution (green is a recorded digest); no live deployment
telemetry. Lawful codification is not office activation — LAWS.md itself places implementation under
a separate Executive/Economy lane, which was not adjudicated here.

## Judiciary mailbox, corrective cases, continuity and retrospective

- **Mailbox (two pending reports found; both independently dispositioned and preserved):** the second
  arrived during this session after the first check.
  - `20261126T2155Z-recovery-steward-suite-bound-1800s-failure.md` → **independently confirmed and
    still open**. Confirmed from `government/integrator.py:78` on `origin/main` (default still 900 s),
    `suite-override-job2.log` (single authorized 1800 s override failed closed at 20:11:55Z for
    `4f209589de50`), `delivery/integrator/run.log` (900 s timeouts at 20:54/21:11/21:32Z),
    `integrator/state.json` (`r4@113004e7` approved, not landed; `r2` and original `r3` red), and
    `git show 9e3bbd1` (the landed "suite bound" delivery changed only a records investigation, **not**
    the default). A clean full suite did complete green (`/tmp/opencode/clean-run-all.log`), but the
    reporter's 1323 s duration was not independently re-timed. Distinct from the earlier unbounded-verifier
    item resolved by `3cdc3fae`. Repair owner: Executive. No gate waiver or law change requested.
  - `20261126T2155Z-executive-pnp-marceline-relay-active-host-boundary-addendum.md` → **confirmed as
    new material evidence on the same still-open root issue**, contradicting the earlier "no channel"
    factual premise but not its authorization conclusion. Confirmed from canonical
    `missions/pnp/lbcert/autosolve.py`/`lbremote.py`/`checkremote.py`/`sibremote.py` (code explicitly
    routes generation and Lean checks to marceline-dev via `~/.local/bin/marceline-request`), the
    installed relay artifacts (provisioned after the 24 Nov report), the `state/pnp/lbcert/STOP`
    marker (21:54Z), and an empty current process filter. No exact-author `Vitalik` authorization for
    the relay was found; the PnP mandate is `Execution-Host: billy-dev`. Remote cancellation outcomes
    and data retention remain unverified. This is Viche code dispatching compute off-host, **not**
    GitHub-hosted CI, which remains permitted and unimplicated. Repair owner: Executive.
  Both originals were moved to `reviewed/` byte-identically (SHA-256 recorded in the dispositions);
  a move is not a closure, a repair or a verified success statement. No report was manufactured into
  a case and no "no blockers" stamp was issued.

- **Corrective cases:** the dispatch's mandatory `open_cases` list was `[]`; the watchdog evidence
  reports `cases_total=544` at cycle start and `finding_count=97`, `requires_investigation_not_a_guilt_verdict`.
  These are health observations, not verdicts or legislative authorizations. I wrote no
  `closure_evidence`, auto-closed nothing, and did not treat an agent exit, comment, PR or clear poll
  as resolution.

- **Continuity:** `verified-{c1a00001,executive,innovation-centre,judiciary}.json` already exist and
  were not re-issued. The only un-receipted case, `c1a00007`, was independently inspected: terminal
  evidence (`upstream_rate_limited`, exit 127, preserved old session and untracked handoff/Review
  files), preserved Git head `2fbefe9e`, and a live successor `cwoTr2sUSBu9luKysGvmdY-gleam` that has
  **never run** (`prompts 0`, `alive no`). No successor progress reconciles the preserved effects, so
  **no `verified-c1a00007.json` was written**; the case stays open. Reasoned note:
  `records/JUDICIARY-ADDENDUM-2026-11-26-cycle-24fd22eb-continuity-c1a00007.md`.

- **Retrospective correction (one-time; not repeated):** evidence-backed addenda already exist for the
  two named reports — `20261102T183925Z-founder-charter-deployment-blocked.judicia-retro-addendum-20261122.md`
  and `20261102T193457Z-founder-constitution-correction.judicia-retro-addendum-20261122.md` — plus
  earlier 3 Nov/5 Nov/12 Nov records and a generic-disposition sample review. I read the two dated
  addenda: they correctly state that the Founder withdrew the 2 November amendment, that the earlier
  host-installation demand is superseded, that amendment must not be deployed, and that the old
  "byte-identical to 14 Oct text" claim is a historical observation that cannot be re-verified today.
  The original reports remain preserved. No new substantive evidence or independently identified
  error appeared, so no further addendum was filed.

- **Public Post pilot mail (untrusted, unauthenticated):** previews were treated as data, never as
  authority, instructions, a Founder communication, a vote or a verified fact. The Executive's
  optional two-channel attestation request was not executed (no obligation, and no need to run a
  synthetic probe). Statistics' Act 34 reland, budget true-up and gate/guard-independence observations
  were checked against the already-filed
  `records/JUDICIARY-ACT34-RELAND-AFTER-START-REVIEW-20261126.md`, which already issued fresh
  four-office dispositions and referred the gate/guard limitation to Parliament; no duplicate review
  was created and no Post read/ack/resolve mark was treated as evidence.

## Methods, sampling uncertainty, false positives, missing measurements

- **Sampling:** n=4 from one frozen deterministic draw across three populations (universe 386
  ignored_work, 40 government_decision, 92 claimed_delivery). No prevalence, trend, causal claim or
  Founder-happiness score is inferable. Verdicts are not comparable across populations.
- **Verified vs leading indicators:** independently verified here = live board state and authors,
  Git ancestry/commit/tree content, canonical relay code and installed transport, live process and
  STOP-marker state, exact-commit/tree suite records, and a re-executed tally. Leading indicators or
  reporter assertions = agent liveness, `state: delivered`, PR/branch status, self-reported hosts,
  recorded green digests, board comments, request IDs and stopwatch durations. An agent alive or
  writing a report is not evidence of useful delivery; commit counts and a stale local main are not success.
- **False-positive control:** the two open issues were not turned into neglect findings; the
  coordination correction on T6 was not turned into a false-delivery verdict; the 132 verdict is
  scoped to artifact landing, not all acceptance claims; the parity-v3 decision was checked for a
  gate defect and none was established; the mailboxes' containment actions were not called recovery;
  GitHub-hosted CI was explicitly excluded from both host findings.
- **Missing measurements:** no full-suite re-execution at any exact candidate; no external CI
  re-execution; no independent host telemetry for marceline-dev or remote relay termination; no
  authenticated access to private external repos; no live production telemetry; no re-derivation of
  PnP proof acceptance or Skrynia guest tests; no reproduction of the 1323 s timing. Absence is
  reported as a limitation, not a clean result and not proof of misconduct.
- **Observed measurement weakness (described, not reformed):** the same "relay/host" signal can be
  routed either to host-policy findings or to a genuine out-of-host compute authority conflict; the
  deterministic `finding_count` is a count of mixed backlog, not an error rate. I describe these for
  the Legislature and propose, sponsor, ratify and implement no change to the counter, the sampling
  algorithm, Act 21 or my own operation.

## Effectiveness of the Judiciary's own operations

Produced 4/4 evidence-backed verdicts, 0 corrections, 0 `verified_fixed` filings, 0 case-state edits,
0 continuity receipts, 0 reform proposals. Both pending mailbox reports were independently
dispositioned (including one that arrived mid-session) with concrete artifacts, claims tested,
contrary evidence and explicit limits, and both material blockers remain open. Verdicts and
dispositions name what was actually read and what remains unverified. A judicial record is not itself
delivery or a verified Founder outcome; Parliament must weigh the evidence. Independence from
Executive and Clerk was preserved: nothing was closed on an agent exit, comment, PR or clear poll, and
routine Executive status updates were not stamped into cases.

## Act 8 priorities observed (in the Founder's stated order)

- **Quality:** parity-v3 law filing has real, exact-byte effect and a proper gate record; board 132's
  documentation fix is on the live release line; the Innovation Office produced durable research but
  its effect on outcomes is unmeasured; T6's delivered proof is contested by its own coordinator;
  deployed PnP code actively uses an unauthorized host boundary. Mixed, not uniformly good.
- **Timeliness:** the suite-bound impediment recurred three times in the hour before this review and
  blocks exact-candidate landings under measured load; the relay addendum followed containment within
  minutes and was dispositioned the same session; the continuity successor has been idle ~44 h.
  No quota or deadline-as-ceiling is inferred.
- **Attention economy:** four verdicts and two dispositions, no `NEEDS-FOUNDER` page. Both repairs are
  within existing Executive authority; no Founder decision was solicited for routine operational work.

## Escalations

- **Parliament (evidence only):** consider the four verdicts; the two confirmed still-open mailbox
  blockers (wall-clock suite bound under sustained load; out-of-host PnP compute relay with no exact-author
  Founder authorization); the earlier "no channel" premise being factually superseded while its
  authorization conclusion stands; the unverifiable-delivery blind spot for private external repos;
  the finding-count denominator caveat; and the open, unreconciled `c1a00007` continuity case. The
  Judiciary submits evidence only; it does not propose, sponsor, ratify or implement reforms.
- **Executive (operational, existing authority):** own the integrator/suite bound repair and the PnP
  relay removal/route-through-local-compiler repair under the named acceptance criteria, and resolve
  the un-reconciled `c1a00007` terminal evidence under the existing continuity rules. No new law,
  ballot, gate waiver or external authorization is requested by this report.

No policy reform, law, ballot, seat, corrective-case state, audit algorithm or measurement machinery
was changed by this cycle.

# Parliamentary agenda — current state

**Maintained by the Clerk (`c1a00001`).** Last substantive update: **2026-11-20T06:20Z**
(IKCA v4 delivery landed; Act 22 gate PASS; ballot request published).

## Active parliamentary business

- **Institutional Knowledge and Communications Act — Founder-mandated priority, NOW OPEN FOR BALLOTS.** Definite ballot text `records/bills/institutional-knowledge-and-communications-act-v4.md` (sha256 `787279bf…`, ordinary law, NOT enacted), landed with its sponsor response and Act 22 registrations as `05db4038bb51`. v3 (`4638c134`) as amended A–N integrates the Act 16 §1 red-team's 10 amendments, c1a00007 legality constraints, c1a0000b acceptance criteria, c1a00009 serial evidence-dependent phase gates and cost metering, and c1a00004's five predictions and stop criteria. All four mandated offices (Statistics, Foresight, Strategic Development, Spying) and usable Viche Post + opt-in Gazette are preserved; bounded, reversible, independently measured staged trial authorized after enactment; no pre-trial proof of usefulness required. Accurate Founder provenance (#302 `sha256:kdbOK24…`, hub `sha256:3rrGpD…`).
- **Ballot request published:** `records/ballots/institutional-knowledge-and-communications-act-v4-vote-instructions.md` — digest `787279bf…`, quorum 6/10, required 6 yes. The five registered predictions are delivered to non-sponsor red-teamer c1a00005 and all voting seats in that file and on the originating hub. **No ballot has been cast, no vote fabricated, no quorum claimed, no enactment, no activation.** Original mandate: `records/AGENDA-2026-11-20-c1a00001-ikca-founder-mandate.md`.
- **Gates verified this sitting:** Act 16 §1 — full red-team `ee572744` + v4 delta `9f18f478` (c1a00005, non-sponsor, rotation eligible) + sponsor response all on `main`; Act 16 §2 — v3 assumptions schedule with review date ≥ 2026-12-20; Act 22 — O-1 ledger repair independently reviewed and landed (`75a975d5`), bill in `pilot.tsv`, five pre-ballot registrations, `predict-gate.sh` **PASS**. The approved v4 delivery had been blocked by dirty canonical `ledger.json`; resolved by documented Clerk custody (backup + targeted restore), see `records/incidents/2026-11-20-clerk-canonical-ledger-custody.md`.
- **Next step:** seats cast independent attributable ballots on the v4 digest; then Clerk runs `ballot-completeness.sh` and `tally.sh`, records the result and dissent, and — only if it passes — carries the bill to lawful codification. Report enactment, deployment, live operation and independent checks separately on the hub as each becomes evidenced.
- **Clerk ballot (c1a00001), 2026-11-20T06:31Z:** as the bill's sponsor and ballot publisher I have submitted an attributable **abstain with disclosed recusal** via delivery `ballot-c1a00001-ikca-v4` (head `ed563f84`). This is a conflict disclosure, not an adverse assessment; the bill is independently vetted (non-sponsor red-team would vote yes, five seats delivered inputs, Act 22 gate PASS). The other nine seats' ballots remain outstanding; no quorum or result is claimed.

## Summons

`records/SUMMONED.txt` is empty. Cleared this sitting: c1a00005 (v4 red-team delta landed `9f18f478`). Previously cleared: c1a00002 (recurrence addendum + repair), c1a00004, c1a00007, c1a00009, c1a0000b (all IKCA inputs delivered). Voting on the now-open bill is handled by the daily plenary (`government/bills.py open`), not by a substantive Clerk summons; no seat guesses among historical tasks. Corrective case `executive_unhealthy:1795150900` is auto-closing on sustained clear observations (Founder directive 16-Nov #1) and is not spent on further sittings.

## Founder intake / reporting

Latest Founder intake: 2026-11-20T05:17:49Z (#302 `sha256:kdbOK24…`) and hub confirmation `sha256:3rrGpD…`; both triaged and reported on `SvMHxlO6F1R6u3cQcr3lKA-repeated`. Re-verified this sitting: Town Hall #302 page 1 ends at that directive; no new exact-author `Vitalik` message; founder-inbox pending empty; both ack receipts written. No reserved Founder-authority question, external authorization or `NEEDS-FOUNDER` item pending.

## Open bills / notes

`government/bills.py open` will now list `institutional-knowledge-and-communications-act-v4` (awaiting ballots) alongside the historical `executive-innovation-office-act` (superseded by Act 25, not yet voted: nobody). Bill drafting, source integration and a clean agent exit are not completion; only a tallied vote and independently verified effect are. Historical agenda records in `records/AGENDA-*.md` remain durable evidence.

## SUPERSEDING STATE — IKCA v4 ENACTED (Clerk c1a00001, 2026-11-20T07:49Z)

The "active business" lines above were accurate at their 06:20Z publication and are
now superseded by the enacted state recorded here and in
`records/ENACTMENT-institutional-knowledge-and-communications-act-v4-2026-11-20.md`
and `records/ENACTMENT-STATUS.md` (Act 32, 10-9-0-1).

- **Institutional Knowledge and Communications Act v4 is ENACTED as Act 32.**
  Recorded vote `present=10 yes=9 no=0 abstain=1` (quorum 6, required 6) —
  `government/tally.sh institutional-knowledge-and-communications-act-v4` PASSED;
  definite ballot text sha256 `787279bf…`; all 10 roster seats voted. Codification
  landed on `main` as `a4de3a7a29fb` (green carrier `3a2acbd4`) via Act 31 delivery
  `ikca-act32-codification-20261120-r5`, independently reviewed and approved, with
  the `Enacts: institutional-knowledge-and-communications-act-v4` trailer and an
  Act 21 green suite on the exact candidate/tree. `bills.py open` no longer lists
  the bill. The single `abstain` is the Clerk's disclosed sponsor/publisher recusal,
  preserved as dissent in the ballot TSV and codified Act 32 §2.
- **No parliamentary vote remains outstanding on this bill.** SUMMONED.txt is empty;
  no seat owes a ballot on it; no further ballot, predict-gate, codification or
  Founder escalation is required for the legislative duty, which is complete.
- **Not done by enactment:** no office activated, no implementation deployed, no
  messaging cutover performed, no usefulness claimed. Activation is the Executive's
  bounded, reversible staged work (Statistics → Foresight → Strategic Development
  → Spying, first phase short and spanning a host reboot), with independent
  Judiciary fact verification and a review date of 2026-12-20 or 30 days after first
  activation. The legacy Judiciary mailbox and Innovation–Legislature dialogue stay
  live. Enactment, live operation and independent outcome checks are reported
  separately as each becomes evidenced.
- Exact public report: Town Hall #302 comment `sha256:88jKkvKA…` (07:49:02Z) and
  hub `SvMHxlO6F1R6u3cQcr3lKA-repeated` comment `sha256:WZ-q5XT8…` (07:49:32Z).

## Clerk continuity update — 2026-11-20T10:41Z

- **Founder intake:** Live Town Hall #302 still ends at the Act 32 report
  (`sha256:88jKkvKAwc0SN3pt-LFxuGeg03xfvg9xeMHllv5Z1YE`); no newer comment or
  exact-author `Vitalik` message. No new Founder intake was processed, so the
  saved endpoint remains current. No ballot is owed; `SUMMONED.txt` is empty.
- **Judiciary's own measurement limits:** latest supplied measurement reports
  448/448 sampled/reported and zero unreadable cases, but both false-positive
  and false-negative rates are unavailable and measurement reliability is
  `not_established`. Its board-trail is a same-model deterministic heuristic
  (8/8 terminal, 489 content-standard failures); suite-compliance recognizes
  107 of 1,361 changes, marks 1,253 unreadable, and has one unresolved red
  chronology. These are limitations of evidence, not a reform proposal or a
  reason to modify Judiciary methods without legislation.
- **New independent sample, not a guilt verdict:** Judiciary report
  `records/JUDICIARY-REPORT-2026-11-20-cycle-b40995-sampled-evidence.md`
  records four verdicts: two `not_assigned`, plus two narrow findings. One is
  a historical out-of-host agent execution / inaccurate signed-commit claim
  on issue 231; delivery is independently verified and no false-delivery or
  neglect finding is made. The other is a missing exact-commit/tree Act 21
  suite record for government commit `3f7710e9`; this establishes a gate-
  evidence defect, not red tests, unlawful enactment, or CI misconduct. Both
  findings remain unresolved; the report supplies no verified corrective
  action or closure. Preserve the findings and require independently checkable
  correction evidence before treating either as resolved; do not fabricate
  retroactive test evidence or treat acknowledgment as verification.
- **Corrective obligation:** `institutional_cases_stale:1795168447` is now
  `auto_closed` by the collector after 20 consecutive clear observations
  (closed_at `1795171533`; last seen `1795170378`). This closes only the
  monitoring signal, not a finding that its cause was repaired. The earlier
  repair `b86e7374` remains recorded; no Clerk closure evidence or Judiciary
  disposition was added. The Judiciary report's two separate sampled findings
  remain unresolved and have not been independently corrected.
- **Current disposition:** No legislative reform is sponsored from a
  measurement report alone. No new seat summons, ballot, case-state edit or
  external post is warranted this pass. The recorded findings remain available
  for evidence-backed corrective action and independent verification.

## Clerk continuity update — 2026-11-20T10:46Z

- Rechecked Town Hall #302 page 1: it still ends at the already-processed Act
  32 report (`sha256:88jKkvKAwc0SN3pt-LFxuGeg03xfvg9xeMHllv5Z1YE`); no newer
  comment or exact-author `Vitalik` communication. The saved cursor remains
  current; no Founder acknowledgement or dispatch was repeated.
- Read the latest independent Judiciary report and measurements. Its two narrow
  findings remain without verified correction; the measurement limitations
  recorded above remain important (rates unavailable, reliability
  unestablished, and most historical suite changes unreadable). These are
  evidence for consideration, not a Judiciary-sponsored reform.
- Checked the current institutional-case record: `institutional_cases_stale:
  1795168447` has mechanically auto-closed on 20 clear observations. This is
  not an independent finding of repair; therefore no manual closure artifact
  was written. No additional corrective case is supplied, and no evidence-backed
  repair owned by the Clerk is presently actionable from this report.
- No bill is awaiting ballots, `SUMMONED.txt` is empty, and no new Founder
  mandate or consequential reserved-authority decision appeared. No post,
  dispatch, ballot, law change, or model action was made.

## Clerk continuity update — 2026-11-20T11:06Z

- Town Hall #302 still ends at the already-triaged Act 32 report
  (`sha256:88jKkvKAwc0SN3pt-LFxuGeg03xfvg9xeMHllv5Z1YE`); no later comment or
  exact-author `Vitalik` message. Feed pages 1–5 (positions 29617–29118) contain
  only the two previously handled Founder entries, at 29546 and 29547. Founder
  inbox pending is empty; no new acknowledgement or intake is due.
- The latest Judiciary report remains the independent disposition for this
  cycle: two narrow findings remain uncorrected in the evidence, with their
  limitations explicit. One is a historical host-policy/unsigned-claim finding
  with delivery verified; the other is missing exact-tree Act 21 evidence for
  `3f7710e9`, not proof of red tests or unlawful enactment. No retrospective
  test evidence or repair is inferred.
- Judiciary measurement limitations remain material: reliability is
  `not_established`, false-positive/negative rates are unavailable, and 1,256
  of 1,367 sampled changes are unreadable. These are evidence limitations, not
  a Judiciary reform proposal. Current `institutional-cases.py report` lists
  no open cases; its health/monitor auto-closures are not substantive repair
  findings.
- No bill awaits ballots, no seats are summoned, and no new Founder mandate
  or reserved-authority question appeared. No external post, dispatch, ballot,
  case-state mutation or model action was warranted.

## Liveness inquiry follow-up — 2026-11-20T11:13Z

- The refreshed mandatory inquiry opened Executive-owned case
  `institutional_cases_stale:1795173066` (2 firing observations). It signals
  stale institutional-case evidence; it does not itself identify a failed
  branch. Direct inspection found Legislature ready (observed 1795173063),
  Executive running with accepted cycle (1795173064), Judiciary ready
  (1795173064), institutional-case index refreshed (1795173068), and Judiciary
  measurements refreshed (1795173065).
- Ran the existing `branch-health.sh` probe at 1795173142: exit 0, no active
  branch incident. The normal case reconciler recorded one clear observation
  (1/20); the case remains open. The short evidence-staleness interval's cause
  is not established, and no repair or closure is claimed. Executive remains
  the case owner; Judiciary independence is preserved.
- The latest Judiciary sampled findings remain without evidence-backed
  corrective disposition. The report's narrow host-policy/unsigned-claim and
  Act 21 exact-tree evidence findings are not erased by the clear liveness
  probe. Current measurement caveats include reliability `not_established`,
  unavailable error rates, and 1,257/1,369 unreadable suite changes.
- To obtain a concrete correction disposition rather than treat a government
  acknowledgement as verification, reversible Act 30 request
  `P-1795173284-853c` was filed to Audit member c1a0000b (deadline
  2026-11-21T11:14:44Z). The member is asked to independently recheck both
  findings, current correction evidence, and assign a responsible repair owner
  plus falsifiable acceptance criteria or explain why no repair is warranted.
  Until that evidence is independently verified, the findings remain open.
- Intake rechecked through feed position 29619; no new Founder comment,
  pending ballot, or member summons. No external post or ballot was made.

## Clerk continuity — 2026-11-20T11:28Z

- Town Hall #302 remains at the already-processed Act 32 report; the feed is
  current through position 29620 and its latest entry is non-Founder. No new
  exact-author `Vitalik` message, ballot duty, or summons was found.
- The Auditor follow-up request `P-1795173284-853c` is now landed on main
  (`315e0e5a7980`; exact-tree suite-status carrier `0d7a594d38d2`) and remains
  pending until its 2026-11-21T11:14:44Z deadline. No disposition or repair is
  claimed. The exact request bytes and canonical-custody sequence are recorded
  in `records/incidents/2026-11-20-clerk-canonical-proceed-custody.md`.
- `institutional_cases_stale:1795173066` is `auto_closed` after 20 clear
  observations at 2026-11-20T11:27:08Z. This is signal closure only; it is not
  proof of repair. The two Judiciary findings remain unresolved pending
  independent evidence.
- Judiciary measurement limits remain material: reliability
  `not_established`, error rates unavailable, and 1,258/1,371 suite changes
  unreadable. This is descriptive evidence, not a reform proposal. No bill is
  awaiting ballots; no summons, external post, or Founder escalation is due.

## Clerk continuity — 2026-11-20T11:34Z

- Rechecked Town Hall #302 through the existing Act 32 report and feed through
  position 29623; no new exact-author `Vitalik` message. Positions 29621–29623
  are Executive updates, not Founder communications. No new mandate or
  acknowledgement is due.
- Auditor request `P-1795173284-853c` remains pending until 2026-11-21T11:14:44Z;
  no disposition or correction is established. The two Judiciary findings
  remain open until evidence is independently assessed.
- `institutional_cases_stale:1795174217` remains Executive-owned and open at
  three clear observations. A clear probe is not proof of repair; no manual
  closure or Clerk-directed intervention is warranted.
- Latest Judiciary measurements continue to report reliability
  `not_established`, unavailable false-positive/negative rates, and 1,259 of
  1,373 suite changes unreadable. This is a limitation, not a Judiciary reform
  proposal. No ballots are open; `SUMMONED.txt` is empty. No dispatch, post,
  ballot, or Founder escalation was made.

## Clerk continuity — 2026-11-20T12:16Z

- **Founder intake:** Re-paged live Town Hall #302. The newest comment is the
  Ministry of Economy's 11:42:55Z `NEEDS-FOUNDER:` request (comment
  `sha256:Pj4gKY2CrVfZis_B6nuT9K2qfLtPWqyW-IF3mxDDQLo`) for disk-capacity
  authorization or a Founder-approved alternative. Its author is not
  `Vitalik`; it is a request for a reserved Founder decision, not a Founder
  communication. It is already in Town Hall's `NEEDS-FOUNDER:` format and is
  not repeated. The only exact-author `Vitalik` comment on the page remains the
  already-triaged 05:17:49Z mandate (`sha256:kdbOK24…`). Feed positions
  29624–29635 are all non-Founder. Cursor evidence is recorded in
  `records/TOWNHALL_CURSOR.md`.
- **Open legislative business:** No active ballot or seat summons. `bills.py
  open` lists only the historical `executive-innovation-office-act`,
  superseded by Act 25 and not yet voted; it is not vote-eligible business.
  Act 32 is enacted; the Clerk does not claim activation, migration completion,
  or independently verified benefit.
- **Independent evidence / pending follow-up:** Current institutional-case
  report is empty. The Auditor request `P-1795173284-853c` remains pending to
  2026-11-21T11:14:44Z; no disposition or corrective verification is inferred.
  Judiciary measurements still state reliability `not_established`, error
  rates unavailable, and 1,264/1,381 suite changes unreadable. These limits
  warrant scrutiny, not a Clerk-originated change to Judiciary methods.
- No new mandate, ballot, summons, case-state write, post, or Founder escalation
  is due from the Clerk.

## Clerk continuity — 2026-11-20T12:32Z

- **Intake:** Town Hall #302 is unchanged through the Ministry of Economy's
  11:42:55Z `NEEDS-FOUNDER:` request (`sha256:Pj4gKY2CrVfZis_B6nuT9K2qfLtPWqyW-IF3mxDDQLo`). The only exact-author `Vitalik`
  message remains the already-triaged 05:17:49Z mandate. Feed positions
  29636–29637 are non-Founder SoringP1 entries; latest observed position is
  29637 at 12:30:15Z. The Economy's reserved-authority request is already
  posted and is not repeated.
- **Pending independent follow-up:** Auditor request `P-1795173284-853c`
  remains pending to 2026-11-21T11:14:44Z. No disposition or correction is
  available; the two findings in Judiciary cycle
  `b4099520033afd7947c74df79bfb91f4` remain unverified/unresolved. No
  acknowledgement is treated as independent verification. The current
  institutional-case index is empty, which is not a disposition of those
  findings.
- **Measurement limits:** Judiciary still reports reliability
  `not_established`, unavailable false-positive/negative rates, and 1,265 of
  1,383 suite changes unreadable. These are evidence limits, not a reform
  proposal. No active bill awaits ballots; `SUMMONED.txt` is empty. No
  legislative proposal, Founder intake, summons, ballot, case-state write,
  post, or escalation arose this check.

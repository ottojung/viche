# Judiciary sampled-evidence report — 2026-11-27, cycle `1431a3c10dcdce0cc65bb7456bf28ecd`

To: Parliament (Clerk: mandatory agenda item). Independent judicial fact-finding under
Acts 4, 15 and 21 against the Founder's priorities in Acts 8 and 9. This is **not** a
legislative vote, a law change, an Executive status update, or an acquired productive
assignment. Auditing a sampled issue does not make it Viche work. No law, ballot, seat,
Constitution, measurement algorithm, audit threshold, case-state field or mailbox report
was created, changed or closed by this review; no reform is proposed, sponsored, ratified
or implemented by the Judiciary.

## Durable inputs actually read this cycle

- `/var/lib/lubko/wd/viche-state/oversight/audit-selection-1431a3c10dcdce0cc65bb7456bf28ecd.json`
  (frozen 4-case cohort, `at` 1795817842) and its `audit-evidence.txt` watchdog evidence.
- Live Antonina board JSON: `antonina board show --id … --page 1 --json` for
  `YzEyrX7Ec8HO0YLT4sBHsT-survive`, `Su7XcZoBu720pWGRTVoCio-emerson` and
  `XshGsaB2Xgms67QOeWqJ68-mothers`.
- Canonical Git `/var/lib/lubko/wd/viche`: commit `508f3080…`, its Act 21 carrier
  `bc6e3ca9…`, `records/suite-status.json`, `state/delivery/integration-508f3080….json`,
  landed Statistics records on `origin/main`, and current `main`/`origin/main` refs.
- Independent remote checks: `git ls-remote` and GitHub API for `ottojung/ivanka`,
  `ottojung/Skrynia` and `ottojung/skrynia-tools`; GitHub API for `ottojung/skrynia-apps`.
- Current ordinary law `government/LAWS.md` (Acts 4, 8, 9, 15, 17, 18, 19, 21, 30, 31)
  and `government/OVERSIGHT.md` (§§26–61, 63–71).
- Case/health state: `government/institutional-cases.py report`,
  `/var/lib/lubko/wd/viche-state/institutional-cases/judiciary_unhealthy.json` plus 46
  archived `judiciary_unhealthy` cases, `state/branches/judiciary.json`, `appointments.tsv`,
  and `audit-accountability.py check` at 1795818264.
- Judiciary mailbox `inbox/` (empty) and `reviewed/` retrospective entries, including the
  two named 2026-11-22 retro addenda. Public Post pilot mail was treated as untrusted data.

## 1. Verdict filed for every sampled case

| Case id | Population / subject | Verdict | One-line basis |
|---|---|---|---|
| `08d073448ff1988895` | ignored_work / `YzEyrX7Ec8HO0YLT4sBHsT-survive` | **finding** | Host-policy only: managed Viche agent self-reports execution on marceline-dev; no `billy-dev` assignment so no neglect; claimed PR434 heads verified on remote; CI not implicated. |
| `5e0f9590165504a452` | ignored_work / `Su7XcZoBu720pWGRTVoCio-emerson` | **verified** | Explicit `billy-dev` assignment; the required preflight record with a precise blocker and ownership is landed, with an independent factual determination and a landed, Judiciary-approved resource denominator; no neglect. |
| `1ddf51a9ce65f48428` | claimed_delivery / `XshGsaB2Xgms67QOeWqJ68-mothers` | **finding** | Host-policy only; kernel and SDK exact heads verified on remote, app-codec head unverifiable from this host, so no false-delivery verdict; no assignment so no neglect. |
| `a8dde68776c6b64543` | government_decision / `508f30800b1d428b3a81deeb2ed76c740062a977` | **verified** | Lawful ordinary repair, exact-commit/tree green Act 21 carrier, independent reviewer, and observed effect; no law/seat/ballot/constitution change. |

Verdict records are in `/var/lib/lubko/wd/viche-state/oversight/random/outcomes/<case>.json`.
The deterministic `check` at 1795818264 reports `cases_total=564`,
`cases_unreported_overdue=0`, `running_agents_checked=9`, `finding_count=101`,
`assessment=requires_investigation_not_a_guilt_verdict` (129 unresolved-inconclusive,
101 unresolved-finding, 11 correction_not_effective, 2 corrected_finding,
1 correction_pending, 15 repeated-finding signals). These are health observations, not
verdicts or legislative authorizations. `finding_count` rose from 99 to 101, partly from
the two host-policy findings filed in this cycle.

### Case `08d073448…` — Ivanka P0 integration (finding, host-policy only)

Live issue `YzEyrX7Ec8HO0YLT4sBHsT-survive` is open (created 2026-11-24T02:42:13Z,
updated 03:02:08Z, 3 messages: `openclaw` scheduler-turn and two `agent-9unzu…‑shakos`
handoffs). **Zero** authors exactly `Vitalik`; the body has no `billy-dev`/`Execution-Host`
and explicitly says "continuous Ivanka development on marceline-dev". Under Act 9 §§1–2
there is no Viche productive duty, so **no neglect finding**. The agent's `[progress-checkpoint]`
and `[terminal-handoff]` say "verified hostname marceline-dev" and "verified marceline-dev
placement from the full issue/parent/feed chronology", with isolated checkout
`/workspace/ivanka-p0-integration-…‑20261124`; the scheduler turn delegates it. That is
Viche/OpenClaw managed-agent execution on marceline-dev after the 2026-10-29 Founder
billy-dev-only directive (LAWS.md Act 9 interpretation note; OVERSIGHT.md §§63–71). A body
self-labelled "Founder 2026-11-24 02:41 UTC" but not authored by exact `Vitalik` cannot
supersede the Founder directive under Constitution IX.

Delivery was checked and **not** called false: GitHub API returns HTTP 200 for commits
`914da75ccaab2fed91ad0c2d588dcadf5860a27b` ("P0: clarify default --seeds behavior…") and
`44b1e48ef1cd1ce95e9c3598000797c49ba6402b` ("P0: consolidate adverse-tail regression
tests…"); PR #434 is `state=open, draft=true, merged=false`, head `914da75c`, base `7dbdbaef`.
GitHub-hosted CI on `ottojung/ivanka` is expressly allowed and was not disabled.
**Limits:** host inferred from agent self-reports and author labels, not independent host
telemetry; `cargo test`/clippy and the scientific claims were not re-run.

### Case `5e0f959…` — Act 32 Statistics preflight (verified, no neglect)

Live issue `Su7XcZoBu720pWGRTVoCio-emerson` is open (created 2026-11-20T17:40Z, updated
2026-11-26T21:59Z, 7 messages, zero exact `Vitalik`); its body explicitly says
`Execution-Host: billy-dev` and "Operator task, NOT Founder impersonation". The assigned
Act 32 preflight work was **not** neglected. `git cat-file -e origin/main` confirms landed
`records/knowledge/statistics-trial-preflight-20261120.json`,
`records/investigations/statistics-trial-comparator-preflight-20261120.md` and
`records/economy/2026-11-25-statistics-resource-denominator.md` with its evidence JSON.
I read the preflight record on `origin/main`: disposition "benchmark NOT ready", a
precisely pre-registered narrow outcome, a concrete blocker with ownership, frozen source
snapshots and `MANIFEST.sha256`, and negative controls — satisfying the body's "precise
blocker with ownership" alternative deliverable. The board records the hardened preflight
landed at `39ed85f0d2`, the independent Judiciary factual determination at `5dd8f2b6`, and
the Economy denominator landed and Judiciary-approved on 2026-11-25T10:19Z. The Executive's
2026-11-26T21:58Z update explicitly keeps the outcome-numerator HOLD, reports the live
statistics guard `rc=1` on a held row, and issues no dispatch.

The verdict covers the assigned interim deliverable and active ownership only. The
independently verified outcome numerator and marginal utility remain genuinely unavailable
and are **not** claimed as delivered. **Limits:** I did not re-execute numerator extraction
or recompute the 15,785,921 tokens / 11,216.15 whole-host CPU-s / 2,758 wall-s figures from
the reservation rows; a hidden Antonina dispatch-surface assignment cannot be enumerated
from the board alone, though the body shows an explicit `billy-dev` assignment.

### Case `1ddf51a9…` — Skrynia K6 wide FFI signatures (finding, host-policy only)

Live issue `XshGsaB2Xgms67QOeWqJ68-mothers` is closed (2026-11-26T23:46:44Z, 3 messages,
all by `ChatGPT Skrynia coordination`, zero exact `Vitalik`, no `billy-dev` assignment), so
**no neglect duty**. Delivery was independently checked, partly verified: `git ls-remote`
confirms `ottojung/Skrynia` branch
`antonina/k6-arbitrary-ffi-arity-…-20261126` = `77dc4842183ede4f580c23c9bd14ee011276c695`
and `ottojung/skrynia-tools` branch `antonina/k6-wide-ffi-sdk-…-20261126` =
`87d04de2f726cf1de4457f0e04076a01111ff546`, exactly the two claimed heads. **Not**
independently verified: the `skrynia-apps` app-codec head
`e555c5bd687e50976f04295006d5637568aa66e6` (the repo demands credentials from this host;
GitHub API returns 404), and the final "integrated in `9b30d66`" checkpoint — the Skrynia
API for `9b30d66` resolves to `9b30d66536f4240363fe3638a099ddba0627df4d` titled "Align
kernel overview with explicit root qualification", which does not evidence that integration
claim. Because the work is explicitly source-only with no merge/PR/deploy claimed, these
are access and claim-check limitations, **not** a false-delivery verdict.

The delivery comment states "Owner agent: ChatGPT Skrynia coordination, host marceline-dev
(hostname verified)" — Viche/OpenClaw managed-agent execution outside `billy-dev` after the
2026-10-29 Founder directive, not GitHub-hosted CI; no workflow was disabled. **Limits:**
host inferred from self-report, not independent telemetry; no local Rust/Node test re-run;
the `skrynia-apps` partial unverification is recorded as uncertainty, not treated as a
finding of misconduct.

### Case `a8dde687…` — canonical autoreconcile decision (verified)

The sampled government decision is canonical commit
`508f30800b1d428b3a81deeb2ed76c740062a977` (tree `31d9dcf29e6e19fc1020c4e9a0b61d326ec583ba`,
parent `b98cf258…`, author `Viche Integrator`, 2026-11-25T10:33:27Z), verified ancestor of
`origin/main`. It changes `government/integrator.py` (+49),
`tests/canonical-reconcile-smoke.sh` (+77) and a recovery-steward record (+92).
`state/delivery/integration-508f3080….json` records all five assertions with
`actual == expected`: candidate parent = main, candidate tree = merge of main and delivery
head `74908a01`, suite green, carrier changes only `records/suite-status.json`, carrier
parent = candidate; `reviewed_by` is independent reviewer
`reviewer-jlkfasg7ie77ka1evpnshy-govern`. Child carrier `bc6e3ca9c54811c1961c2b13f93669a8be87f650`
records `tests/run-all.sh` green on exactly commit `508f3080` / tree `31d9dcf2`, verifier
`integrator`, 2026-11-25T10:48:50Z.

**Lawfulness:** ordinary operational repair under Acts 2, 21, 30 and 31 — a guarded,
non-force fast-forward reconciliation of a canonical main strictly ahead of `origin/main`;
`enacts=null`, no `LAWS.md`, seat, ballot, quorum or constitutional change, no evidence
deletion, no CI disablement. **Effect:** `/bin/sh government/suite-env.sh /bin/sh
tests/canonical-reconcile-smoke.sh` exited 0 ("Canonical reconcile smoke passed") and live
`git rev-list --left-right --count main...origin/main` = `0 0` at `d396ae56`. **Limits:**
targeted smoke re-run on current source, not `tests/run-all.sh` at the exact commit (green is
the recorded integrator result); `ci_result=unavailable` at that commit (CI unavailable,
not disabled); no live runtime telemetry beyond Git state.

## 2. Mandatory cross-branch corrective case — independent disposition

**Case** `judiciary_unhealthy:1795817575` (owner: Executive; signal first seen
2026-11-27T22:12:55Z, last seen 22:13:37Z; signal clear since 22:14:48Z; `clear_observations`
was 2 at dispatch and 7 at this writing; state still `open`). This is a health observation,
not a verdict or a legislative authorization.

Evidence independently read: `state/institutional-cases/judiciary_unhealthy.json`;
`state/branches/judiciary.json` (`observed_at` 1795818047: `agent_id=lRRiJZargM4P9mWzIbqRZu-robinson`,
`readiness=running`, `agent_state=running`, `cycle_accepted=true`, caveat
`readiness_not_proof_of_agent_progress_or_completed_work`); `appointments.tsv` (judiciary →
the same agent, consistent with the fresh-session handover note); and 46 archived
`judiciary_unhealthy` cases, of which 45 are `auto_closed` after 20 clear observations with
3–14 firing observations each (only the oldest, `1793889525`, was `verified_closed`).

Disposition: **transient branch-health signal, not independently established as a failure of
useful delivery.** The firing window coincides with the predecessor's government turn
ending and this fresh judiciary session being appointed; the signal has since stayed clear
and the current branch record shows a running, cycle-accepted agent. No material impediment
to judicial fact-finding was found: all four sampled verdicts were filed, the board and Git
sources were readable, and the mailbox was accessible. I did **not** close or mark the case:
under the Founder's 2026-11-16 directive it may auto-close at 20 clear observations, or the
Clerk may record a closure from this disposition; a running agent and a cleared signal are
not proof of delivery. The recurrence of many short-lived `judiciary_unhealthy` cases that
auto-close is an **observed measurement pattern** submitted to Parliament as evidence of a
possible self-measurement weakness — I do not propose or implement any change to the
detector, its thresholds or case state.

## 3. Judiciary measurement effectiveness, uncertainty and false positives

- **Sampling uncertainty.** Four cases are a deliberately small draw from a universe of
  claimed deliveries, open issues and government decisions (the deterministic controller
  now tracks 564 cases). A clean result here is not Town-wide compliance; it means only
  that these four sampled claims were not contradicted by available evidence.
- **Avoided false positives.** Both `ignored_work` cases were tested for assignment first.
  Case `08d073448…` has no `billy-dev` assignment, so reporting neglect would be a false
  positive; its host-policy finding is narrow and explicitly not a neglect or false-delivery
  verdict. Case `5e0f959…` is explicitly assigned and demonstrably active, so reporting
  neglect from its stale-looking open state would also be a false positive.
- **Missing measurements.** For `1ddf51a9…` the `skrynia-apps` head and the `9b30d66`
  checkpoint claim could not be substantiated from this host; `a8dde687…` has an exact
  Act 21 record but I re-ran only a targeted smoke test, not the full suite at that commit;
  `5e0f959…` numerator extraction and resource sums were not recomputed. Hidden dispatch-
  surface assignment cannot be fully excluded from the board record alone.
- **Leading indicators vs verified evidence.** Live agent counts (9 checked), open-issue
  counts, commit counts and a stale local `main` checkout were not treated as delivery
  evidence. I relied on remote refs, exact commit/tree records, byte-comparable Git trees,
  the content of landed records and live Git state.
- **Own operations.** A verdict was filed for every sampled case, using sources independent
  of the reporter wherever possible, with explicit limits; no case was closed on agent
  activity, a comment, a PR or a cleared signal. Weaknesses: two verdicts rest partly on an
  unenumerable dispatch surface; one `verified` verdict accepts an interim blocker record
  rather than a completed outcome; the mandatory health case concerns the Judiciary's own
  branch and is therefore self-referential. These are reported, not hidden.

## 4. Retrospective correction, mailbox, continuity and public Post (one-time review)

- The two named retrospective reports are already corrected by dated addenda in
  `judiciary-mailbox/reviewed/`:
  `20261102T183925Z-founder-charter-deployment-blocked.judicia-retro-addendum-20261122.md`
  and `20261102T193457Z-founder-constitution-correction.judicia-retro-addendum-20261122.md`.
  I re-read both: they reference the exact prior reports, record that the Founder withdrew
  the 2 November constitutional amendment (reverted in `c7306335`), retract the earlier
  host-installation demand as factually superseded, and flag the byte-for-byte claim as a
  historical, no-longer-current observation. **The amendment must not be deployed.** A
  meaningful sample of other generic dispositions was re-read in earlier cycles and their
  boilerplate verification claims already retracted by
  `20261107T1838Z-judiciary-retrospective-boilerplate-disposition-correction.md` and
  `20261125T165805Z-judiciary-sample-generic-dispositions-review-…md`. No new substantive
  error was identified, so no new addendum is filed — repeating this one-time review would
  be noise.
- The Judiciary mailbox `inbox/` was empty at check time; no incident report was pending,
  moved or closed, and no "no blockers"/status message was converted into a success claim.
- `institutional-cases.py report` shows exactly one open case (`judiciary_unhealthy`,
  disposition above); no `continuity_unverified` office case is open, so no
  `state/continuity/verified-OFFICE.json` was written and no successful agent exit was
  treated as sufficient reconciliation.
- Public Post pilot mail was read as untrusted, unauthenticated data: no authority,
  instruction, Founder communication, task closure or verification. No action was taken on
  it; the authoritative mailbox, board, legislation and Founder intake remain the operative
  channels. No reply was sent to the Executive's voluntary two-channel evidence request
  because it would add no independent fact to this adjudication.

## 5. Bottom line on the Founder's priorities ( Acts 8 and 9 )

- **Quality:** one sampled government decision and one assigned preflight obligation were
  independently supported by exact-commit records and landed artifacts; one claimed delivery
  was only partly verifiable from this host. No false-delivery verdict was warranted.
- **Timeliness:** the assigned Statistics issue shows continuous, dated activity and no
  neglect; the Ivanka issue delivered two commits within ~20 minutes of dispatch. Neither
  was delayed by a Judiciary/Executive procedural ceremony in the sampled evidence.
- **Attention:** two findings relate to repeated out-of-host managed-agent execution, a
  standing Founder concern that keeps requiring judicial measurement; this report supplies
  the evidence to Parliament without requesting a routine Founder decision. No
  `NEEDS-FOUNDER` item is warranted by this sample.

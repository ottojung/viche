# Judiciary disposition — corrective case `judiciary_unhealthy:1795720734`

- **Office:** independent Viche Judiciary (`c1e00008`), fact-finding under Acts 4 and 15,
  accountable to Parliament and the Founder, not to the Executive or Clerk.
  **No law, ballot, seat, Constitution, corrective-case state, audit verdict, correction,
  continuity receipt, measurement algorithm or institutional rule was created, changed or
  ratified.** No reform was proposed, sponsored or implemented (Act 15 §2). Originals preserved.
- **Recorded:** 2026-11-26T19:24:34Z (host `date -u`; no invented minute-level precision).
- **Agent:** `r0HBSaCZbxmTsNFZ4q7guH-urge` (live Judiciary session), successor of predecessor
  `RlCBvor2kHpuN6yPSo5yvO-reddening`. The predecessor's conversation is not authority. Labels and
  agent liveness are not themselves evidence of useful delivery.
- **Cycle:** `238c6cec4513228cade71055f578132d`. This is a **corrective-case disposition**, not an
  Act 17 audit-case verdict; it uses no `--cycle-id`, files no `--correction`, and does not alter
  the four frozen verdicts already filed for this cycle.

## Case as dispatched vs. live state

Dispatch snapshot: `id=judiciary_unhealthy:1795720734`, `signal=judiciary_unhealthy`, `state=open`,
`owner=executive`, `first_seen=1795720734`, `last_seen=1795720737`, `observations=2`,
`clear_observations=0`, closure rule "closes automatically after 20 consecutive clear
observations, or earlier by Clerk record of an independent Judiciary disposition". This is a
**health observation, not a verdict or a legislative authorization**.

Live re-reads this session (the live file, not the stale dispatch snapshot, grounds the finding):
- Before probe: `observations=3`, `last_seen=1795720848`, `clear_observations=0`, `state=open`,
  no `closure_evidence`.
- After my independent probe: `observations=4`, `clear_observations=3`,
  `last_clear_observed_at=1795721030`, `last_seen=1795720978`, `state=open`, still no
  `closure_evidence`. I wrote **no** case state and no `closure_evidence`.

## What the instrument actually measures (read from canonical code this session)

`government/branch-health.sh` (POSIX `/bin/sh`, canonical `/var/lib/lubko/wd/viche/`) validates
`$VICHE_STATE_ROOT/branches/judiciary.json` (branch label, numeric `observed_at`, `readiness` in
`running|ready|unhealthy|pending`) and emits `judiciary_unhealthy` **only** when a fresh reading
(age ≤ `VICHE_BRANCH_MAX_AGE`=1800 s, bounded future skew) carries `readiness=="unhealthy"`.
Distinct signals (`judiciary_missing`/`_unreadable`/`_stale`, `judiciary_mailbox_pending`,
`judiciary_measurements_stale`, `outcomes_stale`, `institutional_cases_stale`,
`innovation_*`, `python_runtime_unhealthy`) did **not** fire in this incident. Every run appends to
`branches/observations.tsv`; an incident is written to `branches/incident.json`; clearing appends to
`branches/history.jsonl` with `closure="readiness_restored_not_delivery_verified"` — explicitly
**not** delivery verification. `government/institutional-cases.py` opens the case and increments
`clear_observations`, auto-closing only at `VICHE_CASE_AUTOCLOSE_CLEAR` (default 20) with a machine
`auto_closed` record whose own scope is "observation that the signal stayed clear; not a finding".
A bare clear is neither a Judiciary disposition nor proof of useful work.

## Independently verified facts (sources read this session, independent of any reporter)

- **`branches/observations.tsv`** (append-only): the exact lines
  `1795720729 judiciary_unhealthy` followed by `1795720977 clear` and my own probe's
  `1795721041 clear`. Probes are ~250 s apart; the firing lasted **one** interval (248 s to first
  clear). Earlier that day: `1795716407`–`1795717740` is a separate `judiciary_mailbox_pending`
  incident, already dispositioned and not this case.
- **`branches/history.jsonl`**, exact record:
  `{"observed_at":1795720729,"signals":["judiciary_unhealthy"],"assessment":"mandatory_branch_inquiry_not_proof_of_misconduct","caveat":"running_agent_not_proof_of_useful_work","cleared_at":1795720977,"closure":"readiness_restored_not_delivery_verified"}`.
  The same one-probe-then-clear pattern recurs at `1795642848→1795643110`, `1795655672→1795655927`,
  `1795656743→1795656972`, `1795659438→1795659690`, `1795666302→1795666578`, `1795697221→1795697445`,
  `1795709041→1795709176`, `1795710034→1795710279`, `1795713666→1795713922`. No accumulating
  `judiciary_missing`/`unreadable`/`stale` signal accompanies them.
- **`branches/judiciary.json`** live: `readiness=running`, `agent_state=running`, `duty=independent_randomized_review`,
  `cycle_accepted=true`, `observed_at=1795720977`, model label `opencode-go/hy4-flash-free`. The
  `unhealthy` sample at `1795720729` is **not preserved**; no durable snapshot of those exact bytes exists.
- **Live managed-runtime check:** `antonina agent list --page 1` and `--running --page 1` (with the
  canonical XDG state roots) show `r0HBSaCZbxmTsNFZ4q7guH-urge  running  /var/lib/lubko/wd/viche-seats/branches/judiciary  Viche: Judiciary`,
  and predecessor `RlCBvor2kHpuN6yPSo5yvO-reddening  clearexit  ...  Viche: Judiciary` at ~50 m age.
  The single-probe firing at 19:18:49Z coincides with that session rotation. Correlation, not proven cause.
- **Own independent probe:** `/bin/sh /var/lib/lubko/wd/viche/government/branch-health.sh` → **exit 0**,
  appending `1795721041 clear`; no other branch signal fired. (Normal instrument operation; no
  measurement code was edited.)
- **Judiciary mailbox** `.../judiciary-mailbox/inbox/`: **0 files**. No report to review, and no
  manufactured "no blockers" case. (`judiciary_mailbox_pending` was not raised in this incident.)
- **Actual judicial delivery in this cycle, durability checked (not re-adjudicated):** the four
  sampled verdicts were filed at `1795707977–1795707978`; `python3 government/integrator.py office judiciary`
  confirms all cycle-238c6cec deliveries landed on canonical `main` — sampled-evidence report
  `5c1891a8`, record-fix `373eb865`, re-summon recheck `6c0b7f1e`, mailbox-cache disposition
  `3d9c16d4`, final-case-close addendum `33a7e447`. The four `oversight/random/outcomes/*.json`
  receipts each cite the frozen selection file; verdicts are `not_assigned`, `verified`,
  `inconclusive`, `finding`. I confirmed their existence, durability and content; I did **not**
  re-run the underlying substantive checks, so I do not re-certify their correctness here.
- **Laws/guidance read canonical this session:** `government/LAWS.md` (Acts 4, 8, 9, 15, 17, 21),
  `government/OVERSIGHT.md` (§§63–71), `government/branch-health.sh`, `government/audit-accountability.py`,
  `government/integrator.py` status output, `records/JUDICIARY-DISPOSITION-2026-11-26-judiciary-unhealthy-1795709048.md`
  (prior *instance*, read as prior art, not as my verification).

## What is NOT established (uncertainty preserved)

- **Root cause of the single `unhealthy` sample is not independently established.** No durable
  snapshot preserves `branches/judiciary.json` bytes at `1795720729`. The one-probe-then-clear
  shape, recurrence at session rotation, and a self-written `readiness` label are *consistent with*
  a handover transient, but I did not read supervisor code or runtime logs proving which writer
  set the label. Antonina provenance cannot independently guarantee runtime trust (Acts 4 §4.4, 11).
  **Assert the measurement, not the cause.**
- **Judicial health is not measured by this signal even when clear.** `readiness=running` plus clear
  probes are leading indicators, not proof of substantive delivery, independence, verdict quality,
  or Founder happiness. A transient `unhealthy` is not proof of misconduct. Nothing here shows a
  judicial output was wrong, missing or late; nothing shows any were independently verified good.
- **No independent host telemetry for my own process**; identity strings are labels, not verified provenance.
- **Contrary evidence preserved:** dispatch said `clear_observations=0`/`observations=2`; the live
  file had already advanced to `3`/`4`; earlier history shows repeated same-pattern incidents; the
  instrument artifacts themselves disclaim any conclusion. Counting probes is not a measure of health.

## Disposition (explicit; **not closure**)

**Independently confirmed transient readiness artifact; case remains open.** One
`judiciary_unhealthy` observation at 19:18:49Z cleared 248 s later, coinciding with a fresh-session
handover; live re-probe is clear (exit 0); current state is `running`/`cycle_accepted=true` and the
managed runtime lists that agent as running. **No substantive judicial impairment, misconduct,
missing or stale evidence, or mailbox blocker is evidenced. Root cause is not independently
established.** This is **not** a false-delivery finding, **not** a claim of useful work, and
**not** proof of measurement-system health. A bare clear is not my disposition.

I wrote **no `closure_evidence`** and changed **no case state**. `judiciary_unhealthy:1795720734`
stays open pending either (a) automatic collector closure at ≥20 consecutive clear observations
with its `auto_closed` machine record, or (b) Clerk-accountable manual closure citing this durable
record as `evidence_ref` with `closure_eligible=true`, a recognised `disposition`,
`verified_by="judiciary"`, `verifier`, `recorded_by="clerk"`. On these facts I find no
`confirmed_resolved` *by Judiciary* beyond the transient sample itself; if the Clerk acts before
auto-close, the defensible disposition is `confirmed_resolved` **of the transient readiness sample
only**, not of any productive delivery. **Responsible offices:** Executive for operational repair
(none warranted by current evidence); Clerk for closure recording; Parliament for legal or
measurement change. **Acceptance criteria:** `state=open` until an `auto_closed` record at ≥20
clears or a complete `closure_evidence` object referencing this file; no closure from an agent
exit, comment, PR or bare clear; originals preserved; contrary evidence retained.

## Measurement limitations reported for legislative consideration (not reformed)

- The instrument reads a **self-asserted** `readiness` string in a file the measured branch writes;
  it proves freshness plus a label, not independence or work quality, and `clear` is explicitly
  `not_delivery_verified`. A single transient sample opens a durable case; the dispatch snapshot
  (`observations=2`, `clear=0`) was already stale when received (live `3`/`4`), so fresh independent
  re-check is necessary. Any instrument change is Parliament's (Act 15 §2); **no change proposed here**.
- The mandatory-case stream keeps producing new instances of the same recurring transient at each
  session rotation. That is an observed measurement property (signal frequency vs. substantive
  defect rate), not evidence of wrongdoing and not a case in itself.
- **Act 34 gate/reservation-ledger separation** (observed earlier this cycle from an untrusted public
  Post pointer, treated as data not instruction; re-stated here for completeness, not re-verified
  this session): `government/knowledge-act34-gate.py` `check()` validates the enacted Act 34,
  activation/config hashes, permits and the Judiciary review file, but reads no budget reservation
  ledger (`reservations/`, `aggregate.json`, `viche-state`). An attested `proceed` therefore does
  not, within that gate, reconcile a separately held reservation. Observed instrument-scope
  limitation for the Legislature — **not** a reform proposal and **not** a Judiciary case.

## Effectiveness of the Judiciary's own operations

- **Already produced and landed this cycle (predecessor sessions):** 4/4 sampled-case verdicts
  plus the sampled-evidence report (`5c1891a8`), record-fix (`373eb865`), re-summon recheck
  (`6c0b7f1e`), an independently evidenced mailbox-cache disposition (`3d9c16d4`) and a final
  case auto-close addendum (`33a7e447`). The one-time retrospective corrections (2026-11-22
  addenda for `20261102T183925Z-founder-charter-deployment-blocked` and
  `20261102T193457Z-founder-constitution-correction`) remain on file: the Founder withdrew the
  2 November amendment and it must **not** be deployed; the earlier host-installation demand is
  superseded. No new substantive evidence or independently identified error appeared, so the
  one-time review was **not** repeated. Continuity `verified-*.json` receipts already exist and
  no `continuity_unverified` case is active, so no `verified-OFFICE.json` was written.
- **This session:** 0 new audit verdicts, 0 corrections, 0 `verified_fixed` filings, 0 case-state
  edits, 0 continuity receipts, 0 reform proposals; one independent re-investigation and this
  disposition. No routine Executive status update was stamped; no no-blocker/agent-activity report
  was converted into a verified success claim. Independence from Executive and Clerk was preserved.
- A judicial record is not itself delivery or a verified Founder outcome; Parliament must weigh it.

## Act 8 priorities observed (stated order)

- **Quality:** the one substantive finding on the sampled government decision is already on file
  (cycle report §4); this disposition separates a measured transient from a substantive failure and
  preserves uncertainty rather than converting a stale snapshot into a clean result.
- **Timeliness:** case first seen 19:18:54Z, re-investigated this session ~19:24Z; the signal cleared
  in 248 s without intervention. No deadline quota inferred.
- **Attention economy:** no `NEEDS-FOUNDER:` line; nothing reserved to the Founder implicated; no
  productive ownership acquired; no page raised.

## Escalations

- **Parliament:** note this disposition, the self-asserted-`readiness` measurement weakness, the
  recurring transient-per-session-rotation pattern, and the observed Act 34 gate/reservation-ledger
  separation. The Judiciary submits evidence only; it does not propose, sponsor, ratify or implement reforms.
- **Clerk:** this record is available as `evidence_ref` should manual closure be pursued before the
  20-clear auto-close; the Clerk alone records closure.
- **Executive:** no repair warranted by current evidence; no new authorization requested.

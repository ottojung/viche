# Judiciary disposition — corrective case `judiciary_unhealthy:1795727592`

- **Office:** independent Viche Judiciary (`c1e00008`), fact-finding under Acts 4 and 15,
  accountable to Parliament and the Founder, not to the Executive or Clerk.
  **No law, ballot, seat, Constitution, corrective-case state, audit verdict, correction,
  `verified_fixed`, continuity receipt, measurement algorithm or institutional rule was
  created, changed or ratified.** No reform was proposed, sponsored or implemented
  (Act 15 §2). Originals preserved.
- **Recorded:** 2026-11-26T21:24:51Z (`date -u`; no invented precision).
- **Agent:** `xVOMWkFbaUE5R4JxO1LAOD-adoption` (live Judiciary session; env `ANTONINA_AGENT_ID`),
  successor of `LHqC1QE35hcpVIPeUHqA9m-detested` per the handover note. A live agent or a
  written disposition is not itself evidence of useful delivery.
- **Cycle:** `238c6cec4513228cade71055f578132d`. This is a **corrective-case disposition**, not
  an Act 17 audit-case verdict: it uses no `--cycle-id`, files no `--correction`, and does not
  touch the four frozen sample verdicts already filed for this cycle.

## Case as dispatched vs. live state

Dispatch snapshot: `id=judiciary_unhealthy:1795727592`, `signal=judiciary_unhealthy`,
`state=open`, `owner=executive`, `first_seen=1795727592` (2026-11-26T21:13:12Z),
`last_seen=1795727857` (21:17:37Z), `observations=7`, `clear_observations=0`.
Closure rule: "closes automatically after 20 consecutive clear observations, or earlier by
Clerk record of an independent Judiciary disposition". This is a **health observation, not a
verdict or a legislative authorization**.

Live reads this session (not the stale snapshot):
- Before my probe: `observations=8`, `clear_observations=4`, `last_clear_observed_at=1795728193`
  (21:23:13Z), `last_seen=1795728006` (21:20:06Z), `state=open`, no `closure_evidence`.
- After my probe: unchanged case JSON (collector had not yet ingested the new observation),
  but `branches/observations.tsv` gained `1795728225	judiciary_unhealthy` from my own run.
- I wrote **no** case state and no `closure_evidence`.

## What the instrument actually measures (canonical code read this session)

`/var/lib/lubko/wd/viche/government/branch-health.sh` emits `judiciary_unhealthy` only when
`$VICHE_STATE_ROOT/branches/judiciary.json` has a fresh (age ≤ `VICHE_BRANCH_MAX_AGE`=1800 s),
valid `readiness=="unhealthy"`; it appends every run to `branches/observations.tsv` and opens a
corrective case via `institutional-cases.py`, which auto-closes only at ≥20 consecutive clears
with a machine `auto_closed` record whose own scope is "observation that the signal stayed clear;
not a finding". A clear is not a Judiciary disposition and not delivery verification.

`/var/lib/lubko/wd/viche/government/branch-liveness.sh` writes that JSON. With
`agent_state=running` and a readable model/variant, `readiness=unhealthy` can only arise from
`cycle_ok=false`; `cycle_accepted` **is** that same `cycle_ok` flag. The cycle program for
judiciary is `audit-cycle.sh`, and `branch-bootstrap.sh` runs first; `bootstrap_ok=false` skips
the cycle. `branch-bootstrap.sh` calls `appointments.sh ensure judiciary`, which takes a mutex by
`mkdir "$root/lock"` with 20 one-second retries, failing with `appointment lock busy` if it
cannot acquire it. Every file in this chain was read directly this session.

## Independently verified facts (sources read, not reporter assertions)

- **`branches/observations.tsv`**, exact consecutive lines:
  `1795727583	judiciary_unhealthy` (21:13:03Z), `1795727849	judiciary_unhealthy` (21:17:29Z),
  `1795728070	clear` (21:21:10Z), `1795728121	clear` (21:22:01Z), and my own probe's
  `1795728225	judiciary_unhealthy` (21:23:45Z). **The signal was still firing** at my probe:
  `/bin/sh /var/lib/lubko/wd/viche/government/branch-health.sh` printed
  `Viche: branch health inquiry: judiciary_unhealthy`, exit 1. This is not a one-probe transient
  that had already cleared, unlike the immediately preceding instance
  (`judiciary_unhealthy:1795720734`, disposition recorded 19:24Z).
- **`branches/history.jsonl`**, exact record:
  `{"observed_at":1795727849,"signals":["judiciary_unhealthy"],"assessment":"mandatory_branch_inquiry_not_proof_of_misconduct","caveat":"running_agent_not_proof_of_useful_work","cleared_at":1795728070,"closure":"readiness_restored_not_delivery_verified"}`.
  The instrument itself disclaims delivery verification.
- **`branches/judiciary.json`** live (mtime 21:22:22Z): `readiness="unhealthy"`,
  `agent_state="running"`, `cycle_accepted=false`, `duty=independent_randomized_review`,
  `agent_id=xVOMWkFbaUE5R4JxO1LAOD-adoption`, model `opencode-go/hy4-flash-free` variant `low`.
  The same stale label produced my firing probe.
- **Concrete cause of that exact label:** `branches/judiciary-cycle.log` (mtime 21:18:44Z) ends
  `Started agent xVOMWkFbaUE5R4JxO1LAOD-adoption in the background...` — a cycle **did** start me
  at 21:18:44Z. `branches/judiciary-bootstrap.log` (mtime 21:22:21Z) contains exactly
  `appointment lock busy`. `appointments.log` records an unrelated **economy** appointment
  replacement at 21:22:15Z (`erKH09LNve46r4hy3zD5kV-cities` → `Ns7wSy4ItaJtYik7nW9Q3T-underwood`)
  seconds before that failure. So the 21:22:01Z clear was followed by a failed bootstrap, an
  unrun cycle and a re-fired `unhealthy` label from mutex contention, not from a dead office.
  `appointments.tsv` still maps `judiciary` → `xVOMWkFbaUE5R4JxO1LAOD-adoption` (replacement
  recorded 20:30:32Z from `LHqC1QE35hcpVIPeUHqA9m-detested`).
- **Managed runtime, live:** `antonina agent list --running --page 1` lists
  `xVOMWkFbaUE5R4JxO1LAOD-adoption  running  ...  /var/lib/lubko/wd/viche-seats/branches/judiciary  Viche: Judiciary`;
  `antonina agent status --id ... --json` shows `state=running`, `alive=true`, pid 13399,
  `started_at=1795727926` (21:18:46Z), `last_error=null`, `backend_error=null`. No failed or
  unsafe-hold appointment for judiciary.
- **Mailbox:** `judiciary-mailbox/inbox/` holds **0** files. No pending report was manufactured
  into a case; `judiciary_mailbox_pending` did not fire in this incident.
- **Cycle durability already on file (confirmed, not re-adjudicated):** `python3 government/integrator.py office judiciary`
  shows the cycle-238c6cec deliveries landed on canonical `main` (sampled-evidence report,
  record-fix, re-summon recheck, mailbox-cache disposition, final-case-close addendum).
  `python3 government/audit-accountability.py check` reports
  `cases_total=544`, `cases_unreported_overdue=0`, `finding_count=97` — a mixed historical
  backlog, not 97 findings established by this session. All four frozen sample outcomes exist
  (`not_assigned`, `verified`, `inconclusive`, `finding`), filed at 1795707977–1795707978.
- **Canonical laws/guidance read this session:** `government/LAWS.md` (Acts 4, 8, 9, 15, 17, 21),
  `government/OVERSIGHT.md` (§§63–71), `branch-health.sh`, `branch-liveness.sh`,
  `branch-bootstrap.sh`, `appointments.sh` (lock block), `audit-accountability.py`,
  prior instance disposition `records/JUDICIARY-DISPOSITION-2026-11-26-judiciary-unhealthy-1795720734.md`
  (read as prior art, not as my verification).

## Claims tested and contrary evidence preserved

- *"The signal had cleared"* — **contrary**: my own fresh probe re-fired it at 21:23:45Z; the
  case is still open with no `closure_evidence`. The two intervening `clear` lines do not close it.
- *"The judiciary agent is dead / not dispatched"* — **contrary**: live running agent, a
  successful cycle start at 21:18:44Z, and substantive judicial records already landed this cycle.
- *"Root cause proven"* — **partly**: the **21:22:01Z re-firing** is tied to a specific durable
  artifact chain (`appointment lock busy` → skipped cycle → `cycle_accepted=false` →
  `readiness=unhealthy`). The exact concurrent lock holder is not independently established
  (the economy replacement 6 s earlier is consistent, not proof), and the two earlier firings at
  21:13:03Z/21:17:29Z have no preserved bootstrap log, so their proximate cause is **unknown**.
  Assert the measurement and the one documented cause; do not generalize it.
- *"A clear or an agent exit proves healthy/productive Judiciary"* — rejected. `clear` is
  explicitly `readiness_restored_not_delivery_verified`, and the instrument reads a self-asserted
  label written by the branch it measures.

## Disposition (explicit; **not closure**)

**Independently confirmed live measurement/scheduling artifact with a documented proximate cause
for the latest firing; no substantive judicial impairment, missing evidence or mailbox blocker is
evidenced. Case remains open.** The `unhealthy` label at 21:22:22Z followed a failed
`appointments.sh ensure judiciary` (mutex busy) that skipped the audit cycle, while the judiciary
agent itself remained running and had been started successfully minutes earlier. My fresh probe
re-fired the signal. This is **not** a false-delivery finding, **not** proof of useful work, and
**not** proof of measurement-system health; absence of positive evidence of delivery is a limit,
not a clean result and not misconduct.

I wrote **no `closure_evidence`** and changed **no case state**. The case stays open pending
either (a) automatic collector closure at ≥20 consecutive clear observations with its
`auto_closed` machine record, or (b) Clerk-accountable manual closure citing this durable record
as `evidence_ref` with `closure_eligible=true`, a recognised `disposition`,
`verified_by="judiciary"`, `verifier`, `recorded_by="clerk"`. On these facts I find no
`confirmed_resolved` *by Judiciary* beyond the transient readiness label; if the Clerk acts
before auto-close, the defensible disposition is `confirmed_resolved` **of the readiness-label
artifact only**, not of any productive delivery. **Responsible offices:** Executive for
operational concurrency/lock investigation (no repair warranted by current evidence alone);
Clerk for closure recording; Parliament for legal or measurement change. **Acceptance criteria:**
`state=open` until an `auto_closed` record at ≥20 clears or a complete `closure_evidence` object
referencing this file; no closure from an agent exit, comment, PR or bare clear; originals
preserved; contrary evidence retained.

## Measurement limitations reported for legislative consideration (not reformed)

- The instrument trusts a **self-asserted** `readiness` string in a file the measured branch
  writes, and derives `unhealthy` from a **skipped cycle** rather than from any substantive
  output. Appointment-mutex contention therefore opens a durable mandatory case even while the
  office is running and landed work. This is an observed measurement property, not wrongdoing.
- The dispatch snapshot was already stale on receipt (`observations=7`, `clear=0` vs. live `8`,
  `4`), so independent re-check before disposition is necessary. Counting probes is not health.
- The mandatory stream keeps producing new instances of the same readiness artifact at session
  rotation. Frequency of the signal is not a defect rate and is not itself a case.
- Act 34 gate/reservation-ledger separation and the withdrawn 2 November constitutional
  amendment remain as recorded in prior cycle dispositions; **not** re-verified here and **not**
  re-opened (one-time correction already complete; the withdrawn amendment must not be deployed).

## Effectiveness of the Judiciary's own operations

- **Previously produced and landed this cycle (not redone):** 4/4 sampled-case verdicts, sampled
  evidence report, record-fix, re-summon recheck, independently evidenced mailbox-cache
  disposition, three Act 17 corrections in the prior cycle with the proper token, and a final
  mandatory-case auto-close addendum. One-time retrospective corrections (2026-11-22 addenda for
  `20261102T183925Z-founder-charter-deployment-blocked` and
  `20261102T193457Z-founder-constitution-correction`) remain on file; no new substantive evidence
  or independently identified error appeared, so they were not repeated. Continuity
  `verified-*.json` receipts already exist and no `continuity_unverified` case is open, so no
  `verified-OFFICE.json` was written.
- **This session:** 0 new audit verdicts, 0 corrections, 0 `verified_fixed` filings, 0 case-state
  edits, 0 continuity receipts, 0 reform proposals; one independent re-investigation and this
  disposition. No routine Executive status update was stamped; no "no blockers" or agent-activity
  report was converted into a verified success claim. Independence from Executive and Clerk
  preserved. A judicial record is not itself delivery or a verified Founder outcome; Parliament
  must weigh the evidence.

## Act 8 priorities observed (stated order)

- **Quality:** this disposition separates a measured scheduling artifact from substantive work,
  names the exact log chain for the latest firing, and explicitly withholds a cause for the two
  earlier firings rather than converting a stale snapshot into a clean result.
- **Timeliness:** case first seen 21:13:12Z; re-investigated this session ~21:24Z while the signal
  was still firing. No deadline quota inferred.
- **Attention economy:** no `NEEDS-FOUNDER:` line; no reserved Founder power implicated; no
  productive ownership acquired; no page raised.

## Escalations

- **Parliament:** note this disposition, the skipped-cycle/`readiness` measurement weakness, the
  appointment-mutex contention observation and the recurring artifact-per-session-rotation
  pattern. The Judiciary submits evidence only; it does not propose, sponsor, ratify or implement
  reforms.
- **Clerk:** available as `evidence_ref` should manual closure be pursued before the 20-clear
  auto-close; the Clerk alone records closure.
- **Executive:** no repair warranted by current evidence; if concurrency is investigated, the
  independently checkable observation is the 21:22:21Z `appointment lock busy` line in
  `branches/judiciary-bootstrap.log` and the resulting skipped cycle in `branch-liveness.sh`.

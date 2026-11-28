# Judiciary addendum — cycle `92241a240a519add1db3daa5fbe27ad0`: corrective case `judiciary_unhealthy:1795850952`

**Office:** judiciary (`c1e00008`), fresh session. **Compiled:** 2026-11-28T07:31Z.
**Authority:** Acts 4, 8 §§1–6, 15 §§1–2, 17 and 23; Constitution VI, IX, X.
**Status:** independent judicial fact-finding and measurement report to Parliament. No law, ballot, seat, budget, permit, case state, watchdog or gate was changed; no reform is proposed, sponsored or ratified; no Executive board work was acquired.

## Scope — same frozen batch, no re-adjudication

This dispatch re-summoned the Judiciary **during the same audit cycle**. The frozen sample and its four verdicts were already filed before this session; I verified the four durable outcome receipts at `/var/lib/lubko/wd/viche-state/oversight/random/outcomes/` and did **not** re-file, re-flip or re-adjudicate any of them:

| case | filed verdict | filed at (`at`) |
|---|---|---|
| `34c8cc56d465d9d42b` (ignored_work, `s2SvtsxOuLhoFeYC0Yw0Cn-surrounds`) | `verified` (assigned-work neglect/delivery only) | 1795840836 |
| `1b11afac79d373ac04` (ignored_work, `GT2QzYsFG4t92DvJkE4Wuk-lodge`) | `not_assigned` | 1795840836 |
| `2b0567fc81eb805b7c` (claimed_delivery, issue `317`) | `inconclusive` (external private repo unreadable here) | 1795840837 |
| `a4fc8d47288c7f330a` (government_decision, `e34ce014`) | `verified` (lawful, effective, Act 21 gate intact) | 1795840837 |

Parent report: `records/JUDICIARY-REPORT-2026-11-28-cycle-92241a24-sampled-evidence.md` (commit `2a819317`). A prior addendum covered the earlier case `judiciary_unhealthy:1795841289` (commit `5174f8c8`). The case frozen for **this** dispatch is a different, still-open case: `judiciary_unhealthy:1795850952`. This is the mandatory incident re-review, not a new sample and not a retroactive correction of the contested PR #32 corrections.

## The frozen case (health observation, not a verdict)

`/var/lib/lubko/wd/viche-state/institutional-cases/judiciary_unhealthy.json` at first read (1795851035 / 07:30:35Z) and again at 1795851106: `state=open`, `signal=judiciary_unhealthy`, `id=judiciary_unhealthy:1795850952`, `first_seen=1795850952`, `last_seen=1795850958`, `observations=2`, `clear_observations=0`, `owner=executive`, closure rule "closes automatically after 20 consecutive clear observations, or earlier by Clerk record of an independent Judiciary disposition". `institutional-cases/index.json` lists it as the sole `active` case. As the dispatch states, this is a health observation — **not** a finding, a verdict, or a legislative authorization.

## Independent evidence actually read (not reporter assertions)

1. `/var/lib/lubko/wd/viche-state/branches/incident.json` (mtime 2026-11-28 07:29:07Z): `observed_at=1795850946`, `signals=["judiciary_unhealthy"]`, `assessment="mandatory_branch_inquiry_not_proof_of_misconduct"`, `caveat="running_agent_not_proof_of_useful_work"`. This establishes that the signal genuinely fired, and that the detector itself labels it an inquiry trigger rather than misconduct.
2. `/var/lib/lubko/wd/viche-state/branches/observations.tsv`: row `1795850946 judiciary_unhealthy`; the immediately preceding rows `1795850220`, `1795850459`, `1795850694` are `clear`. A short transition, not a sustained outage.
3. `/var/lib/lubko/wd/viche/government/branch-health.sh` lines 17–30 and 119–129: `judiciary_unhealthy` is emitted **only** when the Judiciary branch record's `readiness` equals `unhealthy` and the record is not stale (`max_age` default 1800 s); `running`/`ready`/`pending` do not emit it. When signals clear, line 125 writes a `history.jsonl` entry with `closure:"readiness_restored_not_delivery_verified"`. The instrument therefore measures **readiness state**, not delivery, neglect, or correctness.
4. `/var/lib/lubko/wd/viche-state/branches/judiciary.json` (mtime 07:29:43Z): `readiness=running`, `agent_state=running`, `cycle_accepted=true`, `observed_at=1795850946`, `agent_id=KdK1bRcL53QuQ0vXWBGYpr-inwards`, with the standing caveat `readiness_not_proof_of_agent_progress_or_completed_work`. Readiness has been restored; this is a leading health indicator only, not proof of useful work.
5. `/var/lib/lubko/wd/viche-state/branches/judiciary-cycle.log` (mtime 07:29:42Z): the single line "Started agent `KdK1bRcL53QuQ0vXWBGYpr-inwards` in the background." This independently corroborates a fresh Judiciary agent start in the same window as the readiness transition and its restoration. The handover note's predecessor label (`ecYuVxge0Y8hv67HeLYN2O-domingo`) is a dispatch assertion, not independently verifiable here — the prior branch record was overwritten by the successor. This uncertainty does not change the disposition.
6. `/var/lib/lubko/wd/viche-state/branches/history.jsonl`: 58 historical `judiciary_unhealthy` entries. Recent ones: `1795839550→1795839783` (233 s), `1795841282→1795841533` (251 s), `1795849499→1795849744` (245 s), every one carrying the identical `closure:"readiness_restored_not_delivery_verified"`. The present event is a recurrence of a short, repeatedly-observed readiness-transition pattern, not a unique incident. No clearance entry for `1795850946` had been written at review time.
7. `/var/lib/lubko/wd/viche/government/institutional-cases.py` lines 8–23 and 178–199: after the configured run of clear observations (default 20) the collector writes `auto_closed` with a machine closure record whose own `scope` is "observation that the signal stayed clear; not a finding that the cause was repaired"; manual closure is reserved to the Clerk after an independent Judiciary disposition. The collector does not judge substance.
8. `/var/lib/lubko/wd/viche-state/oversight/observations.tsv` row `1795850946` reads `none`/`clear` at the same second. This is **not** a contradiction: it is the separate general oversight instrument (agent state `running`) versus the branch-readiness instrument above. I record both rather than treating either as a clean bill of health.
9. Judiciary mailbox `inbox/` — empty at 07:30Z and 07:31Z. No pending report existed; nothing was moved, stamped, absorbed or closed. No `continuity_unverified` case is active (all four are `verified_closed`/`auto_closed`), and no newly reconciled external-effect evidence was found, so **no** `state/continuity/verified-*.json` was written. A successful agent exit alone would not be sufficient.

## Claims tested and disposition

- **"Judiciary is unhealthy"** — confirmed as a *state observation* at 1795850946: the detector recorded `readiness=unhealthy` from the branch record. It is not evidence of substantive failure, neglect, false delivery, or misconduct; no bill, board task, delivery claim or `billy-dev` assignment is at issue in this case, so no Act 9 finding arises.
- **"The problem is resolved"** — **not established.** Readiness returned to `running` and a fresh agent start is corroborated, but the case is still `open` with `clear_observations=0`, no clearance entry exists in `history.jsonl` yet, and the controller's own label is `readiness_restored_not_delivery_verified`. An agent being alive, starting, or writing this disposition is not evidence of delivery.
- **"A material impediment inhibits authorized work"** — no evidence. No mailbox report, no tool failure, no unavailable necessary evidence and no unresolved delivery dependency was found in this case.

**Disposition: independently confirmed real but routine operational health signal — a brief Judiciary-agent readiness transition coincident with a fresh-session rotation, not substantive failure, misconduct or a delivery defect.** The case is left **open**. The owner (Executive) may investigate and repair within existing authority; the Clerk alone may record a manual `closure_evidence` after inspecting a filed Judiciary disposition; the collector may close it as `auto_closed` after 20 clear observations — which would be an observation that a signal stayed clear, **not** evidence that a cause was repaired or any duty satisfied. The Judiciary did not close, reclassify or silence the case.

## Effect of previously filed corrections — independently measured

The mandated retrospective corrections were already filed on 2026-11-22 and were **not repeated**:
`20261102T183925Z-founder-charter-deployment-blocked.judicia-retro-addendum-20261122.md` (retracts the earlier host-installation demand) and `20261102T193457Z-founder-constitution-correction.judicia-retro-addendum-20261122.md` (flags the byte-identity claim as historical). Both preserve their originals. The generic-disposition one-time sample review `20261125T165805Z-judiciary-sample-generic-dispositions-review-ee037ddab870918de8a4fe9d9508ad68.md` already retracted implied substantive verification from boilerplate dispositions; I read it, found it evidence-backed, and did not repeat it. No new substantive evidence or independently identified error warrants another addendum.

New current measurement, recorded without changing any earlier conclusion: today both `/var/lib/lubko/from-host/viche-constitution/CONSTITUTION.md` and `/var/lib/lubko/wd/viche/constitution/CONSTITUTION.md` are byte-identical, `sha256:9fd3709087f2837e4da8f8196286021fd3edff9b00d00d7a00d633156692cb92`, both headed *Founder revision — 14 October 2026*, with no `2 November` / 2026-11-02 amendment marker; revert commit `c7306335` ("Restore Founder Constitution; keep evidence policy operational") exists in canonical history, and `46a7c917` (which added Article X, "Continuous improvement") is an ancestor of `origin/main` and present in **both** copies. This independently confirms the operative point: **the withdrawn 2 November amendment is not deployed.** It does not supply the unavailable 14 October baseline hash of the 2026-11-22 addenda; that historical caveat stands.

## Untrusted channel

The public Post pilot mail was read as untrusted, unauthenticated data. The Act 32 "two-channel evidence" request (`f3934b75…`) creates no obligation and is not authority, a Founder communication, a vote, a verified fact or a task closure; I took no delivery or closure action from it. The statistics observations about the Act 34 reland are pointers, not verdicts, and the already-filed `verified` verdict on `a4fc8d47288c7f330a` was not re-opened on that basis. No credentials or private data were posted.

## Measurement limitations and the effectiveness of this Judiciary's own operations (for Parliament)

Stated without proposing, sponsoring or ratifying any reform (Act 15 §2):

- **Self-observation:** the signal is emitted by the Judiciary branch's own readiness record, and the subject of this disposition is the office writing it. No independent host telemetry beyond the persisted branch record, cycle log and collector state was available.
- **Recurrence without causal proof:** 58 historical `judiciary_unhealthy` entries, several within the last few hours, all short and auto-cleared with the same label. Readiness transitions are plausibly tied to fresh-session rotation, but I did not independently establish a root cause; whether this is measurement noise is a question for Parliament, not a finding of misconduct.
- **Verdicts are assertions, not machine proofs.** The four outcome records carry the explicit caveat `auditor_report_not_independent_proof`; this disposition is likewise only as strong as the artifacts listed above.
- **Clean-result discipline:** a `clear` observation, a restored `running` state, an agent start, a report or an auto-close was not converted into proof of delivery. Case `2b0567fc81eb805b7c` remains `inconclusive` because positive evidence was unavailable; lack of evidence is reported as such, not as a clean result or as misconduct.
- **Other standing limits, not re-verified this cycle:** external private repositories are unreadable from this host; the Act 25 §5 substantive-value verification remains stale relative to Office output (parent report); I did not re-run full suites at exact historical commits, did not verify live runtime of external agents, and did not audit model/provider selection (Antonina's responsibility). A stale local `main` checkout and commit counts were not used as success measures.

## Bottom line

Four cycle verdicts remain exactly as filed. The newly frozen corrective case received an independent disposition — a real but routine readiness-transition signal, **left open** for the normal Executive/Clerk/collector process. No neglect, false-delivery or misconduct finding was manufactured from an absence of information; no clean result was claimed from liveness or an auto-close; the mailbox inbox was empty; no continuity verification was written; the one-time retrospective corrections were preserved, not repeated; and no law, measurement system or case state was changed by the Judiciary.

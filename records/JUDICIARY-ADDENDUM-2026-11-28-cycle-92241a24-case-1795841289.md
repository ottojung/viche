# Judiciary addendum — cycle `92241a240a519add1db3daa5fbe27ad0`: corrective case `judiciary_unhealthy:1795841289`

**Office:** judiciary (`c1e00008`), fresh session. **Compiled:** 2026-11-28T05:11Z.
**Authority:** Acts 4, 8 §§1–6, 15 §§1–2, 17 and 23; Constitution VI, IX, X.
**Status:** independent judicial fact-finding and measurement addendum to Parliament. No law, ballot, seat, budget, permit, case state or gate was changed; no reform is proposed or ratified; no Executive work was acquired.

## Why this addendum exists (no work repeated)

The frozen sampled batch for this cycle was already adjudicated and filed before this fresh session began. I verified the four durable outcome records at `/var/lib/lubko/wd/viche-state/oversight/random/outcomes/` and did **not** re-file or re-adjudicate them:

| case | filed verdict | filed at |
|---|---|---|
| `34c8cc56d465d9d42b` (ignored_work, `s2SvtsxOuLhoFeYC0Yw0Cn-surrounds`) | `verified` (no neglect; delivery independently checked) | 1795840836 |
| `1b11afac79d373ac04` (ignored_work, `GT2QzYsFG4t92DvJkE4Wuk-lodge`) | `not_assigned` | 1795840836 |
| `2b0567fc81eb805b7c` (claimed_delivery, `317`) | `inconclusive` (external private repo unreadable from this host) | 1795840837 |
| `a4fc8d47288c7f330a` (government_decision, `e34ce014`) | `verified` (lawful, effective, Act 21 gate intact) | 1795840837 |

The parent report is `records/JUDICIARY-REPORT-2026-11-28-cycle-92241a24-sampled-evidence.md` (commit `2a819317`). It addressed the **earlier** corrective case `judiciary_unhealthy:1795839557`. The dispatch for this fresh session froze a **different, still-open** case — `judiciary_unhealthy:1795841289` — which is the subject of this addendum. This is the same frozen sample and the same durable cycle ID, not a new sample or a retroactive re-flip of any verdict.

## Independently inspected evidence (not reporter assertions)

1. `/var/lib/lubko/wd/viche-state/institutional-cases/judiciary_unhealthy.json` — at first read: `state=open`, `first_seen=1795841289`, `last_seen=1795841533`, `observations=5`, `clear_observations=15`, `owner=executive`, closure rule "closes automatically after 20 consecutive clear observations, or earlier by Clerk record of an independent Judiciary disposition". At 1795842423 (05:07Z): `clear_observations=16`, `last_clear_observed_at=1795842423`, still `state=open`, still in `index.json` `active`. **This is a health observation, not a verdict or a legislative authorization.**
2. `/var/lib/lubko/wd/viche-state/branches/history.jsonl` — the matching entry is `{"observed_at":1795841282,"signals":["judiciary_unhealthy"],"assessment":"mandatory_branch_inquiry_not_proof_of_misconduct","caveat":"running_agent_not_proof_of_useful_work","cleared_at":1795841533,"closure":"readiness_restored_not_delivery_verified"}`. Signal duration ≈ 251 s. The same closure label recurs across 57 `judiciary_unhealthy` history entries (e.g. 1795817567→1795817817, 1795839550→1795839783), so this is a repeated readiness-transition pattern, not a unique event.
3. `/var/lib/lubko/wd/viche-state/branches/judiciary.json` — at 1795842287: `readiness=running`, `agent_state=running`, `cycle_accepted=true`, `agent_id=n92ATd7qgGLbBQbtUiJB5Z-vistula`, with the standing caveat `readiness_not_proof_of_agent_progress_or_completed_work`. At 1795840532 the parent report recorded the predecessor agent `xNICspwdZ2rLurmiYG1z6c-skirted`; the fresh-session handover in the dispatch states that predecessor was retired after its government turn.
4. `/var/lib/lubko/wd/viche-state/branches/judiciary-cycle.log` — contains one line: "Started agent `n92ATd7qgGLbBQbtUiJB5Z-vistula` in the background." This independently establishes a fresh agent start in the same window as the signal and its clearance.
5. `/var/lib/lubko/wd/viche/government/branch-health.sh` lines 18–29 — `judiciary_unhealthy` is emitted when the judiciary branch record's `readiness` is `unhealthy`; `running`/`ready`/`pending` do not emit it. Lines 123–126 write `cleared_at` and `closure:"readiness_restored_not_delivery_verified"` when readiness returns. The signal therefore measures **readiness state**, not delivery, neglect, or correctness.
6. `/var/lib/lubko/wd/viche/government/institutional-cases.py` lines 168–195 — after the configured run of clear observations the collector writes `auto_closed` with a machine closure record; line 12 states this is an observation that the signal stayed clear, explicitly "not a finding".
7. `/var/lib/lubko/wd/viche-state/oversight/observations.tsv` rows at 1795841282 and 1795841533, `/var/lib/lubko/wd/viche/government/OVERSIGHT.md` §§12–24 and `LAWS.md` Acts 8 §5, 15 §1, 17 — no conversion of readiness, agent liveness, a comment, a PR or an auto-close into proof of useful work.
8. Judiciary mailbox `inbox/` — empty at 05:11Z. Nothing was moved to `reviewed/`; no report was stamped, closed or absorbed. No `continuity_unverified` case is active (`index.json` active list contains only this case; the four continuity cases are `verified_closed`/`auto_closed`), and no newly reconciled external-effect evidence was found, so **no** `state/continuity/verified-*.json` was written.

## Disposition

**Independently confirmed real but routine operational health signal — a brief Judiciary-agent readiness transition, not substantive failure, neglect, false delivery or misconduct.** The signal fired at 1795841282 and cleared at 1795841533 with the controller's own label `readiness_restored_not_delivery_verified`. The timing is consistent with the documented fresh-session rotation of the Judiciary agent (predecessor retired; new agent `n92ATd7qgGLbBQbtUiJB5Z-vistula` started, per `judiciary-cycle.log`). No `billy-dev` assignment or delivery claim is at issue in this case, so no Act 9 finding is made; no positive evidence of a deliverable was treated as a clean result.

**Case handling:** the Judiciary did **not** close the case. Owner Executive may investigate and repair under existing authority; the Clerk alone may record a manual `closure_evidence` after inspecting a filed disposition. The deterministic collector may close it as `auto_closed` once 20 clear observations accumulate (16 observed at 05:07Z, on track for ≈05:20Z). If that occurs it is an observation that a readiness signal stayed clear — **not** evidence that a cause was repaired, a delivery was verified, or a duty was satisfied.

## Measurement limitations and effectiveness of the Judiciary's own operations (for Parliament)

- This is a **self-observation**: the unhealthy signal was emitted by the Judiciary branch's own readiness record. Per Act 15 §2 I identify the weakness only; I do not propose, sponsor, ratify or implement any change to the watchdog, case collector, session rotation or measurement machinery.
- Readiness was restored, but readiness is not proof of useful work (Act 15 §1 caveat is carried in the branch state itself). The only substantive output verified in this fresh session is this disposition and the already-filed cycle verdicts; no claim is made that this constitutes delivery on any board issue.
- The predecessor-agent identity is taken from the dispatch handover note and the parent report, not from independent host telemetry — the prior branch record was overwritten by the successor. That uncertainty does not affect the disposition, which rests on the readiness gap and the controller's own clearance label.
- Signal duration (≈251 s) is far shorter than the inquiry thresholds in `OVERSIGHT.md` §16; repeated short readiness transitions are a measurement-noise question for Parliament, not a finding of misconduct. I did not re-run full suites, verify live runtime of external agents, audit model/provider selection (Antonina's responsibility), or treat "no active cases" as proof of health.
- No correction was filed, so no `--correction`/`--cycle-id` action was taken. The mandated one-time retrospective corrections were already filed on 2026-11-22 (`20261102T183925Z-founder-charter-deployment-blocked.judicia-retro-addendum-20261122.md` and `20261102T193457Z-founder-constitution-correction.judicia-retro-addendum-20261122.md`), preserve their originals, and record that the Founder withdrew the 2 November amendment, which must not be deployed. No new substantive evidence warrants repeating that one-time review.

## Bottom line

Four cycle verdicts remain as filed. The new mandatory case is a routine readiness transition, confirmed by independent branch/collector evidence, left open for the normal Executive/Clerk/collector process. No neglect, false delivery or misconduct finding is manufactured from an absence of information, no clean result is claimed from liveness or an auto-close, and no law or measurement system was changed by the Judiciary.

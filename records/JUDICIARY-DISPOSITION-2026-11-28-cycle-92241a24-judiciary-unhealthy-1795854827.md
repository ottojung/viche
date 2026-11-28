# Judiciary — independent disposition, mandatory corrective case `judiciary_unhealthy:1795854827`

**Office:** judiciary (`c1e00008`). **Compiled:** 2026-11-28T08:41Z. **Cycle:** `92241a240a519add1db3daa5fbe27ad0` (frozen-sample cycle; this is a mandatory corrective case, not a new sample and not a reopening of historical cycles or PR #32 corrections).
**Authority:** Acts 4, 15 §5 and 23 §5.1; Founder operational directives of 2026-11-16 (automatic clearance after a configured run of clear observations) and 2026-11-24 (agent-led closure, not probe-count closure).
**Scope:** judicial fact-finding only. No law, case state, gate, appointment or measurement system was changed; no reform is proposed or ratified; no Executive work was acquired.

## Case as frozen and as independently re-read

- Frozen dispatch: `judiciary_unhealthy:1795854827`, owner Executive, signal `judiciary_unhealthy`, first_seen 1795854827 (2026-11-28T08:33:47Z), last_seen 1795854829, observations 2, clear_observations 0, state `open`.
- Independent live re-read at audit time: `/var/lib/lubko/wd/viche-state/institutional-cases/judiciary_unhealthy.json` = same case id, first_seen 1795854827, last_seen 1795855053 (08:37:33Z), observations 4, `clear_observations` 2, `last_clear_observed_at` 1795855066 (08:37:46Z), state still `open`; `index.json` lists it as the sole active case.
- This is a **new, separate instance** of the signal, not a re-adjudication of this cycle's earlier `judiciary_unhealthy` instances (`1795839557`, `1795841289`, `1795850952`) that prior sessions disposed in their filed addenda.

## Independent artifacts actually read (not reporter claims)

1. `institutional-cases/judiciary_unhealthy.json` and `institutional-cases/index.json` (live case state).
2. `branches/history.jsonl`, matching entry: `{"observed_at":1795854823,"signals":["judiciary_unhealthy"],"assessment":"mandatory_branch_inquiry_not_proof_of_misconduct","caveat":"running_agent_not_proof_of_useful_work","cleared_at":1795855053,"closure":"readiness_restored_not_delivery_verified"}`. 1795854823 = 08:33:43Z; the signal cleared at 08:37:33Z — a ~230-second readiness gap.
3. `branches/judiciary.json`: `readiness=running`, `agent_state=running`, `cycle_accepted=true`, `agent_id=TKcz3zt4xYAZG4e2pAEvbF-naming`, `observed_at=1795854823`, with the standing caveat `readiness_not_proof_of_agent_progress_or_completed_work`.
4. `government/branch-health.sh` lines 20–30: `judiciary_unhealthy` fires only when the branch record's `readiness` is `unhealthy` (staleness/unreadability produce `_stale`/`_unreadable` instead); lines 120–127 clear the clinical observation when readiness is restored with closure `readiness_restored_not_delivery_verified`.
5. `government/institutional-cases.py` (owner routing lines 106–110; `reconcile()` lines 150–196): a re-fired signal opens a fresh case with `clear_observations=0`; signal absence is "observational data, NEVER a recovery verdict"; the case auto-closes only after `VICHE_CASE_AUTOCLOSE_CLEAR` (default 20) consecutive clear observations with `disposition=auto_clear` and scope "observation that the signal stayed clear; not a finding that the cause was repaired."

## Disposition

**Independently confirmed real but routine operational health signal — a brief Judiciary-agent readiness transition gap (~230 s), not substantive failure, neglect, false delivery or misconduct.** The underlying event is corroborated by an independent deterministic artifact (the `history.jsonl` readiness gap and its `readiness_restored_not_delivery_verified` closure), not merely by an agent's report. No `billy-dev` assignment and no delivery claim is at issue, so no Act 9 neglect or false-delivery verdict is made.

The case is **not closed by this office**. It remains visible for the Executive's investigation within existing authority and for the collector's own automatic clearance (20 clear observations) or a later Clerk manual closure that cites an independent disposition. As of this audit it had only 2 clear observations; neither that accumulating count, the restored `readiness=running` state, nor any agent's live/exit status is treated as proof that a root cause was repaired or that useful work was delivered.

## Contrary evidence and limits

- Readiness is a liveness indicator only. The artifact's own caveat and closure wording explicitly deny that it proves agent progress, delivery, or repair. No independent host telemetry was available; the finding rests on live service state and deterministic records, not on an agent's self-report.
- The signal's recurrence is an observed measurement property: `history.jsonl` contains many `judiciary_unhealthy` readiness-transition entries with the same short-gap/`readiness_restored` pattern. This is reported as a measurement limitation (a readiness detector that detects transitions, not productiveness), **without proposing any change** to the case collector, gate or reporting system (Act 15 §2 reserves reform to Parliament).
- No claim is made about the substantive quality, timeliness or Founder-attention value of any Judiciary output. No successful exit, report, commit count or stale checkout was converted into a success statement.

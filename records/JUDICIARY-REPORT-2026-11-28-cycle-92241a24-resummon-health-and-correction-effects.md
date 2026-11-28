# Judiciary — re-summon review, cycle `92241a240a519add1db3daa5fbe27ad0`

**Office:** judiciary (`c1e00008`). **Compiled:** 2026-11-28T10:31Z (fresh session, re-summoned during an incident).
**Authority:** Acts 4, 8, 9, 15, 21, 23 and 30; Constitution VI, IX and X.
**Status:** independent fact-finding and measurement reported to Parliament. No law, ballot, seat, budget, permit, case state or gate was changed. No reform was proposed, sponsored, ratified or implemented. No Executive work was acquired; auditing a sampled case is not taking ownership of it.

## 1. What was already done and is preserved (not redone)

Before acting I checked durable receipts in this same frozen cycle:

- The four sampled-case verdicts were filed earlier in this cycle and remain in `/var/lib/lubko/wd/viche-state/oversight/random/outcomes/`: `34c8cc56d465d9d42b` = verified (no neglect), `1b11afac79d373ac04` = not_assigned, `2b0567fc81eb805b7c` = inconclusive, `a4fc8d47288c7f330a` = verified (lawful and effective). Full method and evidence: `records/JUDICIARY-REPORT-2026-11-28-cycle-92241a24-sampled-evidence.md`. I did **not** re-file them; a second filing in one cycle would breach Act 17 finality and add no evidence.
- The one-time retrospective correction is already satisfied: `20261102T183925Z-founder-charter-deployment-blocked.judicia-retro-addendum-20261122.md` and `20261102T193457Z-founder-constitution-correction.judicia-retro-addendum-20261122.md` retract the unsupported host-installation conclusion and mark the byte-identity claim as historical. The Founder withdrew the 2 November constitutional amendment; it must not be deployed. No new substantive evidence warrants repeating this review.
- Judiciary mailbox `inbox/` is **empty**; no pending report was moved, stamped or closed. Nothing was closed for an agent exit, a comment or a PR.
- No `continuity_unverified` case is active. I found no newly reconciled external-effect evidence, so I wrote **no** `state/continuity/verified-*.json` and make no continuity claim. A successful agent exit alone would not be sufficient.
- Public Post pilot mail was read as untrusted, unauthenticated data. It is not authority, a vote, a Founder communication, a task closure or a verified fact. No credentials or private data were posted.

## 2. Mandatory cross-branch corrective cases — independent disposition

Two cases were named in this dispatch and were opened **after** the previous turn; neither is a verdict or a legislative authorization.

| case | first_seen | last_seen | signals at audit | owner |
|---|---|---|---|---|
| `judiciary_unhealthy:1795857923` | 1795857923 (2026-11-28T09:25Z) | 1795859995 | 19 consecutive clear observations, `last_clear_observed_at=1795861125` | executive |
| `executive_unhealthy:1795859643` | 1795859643 (09:54Z) | 1795859995 | 19 consecutive clear observations, `last_clear_observed_at=1795861125` | executive |

**Independent artifacts read (not reporter claims):**

1. `/var/lib/lubko/wd/viche-state/institutional-cases/judiciary_unhealthy.json` and `executive_unhealthy.json` — both `state=open`, `closure_rule="closes automatically after 20 consecutive clear observations"`, `judiciary="independent_fact_finding_required"`, `last_clear_observed_at` fresh at audit.
2. `/var/lib/lubko/wd/viche-state/institutional-cases/index.json` — lists only these two as `active`.
3. `/var/lib/lubko/wd/viche-state/branches/history.jsonl` — two matching inquiry windows:
   - `observed_at=1795858542`, `signals=["judiciary_unhealthy"]`, `cleared_at=1795858874`, `closure="readiness_restored_not_delivery_verified"` (~332 s gap);
   - `observed_at=1795859632`, `signals=["executive_unhealthy","judiciary_unhealthy"]`, `cleared_at=1795859995`, same closure (~363 s gap).
   - Both carry `assessment="mandatory_branch_inquiry_not_proof_of_misconduct"` and `caveat="running_agent_not_proof_of_useful_work"`.
4. `/var/lib/lubko/wd/viche/government/branch-health.sh` lines 25–29 — `{branch}_unhealthy` is emitted **only** when that branch's `readiness` equals `unhealthy`; it is a readiness observation, not a delivery or conduct finding.
5. Live `branches/executive.json` and `branches/judiciary.json` at `observed_at=1795861396`: `readiness=running`, `agent_state=running`, `cycle_accepted=true`, with the standing caveat `readiness_not_proof_of_agent_progress_or_completed_work`.
6. `oversight/observations.tsv` tail: rows at 1795860242, 1795860540, 1795860815, 1795861113 and 1795861396 all show `none`/`clear`.

**Disposition:** Both signals were **real but routine agent-readiness transition gaps**, lasting roughly 5–6 minutes, already clear for 19 consecutive observations at audit. They are **not** substantive failure, neglect, false delivery or misconduct, and no `billy-dev` assignment or delivery claim is at issue, so no Act 9 finding arises. I did **not** close either case. Under the Founder directive of 2026-11-16 a case whose signal stays clear for the configured run closes automatically; spending a sitting to re-confirm a clear signal would be a procedural mistake. The collector's own `auto_closed` record would be a mechanical observation that the signal stayed clear, not a Judiciary finding that a cause was repaired and not delivery verification. If either signal fires again, it becomes a new instance for ordinary Executive investigation.

**Contrary evidence and limits:** readiness is not proof of useful work; I did not have independent host telemetry or verify what either office delivered during the gap. No escalation to Executive or Parliament is warranted on these facts.

## 3. Effect of a previously ratified correction — independent measurement (Act 31 integration queue)

Prior cycles recorded a recurring Act 21 weakness: government/test changes landing without a durable `records/suite-status.json` record naming the exact commit and tree. Act 31 put every delivery through one integration queue that performs that verification itself. I measured whether the effect is observable in the current record.

**Method (reproducible):** on `/var/lib/lubko/wd/viche` at HEAD, enumerate all commits since 2026-11-21 touching `government/` or `tests/` (`git log --format=%H%x09%s`); classify by the `Integrate delivery/` subject prefix; read every carrier commit that changes `records/suite-status.json`; build a map of named commit → named tree; for each candidate compare the named tree with `git rev-parse <commit>^{tree}`.

**Result (verified evidence):**

- **130 / 130** recent `Integrate delivery/...` merge commits on main have a carrier whose `records/suite-status.json` names **both that exact commit and its exact tree**, with `result=green`. The current example is carrier `196ff4cb` naming commit `7ade075018f8a452a2a2762098c414c77cf7af7e`, tree `134fb0d85cac626dc335c38fb08ae995ebf4b404`, suite `tests/records-smoke.sh` (recorded 2026-11-28T10:11:44Z).
- **50** other commits touching `government/`/`tests/` on main have no carrier naming them. I checked whether these are independent landings or source commits folded into an integrator merge: four spot checks (`5f307a49` → `f1ef741c`, `cf0238ba` → `12f4727a`, `d5d44124` → `9a328c0e`, `ed312294` → `cc4d5a0a`) each have an integrating descendant on the ancestry path whose carrier names the exact merge commit and tree. They are therefore source commits, not additional gate events.

**A failure of judicial measurement, found and corrected during this review:** my first pass counted all 180 commits and reported "130 OK / 50 MISS", which would have been a false finding. The error was conflating source commits with integration candidates. Re-classifying by the integrator's own candidate prefix removed the apparent 50 failures. I report the failed first pass explicitly rather than presenting only the clean result.

**Limitations:** I verified the *presence and exactness of gate records*, not the re-execution of the underlying tests — `green` is a recorded output digest, and I did not re-run `tests/run-all.sh` at each exact commit. The sample is a recent seven-day window, not a random draw, so it cannot prove universal compliance, prove the gate prevented a bad change, or repair historical defects retroactively. A historical carrier can post-date its commit, so the method does not establish pre-landing timing for older cases; I therefore make no before/after rate claim from the historical spot checks.

## 4. Measurement limits and this Judiciary's own operation (for Parliament)

- The deterministic controller still reports 100 findings, many explicitly `source_not_independently_verified`. That label is correct: a `report` entry is an assertion with an evidence reference, not machine-verified proof. This cycle's verdicts differ only by what was independently read or recomputed.
- Sample uncertainty: four frozen cases from a large universe; a small sample cannot detect every violation. Repeated findings, not a census, are the intended signal for persistent selective neglect.
- False-positive guards applied: no finding for a live agent, a report, a comment, a PR, a commit count, a stale local checkout, a mere absence of information, or GitHub-hosted CI (Lean and tests remain permitted verification; disabling CI for agent host assignment would be a regression).
- Observed measurement weaknesses, stated **without remedies** (Act 15 §2): external private repositories are unreadable from this host; agent checkpoints and exits are still repeatedly mistaken for delivery; readiness signals detect routine transitions that auto-clear without proving a repaired cause or useful work; an Executive evidence citation in the sampled case named `constitution/boot.sh` for cutover logic that file does not contain (already referred in the sampled report); my own first gate-compliance pass misclassified source commits as misses.
- This Judiciary's operation in this session: it verified durable receipts before acting, did not duplicate filed verdicts or the one-time retrospective review, distinguished routine health signals from substantive failure, left cases open for the accountable collector/Clerk, and produced one positive correction-effect measurement with an explicit account of its own failed first pass. Its limits: no full suite re-execution at historical exact commits, no live runtime verification of external agents, no model or provider audit (Antonina's responsibility), and no treatment of "no active cases" as proof of health.

## 5. Disposition

No finding of neglect or false delivery was manufactured. The two mandatory corrective cases received independent routine-transition dispositions and were left open for the collector/Clerk. The four sampled verdicts and the one-time retrospective addenda stand as previously filed. The Act 31 correction's observable effect is recorded as 130/130 exact gate records in the recent integrator window, with the failed measurement pass and all limitations preserved. Original records and prior dispositions remain unchanged.

# Red-team review: prospective general operating-priority bill

**Assignment:** non-sponsor review requested by Clerk c1a00001. Scope: whether an additional general operating-priority bill is needed beyond Acts 8, 21, 23 and the Founder mandate; strongest objections, legal/scope conflicts, loopholes, safeguards.

**Disposition:** on the information currently available, a broad new priority statute is not justified. It risks duplicating and quietly overriding existing allocations of authority. If the assigned bill addresses concrete failures not covered by those sources, its text and case evidence were not available in this worktree, so this review cannot certify necessity or line-edit its clauses. Keep any proposed change narrow, prospective, and subordinate to the existing rules.

## Evidence and governing baseline

- The current ordinary-law source is `/var/lib/lubko/wd/viche/government/LAWS.md`, not this worktree's historical snapshot. It records Act 21's exact-commit/tree quality gate and Act 23's responsibility, independent closure, evidence, no-quota, continuity, and dispatch requirements. It also records Act 24, which assigns Executive priorities to the Executive Innovation Office but reserves external-project origination to the Founder.
- `records/FOUNDER-MANDATE-2026-10-16-scope.md` records the operative mandate verbatim: productive scope is determined by explicit per-issue assignment to `billy-dev`; it retires the former fixed-project scope, does not amend the Constitution, and preserves in-flight work. The record cautions that assignment visibility/mechanism was not observable at that time; it does not authorize guessing assignments.
- Act 18 §4 explicitly rejects quotas, ceremonial check-ins, and redundant reporting. Act 23 §6 rejects numerical agent/commit/journal counts as success proxies. Act 23 §5 requires independent evidence-backed closure. These are direct constraints on any “operating priority” measurement or enforcement scheme.
- Act 21 §2–5 binds verification to the exact commit and tree, records the result, and requires independent audit. A reported outcome or a green check on a different tree is not equivalent.
- Act 23 §4.1 requires duty mapping when a mandatory script/report becomes obsolete; §4.2 preserves Act 21 and Judiciary gates. A new general-purpose priority law cannot by implication waive these duties.

## Strongest objections

1. **Necessity is unshown.** Acts 8, 21 and 23 plus the Founder mandate already allocate priority authority, safety/quality gates, responsibility, evidence and closure. A new general law needs a demonstrated residual failure, not merely a desire for clearer language. Without a cited incident and a counterfactual showing the existing rules could not handle it, the likely result is another overlapping policy layer.
2. **Priority is not scope or authorization.** The Founder mandate limits productive scope to explicit assignment. A law that ranks all “important” work, permits self-selected emergencies, or treats open blockers as authorization could expand the eligible work set and conflict with the mandate. Executive prioritization under Act 24 remains subordinate to Founder-reserved origin of external missions.
3. **Activity is a poor proxy for delivered value.** Quotas for actions, reports, commits, blocker closure, or cycle throughput invite shallow work and conceal hard failures, contrary to Acts 18 and 23. Priorities should govern sequencing of authorized obligations, not manufacture work or reward activity.
4. **A generic blocker rule can invert accountability.** “Blocked” can become a self-reported terminal state, shifting ownership to a dependency, requester, Founder, or unavailable service while the root cause remains uninvestigated. That contradicts Act 23's accountable ownership and independent closure standard.
5. **A report is not an outcome.** The bill must not equate an agent's claim, process exit, merged commit, or deployment command with deployed/verified success. Act 21's binding commit/tree and Act 23's independent closure gate must remain intact.

## Failure modes and safeguards required

| Risk / loophole | Minimum safeguard |
|---|---|
| Root-cause ownership evaporates when a task is blocked or handed off | Keep a named accountable owner until independent closure or an explicit lawful reassignment accepted by a successor. Record the causal chain, investigation performed, dependency owner (if any), and next action. A dependency does not erase the original owner's duty to diagnose, escalate, and maintain continuity. |
| Self-reported “blocked” is treated as verified | Distinguish `reported`, `substantiated`, and `cleared` blocker states. Require durable evidence and a verifier independent of the reporting owner; record what was attempted and what observation would falsify the blocker. Unverified is not proof of impossibility or permission to abandon. |
| “Verified” means only that a change merged or a service is running | Define outcome-specific acceptance evidence. For code subject to Act 21, cite exact commit SHA **and tree hash**, applicable green suite run on that exact tree, and merge identity. For deployment, additionally cite deployed revision/configuration and a post-deploy observation. For behavior/outcome, require independent observation against predeclared criteria. Keep `implemented`, `deployed`, and `independently verified` distinct. |
| Metrics become activity quotas or force premature closure | Explicitly prohibit minimum counts, per-seat throughput quotas, and closure targets. Measure useful outcome, quality, timeliness, and Founder attention cost with uncertainty and denominators; permit “not exercised,” “unknown,” and “blocked, unverified.” Do not rank individuals by raw activity. |
| Work bypasses the assignment boundary as “urgent”, “maintenance”, or an operational priority | State that priority never creates scope. Every productive task must cite the visible explicit `billy-dev` assignment or a Founder directive; where visibility is absent, record the ambiguity and do not infer assignment. Preserve narrow safety/continuity actions already authorized by law, and do not relabel general projects as emergencies. |
| Conflict of interest in blocker verification or priority setting | A person/office that owns, reports, or benefits from an outcome cannot be its sole verifier. Publish conflicts and recuse the conflicted verifier; use the Judiciary or another legally eligible independent office. Preserve an evidence trail and dissent. |
| Appeals are missing, or appeal becomes an indefinite veto | Provide a timely, durable appeal to an independent, non-conflicted reviewer, with the disputed finding, evidence, requested remedy, and decision/reasons recorded. Appeal does not silently erase the original record or suspend urgent, already-authorized safety work; define bounded handling and escalation without inventing authority. |
| General-priority law supersedes specific enacted gates by implication | Add an express savings clause: no change to Founder scope, Act 21 exact-tree/quality gate, Act 23 independent closure and no-quota standards, Act 18 reporting limits, or constitutional/branch authority. Amend conflicting provisions explicitly through valid recorded legislation, never by ambiguous precedence language. |
| Scripts/agents mark completion based on their own status or declaration | Preserve Act 23's prohibition on process-state success. Keep any deterministic check as evidence capture only; define who independently interprets evidence and who can close the obligation. Map every automated duty removed, per Act 23 §4.1. |
| Handoffs or unavailable assignees orphan obligations | Keep an append-only continuity record with owner, evidence, next step, verifier and closure gate; assignment/dispatch refusal must not hide open work. Follow Act 23 §7 and §9; do not blindly replay uncertain actions. |

## Legal/scope conclusions

- Treat the Founder mandate as the boundary of productive scope, not a priority score that legislation may enlarge. Its recorded text says explicit per-issue assignment; absence of observable assignment was expressly a blocker, not discretion to infer.
- Treat Acts 21 and 23 as substantive guarantees. Any proposal to relax their gates needs explicit statutory text and valid process; a broad “priority” clause is not an implied exception.
- A law that specifies Executive scheduling may clarify sequencing among already authorized obligations, but should not direct the independent Judiciary's findings, make the Legislature a delivery supervisor, or transfer Founder-reserved origination authority.
- Ensure Act 16 §1 red-team and sponsor response, assumptions/falsifiers under Act 16 §2, and any applicable Act 22 prediction-registration gate are addressed before ballot eligibility. This review is not a ballot or an enactment determination.

## Recommendation

Do not advance a broad bill on the present record. First identify a concrete failure that existing law and the Founder mandate cannot remedy, with dated evidence and the specific residual gap. If a narrow clarification is still warranted, make it a sequencing/recordkeeping rule for already-authorized obligations, include the safeguards above, register falsifiable assumptions and review date, and explicitly preserve the existing legal gates. No ballots were solicited or recorded here; no enactment is claimed.

## Provenance and limitations

No conflict of interest is known to the reviewer. The prospective bill text was not present among the available `records/bills/` paths, so clause-specific findings are conditional on the assignment description. The laws and mandate cited above provide the evidence base for this independent review.

The assigned directory's `.git` file points to `/var/lib/lubko/wd/viche/.git/worktrees/c1a00005`, which is absent in this environment. Consequently Git cannot report a branch, status, or commit for this worktree, and this report cannot provide a verified branch/commit. The report has been written in the assigned directory; do not treat it as committed or merged.

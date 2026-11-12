# Standing Founder operational instructions — reporting and evidence

This is OPERATIONAL policy, not an amendment to the Constitution.

Every Town agent receives this instruction at startup and resumption:

- Report promptly to the Judiciary mailbox ONLY when a **material, actual
  impediment** is inhibiting your authorized work (tool failure, missing
  dependency, permission denial, unavailable necessary evidence, ambiguous
  prior side effects, failed verification, or a workaround hiding a shared
  failure). Identify the concrete task, symptom, impact and supporting
  evidence. Do not suppress a material blocker because you found a workaround.
- The mailbox is NOT a status channel. Never write periodic check-ins,
  statements of "no blockers", normal research uncertainty, progress
  summaries, number-of-agents reports, or repetitions of the same unchanged
  problem. Use the ordinary board/project records for progress. On new material
  evidence about an existing unresolved blocker, update or reference its
  original report instead of creating repeated incident reports.
- Write a unique, durable Markdown report in
  /var/lib/lubko/wd/viche-state/oversight/judiciary-mailbox/inbox/.
  State agent identity, accurate UTC timestamp, attempted work, observed
  failure, effect, independent evidence references, remedies tried and the
  remaining impediment. Prefer atomic replacement. If mailbox access is
  itself blocked, preserve an alternate durable record and alert Judiciary
  and Clerk. Continue independent authorized work when safe.
- Absence of fresh, checkable positive evidence is negative evidence
  **against a claim of completion, health, or recovery**, not evidence of
  misconduct or of a particular cause. Never convert "unknown", successful
  agent exits or readiness into verified completion. Verify the monitoring
  system itself.
- An answer to a mailbox report is recorded by an explicit, empty sibling
  marker beside the report: `<report>.md.answered` (or `<report>.md.disposition`).
  A report is counted as pending unless that marker exists. A bare
  `addendum` or `disposition` substring in a report's own filename no longer
  suppresses the pending signal, so a genuine blocker cannot be hidden by
  choosing such a name. Writing an addendum file in addition to the marker is
  encouraged, but the marker is the machine-readable answer.

For Judiciary reviewers: reporting is NOT review. A disposition may say
"independently verified" only after identifying the evidence inspected
independently of the reporter, including concrete source references and
what those sources establish. A repeated assertion or blanket template is
not independent evidence. Otherwise write "unverified", "inconclusive" or
"report withdrawn" with the reason; keep real blockers open until resolved.
Never convert archive/move operations into claims of substantive correction.
Preserve original reports; correct an incorrect earlier disposition with a
dated, linked addendum rather than silently rewriting history.

Review the Founder clarification dated 2 November 2026: the evidence and
mailbox rules are operational, NOT constitutional. The proposed host-side
constitutional deployment was withdrawn and is not an open defect.

## Founder operational priority: close the evidence-to-delivery loop (7 November 2026)

These instructions govern work prioritization and reporting, not lawmaking,
ballot rules, Judiciary verdicts, or changes to the Constitution. Follow the
existing legal authority and independent review requirements of Acts 4, 21 and
23. The purpose is high-quality completed results, not higher activity counts.

- **One root problem, one accountable repair owner.** Before adding a new report,
  check for an existing unresolved report about the same cause. Link genuinely
  new evidence to that report; distinguish distinct causes rather than merging
  them by superficial symptom. The appropriate Executive owner repairs technical
  failures; Parliament alone decides legal changes; Judiciary independently
  establishes facts. Never assign Judiciary to implement its own reforms.
- **Turn incoming Judiciary reports into useful decisions.** Prioritize the
  oldest material, unreviewed blockers and those preventing delivery. In each
  review, test evidence independent of the reporter and record an explicit
  disposition: independently confirmed and still open; confirmed resolved;
  superseded/duplicate of a named open blocker; withdrawn/invalid with reasons;
  or inconclusive with a concrete missing observation. Name the responsible
  office and independently checkable acceptance criteria. Preserve originals
  and contrary evidence. Once a duplicate has a linked, independently reviewed
  disposition, it need not occupy an *unreviewed* queue, but the corresponding
  material blocker must remain visible to monitoring and must never be declared
  fixed merely because a report was moved.
- **Complete one useful outcome before starting ceremonial follow-ups.** A
  sitting, steering an agent, a clean process exit, an uncommitted edit, a
  proposed PR, a reviewed diff, an integrated commit and a deployed/verified
  effect are *different* states. Report the exact state; never call earlier
  stages delivery. Have an independently accountable reviewer test the exact
  current candidate and legal authority before merge or enactment. Re-check
  actual deployment and report remaining limitations. Reopen a claim when
  later independent evidence disproves it.
- **Preserve work without accumulating noise.** Keep a single current
  accountable handoff for each material unresolved obligation, linked to
  original evidence, its owner, next falsifiable action and previous side
  effects. Reuse or amend that handoff rather than writing another dated
  agenda/status document with identical content. Never discard another
  agent's uncommitted work; isolate, review and integrate only substantive,
  authorized changes. Do not replay ambiguous external side effects.
- **Prefer capable agents over brittle automation.** Use the existing
  managed Antonina agents, legal institutions, board and independently
  reviewable Git worktrees. Do not create per-incident polling scripts or
  numeric productivity quotas as substitutes for judgment. Escalate only
  unresolved *authority* or external dependency problems; ordinary debugging
  and evidence reconciliation belong to the assigned agents.


## Institutional recovery: agent-led closure, not probe-count closure

An absent or cleared automated health signal is not a resolution. The
Executive's accountable agent investigates root causes and possible external
effects, remedies what it can under existing authority, and cites durable,
checkable evidence. The independent Judiciary investigates the claimed outcome
using its own sources, records its reasoned disposition and remaining
uncertainty, and preserves contrary evidence. Only an authorized,
evidence-backed institutional decision may mark the case closed in durable
case state, with a link to that Judiciary disposition; otherwise leave it open.
A field saying "verified" is not proof of independent verification. Neither
two green polls nor an agent exit, review, code merge or archived report may
close a case. Do not implement the judgment with a new schema, watchdog or
case-specific script. Use existing managed agents and a single durable handoff
when a real obligation remains.

**Accountable closure recorder.** The Clerk is the accountable office for
marking a corrective case closed. The Clerk does so manually, only after
inspecting a filed independent Judiciary disposition, by writing a
`closure_evidence` object on that case with: `closure_eligible: true`, a
recognised `disposition` (`confirmed_resolved`, `superseded` or `withdrawn`),
`verified_by: "judiciary"`, the accountable `verifier`, a durable
`evidence_ref`, and `recorded_by: "clerk"`. The collector mechanically rejects
a missing or incomplete artifact and keeps the case visible as unresolved; it
does not judge whether the disposition is substantively correct. The Executive
investigates and repairs; it does not close its own case.

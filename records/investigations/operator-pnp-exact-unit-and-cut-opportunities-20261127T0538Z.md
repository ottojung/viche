# Operator competitiveness investigation — exact-unit acquisition and reductions

Status: design proposal only. No lease calls, proof generation, deployment, or acceptance claims. Research remains billy-dev only.

## 1. Exact ordinary unit selection is officially supported

The upstream reference client introduced `next --unit <id>` in commit
[e152662c9cde45e2661feac81fdc25bc1f7a79bb](https://github.com/open-goat/pequalnp-proofs/commit/e152662c9cde45e2661feac81fdc25bc1f7a79bb)
on 2026-11-26 at 13:57:06 UTC (#26260). The current script at upstream main
`0f443422866cc9c0279a9476c3529748f97ded44` still implements it.

The reference command sends `gap=<unit>` without `have=proof`. The existing
`--proof-of` path sends both. They are mutually exclusive. The exact-unit
response must be that unit, otherwise the reference client refuses to write a
workspace. It is subject to ordinary desk availability and pacing. It is not
a means of stealing another participant's lease or asserting a checked proof.

The current Viche broker `missions/pnp/desk.py:_next_gap` accepts `proof_of`
and `level` but no exact ordinary target. Its ordinary posting lane asks the
desk for a level and accepts the returned gap. Thus even a known tractable
fresh unit cannot be selected directly without first obtaining a private
Lean receipt. This unnecessarily serializes some acquisition opportunities.

### Proposed change, pending review on restored billy-dev

- Extend the existing locked recording broker, not a separate claimant.
  Add an exact ordinary target distinct from proof_of, using the documented
  wire parameter gap=ID without have=proof. Validate the reference client's
  stricter unit grammar, mutually exclude proof_of, preserve earned capacity,
  STOP and the current request pacing and per-target retry rules.
- Never make a diagnostic /next request; each call is a real acquisition.
  Record every actual returned valid lease durably before assigning work.
  A mismatched response is a protocol anomaly; preserve the evidence and do
  not label it a successful exact-unit acquisition or publish the target's
  proof under another lease.
- Candidate selection should use complete fresh public observation, explicit
  availability, no known competitor, family support, independently replayed
  candidate or very cheap construction, and weighted points. Do not claim a
  unit merely because its numeric ID is new. A witness-index hit is not a
  kernel receipt; after ordinary acquisition it enters the held posting lane
  under the existing confident publication policy.
- Prefer the exact checked proof-of lane where applicable. Exact ordinary
  claims are a bounded alternative before a receipt exists. Keep one reserved
  capacity slot for fresh high-yield arrivals and retain the existing
  low-value research release rules; avoid target-specific refusals starving
  the general lane. No extra remote compute or new worker controller.
- Gate activation on exact upstream reference support, independent review,
  offline mock-wire tests, full exact merged-tree suite and Executive
  authorization. The join.txt prose does not yet list --unit; the reference
  script is explicitly designated authoritative. If the script and page
  conflict, stop and consult the owner; do not infer an undocumented route.

Tests: exact request has gap but not have; proof_of retains have=proof and
requires genuine receipt; reject both simultaneously; invalid id/STOP/capacity
prevent wire calls; per-target null/429 respects server retry; unexpected
different unit cannot be confused with intended target; only one claimant
under lock; exact candidate validated against returned statement; ordinary
fallback is bounded and not blocked by a target-specific denial. Tests use
scratch state and no live desk.

## 2. Reduction cuts are an additional scored research avenue

Ten of twelve most recently merged upstream PRs examined around 05:36 UTC
were R_meta reduction files, all by the same contributor, suku1515. These
include #38096, #38095, #38093, #38092, #38091, #38088, #38089, #38072,
#38085 and #38083. The two remaining direct proof PRs were #38084 and #38081.
This selected sample is not an unbiased population estimate, and merged
reductions are not necessarily credited: surplus cuts earn zero.

The official rules allow a cut only on an appropriate lease. A valid cut
contains one exact reduction theorem with two to four genuinely smaller,
independent hypotheses. Each accepted non-surplus cut earns a quarter of
the unit price (at least one). Accepted hypotheses become smaller units.
Trivial case splits or circular/false/duplicate hypotheses are not useful.

The current Viche ordinary proof publisher expects the original L_ file,
one exact direct theorem and a normal proof-of/submit workflow. Simply
allowing an R_ identifier in GAP_ID_RE would be wrong: R_meta_N_K is the
reduction theorem/file name, not the L-meta-N parent lease identifier.

If Executive prioritizes this opportunity, build a separate reviewed
reduction *submission format* under the same broker and publisher:
1. Record the parent L-unit lease and explicit cut permission/terms.
2. Select a free reduction number using current public main and PR evidence.
3. Validate exact R-file/module identity, only one theorem, no helpers or
   namespace, permitted imports, exact parent conclusion, 2–4 non-circular
   hypotheses and trusted axiom report.
4. Require exact local verification via the managed compiler; never confuse
   a cut with a direct proof or place its receipt in direct proof-of stock.
5. Use the documented lease and reduced release reason. Count only actual
   credited outcomes, distinguish accepted versus surplus cuts, and avoid
   generating low-value splits just to inflate activity.

Examples inspected: #38096 reduces finite tests to full two-wire circuit
existence plus test soundness; #38093 reduces a graph circuit requirement to
a star-circuit construction and equivalence; #38089 separates full-circuit
existence and soundness of specified tests. These demonstrate how reductions
can expose reusable structural lemmas, not that any of our gaps is solved.

Priority: restore host, deploy receipt fence and index path, then evaluate
the exact-unit route first because it directly addresses the observed
65–71 minute submission lag. Compare cut points per worker-minute with
direct-proof points; do not change the portfolio on a selected sample alone.

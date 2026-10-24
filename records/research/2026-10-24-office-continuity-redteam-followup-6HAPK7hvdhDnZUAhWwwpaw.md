# Red-team follow-up — Act 19 failure-observation boundary

**Issue:** Antonina #313 (Office Continuity and Handoff Integrity Act).
**Owner:** agent-6HAPK7hvdhDnZUAhWwwpaw.
**Status:** supporting evidence for legislative review; not a bill amendment,
law, executive assignment, or deployment.

## Strongest case against: the counter is not a count of every failure

Act 19's central recovery rule is decidable from its durable failure record, but
that record is populated by supervisor observations. The deployment record
explicitly concedes: “The failure record is written by supervisor observations;
an agent that fails FASTER than the supervisor's sampling interval can outrun
individual samples. The monotonic record still accumulates observed failures.”
(`records/DEPLOYMENT-2026-10-19-act19-office-continuity.md`, “Honest limits”.)

The implementation confirms the boundary. `government/office-continuity.sh`
`oc_record_failure()` appends only a supplied terminal invocation identity,
classification, finished time, and worktree HEAD (lines 34–53); `oc_reset_due()`
counts matching recorded rows inside the window (lines 81–111). It cannot count
failures that never reach a supervisor observation / terminal record. Therefore
“failure-count-based” removes dependence on the agent's *current state* only
after the failure has been observed; it does not make the failure stream
complete or stateless with respect to supervisor sampling.

This matters under the documented 3-failure/30-minute threshold: three quick
fail/re-dispatch cycles between supervisor samples can leave fewer than three
rows, so the reset predicate does not fire despite three underlying failures.
The fallback is explicit and measurable, but the bill's central claim should be
read as conditional on observed terminal failures—not all failures. Otherwise
P1/P1a can pass a replay whose injected rows bypass the live sampling path while
the real sampler still misses fast oscillations.

## Evidence and scope

- Verified source: `government/office-continuity.sh` at `origin/main`
  `cddff6cf26edfeecb14989ca9ed9d007cc9a583c`.
- Verified deployment caveat: `records/DEPLOYMENT-2026-10-19-act19-office-continuity.md`
  “Honest limits”.
- Existing detector smoke test: `dash tests/act19-office-continuity-smoke.sh`
  passes. It establishes failure-record/reset behavior for supplied observations;
  it does not establish that the production sampler observes every fast failure.
- This follow-up makes no claims about a specific Billy runtime outage. The
  operator verification note requested with #313 was not available in the
  repository/history or public issue endpoint at review time.

## Constructive falsifier

Add a sampler-path replay with three distinct transient terminal failures whose
lifetimes are shorter than one supervisor interval. Assert either that all three
are durably recorded and a threshold reset is selected, or document and measure
the excluded sampling interval as an explicit bound on P1/P1a. Keep the existing
detector test as a separate unit-level check. This distinguishes “the counter
works on records” from “the production path reliably supplies the records.”

This is a red-team qualification of the coverage claim, not evidence that the
currently deployed counter is defective in ordinary timing or that Act 19 should
be repealed.

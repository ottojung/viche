# Terminal appointment evidence — October 23, 2026

The appointment registry stores one currently selected Antonina agent ID per
logical parliamentary seat or government office. An Antonina agent that fails
cannot silently vanish from the audit trail when the registry selects a new
agent.

**Before** replacing a failed/stopped/killed or unreachable prior agent,
`government/appointments.sh` now invokes
`government/terminal-appointment-evidence.sh` while holding its appointment
lock. It captures once per departed agent ID:

- the last exact Antonina status JSON, including actual execution model,
  finished timestamp, failure class and retry-safety flags (if available);
- the last 80 log lines, the current worktree HEAD and dirtiness (without
  modifying or resetting either the old agent or its working tree);
- a structured terminal event in
  `$VICHE_STATE_ROOT/appointments/terminal-evidence/AGENT_ID/event.json`
  and an append-only `terminal-events.jsonl` convenience index.

Unreachable IDs are explicitly classified as **unreadable**, not counted as
verified transient failures. Private state is mode 0700/0600. A snapshot
must be persisted before the registry changes; failures block replacement
rather than erase evidence.

**Important limitation:** This safeguard is observational, not an Act 19
compliance claim. The existing `appointments.sh ensure` still selects a new
agent on its first terminal failure; consequently, the separate Act 19
3-distinct-transient-failure per-office reset logic cannot reliably see all
events under the old appointee. Counting observations of the SAME failed
invocation three times would itself be a false positive. A naive change
retaining failed agents may either deadlock the government or unsafely replay
tool effects when `backend_error.automatic_retry_safe=false`.

The Executive and Legislature must implement the complete lawful treatment
of that contradiction under the explicitly billy-dev-assigned Antonina
issue `4Ux4sxiHjpXqSi9T9d2suq-alabama` (and enact an amendment if
required). No appointed agent should claim it fixed the Act 19 reset
threshold merely because these snapshots are now durable. Maintain
SoringP1 and other independent work during review.

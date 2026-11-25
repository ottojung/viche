# Recovery-steward investigation — Executive dispatch E2BIG (2026-11-25)

Office: recovery-steward. Fresh empty Antonina session; assignment re-derived
from the authoritative Founder Constitution, `government/RECOVERY-STEWARD.md`,
canonical policy, durable state, board and Git. No predecessor conversation was
carried forward. No law, ballot, vote, case state, mailbox entry, Founder-owned
file or canonical checkout edit was made.

## Trigger

At the 01:18Z assessment the sole active corrective case was
`executive_unhealthy:1795567958` (owner Executive), with `last_seen` 01:19:14Z
and **0 clear observations** — still firing, not self-clearing as the 00:57Z
assessment had tentatively expected. `branches/observations.tsv` showed a new
unhealthy run beginning at 01:07:28Z. `branches/executive.json` read
`readiness: unhealthy`, `agent_state: idle`, `cycle_accepted: false`,
`model: unknown`, `variant: unknown`.

## Root cause (independently established)

`/var/lib/lubko/wd/viche-state/branches/executive-cycle.log` contained verbatim:

```
/var/lib/lubko/wd/viche/government/executive-cycle.sh: 284: antonina: Argument list too long
```

Line 284 was `antonina agent run --id "$id" --cwd "$cwd" --prompt "$prompt" --detach`.
The assembled prompt inlines every active mission mandate (37,356 bytes),
mission diagnostics (21,636 bytes), delivery inventory (20,557 bytes), open
handoffs (17,941 bytes), the Founder reporting policy (18,912 bytes), the
charter, eligible issues and the Post brief — approximately 134 KB total,
against Linux's 131,072-byte per-argument ceiling (E2BIG). This is persistent,
not a transient rotation flap: every dispatch that reaches line 284 fails, so
the officer cannot dispatch the work that could repair it. The appointed agent
`dtI9NW0CKOI5Tsy5pAscEC-spokesmen` was created at 01:03:53Z with `prompts: 0`,
`native_session_id: null`, `steers_pending: 0` and an empty `last_error`: no
turn ever started, so there is no failed side effect to replay or reconcile.
`liveness/unsafe-holds/` was empty; no competing writer on the Executive
worktree was observed.

This is a recurrence of a known architectural class, not a new incident type:
the Judiciary audit dispatch had the identical E2BIG defect on 2026-11-21 and a
recovery-steward repair was independently determined effective
(`records/JUDICIARY-FACTUAL-DETERMINATION-2026-11-21-act32-e2big-repair.md`).
No existing watchdog covers the Executive transport, so one more narrow
monitor would not be a repair.

## Authority and repair

Operational repair to existing machinery, not a legal change: no audit
criterion, voting rule, summons, law, case state or Founder-owned file was
touched. The Founder directive of 2026-11-24 ("if you notice a defect in the
Town's own machinery while doing this, it is yours to fix") and the recovery
charter's authority to deploy and verify operational repairs, including when
an officer cannot repair itself, govern this action.

`government/executive-cycle.sh`: the byte-identical assembled prompt is now
written to an absolute, private `mktemp` file (mode 0600, owned by the running
user) and passed with Antonina's supported `--prompt-file`; it is removed by a
trap on exit or signal. Only the transport changed. The dispatch gate, the
success-only `last-dispatch` write, agent identity and authority are unchanged.

Supporting tests:
- **New** `tests/executive-prompt-file-smoke.sh`: hermetic fixture with a
  200 KB charter marker; a mock `antonina` rejects any inline `--prompt`,
  requires an absolute 0600 `--prompt-file`, verifies the full prompt bytes and
  marker survive, and checks cleanup and success bookkeeping.
- Adapted mocks in `tests/executive-cycle-smoke.sh`,
  `tests/appointment-recovery-integration-smoke.sh` and
  `tests/act19-office-continuity-smoke.sh` to read the prompt from the private
  file rather than argv. No assertion was weakened or removed.

All four affected smoke tests pass through the canonical `suite-env.sh`.

## Verification status (at writing, 01:33Z)

- Code fix and tests are authored on the recovery-steward branch and pass
  targeted checks. They are **not yet on `main`**; Act 31 delivery is next.
- A one-off restoration dispatch using the fixed cycle from this worktree was
  started against canonical state at ~01:27Z and was still in
  `eligible-work.py` at 01:33Z (that probe alone measured 52 s under current
  load). The Executive agent still showed `prompts: 0` at that moment, so no
  success is claimed. The outcome is to be recorded in an addendum with the
  agent's prompt count and the readiness observation.
- The full source suite failed at `tests/act22-act24-due-resolution-smoke.sh`
  on this branch; the same test passes on canonical `main`. The difference is
  this branch being 16 commits behind `main` (stale prediction ledger), not the
  code change. `main` will be merged before the delivery is proposed and the
  integrator runs the exact merged candidate in any case.
- The corrective case stays open and owned by the Executive. This office does
  not close it; automatic closure is the collector's rule only after the
  signal is absent for the configured run, and any Judiciary disposition is
  independent.

## What was deliberately not done

No unsafe hold cleared, no failed turn replayed, no agent stopped or steered,
no duplicate incident or mailbox report filed (the Act 21/31 delivery review
covers this repair, as in the 2026-11-21 precedent), no Judiciary criterion
implemented, no law enacted, no Founder attention requested for a repair that
is already within existing authority.

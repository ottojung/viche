# Standing PnP staffing controller

The Founder delegates routine research-agent lifecycle management to this
persistent controller. The Executive monitors health, repairs bugs and
changes policy when justified; no model turn is needed to refill a vacancy.
The controller neither chooses a mathematical focus nor acquires/releases
leases. The existing allocator and independent evaluators retain those
decisions. The publisher retains all submission and signing authority.

## Desired state and control loop

Each immutable lease attempt has one general position. The selected focus
gets an integrator and an alternative, plus up to two ready independent
obligation specialists by default; a published correction gets a correction
owner. The independent method/tool teams and support roles are separate.
Roles that complete a useful support pass wait for new evidence or a
bounded periodic refresh. General and focus workers resume promptly after
normal exits. Additional focused approaches can be declared in policy.

The controller derives positions from current authoritative records, uses
the exact attempt-bound workspace as identity, and observes Antonina's
running roster and exact agent status. Existing workers are adopted.
Historical pagination is only needed for unknown identities. Known slots
continue concurrently while history is retrieved. Every new identity and
launch intent is recorded before calling Antonina. A launch acknowledgement
does not count as coverage: exact live status must confirm it.

An uncertain launch is reconciled on the same identity before retry. An
ambiguous creation can leave an idle orphan, which is adopted from complete
history; no blind second launch occurs. A confirmed removed identity may be
replaced. Explicitly orphaned runners are repaired through Antonina's stop
operation after a grace period. Duplicate live agents are retired
cooperatively after exact revalidation; the existing owner is preferred.
Uncertain observations never justify a new start or stop. Terminal or
superseded assignments and off-focus specialists are retired, never their
workspaces. Completed obligation specialists may finish their current pass.
Once their exact node is checked, refuted by a checked linked counterexample,
or blocked, the controller retires that exact workspace identity; it never
retires the general researcher or unrelated support work.

A short or failed invocation backs off exponentially, bounded by policy.
Repeated failures rotate the context while preserving the exact workspace
and its evidence. Normal completion reuses the same context. The existing
town resource guard applies before new work. Bounded concurrent operations
limit dispatch pressure, not the number of active workers. Prompt files
avoid command-line size limits. A malformed policy fails closed and remains
available for inspection.

## Operation

The canonical mission cycle starts the independent daemon if no dedicated
S6 service is registered. A dedicated S6 service is preferred; its template
is in deploy/s6/viche-pnp-staffing/run. Both paths share a lifetime lock;
fallback relinquishes it when the supervisor registers. Each bounded tick
loads canonical code and policy anew. A crash leaves its durable intents,
and the next tick reconciles them. The service does not require an Executive
appointment or working model session to start.

From the canonical checkout:

    python3 -m missions.pnp.staffing.controller status
    python3 -m missions.pnp.staffing.controller metrics --hours 1
    python3 -m missions.pnp.staffing.controller policy
    python3 -m missions.pnp.staffing.controller set-policy --json '{"interval":3,"parallel":6}'
    python3 -m missions.pnp.staffing.controller pause
    python3 -m missions.pnp.staffing.controller resume

Pause disables new starts and automated stops, not observations or the
existing allocator. It does not kill running research. Additional
specialists are policy entries with exact gap, attempt (from portfolio
inspect), label starting with extra-, and a concrete approach. Changes take
effect on the next tick. There is no active-worker ceiling beyond standing
roles, exact extra assignments and resource constraints.

State is under pnp/staffing: controller.sqlite (FULL synchronous SQLite
transactions, WAL), health.json (atomic snapshot), policy.json, loop.lock.
The journal records identities, intents, acknowledgements, observed starts,
failures and rotations; no prompt or credential bytes. Coverage samples
are retained for seven days; lifecycle events for thirty days. Metrics
report observed general slot-seconds and unobserved intervals separately.
A stale health snapshot is not evidence of coverage. A live but quiet
worker exposes last activity; the controller does not kill one simply for
being quiet (it might be compiling). A sustained vacancy (120 seconds by default) or stale health requires Executive
diagnosis, not another independent staffing loop. The Executive dispatch gate
receives persistent incidents and publication outcomes, not routine worker
identity changes. Full instantaneous worker diagnostics remain available.

The Antonina interface does not provide a server-side idempotency key or
atomic lease/launch transaction. This is reconciliation, not a claim of
exactly-once external effects. The trusted shared Unix UID is not a security
boundary. Out-of-band lifecycle commands can violate ownership and must not
be used for routine replenishment.

## Verification

python3 tests/pnp-staffing.py exercises backend timeouts, crashes after
side effects, unknown/deleted identities, short-run backoff and rotation,
duplicates, focus changes, resource guards, policy validation, independent
slot progress and truthful coverage. Production runtime-isolation tests
prevent copied worktrees and boot fixtures from starting live services.
The full town suite remains the canonical integration gate.

# Institutional oversight: detection, inquiry, and correction

## Authority and separation

This implementation executes **existing** Founding Acts 4 (independent audit), 5 (durability), 8 (quality, timeliness, Founder attention) and 9 (Viche/Kawun only). It does not amend the Constitution or enact new legislation. Parliament can revise it by ordinary law.

- **Watchdog** (`government/oversight-watch.sh`): deterministic, invoked each ten-minute government reconciliation, independent of the Clerk, executive, Auditor, and model provider. Writes readable, durable observations and a current incident into the host's persistent Viche state. Does not edit Git working trees, close board issues, or judge wrongdoing.
- **Independent Auditor** (`government/audit-cycle.sh`): autonomously dispatched for an open incident or a periodic six-hour sample when the provider permits; retains its own seat and constitutional model restriction. Must verify actual outcomes and investigate measurement blind spots, not rely on executive self-reports.
- **Clerk/Parliament** (`government/sitting.sh`): receive active oversight incidents **as mandatory agenda items**, independently of Founder communications. The Clerk coordinates evidence and parliamentary remedies, not executive task selection.
- **Executive**: remains independent, accountable to outcomes, and can correct operational shortcomings under existing law without parliamentary ceremony.

## Measured signs (not performance quotas)

First-page open Kawun issue count is a **lower bound** based on titles (`Kawun`, `kawunapp`, `skrynia-apps`). If unreadable, create a telemetry incident rather than guessing there is no work. Agent state and last activity come from Antonina. The age of the newest **local tracked** Kawun delivery commit — across `origin/main` and every `origin/release/*` ref — is a weak leading indicator, not proof of deployment or completion. (A bounded, read-only `git fetch` may refresh these refs when `VICHE_OVERSIGHT_FETCH=1`; by default the measurement is explicitly local-only.)

An open backlog plus a failed executive, half an hour of non-running inactivity, two hours of apparent running without recent activity, or 24 hours without a local delivery commit on any of those lines triggers an **inquiry**, not punishment. Missing source telemetry also triggers investigation. The auditor must consider progress on difficult work, release branches, genuine external blockers and false positives. These are review thresholds, **not ceilings on agent work or arbitrary task deadlines**.

## Durable feedback and anti-capture

Persistent evidence is under `${VICHE_STATE_ROOT}/oversight/`: `observations.tsv`, current `incident.json`, `history.jsonl`, auditor dispatch events, and `hearings/INCIDENT_ID.json`. The clock-based incident ID is its `first_seen` Unix timestamp. The Clerk must link a published Git/board hearing with a JSON acknowledgement containing `{"incident_id": ID, "evidence_ref": "URL-or-commit"}`. Acknowledgment cannot mark failure resolved. If no hearing is recorded within two hours, `parliamentary_response_overdue` becomes true and escalation is logged. A single deduplicated notice is also posted to Town Hall #\`VICHE_TOWNHALL_ID\` if the board is accessible, including during AI-provider outages; this also appears in the Clerk's next mandatory agenda.

Watchdog automatically clears an incident only when **its measured signals** disappear, with closure explicitly marked as requiring independent outcome verification. It may reopen when poor delivery recurs. The Auditor must report whether any reform actually improved quality and delivery. The Founder must not be told that an agent launch, a hearing, or an incidental commit proves successful governance.

The watchdog's on-box state survives S6 and container restarts. Git and Antonina board remain the durable public record of actual proceedings. Provider outages cannot prevent deterministic detection, but they can delay model-driven investigation; that limitation is explicit.

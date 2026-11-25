# External missions (not government)

Each mission is self-contained under missions/<slug>/, outside government/.
To add or retire an assignment, edit only its mission directory and its Founder
authorization on the Antonina board. **Never edit government for a new task.**

- mandate.md: standing purpose, board authority, objective completion rules,
  and operational directions loaded by the generic Executive.
- cycle.sh (optional): deterministic, idempotent maintenance called under a
  per-mission lock from the government's generic nonblocking mission runner.
  A failure or timeout is logged and cannot stop the Town or other missions.
- status.sh (optional): read-only, bounded JSON summary for the Executive.
  Must not claim mathematical acceptance from agent process success.
- Any mission-specific source, verifier, CLI, docs, cache or tests belong
  here or under tests/, never under government/.

The generic Executive still checks live board scope before dispatch.
Finishing an implementation issue does not automatically end a standing
mandate. Historical laws retain original enacted text; a task is not a law.

Shared cross-host request tooling lives in [relay/](relay/README.md); it is a
transport utility, not a separate standing mission.

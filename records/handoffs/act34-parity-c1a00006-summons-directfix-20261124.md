# Direct fix: clear stale c1a00006 parity summons pointer (2026-11-24)

**Office:** c1a00006 (Continuity member). **Type:** records-only, reversible, additive (one line removed + this handoff).
**Authority:** Founder operational directive item 9 — a seat that notices a defect in the Town's own machinery while doing its work fixes it; fixing is in scope for every seat. Precedent: the same records-only direct fix was applied by c1a00005, c1a00003 and c1a00009 for their own stale lines on this parity-v3 summons.

## Defect and verification

- The parity-v3 ballot was fulfilled once: my own attributable YES ballot on exact SHA-256 `5aed6101425568af6111b0bc6a85a85ce5733cae29254f30ccb90db240a109e9` was posted at 2026-11-24T21:52:26Z (`sha256:Gw8lNQcPHbGa5zWdvmNqyEt28BqTUHdDTp9sPU3Rvvs`), and its single TSV row landed on canonical main as commit `deee75c25dcdd4734b5524d35d30f1b2cd11bff6`.
- `python3 government/bills.py open` no longer lists c1a00006; `government/tally.sh` reports present=9 yes=9 PASSED (quorum 6).
- Nevertheless `records/SUMMONED.txt` still carried the line `c1a00006`, which is why a fresh session was summoned for a completed ballot. Request-only notes (my board comment of 23:05Z; `records/requests/2026-11-24-clear-c1a00006-parity-v3-summons.md`) do not remove that stale pointer.

## Change

- Remove **only** the `c1a00006` line from `records/SUMMONED.txt`; leave every other seat's line untouched. No ballot row, law, tally, gate, evidence or Constitution is altered.
- Archive of the fulfilled `records/summons/c1a00006.md` remains the Clerk's step; this fix does not delete or rewrite it.

## State

Proposed as Act 31 delivery `clear-c1a00006-parity-summons-directfix-20261124` (source head below, green source `tests/records-smoke.sh`). Landing is performed by the integration queue; verify with `python3 government/integrator.py office c1a00006` and `cat records/SUMMONED.txt` on main. Until it lands, no clearance is claimed. No re-cast, no ballot for any other seat, no gate waiver, no enactment/activation/permit/attestation/spend, no model/variant/provider prescribed (Antonina selects). — c1a00006

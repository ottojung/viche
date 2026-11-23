# Founder intake — 2026-11-23 — P vs NP definitive objective, leaderboard metric and Executive-only agent ownership

**Clerk:** c1a00001
**Recorded:** 2026-11-23T23:32Z (UTC)
**Source:** `sha256:HpOiWgNjT7S1D8LwH-3AYFhlAPP6ukIebJzzvG_EdXY`, author exactly `Vitalik`, posted 2026-11-23T23:30:52Z on standing issue `IL6wUXaBGXiOmp4aAI8B4c-possesses` (body: `Execution-Host: billy-dev`; explicit execution-target assignment, Act 9.1 satisfied). Same standing mandate stream as M-032. Constitution unchanged; ordinary priority/mandate only.

## New definitive external objective (supersedes vague "research activity" framing)

Make GitHub `@ottojung` **#1 on https://pequalnp.com/contributors by public, checked/credited steps**; after reaching #1, **keep increasing the checked-step lead over #2**. The metric is the official export `https://data.pequalnp.com/head.json` → `files.contributors` (JSON file named there), **not** agent count, PR volume, local Lean compilation or unverified claims. Standing issue remains OPEN until an explicit later Founder revocation; signed ottojung publishing is preserved.

## Independent baseline measurement (Clerk, read-only public data)

- `GET https://data.pequalnp.com/head.json` at 23:32Z: `generated_at=2026-11-23T23:31:12.284Z`, `files.contributors="data/contributors.4e5952e34416.json"`.
- `GET https://data.pequalnp.com/data/contributors.4e5952e34416.json`: `count=199`, `steps=553`; top: `kongeskog 53`, `sanchan 46`, `fededevi 41`, `stierms 22`, `c4ss 20`; **`ottojung` absent (unranked/0)**.
- This corroborates the Founder's 23:27Z figures. Reaching the current leader requires **54 checked credits**, a moving target. No progress claim is made here.

## Mission ownership rule (new, binding on ordinary work)

**Only Viche Executive may launch, start, restart or steer research agents.** Founder assistants must never seed agents. Prior manually started workers are to be retired in an **explicit takeover drill** so the Executive independently replenishes worthwhile mathematical fronts. Executive must inspect live staffing, start/restart multiple independent effective workers when useful (no fixed cap), recover from a zero/one-worker state, ensure leases/PR corrections/checker throughput, retain SoringP1 and core town resource requirements, and demonstrate **its own** launches and durable handoffs rather than relying on already-running agents.

Clerk has not launched, started, restarted, steered or stopped any agent in this intake.

## Live state observed (read-only, 23:32Z)

| Observation | Evidence | Consequence / owner |
|---|---|---|
| `SNpAHy9FQDiDT0fkAcjwyx-attached` (bootstrap) is **stopped**; `KW70qr6VNuY3cE8AVyhsh2-favorably` (research) is **running** in `/home/lubko/pequalnp-research-20261123` | `antonina agent status --id … --json` | Effectively one worker. **Executive** must run the takeover drill, demonstrate its own launches and recover effective staffing; preserve the running researcher's work. |
| `L-meta-1393` lease is `STALE` (410), no branch/commit/PR; researcher moved the `sorry`-ending scaffold out of the submittable path | `viche-state/pnp/gaps/L-meta-1393/state.json`; researcher board comment `sha256:fvCLxJDY…` (23:16Z) | Broker/Executive reconcile honestly; no submission of an unfinished proof. |
| `cli.py acquire`, `--hard`, `--another` exit 1 with `DeskError: desk next is missing gap/lease keys` (`desk.py:122`) while the desk returns the normal empty-frontier `{"gap":null,…,"retry_after_s":300}` | Researcher board comment `sha256:fvCLxJDY…` | **Executive** repair via Act 31; a normal "all gaps held" response must not be an error. |
| Earlier bootstrap blockers (CLI relative import; `branch_for` vs `BRANCH_RE`) remain in the unpublished bootstrap worktree; its agent is now stopped | Prior audit record `records/FOUNDER-INTAKE-2026-11-23-pnp-bootstrap-live-audit.md` | **Executive** owns repair/integration after takeover; no completion claim. |
| `founder/pnp-leaderboard-20261123` worktree `/home/lubko/viche-pnp-leaderboard-20261123` has UNCOMMITTED changes (`M government/executive-cycle.sh`, `missions/pnp/README.md`, `cycle.sh`, `mandate.md`, `status.sh`; `?? missions/pnp/leaderboard.py`, `status.py`, `tests/pnp-leaderboard-smoke.sh`) on HEAD `1fc9605b` (same as main) | `git worktree list`, `git status` in that worktree | Poller/trends/staffing work is **not integrated into main**. Preserve it; Executive reviews and lands via Act 31 with tests, rather than duplicating or discarding. |

## Durable mandate — owners and next falsifiable actions

| # | Obligation | Owner | Next falsifiable action |
|---|---|---|---|
| 1 | Exclusive Executive ownership of research staffing; takeover drill retiring prior manually seeded workers; independent replenishment, no cap, recover from low staffing; retain SoringP1/resources. | **Executive** c1e00002/c1a00002 | Show its own `antonina agent new`/`run` launches with worktrees and prompts, a dated handoff, and a post-drill staffing observation; never a bare claim that existing agents suffice. |
| 2 | Achieve and grow the checked/credited-step lead using the official export as the scoreboard. | **Executive** (research coordination), with Antonina-managed workers | Poll and save trends; report `@ottojung` rank/steps and the lead over #2 from `head.json` data at checkable timestamps; outcomes, not PR/agent counts. |
| 3 | Unblock the contribution pipeline: acquisition/desk handling, lease/PR corrections, checker throughput, bootstrap blockers; preserve signed ottojung publishing. | **Executive** | Fix the `desk.py:122` empty-frontier misclassification and the two bootstrap blockers; pass actual-CLI and generated-branch tests; land via Act 31; genuine checked proof before any PR claim. |
| 4 | Integrate the leaderboard poller/trends/staffing work from `founder/pnp-leaderboard-20261123`. | **Executive** | Preserve uncommitted work; independent review + Act 31 tests; record the scoreboard source and trend retention; no unreviewed cutover. |
| 5 | Intake, mandate record, public acknowledgement, receipts. | **Clerk** c1a00001 | This record, MANDATES M-033, updated handoff, board comment, empty receipt. No law, ballot, agent mutation, gate waiver or completion claim. |

## Non-actions and honesty constraints

- No agent was launched, restarted, steered or retired by this intake; the running researcher and all in-flight work are preserved.
- No law enacted/amended, ballot cast, office activated, gate waived, PR opened/merged, proof claimed or model/provider prescribed (Antonina owns selection).
- Local compilation, an unmerged PR or a local scoreboard file is not a checked/credited step; the official export is the metric.
- Standing issue stays OPEN; this record does not close the implementation issue or declare the mission complete.

## Evidence references

- Full issue `IL6wUXaBGXiOmp4aAI8B4c-possesses` (6 messages) read this pass; current `/var/lib/lubko/wd/viche/AGENTS.md` and `government/LAWS.md` read this pass.
- `https://data.pequalnp.com/head.json` (generated_at 23:31:12Z) and `https://data.pequalnp.com/data/contributors.4e5952e34416.json`, fetched 23:32Z.
- `antonina agent status --id … --json`; `viche-state/pnp/gaps/L-meta-1393/state.json`; board comments `sha256:htGXivX…`, `sha256:fvCLxJDY…`.
- Worktree/branches as above; prior records `records/FOUNDER-INTAKE-2026-11-23-standing-pnp-full-protocol.md` and `…-pnp-bootstrap-live-audit.md`.
- Constitution: `/var/lib/lubko/from-host/viche-constitution/CONSTITUTION.md` (supreme; unchanged).

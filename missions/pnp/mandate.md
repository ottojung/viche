## Standing Founder priority — autonomous P vs NP contributions (2026-11-23)

The Founder authorized an INDEFINITE external research mission on billy-dev,
tracked by Antonina board issue IL6wUXaBGXiOmp4aAI8B4c-possesses.
**NEVER close that standing issue until the Founder explicitly revokes the
mission.** The bootstrap issue R4WYVaWyRxoD911soUtcAo-sciatic may be closed
only after the independently checked delivery is deployed; the research
mission must continue without any new setup project or Founder prompting.

## Objective: lead the public, all-time contributor leaderboard

The Founder explicitly defines the long-standing performance objective as:
**maximize the account ottojung's position on pequalnp.com's public,
all-time contributor leaderboard. Once ottojung is #1, maximize and
continuously seek to INCREASE its lead in accepted, checked steps over #2.**
Competing agents can improve at any time; assess and improve the real
lead trajectory rather than claiming it can never fall. Tie-breaks are the
website's published first-proof order; prefer a strictly positive step lead.

The metric is **checked steps credited to ottojung in the site's published
immutable contributor export**, not agents launched, files written, branches,
PRs opened, GitHub Actions green, or locally compiling proofs. Refutations
count when the site credits them. Leaderboard evidence and change history:
  /var/lib/lubko/wd/viche-state/pnp/leaderboard/{latest.json,history.jsonl}
  python3 missions/pnp/leaderboard.py status
  /bin/sh missions/pnp/status.sh
Treat unavailable/stale data as UNKNOWN, never zero. Recheck external credit
after GitHub's authoritative checker has accepted/merged contributions.
Current 2026-11-23 public baseline: ottojung absent/unranked (zero checked),
first 53 checked steps, second 46. This is a baseline, NOT a fixed threshold:
poll the live source and adapt to leaderboard movement.

## Ownership, staffing, and continuity — Executive only

**ONLY Viche Executive may create, start, restart, steer or retire research
agents.** Founder's external assistants, maintenance automation, Judiciary,
researchers and publisher do not launch research agents. The Founder may
specify objectives and inspect the system without seeding worker sessions.
Do not infer Executive staffing effectiveness from agents started by an
external operator. Require evidence that Executive independently recognizes
zero/insufficient useful staffing and replenishes it through Antonina.
Record the Executive's decisions and worker assignments durably.

For every Executive cycle:
- Inspect the exact public rank/score, the #1 and #2 totals, gap, and changes
  since earlier measurements, plus desk leases, research experiments and PRs.
- Dispatch and replenish **multiple genuinely independent mathematical
  fronts** (Lean formalization, counterexample searching, proof reasoning,
  desk gap claims and PR corrections as appropriate), allocating concurrency
  by marginal verified contributions, host resource availability and current
  independent tasks. ONE researcher is not a satisfactory steady state while
  multiple valuable fronts are available. Do not hard-cap worker count or
  spawn redundant agents just to increase a counter.
- Take over the preexisting managed agents/worktrees under the roster
  /var/lib/lubko/wd/viche-state/pnp/swarm/agents.json if useful, or retire them
  and replace them yourself. Never expect an outside operator to restart them.
  Check their actual Antonina states, output, remaining leases and dependencies.
- Prefer claimable, well-scoped proofs with high expected accepted-step
  throughput; keep a portfolio of harder/high-value results and rigorous
  refutations where useful. Demand completed exact Lean proofs or reproducible
  counterexamples, honest releases, and measurable progress. Track verified
  accepted steps per time and resource use; avoid duplicate expensive builds.
- When all desk leases are held or claim service is cooling, DO NOT go idle:
  investigate published open claims and prepare proofs or bounded searches,
  then promptly obtain official leases once available; never submit an
  unleased gap against the project's rules.
- Investigate any slowdown in credit rate or lost leadership: stalled workers,
  model access, invalid checker, forgotten claims, unnecessary work, duplicate
  efforts, excessive resources, or stalled upstream verdicts. Correct the
  causes as part of normal Executive work without asking the Founder to
  operate agents.

Standing mission stays OPEN even while #1 or its lead is growing; this is
an ongoing competition and never a one-time completion condition.

Exact project rules and execution contract:
missions/pnp/PROTOCOL.md.
Operator interface from the canonical checkout:
python3 missions/pnp/cli.py status|acquire|beat|release|submit|reconcile.
Desk lease reconciliation and public leaderboard observation are run
by the independently nonblocking missions/pnp/cycle.sh from generic boot; the Executive still owns research,
failed-work decisions and dispatch. Do not launch a competing scheduler.
The publisher hardcodes Otto Jung <otto.jung@vauplace.com>, his GPG signing
subkey 08AF2726387BD4A4C87DF1821BEDDF96D7B1BA2B and the exact fork and
upstream PR destinations. Researchers must not open PRs with generic gh. They must directly invoke
`python3 /var/lib/lubko/wd/viche/missions/pnp/cli.py submit GAP FILE` as soon as
a complete candidate exists. No redundant local full checker, approval handoff,
or waiting for an Executive cycle: the detached deterministic publisher checks
the local build, signs and submits. Resume or correct failures promptly.
Persist evidence and follow the mission through mandatory host restarts.
Quiet periods, checker faults, depleted research packets, or one merged PR
never end this assignment.

## Race-critical work (Founder priority)

Choose expected accepted steps per resource-hour. Ask the desk for ordinary
work first; use its documented hard offers only if concrete mathematical
progress justifies the investment. The desk chooses the lease; do not churn
leases or attempt undocumented requests. Held counts are competition signals,
not PR counts or proof of acceptance. A rival PR alone does not invalidate a
promising proof. Reassess remaining work using actual progress, competition,
and claimable alternatives, not a fixed timer or agent headcount.

Before lengthy work, and between bounded computation or proof-development
steps, each worker runs the cheap local command:
  python3 /var/lib/lubko/wd/viche/missions/pnp/cli.py guard GAP --lease LEASE
Supply the assigned lease identifier at dispatch. A stop decision means finish
cooperatively, preserving the proof and concise reusable findings. A wait
means check current state with the coordinator, not a crash or indefinite
busy loop. Never start another expensive search on a terminal lease. An
unknown snapshot never authorizes cancelling a live worker. Executive checks
workers_on_terminal_gaps and active_lease_gaps early each pass, not only the
worker count; it alone handles reassignment. Do not wait for PR verdicts to
replenish research.

Use mathematical locality: assign related problems to a worker with relevant
prior results when useful, and reuse concise proof fragments, known lemmas,
failed approaches and checked examples from existing worktrees. Do not create
new documentation deliverables or ask workers to re-read all historical logs.
Start with the gap's own sketch and exact statement. Prefer narrow imports
for scratch development, then hand the full required candidate to submit.
Avoid full local checker runs and redundant full Mathlib loads. While a
publisher build is pending, prioritize that finite job over speculative local
CPU/memory-heavy search. Keep independent model-bound reasoning productive.

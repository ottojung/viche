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
- Concentrate parallel mathematical work on the SINGLE research_focus from
  mission status. Keep the other leases as reserves. Delegate genuinely
  independent approaches (construction, refutation, sublemmas, Lean
  formalization and proof reuse) on that same gap. Allocate as much useful
  concurrency as resources permit; do not duplicate expensive builds or
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

Choose expected accepted steps per resource-hour. The deterministic lease allocator
asks for ordinary work first and fills remaining capacity with hard offers. The desk chooses the lease; do not churn
leases or attempt undocumented requests. Held counts are competition signals,
not PR counts or proof of acceptance. A rival PR alone does not invalidate a
promising proof. Reassess remaining work using actual progress, competition,
and claimable alternatives, not a fixed timer or agent headcount.

Before lengthy work, and between bounded computation or proof-development
steps, each worker runs the cheap local command:
  python3 /var/lib/lubko/wd/viche/missions/pnp/cli.py guard
Run from the immutable assignment workspace returned by the preparation command below. A stop decision means finish
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

Full Mathlib/checklemma processes can exhaust the machine: the local full
checker is NOT a publication prerequisite. Do not run it on billy-dev.
Use the publisher for the required full build, not multiple simultaneous
full-import Lean scratch processes. Use minimal scratch imports, bounded
search subprocesses and small test inputs. A memory-deferred publisher
preserves the proof and retries; do not start a competing full build.

## Shared Lean compilation queue

All P vs NP local Lean computation uses the shared queue, including research.
From the Lean directory run:
  PYTHONPATH=/var/lib/lubko/wd/viche python3 -m missions.pnp.compile -- lake build +MODULE
For small scratch files with narrow imports:
  PYTHONPATH=/var/lib/lubko/wd/viche python3 -m missions.pnp.compile --light -- lake env lean Scratch.lean
Use heavy (the default) for any full Mathlib import or unknown memory demand.
Do not invoke raw lean/lake/checklemma for research or start competing full
builds. Up to two light compilations may overlap when memory permits; heavy builds
are exclusive, and publication has admission priority. Exit 75 means a
resource/lease deferral, not a rejected theorem. Do not busy-retry; pursue
independent reasoning or simplify the proof. A heavy build may use available
RAM above the host reserve without a fixed per-proof cap. A resource-blocked
publisher preserves its candidate and waits for increased headroom or new
proof bytes. Executive owns reassignment; no process kills of researchers.

Research admission waits only briefly (at most 15 seconds) before returning
75, so a queued compilation does not occupy an agent tool call indefinitely.
Legacy raw PnP compiler processes are recognized as an admission constraint.
The Executive must retire or cooperatively reassign obsolete workers rather
than allow them to restart unnecessary full checkers.

## Revocable computation (Founder priority)

The deterministic mission watchdog runs independently of Executive sessions.
It revokes only identifiable Lean/lake/checklemma subprocesses in canonical
gap worktrees whose durable assignment has ended (STALE, RELEASED, ACCEPTED,
PR_OPEN). It never terminates or launches agent sessions, touches unrelated
worktrees, or acts on missing/unreadable state. Exact gap state and process
identity are checked under the assignment lock; a fresh reacquisition is
not cancelled on old evidence. Research commands use their immutable workspace binding with the shared compiler entry point. The Executive remains
sole authority for researcher reassignment and must do it early, before
lengthy deliberation. Preserve proof files; no repeated compilation of a
settled gap. Computational cancellation is not a mathematical verdict.

## Work-conserving research allocation

Executive: after a successful acquire (or when adopting a live assignment),
run `python3 /var/lib/lubko/wd/viche/missions/pnp/cli.py assignment GAP`.
Use its returned absolute cwd for Antonina new/run. It prepares an isolated
pinned checkout and shares only pinned package dependencies. Never relabel
a previous attempt after reacquisition. The guard and compiler infer the
immutable assignment from cwd; do not type or expose lease IDs. Use the
same workspace for submit and preserve earlier attempts for reuse.

Prefer incremental formalization and explicit reductions to known theorems.
Before investing in an open-ended lower bound, identify a concrete proof
route, its nearest checked lemma, and the missing inference or certificate.
Reuse the previous research notes for the same or related problem rather
than repeating failed SAT encodings. The allocator fills capacity with hard gaps when ordinary work is unavailable.
The Executive identifies the best proof route for each assignment and stops
work that has genuinely been abandoned. The desk alone chooses claimable gaps.
Do not churn leases or release on a speculative difficulty judgment.
Reassess work at natural evidence checkpoints, not arbitrary deadlines:
a successful sublemma, a failed reduction, new rival evidence, a search
budget exhausted, or a candidate. Keep the highest-yield route moving.

The Executive first addresses an unstaffed research focus and obsolete
assignments. Reserve gaps require no researchers. After these allocation decisions,
delegate substantive investigations rather than waiting in the coordinator
session; finish the pass promptly so the next state change can trigger it.
No polling sleep inside Executive reasoning. No new review or reporting gate.


## Productive overlap while tools run

All workers follow the canonical work-conserving attention rule in
`/var/lib/lubko/wd/viche/government/AGENT-REPORTING-POLICY.md`. In particular,
a bounded SAT search can run while its owner prepares the Lean witness
verification, reasons about the graph, studies symmetry or derives a
complementary search formulation. Do not run identical searches or poll a
solver repeatedly without other useful work. Keep search scripts, job
handles, logs and exit results in the bound assignment workspace, use
unbuffered/progress output when supported, and retain a finite budget.
Check the assignment guard and incorporate new evidence at natural
checkpoints; do not start new work after the lease ends. Do not background
unmanaged Lean: use the shared compiler and respect its resource admission.
A complete candidate must be submitted promptly rather than waiting on an
irrelevant experimental branch. Executive delivers actionable mathematical
handoffs to the existing researcher promptly, preserving search progress.

## Immediate publication
Submit complete high-confidence proofs immediately with the normal submit command.
Never wait for a redundant compile before opening the PR. The publisher validates,
signs and publishes, then checks the exact published revision locally in parallel
with upstream CI. Do not submit unfinished proofs, placeholders or guesses.
Executive must promptly delegate corrections shown in correction_needed, reusing
the same open PR and the existing research artifacts. Do not treat a local check
failure as a final external verdict; do not repeat rejected identical proof bytes.

## Reusable proof infrastructure

From the bound assignment directory run:
`PYTHONPATH=/var/lib/lubko/wd/viche python3 -m missions.pnp.proofs find`
to find related checked upstream proof statements and tactics. Inspect a result
using the same command with `source MODULE`. Direct import is legal only when
the result explicitly marks it as allowed by the desk. Otherwise adapt the
reasoning into local helper lemmas; never submit another proof unchanged.
For an explicit small circuit truth-table row run `... proofs circuit --output
candidate.lean` (the full command uses the same PYTHONPATH above). The generator
independently checks every input, creates a statically validated candidate only
for recognized shapes, and never submits or claims a lease. Review all clauses
and use ordinary submit once confident. These are deterministic research tools,
not institutional gates. Prefer using them before spending model turns on
repeated Lean boilerplate.

For small existential monotone edge-function circuits use the same command with
`synthesize --output candidate.lean`. It searches shared star/biclique
expressions, independently checks every Boolean input, enforces the gate
budget, and emits a self-contained candidate. A failed search is not evidence
of nonexistence. No generator claims a lease or publishes a proof.

## Compilation duration

Managed Lean compilation has no elapsed-time deadline. A build may continue
as long as its assignment or exact published revision remains relevant and
memory is safe. The short resource-admission wait is not a compilation
deadline. Do not wrap useful builds in wall-clock timeout commands or use
the removed compiler timeout option. For long compilations, use a managed
detached process with a durable log rather than blocking an agent tool call.
Cancel obsolete work, not merely old work.


## Continuous parallel research support (Founder priority)

Optimize accepted contributions per elapsed and resource hour. Keep the
primary proof/construction owner working independently while other agents
continually seek actionable evidence for the single research focus. Do not make
the Executive search proofs, debug algorithms, or review every submission.

Executive: staff and replenish useful independent support fronts as well as
primary researchers, using the separate coverage in the mission diagnostic.
Use Antonina titles `Viche P vs NP support: knowledge`,
`Viche P vs NP support: methods`, and `Viche P vs NP support: flow`.
One agent may cover related roles (comma-separated titles, e.g.
`Viche P vs NP support: knowledge, methods`) when the workload justifies it;
parallelize distinct useful investigations when resources permit. These are
roles, not prescribed headcounts or new institutions. Support agents never
count as leased proof owners, never claim another agent's lease, and must
not edit a primary's workspace or open competing PRs. Use independent scratch
directories and existing shared proof/compile tools. Restore coverage promptly
when a support agent finishes and further useful work remains; when no
actionable work exists, finish rather than manufacture activity or poll.

- Knowledge: check exact claims and opposite conclusions against the checked
  proof corpus; inspect relevant upstream proofs, newly accepted results,
  nearby reductions and transferable tactics. Verify semantic applicability,
  allowed imports and exact checked revision. Catch obsolete work early.
- Methods: independently derive promising proof steps, counterexamples,
  structural reductions, alternative algorithms or reusable verified code;
  identify specific invalid assumptions and duplicate searches. Deliver
  concrete mathematical assistance promptly, not generic commentary.
- Flow: identify lost race time, resource contention, repeated computations,
  unattended corrections, incomplete handoffs and more productive opportunities.
  Evaluate actual marginal yield; give Executive concise evidence and a proposed
  allocation or process change when it would matter. Do not watch individual
  tool calls or demand more reports.

All support agents use, from any independent scratch directory:
```
export PYTHONPATH=/var/lib/lubko/wd/viche
python3 -m missions.pnp.support targets
python3 -m missions.pnp.support advise GAP ATTEMPT ROLE EVIDENCE MESSAGE
```
Copy GAP and ATTEMPT from targets, not a lease secret. ROLE is knowledge,
methods or flow. EVIDENCE is an exact proof link or durable artifact path;
MESSAGE is the concise substantive finding and useful next action. Put longer
proofs/code in a separate durable artifact and link it. Add `--coordinate`
only when Executive needs to change ownership, priority, resources, or stop
confirmed obsolete work. For portfolio-wide findings without a live gap, use
the existing Executive handoff queue; no new reporting system. Retain only
material findings: the latest finding per role is delivered by the primary's
existing guard command. Never wait for acknowledgment or a scheduled meeting.

The detached checked-proof scan refreshes the upstream corpus in parallel
and supplies exact syntactic statement/opposite-conclusion matches as
advice. Knowledge support still verifies matches, finds nontrivial semantic
equivalences and mathematical reuse. No match is not proof of novelty.
Neither advisory evidence nor a support outage changes guard decisions or
publication eligibility. A confirmed checked refutation ends the impossible
construction effort; retain evidence and let Executive handle assignment
release and reassignment. A rival's unaccepted PR alone is not a refutation.

Primary researchers incorporate relevant guard advice at their normal
checkpoints; use evidence critically, don't blindly execute it. Submit a
complete proof immediately without waiting for any scout, review, or Executive
approval. Executive delivers urgent coordination findings promptly; preempt
only when confirmed material benefit outweighs interruption and preserve
ongoing useful computations. Never dispatch, restart or steer an agent from
a support agent. Executive retains sole lifecycle authority.

## Continuous lease allocation (Founder priority)

The mission allocator, not model turns, maintains up to five distinct leases.
It prefers ordinary assignments, falls back to documented hard assignments,
and keeps polling even with no work. The desk chooses exact gaps; do not
attempt arbitrary ID claims. The allocator selects one stable research focus, preferring concrete,
ordinary and low-competition work among held gaps. Do not staff reserve
gaps. The Executive owns research strategy and agent starts/stops; do not
duplicate allocator polling. A formerly staffed gap is released only after
confirmed sustained absence, not because a reserve has no workers.
Incomplete roster observations, active compilers, queued candidates and
publication are protected. Preserve work artifacts. Explicit honest release is still possible
when the Executive decides a route is exhausted. No active proof is cancelled
just to make room for a more attractive offer.

## Single-gap parallel research (Founder priority, supersedes portfolio staffing)

Strive to maintain five live leases, including four intentional reserves.
Work on the single research_focus reported by mission status. Parallelize
that gap as much as useful: appoint a proof integrator and independent
researchers pursuing distinct sublemmas, proof strategies or counterexamples.
For independent writable checkouts run
`python3 /var/lib/lubko/wd/viche/missions/pnp/cli.py assignment GAP --worker LABEL`
with a distinct short label per researcher. Each checkout is bound to the
same exact lease and has independent mutable build state; no competing PRs.
Share useful evidence and partial proofs directly, not the writable checkout.
The first complete valid candidate goes straight to the publisher. When
publication owns the candidate, the allocator rotates focus to the best
remaining reserve and fills the vacant lease slot after submission.
An existing PR requiring correction is eligible as the next focus; do not
split ongoing research across two gaps just to fix a pending correction.
If the Executive abandons a focus, release it honestly and move to the next.
Do not rotate simply because another promising gap arrives; never leave
all reserves unattended until their leases expire. The automated heartbeat
renews the whole pool.

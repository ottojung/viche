## Immediate operational rule (Founder priority)

The running allocator exclusively claims leases. Never call Desk.next_gap,
the private wire operation, curl /desk/next, upstream pnp.sh next, or manual
CLI acquire while the allocator runs. All of these are mutations, not
diagnostics. Use mission status. If missing_general is nonempty, first run the baseline batch command
described below. If research_focus lacks useful parallel workers, dispatch
additional specialists.
Choose independent mathematical approaches using focus_details and invoke
the one-command batch helper:
`python3 -m missions.pnp.staff GAP --worker 'LABEL=APPROACH' --worker 'LABEL2=APPROACH2'`
from the canonical Viche checkout. Add as many distinct useful approaches as
resources permit; the helper handles independent bound workspaces, existing
agents and detached starts. No separate model turn, per-worker setup routine,
or administrative review. Only the Executive invokes this dispatch helper.
If no focus exists, do not acquire manually.

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
Record the Executive's decisions and worker assignments durably in existing
mission state and operational logs. Routine allocation, replenishment and
focus decisions do not need a new records/research report, Git commit, delivery,
integration, or review; preserve the evidence and decision reason in the
mission's existing durable state instead. Only material outcomes, consequential
orders and actual changes to the software or law require the usual delivery
process. No duplicate records or artificial approval gates.

For every Executive cycle:
- Inspect the exact public rank/score, the #1 and #2 totals, gap, and changes
  since earlier measurements, plus desk leases, research experiments and PRs.
- Maintain one general researcher on EVERY live research lease, and
  concentrate additional parallel mathematical work on the SINGLE research_focus.
  Delegate genuinely
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

The Executive first addresses missing_general across all live research leases
and obsolete assignments. Every nonfocused lease requires one general researcher. After these allocation decisions,
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


## Role-specific instructions at dispatch (Founder priority)

Every P vs NP agent invocation receives actionable instructions in its initial
prompt. Never delegate discovery to a README. The mechanical staff helper
injects instructions for general researchers, integrators and specialists.
For each support or engineering agent, Executive uses
`PYTHONPATH=/var/lib/lubko/wd/viche python3 -m missions.pnp.role_prompt ROLE --agent ID --cwd WORKSPACE --task "specific assignment"`
for dispatch after creating/reusing an idle agent. This helper inserts role
instructions into the actual agent invocation; do not send an unadorned task. Roles: knowledge, methods, flow, portfolio,
lease-evaluation, transport, adapter, benchmark. For a combined support role,
include the other role’s generated instructions in the specific task. Prefer short role-specific commands over
a long generic inventory; do not require irrelevant tool calls. Replenishment
and reassignment use the same prompt mechanism. Existing agents receive
updated guidance at their next natural checkpoint or a justified steer.

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
a support agent. The standing staffing controller executes lifecycle actions; Executive monitors and repairs it.

## Continuous lease allocation (Founder priority)

The mission allocator, not model turns, maintains up to five distinct leases.
It prefers ordinary assignments, falls back to documented hard assignments,
and keeps polling even with no work. The desk chooses exact gaps; do not
attempt arbitrary ID claims. The allocator selects one stable research focus, preferring concrete,
ordinary and low-competition work among held gaps until the portfolio
researcher makes an evidence-based decision. Every held researchable lease
has one general researcher. The staffing controller owns routine agent starts/stops; do not
duplicate allocator polling. Missing staffing is a replenishment signal,
not a mathematical release decision. The lease evaluator decides honest
releases. Preserve work artifacts and protect queued/publishing candidates.

## Single-gap parallel research (Founder priority, supersedes portfolio staffing)

Strive to maintain five live leases, each with one general researcher.
Only the single research_focus reported by mission status receives additional
researchers. Parallelize that gap as much as useful: appoint a proof integrator and independent
researchers pursuing distinct sublemmas, proof strategies or counterexamples.
For independent writable checkouts run
`python3 /var/lib/lubko/wd/viche/missions/pnp/cli.py assignment GAP --worker LABEL`
with a distinct short label per researcher. Each checkout is bound to the
same exact lease and has independent mutable build state; no competing PRs.
Share useful evidence and partial proofs directly, not the writable checkout.
The first complete valid candidate goes straight to the publisher. When
publication owns the candidate, the allocator rotates focus to the best
remaining held lease and fills the vacant lease slot after submission.
An existing PR requiring correction is eligible as the next focus; do not
split ongoing research across two gaps just to fix a pending correction.
The lease evaluator may release a genuinely unpromising gap. The portfolio
researcher may change focus. The automated heartbeat renews the whole pool.

## Cumulative research and mathematical families (Founder priority)

Maintain theorem research, independent mathematical method research, and
tool research concurrently. Method and tool researchers are not leased proof
owners and do not count toward the five baseline researchers. Executive
allocates useful independent method fronts by mathematical family and keeps
them working across lease changes. Each method front produces exact reusable
lemmas, obstructions or certificates; tool fronts produce independently
verified automation and held-out family benchmarks. Prefer results over reports.

At dispatch inject the role-specific executable workflow directly into the
initial prompt. The standing staff/continuity helper does this automatically
for bound and support roles. Workers first run pnp-research start for their
actual work packet; pnp-research guide ROLE gives examples on demand.
Do not require reading the entire mandate or a documentation quiz before
research. Measure actual adoption with pnp-research adoption, and separately
measure checked output. For explicit independent method/tool researchers,
knowledge curators and portfolio evaluators, after creating/reusing the idle agent run
`pnp-research dispatch ROLE --agent ID --cwd WORKSPACE --task "specific task"`
(or include the role text from `pnp-research dispatch ROLE` with the existing
role instructions). This is an Executive lifecycle action, not a worker tool
for launching other agents. The existing baseline and focus rules remain.

When an approach admits a useful decomposition, the proof integrator
requests exact Lean obligations with `pnp-research obligations request`
and specifies their dependencies. The standing controller assigns unresolved ready nodes
to complementary specialists; do not allocate every specialist the same
complete theorem. Keep independent approaches when useful. New focused
specialists should share the general researcher's exact pinned base. Existing
workspaces need not be reset: fork obligations and independently recheck on
another base. Check proof bodies with `pnp-research obligations solve`;
complete roots can be assembled as ordinary validated candidates. Only the
existing submission pipeline publishes. A failed check is not a refutation.

Use `pnp-research knowledge` for persistent mathematical objects and
`pnp-research yield` for empirical family-level baseline, actual graph
progress, available techniques and competition. Historical import includes
quarantined attempts. Index missed findings with `knowledge ingest`.
The guard and portfolio expose these as advisory information. Estimates do
not themselves authorize release, focus change, or publication. No extra
approval gates. See missions/pnp/research/README.md for operator details.

## Independent portfolio decisions (Founder priority; supersedes no-preemption)

Executive must maintain two distinct useful researcher roles, independently of
the proof swarm: `Viche P vs NP support: portfolio` and
`Viche P vs NP support: lease-evaluation`. Use separate Antonina agents.
Portfolio is needed with two or more held gaps; lease-evaluation with any held
gap. When a pass finishes, replenish on new assignments or meaningful new
mathematical evidence; avoid idle polling. Both use:
`python3 -m missions.pnp.portfolio inspect`
from the canonical checkout. It returns every held research lease, exact
statement, immutable attempt, competition, remaining time, artifact paths,
per-worker findings, worker identities and commands to read their logs.
Base decisions primarily on the general researchers' actual work and logs,
and on focused specialists' results where relevant. Do not substitute
independent speculative assessments for available first-hand research.

Portfolio researcher compares ALL held problems, including progress on the
current focus. Study proof corpus, actual partial proofs, obstacles, remaining
Lean work, competitor activity, and remaining lease time. Choose expected
accepted steps per remaining resource-hour. Switch only for a substantially
more promising concrete route, accounting for discarded progress and
handoff cost. No switching based solely on titles, arbitrary timer, or
ordinary/hard label. Record specific comparative arguments and evidence.
Directly decide, without Executive approval:
`python3 -m missions.pnp.portfolio switch NEW NEW_ATTEMPT --from-gap OLD --from-attempt OLD_ATTEMPT --reason 'comparative mathematical argument' --evidence 'artifact paths or exact checked lemmas'`
If the current focus is better, keep it and deliver useful findings instead.
A switch retains both leases and their general researchers. Executive promptly
moves only the extra specialists to the new focus, preserving artifacts. Do not launch
agents yourself.

Lease evaluator independently investigates the least promising held problems.
Develop actual confidence: inspect exact claim, previous attempts and useful
reductions, identify why plausible routes fail or require major new results,
weigh expected yield and replacement opportunity. Consider progress by the
active proof swarm before abandoning its focus. A difficult label, age or
one unsuccessful tactic is insufficient. If a lease is genuinely not worth
holding, directly decide:
`python3 -m missions.pnp.portfolio release GAP ATTEMPT --reason 'specific mathematical obstacles and opportunity cost' --evidence 'checked lemmas, failed route artifacts or reproducible experiments'`
Direct operator CLI release is reserved for deliberate exceptional repair;
it requires --operator-override, exact current --attempt and --evidence.
It cannot release an assignment owned by the publisher or a superseded
attempt. Routine releases must go through the independent lease evaluator;
do not mass-release live research assignments from external maintenance.
No additional approval is required for the normal evaluator path.

The allocator executes the documented reason other, preserves artifacts,
protects queued/publishing candidates, honors hard-step minimum holding time,
and refills the slot. No additional review or approval. Never release
merely because a lease is temporarily unstaffed. Both evaluators finish their passes
rather than manufacturing activity. The standing controller staffs and retires
agents, and immediately obeys a valid focus decision.

## Baseline research on every lease (latest Founder priority)

Every live researchable lease gets one persistent general researcher, with
workspace label general. This is substantive mathematics, not a reporting
job: understand the exact problem, relevant literature and checked lemmas,
prior attempts, candidate constructions and obstacles; work toward a proof.
The general researcher continues when focus moves and can submit directly.
Only the focused lease receives additional specialists. Existing proof
work is preserved; after switching, retire extra specialists on the old
focus, not its general researcher. Do not count support roles as lease workers.
When a general researcher finishes, replenish promptly while the lease is
still live. A queued complete proof is owned by the publisher instead.

The standing staffing controller replenishes missing general researchers.
The Executive inspects controller health and persistent vacancies, diagnoses
failures and changes exact-attempt policy when necessary. Routine manual
agent starts or stops are not part of the Executive model turn.
See missions/pnp/staffing/README.md for commands and fault recovery.

All bound researchers share substantial mathematical findings directly,
including promising routes, failed approaches, precise blockers and checked
proofs, from their bound workspace:
`PYTHONPATH=/var/lib/lubko/wd/viche python3 -m missions.pnp.support finding --evidence 'artifact or checked lemma' --message 'concrete result and next step'`
The existing guard delivers research_findings from peers on the same exact
lease, including the general researcher. Keep full artifacts in workspaces.
Do not generate empty progress reports. Evaluators use portfolio inspect to
read these findings and the actual agent logs; they should seek clarification
or more mathematical evidence when necessary, not impose an extra review gate.
The allocator must never infer mathematical abandonment from agent absence.


## Standing Executive continuity order (Founder priority, supersedes vacancy holds)

Founder directive (2026-11-25): routine staffing is programmatic and
independent of the Executive model and branch. The standing staffing
controller reconciles every exact desired position continuously. The
Executive monitors, debugs, and adjusts policy; the controller exclusively
owns routine research-agent starts, replenishment and cooperative retirement.
Only the existing allocator claims leases; the independent evaluators own
evidence-based allocation decisions. There is no manual staffing fallback
that competes with the controller.

Every researchable lease has an actively reasoning general researcher.
A completed bounded pass is NOT a reason to leave a reserve empty. Reuse the
workspace and prior findings; change approach or give the lease evaluator
specific evidence of exhaustion. Only a valid release, publication, or
demonstrated resource/model blocker ends this obligation. Prior records holding
vacancies until a new idea appears are superseded. The standing allocation
order also supplies an integrator and at least one independent alternative when
those fronts are uncovered, and a correction owner when the selected PR needs repair.
These are starting roles, never a maximum; the Executive may declare additional
useful exact-attempt approaches in controller policy. Support passes are replenished on new assignments
or substantive primary evidence, not identical status polling. No additional
report, approval or publication gate is introduced.

Use the shared bounded finite-search tool (proofs search) for suitable
circuit questions. Verify every witness against the full truth table; an
UNSAT search is only evidence for its exact encoding and is not a checked
Lean refutation. For difficult transplanted/generated proofs, use managed
compilation as early as useful, especially before risky publication, without
requiring redundant full checks for a complete high-confidence proof.


Parallel formalization: integrator identifies exact missing lemmas and splits
them into independently testable pieces. Each specialist can snapshot a helper
using `python3 -m missions.pnp.proofs share FILE --message RESULT` (from the
bound workspace, with canonical PYTHONPATH). Peers retrieve paths and exact
content digests with `proofs fragments --all-attempts`. These immutable
sources survive agent exits and new leases; status is self-described, never
an assertion of kernel checking. Use narrow scratch imports and the managed
light queue when possible; the integrator checks the combined exact file.
Proof reuse hints in `proofs find` include relaxed conclusion/hypothesis
matches; a high score is NOT a proof of implication.


## Research capability awareness

The live tool inventory (`python3 -m missions.pnp.tools`, with the canonical
town PYTHONPATH) is part of every assignment, not a one-time announcement.
Each guard reports the tool revision and discovery command. A changed revision
means inspect the applicable new capabilities before doing redundant work.
Cheap automatic preflight runs separately for every live lease; its candidates
are not kernel-checked or automatically published. Researchers should review
and use them promptly. Engineering deliveries that introduce tools must also
update the inventory with actionable examples, applicability and limitations.
Use `tools --usage` for attempt-scoped observed CLI invocations; never infer
proof success from invocation. Use evidence of actual tool use and successful proofs, not mandatory reports
or ritual invocations, to evaluate adoption. Persistent tooling engineering
continues independently of any single lease.

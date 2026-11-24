# P vs NP: executable mission and publishing protocol
Founder task design, 2026-11-23. Execution host: billy-dev.

## Authority and lifetime
Standing board issue: IL6wUXaBGXiOmp4aAI8B4c-possesses.
Implementation issue: R4WYVaWyRxoD911soUtcAo-sciatic.
The standing issue remains open until Vitalik explicitly revokes the mission. No idle period, checker fault, single PR, or successful setup closes it. Implementation issues may close individually only after independently evidenced acceptance tests. The ongoing research loop remains part of ordinary Viche Executive scheduling. No other host may run Viche agents. Preserve Viche resource policies and current Founder-authorized mission scope.

## Precise interfaces
Upstream: brilliant-hq/pequalnp-proofs, base branch main.
Fork: ottojung/pequalnp-proofs.
Desk: https://pequalnp.com/desk with documented next/beat/release endpoints.
Instructions: https://pequalnp.com/join.txt and upstream CONTRIBUTING.md (live version takes precedence).
Authenticated CLI: /home/lubko/.local/bin/gh-pequalnp (loads public_repo token).
Commit identity: Otto Jung <otto.jung@vauplace.com>.
Required signing subkey: 08AF2726387BD4A4C87DF1821BEDDF96D7B1BA2B.
Public key registered with GitHub; local noninteractive signing tested on 2026-11-23.
All proof artifacts are single UTF-8 .lean files at their EXACT desk-provided path.

Implement the mission as one small, nonfatal subsystem in the Viche repository, suggested files:
  missions/pnp/{cli.py,desk.py,state.py,validate.py,publish.py,reconcile.py}
  tests/pnp-*.py
and durable state under /var/lib/lubko/wd/viche-state/pnp/.
Keep all shell scripts POSIX /bin/sh as required by Viche.
Use Python for coordination; Lean proves mathematics; Antonina manages all AI workers. Do not introduce a new model backend, competing scheduler, or a new constitutional service. Use normal Act 31 delivery into Viche main.

Define the stable operator interface:
  python3 missions/pnp/cli.py status
  python3 missions/pnp/cli.py acquire [--hard]
  python3 missions/pnp/cli.py beat <gap-id>
  python3 missions/pnp/cli.py release <gap-id> <reason>
  python3 missions/pnp/cli.py submit <gap-id> <candidate-file>
  python3 missions/pnp/cli.py reconcile
The exact file structure can vary only if the commands and behaviors remain equally clear and tested.

## Responsibilities (do not conflate)
1. **Viche Executive/research coordinator** chooses whether to invest effort and dispatches independently chosen mathematical approaches to Antonina-managed workers. The automatic allocator requests ordinary gaps first, then hard gaps to fill all available lease slots. No numeric cap on researchers except the desk's active lease limit and actual resource constraints.
2. **Desk broker** exclusively owns desk claims/lease renewals/release/reconciliation for the ottojung handle. Research agents do not independently consume leases. Max five active leases under the current desk rule; every researchable lease has one general researcher; only the selected focus receives additional specialists. Re-read desk docs on startup, rather than trusting old pnp.sh comments.
3. **Research workers** produce Lean candidate files, mathematical arguments, and negative results. They never call authenticated GitHub mutating operations as part of their task. They may read public repositories, use Lean, and communicate with the coordinator. A candidate is input data, not an approved Git commit.
4. **Publisher** is a deterministic program, not a reasoning agent. It is the only *supported workflow* for authenticated repository mutations. Its parameters are only gap ID and local candidate filename. It never accepts a repository, URL, PR target, author, committer, signing key, shell command, or branch from the worker. It signs and constructs the commit itself.
5. **Reconciler** monitors the desk, local state, fork Git objects, upstream PRs, and checker verdicts; schedules corrections and recoveries without duplicating submissions. It does not mistake a good PR checker result for mathematical novelty.

This is attribution/workflow control, not OS security hardening: existing lubko UID can technically read its own credentials. Do not spend the mission budget adding user/container isolation unless an actual blocker demonstrates the need.

## State machine and recovery
Store one atomically written state record per gap ID, with a file lock:
 gap ID, exact desk statement/module/path/imports, lease ID/expiry and source timestamp,
 pinned upstream base SHA and Lean toolchain, researcher assignments, candidate digest,
 worktree/branch name, signed commit SHA, PR number/URL, external verdict,
 retry/failure reason, last successful reconcile, and full append-only event evidence.

Valid states: DISCOVERED -> LEASED -> RESEARCHING -> CANDIDATE_READY ->
 LOCAL_CHECKED -> SIGNED -> PUSHED -> PR_OPEN -> {ACCEPTED, REJECTED, FAULT}.
REJECTED returns to research/edit using the *same PR* where appropriate.
A gap can become RELEASED or STALE, without losing its research record.
Write-ahead intent before external effects. Recovery always queries remote ground truth
before retrying. A process death, host reboot, timeouts, network failure, lost
acknowledgement, or token outage must never result in a duplicate PR.
If a branch is pushed but PR creation fails, reconcile discovers branch and finishes.
If PR exists but lease release failed, reconcile records PR and retries idempotently.
If the lease expires before submission, do not submit without checking current desk
gap availability. If a PR is already open, monitor it regardless of lease expiry.
Rate-limit desk operations and back off on temporary 429/5xx responses.
Lease heartbeat must run every <=10 minutes while held (or more frequently if the live
docs require), independently of researchers; after restart recover or release stale leases.
No polling loop may crash, block, or be necessary for the Viche town's overall liveness.

## Publisher: exact validation order
Reject any gap ID not matching the published gap-ID grammar. Fetch public metadata
independently from the desk; verify it is still open and the stored lease pertains to it.
Read candidate content *as data*, never execute a script from candidate or trust its Git
metadata. Enforce upstream CONTRIBUTING.md including path, UTF-8, <=512KiB,
imports, theorem/statement equivalence, checker restrictions (no sorry, added axioms,
native_decide, unsafe commands), and exactly one Lean proof file.
Use a fresh isolated Git checkout/worktree based on a pinned upstream main SHA and
a new branch unique to the leased gap. Never use untrusted candidate worktree Git hooks,
configs, pre-existing branch, or commit history as submission input.
Submit complete, high-confidence proofs immediately after static validation and lease
confirmation. Do not delay signing, pushing or PR creation for local compilation.
After the PR opens, independently verify that exact committed revision with the
managed compiler unless matching successful managed build evidence already exists.
A local failure is a correction signal, not an authoritative rejection. Correct
the same open PR with a new signed commit; never open a second PR for the gap.
Reconcile only authoritative verdicts for the current PR head, and require merge
for ACCEPTED. Do not run a redundant full local authoritative checker. A worker hands a complete
candidate directly to the publisher via submit; no additional Executive approval
or researcher-side full checker is needed. Snapshot the candidate and start a
detached, per-gap locked deterministic publisher immediately. Recover interrupted
publication via the normal mission cycle; a dead process cannot leave a held
publisher lock. Failed source proofs can be corrected on the same live lease.
Stage only the independently approved exact path. Verify one added file, no other
changes, and exactly one new commit relative to the recorded base.
Set author and committer explicitly:
 Otto Jung <otto.jung@vauplace.com>.
Use Git GPG signing subkey EXACTLY:
 08AF2726387BD4A4C87DF1821BEDDF96D7B1BA2B!
No unsigned, unverified, alternate-key, alternate-name, or alternate-email commit
may be pushed. Before push verify git verify-commit, %G? good signature, %GF exact
signing subkey fingerprint, and inspect author/committer directly.
Set push remote *internally* to ottojung/pequalnp-proofs only. Before any mutation,
verify authenticated gh account is ottojung and allowed remote/branch.
Push the one signed commit as a new uniquely named branch. Verify GitHub API
commit.verification.verified == true for the exact pushed SHA. If false, STOP
without opening a PR and record the reason.
Before opening PR, search upstream existing open/closed PRs for this exact
head branch and gap ID. If already present, reuse its ID; never open duplicates.
Only create PR to brilliant-hq/pequalnp-proofs, base main, title gap ID,
head ottojung:<branch>. Then GET created PR and verify author == ottojung,
head repo == ottojung/pequalnp-proofs, base repo == brilliant-hq/pequalnp-proofs,
base ref == main, changed file list exactly one added proof, PR commit list
contains exactly the expected signed SHA, GitHub verification == true.
If post-create validation fails, report and stop automated mutations; do not
hide the discrepancy. Never merge, close, comment on unrelated PRs, change settings,
delete branches as incidental cleanup, or operate on other repositories.
For an allowed correction, sign new commit(s) and prove every PR
commit beyond the upstream base is signed and attributed to ottojung before updating.

## Research program (standing)
At each normal Viche executive scheduling pass: reconcile first, inspect current
assigned research, recent checker verdicts, math bottlenecks and costs, then choose
useful next steps. Active work should not be preempted simply for a new gap.
Use independent thinkers / constructive provers / adversarial counterexample searches
as needed, but verify proof quality with the Lean kernel and upstream authoritative
checker. Counterexamples may be valuable; use the desk's documented refutation
submission or release mechanism. Failure to prove a gap is a result worth recording;
release it with the documented honest reason and move to a useful alternative.
When there are no claimable gaps, periodically try again or pursue independent
preparatory mathematics without manufacturing busywork.
Keep local Lean/Mathlib caches shared; do not launch duplicate bulk builds on the
4-core / 15GiB host. Keep disk bounded, preserve current unrelated town workload.
Only send substantial milestones or verified blockers to Founder-facing channels.

## Required test scenarios, in order
1. Token/identity preflight works from a fresh noninteractive process (gh-pequalnp).
2. GPG key signs without prompt; Git verifies the exact subkey fingerprint and
   configured identity; GitHub recognizes the key. Confirm verified email.
3. Offline fixtures reject: unsigned commit, other GPG key, author/committer mismatch,
   wrong repo/base, extra files, unapproved import/statement, sorry, expired lease,
   duplicate PR, failed remote verification and ambiguous external response.
4. Test interruption/restart separately after LEASED, SIGNED, PUSHED and PR_OPEN.
5. Unit tests mock desk/GitHub APIs; no fake PRs on the real upstream.
6. Use a real desk-assigned mathematical gap and get a genuine checked proof.
   Push the signed commit and open a REAL PR as ottojung without manual intervention.
   Record PR URL, verified GitHub commit status, exact one-file diff, checker verdict.
7. Show that a rejection is fixed in the same PR with valid signed commits, and
   that a clean restart has no duplicate PR or abandoned lease.
8. Land implementation into Viche main via Act 31. Verify normal Viche scheduling
   actually continues the standing mission after the implementing agent exits.
   An implementation issue can close after these checks, but the standing mandate
   cannot close without an explicit later Founder instruction.

Do not report agent setup, branch push, an unmerged PR, or a merely local
compilation as a mathematically accepted contribution.

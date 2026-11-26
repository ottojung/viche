# Executive decision — sanctioned local pre-lease proof-check service (billy-dev only)

Date: 2026-11-26T22:38Z. Office: executive (billy-dev seat worktree).

Authority: Founder handoff `H-1795732505-1c6c` (`assigned-by: founder`, created
2026-11-26T22:35:05Z) and the Founder competitiveness directive of the same
date. This is an operational decision under existing Executive authority. It
does not amend the Constitution, enact law, change a ballot, seat or CI
workflow, authorize remote compute, or activate any service. Status:
**design DECIDED and conditionally AUTHORIZED; service DISABLED, not activated.**
Activation requires the review gate in section 5.

## 1. Problem this decision solves

- The independently proposed host-boundary repair `cbf00ac3` (delivery
  `pnp-host-boundary-local-only-20261126`, proposed 22:32:54Z) deliberately
  routes Lean verification through `missions/pnp/lbcert/checklocal.py`, which
  requires `assignment.binding(cwd)`: an exact *active bound workspace* for a
  held lease. Candidate bytes that are not yet leased cannot be kernel-checked,
  so `have=proof` stock (`missions/pnp/lbcert/ready.py` exact receipt markers)
  is zero. That is a competitiveness bottleneck, not a checker outage.
- A unittest fixture with fake signed state for `L-meta-582` (fake `CANDIDATE_READY
  -> LOCAL_CHECKED -> SIGNED`, `sha = aaaa…`) leaked to production through
  multi-module `unittest` import order. It was removed under locks and
  quarantined at `pnp/quarantine/test-fixture-L-meta-582-1795732358`
  (manifest sha256 `7ddb0e21…`). Fixture-scope fix `acd0a372` is proposed as
  `delivery/pnp-fixture-scope-20261126`. Any pre-lease checker must be
  structurally incapable of repeating that leak.

## 2. Decision

Authorize **one** sanctioned local pre-lease proof-check service, implemented by
the operator as a disabled-by-default path, under the exact contract below.
No other agent may create a competing checker, and no path may bypass Act 31.

### 2.1 Host and workspace

- **billy-dev only.** Every out-of-host proof transport is unconditionally
  refused by `missions/pnp/host_boundary.py` (`remote_transport_disabled`,
  exit 9). No relay/marceline request, remote lean build, remote sibling/plugin
  compile, remote polling or async submission. GitHub-hosted Actions CI is a
  separate host allowed by the Founder and is out of scope for this service.
- A **dedicated private clean sparse worktree**, distinct from the canonical
  Town checkout and from every lease/worker checkout, checked out once at an
  **exact public upstream commit (40-hex)** pinned into the service
  configuration and echoed into each receipt. No fetch, pull, merge or write
  to that worktree during a check; the candidate file is staged in a temporary
  path inside it and removed after the check.
- A **private state root**, separate from the production `PNP_STATE_ROOT`.
  All operator tests run under `suite-env` with a scratch state dir. Fixture
  state can never be read as a lease, a desk claim or a production receipt.

### 2.2 Shared admission and bounded time

- The **only** Lean subprocess is the canonical managed compiler:
  `PYTHONPATH=/var/lib/lubko/wd/viche python3 -m missions.pnp.compile -- ...`
  (`--light` for narrow imports, heavy otherwise), admitted through the shared
  compile queue. Exit 75 is a resource deferral, never a theorem rejection;
  no raw `lake`/`lean`/`checklemma`, no competing full build, no unmanaged
  background process. Publication retains admission priority; research and
  this service share the remaining admission honestly.
- **Bounded job:** a finite per-check budget on the pre-lease wrapper, a
  per-candidate byte cap of 512 KiB (matching `ready.py`), and resource-based
  admission. On exhaustion or deferral the service preserves the candidate and
  returns `deferred` or `unavailable`; it never returns a mathematical verdict
  and never leaves an unowned process. A deferral is not a failed check.

### 2.3 Exact candidate, static validation and independently enforced axioms

- The candidate is **data, never executed**. Its SHA-256 over the exact bytes
  is the identity; declared gap/base are metadata, not evidence.
- **Static validation** uses `missions/pnp/validate.py` as-is: no `sorry`,
  `admit`, `axiom`, `unsafe` or `native_decide`; allowed imports and options
  only; no hash commands or ambiguous declarations. Any ambiguity fails closed.
- **Independently enforced allowed axioms:** a compiler-enforced `#print axioms`
  guard (the rule implemented in `missions/pnp/research/obligations.py`), run by
  Lean on the exact candidate bytes, rejecting any axiom outside exactly
  `{propext, Classical.choice, Quot.sound}`. The result must come from the
  compiler, not from candidate text, a self-report, or a cached value.
- A receipt is accepted only when `ready.exact_receipt` holds: `status == ok`,
  `compiled is True`, `sha256 == SHA256(exact bytes)`, and `checked_base` is the
  exact pinned 40-hex upstream commit. The marker is written only into the
  private state root. Promotion of a verified receipt into production
  `have=proof` stock, if any, is a **separate reviewed step**, not an automatic
  side effect of the checker.

### 2.4 Strict non-effects

- No `cli.py acquire/beat/release/submit`, no `desk.next_gap` or private wire
  operation, no lease mutation, no PR or GitHub API write, no network call,
  no relay contact.
- No agent is launched, steered or retired by this service; no competing worker
  is created.
- A check result is a kernel-check receipt for **exact bytes only**. It is not
  an external step credit, not website acceptance, and a compile error is not a
  claim that the statement is false.

## 3. Why this is lawful within current authority

The Constitution assigns the Founder amendment power and requires transparent,
auditable operation. The Founder handoff expressly authorizes a managed
pre-lease checker under the stated limits and requires review/authorization
before activation. This decision stays inside that delegation: it creates an
operational service design, not a law, and it preserves the Founder-owned
constitutional boundary and the Act 21/31 quality and delivery gates. The
 standing staffing controller, allocator, lease evaluator and portfolio
researcher keep their existing exclusivity; this service changes none of them.

## 4. Coordination and dependencies

- **Host-boundary dependency:** the service must be built on the host repair's
  unconditional refusal contract (`cbf00ac3` or a clean reviewed successor).
  It must not reintroduce any relay/marceline or out-of-host path. STOP stays
  in force; only the Executive may decide its removal after exact reviewed
  deployment.
- **Fixture isolation:** `acd0a372` (or a clean successor) must land first. Its
  isolation test must show that a test fixture cannot be promoted into a lease
  or production receipt regardless of unittest import order.
- **Hybrid:** consolidate onto the host repair lineage
  (`operator/pnp-hybrid-rebased-20261126`, based on the host repair parent);
  any older hybrid branch (e.g. `operator/pnp-hybrid-fresh-20261126`) must be
  statically scanned for remote reintroduction before it is used or relanded.
  No hybrid may carry remote transport bytes.
- All changes reach `main` only through `propose-delivery.sh --office …` and
  the Act 31 integrator. No manual landing, no competing delivery, no bypass,
  no manual lease/staffing action. Recovery Steward retains full-suite and
  consolidation throughput ownership.

## 5. Activation gate — all required, none satisfied at decision time

1. `cbf00ac3` or a clean successor is independently reviewed and deployed on
   canonical main; STOP decision remains with Executive.
2. `acd0a372` or a clean successor is landed and fixture isolation is verified.
3. The consolidated hybrid is rebased onto the host repair and no hybrid branch
   reintroduces a remote transport path (static scan + tests).
4. The operator's disabled-by-default implementation is proposed via Act 31,
   independently reviewed, its exact-candidate suite is green under the normal
   bound (no wall-clock bypass), and an explicit Executive enable flag is
   recorded with its authorization.

Until all four hold, the flag remains **off** and no pre-lease check is run.
This document authorizes the design and the gate; it does not enable it.

## 6. Evidence checklist for the independent reviewer

- Pinned worktree is private, clean, sparse, and at the exact declared upstream
  sha; no production checkout is touched.
- Shared compiler admission is used; exit 75 deferral is honoured; the job has a
  finite budget and no unmanaged subprocess remains.
- `validate.py` static check and the compiler `#print axioms` allowlist both
  run on the same exact bytes; the axiom allowlist is exactly the three named
  axioms.
- Receipt identity equals `SHA256(bytes)` and `checked_base` equals the pinned
  sha; `ready.exact_receipt` is the only acceptance test.
- Static scan shows zero out-of-host transport calls and zero desk/PR mutations;
  tests run under `suite-env` with a scratch `PNP_STATE_ROOT`.
- Fixture-scope test proves a leaked fake fixture cannot become a lease or a
  production receipt; quarantine at
  `pnp/quarantine/test-fixture-L-meta-582-1795732358` is preserved.
- No law, ballot, seat, Constitution, CI workflow, agent lifecycle or remote
  compute change is included.

## 7. Resulting state

Handoff `H-1795732505-1c6c` stays open: this decision discharges only the
"decide and document the pre-lease checker" obligation. Deployment of the host
repair, landing of fixture-scope, hybrid consolidation and reviewed activation
remain outstanding and are tracked in that handoff and the existing delivery
queue. No step credit is claimed from this decision.

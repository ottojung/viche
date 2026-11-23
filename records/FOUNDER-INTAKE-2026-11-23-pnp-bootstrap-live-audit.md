# Founder intake — 2026-11-23 — P vs NP bootstrap live implementation audit

**Clerk:** c1a00001
**Recorded:** 2026-11-23T22:40Z (UTC)
**Source:** `sha256:gaie7cQgP515Y99yNJ2arZCORouN9SW06Lw9psRjM08` on `R4WYVaWyRxoD911soUtcAo-sciatic` (Execution-Host: billy-dev, explicitly assigned; Act 9.1 satisfied). This is the same standing P vs NP mandate stream as M-032.

## Founder-reported findings (reproduced read-only by Clerk)

| Finding | Clerk reproduction (2026-11-23T22:39Z, read-only) | Owner / next step |
|---|---|---|
| `python3 government/pnp/cli.py --help` fails `ImportError: attempted relative import with no known parent package` | Reproduced in `/home/lubko/viche-pequalnp-bootstrap-20261123` (HEAD `b9c3ff94`, clean worktree): exit 1 with the reported ImportError from `cli.py:16`. | **Bootstrap agent `SNpAHy9…`** (owner): make the documented CLI invocation work as specified; add a test that invokes the actual CLI command path. |
| `config.branch_for("L-meta-1393")` returns `pnp/l_meta_1393` but `config.BRANCH_RE.fullmatch(...)` is False; gitctl rejects normal generated branches | Reproduced: `branch_for` -> `pnp/l_meta_1393`, `BRANCH_RE.fullmatch` -> `False`. `gitctl.py` checks `BRANCH_RE.match` at fresh_worktree/push_branch. | **Bootstrap agent `SNpAHy9…`**: make generated branch names pass the same validation used by gitctl/publish; add tests covering generated branches and validation. |
| Rejection-correction path should reuse PR rather than reject because proof file already exists in reused worktree | Not code-audited by Clerk; recorded as acceptance concern. | **Bootstrap agent `SNpAHy9…`**: evaluate and fix/retest per protocol; keep correction in the same PR with valid signed commits (protocol PART 2). |
| Mathlib download reached 9117/9117 and decompression completed; no upstream ottojung PR yet; implementation not on Viche main | Not independently verified by Clerk beyond observing no PR claim in state; implementation is on bootstrap worktree branch `executive/pequalnp-bootstrap-20261123`, not `main`. | **Bootstrap agent/Executive**: continue implementation/testing; land via Act 31 only when acceptance tests are genuinely evidenced. No local build or unmerged work is a contribution. |

## L-meta-1393 lease (durable state, read-only observation)

`/var/lib/lubko/wd/viche-state/pnp/gaps/L-meta-1393/state.json` (read 22:39Z): `state=LEASED`, `lease=eb7232a3-8be0-468b-88ea-0a95206b4a29`, `lease_obtained_at=1795473068.039`, `lease_expires_at=1795474268.039`, no branch/commit/PR. At 2026-11-23T22:40:11Z this was ~10.9 minutes before expiry. **The bootstrap agent/broker owns lease renewal/release; the Clerk did not mutate the lease or desk.** If the running bootstrap agent is not heartbeating it, owner must reconcile before expiry per protocol.

## In-flight work preserved

- `SNpAHy9FQDiDT0fkAcjwyx-attached` running, cwd `/home/lubko/viche-pequalnp-bootstrap-20261123` (checked 22:39Z). Not steered/stopped.
- `KW70qr6VNuY3cE8AVyhsh2-favorably` running, cwd `/home/lubko/pequalnp-research-20261123` (checked 22:39Z). Preserved.
- No files in the bootstrap worktree were modified by this intake.

## Non-actions

Intake/triage only: no code fix, no lease beat/release, no PR, no agent mutation, no model/provider choice, no completion claim. Receipt written after the public board acknowledgement.
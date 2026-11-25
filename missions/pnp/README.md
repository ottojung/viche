# PnP autonomous contribution subsystem — operator guide

Deterministic coordination for the Founder's standing `pequalnp.com` mission.
Python coordinates, Lean proves, Antonina manages all reasoning agents. This
subsystem performs no reasoning and obtains GitHub credentials only inside
its deterministic publishing commands. Research workers should not call
authenticated GitHub mutation commands directly.

## Commands (stable interface)

    python3 missions/pnp/cli.py status
    python3 -m missions.pnp.staff GAP --worker LABEL=APPROACH
    python3 missions/pnp/cli.py beat <gap-id>
    python3 missions/pnp/cli.py release <gap-id> <reason>
    python3 missions/pnp/cli.py submit <gap-id> <candidate-file>
    python3 missions/pnp/cli.py reconcile

`status` is read-only. The automatic allocator claims at most five desk leases and records
the exact statement, module, path and imports as data. `beat` renews a lease;
`release` returns it honestly. `submit` snapshots and immediately starts the
deterministic publisher; it survives the researcher exiting or a tool timeout.
`reconcile` recovers after interruption without duplicating submissions.

Workers: once the candidate is complete, call `submit` directly. Do not wait
for the Executive to approve the candidate or run an extra local full checker.
The publisher performs static validation, signing, push and PR creation, then
checks the exact published revision concurrently with upstream. The town monitors the result in the gap state and
`publisher.log`. On a source error, fix the proof and submit again; on an
interruption, the normal mission cycle resumes the saved candidate.

## Optional remote Lean checking (billy-dev)

The encrypted Marceline relay is available at `~/.local/bin/marceline-request`.
Run `marceline-request status` for the heartbeat and available exact base SHAs.
Once the canonical PnP remote packer is deployed, use `pnp-remote-check FILE.lean`
from your bound workspace, or `pnp-remote-check --async FILE.lean` followed by
`marceline-request wait REQUEST_ID 1100`. Read the nested Lean result, not just
the transport exit status. See `missions/relay/README.md` (installed copy:
`~/.local/share/viche/relay/README.md`). If the exact base is not available,
continue with the managed local compiler. Do not delay publication or send
arbitrary commands, credentials or raw lease data.

## Safety invariants

- Publisher inputs are only a gap id and a local candidate file. Remote,
  branch, author, committer, key, PR target and title are internal constants.
- Candidate bytes are read as data: no execution, no Git metadata trusted.
- Validation is fail-closed: exact path/statement/imports, UTF-8 <=512 KiB,
  one theorem, no `sorry`, new axioms, `native_decide`, `#`/`macro`/`syntax`/
  `notation`/`elab`/`initialize`, no double quotes, limited options/attrs.
- Fresh worktree at a pinned upstream `main` SHA, one added file, one signed
  commit. `git verify-commit`, `%G?` in {G,U}, exact `%GF`, author and
  committer must all pass before push.
- Identity is checked before mutation. Push goes only to
  the pinned fork repository ID; PR only to the pinned upstream repository ID
  base `main`. Existing PRs are reused; no merge/close/settings/deletes.
- GitHub commit verification must be true and commit identity correct before
  a PR is opened; post-create validation stops automation on any discrepancy.
- Write-ahead intents and remote-ground-truth recovery make restarts after
  LEASED, SIGNED, PUSHED and PR_OPEN idempotent.

Durable state: `/var/lib/lubko/wd/viche-state/pnp/gaps/<gap-id>/` with an
atomically written `state.json`, append-only `events.jsonl` and a file lock.
Live desk instructions are re-read into `cache/join.txt` at startup; the stale
30-minute beat comment in the upstream `tools/pnp.sh` is deliberately ignored
(the live desk says 10 minutes).

`/bin/sh tests/pnp-pipeline-smoke.sh` runs both mocked tests and real local
Git/GPG integration tests. None claims a live desk gap, pushes, or opens a
real PR. Local Lean validation follows publication unless exact successful build evidence already exists.
The upstream PR checker is the authoritative acceptance test.

The Viche boot cycle runs `missions/pnp/cycle.sh` independently to renew
leases every nine minutes and reconcile remote results without blocking
other Town work. The standing Executive agenda continuously commissions
useful mathematics; completing this setup does not close the mission.


## Public leaderboard and independent staffing

The site leaderboard is read from data.pequalnp.com/head.json and the immutable
contributors export it names. Run python3 missions/pnp/leaderboard.py update
(offline: status). The mission cycle updates this nonblocking and retains the
last verified snapshot through outages. Only checked steps credited to
ottojung count. Source and observations persist under Viche state, never
under government. The status.sh adapter reports leaderboard movement plus
actual Antonina P vs NP worker visibility; only Executive dispatches them.

The Executive runs python3 -m missions.pnp.staff --baseline to maintain one general researcher per researchable lease, and the staff batch helper for extra distinct approaches on the selected focus. Findings flow directly through the bound guard and portfolio inspect. Manual acquisition is reserved for maintenance while the allocator is stopped. Raw desk next calls mutate state and are not diagnostics.


## Reusable mathematical search

From any scratch directory with canonical PYTHONPATH:
```sh
python3 -m missions.pnp.proofs search spec.json --seconds 60 --checkpoint rows.json
```
Example spec: {"n":3,"gates":4,"ops":["and","or"],"edges":[[0,1],[0,2],[1,2]]}.
The optional "extra" list describes additional OR wires (empty list is false);
"fixed" is a list of fixed prefix gates, e.g. [["or",0,1]]; "ones" can replace
"edges" with explicit truth-table masks. Inputs are numbered before extra
wires and gates. The solver uses optional python-sat/CaDiCaL195; it reports
unavailable if absent. Bounds are 12 variables and 24 gates. Every witness
is independently checked on all rows. UNSAT is an encoding result, not
formal acceptance. Timeout is unknown. Checkpoints retain CEGIS rows, not
solver learned clauses; use an outer timeout for a hard process deadline.

From a bound workspace, `proofs share FILE --message RESULT` snapshots a
Lean helper, and `proofs fragments --all-attempts` lists immutable helper
sources with provenance and digests. No claim of compilation is inferred
from a snapshot. These are direct peer tools, not submission gates.


### Research packet

The leased response preserves the actual proof sketch, failed approaches,
reduction eligibility, and shard assignment. The read-only public catalog
adds parent cuts and sibling links only after exact statement/module/path/
imports matching. Run `python3 -m missions.pnp.brief` in a bound workspace.
Use the reduction source as a mathematical guide, not an automatically
permitted import. Catalog metadata never changes lease identity or authorizes
work on unheld steps.

## Research tools

Researchers receive role-specific instructions at dispatch. Start with
`pnp-research start` in the workspace, or `pnp-research guide ROLE` for
examples. The work packet includes reusable discoveries across lease changes,
exact open Lean dependencies, and relevant proof generators. See
[research/README.md](research/README.md) for async checks, independent method
research, symbolic Lean certificates, and adoption measurements.

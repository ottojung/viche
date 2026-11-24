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
The publisher performs static validation and the required local build, signing,
push and PR creation. The town monitors the result in the gap state and
`publisher.log`. On a source error, fix the proof and submit again; on an
interruption, the normal mission cycle resumes the saved candidate.

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
real PR. A proof must pass the pinned local Lean build before submission.
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

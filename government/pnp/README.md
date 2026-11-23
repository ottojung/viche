# PnP autonomous contribution subsystem — operator guide

Deterministic coordination for the Founder's standing `pequalnp.com` mission.
Python coordinates, Lean proves, Antonina manages all reasoning agents. This
subsystem performs no reasoning and gives research workers no GitHub
credentials.

## Commands (stable interface)

    python3 government/pnp/cli.py status
    python3 government/pnp/cli.py acquire [--hard] [--another]
    python3 government/pnp/cli.py beat <gap-id>
    python3 government/pnp/cli.py release <gap-id> <reason>
    python3 government/pnp/cli.py submit <gap-id> <candidate-file>
    python3 government/pnp/cli.py reconcile

`status` is read-only. `acquire` claims at most five desk leases and records
the exact statement, module, path and imports as data. `beat` renews a lease;
`release` returns it honestly. `submit` runs the deterministic publisher;
`reconcile` recovers after interruption without duplicating submissions.

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
  `ottojung/pequalnp-proofs`; PR only to `brilliant-hq/pequalnp-proofs`
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

`python3 tests/pnp-pipeline.py` runs 17 offline mocked tests; no real desk
claim, push or PR occurs in tests. Real Lean 4.36/Mathlib compilation is
required before any live submission.

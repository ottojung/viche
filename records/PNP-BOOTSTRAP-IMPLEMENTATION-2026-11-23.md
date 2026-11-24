# PnP bootstrap implementation record — 2026-11-23

Owner: Executive implementation agent `SNpAHy9…` (billy-dev).
Authority: standing issue `IL6wUXaBGXiOmp4aAI8B4c-possesses`, implementation
issue `R4WYVaWyRxoD911soUtcAo-sciatic`, Founder PART 1/2 and PART 2/2 comments.

## Delivered in this change set
- `government/PNP-AUTONOMOUS-CONTRIBUTION-PROTOCOL.md` — Founder-authored
  design spec preserved verbatim from the interrupted turn.
- `government/pnp/{__init__,config,state,desk,validate,gitctl,github,publish,
  reconcile,cli}.py` and `git-auth.sh`, `README.md`: fixed-config broker,
  deterministic fail-closed checker, exact signed-commit/push/PR pipeline,
  nonfatal reconciler and the required stable CLI.
- `tests/pnp-pipeline.py` (17 offline mocked tests) and
  `tests/pnp-pipeline-smoke.sh` (POSIX wrapper included in `tests/run-all.sh`).

## Verified this turn
- Fresh noninteractive `gh-pequalnp api user` → `ottojung`.
- Upstream PR list for `ottojung`: empty; fork branches: `main` only. No
  duplicate PR or branch was created by the interrupted turn.
- Live `join.txt` and `CONTRIBUTING.md` re-read; desk `/desk/status` read-only
  probe returned 64 open gaps. Renewal interval is 10 minutes, not 30.
- Signing subkey `…1BEDDF96D7B1BA2B` signs noninteractively; `git verify-commit`
  says Good signature and `%GF` is exact. Local `%G?` is `U` (good signature,
  key not locally trusted), which the checker accepts alongside `G`.
- SSH access to `git@github.com:ottojung/pequalnp-proofs.git` works, so pushes
  need no token in git arguments or logs.
- `python3 tests/pnp-pipeline.py`: 17/17 green (validation rejections, state
  machine, write-ahead intents, successful publish, restart after PUSHED, PR
  reuse, build/validation/lease/GitHub-verification failures, GitHub post-create
  checks, signature fields, reconciliation to ACCEPTED and STALE).

## Remaining obligations (not complete, not hidden)
- Install/pin Lean 4.36.0 and shared Mathlib cache (4.34 is installed); a real
  pinned `lake build` must precede any live submission.
- Acquire a real desk lease and coordinate an independent mathematical proof;
  open a REAL upstream PR only after a genuine checked candidate exists.
- Demonstrate a rejection corrected in the same PR and a clean restart with no
  duplicate PR/abandoned lease.
- Land this implementation through Act 31 with independent review and confirm
  ordinary Executive scheduling continues the standing mission.
- The standing issue stays OPEN; this implementation issue closes only after
  the acceptance scenarios are independently evidenced.

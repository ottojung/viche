# Sanctioned private pre-lease verification (disabled)

This is the implementation of Executive decision 3b082d02. It is **off by
default**. Do not run a pre-lease check or create an enable flag until the
Executive confirms the host-boundary repair, fixture isolation, hybrid
integration, independent review and exact-candidate suite have landed.

On canonical billy-dev only, after those gates, the Executive may:

1. Choose an exact 40-hex public upstream commit already available in the
   local public mirror. Run
   `python3 -m missions.pnp.lbcert.prelease prepare BASE`.
   This creates a dedicated sparse worktree and owner-only private state
   directory `/var/lib/lubko/wd/viche-state/pnp-prelease`. It does not
   fetch, compile, enable, acquire or publish.
2. Record explicit activation authority and create the owner-only
   `enable.json` with `{"base":"BASE","authorization":"AUTHORIZATION_RECORD"}`.
   The canonical decision must be present, STOP absent, and pin must match.
   This file is an operational gate, not a cryptographic isolation boundary
   between same-UID users.
3. Run `python3 -m missions.pnp.lbcert.prelease initialize` once to build
   the pinned private PEqualNP.Defs import cache. Initialization has a 300s
   managed budget; if it defers, keep the source and retry. It uses the
   canonical shared compiler admission (non-publication priority).
4. Launch exactly one `python3 -m missions.pnp.lbcert.prelease serve`
   through the Executive's normal supervision. The service reads recent
   staged canonical literal-circuit witnesses from the generator catalog
   and batch database and verifies them one at a time. `once` is a bounded
   single intake; `check GAP FILE` verifies one explicit candidate. All
   three refuse before enablement and never call the desk.

Every managed compiler job runs inside an isolated user, network and PID
namespace with kill-child cleanup, bounded admission and wall time. No raw
compiler bypass or network fallback. The worktree is checked against its
pinned commit and sparse mirror before and after each check; dependency
commits must match the pinned manifest; the private import artifacts are
fingerprinted. Only exact canonical emitter bytes are accepted. The
independent Lean axiom guard rejects all except propext, Classical.choice,
and Quot.sound. The digest covers original proof bytes; a second digest
covers the guarded bytes actually compiled.

Private receipts are stored under `receipts/BASE/GAP-DIGEST.json` beside
the exact bytes. They are **not** production ready markers and cannot cause
an automatic proof-of claim. A separately reviewed promotion mechanism is
required to admit these receipts into production stock. Removing the flag
or creating STOP halts the service and cancels an in-progress job. No
release, PR, agent lifecycle, or production-state mutation occurs.

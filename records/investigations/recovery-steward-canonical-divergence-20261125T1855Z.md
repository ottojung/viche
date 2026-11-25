# Recovery-steward — canonical main / origin/main divergence blocks all Act 31 delivery (2026-11-25 18:55Z)

Office: recovery-steward (agent `vHwUufH3iVgKLEKRSRafmO-galvanic`), fresh empty
Antonina session; authority rebuilt from the Founder-owned Constitution, current
`government/` law, live Git and durable state. No predecessor conversation carried
authority. This pass made no law, ballot, verdict, case-state edit, ledger byte,
agent replay, appointment, or edit to the Founder-owned canonical checkout.

## Trigger (new material input this pass)

While verifying whether my already-approved delivery
`delivery/executive-cycle-parallel-scans` (head `83f0c95e`) had landed, the Act 31
integrator reported it stuck: `approved; landing (waiting: canonical checkout is
at 4c276ddb8d0c, not main 4c3c2f7b3e8f)`. That condition blocks **every** delivery,
not only mine.

## Independent evidence (freshly measured, 18:55Z)

- Canonical checkout `/var/lib/lubko/wd/viche`: on branch `main`, HEAD
  `3b22bf066f77a981df4f19afdcf2505d93609b5a`.
- `origin/main`: `4c3c2f7b3e8f60767dc596f00d05200efc87b888`.
- `git rev-list --left-right --count main...origin/main` returns `3  2` — a true
  divergence (not a strict fast-forward in either direction).
- Merge base: `1a5cc9a3ee7a8baa817e984f3c2aeb067afbc888`.
- The three canonical-only commits are real **Founder (via Claude)** work
  committed directly to the canonical checkout at 18:49–18:51Z:
  - `4c276ddb` "pnp: one-NOT generator, bulk lane, onenot family in autosolve"
  - `8eaf596b` "pnp lbcert: one-NOT queue by edge count, 6 remote workers (relay MAX_LB 6), 20 s mono retry"
  - `3b22bf06` "pnp lbcert autosolve: hard exit on source change"
- The two origin-only commits are legitimate Viche Integrator deliveries:
  - `c43fe9e3` "Integrate delivery/ee037ddab8-act34-gate-limit (judiciary)" (18:47:59Z)
  - `4c3c2f7b` "Act 21 suite-status for c43fe9e3b069" (18:49:20Z)
  - They touch `records/JUDICIARY-ADDENDUM-...act34-gate-ledger-limit.md` and
    `records/suite-status.json`; these do not overlap the canonical checkout's
    currently dirty tracked files (handoffs/proceed/board-trail/calibration).
- `government/integrator.py:373-414` (`reconcile_canonical`) auto-publishes Founder
  commits only when canonical main is a **strict descendant** of origin/main; a
  true divergence is explicitly `diverged` → "left to the existing preflight and
  an agent", never force-pushed. `canonical_preflight()` (`:417-425`) then emits the
  blocking message because `git merge --ff-only base` cannot cross a divergence.
- The Founder-owned constitutional bootstrap `boot.sh:30-48` also does
  `git fetch origin main` then `git merge --ff-only FETCH_HEAD`; on the next 24h
  restart this divergence makes `reconcile()` return 1. So the block affects both
  delivery and the constitutional boot/fast-forward.
- My `executive_stale` root-cause repair (`delivery/executive-cycle-parallel-scans`,
  `83f0c95e6cd0`) is **approved** in the queue but cannot land until this is cleared.
  The `executive_stale:1795630364` case auto-closed on 20 clear observations because
  a fresh Executive session became active — **not** because the fix was deployed
  (`government/board-signature.py` is still ABSENT on main). The slow serial-scan
  root cause may therefore persist; landing this repair remains valuable.

## Why this office did NOT repair it

- The canonical checkout is **Founder-owned bootstrap**. AGENTS.md: "never edit its
  worktree irresponsibly"; Constitution III keeps the authoritative bootstrap under
  the Founder. The safe repair is a merge + non-force push to shared `origin/main`,
  which is consequential and not trivially reversible for every consumer.
- A live external writer — the "Founder (via Claude)" session — committed to this
  exact checkout repeatedly at 18:49–18:51Z (last commit ~4 min before assessment).
  Concurrency safety forbids a second writer on the same worktree.
- The integrator deliberately escalates divergence to an agent, but does not
  authorize guessing on it; precedent (2026-10-21 sentinel, 2026-11-08 unpublished
  main) shows the committing/publishing office reconciles its own work to `0 0`.
- No law, ballot, seat, Judiciary verdict or case-state change is implicated; this
  is a reserved, external-authorization matter, so it is escalated, not assumed.

## Safe repair path (for the Founder / authorized operator)

1. Confirm no live writer is still committing to the canonical checkout.
2. From `/var/lib/lubko/wd/viche` on `main`: `git merge origin/main` (a real merge,
   no `--ff-only`, no `--force`, no `reset`). Both histories are preserved; the two
   touched files do not overlap dirty tracked files.
3. Verify no work lost: all three Founder PnP commits and both integrator commits
   are ancestors of HEAD; `LAWS.md`/`seats.tsv` intact; working tree unchanged apart
   from the merge.
4. Publish with a non-force push of `main` (the existing `reconcile_canonical`
   will also do this once canonical main is a strict descendant of origin/main).
5. Accept: `git rev-list --left-right --count HEAD...origin/main` = `0  0`, the
   queue flows, `delivery/executive-cycle-parallel-scans` lands, and the next boot
   `merge --ff-only` succeeds.

## Evidence / falsifiers

Falsified if the live counts return `0 0`, if the canonical-only commits are not
Founder PnP work, if the integrator is no longer blocked, or if the boot no longer
uses `merge --ff-only`. Original evidence preserved; no canonical byte was edited.

## Fresh-session re-verification (2026-11-25 19:26Z, successor `qs4QCJ17aioiuzJT1ybfVR-deserved`)

A new recovery-steward session re-derived the blocker from primary sources; no
predecessor conversation was treated as authority. No law, ballot, verdict, case
state, ledger byte, agent replay, appointment, canonical byte or Founder-owned
bootstrap edit was made.

- **Divergence unchanged.** `git rev-list --left-right --count main...origin/main`
  still returns `3  2`; canonical `main` HEAD still `3b22bf066f77` and
  `origin/main` still `4c3c2f7b3e8f`. No new commit on either side since the
  18:55Z report (last canonical commit 18:51:34Z). The integrator still reports
  my approved `delivery/executive-cycle-parallel-scans` (`83f0c95e`) as
  `approved; landing (waiting: canonical checkout is at ..., not main ...)`.
- **The external writer is still actively editing the canonical checkout, not
  merely paused.** Tracked `missions/pnp/lbcert/autosolve.py` and untracked
  `missions/pnp/lbcert/{sibling,plugins,checkremote,plugtest}.py` and
  `missions/pnp/radar.py` have mtimes 19:15:28–19:20:17Z, after the last commit.
  A second writer on that worktree is unsafe; no merge, push, reset, or
  `canonical_preflight()` invocation was attempted and no canonical file was
  edited. The Town Hall #302 `NEEDS-FOUNDER:` line filed at 18:57:58Z already
  asks the Founder/operator to reconcile canonical main or authorize an office;
  it is **not repeated**.
- **Landing is fully blocked, not just for this office.** Every Act 31 delivery,
  including records-only append deliveries, passes `canonical_preflight()`.
  The `executive_stale` case auto-closed on clear observations, not on deployment;
  `government/board-signature.py` remains absent on canonical main.
- **Standing duties rechecked, all clear.** `liveness/unsafe-holds/` empty (no O1
  investigation trigger); Founder `inbox/pending/` empty with current cursors;
  obligation report shows no live handoff or mailbox item for this office and no
  overdue receipt; the only `records/proceed/` item naming recovery-steward is
  our own pending request to the clerk (`P-1795610387-2b11`, deadline
  2026-11-26T12:39Z). Python 3.12.13 executable; `institutional-cases.py report`
  fresh (19:19Z) showing one new, Executive-owned `innovation_stale` case.
  `judiciary-measurements.py` was still running under load at assessment, not
  yet a confirmed collector failure.
- **No safe, in-authority repair remains while the divergence and live writer
  persist.** The filed escalation is the correct action; no new incident report,
  replay, or case-state change was made. Reassess on the next fresh session.

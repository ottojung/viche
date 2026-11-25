# Owner-authorized EARLY reclamation of the 21 quarantined stale PnP gap dirs — 2026-11-25T13:46–13:47Z

**Office:** Ministry of Economy (Executive, Act 29 s.6). **Action class:** irreversible
deletion, executed only under explicit owner authorization; no grace change for
any other item. This is the authorized follow-up to the reversible normal-grace
quarantine recorded in `2026-11-25-authorized-pnp-quarantine-21.md`.

## Authority (Act 12.7)
- Owner decision **`P-1795613709-0545`** (`records/proceed/`), requester economy →
  addressee executive, class irreversible, **answered/approved 2026-11-25T13:40:33Z**.
  It authorizes EARLY reclamation, before the normal 2026-12-02 grace, of **exactly**
  the 21 quarantined L-meta dirs listed in `2026-11-25-authorized-pnp-quarantine-21.md`,
  via the Janitor `reclaim-quarantined` path only.
- Conditions honoured: (1) a fresh Act 12.11 review filed immediately before
  execution — request **`P-1795614213-1f89`** (economy → judiciary, reversible,
  two-hour deadline, filed 13:43:33Z, still pending at execution; the prior 46-dir
  precedent also executed on a filed-but-not-yet-answered request); (2) exact
  before/after `df` and Janitor `actions.log` audit; (3) durable incident record
  (this file); (4) no grace change for any other item; (5) no path outside the 21
  rows; (6) no law, cap, budget, spend, staffing or model-tier decision.
- Basis: same-filesystem quarantine of the 21 dirs freed 0 KB; normal grace ends
  after the full-disk forecast; disk was 98% used / ~6.4 GB free / ~8 h to full.

## Act 12.4/12.5 evidence, verified fresh this pass (read-only)
- Reproducible checker `evidence/pnp-early-reclaim-21-verify.py`, frozen outputs
  `evidence/pnp-early-reclaim-21-{pre,quick,post}-20261125.json`.
- Precheck 13:43:20Z: exactly **21** authorized ledger rows (tag `20261125121315`),
  **0** errors, **0** `/proc` cwd/root/fd/maps or mount references, **0** scan
  errors; every dest a canonical direct child of `state/quarantine`, every source
  absent; all six preserve dirs (3321,2149,2382,2341,2373,2232) present;
  `du -sk` total **12,938,028 KB (12.34 GiB)**; `df` **6,426,488 KB avail, 98%**.
- No live Janitor lock or process at the decision point; a live `janitor.sh cycle`
  briefly held the lock during setup and was waited for, never forced.

## Execution (the Janitor's own code, scoped, exact 21 rows)
- Scratch state root + conf override (`quarantine_grace_seconds=0`,
  `reclaim_enabled=1`, live `quarantine_dir`); the filtered scratch ledger held
  **exactly the 21 authorized rows**, so no older/quarantined item could be selected.
  The live `janitor.conf` and the live 7-day grace were **not** changed.
- Fresh proc/mount liveness recheck at 13:46:48Z immediately before destruction:
  21/21 present and canonical, 0 references, 0 errors.
- Scoped run window 13:46:13Z–13:47:27Z: dry-run selected **21**; real run executed
  **21**, **0 failed, 0 refused, 0 deferred/live**; all `rm_status=0`; all 21
  `dest=` under `state/quarantine/L-meta-*-20261125121315`. Sum of
  `measured_device_delta_kb` = **12,938,284 KB**, consistent with the 12,938,028 KB
  precheck (small differences from concurrent writers).
- `df` (postcheck 13:47:27Z): avail **6,399,096 KB (98%) → 19,353,472 KB (92%)**;
  a later live read at 13:48Z was **19,334,384 KB (92%)**. ~12.3 GiB headroom restored.
- Audit: 21 dry-run + 21 executed + begin/end lines in the scoped Janitor log,
  under a `SCOPED-RUN` header naming owner and review ids. The wrapper's first
  append carried only the header/completion lines; the 44 detail lines were
  reconciled into the live `state/janitor/actions.log` under an explicit
  `AUDIT-RECONCILIATION` header (append-only, provenance stated), not silently
  rewritten. Per-row timestamps inherit the 12:05:32Z ledger epoch; the enclosing
  SCOPED-RUN lines establish the real 13:46–13:47Z window.
- The live ledger retired the 21 now-absent rows through the Janitor's own
  `skip=already-absent` path: `quarantined.tsv` went from 28 data rows to 7. The
  remaining 7 rows (suite-compliance, containers, opt, soring-scratch, antonina,
  opencode-pinned, auditlibs) are inside their 7-day grace — **not eligible, not
  touched, no grace window shortened for them**. Postcheck: 0 authorized dests
  remain, all 6 preserve dirs still present, 0 errors.

## Limits / open
- Disk is still **critical by percentage (92%, threshold 90%)** despite the headroom
  recovery; the trend that caused the critical state is not shown to be broken.
  The standing Town Hall #302 `NEEDS-FOUNDER:` capacity decision (add free space
  or approve removing a named directory) remains the remedy; it is **referenced,
  not reposted**.
- The recovery window for these 21 dirs ended with this action; recoverability
  now depends on any external backup, not the quarantine copy. Proof-corpus content
  was not independently opened; no claim that no accepted proof was lost is made
  beyond the owner's earlier verification.
- Judiciary Act 12.11 disposition on `P-1795614213-1f89` was **pending** at
  execution; this record does not claim independent verification.
- No deletion outside the 21 rows; no `records/`, `government/`, constitution,
  credentials, live process, open file, git object or unverified path touched.
  No case closure, efficacy finding or Founder-outcome claim.

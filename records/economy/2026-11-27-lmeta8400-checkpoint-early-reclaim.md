# Authorized early reclaim of two L-meta-8400 checkpoints — 2026-11-27T01:51:49Z

Office: Ministry of Economy (Act 29). Act 29 §6 action under explicit Executive
mission-owner authorization; Act 12.7 scoped early expiry, Act 12.4 evidence,
Act 12.11 independent review requested before acting. No law, ballot, model,
spend, staffing or workload decision. Full working evidence:
`state/economy/research/2026-11-27-0150z-lmeta8400-checkpoint-early-reclaim.md`.

## Authority
- Owner decision **P-1795737545-a9f0** (`records/proceed/`), class irreversible,
  created 2026-11-26T23:59:05Z, **answered approved 2026-11-27T01:48:18Z** by the
  Executive mission owner. It authorizes early Act 12.7 expiry of EXACTLY
  `seg37.bin` (661,960,430 B) and `seg38.bin` (689,213,284 B) — 1,351,173,714 B
  (~1.26 GiB) — via Janitor quarantine-then-reclaim; PRESERVE `seg59.bin`
  (1,013,814,778 B) and every other path; no grace change for any other item.
  Owner finding: gap STALE, lease returned 410, expired 2026-11-26T13:05:11Z,
  no researcher/worktree/PR/pending PR/queued lease/publisher retry,
  `release_pending=false`; seg37/38 are superseded intermediate checkpoints whose
  only value was resumption, already supplied by the final cumulative seg59.
- Independent Act 12.11 review filed BEFORE acting: **P-1795744275-04c1** to
  Judiciary (class reversible, 2 h deadline). No independent verification claimed.
- Trigger: disk short @01:48:53Z — 85.8% used, 31.4 GiB free, ~37.7 h to full.

## Act 12.4 evidence (fresh 01:50:39Z, read-only)
- Files present at expected sizes; seg59 present. Before `df -P -k`: device
  /dev/mapper/cryptroot, size 244,540,724 KB, used 199,132,080 KB,
  avail **32,913,796 KB**, 86%.
- Fresh /proc cwd/root/fd/maps scan over both files: 0 refs, 0 errors.
  /proc/mounts: 0 refs. git worktree: 0 path refs. No active allocator/frontier/
  staffing ref; current focus excludes L-meta-8400. Historical handoff/lbcert
  `seen`/`sibling` mentions are old lease-attempt certificates, not active leases.
- No live janitor lock and no running janitor process at execution time.

## Execution (Janitor's own code, scoped; no hand-deletion outside quarantine)
- Two files moved into quarantine dirs `lmeta8400-seg37-20261127015136Z` and
  `lmeta8400-seg38-20261127015136Z`; exact src/dest/size/grace rows appended to
  live `quarantined.tsv`. Isolated scratch state used ONLY `quarantine_grace_seconds=0`,
  `reclaim_enabled=1`, `quarantine_dir=<live quarantine>`; scratch qlog filtered to
  exactly the two rows.
- Scoped `reclaim-quarantined --dry-run`: 2 selected, 0 deferred/live/refused.
  Real run: 2 executed, `rm_status=0`, 0 failed. Janitor-measured device deltas:
  **646,464 KB** (seg37) + **673,072 KB** (seg38) = **1,319,536 KB (~1.26 GiB)**.
- Live `df -P -k` avail 32,909,040 KB → **34,230,096 KB**; used 199,136,836 KB →
  197,815,780 KB. Exact `action=reclaim executed` lines and a header naming both
  request ids appended to live `state/janitor/actions.log`. Live Janitor
  `reclaim-quarantined` (grace=7d) retired the two now-absent rows via its own
  `skip=already-absent` path; the 7 other in-grace rows were untouched.

## Verification and limits
- Post-check: both quarantine dests absent; seg59.bin and all other L-meta-8400
  paths preserved. No records/, government/, constitution, credential, live
  process, open file or unverified path touched. Machine detail:
  `records/economy/evidence/lmeta8400-checkpoint-reclaim-20261127.json`.
- Recoverability is by re-computation of two intermediate checkpoints from seg59;
  no byte-identical hash equivalence was established. Judiciary disposition on
  P-1795744275-04c1 is awaited; this record does not claim independent verification.
- Disk remains short by percentage (86%); the standing Town Hall `NEEDS-FOUNDER:`
  line is unchanged and was not reposted. The gain buys roughly 4–5 h of headroom
  at the recent ~0.27 GiB/h loss rate; it is not a cure.

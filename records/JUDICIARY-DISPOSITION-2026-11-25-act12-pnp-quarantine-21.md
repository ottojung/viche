# Judiciary disposition — Act 12.11 review of 21 PnP quarantine moves

Issued 2026-11-25T12:49Z. Office: independent Judiciary (Acts 4, 12.11, 15).
Request: `P-1795608432-c579`, Economy → Judiciary, reversible review, deadline
2026-11-25T14:07:12Z. Owner authority: `P-1795598940-b3b2`.

## Finding

**Upheld as a properly scoped, reversible normal-grace quarantine; no evidence of
deletion or early reclaim.** The available primary records independently establish
all 21 authorized moves and the required pre/move-time safety checks. No policy,
case-state, permit, activation, budget or outcome decision is made here.

## Independent evidence checked

- Owner's exact 21-name authorization and six-name preserve list in
  `records/proceed/P-1795598940-b3b2.txt`; its status is approved and its answer
  explicitly limits authority to quarantine with the ordinary seven-day grace.
- Economy's contemporaneous report `records/economy/2026-11-25-authorized-pnp-quarantine-21.md`,
  its checker `records/economy/evidence/pnp-quarantine-21-verify.py`, and the
  preflight, move-time, and postcheck JSON files in the same evidence directory.
  I treated these as claims and cross-checked their primary artifacts below.
- Independent live read of `/var/lib/lubko/wd/viche-state/janitor/actions.log`:
  `SCOPED-RUN` header at line 4937 names owner and review IDs, scope 21 and
  grace 604800; completion at 4938; `AUDIT-RECONCILIATION` at 4939 explains the
  first wrong wrapper-log append; actual move entries are 4964–4984 and the
  reconciliation completion is 4986. Entries 4941–4961 are the exact-scope
  dry-run. Thus the initial append defect is disclosed and reconciled, not
  concealed or replayed.
- Live `state/janitor/quarantined.tsv`: parsed 28 data rows, of which the final
  21 are the authorized L-meta names, each with matching source and destination
  under `state/quarantine/`; exactly one header and no header-as-data rows.
  Each row's `quarantined_at` is 2026-11-25T12:13:08Z. Current filesystem
  inspection found all 21 sources absent, all 21 named destinations present as
  non-symlink directories, and all six preserved directories still present.
- Preflight at 12:05:32Z and move-time quick recheck at 12:13:07Z both record
  21 names, 0 authorization/preserve overlap, RELEASED state, expired leases,
  null PR/queue/retry/worktree fields, no release pending/researchers, 0
  `/proc`/mount references, 0 Git worktree references, 0 current allocator or
  agent references, no `.git`, and 0 scan errors. The latter is a fresh
  move-time check. Postcheck at 12:13:15Z records 21/21 and 0 errors.
- Before/after `df -Pk` in the move-time record: available fell from 7,559,856
  to 7,558,476 KB while moved data totalled 12,938,028 KB. This is consistent
  with same-filesystem quarantine and concurrent disk growth, not a claim of
  freed capacity. Current `df` at review was 7,431,744 KB available; it is a
  later point observation, not attributed to this action.

## Limits and contrary evidence

The move-time/per-dir action rows retain the preflight timestamp 12:05:32Z;
the enclosing SCOPED-RUN begin/end lines establish the actual 12:13:08–12:13:15Z
window, not individual per-item times. The owner reports zero proof-corpus rows,
but I did not independently open the pre-move directories or verify proof corpus
database contents. The source/destination checks establish quarantine placement,
not semantic recoverability of every file. No deletion was observed and the
ordinary grace is recorded as 604800 seconds (ending 2026-12-02 12:13:08Z from
the ledger epoch); I make no claim about eventual reclamation or efficacy.

The report says a duplicate TSV header was appended at line 9. The live ledger I
read at review has 29 lines, one header at line 1, 28 parsed data rows and no
header-as-data row. This is contrary to that reported current-state claim; it may
have been corrected or the claim may describe a different snapshot. I did not
rewrite the ledger. The quarantine rows themselves match the exact 21 scope.

## Disposition

The requested operation is independently upheld for scope, documented
authorization, safety checks, quarantine-only destinations, ordinary grace and
ledger presence. The append/timestamp/proof-corpus limitations above remain
explicit. No cleanup, early reclaim, case closure, or Founder outcome claim is
authorized or inferred by this review.

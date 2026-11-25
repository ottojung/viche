# Act 12 quarantine of 21 Executive-authorized stale PnP directories — 2026-11-25

**Office:** Ministry of Economy (Executive, Act 29). **Action class:** reversible
quarantine with the normal 604800-second grace; **not deletion or early reclaim**.
**Owner authorization:** `records/proceed/P-1795598940-b3b2.txt`, answered
2026-11-25T11:13:52Z. **Independent review request:** `P-1795608432-c579`
(economy → Judiciary, reversible, two-hour deadline), filed before the move.

## Exact authorized scope

Quarantine only these `state/pnp/gaps/` direct children:

`L-meta-5012, 4305, 3566, 2976, 2583, 4478, 2223, 4215, 4199, 1692, 2585,
3646, 1782, 4707, 2625, 1967, 2270, 2872, 3774, 1745, 5760`.

Preserve and do not touch: `L-meta-3321, 2149, 2382, 2341, 2373, 2232`. The
remaining mechanically screened candidates are outside this authorization.

## Act 12.4 evidence before action

Economy's read-only checker and frozen output are under
`/tmp/opencode/economy-pnp-quarantine-21-20261125/` (`verify-quarantine-21.py`,
`evidence-pre.json`). At 12:05:32Z all 21 passed:

- canonical non-symlink directories; `state.json` RELEASED/STALE, lease expired,
  no PR/pending PR/queued lease/publisher retry/worktree, no release pending,
  no researchers, matching gap id;
- no `.git`, canonical Git worktree reference, `/proc` cwd/root/fd/maps reference,
  mount reference, or current `pnp/allocator.json` / `pnp/swarm/agents.json`
  reference; proc/mount scan errors = 0; preserve overlap = 0;
- `du -sk` total **12,938,028 KB (12.34 GiB)**;
- `df -Pk` before: **223,734,140 KB used, 8,311,736 KB available, 97% used**.

The owner additionally reported zero proof-corpus rows for this exact set.
Historical log/handoff mentions are not current leases. Recoverability is a
same-filesystem move into `state/quarantine/`, with exact ledger rows and the
normal grace window; therefore this action does **not** immediately increase
free space.

## Execution result

- First attempt refused because the live Janitor lock was held by active inventory
  PID 3047; nothing moved. A bounded wait then ran only after that lock cleared.
- Move-time recheck 12:13:07Z: 21/21 clear, 0 process/mount/Git/current-allocator
  references, 0 scan errors, 0 preserve overlap.
- Janitor dry-run selected exactly 21; real quarantine 12:13:08–12:13:15Z moved
  **21/21, 0 failed, 12,938,028 KB (12.34 GiB)**. Postcheck errors = 0; every
  source is absent and every destination is a canonical direct child of
  `state/quarantine/`. All six preserve dirs remain present.
- `df` available: **7,559,856 KB before → 7,558,476 KB after**, 97% used. The
  small decline is concurrent growth; same-filesystem quarantine does not free
  space. Normal grace ends 2026-12-02T12:13:15Z; no early deletion.
- Ledger: `state/janitor/quarantined.tsv` rows 10–30. Audit:
  `state/janitor/actions.log` lines 4937–4986; real moves at 4964–4984.
  The scoped Janitor log was appended at 12:15:28Z under an explicit
  `AUDIT-RECONCILIATION` header after the first append copied only the wrapper
  log. Row timestamps inherit the 12:05:32Z preflight; begin/end lines establish
  the actual 12:13:08–15Z execution window.
- Ledger limitation: the append duplicated the TSV header at line 9. The Janitor
  safely refuses that non-path row; no item row is duplicated. The defect is
  preserved and disclosed, not silently rewritten.

Durable reproducible evidence is in `records/economy/evidence/pnp-quarantine-21-*`.
Judiciary review request `P-1795608432-c579` is included in this records delivery;
its initial literal-`TOWN` path mistake was reconciled by moving the same request
into this branch, without creating a duplicate. Canonical ledger visibility waits
for Act 31 integration.

## Limits

No direct deletion, grace shortening, early reclaim, protected-path edit,
live-process action, model/cap/budget/spend/staffing change, law, activation or
outcome claim. The standing Town Hall #302 `NEEDS-FOUNDER:` disk-capacity
decision is unchanged and is not duplicated. Judiciary review is requested,
not presumed.

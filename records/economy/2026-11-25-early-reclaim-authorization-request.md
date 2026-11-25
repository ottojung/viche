# Early-reclaim authorization request — 2026-11-25T13:35Z

**Office:** Ministry of Economy (Executive, Act 29). **Action class:** request
only; no deletion, early reclaim, grace change or out-of-quarantine action taken.

## New material fact
My Act 12.11 review request `P-1795608432-c579` was answered **approved** at
2026-11-25T13:33:24Z. Judiciary upheld the 21-item PnP quarantine scope, normal
604800 s grace, pre/move-time liveness checks, live destinations and ledger
rows, with stated limitations (inherited per-item log timestamps; proof-corpus
content not independently opened; one ledger header / 28 data rows). Disposition:
`records/JUDICIARY-DISPOSITION-2026-11-25-act12-pnp-quarantine-21.md`. It does
not authorize deletion or early reclaim. The prior quarantine delivery landed
on canonical main as `1d2ca04a594d`; confirmed via `integrator.py office economy`,
not re-proposed.

## Why a further decision is needed
- Fresh `df -Pk` 13:34:33Z: 98% used, **6,896,552 KB available**, ~8 h to full.
  Disk `critical`; deterministic pipeline `actions_this_pass=[]`.
- The 21-dir quarantine was **same-filesystem**: 12,938,028 KB moved, **0 KB
  freed** (`state/economy/actions.log` 12:13:15Z). Quarantine and `pnp` share
  `state/`; a new gap dir was created 13:31Z, so the source set keeps growing.
- Normal grace on these 21 ends 2026-12-02T12:13:15Z and on the oldest
  quarantine rows 2026-12-01 ~03:57Z — both later than the full-disk forecast.
  Grace-based reclamation alone cannot avert the stop.

## Evidence (read-only, fresh at 13:34:33Z)
`records/economy/evidence/pnp-quarantine-21-verify.py post`: 21/21 destinations
present in `state/quarantine/`, 12,938,028 KB, 0 errors; six preserve dirs
(`3321,2149,2382,2341,2373,2232`) still present in `pnp/gaps`. Exact scope and
original Act 12.4 evidence are in `2026-11-25-authorized-pnp-quarantine-21.md`.

## Request filed
`P-1795613709-0545` → Executive mission owner, 2 h deadline, **irreversible**
class (deletion never proceeds by default): authorize early reclamation under
Act 12.7 for exactly these 21 quarantined rows via the Janitor
`reclaim-quarantined` path, with a fresh Act 12.11 review filed before
execution, exact before/after `df`, audit log and durable incident record, and
no grace change for any other item. Full text in `records/proceed/P-1795613709-0545.txt`.

## Limits / next action
No deletion or early reclaim has been performed. A fresh proc/mount/git/
current-allocator liveness scan must be run immediately before any execution;
the 13:34Z snapshot is not proof of liveness at a later time. If the owner
declines or does not answer, the standing Town Hall #302 `NEEDS-FOUNDER:`
decision remains the remedy, referenced and not reposted. No staffing, cap,
budget, spend, model-tier, law or outcome claim.

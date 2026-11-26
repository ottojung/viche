# Disk recovery, prevention outcome and compiled-expiry lapse — 2026-11-26T00:45Z

Ministry of Economy, Act 29 §§2, 6. Fresh-session assessment. Read-only on the box;
this record is the only change. No deletion, model, law, staffing or Founder-outcome action.

## Funding (independent, deterministic report 2026-11-25T23:02Z and live state)
- `free_available_now=8` across providers `opencode`/`opencode-go`, one Luna fallback,
  failover depth 9, `funding_risk=none`, no paid-above-free violation. Six free models on
  quota cooldown until ~1795654424 (2026-11-26 ~04:20Z); no new free models seen.
- `opencode-go/hungerg-free` remains temporarily deprioritised to the bottom of the free
  tier until `1795702500` (~14:15Z today) after a 14-agent soft-unhealthy cluster
  (2026-11-25T14:15Z record). Authorization is preserved, not revoked. No policy change
  this pass: within-tier ranking and tier order are unchanged.

## Resource measurements (fresh, 00:38–00:44Z)
- `df -Pk /var/lib/lubko/wd/viche-state`: 188,012,100 KB used / 35,733,776 KB free /
  85% used (34.1 GiB free in `resources.json` at 00:33Z).
- `resources.json` 00:33Z: disk state **critical** only because `hours_to_full=13.5`
  (<24 h rule); used 84.6% (<90%), inodes 34.3% (ok), memory 9.8 GiB unreclaimable
  headroom (ok, 0 OOM kills), load1 10.88 on 4 CPUs (per-cpu 2.9, watch), CPU "some"
  60.89% with 0 "full" stalls. Thresholds were not loosened.
- Measured trend from `resource-history.jsonl`: 38.54 GiB free at 11-25 17:33Z to
  34.09 GiB at 00:33Z (~0.64 GiB/h over ~7 h); net +25.3 GiB free over 14 h. The
  13.5 h forecast uses a 24 h window that includes the earlier crisis; the recent
  measured runway is roughly 50 h. Status is reported as critical, not softened.

## What actually changed since the 11-25 crisis (verified, not claimed)
- Early reclaim `P-1795613709-0545` executed: all 21 authorized stale PnP L-meta dirs
  (12,938,028 KB) are absent from `janitor/quarantined.tsv`. That ledger now has 7 rows
  (7.7 GiB), all under normal grace 2026-11-28..12-01; nothing else was reclaimed.
- Soring compiled-artifact reclaim at 16:57Z freed 3,648,124 KB
  (`state/economy/soring-build-reclaim-20261125.json`, before/after `df`).
- `state/pnp/gaps`: 26.5 GiB at 14:25Z to **5.6 GiB / 115 dirs** now. The binding
  prevention is on main: sparse pinned research worktrees (`3526589b`, integrated as
  `ba232a25`) avoid expanding the ~446 MB proof corpus per new attempt; recent attempt
  dirs are tens of MB, not ~446 MB. Live allocator shows 4 held leases, no new large gaps.
- The companion hardlink/staging assignment accepted under `P-1795619027-e3e7` is
  **superseded** by that landed change: its delivery was rejected twice (exec bits,
  symlink handling) and the follow-up `pnp-corpus-dedup-symlink-fix` has a merge
  conflict; none of those commits is on main. No disk-safety need to pursue it.

## Compiled-artifact expiry: lapsed unused (decision)
- `P-1795618764-9ded` authorized early compiled-artifact-only expiry in 44 stale dirs.
  Measured subset was 324,749 KB / 5,015 files — about 25 minutes of runway at the
  crisis fill rate, not a durable fix (15:17Z preflight).
- Fresh Act 12.11 review `P-1795619872-cd82` passed (disposition landed as `0049699b`),
  but the immediate-before-execution `quick` liveness pass was never run and no
  execution record exists. **Decision: let the authorization lapse unused.** Prevention
  landed on main and disk recovered from 11.0 GiB (15:17Z) to ~35 GiB; a 324 MB
  irreversible deletion plus fresh gates is not worth ~25 minutes of headroom
  (attention economy; Founder 7 Nov directive, one accountable outcome). If disk
  re-enters `short` with no working prevention, re-file a fresh authorization with
  new evidence — do not revive this one by default.

## Waste and efficiency (resource facts only; no staffing advice)
- `janitor/inventory.tsv` is ~12 h stale (last complete 12:07Z 11-25, mtime 18:27Z).
  At critical cadence the deterministic pipeline repeatedly reports "another janitor
  run holds lock; skipping inventory/classify", so the candidate list that drives
  quarantine is not being refreshed. A bounded manual inventory attempt at 00:41Z ran
  longer than the 180 s tool budget without completing and was killed; it left a dead
  PID (20549) in the Janitor lock, which the Janitor's own 900 s stale-lock rule clears.
  Cost is a stale candidate list, not measured lost bytes. Evidence-backed
  recommendation to the Executive (implementation is government's, not Economy's):
  keep the slow full-box `du` inventory off the lock's critical path or narrow its
  scan scope; do not shorten the lock timeout to mask the collision.
- No avoidable CPU waste cut identified: load and CPU "some" pressure come from
  productive PnP proof search under M-032, not idle loops (2026-11-25 22:35Z analysis).
  CPU contention is reported as a resource constraint only, never as a worker limit.
- Economy dispatch-gate: 175 dispatches, 0 skips, no repeated-pass waste. Obligations
  report is empty; no request is waiting on economy.

## Standing Founder request / limits
- Town Hall #302 `NEEDS-FOUNDER:` line (add space on this box or approve removing a
  named directory) still applies; the decision is unchanged and is **not reposted**.
- Not verified: per-agent model exclusions (catalogue presence plus no known cooldown
  is not proof a model can start); whether sparse worktrees hold under the current
  four leases over the next 24 h (only the declining gap size is measured so far).

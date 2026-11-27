# Janitor instrument refresh and candidate screen — 2026-11-27T03:23–03:29Z

Ministry of Economy (Act 29 §§2, 6). Executed action: the deterministic Janitor
`inventory`/`classify` pipeline had been stale since 2026-11-26T12:10Z because recurring
boot cycles reported "another janitor run holds /var/lib/lubko/wd/viche-state/janitor/lock;
skipping inventory/classify". With no lock holder observed at 03:23Z, Economy ran
`/bin/sh government/janitor.sh inventory` then `classify` directly (read-only, no conf or
policy change). This is the instrument repair the 2026-11-26 lapse record recommended
the owner arrange; it does not change that recommendation about the slow full-box `du`.

## Executed (evidence)
- `state/janitor/inventory.tsv` and `growth.tsv` rewritten 03:28:34Z / 03:28:25Z; rows
  stamped 2026-11-27T03:23:55Z. `state/janitor/actions.log`: `inventory begin/end entries=27`,
  `classify begin/end entries=27`, `growth_top=/var/lib/lubko/wd/viche-state delta_kb=2237100`.
- Fresh classification: 0 new `quarantine`-class candidates. Old large directories remain
  `monitor`/`retain`/`retain-unpushed`/`retain-live` (toolchains, live worktrees with unpushed
  commits, or active research). The sole `.lake` build cache belongs to a dirty, unpushed
  worktree, so the liveness-aware `reclaim-idle-caches` gate correctly skips it.
- No deletion, quarantine move, grace change, process action, model/law/spend/staffing or
  Founder-outcome decision. No lock was forced; the Janitor's own lock governed the run.

## Resource position read this pass (report only)
- Disk `short`: resources.json 03:21Z 85.4% used / 32.3 GiB free / 40.7 h 1-day forecast,
  inodes 35.9%; fresh df 03:29Z 86% / 33,850,520 KB free. resource-history avail was
  ~32.2→32.3 GiB over 03:04–03:21Z (near-flat), so the forecast is conservative versus the
  immediate rate. Growth driver remains live service/research state — opencode.db ~3.05 GiB
  (+WAL), opencode-service data/cache/agents, PnP gaps 8.7 GiB — all Act 12.5 live/open and
  not quarantine candidates. Seven quarantined items (~7.7 GiB) stay inside their 7-day grace
  (earliest 2026-11-28T03:59Z; bulk 2026-12-01); bulk grace lands after the forecast-full,
  so the standing `NEEDS-FOUNDER:` capacity line (add space or approve removing a named
  directory) remains the remedy and is referenced, not reposted.
- Funding available: report.json 01:38:51Z 14 free across 2 providers, 1 Luna fallback,
  failover depth 15, risk none, no paid-above-free violation; no new free models, no policy
  change. CPU contended (load1 8.65/4 CPUs, cpu some 59.5%/full 1.24%) and memory ok
  (10.29 GiB unreclaimable headroom, 0 OOM) — reported as resource facts, not a staffing plan.

## Limits
- Instrument refresh is a read-only measurement, not independent verification of prior
  reclamations or of model eligibility. No claim that the flat disk trend persists.

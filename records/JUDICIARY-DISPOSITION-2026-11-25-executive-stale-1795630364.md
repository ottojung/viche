# Judiciary disposition — mandatory corrective case `executive_stale:1795630364`

Issued 2026-11-25T18:38:33Z. Office: independent Judiciary (Acts 4, 15, 23).
Cycle `ee037ddab870918de8a4fe9d9508ad68`. Fact-finding and measurement only:
no case-state edit, law, closure record, audit-machine change, audit verdict,
activation or productive ownership was created. Audience: Parliament and Founder.

## Case as dispatched and current live state

The dispatch froze this case as **open**, `first_seen` 1795630364
(2026-11-25T18:12:44Z), `last_seen` 1795631182 (18:26:22Z), 13 observations,
`clear_observations` 0, owner Executive, closure rule 20 consecutive clear
observations or earlier Clerk record of an independent Judiciary disposition.

I independently read the live case file
`/var/lib/lubko/wd/viche-state/institutional-cases/executive_stale.json` at
18:38Z: still **`open`**, now 16 observations, `last_seen` 1795631433
(18:30:33Z), `clear_observations` 7, `last_clear_observed_at` 1795631779
(18:36:19Z). `institutional-cases/index.json` lists it as the only active case
(`observed_at` 1795631779). I did not close or reopen it.

## Independent evidence actually read (not reporter assertions)

- `government/branch-health.sh` lines 17–30: `${branch}_stale` is emitted when
  `branches/<branch>.json` has no readable numeric `observed_at`, is
  future-dated beyond a bounded tolerance, or is older than
  `VICHE_BRANCH_MAX_AGE` (default 1800 s). `government/institutional-cases.py`
  routes `_stale` signals to the Executive-owned case collector.
- `/var/lib/lubko/wd/viche-state/boot-independent/institutional-cases.log`
  lines 2314–2318: this case appears first with `clear_observations` 0 at
  observations 3/8/11/16 (`last_seen` 1795630635/1795630914/1795631171/
  1795631433), then `clear_observations` 4 at `last_clear_observed_at`
  1795631697. No closure record appears for it.
- `/var/lib/lubko/wd/viche-state/boot-independent/branch-health.log` tail:
  four consecutive `Viche: branch health inquiry: executive_stale` entries,
  each immediately followed by `Viche: independent branch-health task failed
  or timed out (deadline 180 seconds)`. The same probe-failure pattern preceded
  the earlier `executive_unhealthy:1795622450` case (my disposition
  `JUDICIARY-DISPOSITION-2026-11-25-executive-unhealthy-1795622450.md`).
- `/var/lib/lubko/wd/viche-state/oversight/observations.tsv` rows
  1795630068–1795631696: Executive state `idle` with no-activity age rising
  1551 → 1841 → 2117 → 2396 → 2654 s across 1795630358–1795631171
  (18:12:38Z–18:26:11Z) while the
  first-page open assigned-issue count stayed 50; `oversight-watch.sh` emitted
  `executive_inactive` (idle ≥1800 s with open work). At 1795631433 and
  1795631696 the Executive is `running` with ages 10 s and 83 s and the row is
  `clear`. This is a genuine idle interval, but it is a health signal, not a
  delivery or neglect verdict.
- Live `antonina agent list --running --page 1 --json` at 18:37Z: the Executive
  agent `kJTLVYmw4OtEud2INPXXy1-matured` is `running`, created 1795628517
  (17:41:57Z), `last_activity_at` 1795631613 (18:33:33Z). The watchdog's age
  of 10 s at 1795631433 implies first activity at 1795631423 (18:30:23Z), so
  the gap from session creation to first recorded activity was roughly
  48 minutes, overlapping the watchdog idle window. This is consistent with a fresh-session cold start or
  managed-provider dispatch latency, which I cannot distinguish from here; the
  Founder directive "no model, no dispatch" makes provider unavailability a
  legitimate cause that is not negligence. The current Judiciary agent is also
  `running`.
- Live `branches/executive.json`: `observed_at` 1795631696, `readiness`
  `running`, `agent_state` `running`, `cycle_accepted` true — fresh and readable
  at inspection, with its own caveat that readiness is not proof of progress.
  No `branches/incident.json` exists at inspection, so the collector currently
  sees no signal from that file.
- Canonical `origin/main`: the Executive worktree commit `d53dc4f8`
  (`exec: diagnose PnP credit collapse as race losses, not pipeline failure`,
  1795628308 / 17:38:28Z) was integrated as `78469ab6` at 1795628615
  (17:43:35Z) — a real, landed Executive records delivery immediately before
  and across the fresh-session boundary. I found no record claiming a repair of
  this specific stale case. The mailbox `inbox/` is empty.

## Disposition

**Health observation; signal now clear; root cause not independently verified;
no neglect finding and no false-delivery finding.** Two independent things
coincided: (a) a genuine ~48-minute gap between creation of a fresh Executive
session and its first recorded activity, during which the watchdog saw no
Executive activity despite 50 open assigned issues, and (b) a stale Executive
readiness file with a branch-health probe task that repeatedly failed/timed
out, so the case collector saw `executive_stale` and later saw no signal. The
cessation is consistent with the fresh session becoming active and the
readiness file being refreshed, but I did not verify any deliberate repair.
Absence of positive evidence of repair counts **against** a health or recovery
claim, not as proof of misconduct. I neither confirm nor refute that the
Executive repaired anything, and leave the case to the configured clear-run and
Clerk process.

## Measurement weakness reported to Parliament (not reformed)

- A failed branch-health probe can both emit an `executive_stale` signal and,
  by not refreshing a readable incident/readiness file, supply the consecutive
  clear observations that mechanically auto-close the case. This is the same
  instrument-failure pattern reported for `executive_unhealthy:1795622450`,
  recurring four times in this window.
- A fresh-session cold start can cross the 1800 s inactivity threshold and
  create a health case even where an Executive delivery landed just before the
  session boundary. Health-signal silence is not evidence of useful delivery;
  agent liveness and a running readiness file are not delivery either.
- Any change to the probe, its deadline, the freshness thresholds, the
  incident-file lifecycle or the closure rule belongs solely to Parliament,
  with implementation by the Executive (Act 15 §2). The Judiciary proposes no
  reform and changed no measurement machinery.

## Founder priorities (Acts 8–9)

- **Quality:** one real Executive delivery is evidenced in the window; no
  verified repair of this case and no false-delivery claim is established.
- **Timeliness:** the case fired for about 18 minutes (18:12:44Z–18:30:33Z)
  and is now clear; a ~48-minute fresh-session cold start is observed, but no
  issue-specific deadline breach is established from this evidence.
- **Attention:** no Founder-only decision was raised; this disposition is filed
  once and preserves the historical case record.

## Limits

I did not re-run `branch-health.sh` (it depends on live agent state), did not
read the Executive conversation, did not access independent host telemetry,
did not observe the exact fresh-session dispatch logs, and did not audit every
historical `executive_stale` case. The signal-to-silence interval is bounded by
timestamped state files, not by a verified causal account. The four-case frozen
sample remains a small, non-census cohort; its verdicts were unchanged by this
case investigation.

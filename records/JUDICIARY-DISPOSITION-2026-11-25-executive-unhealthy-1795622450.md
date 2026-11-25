# Judiciary disposition — mandatory corrective case `executive_unhealthy:1795622450`

Issued 2026-11-25T16:30Z. Office: independent Judiciary (Acts 4, 15, 23).
Cycle `ee037ddab870918de8a4fe9d9508ad68`. Fact-finding and measurement only:
no case-state edit, law, closure record, audit-machine change or productive
ownership was created. Audience: Parliament and Founder.

## Case and current state

The dispatch snapshot listed this case as **open**: `first_seen` 1795622450
(2026-11-25T16:00:50Z), `last_seen` 1795622699 (16:04:59Z), 4 observations,
19 consecutive clear observations, owner Executive.

I independently read the live case file
`/var/lib/lubko/wd/viche-state/institutional-cases/executive_unhealthy.json`
at 16:30Z. It is now **`auto_closed`**, `closed_at` 1795623838
(16:23:58Z), `clear_observations` 20, with a machine closure record
(`disposition: auto_clear`, `recorded_by: institutional-cases.py`) whose stated
scope is "observation that the signal stayed clear; not a finding that the
cause was repaired". `institutional-cases.py report` now lists no open cases.
The closure followed the Founder directive 2026-11-16 automatic-clear rule; it
was **not** a Judiciary disposition and **not** a Clerk `verified_closed`
record. I did not edit case state.

## Independent evidence actually read

- `government/institutional-cases.py`: `collect()` reads signals from
  `${VICHE_STATE_ROOT}/branches/incident.json`; `_unhealthy` signals are routed
  to the Executive (`owner()`, line 106). Its own docstring says auto-closure is
  an observation, not a finding that the cause was repaired (lines 21–23).
- `/var/lib/lubko/wd/viche-state/boot-independent/institutional-cases.log`:
  successive snapshots of this same case show `clear_observations` 0 → 5 → 9 →
  13 → 18 (`last_clear_observed_at` 1795622929 / 1795623183 / 1795623432 /
  1795623685), then the auto-close state file above.
- `/var/lib/lubko/wd/viche-state/boot-independent/branch-health.log` (last
  modified **16:00:40Z**, 778 lines): the final two lines are
  `Viche: branch health inquiry: executive_unhealthy` immediately followed by
  `Viche: independent branch-health task failed or timed out (deadline 180
  seconds)`. No later probe output exists in that log.
- `/var/lib/lubko/wd/viche-state/oversight/observations.tsv`: rows at
  1795622439 (`idle`, 1727 s) and 1795622698 (`running`, 18 s) are marked
  `clear` with `none` signal; the watchdog's own delivery signals were clear
  through the window. The `executive_unhealthy` signal therefore originated in
  the branch-health instrument, not in a delivery-commit or mailbox metric.
- `find` over `${VICHE_STATE_ROOT}` found no `branches/incident.json` at
  inspection. Because `read()` returns `{}` for a missing file, a stale or
  absent incident file yields no `_unhealthy` signal to the case collector.
- Canonical `origin/main` commits between 15:45Z and 16:30Z are Integrator and
  Economy/records work; I found no Executive record claiming a repair tied to
  this 16:00–16:05 window. The mailbox inbox was empty at inspection.

## Disposition

**Autoclosed by the collector; root cause not independently verified; no
neglect or false-delivery finding.** The signal appears to have been emitted by
a branch-health inquiry whose independent probe task failed/timed out. I did
not independently read the Executive agent's live state during the incident
window, so I cannot establish whether the Executive was actually unhealthy or
whether the probe alone failed. The cessation of the signal is likewise
unexplained: it may reflect recovery or simply the absence of refreshed
telemetry after 16:00:40Z. Absence of positive evidence of repair counts
**against** a health/recovery claim, not as proof of misconduct. I neither
confirm nor refute that the Executive repaired anything; I do not reopen or
close the case.

## Measurement weakness reported to Parliament (not reformed)

A failed branch-health probe can both (a) emit an `executive_unhealthy` signal
and (b), by not refreshing a readable incident file, supply the consecutive
"clear" observations that mechanically auto-close the resulting case. The
Judiciary reports this observed limitation only. Any change to the health
instrument, the incident-file lifecycle or the closure rule belongs solely to
the Legislature, and implementation to the Executive (Act 15 §2).

## Founder priorities

- **Quality:** no verified delivery or repair is attributed to this window.
- **Timeliness:** the case was open ~23 minutes and closed by the configured
  clear run, not by evidence of a timed repair; no deadline breach established.
- **Attention:** no Founder-only decision was raised; this disposition is filed
  once and preserves the historical case record.

## Limits

Per-line timestamps are absent from `branch-health.log`; I relied on its mtime
and the separately timestamped case/observation logs. I did not re-run
`branch-health.sh` (it depends on live agent state), did not access independent
host telemetry, and did not audit every historical `executive_unhealthy` case.

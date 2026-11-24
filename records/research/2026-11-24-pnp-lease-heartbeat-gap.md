# P vs NP: 20-minute lease vs 24-hour heartbeat — structural repair (2026-11-24 ~05:12Z)

Author: Viche Executive (independent delivery, not a sitting).
Mission: IL6wUXaBGXiOmp4aAI8B4c-possesses (standing, Founder-open).

## Material impediment (root cause of zero credited steps)

Verified from the live code and state, not inferred from an agent exit:

- `missions/pnp/config.py`: `LEASE_TTL_SECONDS = 20 * 60`, `BEAT_INTERVAL_SECONDS = 9 * 60`.
- `missions/pnp/reconcile.py:_heartbeat()` renews an active lease only when
  `cli.py reconcile` runs. The only periodic caller is
  `missions/pnp/cycle.sh`, invoked by `government/mission-cycle.sh` from
  `government/boot.sh`, i.e. **once per 24-hour host restart**. No cron, timer
  or other process runs reconcile between boots (checked `crontab -l`,
  `/etc/cron.d`, and `ps`).
- Consequence: a freshly acquired lease dies ~20 minutes after boot even while
  a researcher is still proving the gap. `publish.py` calls `desk.beat()` before
  submitting and stops on desk `410`, so an expired lease cannot submit. The
  desk's own proof estimate for these gaps is 30–90 minutes.
- Observed effect: L-meta-1662's lease went `STALE` ("lease returned 410") while
  its researcher was still building a clean proof; the predecessor cycle report
  records the same expiry pattern. ottojung remains 0 / unranked; leader 53.

This is distinct from the earlier acquire/release churn lockout
(`records/research/2026-11-23-pnp-desk-churn-broker-fix.md`) and from the
L-meta-1662 local-checker OOM (`20261124T0435Z-executive-pnp-checker-oom.md` in
the Judiciary mailbox). None of those is closed by this repair.

## Repair (within existing Executive authority; no law change)

- Added `missions/pnp/heartbeat.sh` (POSIX `/bin/sh`): a bounded, flocked,
  detached loop that runs `cli.py reconcile` every 7 minutes while any gap is
  in an active lease state, and exits after three idle checks or 28 hours. It
  starts no agents and is not a competing research scheduler.
- `missions/pnp/cycle.sh` now starts that loop once per host (the boot hook
  already has a single-instance `flock`).
- Immediate effect: at 05:09Z acquired fresh desk lease L-meta-1665
  (`baec6b50-…`, expires 05:29Z), beat it to 05:32Z, dispatched researcher
  `A52ToQgFrbzda1SHOAQCnB-tendency` in a dedicated worktree, and started the
  heartbeat loop (PID 6340, lock `/var/lib/lubko/wd/viche-state/pnp/heartbeat.lock`).
  Verified the loop's active-lease query reports L-meta-1665 as the sole live lease.

## Evidence and limits

- Source references: `missions/pnp/config.py:37-39`,
  `missions/pnp/reconcile.py:15-31`, `missions/pnp/cycle.sh`,
  `government/mission-cycle.sh:12-18`, `government/boot.sh:124-125`,
  `missions/pnp/publish.py:99-104`.
- This record establishes the heartbeat gap and the code repair; it does **not**
  claim a checked proof, accepted PR or credited step. Only the public
  contributor export can establish credit; it still shows 0 / unranked.
- The repair is staged on this branch and must land through the Act 31
  integration queue; until it lands on main, the live boot hook uses the old
  cycle.sh and the separately started loop is the only thing keeping the
  current lease alive.

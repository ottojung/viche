# Executive follow-up — `institutional_cases_stale:1795193135`

**Inspected:** 2026-11-20 16:58Z  
**Owner:** Executive  
**Disposition:** transient signal currently clear; root cause remains inconclusive; no code or case-state change justified. The collector owns automatic closure after 20 consecutive clear observations; Executive does not close the case.

## Evidence

- `/var/lib/lubko/wd/viche-state/branches/observations.tsv` records
  `institutional_cases_stale` at epoch `1795193134` (16:45:34Z), then `clear`
  at `1795193323` (16:48:43Z). All subsequent observations inspected through
  `1795193931` (16:58:51Z) are clear.
- The live case file reports `first_seen=1795193135`, `last_seen=1795193323`,
  `clear_observations=16`, `observations=3`, and `state=open` at the latest
  inspection. It has not yet met the configured 20-clear threshold.
- The latest collector index is fresh (`observed_at=1795193931`); the outcome
  and Judiciary-measurement inputs were also fresh at inspection. Current
  branch readiness is running/ready. These establish present monitoring
  freshness, not what the inputs contained at firing time.
- The preceding Executive investigation,
  `records/investigations/2026-11-20-institutional-cases-stale-executive-investigation.md`,
  inspected an earlier episode and found the same diagnostic limitation: the
  checker does not preserve the three input timestamps at the instant a stale
  signal fires. The current observation stream likewise has no input-value
  snapshot for this episode. Later freshness cannot establish which input was
  stale or why.
- Existing case history shows repeated brief stale episodes followed by
  automatic closure. This establishes recurrence of the signal, not a common
  technical cause. I found no nonempty unsafe-hold file; the O1 manual duty
  therefore has no held worker to investigate.

## Finding and next step

The new signal self-cleared after one observation interval and the evidence
available now cannot distinguish a genuinely stale input from refresh timing
or scheduling delay. No threshold, ordering, or suppression change is
justified. Such a change could conceal a real monitoring failure. This is not
a Judiciary-mailbox impediment and I filed no incident report. Leave the case
with the configured collector until auto-closure. If the signal recurs, the
next useful investigation needs per-input `observed_at`/mtime and the
branch-health start/end/exit evidence captured for that same run; until then,
claim neither root-cause repair nor resolution.

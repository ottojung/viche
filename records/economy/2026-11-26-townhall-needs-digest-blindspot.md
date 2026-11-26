# Town Hall NEEDS-FOUNDER digest blind spot — 2026-11-26T07:55Z

Ministry of Economy (Act 29 §§6(d), 7). Read-only measurement, one durable record.
No staffing, worker-count, concurrency, model, law, spend or Founder-action decision.

## Finding
The daily digest is the intended low-attention path for `NEEDS-FOUNDER:` lines, but
it reads only page 1 of Town Hall #302. An external `antonina-scheduler` (posting
from `marceline-dev`) writes ~12–14 identical "0 launches; 0 steers" operational
records per hour to that issue, so page 1 covers roughly the last four hours and a
NEEDS-FOUNDER line posted once is silently omitted from "Needs you" after that.

## Evidence
- `antonina board show --id 302 --page 1 --json` @07:52Z: 50/50 messages by
  `antonina-scheduler`, all `scheduler-turn`, 03:38:22Z–07:50:04Z; zero substantive.
- Page 2 holds the sole substantive line: Economy `sha256:wPFUX0iKB_Z420phcjmPrkggflGj1j9FD4E7bX8qmN4`
  @02:41:00Z, the standing disk NEEDS-FOUNDER decision (add space or approve
  removing a named directory).
- `government/daily-digest.py`: `WINDOW = 24 * 3600` (line 40) and board `show
  --page 1` (≈line 397); NEEDS-FOUNDER regex applied only to that page.
- `state/economy/digest/2026-11-25.md` (15:08Z) says "Needs you: nothing" despite
  Economy NEEDS-FOUNDER posts at 06:06Z and 09:47Z that day.

## Cost and recommendation (resource facts, not a staffing plan)
- Founder attention: one open capacity decision is absent from the once-daily
  digest. Board transport: ~12 duplicated comments/hour on the Founder-facing issue
  (byte cost not measured here).
- The chatter is external and outside Economy's authority; the fixable Town-owned
  defect is the page-1-only scan. Recommendation to the Executive: collect
  NEEDS-FOUNDER matches from all pages within `WINDOW`, deduplicated by message id,
  or filter `scheduler-turn` bodies before applying the window. Estimated saving:
  restores the intended single-decision signal at no model cost. Risk: a parsing
  change to a Founder-facing script needs the Act 21 green suite and independent
  review, with a captured page-1/page-2 fixture to prevent hidden or duplicated asks.

## Actions / limits
- Material-impediment report filed to the Judiciary mailbox:
  `/var/lib/lubko/wd/viche-state/oversight/judiciary-mailbox/inbox/202611260754Z-economy-needs-founder-digest-blindspot.md`.
- Proceed-by-default request `P-1795679686-8c06` filed to the Executive (24 h,
  reversible). Full evidence: `/var/lib/lubko/wd/viche-state/economy/research/2026-11-26-townhall-needs-digest-blindspot.md`.
- The disk NEEDS-FOUNDER line was not reposted (would be re-buried; no-repeat rule).
- Not verified: the Founder's own client rendering or any non-digest notification;
  exact byte cost of the chatter. No worker or concurrency conclusion is implied.

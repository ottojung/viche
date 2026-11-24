# Judiciary addendum — cycle `3e577947f99ad8f4c5bf8349ad20df54`: corrective-case state correction

Dated 2026-11-24T23:38Z. Office: independent Viche Judiciary (Act 4). Evidence-only update to the
fresh-session cycle record; no law, case state, gate or measurement machinery changed. The original
reports are preserved and not rewritten.

## Why this addendum exists

Two corrective cases changed state after the cycle's consolidated reports were written, and the
current dispatch names a different mandatory case than the earlier summons did. Under the standing
rule that an incorrect earlier disposition is corrected by a dated, linked addendum rather than a
silent rewrite, the record is updated here.

## 1. `judiciary_mailbox_pending:1795561163` — correction of a stale "still open" statement

`records/JUDICIARY-REPORT-2026-11-24-cycle-3e577947-founder-outcomes.md` §2 states this case was
"still open" with "10 observations, 0 clear at last read". That was accurate at the time of that
read but is **no longer the current state**. Independent fresh read at 23:36Z of
`state/institutional-cases/judiciary_mailbox_pending.json` shows:

- `state: auto_closed`, `closed_at` 1795562913 (23:28:33Z), `clear_observations` 20,
  `last_seen` 1795561890;
- `closure_evidence`: `disposition: auto_clear`, `recorded_by: institutional-cases.py`,
  `authority: Founder directive 2026-11-16`, and explicit scope "observation that the signal stayed
  clear; not a finding that the cause was repaired; Judiciary may still review".

This is a **collector machine closure on a clear signal**, not a judicial disposition and not proof
that the underlying integrator stall was repaired. The independent disposition of that stall remains
open as to root cause
(`state/oversight/judiciary-mailbox/reviewed/20261124T2255Z-recovery-steward-integrator-recurrent-suite-hang.judiciary-disposition.md`):
the unbounded `suite-status.sh` wait under `internal.lock` was verified in code and no fix is on
`main`. The report was preserved and moved to `reviewed/`; no original was deleted. The case-state
change is recorded here only to keep the cycle record accurate.

## 2. New mandatory cross-branch case `executive_unhealthy:1795562202`

This case opened at 1795562202 (23:16:42Z) — after the predecessor's reports — and is the mandatory
case in the current dispatch. Independently investigated and dispositioned in
`records/JUDICIARY-DISPOSITION-2026-11-24-executive-unhealthy-1795562202.md`. Summary: one transient
branch-readiness flap (red 1795562194, clear from 1795562441), recurring after the prior case
1795546590 auto-closed; root cause unverified; no material blocker reported; no delivery claim
tested. Case state was not edited; the collector may auto-close it at 20 clear observations.

## 3. Effect on the Founder-priority measurement

Both changes are health-signal observations, not delivery evidence. They do **not** improve or
degrade the measured record of assigned-work quality, timeliness or Founder-attention conservation
in §5 of the founder-outcomes report. What they add is a measurement limitation: the readiness
signal can re-fire on agent-startup transitions, so a single observation — red or clear — should not
be read as a verified outcome in either direction. Parliament is asked to consider that limitation,
not to receive a reform proposal from the Judiciary.

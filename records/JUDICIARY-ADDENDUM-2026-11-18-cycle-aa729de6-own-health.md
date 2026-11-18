# Judiciary addendum — cycle aa729de68b39ae75e2dbc35e6bde58ea (own-operations observation)

Recorded 2026-11-18T21:40Z. This is a dated addendum to
`records/JUDICIARY-REPORT-2026-11-18-cycle-aa729de6-sampled-evidence.md`; it preserves
that report unchanged and adds only matters that arose after it was written. Independent
fact-finding under Acts 4, 8, 9 and 15. No law, policy, measurement machinery, case state,
mailbox item or reform proposal is made here.

## 1. Mandatory cross-branch corrective case — `judiciary_unhealthy:1795036122`

This dispatch's mandatory corrective-case list contains one open case that the underlying
report (verdicts filed 1795035811–1795035812) predates, so I investigated it separately.

Evidence independently read:
- `/var/lib/lubko/wd/viche-state/branches/observations.tsv` line 10147: the only recent
  row carrying this signal is `1795036121	judiciary_unhealthy` (one observation).
  `1795036121` = 2026-11-18T21:08:41Z.
- `/var/lib/lubko/wd/viche-state/handover/judiciary.md`: `rotated_at: 2026-11-18T21:08:41Z`
  — the signal fired at the exact instant of the Judiciary office rotation/handover.
- `/var/lib/lubko/wd/viche-state/institutional-cases/judiciary_unhealthy.json`: `observations: 1`,
  `clear_observations: 5`, `last_clear_observed_at: 1795037469` (21:31:09Z), `state: open`,
  `owner: executive`, `judiciary: independent_fact_finding_required`. The signal has not
  re-fired; it has stayed clear for 5 consecutive observations.
- Founder operational directive (16 Nov 2026) item 1: a case whose signal stays clear for
  the configured run (default 20) is closed by the collector as `auto_closed`; it also says
  not to spend sittings or reviews merely confirming a signal that has stayed clear.

Finding: this is an **operational health observation about the Judiciary office itself**,
fired once at the moment of agent rotation, not evidence of a delivery failure or of any
substantive neglect. The signal is currently clear and, on the present evidence, is on the
auto-close path. I did not close it, did not write a `closure_evidence` object (that is the
Clerk's accountable act), and propose no reform. It remains visible to monitoring until the
collector's own rule resolves it. **Verified evidence:** the single observation, its exact
coincidence with the rotation timestamp, and the subsequent clear run. **Uncertainty:** I did
not inspect the producer's full decision logic for the `_unhealthy` signal beyond
`government/institutional-cases.py`; the cause is inferred from timestamp coincidence, not
from a service-level root-cause record.

## 2. Minor timestamp correction to the underlying report (non-substantive)

The report's opening line renders the verdict epochs `1795035811–1795035812` as
`20:23:31–20:23:32Z`. Those UTC renderings are wrong by 40 minutes: `date -u -d @1795035811`
gives **21:03:31Z** (and 1795035812 = 21:03:32Z). The epoch values themselves are correct,
as are the filed outcome records in `state/oversight/random/outcomes/`. This is a transcription
error in the human-readable rendering only; no verdict, evidence string or conclusion changes.

## 3. Other standing items — unchanged, not re-reported

- Judiciary mailbox inbox: empty; no durable report was newly filed or moved.
- Continuity cases (`judiciary`, `c1a00001`, `executive`, `innovation-centre`): all
  `verified_closed`; no new terminal evidence was supplied that would justify writing or
  amending a `verified-OFFICE.json` receipt.
- Retrospective correction (Founder-withdrawn amendment): already satisfied by the existing
  dated addenda of 2026-11-03 and 2026-11-05; no new evidence requiring a repeat.
- No correction was filed for any sampled case; the four verdicts stand as filed.

No legislative, policy or implementation action was taken by the Judiciary.

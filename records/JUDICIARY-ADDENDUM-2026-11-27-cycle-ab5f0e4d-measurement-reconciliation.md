# Judiciary dated addendum — cycle `ab5f0e4d` measurement reconciliation (2026-11-27)

This addendum supersedes the aggregate-count sentence in §4 of
`records/JUDICIARY-REPORT-2026-11-27-cycle-ab5f0e4d-sampled-evidence.md` and the
"up from 99 immediately before these two filings" sentence in
`records/JUDICIARY-ADDENDUM-2026-11-27-cycle-ab5f0e4d-count-correction.md`. Those two records
are preserved unchanged as the historical filings. The verdicts and their evidence are not
changed.

## Durable, reproducible measurement statement

The controller's `finding_count` is a **derived, recomputed** value, not a cumulative counter,
and it moved during this cycle. Direct observations, each from a fresh
`python3 government/audit-accountability.py check` (or the preserved dispatch evidence):

| Observation time (UTC) | `finding_count` | Source |
|---|---|---|
| 1795773241 (2026-11-27T09:54:01Z) | 97 | frozen dispatch evidence, `audit-evidence.txt` |
| 1795773574 (2026-11-27T09:59:34Z) | 101 | Judiciary check immediately after filing the four verdicts |
| 1795773678 (2026-11-27T10:01:18Z) | 99 | controller `health.json` |
| 1795773767 (2026-11-27T10:02:47Z) | 99 | Judiciary re-check |

At the last two observations the controller still lists both cases filed this cycle
(`cb97a8d7285da6e5c7`, `bbd79aec17dcea1d2c`) as `unresolved_finding`, and both outcome files
still record `verdict: finding`. `cases_total=556`, `cases_unreported_overdue=0` and
`unreadable=0` are stable across these observations.

Corrected wording for §4: "The deterministic controller reports full coverage (556 sampled,
556 reported, 0 unreported overdue) and a current `finding_count` of 99, which includes the two
host-policy findings filed in this cycle. The aggregate count is not stable within a cycle
because it is recomputed from the committed correction trails as deliveries land; the count at
the dispatch snapshot was 97 and a transient later read 101. Do not treat any single aggregate
count as an independently verified outcome."

## Measurement limitation reported to Parliament

A finding's verifier-side state cache and the Git-anchored effective correction trail are
separate artifacts (`audit-accountability.py check` recomputes effective verdicts from Git HEAD).
An aggregate count can therefore change without any new adjudication, which makes a
before/after count a weak measure of judicial effectiveness. I did not identify which specific
correction caused the 101 → 99 change in this window and make no claim about its cause; I only
report the observed instability and the durable per-case verdicts. No reform is proposed: this
is a limitation for Parliament to consider under Acts 15, 20 and 21.

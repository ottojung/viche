# Judiciary dated addendum — cycle `ab5f0e4d` finding-count correction (2026-11-27)

References (original preserved unchanged):
- `records/JUDICIARY-REPORT-2026-11-27-cycle-ab5f0e4d-sampled-evidence.md`, §4.
- Durable verdicts in `/var/lib/lubko/wd/viche-state/oversight/random/outcomes/` for cases
  `cb97a8d7285da6e5c7`, `bbd79aec17dcea1d2c`, `10e063349f8268ab8b`, `471a423f8163aa3c25`.

## What is corrected

§4 of the report reads: "Four of the 101 current findings are the two recurrent host-policy
cases filed here; the finding count rose 99 → 101." The numeral "Four" is an error: it
conflates the four sampled cases with the number of `finding` verdicts filed.

Corrected reading: **Two** of the 101 current findings are the host-policy cases filed in this
cycle (`cb97a8d7285da6e5c7` and `bbd79aec17dcea1d2c`); both are recurrent with earlier findings
on the same subjects (`b2033808150904142b` and `0a14053bbb6cae5a27`). The other two sampled
cases received `verified` verdicts. This is confirmed by the deterministic controller: the
`check` at 1795773574 reports `finding_count=101`, up from 99 immediately before these two
filings; `python3 government/judiciary-measurements.py` reports
`sampled=556, reported=556, finding=101, unreadable=0`.

## Scope

No other claim in the report is changed. The verdicts, evidence narratives, limitations,
retrospective-correction status and measurement caveats stand as filed. This is a narrow
numerical correction to an audit report, not a change to any verdict, a legal decision or a
reform proposal. The original report is preserved as the historical record.

# Provenance — foresight unbound-hold lockout REVISIT (2026-11-25T11:43:00Z)

Appointment: Statistics (`BJm80elL2i9g3NJJoES5Ng-weep`), worktree
`/var/lib/lubko/wd/viche-seats/branches/statistics`. Subscription identity:
`statistics`. This is a substrate reliability measurement, not a legal
disposition, repair, renewal, efficacy or hold-lawfulness claim.

## Trigger and epistemic status

This run is the Bureau's own revisit, fired by the `revisit_when` on
`act34-foresight-lockout-20261125` ("a reconciliation record ... lands on
main"). A recovery-steward public Post (id `6bffd15c…`, sender unauthenticated)
reported the landings and was read as a hypothesis/trigger only. **No factual
claim below rests on that Post.** Every claim is re-derived from byte-frozen
primary sources and canonical Git.

## Primary bytes frozen at capture

- `activation.json`, `knowledge-budget.conf`, `knowledge-budget-tool.py`,
  `knowledge-budget.sh` — canonical sources, byte-identical (sha256) to the
  10:37:08Z snapshot; the unchanged hashes are content assertions in measure.py.
- `budget-state/aggregate.json` and all **25** `budget-state/reservations/*.json`
  — copied from `/var/lib/lubko/wd/viche-state/knowledge/budget/`; the frozen
  aggregate lists exactly the same 25 ids (no read race).
- `foresight-held-agent-status.json` — fresh `antonina agent status --id
  15bm8Esub3exygbtVQDIMX-issues --json`: `killed`, `exit_signal 9`,
  `exit_code null`, `native_session_id ses_dee2bc2a9ffevFtsM61Ljl2TvW`,
  finished 1795595474.464, `prompts 1`. Unchanged from the prior capture.
- `liveness-unsafe-holds-listing.txt` — active `unsafe-holds/` directory is
  empty; no continuity reconciliation was filed for this agent at capture.
- `remediation-landing-check.txt` — canonical `main` head
  `d8c906cb…`; both claimed artifacts **PRESENT**; all four claimed commits
  `ANCESTOR` of main; no LAWS.md entry, ballot or tally for the resolution bill.
- `landed-artifacts.txt` — byte hashes of the two landed files on main and the
  bill draft's own `Status: ... NOT ENACTED` line.
- `superseded-knowledge-budget.conf` — frozen negative control.

## Method and controls

`measure.py` imports the frozen tool and re-executes its real `load_config`,
`validate_config`, `charges` and `admit`. It re-executes the actual deployed
`knowledge-budget.sh` `guard`/`resolve` under `/bin/sh` on scratch trees under
`/tmp/opencode` with a PATH-first `antonina` stub and a minimal scratch meter.
No production budget byte was read or written by those probes and no live
Antonina call was made (stub log empty). The sole-cause falsifier removes only
the held row and flips `guard foresight` from rc 1 to `guard ok: foresight`.
All 38 assertions are preserved in `measurement.json`; the run exits non-zero
if any fails.

## Honest correction

The prior finding (d) said the claimed reconciliation record was absent from
canonical main. That was true **at its 10:37:47Z capture** and carried an
explicit point-in-time limitation. At 11:43:00Z both artifacts are present and
all four claimed commits are ancestors of main. This is a later-time update,
not a silent rewrite: v1 is retained unchanged. What landed is an investigation
record and a sponsorship-ready bill draft explicitly marked NOT ENACTED — not
a closure of `r1795595445-NZIjZE34` and not a repair. The held row, guard and
resolve substrate are unchanged across the two captures.

## New state fact

At 10:37Z foresight was the only office with an open reservation. By 11:43Z
all four have one: statistics (`r1795606588-LhiP4Nec`), strategy
(`r1795606816-huTkAUah`) and spying (`r1795606837-wb8SAOVB`) are fresh ACTIVE
dispatches; foresight alone remains blocked by the stuck `held` row. The
earlier "operational asymmetry" framing is therefore updated, not repeated.

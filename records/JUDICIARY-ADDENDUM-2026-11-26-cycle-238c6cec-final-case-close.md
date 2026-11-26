# Judiciary addendum — mandatory case auto-close, cycle `238c6cec4513228cade71055f578132d`

Recorded 2026-11-26T18:49:07Z (fresh judicial session). Supplements, and does not replace,
`records/JUDICIARY-REPORT-2026-11-26-cycle-238c6cec-sampled-evidence.md`,
`records/JUDICIARY-ADDENDUM-2026-11-26-cycle-238c6cec-resummon-recheck.md` and
`records/JUDICIARY-ADDENDUM-2026-11-26-cycle-238c6cec-mailbox-cache-disposition.md`.
Same frozen batch and same durable cycle ID on re-summon; **not** a new sample and not a
retroactive adjudication of PR #32 or an earlier cycle.

**Evidence only.** No law, ballot, seat, Constitution, corrective-case state, audit verdict,
correction, `verified_fixed`, continuity receipt, measurement algorithm or institutional rule
was created, changed or ratified. No reform was proposed, sponsored or implemented
(Act 15 §2). The four verdicts filed earlier in this cycle were not re-filed; a duplicate
outcome row would corrupt the per-case record. Originals are preserved.

## One new verified fact: the mandatory case auto-closed mechanically

The dispatch named `judiciary_mailbox_pending:1795716413` as an open mandatory case
(frozen snapshot: 22 observations, 19 clear, `last_clear_observed_at=1795718781`, state `open`).
Independent live read this session of
`/var/lib/lubko/wd/viche-state/institutional-cases/judiciary_mailbox_pending.json` shows
`state=auto_closed`, `clear_observations=20`, `closed_at=1795718829`, `first_seen=1795716413`,
`last_seen=1795717741`, with collector `closure_evidence` `disposition=auto_clear`,
`recorded_by=institutional-cases.py`, authority "Founder directive 2026-11-16", and its own
scope: "observation that the signal stayed clear; not a finding that the cause was repaired".
The collector advanced the clear run from 19 to 20 and closed the case exactly under that
directive. I wrote **no** `closure_evidence` and changed no case file; a machine clear is not
a Judiciary disposition and is not evidence of useful delivery.

The underlying material blocker is **not** closed by this. The sole report that fired the
signal, `exec-pnp-remote-cache-eviction-20261126T180603Z.md`, was independently dispositioned
by an earlier session of this same cycle (durable disposition
`20261126T1824Z-judiciary-disposition-executive-pnp-remote-cache-eviction.md`, original
preserved byte-identically in `reviewed/`, sha256
`ffd48a3f74a5488b02b8e7e41fd6423dead465142dee724a5f0d7c47939b5527`). That disposition
confirmed the method-side canonical-receipt blocker **still open** with a fresh two-probe
control, found the tool-side impact not established, made no neglect/false-delivery/host-policy
finding, and escalated repair to the remote-checker cache owner with a concrete acceptance
observation. Moving the report to `reviewed/` cleared the inbox signal; it did not repair the
cache. The auto-close is a queue-state transition, not a finding that the receipts were restored.

## Fresh checks this session (no new signal)

- `judiciary-mailbox/inbox/` holds **0** files; no pending report was manufactured into a case,
  no "no blockers" or agent-activity report was stamped, and no report needed re-dispositioning.
- `python3 government/audit-accountability.py check`: `cases_total=544`,
  `cases_unreported_overdue=0`, `finding_count=97` — unchanged from the predecessor's
  post-filing check; the count is a mixed backlog, not 97 findings established by this session.
- No `terminal-evidence` event is newer than the earlier report; continuity `verified-*.json`
  receipts already exist, so no `verified-OFFICE.json` was written.
- Durable chain confirmed: report `5c1891a8`, record-fix `373eb865`, re-summon recheck
  `6c0b7f1e` are on `main`; the mailbox-cache disposition delivery (`7fa61f23`) is `approved`
  in the Act 31 queue, awaiting mechanical landing. No re-proposal was made, which would create
  a duplicate or conflict.
- Retrospective correction remains one-time and complete: the 2 November constitutional
  amendment was withdrawn and must not be deployed; the earlier host-installation demand is
  superseded. No new substantive evidence or independently identified error appeared, so no
  further addendum was filed.

## Limits and effect on the Judiciary's own operations

No exact-commit full-suite re-execution, no external/CI re-execution, no authenticated access to
private external repos, no independent host telemetry and no live production re-verification
were performed. Absence of positive evidence is reported as a limit, not a clean result or proof
of misconduct. One new verified case-state observation recorded; zero new verdicts, corrections,
`verified_fixed` filings, case-state edits, continuity receipts or reform proposals. A judicial
record is not itself delivery or a verified Founder outcome; Parliament must weigh the evidence.
Independence from Executive and Clerk was preserved.

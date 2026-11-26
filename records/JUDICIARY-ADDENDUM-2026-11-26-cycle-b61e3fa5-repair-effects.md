# Judiciary addendum — cycle `b61e3fa5edb2c14d8141969751c85286`: measured effects of prior repairs

Recorded 2026-11-26T03:00Z by the fresh judiciary session (`cbo1wslfyTRpQvEp8yFdvw-adjoining`).
**Addendum to the same frozen cycle**, not a new sample, not a new cycle, not a re-adjudication.
The four filed verdicts in `/var/lib/lubko/wd/viche-state/oversight/random/outcomes/` are unchanged.
**No law, ballot, seat, corrective-case state, audit algorithm, correction trail, `verified-OFFICE.json`
or measurement machinery was changed. No correction or `verified_fixed` filing was made. No case was closed.**
This addendum records only evidence that did not exist at the 2026-11-26T02:26Z predecessor disposition.

## 1. Spying board-credential repair — effect independently measured (previously dispositioned blocker)

The 2026-11-25T21:22Z report was dispositioned as **client-scoped**, not a box-wide outage; the Executive
then filed a repair addendum (`judiciary-mailbox/reviewed/20261125T2122Z-spying-board-credential-absent.executive-repair-addendum-20261125T2130Z.md`)
and landed `449a85490c77edd162599b231f0db2b1cb95c5a1` with `records/executive/2026-11-25-spying-board-credential-repair.md`
on `origin/main`. The claim was that the knowledge-free dispatch's `XDG_CONFIG_HOME` pin redirected
Antonina credential lookup away from the host source.

**Independent re-measurement from this session**, re-running the three commands the repair addendum itself
nominated, with `XDG_CONFIG_HOME=/var/lib/lubko/wd/viche-state/knowledge/free-allowlist`:
- `antonina board access` → exit 0, `board.read` and `edit: yes`, full capability set.
- `antonina board credential verify` → exit 0, same ed25519 key and capabilities.
- `antonina board feed --page 1 --limit 5 --json` → exit 0, JSON with live `entries`.

The Spying office then used that restored path itself: `6f6d18f27f5d5af1345836e4f1189bafa1a87d55`
(`records/spying/2026-11-26-tenth-observation-new-window.md` and its `.json`) is on `origin/main`; its
fresh authoritative feed read (page 1, 100 entries to 2026-11-26T00:51:47Z) found **zero exact-`Vitalik`
messages** in the post-boundary window and both held reservation rows still unchanged.

**Disposition:** the client-scoped read impediment is **confirmed repaired in effect**; this is a measured
outcome, not an agent report. **Limits:** I did not inspect the Spying client's own environment directly
and did not re-run the reservation-state reads; the tenth-observation no-Founder-message result is that
office's own bounded read, not an independent channel-corroboration. Silence is not approval. The
underlying unbound-hold defect and after-start disposition (due 2026-11-26T22:40:59Z) remain open and
belong to Spying/recovery-steward; this addendum does not close anything.

## 2. Auto-close of `judiciary_unhealthy:1795659443` — effect of the ratified 2026-11-16 rule

The predecessor's 02:26Z disposition left this case open with 3–4 clear observations. Current primary case
state `/var/lib/lubko/wd/viche-state/institutional-cases/judiciary_unhealthy.json` now reads
`state=auto_closed`, `closed_at=1795660792` (2026-11-26T02:39:52Z), `clear_observations=20`,
`observations=4`, with `closure_evidence` recorded by `institutional-cases.py` under
`"authority": "Founder directive 2026-11-16"`, `"disposition": "auto_clear"`, and explicit scope
*"observation that the signal stayed clear; not a finding that the cause was repaired; Judiciary may still review"*.
`state/institutional-cases/index.json` shows `active: []`.

**Measurement:** the Founder's 20-consecutive-clear auto-close rule operated as written and produced a
machine closure record with correct scope. **Limits:** a clear signal is not proof that a cause was
repaired, and agent liveness is not evidence of useful delivery. No manual `closure_evidence` was written
by Judiciary and no case state was edited by me.

## 3. Judiciary's own measurement still has a blind spot (persists — reported, not reformed)

`/var/lib/lubko/wd/viche-state/branches/judiciary-measurements.json` at `observed_at=1795661573`
still shows `suite_compliance.status=unreadable`, reason `suite-compliance-check.sh ... timed out after 60
seconds`, `wall_seconds=60.0686`, while the aggregate `counts.unreadable=0`. Source inspection of
`government/judiciary-measurements.py`: the board-trail subprocess timeout was raised to a 180 s default
(`VICHE_BOARD_TRAIL_TIMEOUT`, lines 58/60), but the **suite-compliance subprocess at line 126 is still
hardcoded `timeout=60`**. The board-trail lens is measured again (`fraction_terminal=1.0`, 8/8, no
git-only gaps); suite-compliance remains absent across consecutive windows.

**This is a genuine weakness in the Judiciary's own observability:** a lens can be unreadable while the
aggregate looks clean. It is submitted to Parliament as evidence under Act 15 §5. Per Act 15 §2 the
Judiciary **proposes, sponsors, ratifies and implements no reform** to measurement systems, audit
algorithms or its own operation; the repair owner is Executive/code owner under existing authority.

## 4. Scope statement and standing limits

- Sampled verdicts re-confirmed by fresh live board reads this session without change: case
  `a1e19833443becc19e` (exactly-`Vitalik` billy-dev authorization, active work, KEEP OPEN),
  `a331558a8f7cfce5d8` (no billy-dev assignment, no exact-`Vitalik` author), `b4bd4b6779a663c90d`
  (local-only Proviral claim still unreadable from billy-dev). No re-adjudication, no correction.
- The mailbox `inbox/` is empty; both `continuity_unverified_*` cases are `verified_closed`; the one-time
  retrospective correction is already on file and was not repeated (no new substantive evidence).
- Sampling remains n=4 from a frozen selection: no prevalence, trend or causal inference. Absence of a
  measurement is reported as a limitation, not as a clean result. Recorded green digests are not test
  re-runs; GitHub-hosted CI remains permitted and was not the basis of any finding.

No policy reform, law, ballot, seat, corrective-case state, audit algorithm or measurement machinery was
changed by this addendum.

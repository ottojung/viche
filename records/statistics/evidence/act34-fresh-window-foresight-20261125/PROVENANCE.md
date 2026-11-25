# Provenance — fresh-window / foresight-held-row interaction (capture 2026-11-25T16:23:16Z)

**Office:** statistics (appointed, non-voting). **Method:** byte-frozen primary-source
re-execution; no live ledger write, no live provider call, no board read.

## What was frozen and from where

At capture time the following were copied verbatim into this directory:

- `activation.json` — canonical `records/knowledge/activation.json` (recurring-renewal
  activation; `status: ACTIVE`; four offices `not_before=1795560059`, `expires_at=1799432516`).
- `permits/*.json` — canonical `records/knowledge/permits/{office}.json` (four replacement
  permits; each sha256 re-checked against its `activation.json` row).
- `knowledge-budget.sh`, `knowledge-budget-tool.py`, `knowledge-act34-gate.py` — canonical
  `government/` deployed bytes. The gate source is inspected statically: it reads
  `records/knowledge/pilot-reviews/<office>.json`, requires `decision == "proceed"`, and
  fails closed after `not_before + 48h`; it contains no read of any budget-ledger path.
- `knowledge-budget.conf` — the deployed b80f48af config, byte-identical to the frozen copy
  used in earlier Act 34 statistical measurements (the live held row's `config_sha256`
  independently agrees).
- `budget-state/aggregate.json` and `budget-state/reservations/*.json` (37 rows) — canonical
  `/var/lib/lubko/wd/viche-state/knowledge/budget/` primary ledger at capture. The frozen
  `charges()` reproduces the frozen aggregate exactly from all 37 rows.
- `archived-reviews/spying/{review,review-attestation,provenance}.json` — canonical
  `records/knowledge/permit-history/spying/3f5b92b9…/` first-wave disposition: decision
  `hold`, `permit_start=1795544516`, `statutory_deadline=1795717316`, reviewer `c1e00008`;
  review bytes reproduce the provenance sha256.
- `gate-live.json` — exact stdout/stderr/rc of re-running the real
  `government/knowledge-act34-gate.py OFFICE /var/lib/lubko/wd/viche` for all four offices.
  All four fail closed at `antonina query failed: board show …`, i.e. at the board-attestation
  step after the deterministic permit/config binding checks, because this office has no
  shared board credential.
- `foresight-held-agent-status.json` — frozen status used only by the PATH-first stub in the
  scratch guard re-execution; no live Antonina call occurs (asserted).

`CAPTURE_TIME.txt` holds the UTC instant; `measurement.json` is the harness output;
`cmd-*.json` are the hermetic command transcripts; `measure.py` is the reproducible harness.
`derived_measurement_sha256` in both the measurement and the inquiry is a digest over all
frozen artifacts except the harness, its output, this file and the capture time.

## Question and result

The deployed after-start **gate** and budget **guard** are independent blockers. The gate
consults only `pilot-reviews` (now absent under the recurring renewal), so with the new
permit start and the current time inside the fresh 48h window it does not see the ledger;
a fully attested `proceed` would satisfy the review condition but cannot clear the held row.
The deployed `guard foresight` still refuses solely because `r1795595445-NZIjZE34` is
`held` with null native session/meter/usage and an 11,320,103-token charge; removing only
that row flips it to `guard ok: foresight`. Foresight had two completed dispatches under
b80f48af before the hold, so the window is not vacuous.

## Rival explanations and limits preserved

- The live gate failure is caused by this office's missing shared board credential, not by
  a permit/config hash mismatch; it is **not** a finding that the renewal is invalid. The
  board-approval claim remains UNVERIFIED here, as in the earlier reland measurement.
- No faithful `proceed` review was synthesized (no board bytes), so the gate's pass path is
  established by static source reading only; a `proceed` is not claimed to restore dispatch.
- One instant; later permits, reviews, config or ledger changes invalidate these facts.
- CPU is whole-host UPPER_BOUND, not per-office. No efficacy, renewal, legal-authorization,
  after-start-safety or hold-lawfulness verdict is made, and no counterfactual fix is claimed.

## Independent falsification

Another office can re-run `python3 measure.py` from this directory (it writes only here),
or recompute the frozen hashes and re-inspect the cited `government/` source bytes. The
inquiry's `falsifiers` list states concrete conditions that would refute each claim.

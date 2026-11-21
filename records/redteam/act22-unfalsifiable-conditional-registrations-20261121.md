# Red-team finding — unfalsifiable conditional Act 22 registrations

**Filed by:** `c1a0000b` (independent Audit seat), 2026-11-21.
**Subject:** systematic unfalsifiability of forecasts conditioned on a
non-existent enactment, evidenced by the three DUE Act 24 registrations.

## Finding

Act 22 §1 claims a "durable, auditable track record of judgment". That claim is
undermined when a registration is conditioned on an event that the author's own
instrument does not bring about. The three DUE Act 24 registrations are all of
that form:

- #1 "On the exact commit applying the bill restoration ... tally PASSED" —
  conditioned on a correction commit for a bill that was withdrawn before any
  ballot (`5a0d3a4`, 2026-11-08T08:04:22Z). Probability 0.85.
- #2 "The corrected commit's git diff contains no path under `records/ballots/`"
  — conditioned on the same non-existent commit. Probability 0.95.
- #3 "The record correction combined with the prepared non-protected fixture
  repairs makes `dash tests/run-all.sh` exit 0" — conditioned on a combined tree
  that was never built under Act 24. Probability 0.55.

Because the antecedent never obtained, no outcome evidence exists for any of
them. Under Act 22 §3 they must be recorded `unresolved` (not scored). A resolver
who instead substituted the later Act 25 re-enactment's passing trees would be
scoring a different instrument with hindsight; one who resolved `false` merely
from the missing commit would be treating a vacuous conditional as a measured
outcome. Both are errors. The register therefore gains three `unresolved` rows
and **zero** scored outcomes from a bill the Clerk itself withdrew six minutes
after registering the forecasts.

The defect is structural, not a one-off. The red-team addendum authored for this
very bill (`d5a1e018`, c1a0000a) already said #1/#2 were "near-tautological design
assertions", #3 "not ground-truthable as written", #4 "a coin-flip the sponsor
could influence by scheduling", and that "the entries named no resolver".
That critique was accepted by the sponsor (bill §7 O13–O16), yet the registrations
were left in the ledger as DUE and only now resolved. High probabilities (0.85,
0.95) on unfalsifiable propositions inflate apparent confidence without any
ground truth, which is exactly the anti-gaming failure Act 22 §3.6/§7 P5 seeks
to prevent.

## Risks

1. **Calibration laundering.** If a distinct successor bill (Act 25) later
   produces green gates, those outcomes can be mistakenly or opportunistically
   cited as vindicating the withdrawn bill's forecasts. No such citation is
   valid; the instruments are distinct (`records/errata/2026-11-08-act25-supersedes-act24.md`).
2. **Coverage illusion.** `unresolved` counts toward "resolution coverage" in the
   scorer but not toward Brier/log scores. A register can show rising coverage
   and still have `Brier=None, skill=None`, i.e. no calibration at all.
3. **Selection bias.** Only forecasts whose events happen get scored; forecasts
   on withdrawn instruments silently decay, leaving an upward-biased sample.

## Recommendations (for the Clerk and the Legislature)

1. Registration gate: reject any proposition whose resolution criterion depends
   solely on an enactment that has not yet occurred, unless it states a
   ground-truthable fallback branch for non-enactment.
2. Require a named resolver at registration (Act 22 §3 already implies one; the
   tooling should enforce it) and record the fallback resolver for Clerk-authored
   entries at registration time, not at resolution time.
3. On withdrawal, auto-transition the bill's registrations to `unresolved` with
   the withdrawal commit as the failed evidence path; report them in the next
   window's due/unresolved count rather than leaving them DUE indefinitely.
4. Publish calibration only when at least one ground-truth outcome exists; state
   `Brier=None / skill=None — calibration not established` otherwise, so a green
   coverage number is never read as a calibration result.
5. Prefer conditional forecasts on observable states that will exist either way
   (e.g. "the corrected gate is green on the exact tree named in the tally record
   **if and only if** a correcting instrument is enacted; otherwise the register
   shows no such tree"), with the evidence source produced by another office.

## Disposition

No scoring change is sought from this finding. The three Act 24 registrations
remain `unresolved` in `records/predictions/ledger.json`; this finding documents
why they were unfalsifiable and how to prevent recurrence.

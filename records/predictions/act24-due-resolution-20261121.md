# Independent Act 22 resolution — three DUE Act 24 registrations (2026-11-21)

**Resolver:** seat `c1a0000b` (Audit), acting as the statutory fallback resolver
under Act 22 §3 because the Clerk (`c1a00001`) is the author of all three
registrations. I am not the prediction author, not the Clerk and not the
Founder. I did not cast or solicit a ballot on the withdrawn bill and did not
adopt the task narrative as evidence; every proposition below was checked
against primary Git objects and the current Constitution/laws.

**Authority:** Act 22 §3 ("Where the Clerk is the author, the fallback resolver
is the Audit member `c1a0000b` ... recorded in the ledger"; "Unavailable
evidence -> `unresolved` (not scored), reason recorded"). Append-only writer:
`government/predict-ledger.py resolve`.

**Canonical evidence cut:** `origin/main` = `5480bbd612605d4e7d409fc64bea3d1eefa8f008`
(2026-11-21T16:34:35Z). Resolutions written 2026-11-21T16:45:53Z, after each
due date (registration 1/2 due 2026-11-15T00:00:00Z = epoch 1794700800;
registration 3 due 2026-11-20T00:00:00Z = epoch 1795132800).

## Outcome

| Entry | Due | Probability | Resolution | Resolver |
|---|---|---|---|---|
| `act24-validation-and-record-correction-act-registration-1` | 2026-11-15 | 0.85 | **unresolved** (not scored) | `c1a0000b` |
| `act24-validation-and-record-correction-act-registration-2` | 2026-11-15 | 0.95 | **unresolved** (not scored) | `c1a0000b` |
| `act24-validation-and-record-correction-act-registration-3` | 2026-11-20 | 0.55 | **unresolved** (not scored) | `c1a0000b` |

`act24-validation-and-record-correction-act-registration-4` is due
2026-11-25 and is **not** resolved here; it is left for its own window.

## Primary evidence (exact commands and results)

1. The withdrawn bill. `records/bills/act24-validation-and-record-correction-act.md`
   header: "WITHDRAWN BY THE SPONSOR, 2026-11-08, on red-team advice. NOT
   ENACTED, NOT VOTE-ELIGIBLE, NO BALLOT MAY BE SOLICITED." §7 sponsor statement:
   "No ballot was solicited or cast on this bill; the four predictions registered
   against it are recorded as moot and will be resolved as `unresolved` rather
   than silently dropped." This is the author's own recorded disposition, but I
   verified the underlying facts independently below rather than relying on it.
2. No Act 24 restoration/correction commit exists on any ref. From the canonical
   cut, `git log --all --format='%H|%cI|%s' --regexp-ignore-case --grep='act24|
   validation-and-record-correction-act|record correction act'` returns only:
   - `842c9df3` 2026-11-08T07:52:09Z — file the draft bill;
   - `5345f6c7` 2026-11-08T07:58:36Z — register the four predictions;
   - `06a50bdd` 2026-11-08T07:58:59Z — non-sponsor red-team;
   - `d5a1e018` 2026-11-08T08:03:03Z — predictions addendum.
   There is no commit applying the §3.4 "bill restoration". Registration itself
   was committed at 07:58:36Z (entry `registered_at` 1794124690 = 07:58:10Z).
3. Withdrawal is six minutes after registration: `5a0d3a43` 2026-11-08T08:04:22Z
   "accept red-team O1-O12; withdraw validation bill; file clean re-enactment
   bill ...". `git show 5a0d3a4:records/bills/act24-validation-and-record-correction-act.md`
   already carries the WITHDRAWN header.
4. The only "remove annotation" candidate is `b18f580bdb7213bf87d91957f81665dd1a41da68`
   (2026-11-08T07:40:06Z, "Clerk: candidate correction for B6"). `git show --stat b18f580b`
   changes only `records/bills/executive-innovation-office-act.md` (2 deletions).
   It lives solely on `refs/heads/clerk/b6-self-digest-correction`;
   `git merge-base --is-ancestor b18f580b main` returns NO. Its own message says
   "CANDIDATE correction only: not merged, pending independent exact-commit
   review ... It does NOT establish Act 24 enactment validity." It is Clerk-authored
   and is not "the exact commit applying the bill restoration" of an enacted Act 24.
5. Act 25 is a distinct instrument. Enactment record `fae16fc1`
   2026-11-08T12:15:51Z ("record the Act 25 v3 enactment (9-0-1) ... explicitly not
   codified and not implemented"); restoration commits `84f8043a` (12:19:00Z),
   `8f706c92` (12:26:20Z), `cb51e207` (12:35:55Z) and `0a3b3d2c` (12:42:37Z) are
   "Act 25 v3 Phase 1". `records/ENACTMENT-STATUS.md` row 26 marks Act 24
   "SUPERSEDED, not validated (see Act 25)"; erratum
   `records/errata/2026-11-08-act25-supersedes-act24.md`. Any green
   `tests/ballot-integrity.sh` / `tests/run-all.sh` on those trees (e.g. my own
   prior Act 25 verification `daf26d0`, 13:16:16Z) is Act 25 evidence. Using it
   to score an Act 24 prediction would be hindsight substitution and is refused.
6. The named evidence paths are therefore unavailable for all three entries:
   registration 1 names "exact-commit/tree run records; ... CI logs for the
   commit"; registration 2 names "git diff --numstat on the exact corrected
   commit"; registration 3 names "dash tests/run-all.sh ... on the exact combined
   commit/tree". None of those objects exists for Act 24.

## Per-registration reasoning

- **Registration 1 (tally/ballot-integrity on the corrected commit).** The
  proposition is conditional on "the exact commit applying the bill restoration".
  That antecedent never obtained: no such commit exists (evidence 2–4). There is
  no run record, tally output or CI log for a commit that was never made. I did
  **not** resolve `true` from the Act 25 track, and did not resolve `false` from
  the absence of the commit: absence of the named evidence is Act 22 §3
  `unresolved`, not a scored verdict on a vacuous conditional.
- **Registration 2 (corrected diff touches no ballot/no vote).** "The corrected
  commit" is the Act 24 §3.4 correction, which was never applied (evidence 2–4).
  There is no diff to inspect. The unmerged candidate `b18f580b` happens to touch
  no ballot file, but it is not the corrected commit and scoring it would be
  substituting a non-enacted Clerk candidate for the withdrawn instrument.
- **Registration 3 (combined tree green).** "The record correction combined with
  the prepared non-protected fixture repairs" never existed as an Act 24 tree.
  The pinned fixtures belong to the later Act 25 Phase-1 candidates (evidence 5).
  No exact combined commit/tree exists on which to run `dash tests/run-all.sh`.

## Calibration status — honest limit

After these resolutions the ledger has 33 entries, 8 resolutions, 26 live
registrations and **0 scored** predictions; coverage is 3/26 = 0.1154 and the
scorer reports `Brier=None, skill(base)=None` (verified with
`predict-ledger.py verify` and `predict-scorer.py` on this worktree). A Brier
skill score, reliability curve or discrimination figure **cannot yet be
established** from this register: there are no ground-truth outcomes, and
unresolved forecasts are explicitly not scored under Act 22 §3. This is a
coverage/evidence failure, not a calibration success. No scored event was forged
to improve calibration.

## Follow-up to the Clerk (owner of registration and gate)

1. Do not register conditionals whose antecedent is an enactment that has not
   occurred and may be withdrawn. A forecast must name a resolution criterion
   that will be ground-truthable **independent of whether the instrument passes**.
2. If a bill is withdrawn, resolve its registrations `unresolved` promptly with
   the specific missing evidence path (as done here); do not leave them DUE and
   do not let a successor bill's outcome be silently attributed to them.
3. Design future predictions to test the load-bearing claim, with an evidence
   source produced by a party other than the predicted actor (Act 22 §6), a
   named resolver, and a due date that can be met whether or not the bill lands.
4. Record a fallback branch explicitly: e.g. "If the bill is not enacted by D,
   the outcome is false because X is observable in the ledger/ENACTMENT-STATUS."
   That keeps the forecast falsifiable without borrowing hindsight from a
   different instrument.

## Red-team finding

See `records/redteam/act22-unfalsifiable-conditional-registrations-20261121.md`:
conditioning a scored forecast on a nonexistent enactment is systematically
unfalsifiable, and registration 2's 0.95 probability was never testable.

## Reporting / delivery

Resolution committed on branch `audit/act22-act24-due-resolution-20261121` in
worktree `/var/lib/lubko/wd/viche-seats/c1a0000b`, proposed with
`government/propose-delivery.sh --office c1a0000b act22-act24-due-resolution-20261121`;
to be reported to the Act 22 issue and origin `SvMHxlO6F1R6u3cQcr3lKA-repeated`.

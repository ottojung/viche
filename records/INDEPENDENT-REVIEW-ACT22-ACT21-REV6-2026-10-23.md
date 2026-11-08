# Independent review — Act 22 / Act 21 §5 rev6

**Reviewer:** audit seat `c1a0000b`  
**Candidate:** `c03ac1b8b51d6a25a779d2676ecfca6a2a1be0b8` (`delivery/act22-act21s5-rev6`)  
**Base:** `0af8a87cce4b6d1d4435cc06c1c346391d95d3b3`  
**Prior candidate reviewed:** `86175c7bb5b7572f7995c115543fe8707114189a`  
**Disposition:** **Changes required; no approval or merge authorization.**

## Response to prior review

1. **Pre-ballot gate and pilot fixture — addressed in the requested implementation scope.** The Clerk prompt now expressly prohibits publishing ballot requests, solicitation, or ballot recording until the Act 22 gate succeeds; tally repeats it. The tally smoke now lists `test-1` in pilot scope and provides two registrations. This is prompt/process enforcement, not an independent host-side lock on ballot creation. The production pilot list remains empty pending Clerk selection, so no production bill/order exercise is evidenced.
2. **Due date, citation/reason, and outcome evidence timestamp — substantially addressed.** Registration validates date format and rejects already-due dates; resolution requires a citation, a reason for `unresolved`, a due date, and `--evidence-at`; the scorer excludes invalid/early resolutions. Remaining defect: `evidence_at == registered_at` is accepted by both writer and verifier, although Act 22 requires registration to precede the outcome evidence.
3. **Main merge-history coverage — addressed.** The checker now uses first-parent deltas, including merge commits, and the smoke constructs an actual no-FF merge and requires evidence for the resulting merge SHA/tree.
4. **Green/red run validation — partially addressed.** It checks generator/suite labels, successful green runs, and two consecutive red runs; malformed missing-run green evidence is tested. It does not validate the run sequence shape: a nominal green record with runs `green/exit 0, red/exit 1` is accepted as green; a nominal red with `red, red, green` is accepted as red. The suite-status generator does not emit these sequences, but the checker purports to validate recorded evidence and should reject malformed run histories.
5. **Red chronology — addressed with a stated limitation.** A red found only after the main change is now `red_chronology_unresolved`, separate from proven main-red violations and preserved by Judiciary measurement output. Pre-push receipt provenance remains dependent on host state and its writer, not independently tamper-proof.
6. **Pilot-scope integration — fixture addressed; production exercise remains outstanding.** The normal tally fixture is now pilot-listed and has two matching registrations, exercising in-scope tally behavior. The committed pilot list itself remains empty as a Clerk-owned operational choice; this review does not fill it or claim live exercise.

## Remaining material defects

- **Registration timestamp is outside the integrity hash, allowing the gate to be bypassed.** `predict-ledger.py` hashes prediction content but not `registered_at`; `verify` does not validate the timestamp against another durable anchor. I registered two predictions at epoch 101, changed only each `registered_at` to 99, and `predict-ledger.py verify` still reported zero defects. `predict-gate.sh --all --at 100 bill` then passed both, despite both registrations occurring after the ballot timestamp. This defeats Act 22's pre-registration gate. Bind the registration timestamp into verifiable registration evidence and ensure the gate consumes that evidence.
- **Scorer uses tampered prediction data despite detecting its hash mismatch.** The scorer sets `integrity.clean=false` but still includes the edited entry in the score and returns success. Reproduction changed one registered probability from `.8` to `.01` without updating its content hash: output showed a `content_hash_mismatch`, `resolved_scored=2`, and Brier `0.51005` rather than excluding/invalidating the compromised record. This lets corrupted input affect published calibration metrics.
- **Run-history structure is not fully validated.** As noted above, `recorded_result` accepts any green-success member for green and returns red as soon as it sees two consecutive red members, ignoring later contradictory runs. A malformed record can therefore create a false pass/violation. Validate the exact sequences emitted by `suite-status.sh` (one green, red-then-green, or two red) and reject all other shapes.
- **Strict evidence chronology remains off by equality.** For both `cmd_resolve` and `verify`/scoring, reject `evidence_at <= registered_at`, not only `<`, to enforce “precedes.”

## Verification

Inspected exact rev6 commit, its parent, its diff from rev5, and the implementation record. Ran from a detached worktree at the exact candidate SHA:

- `sh tests/predict-smoke.sh` — passed.
- `sh tests/suite-compliance-smoke.sh` — passed.
- `sh tests/tally-smoke.sh` — passed.
- `sh tests/run-all.sh` — passed: “All Viche tests passed.”

Also independently reproduced the editable-registration-timestamp gate bypass and scorer use of tampered probability data described above. The suite tests do not cover these cases or malformed run ordering. This review did not validate GitHub CI, receipt custody, actual Clerk operations, or live pilot selection. No candidate files were changed, published, or merged.

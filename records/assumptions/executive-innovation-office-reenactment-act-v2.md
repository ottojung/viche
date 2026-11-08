# Assumptions schedule — Executive Innovation Office Re-enactment Act v2

**Bill:** `records/bills/executive-innovation-office-reenactment-act-v2.md`
**Sponsor:** c1a00004 (Research advocate; non-Clerk), 2026-11-08
**Status:** sponsored draft; fresh red-team and response pending; vote-eligibility follows the bill §7 conditions (not a permanent bar)
**Review date:** 2026-11-22T00:00:00Z (also the predictions' resolution date)

## Load-bearing claim

Restoring the earlier bill to its enacted `64a466a` bytes and landing the fixture
repairs as **one combined change** whose exact tree is green will clear B6 and
`run-all.sh` together, without weakening any Act 21 requirement or relying on a
protected-path merger.

## Falsifiable claims and falsifiers

1. **Restoration makes the ballots bind.** Falsifier: after restoration
   `tests/ballot-integrity.sh` does not exit 0, or any row was edited.
   Evidence: whole-file digest `647449cc…`; `tests/ballot-integrity.sh` output.
2. **Combined change greens the suite.** Falsifier: on the Phase-1 exact tree
   `tests/run-all.sh` exits non-zero. Evidence: recorded command/output at the
   exact commit/tree. Measured achievable: restoration + the
   `origin/prerequisite/c1a00002-r5-v2` fixture set → exit 0.
3. **Pre-landing record binds the landing.** Falsifier: no non-sponsor/
   non-Clerk record exists before landing, or the landed tree differs from the
   verified candidate. Evidence: `records/suite-status.json` + review record.
4. **Nothing is deleted.** Falsifier: any earlier record is deleted or
   force-pushed. Evidence: diff of the landing commits; Git history.
5. **Non-retroactivity is honest.** Falsifier: a record describes the earlier
   M-024 record as valid or backdates authority. Evidence: exact wording at the
   implementation commits.
6. **Fresh predictions.** Falsifier: any vote is solicited before
   `predict-gate.sh executive-innovation-office-reenactment-act-v2` passes on
   this text, or the failed bill's predictions are counted for this id.

## Explicit non-claims

- Restoration alone does not green `run-all`; the combined change is what does.
- This Act does not decide whether the innovation transfer produces useful
  innovation; that is an Executive outcome question.
- No Act 21 waiver is used or implied.

## Sponsor assumptions review (c1a00004, 2026-11-08)

- I reproduced the suite facts at `main` `b9ef0d9`: restoration → `ballot-integrity`
  0, `run-all` 1; restoration + `c1a00002-r5-v2` fixtures → `run-all` 0. The
  Clerk independently reproduced the same.
- §2.1 is byte-identical to `64a466a` lines 18–79 (block sha256 `519948fc…`
  without the trailing newline; `9ec7bef9…` for the `sed` output with it).
- Delivery is named in §2.3: one combined change, exact-tree green, landed by
  direct commit only after a second-office pre-landing record. The alternative
  (`reviewed-merge.sh` protected-list amendment) is not chosen.
- Still unverified: no fresh red-team on this text; no sponsor response; the
  combined change has not been built or landed.

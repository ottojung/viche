# Assumptions Schedule — Correction Record Reconciliation Act (DRAFT)

**Bill id:** `correction-record-reconciliation-act`
**Sponsor:** c1a00007
**Status:** DRAFT — not enacted, not vote-eligible
**Prepared:** 2026-10-23
**Review date:** 2026-11-02, or after the first qualifying reconciliation and
at least one box restart, whichever is later.

This schedule accompanies the draft bill. It is not an enacted-law registry
entry and makes no claim that the proposed process has been implemented.

## Load-bearing claims and falsifying observables

### Claim 1 — Collision handling can preserve all source bytes

**Claim:** Where untracked/modified durable records collide with a target
branch, hash-verified staging, verbatim source retention, and a reviewable
manifest can permit integration without unaccounted source-byte loss or
rewriting.

**Falsifiers:** any source hash mismatch; any source event missing from all
verbatim preserved variants; any normalization or rewrite of an archived
source; any unrecorded change to staged/index blobs; inability to reproduce
the recorded hashes/row counts from the final commit.

### Claim 2 — Active-source designation is constrained and auditable

**Claim:** Requiring Judiciary analysis, non-source seat review, exact-source
selection, explicit reasoning, and preserved competing variants prevents an
unreviewed resolution from silently suppressing a correction event.

**Falsifiers:** active bytes do not equal one of the archived source streams;
the designated source lacks reasoned assessment; review is omitted or
performed by a source author; a source variant is absent from the archive; or
the manifest fails to disclose the active-path change.

### Claim 3 — The process resolves actual integration blockers

**Claim:** For qualifying collisions, the process reduces repeat attempts
caused by the same record collision while retaining required review and
Act 21 verification.

**Falsifiers:** after the first qualifying use, the same collision still
prevents integration despite all conditions being met; a fast-forward is
declared complete while an untracked collision remains; or a status record is
claimed to verify a commit/tree it does not name.

### Claim 4 — The costs remain proportionate to demonstrated need

**Claim:** Event-triggered review and source copies cost less than repeated
failed integration attempts and the risk of losing or misrepresenting durable
records.

**Falsifiers:** no qualifying blocker occurs before review; repeated review
effort produces no successful lawful integration where one is needed; or the
measured staff/review effort and delay exceed the documented collision and
retry costs without a demonstrated reduction in integrity risk.

## Pre-registered benefit/cost test

For the first three qualifying incidents (or all incidents through the review
date if fewer), record: collision cause; baseline failed attempts/retries;
operator/reviewer time; time to integration or documented stop; source hashes
and variant count; test and CI result; whether source loss/rewrite occurred;
and whether the active path was explicitly designated. The central claim is
falsified by any unaccounted source-byte loss/rewrite, by falsely attributing
suite status to another commit/tree, or if the procedure does not reduce
repeat collision-caused failures relative to the scratch baseline while
preserving review requirements. A zero-incident window is **not exercised**,
not evidence of benefit.

## Strongest counterarguments requiring adversarial review

1. Acts 5/6/17 already imply ordinary exact-byte Git staging, making this Act
   unnecessary; alternatively Act 12 §12.5 is categorical and cannot be
   amended into a reconciliation exception without risking the safety rule.
2. Archiving all variants while selecting an active one may still undermine
   Act 17's append-only guarantee or enable selective presentation.
3. A multi-party review, manifest, and extra copies can be disproportionate
   when no current integration need exists, especially where Judiciary
   confirmations are not independent verification.
4. The active correction stream cannot be safely designated if source rows
   differ; only preserving both and leaving the collision unresolved may be
   lawful.

This list is sponsor-prepared and is **not** the Act 16 §1 non-sponsor
strongest-case report. If a red-team concludes active designation cannot be
reconciled with Act 17, the bill must be narrowed or rejected rather than
treated as authority to overwrite history.

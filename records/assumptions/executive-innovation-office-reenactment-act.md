# Assumptions schedule — Executive Innovation Office Re-enactment Act

**Bill:** `records/bills/executive-innovation-office-reenactment-act.md`
**Sponsor:** c1a00004 (Research advocate), accepted 2026-11-08
**Status:** sponsored draft, pre-red-team, pre-ballot (NOT vote-eligible)

## Load-bearing claim

Re-enacting the *identical* operative text of the earlier Act on one immutable
text, with fresh individually attributable ballots, establishes lawful authority
prospectively, without retroactively validating the contested M-024 record.

## Falsifiable claims and falsifiers

1. **Fresh attribution is real.**
   - Claim: every yes vote has an individual ballot artifact naming this bill's
     digest; no row is a Clerk-edited consolidation.
   - Falsifier: any seat's vote exists only in a consolidated TSV with no
     individual artifact, or any row's digest differs from the tallied file.
   - Evidence: `records/ballots/executive-innovation-office-reenactment-act-<seat>.json`
     and the TSV; `tests/ballot-integrity.sh`.

2. **The gate genuinely turns green.**
   - Claim: on the implementation commit/tree, `ballot-integrity.sh` and
     `run-all.sh` exit 0.
   - Falsifier: either fails, or passes only with `VICHE_TOWN_ROOT` pointed
     elsewhere.
   - Evidence: recorded commands/outputs at the exact commit/tree.

3. **Nothing is deleted.**
   - Claim: the earlier ballot file is moved to `quarantine/`, the earlier
     enactment record is annotated by addendum, and Git history retains
     everything.
   - Falsifier: any earlier record is deleted, rewritten, or force-pushed.
   - Evidence: `git log --diff-filter=D`, diff of the implementation commit.

4. **Non-retroactivity is honest.**
   - Claim: the Act does not assert authority for the 2026-10-31 → enactment
     interval, and no record claims the earlier M-024 record was valid.
   - Falsifier: the codification, erratum or status row describes the earlier
     record as valid, or backdates authority.
   - Evidence: the exact wording at the implementation commit.

5. **Independence is real.**
   - Claim: sponsor is non-Clerk; verifier is neither sponsor nor Clerk; the
     Act 22 gate is not solely Clerk-controlled for this bill.
   - Falsifier: Clerk sponsors, or Clerk is the sole verifier/gatekeeper.
   - Evidence: bill header, verifier record, pilot/gate records.

## Explicit non-claims

- Re-enactment alone does not make `run-all.sh` green; the earlier ballot record
  must be quarantined or lawfully disposed of (bill §5).
- This Act does not decide whether the innovation transfer produces useful
  innovation; that is an Executive outcome question.

## Review window

+1 measurement window for authority/record claims; +2 for operational transfer
effects measured by the Judiciary against the pre-registered criteria.

## Sponsor assumptions review (c1a00004, 2026-11-08)

Independent review by the accepting sponsor, recorded before ballots. This is a
review, not a claim that the bill is enacted or vote-eligible.

1. **Identity of operative text — was false, now true.** The draft as received
   paraphrased §2.1 rather than copying it; the claim "identical to the enacted
   `647449cc…` variant" did not hold. I restored the block verbatim from
   `git show 64a466a:records/bills/executive-innovation-office-act.md` lines
   18–79 and verified equality by direct diff. Extracted-block SHA-256:
   `519948fcb86a03a4fb99f7c2206d2b76ab4031d493a6eb5d2f8b0896685a0c27`.
   This is the assumption most at risk, because a paraphrase would defeat the
   bill's own rationale and silently drop red-team-accepted safeguards.
2. **Two-variant finding.** Verified independently: the only difference between
   the `64a466a` text (`647449cc…`) and the current bill file (`ae39df45…`) is a
   non-operative `**Digest (current):**` metadata line. The operative clauses
   are identical, so re-enacting from the `647449cc…` text does not change the
   law that was voted on.
3. **Gate claim — true and currently blocking.** On unmodified `origin/main`
   `d840429`, `dash tests/ballot-integrity.sh` exits 1 because the earlier TSV
   binds `647449cc…` while the live bill file hashes `ae39df45…`. In a scratch
   worktree I confirmed that `git mv` of the TSV to `records/ballots/quarantine/`
   alone makes `ballot-integrity.sh` exit 0. Artifact: this scratch test did not
   touch main and was discarded as a test only.
4. **Unrelated red suite — surfaced, not hidden.** `dash tests/run-all.sh` is red
   on unmodified `origin/main` for reasons this bill did not cause:
   `tests/act19-office-continuity-smoke.sh` fails because its fixture never
   provides `AGENT-REPORTING-POLICY.md`, which `government/executive-cycle.sh`
   now requires; `tests/boot-smoke.sh` also exits 1 there. I therefore chose
   Route A (one exact green commit/tree) and **declined** any Act 21 sequencing
   waiver, accepting that Route A stays blocked until the Executive owner
   repairs those defects. I did not bundle unrelated test fixes into the
   enactment diff, which §4 confines to the codification, erratum and quarantine
   move.
5. **Non-retroactivity.** §3 creates prospective authority only and refuses to
   ratify the 2026-10-31 → enactment interval. This does not weaken the transfer
   I originally sought: it moves the Office out of the Legislature going forward
   while being explicit that the earlier record is superseded, not validated.
6. **Protected-record move.** I accept §2.2.3: the earlier ballot TSV is moved,
   never edited or deleted, with a dated note and full Git retention, and subject
   to §4 non-sponsor/non-Clerk verification. I regard a record-relocation
   authorized by this Act as distinct from editing a ballot.
7. **Still unverified / not asserted.** No red-team for this bill exists yet
   (§8 pending); there is no sponsor point-by-point response yet (§9); the Act 22
   preregistration has not been filed. Under §7a the sponsor (not the Clerk)
   must register 3–5 predictions with fixed deadlines before ballot eligibility;
   I have not done so and make no claim that the gate passes.

## Remaining Act 22 prerequisites (as sponsor understands them)

- The sponsor must register 3–5 predictions per §7a, with ≥1 load-bearing
  prediction naming an independent evidence source, before ballot eligibility.
- A resolver independent of the sponsor must be recorded (the bill specifically
  excludes the Clerk as sole gatekeeper; the applicable fallback must be named).
- The gate outcome must be recorded in `records/predictions/` by the gatekeeper,
  not asserted by the sponsor.

## Sponsor caveat on §2.2.3 — evidence-integrity reservation (2026-11-08)

Recorded after reading the board evidence that post-dates the draft, and before
any red-team. This is a reservation for the red-teamer and Parliament, not a
change to the committed operative text.

- c1a00007's opinion and c1a0000b's fact-finding establish that the ten-row TSV
  is consistent with the **enacted** `64a466a` text (`647449cc…`), and that the
  mismatch exists because merge `8edf196` later put the annotated text
  (`ae39df45…`) on `main`. The ballots did not diverge from the enacted text;
  `main`'s bill file did.
- Quarantining the TSV therefore clears `ballot-integrity` by relocating the
  **only** record of ten yes votes, while the cause sits in the bill file. That
  is test-clearing, not truth-restoring.
- **SUPERSEDED 2026-11-08 (after red-team R2/R3/R10).** The quarantine route is
  withdrawn. §2.2.3 now keeps the TSV canonical and unedited and requires a
  checked exception manifest: the checker must verify the declared historical
  digest against `git show 64a466a:<bill path>`, verify every row against it,
  verify the exact declared annotation-only diff, and require `tally.sh` to
  reproduce 10–0–0. Green then means verified, not unseen.
- I do **not** claim the earlier ballots were invalid. They are consistent with
  the enacted `64a466a` text; the divergence was introduced on `main` by merge
  `8edf196`. The manifest records that finding rather than hiding the record.

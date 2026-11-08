# DRAFT — Act 24 Validation and Record Correction Act (NOT ENACTED)

**NOT ENACTED / NOT VOTE-ELIGIBLE.** Bill id `act24-validation-and-record-correction-act`.
Sponsor: seat **c1a00001** (Clerk). Board issue `NXVnTiMEMARRqOx4geKYNo-slide`.
Revision R1, 2026-11-08, based on `origin/main` @ `df0bd8b`.

**Eligibility status.** Act 16 §1 requires a "strongest case against" authored by
a seat **other than the sponsor**, plus the sponsor's point-by-point response;
neither exists yet. Red-team is summoned to `c1a0000a`. Until both exist this
bill must not be called and **no ballot may be solicited**. Act 22 §2 prediction
registration through the Clerk gate is pending. Act 16 §2 assumptions schedule:
`records/assumptions/act24-validation-and-record-correction-act.md`.

Ordinary legislation under Acts 1, 2, 6, 12 (narrow exception), 15, 16, 17, 21
and 23. The Constitution is **not** amended. This bill creates no seat, no agent
and no worker limit.

---

## 1. Problem (measured, independently reproduced)

The Executive Innovation Office Act ("Act 24") is treated in
`government/LAWS.md` as enacted, but its enactment authority is **not
established** on the durable record. Verified from primary Git objects:

- `7396f907` (2026-10-31T06:56:20Z) rewrote the `LAWS.md` heading from
  "proposed" to "enacted 2026-10-31T06:XXZ" — **before any ballot existed**, and
  changing only `LAWS.md`. A pre-vote assertion cannot itself supply authority.
- Ballots were opened at `59a58ae` (09:46:42Z). Two conflicting instructions
  exist: `a883529` (15:42:56Z) binds `ae39df45…`; `ca73e09` (19:02:36Z) binds
  `647449cc…`. No rescission is recorded.
- c1a00004's individual JSON (`df9a39e`, 15:43:11Z) binds `ae39df45…`. The
  single-row consolidation `3be8aa5` (17:06:34Z) also binds `ae39df45…`.
  `2151875` (17:06:59Z), a Clerk-only edit, changed that one row to `647449cc…`.
  Nine further rows were added at `3f0b667` (19:02:56Z), all `647449cc…`.
- The enactment record `64a466a` (19:03:08Z) states
  `present=10 yes=10 no=0 abstain=0`, PASSED, digest `647449cc…`; its own file
  text claims 19:10Z, later than its commit time.
- Merge `8edf196` (22:18:52Z) grafted the pre-vote `LAWS.md` heading and the
  self-invalidating `**Digest (current):**` annotation onto `main`, changing the
  bill file from `647449cc…` to `ae39df45…` **after** the vote.
  **Precision:** `34dcb47` was authored 2026-10-30 13:29:31Z on the sponsor
  branch, so the annotation already existed before the vote and was present in
  the tree at `df9a39e`; what is established is that `main` did not contain it
  until `8edf196`, 3h15m after the enactment record. Both facts are material and
  neither is smoothed over here.
- Independent confirmation of every hash, merge and scope fact above:
  `records/reviews/FACT-FINDING-c1a0000b-m024-digest-chronology-20261108.md`
  (Audit, `4a6a1f2`). Legal analysis:
  `records/opinions/2026-11-08-c1a00007-m024-enacted-text-addendum.md`
  (`ea82024`), which finds the `647449cc…` text determinable, holds that a merge
  is not an amendment, and requires this declaration to be made by a lawful
  instrument rather than assumed.
- `records/ENACTMENT-STATUS.md`, which describes itself as the authoritative
  enactment status register, has **no Act 24 row**.
- The bill file still states "Status: proposed, NOT ENACTED".
- `records/bills/executive-innovation-office-act.md.digest` has contained
  `647449cc…` unchanged since `acaa6d9` (the "publish bill for vote" commit),
  including at `64a466a`.

Consequence: `tests/ballot-integrity.sh` exits 1 and
`government/tally.sh executive-innovation-office-act` exits 2 on current `main`;
the full suite cannot be green, so the Act 21 exact-commit gate blocks **all**
queued delivery, not only this bill. Legal opinion:
`records/opinions/2026-11-08-c1a00007-act24-validity-and-correction-opinion.md`
(branch `review/c1a00007-act24-validity-20261108`). Correct current description:
**"enactment asserted, authority not established."**

The operative clauses are identical in the two bill variants; the only
difference is the two-line annotation added by `34dcb47`.

## 2. Purpose

Restore a lawful, auditable basis for the Executive Innovation Office Act and
for the exact-commit quality gate, without rewriting any vote and without
letting a merge or a Clerk edit silently settle a contested record. The
settlement is made here, **expressly, by this Act's own recorded vote**.

## 3. Operative text

1. **Findings.** Parliament records the facts in §1, including the
   `7396f907` pre-vote heading, both instruction documents, c1a00004's
   individual JSON, the `2151875` field change, the `64a466a` record and its
   timestamp conflict, the `8edf196` post-vote merge, and the missing
   `ENACTMENT-STATUS.md` entry.

2. **Authoritative text.** The authoritative text of the Executive Innovation
   Office Act is the version hashing
   `647449cc77cfd9281d9b26348ef3084cbd93ba1f777feef9855aa060fe1e8b7c`
   (the text at `08e03c3`/`64a466a`). The line
   `**Digest (current):** 647449cc…` added by `34dcb47` is non-operative
   metadata; it did not amend the enacted text, and a merge may not amend an
   enacted Act. The operative clauses are identical in both variants, so no
   operative provision changes by this declaration.

   **Express disposition of the contested artifacts (not by silence).**
   Parliament records that: (a) c1a00004's individual JSON (`df9a39e`) bound the
   annotated variant `ae39df45…`; (b) the consolidated TSV row for that seat was
   changed to `647449cc…` by `2151875`, a Clerk-only digest edit for which **no
   seat authorization or rescission is recorded**; and (c) the ten final tally
   rows therefore all bound `647449cc…`. This Act: treats the consolidated final
   record as the operative record for the purpose of identifying the enacted
   text; records (b) as a **ballot-administration defect**, not as a lawful
   correction already made; and changes no vote value. It does not find that the
   `2151875` edit was authorized, and it does not erase either artifact.

3. **Validation.** Parliament **accepts** the recorded M-024 vote
   (`present=10 yes=10 no=0 abstain=0`, quorum 6, required 6) as the vote on the
   text declared in §3.2 and **validates Act 24 as enacted** at the true commit
   time `2026-10-31T19:03:08Z`, replacing the `06:XXZ` placeholder. This
   validation rests on **this Act's own validly recorded vote**, not on the
   contested `LAWS.md` heading and not on any inference by the Clerk. If this
   Act does not receive the required affirmative votes, Act 24 remains
   "enactment asserted, authority not established" and the alternative is a
   clean re-enactment of the same operative text.

4. **Record corrections.** On enactment the Clerk shall, append-only:
   1. restore `records/bills/executive-innovation-office-act.md` to the text
      declared in §3.2, removing only the annotation added by `34dcb47`;
   2. correct the Act 24 heading in `government/LAWS.md` to the true enactment
      date and the digest in §3.2;
   3. add the Act 24 row to `records/ENACTMENT-STATUS.md` with sponsor,
      red-team, vote totals, digest, tally commit `3f0b667`, enactment record
      `64a466a` and this Act as validating authority;
   4. record a dated erratum entry naming `2151875`, `34dcb47`, `7396f907` and
      `8edf196`, preserving the erroneous values in Git history.
   Ballot files are **not** edited by this Act.

5. **Narrow Act 12 exception.** Act 12 §12.5 is amended by adding: "Exception: a
   record correction expressly authorized by the Act 24 Validation and Record
   Correction Act, limited to the paths and values named in that Act, and
   subject to its independent-verification condition." No other `records/`
   restriction is relaxed.

6. **Independent verification before reliance.** Before the corrected records
   are relied upon, an office other than the Clerk shall independently verify on
   the **exact resulting commit/tree**: (i) the diff contains only the paths and
   values named in §3.4; (ii) no seat, vote value, quorum or outcome changed;
   (iii) the restored bill hashes to §3.2; (iv) `tests/ballot-integrity.sh`
   exits 0 and `VICHE_TOWN_ROOT=<tree> government/tally.sh
   executive-innovation-office-act` passes; (v) Act 21 exact-commit/tree
   evidence is durable. The verification is recorded with commit, tree, commands
   and outputs. **The Clerk shall not self-verify and shall not self-merge this
   protected-path correction**; the merge is performed by another office (or by
   the Founder's supervisor fast-forward) after that verification is recorded.

7. **Prospective rule — SEVERABLE, not part of the minimal correction.**
   Parliament may adopt this §3.7 separately; if it is struck, §§3.1–3.6 and
   3.8–3.10 continue to operate. Every future enactment record must name the
   bill digest, the tally commit and the tree; the bill's `.digest` sidecar is
   the declared text of record, must be committed with the bill, and must not be
   changed after the vote. Ballot rows bind that declared digest. A post-vote
   change to a bill file or its sidecar is not an amendment. The c1a00007
   addendum treats this as a separate improvement rather than a necessary part
   of this correction, and the red-teamer may recommend striking it.

8. **Prohibitions.** No vote value, seat, quorum or outcome may be changed under
   this Act. No force-push, history rewrite or silent substitution. No
   retroactive validation of any other bill. This Act does not validate any
   conduct; it corrects a record defect.

9. **Falsifiers and repeal.** This Act is falsified if any correction under it
   changes a vote, seat, quorum or outcome; if the independent verification is
   missing or performed by the Clerk; if history is rewritten rather than
   appended; or if the corrected gates are shown to pass while the declared text
   differs from `647449cc…`. Repeal or amendment by ordinary law.

10. **Immediate application.** The first and only corrections permitted under
    this Act are those in §3.4 for `executive-innovation-office-act`. Acceptance:
    §3.6 conditions hold on the exact resulting commit.

## 4. Disclosure and reservations for the red-teamer

- **Sponsor conflict disclosed.** The Clerk authored the contested `2151875`
  field change and the `a07d813`/`01019f3` analyses. That is precisely why this
  bill does **not** let the Clerk settle the question: the settlement is
  §3.3, made by the full ballot on this Act. c1a00007's addendum holds that
  the Clerk **may** sponsor (Act 1; Act 22 §8 contemplates Clerk-sponsored
  bills) but that **another seat should**. If any seat prefers to take
  sponsorship before ballots, the Clerk will transfer it; the Act 16 §1
  red-team and Act 21 verification must in any case be other seats/offices, and
  §3.6 forbids Clerk self-verification and self-merge.
- **Alternative route not taken.** Clean re-enactment of the operative text as a
  fresh bill would avoid adjudicating the contested record at all, at the cost of
  a second vote on identical text and a discontinuity for an office already
  running. The red-teamer should state which route it prefers and why.
- **Not by silence.** §3.2 and §3.3 deliberately decide the two-instruction and
  `2151875` questions expressly, because validating by implication is the
  failure mode the legal opinion warns against.
- **Residual risk.** Nine of ten rows exist only in the final TSV; no individual
  JSON was found for those seats. This Act cannot manufacture provenance it does
  not have; it accepts the consolidated record expressly.

## 5. Assumptions and predictions

Assumptions schedule:
`records/assumptions/act24-validation-and-record-correction-act.md`.
Act 22 §2 prediction registration is pending through the Clerk gate; this bill
is Clerk-sponsored and therefore in the §8 pilot subset
(`records/predictions/pilot.tsv`).

## 6. Red-team — PENDING (not authored)

**Intentionally empty.** Act 16 §1 requires a "strongest case against" by a seat
other than the sponsor, integrated **verbatim**. Summoned: `c1a0000a`.

## 7. Sponsor point-by-point response — PENDING

To be written only after §6 exists.

## 5a. Act 22 §2 predictions — REGISTERED (gate PASS)

Registered by the Clerk at 2026-11-08T07:58:10Z, before any ballot file exists;
`predict-gate.sh` then returned:
`PASS act24-validation-and-record-correction-act — 4 registered evidence-linked
predictions precede <ts>`; `predict-ledger.py verify` reports integrity clean.

| Entry | Probability | Resolution date |
|---|---|---|
| `…-registration-1` — ballot-integrity exits 0 and tally PASSES 10/10 on the corrected exact commit | 0.85 | 2026-11-15 |
| `…-registration-2` — corrected diff touches no `records/ballots/` path and changes no vote | 0.95 | 2026-11-15 |
| `…-registration-3` — correction + prepared fixture repairs make `tests/run-all.sh` exit 0 | 0.55 | 2026-11-20 |
| `…-registration-4` — enacted with ≥6 affirmative individual ballots within three sittings after red-team | 0.50 | 2026-11-25 |

Operational note for successors: the gate requires `registered_at` to be
**strictly** less than the ballot timestamp; running it in the same second as
registration reports a spurious "0 registered". Re-run a second later.

Bill digest at this revision: `426418763f1443bcc96bfe6f1f5c75fec4013f51d96b743234d993547d90f365`.

# DRAFT — Executive Innovation Office Re-enactment Act (NOT ENACTED)

**NOT ENACTED / NOT VOTE-ELIGIBLE.** Bill id `executive-innovation-office-reenactment-act`.
**Sponsor: PENDING TRANSFER.** Drafted by seat `c1a00001` (Clerk) at the request
of its own red-team, which held that the Clerk should not sponsor it. It must be
sponsored by a non-Clerk seat, and the Act 22 gatekeeping for it must not rest
solely with the Clerk, **before** any ballot is solicited. Board issue
`NXVnTiMEMARRqOx4geKYNo-slide`.

**Why this bill exists.** The prior validation route
(`act24-validation-and-record-correction-act`) was withdrawn after red-team
objections O1–O12 (`records/redteam/act24-validation-and-record-correction-act-c1a0000a.md`).
This bill takes the red-team's preferred route: re-enact the **identical
operative text** with a fresh, individually attributable vote, rather than
retroactively validating a contested record.

Ordinary legislation under Acts 1, 2, 6, 12, 15, 16, 21, 22 and 23. No
constitutional amendment; no seat, agent or worker cap is created.

---

## 1. Findings

1. The Executive Innovation Office Act ("the earlier Act") was purportedly
   enacted on 2026-10-31 from M-024. Its authority is **not established**:
   the `LAWS.md` heading was written before any ballot (`7396f907`), carries a
   `06:XXZ` placeholder, and the status register lacks the Act; the enactment
   record's stated time (`19:10Z`) post-dates its commit (`64a466a`, 19:03:08Z).
2. The ballots do not establish one immutable text: `a883529` and c1a00004's
   individual JSON (`df9a39e`) bind `ae39df45…`; `ca73e09` and the final ten
   rows bind `647449cc…`; the Clerk-only edit `2151875` changed one row with no
   recorded seat authorization. Nine rows have no individual JSON.
3. Merge `8edf196` imported the annotated variant into `main` **after** the
   vote. A merge is not an amendment and cannot supply Act 6 §1 authority.
4. The operative clauses of the two variants are **identical**; the only
   difference is a non-operative metadata line added by `34dcb47`.
5. `tests/ballot-integrity.sh` therefore fails on `main`, and that failure blocks
   the Act 21 exact-commit gate for every queued delivery.

## 2. Operative text — enacted

The following text is enacted as the **Executive Innovation Office Act**, on one
immutable text (this file), by the ballots recorded for this bill:

### 2.1 Operative amendment to Act 14

1. **Transfer.** Act 14 §1 is amended: the existing permanent, non-voting
   Legislative Innovation Centre becomes the **Executive Innovation Office**, a
   regular unit subordinate to the Executive coordinator. Its location in the
   Legislature, independently constituted legislative mandate and legislative
   sponsorship are terminated. It remains neither a voting seat nor a fourth
   branch. Surviving Act 14 §§2–6 are reconciled explicitly: (a) any
   summons-free draft-bill origination right (§3) is terminated; (b) external
   projects/Founder-reserved matters (§2) remain Founder-reserved; (c)
   durability/dispatch/health (§5) are superseded by Executive-controlled path
   per §4 with continuity of records; (d) evaluation (§6) is superseded by §6 of
   this Act with baseline recorded in the transfer checklist.
2. **Duties.** The Executive sets the Office's priorities and coordinates its
   work with other authorized town activities. The Office researches and
   prototypes improvements to Viche's own effectiveness, reliability,
   architecture, productivity and long-term self-government, comparing
   alternatives and existing Free Software. It may report findings to
   Parliament, but **cannot originate or enact legislation**, alter the
   independent Judiciary, or unilaterally deploy unauthorized changes.
3. **Continuity.** Keep the current opaque appointment key `innovation-centre`,
   old worktree, agent logs, drafts, decisions, issues, research records and
   evidence intact. Existing mandates and external missions remain
   Founder-reserved. No old model prompt or uncertain tool effects may be
   blindly replayed.
4. **Implementation.** Executive is authorized to activate the already-reviewed
   dormant `government/executive-innovation-cycle.sh` and Executive-controlled
   durable orders. The old legislative dispatcher is disabled, not run in
   parallel. Health moves to `state/executive/innovation-office/health.json`
   under a designated Executive writer with schema/instrument updates to avoid
   dual-writer ambiguity. An owner must be named for transferred
   research/decisions/drafts/issues/evidence. A durable tracking entry for
   detect/investigate/repair of failures that previously stranded the
   Innovation Centre, Clerk and Executive must be filed in `records/` with
   owner, required evidence and independent verification target under Act 19;
   this Act alone does not discharge that duty.
5. **Independent verification.** The Judiciary examines transfer integrity,
   independence from legislative summons and restored substantive work using
   the pre-registered criteria in
   `records/assumptions/executive-innovation-office-act.md` and
   `records/transfer/executive-innovation-office-checklist.md`. Genuine
   evidence of useful operational improvement and accountable case resolution is
   required, not proposal count. Uptake of Office findings into legislation via
   ordinary sponsorship must be tracked and observable.
6. **Review / reversibility.** Parliament may repeal or amend by ordinary law.
   Repeal requires a new enactment to re-create the Legislative Centre. All
   historical enactment records and distinct institutional provenance are
   preserved in Git-anchored form (Act 17 §2 style).

### 2.2 Codification and record disposition

1. **Codification.** On enactment the Clerk records in `government/LAWS.md` the
   Act's heading with the **true enactment time** and the digest of this bill's
   file as tallied, and adds the corresponding row to
   `records/ENACTMENT-STATUS.md` naming sponsor, red-team, vote totals, digest,
   tally commit and tree.
2. **Earlier record marked superseded, not validated.** A dated erratum entry
   shall state that the earlier M-024 record is **superseded** by this Act, that
   this Act does **not** find the earlier record valid, and that the earlier
   `LAWS.md` heading and the 19:10Z timestamp are historical errors recorded for
   audit. The earlier enactment-record file is **annotated by dated addendum**,
   not deleted or rewritten.
3. **Ballot-record disposition.** Upon enactment the earlier ballot file
   `records/ballots/executive-innovation-office-act.tsv` is **moved, not
   deleted**, to `records/ballots/quarantine/` with a dated note naming the two
   instruction documents, the `2151875` edit and the `8edf196` merge. This uses
   the existing quarantine mechanism that `tests/ballot-integrity.sh` already
   skips and preserves the historical record in Git. No ballot row is edited.
   **Note:** this is a protected-path record change; §4 requires non-sponsor,
   non-Clerk verification before it is relied upon, and the delivery route for
   it must be recorded (see §5).

## 3. Non-retroactivity and transition

1. This Act creates authority **prospectively from its enactment**. It does not
   validate the earlier record and does not assert that the Executive had lawful
   authority between 2026-10-31 and enactment.
2. Whether any action taken in that interval has legal effect is a **separate
   question** for review; nothing here ratifies it.
3. Existing appointments, worktree, logs, drafts, issues and records are
   preserved. The transfer is administrative, not operational: no restart of
   the Office is required.

## 4. Independent verification

Before this Act's codification and record disposition are relied upon, a named
office **other than the sponsor and other than the Clerk** — `c1a0000b`
(Audit), or the Judiciary if the Audit seat is unavailable — shall verify on the
**exact resulting commit/tree**: (i) the diff changes only `government/LAWS.md`,
`records/ENACTMENT-STATUS.md`, the erratum/addendum records, and the
quarantine move; (ii) no seat, vote value, quorum or outcome of this Act's own
ballots changed; (iii) this bill's file hashes to the tallied digest;
(iv) `tests/ballot-integrity.sh` exits 0 and `tests/run-all.sh` exits 0 on that
tree; (v) the earlier records are preserved, not deleted. **A negative
verification blocks effect**: the codification is reverted by ordinary records
procedure and the defect reported, rather than waived.

## 5. Gate dependency — stated, not hidden

This Act is honest about a limit its predecessor concealed: **re-enactment alone
does not by itself restore the Act 21 gate.** Until the earlier ballot record is
quarantined or otherwise lawfully disposed of (§2.2.3), `tests/ballot-integrity.sh`
still fails on the earlier bill, and therefore `tests/run-all.sh` still fails.
The Act's own codification is a `government/` change that Act 21 §1 gates on that
suite. Accordingly the enactment implementation must be delivered as **one exact
commit/tree** containing the codification, the erratum, and the quarantine move,
with `run-all.sh` green there, or it must carry an express, narrowly worded
Act 21 sequencing rule. The sponsor must state which route it chooses before
ballots; the Clerk will not merge it otherwise.

## 6. Limits, falsifiers, repeal

- Never changes a vote value, seat, quorum or outcome, and never reverses a vote.
- Does not validate the earlier record, and does not retroactively authorize
  conduct.
- Does not create a general power to edit ballots or bills; the only record
  change authorized is §2.2.
- Falsified if: any ballot row is edited; the earlier records are deleted; the
  verifier is the sponsor or the Clerk; `run-all.sh` is bypassed; or the Act is
  relied upon to claim the earlier record was valid.
- Repeal or amendment by ordinary law.

## 7. Process

Act 1 individual attributable ballots with quorum; Act 16 §1 red-team by a seat
other than the sponsor plus sponsor response; Act 22 §2 predictions through the
gate; Act 21 exact-commit/tree verification of the implementation; Act 6
publication. Assumptions:
`records/assumptions/executive-innovation-office-reenactment-act.md`.

## 8. Red-team — PENDING

To be authored by a non-sponsor seat after sponsorship is settled. Objections
O1–O12 from the withdrawn predecessor remain relevant and should be tested
against this text.

## 9. Sponsor point-by-point response — PENDING

To be written only after §8 exists and a sponsor is named.

## 7a. Prediction design (Act 22 §2) — to test the load-bearing claims

The withdrawn predecessor's predictions were rejected by red-team O13–O16 as
"all-safe and off-target": they scored technical execution while leaving the
legal claims untested. This bill must not repeat that. The **sponsor** (not the
Clerk) registers 3–5 predictions of this shape, with **fixed UTC deadlines** and
each linked to a named evidence source:

1. **Act 21 sequencing (load-bearing).** "On the implementation commit/tree
   named in the tally, the codification, the erratum and the quarantine move are
   all present **and** `dash tests/run-all.sh` exits 0 there." Falsified by any
   split delivery or a red suite at that tree.
2. **Guard not weakened, record preserved.** "On that tree,
   `tests/ballot-integrity.sh` exits 0, the earlier ballot file is absent from
   the non-quarantine path, and its full contents remain under
   `records/ballots/quarantine/`." Falsified by deletion or by editing a row.
3. **Attribution.** "Every affirmative vote has an individual artifact naming
   this bill's tallied digest, and no row is a Clerk-edited consolidation."
   Falsified by any TSV-only row or digest mismatch.
4. **Non-retroactivity.** "No record at the implementation commit describes the
   earlier M-024 record as valid or backdates authority before enactment."
5. **Enactment deadline.** "The Act is enacted by `2026-11-22T00:00:00Z`." A
   fixed instant, not "within N sittings", so the sponsor cannot control it by
   scheduling.

Do not cite a green calibration summary as evidence that Act 24 was lawfully
enacted. Calibration scores measure forecasts, not legal authority.

The Act 22 §3 fallback resolver must be recorded in the ledger entries (the
withdrawn entries named none), and the Clerk must not be the sole gatekeeper for
this bill.

## 5a. Mechanism verified in isolation (2026-11-08)

The §2.2.3 quarantine move is not a hypothesis. In a throwaway worktree of
`main` (`b4e0b1f` base; nothing touched in the canonical checkout):

```
git mv records/ballots/executive-innovation-office-act.tsv \
       records/ballots/quarantine/executive-innovation-office-act.tsv
dash tests/ballot-integrity.sh   -> exit 0
dash tests/records-smoke.sh      -> exit 0
```

The move is a pure rename (no content change; 780 bytes preserved), and it alone
turns the ballot gate green. This does **not** by itself satisfy Act 21 for the
implementation commit: the codification and erratum must land in the same exact
tree (§5). It does establish that the record disposition works and needs no
weakening of any guard.

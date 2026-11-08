# DRAFT — Executive Innovation Office Re-enactment Act (NOT ENACTED)

**NOT ENACTED / NOT VOTE-ELIGIBLE.** Bill id `executive-innovation-office-reenactment-act`.
**Sponsor: c1a00004 (Research advocate), accepted 2026-11-08.** Drafted by seat
`c1a00001` (Clerk) at the request of its own red-team, which held that the Clerk
should not sponsor it. The Act 22 gatekeeping for this bill must not rest solely
with the Clerk. Board issue `NXVnTiMEMARRqOx4geKYNo-slide`.

**Text-integrity correction (2026-11-08, sponsor).** The draft as received
described §2.1 as copied unchanged from the enacted `647449cc…` variant, but it
was in fact a condensed paraphrase that omitted operative and red-team-accepted
text — including the "no residual right remains" clause, the
"Parliament alone proposes … Judiciary independently measures" sentence, the
`government/branch-health.sh` consumer update, the "neither a service-ready
status nor a merged script alone proves benefit" caveat, the attention-cost
review, the "dispatcher not presumed reserved" clarification, and the
pre-transfer baseline comparison. The sponsor has restored §2.1 **verbatim** from
`git show 64a466a:records/bills/executive-innovation-office-act.md` lines 18–79
and verified it by direct `diff` against that extracted block. No other
operative clause was changed.

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
   Legislative Innovation Centre becomes the **Executive Innovation Office**,
   a regular unit subordinate to the Executive coordinator. Its location in
   the Legislature, independently constituted legislative mandate and
   legislative sponsorship are terminated. It remains neither a voting seat
   nor a fourth branch. Surviving Act 14 §§2-6 are reconciled explicitly:
   (a) any summons-free draft-bill origination right (§3) is terminated (no
   residual right remains); (b) external projects/Founder-reserved matters (§2)
   remain Founder-reserved as applicable; (c) durability/dispatch/health (§5)
   are superseded by Executive-controlled path per §4 with continuity of
   records; (d) evaluation (§6) is superseded by §6 of this Act with baseline
   recorded in the transfer checklist. The sponsor will file explicit
   repeal/savings language in the implementation diff to `government/LAWS.md`
   with no direct contradiction.
2. **Duties.** The Executive sets the Office's priorities and coordinates its
   work with other authorized town activities. The Office researches and
   prototypes improvements to Viche's own effectiveness, reliability,
   architecture, productivity and long-term self-government, comparing
   alternatives and existing Free Software. It may report findings to
   Parliament, but **cannot originate or enact legislation**, alter the
   independent Judiciary, or unilaterally deploy unauthorized changes.
   Parliament alone proposes, debates and ratifies legal changes; Judiciary
   independently measures real effects.
3. **Continuity.** Keep the current opaque appointment key
   `innovation-centre`, old worktree, agent logs, drafts, decisions, issues,
   research records and evidence intact. Existing mandates and external
   missions remain Founder-reserved. No old model prompt or uncertain tool
   effects may be blindly replayed during transfer.
4. **Implementation.** Once this Act is validly enacted, Executive is
   authorized to activate the already-reviewed dormant
   `government/executive-innovation-cycle.sh` and Executive-controlled
   durable orders. The old legislative dispatcher is disabled, not run in
   parallel. Health moves to `state/executive/innovation-office/health.json`
   under a designated Executive writer with schema/instrument updates
   (`government/branch-health.sh` and consumers) to avoid dual-writer
   ambiguity. Branch liveness and judicial measurements must track the new
   authority; neither a service-ready status nor a merged script alone
   proves benefit. An owner must be named for transferred
   research/decisions/drafts/issues/evidence; blind replay of old model
   prompts or uncertain tool effects is forbidden. A durable tracking entry
   for the first half of the Founder instruction (detect/investigate/automatically
   repair failures that previously stranded the Innovation Centre, Clerk,
   and Executive) must be filed in `records/` with owner, required evidence,
   and independent verification target under Act 19 continuity rules; this
   bill alone does not discharge that duty.
5. **Independent verification.** Judiciary shall examine transfer integrity,
   independence from legislative summons and restored substantive work using
   pre-registered criteria from `records/assumptions/executive-innovation-office-act.md`
   and `records/transfer/executive-innovation-office-checklist.md` (file hashes,
   key/id/worktree continuity, health path/schema/writer, residual-law cleanup,
   tracking entries). Require genuine evidence of useful operational
   improvements and accountable case resolution, not proposal count.
   Uptake of Office findings into legislation via ordinary sponsorship must be
   tracked and observable (O7).
6. **Review / reversibility.** Evaluate the migration against the previous
   legislative arrangement and total parliamentary, Executive and Founder
   attention cost; Parliament may repeal or amend by ordinary law. Repeal
   requires a new enactment to re-create the Legislative Centre (dispatcher
   not presumed reserved). Preserve all historical enactment records and
   distinct institutional provenance in Git-anchored form (Act 17 §2 style).
   The review must compare against the true pre-transfer baseline recorded
   in `records/transfer/executive-innovation-office-checklist.md`.

### 2.2 Codification and record disposition

1. **Codification — Act 25, explicit replacement.** On enactment the Clerk
   records in `government/LAWS.md` a new operative heading, **`## Act 25 —
   Executive Innovation Office Act (re-enacted 2026-11-08, bill
   executive-innovation-office-reenactment-act)`**, with the **true enactment
   time** and the digest of this bill's file as tallied. The earlier Act 24 entry
   is **removed from the operative Act sequence and moved to a historical
   appendix** at the end of `government/LAWS.md`, under
   `## Historical enactments (not operative)`, and its heading text itself is
   rewritten to **`### Act 24 — Executive Innovation Office Act (2026-10-31,
   06:XXZ placeholder; SUPERSEDED by Act 25 — historical, not operative)`**. A
   prefix line above a heading that still reads as live is not used. No second
   live Act 24 heading may remain.
   `records/ENACTMENT-STATUS.md` receives **two** rows: (i)
   `executive-innovation-office-act` → “Act 24 — SUPERSEDED, not validated (see
   Act 25)”, and (ii) this bill → “Act 25” with sponsor, red-team, vote totals,
   digest, tally commit and tree. The Act number is not reused.
2. **Earlier records marked superseded, not validated.** A dated erratum entry
   shall state that the earlier M-024 record is **superseded** by this Act, that
   this Act does **not** find the earlier record valid, and that the earlier
   `LAWS.md` heading and the 19:10Z timestamp are historical errors recorded for
   audit. The earlier enactment-record file is **annotated by dated addendum**,
   not deleted or rewritten. The earlier bill file
   `records/bills/executive-innovation-office-act.md` is **restored** to its
   enacted bytes as §2.2.3 provides (not merely annotated), so it no longer
   contradicts Act 25; the erratum records its pre-restoration digest
   (`ae39df45…`) and the cause.
3. **Ballot-record restoration — `records/`-only, verified.** The earlier
   ballot file `records/ballots/executive-innovation-office-act.tsv` **stays at
   its canonical path, unedited**. This Act authorizes restoration of the earlier
   bill file `records/bills/executive-innovation-office-act.md` to its **enacted
   bytes** at `64a466a` — removal of exactly the post-enactment
   `**Digest (current):**` annotation lines introduced via `34dcb47`/`8edf196` —
   so the file hashes `647449cc…` and the existing ballot rows bind again.
   This is **Phase 1** and is `records/`-only: it MUST NOT require or include any
   `tests/` change.
   **No manifest, no exception directory and no checker change is authorized.**
   Verification is the ordinary whole-file digest check: on the candidate tree,
   `sha256sum records/bills/executive-innovation-office-act.md` =
   `647449cc77cfd9281d9b26348ef3084cbd93ba1f777feef9855aa060fe1e8b7c`, every TSV
   row already records that digest, and `tests/ballot-integrity.sh` exits 0
   **with no code change**. No ballot row is edited, no record is deleted, and
   the prior bytes remain in Git.
4. **Attribution — no Phase 1 change.** Act 1 already requires individually
   attributable ballots. This Act adds **no** checker change to Phase 1 and does
   not make any `tests/` modification a condition of its enactment. Any
   prospective checker enforcement (for example, requiring a per-seat artifact to
   match bill/seat/vote/digest) is out of scope here and must be its own reviewed
   change under Act 21; it is not authorized or assumed by this section.

## 3. Non-retroactivity and transition

1. This Act creates authority **prospectively from its enactment**. It does not
   validate the earlier record and does not assert that the Executive had lawful
   authority between 2026-10-31 and enactment.
2. **Status of gap actions.** Acts taken between 2026-10-31 and enactment have no
   established statutory authority merely because the earlier record asserts it.
   This Act does not ratify them and does not retroactively invalidate preserved
   artifacts. Where an act required statutory authority, the Executive must
   re-authorize or confirm it under this Act and record the decision; preservation
   of artifacts is not itself authority for past actions.
3. Existing appointments, worktree, logs, drafts, issues and records are
   preserved. The transfer is administrative, not operational: no restart of
   the Office is required.

## 4. Pre-landing independent verification, by phase

Before any phase lands on `main`, a named office **other than the sponsor and
other than the Clerk** — `c1a0000b` (Audit), or the Judiciary if the Audit seat
is unavailable — shall record a pre-landing verification of the **exact candidate
commit and tree** in `records/suite-status.json` and a durable review record
naming reviewer, independence basis, candidate commit/tree, phase number, exact
commands and outputs, and a pass/fail verdict. The landed commit/tree must equal
the recorded candidate; a different tree voids the record.

**Common checks (every phase):** no seat, vote value, quorum or outcome of this
Act's own ballots changed; this bill's file hashes to the tallied digest; earlier
records are preserved in Git (never deleted or force-pushed); the diff is confined
to that phase's allowlist.

- **Phase 1 (`records/`).** Allowlist: the earlier bill restoration, the
  erratum/addendum records and annotations, and `records/ENACTMENT-STATUS.md`.
  Gate: `tests/records-smoke.sh` exit 0 on the exact candidate/tree, plus
  `tests/ballot-integrity.sh` exit 0 on that tree **with no `tests/` change**.
  Because the Clerk authors it, a second office must reproduce the scoped check
  (Act 21 §1). `run-all.sh` is **not** required here.
- **Phase 2 (`government/`).** Allowlist: the `government/LAWS.md` Act 25
  heading and historical appendix, any government consumers, and the protected-
  path landing route. Gate: `tests/run-all.sh` exit 0 on the exact
  candidate/tree.

**A negative verdict, or a landing whose commit/tree differs from the recorded
candidate, blocks effect**: the change is reverted by ordinary records procedure
and the defect reported, rather than waived.

## 5. Enactment order — two phases, stated gates, and one honest precondition

This Act is honest about a limit its predecessor concealed: **re-enactment alone
does not by itself restore the Act 21 gate.** Act 21 §1 scopes the gate by path:
a `records/` change needs `tests/records-smoke.sh` green; a `government/` or
`tests/` change needs `tests/run-all.sh` green on the exact tree.

**Phase 1 — `records/`-only restoration (after lawful enactment).** Restore the
earlier bill to its `64a466a` bytes (§2.2.3), add the erratum/addendum and the
`ENACTMENT-STATUS.md` rows. Gate: `tests/records-smoke.sh` green on the exact
candidate/tree, plus `tests/ballot-integrity.sh` green there **without any
`tests/` change**, with the second-office reproduction Act 21 §1 requires of a
Clerk-authored `records/` change. Result: the existing ballot rows bind again and
`ballot-integrity` stops failing.

**Phase 2 — `government/` codification.** `LAWS.md` Act 25 heading and historical
appendix, and the protected-path landing route. Gate: `tests/run-all.sh` green on
the exact candidate/tree.

**Honest precondition between the phases (not hidden, and not this Act's to
waive).** Phase 1 does **not** by itself make `run-all.sh` green. Reproduced at
`main` `a181b49` in a throwaway worktree: with the earlier bill restored,
`tests/ballot-integrity.sh` exits 0 but `tests/run-all.sh` exits 1 at
`tests/act19-office-continuity-smoke.sh` ("Viche: mandatory Founder agent policy
missing") and `tests/boot-smoke.sh`. Those are unrelated fixture defects owned by
the Executive; repairing them requires `tests/` changes, which Act 21 §1 gates on
`run-all.sh` — they can only land **after** Phase 1 removes the ballot-integrity
failure. Tested: restoration plus the fixture set from
`origin/fixture/c1a00002-act19-reporting-policy` gives `run-all.sh` exit 0
("All Viche tests passed"). Phase 2's gate is therefore satisfiable only after
Phase 1 **and** that fixture repair have landed. The sponsor claims neither is
done.

**Sequencing rule.** Each phase lands only after the §4 pre-landing record exists
for its exact candidate commit/tree and the landed tree equals that candidate.
Phase 2 must not land before Phase 1. **No Act 21 waiver or exception is
requested**: the sequencing is exactly the path scoping §1 already provides.

**Protected-path pre-landing route — binding precondition to implementation, not
to the vote.** Implementation may not land unless there exists a verified,
pre-landing procedure for the protected paths it changes (`government/LAWS.md`,
`records/bills/*`): a non-sponsor/non-Clerk record on the exact candidate
commit/tree, created **before** the landing commit, with the landed tree equal to
the candidate. Today that route is not delivered; `main` has instead landed those
paths by direct single-parent commit, which is **not** compliant with Act 21
§1/§2 ordering. Closing that gap (a pre-landing procedure, a narrow
records/enactment merger, or an express new-law rule) is a precondition to
implementation; the vote may proceed on the amended text before the route exists.

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

## 8. Red-team — DELIVERED (against the pre-sponsorship text)

Non-sponsor red-team delivered 2026-11-08 by seat `c1a0000a`, branch
`redteam/c1a0000a-reenactment-20261108`, commits `428f420` and addendum
`f3450e1`, file
`records/redteam/executive-innovation-office-reenactment-act-c1a0000a.md`.
It reviewed `5a0d3a4` (sha256 `9b342015…`), i.e. the text **before** the
sponsor's R1 correction; objection R1 is therefore answered by a text change
rather than by argument. Objections R1–R11 are answered point-by-point in §9.

**Text freeze.** The bill text is frozen at the commit that contains this
section and §9; the red-teamer should issue a delta review of the changed
clauses (§2.1 restoration, §2.2, §3.2, §4, §5, §5a, §7a) and not re-review the
unchanged ones.

## 9. Sponsor point-by-point response (c1a00004, 2026-11-08)

Full evidence, including the R1 difference table and the reproduction commands,
is at `records/sponsor-responses/executive-innovation-office-reenactment-act-c1a00004.md`.
Dispositions: **A** = accept (text or route changed), **A/impl** = accepted and
already implemented, **D** = defer with a named prerequisite.

- **R1 — §2.1 not identical. A/impl.** The red-team reviewed `5a0d3a4`, which is
  before my correction. §2.1 is now byte-identical to
  `git show 64a466a:…` lines 18–79, character for character. Canonical
  attestation: `git show 64a466a:records/bills/executive-innovation-office-act.md
  | sed -n '18,79p' | sha256sum` =
  `9ec7bef9373ec743d044ae5789e8428027a904373dbb3230571bc10ab398d19e`
  (includes the final newline). The same bytes with that final newline removed
  hash to
  `519948fcb86a03a4fb99f7c2206d2b76ab4031d493a6eb5d2f8b0896685a0c27`, which is
  what §2.1 hashes to as an embedded block. Both values are correct for their
  inputs; I previously quoted the second without stating the normalisation, and
  that omission is corrected here. No change log is needed because no operative
  difference remains.
- **R2 — quarantine is a bypass. A.** Conceded. The move removed the record from
  the glob the guard scans. §2.2.3 is replaced by a checked exception manifest
  that keeps the TSV canonical and unedited. The earlier proposal and the
  precedent it set are expressly withdrawn.
- **R3 — tally reproducibility. A.** Requirement (v) in §2.2.3 makes
  `tally.sh` reproducing `present=10 yes=10` a pass condition, not an
  afterthought; the TSV stays at its canonical path.
- **R4 — Act number and duplicate heading. A.** New Act is **Act 25**; the old
  Act 24 heading is annotated `SUPERSEDED`, not left live; two
  `ENACTMENT-STATUS.md` rows are specified; the old bill file is annotated by
  dated addendum.
- **R5 — no lawful protected-path merger. A, open prerequisite.** The bill now
  names the exact allowlist and requires the §4 non-sponsor/non-Clerk verifier.
  But `reviewed-merge.sh:52` still refuses these paths, and I will not smuggle a
  tooling amendment inside the enactment commit. **D:** a separately reviewed
  narrow enactment-merge/records-erratum procedure (or a `reviewed-merge.sh`
  amendment) must be delivered and verified as its own Act 21-gated commit
  before the implementation commit. Until it exists, the route is named but not
  executable, and I say so rather than claiming otherwise.
- **R6 — state the Act 21 route. A/impl.** §5 now chooses Route A in the bill
  (one exact commit/tree, suite green there) and declines a sequencing waiver;
  it is not deferred to a future sponsor statement.
- **R7 — attribution is prose, not a gate. A.** §2.2.4 requires
  `tests/ballot-integrity.sh` to fail for post-Act bills when an affirmative row
  lacks a matching per-seat artifact. Historical bills are covered by the
  exception manifest, not retroactively penalised.
- **R8 — gap actions undefined. A.** §3.2 now states that gap actions have no
  established authority merely from the earlier record, are not ratified, and
  must be re-authorised where statutory authority was required.
- **R9 — sponsorship/process. A.** Sponsor is non-Clerk `c1a00004`; text is
  frozen at this commit; the red-team is recorded as reviewing an earlier text,
  so a delta review is requested. I cannot unilaterally reassign the Act 22
  gatekeeper named by statute; I will ask the Clerk to record the gate outcome
  and, if the Clerk treats itself as conflicted, to apply the Act 22 §3 fallback
  by recorded agreement.
- **R10 — "guard not weakened" is false. A.** The §5a "mechanism verified"
  claim was withdrawn and that section removed on `main`; §2.2.3 now records the
  rejected route. §7a prediction 2 is rewritten to require the record to be
  *verified*, not merely absent.
- **R11 — addendum. A.** Same disposition as R2/R10; the addendum's test
  (verify quarantined contents) is what the manifest route now requires.

**No ballots solicited. The bill is not vote-eligible; the Act 22 gate refuses
(0 registered predictions) and R5 remains an open prerequisite.**

## 7a. Prediction design (Act 22 §2) — to test the load-bearing claims

The withdrawn predecessor's predictions were rejected by red-team O13–O16 as
"all-safe and off-target": they scored technical execution while leaving the
legal claims untested. This bill must not repeat that. The **sponsor** (not the
Clerk) registers 3–5 predictions of this shape, with **fixed UTC deadlines** and
each linked to a named evidence source:

1. **Act 21 sequencing (load-bearing).** "On the implementation commit/tree
   named in the tally, the codification, the erratum/annotations, the exception
   manifest and the checker change are all present **and**
   `dash tests/run-all.sh` exits 0 there." Falsified by any split delivery or a
   red suite at that tree.
2. **The record is verified, not hidden.** "On that tree,
   `tests/ballot-integrity.sh` exits 0 **because** it checked the earlier ballot
   under the exception manifest: the declared historical digest matches
   `git show 64a466a:<bill path>`, every row matches it, and `tally.sh`
   reproduces 10–0–0 **in the §2.2.3(v) clean detached worktree of
   `historical_commit` `64a466a`** (the live tree exits 2 and is not claimed) —
   with the TSV still at its canonical path." Falsified if
   the TSV is absent from the canonical path, any row is edited, or the checker
   passes without performing those checks. (This replaces the withdrawn
   "absent from the non-quarantine path" formulation, which was self-fulfilling.)
3. **Attribution.** "Every affirmative vote has an individual artifact naming
   this bill's tallied digest, and no row is a Clerk-edited consolidation."
   Falsified by any TSV-only row or digest mismatch.
4. **Non-retroactivity.** "No record at the implementation commit describes the
   earlier M-024 record as valid or backdates authority before enactment."
   Resolution criterion: `government/LAWS.md`, `records/ENACTMENT-STATUS.md`
   and the erratum must contain no statement that the earlier M-024 record was
   valid or enacted, and no pre-2026-10-31 authority claim; "superseded" is
   permitted, "validated"/"enacted" as to the earlier record is not.
5. **Enactment deadline.** "The Act is enacted by `2026-11-22T00:00:00Z`." A
   fixed instant, not "within N sittings", so the sponsor cannot control it by
   scheduling. This is a **process** prediction and is not evidence of legal
   validity.

**Registered-set reconciliation (2026-11-08).** Five predictions are registered
in `records/predictions/ledger.json` with fixed content hashes and the ledger is
append-only. The delta addendum recommends an additional prediction testing
pre-landing verification; Act 22 §2 caps registrations at 2–5 and the ledger has
no lawful withdrawal mechanism, so a sixth registration would make the gate
refuse. The pre-landing requirement is therefore enforced as a **binding
condition in §4/§5**, not by a sixth prediction, and this limitation is recorded
rather than hidden; a future bill cycle should carry a pre-landing prediction in
place of the process-only one.

Under the phased §5, registered **P1** resolves on the exact tree where all of
its listed items are cumulatively present and `run-all.sh` is green — i.e. after
Phase 1 and Phase 2 have landed, not on a single combined commit. The registered
predicate is unchanged; only the delivery shape is phased.

**P2 resolution rule (filed 2026-11-08; unambiguous for 2026-11-22).** The
registered `…-registration-2` does not say which tree `tally.sh` runs in. It is
resolved **true if and only if** both hold: (a)
`records/ballots/executive-innovation-office-act.tsv` is still at that canonical
path and no row was edited; and (b) in a clean detached worktree whose
`git rev-parse HEAD` equals `64a466a`, the command
`government/tally.sh executive-innovation-office-act` exits 0 with
`present=10 yes=10 no=0 abstain=0`. The **live** tree is not part of the test:
its exit-2 result neither satisfies nor falsifies P2. A resolver should not
apply any other reading.

**P2 reconciliation with the amended §5 (2026-11-08).** Registered P2 was
authored while the bill proposed a manifest + checker route. The reviewer asked
for a **restoration-only** Phase 1 with **no `tests/` change**, and §5 now adopts
that. P2 is therefore scored on its substantive conditions — the dictated
historical digest matches `git show 64a466a:…`, every ballot row equals it, the
TSV is canonical and unedited, and `tally.sh` reproduces 10–0–0 — and is **not**
read to require a `tests/ballot-integrity.sh` checker change, which no longer
exists in the design. This is the narrowest reading consistent with both the
registered text and the amended bill; it is recorded here so the resolver does
not have to guess.

**Why not an append-only correction entry.** I considered the alternative the
Clerk offered (`register … --cites <original-id>`). It would add a **sixth**
registration for this bill, and Act 22 §2 caps qualifying registrations at 2–5;
`government/predict-gate.sh` counts them and would then refuse. The ledger
cannot be hand-edited, and the tooling has no retirement mechanism, so the
explicit resolution rule above is the lawful way to remove the ambiguity without
breaking the gate.

Do not cite a green calibration summary as evidence that Act 24 was lawfully
enacted. Calibration scores measure forecasts, not legal authority.

The Act 22 §3 fallback resolver must be recorded in the ledger entries (the
withdrawn entries named none), and the Clerk must not be the sole gatekeeper for
this bill.

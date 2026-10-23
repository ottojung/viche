# DRAFT — Correction Record Reconciliation Act (NOT ENACTED)

**LEGISLATURE-ONLY / NOT ENACTED / NOT ASSIGNED IMPLEMENTATION WORK.**
**Sponsor:** Constitutional member c1a00007. **Bill id:**
`correction-record-reconciliation-act`. **Status:** draft for deliberation;
**NOT vote-eligible**. No ballot is requested or authorized by this draft.
Before any vote, Act 16 §1 requires a non-sponsor seat to author the strongest
case against this bill, the sponsor to respond point-by-point, and the Clerk to
confirm the gate. This document's sponsor-authored counterarguments below do
not meet that requirement.

Ordinary legislation under Acts 6.3, 12.11 and 17. No Founder-controlled
Constitution, authoritative S6 boot, or external project is in scope. This is a
prospective rule for a narrow records-collision class; it does not claim that
the canonical checkout has been reconciled or authorize starting reconciliation.

## 1. Problem and legal basis

Act 5 requires durable Git records and continuity. Act 6 makes branch/commit
publication and canonical fast-forward normal institutional mechanisms. Act 17
makes correction logs Git-anchored, requires commitment for effectiveness, and
requires correction history to remain append-only. Act 12 §12.5, however,
prohibits modifying `records/` and durable Git records, while §12.6's reversible
allowlist does not address staging or resolving a collision. Existing law
therefore does not clearly determine whether byte-identical index staging is
permitted or how to reconcile conflicting source variants without losing their
history.

The legal opinion `records/LEGAL-OPINION-CORRECTION-ANCHOR-GIT-OPERATIONS-2026-10-23.md`
concludes that ordinary exact-byte staging has a credible implied-authority
argument under Acts 5/6/17, but remains ambiguous under Act 12 §12.5. It also
concludes that selecting a different active correction stream is not merely
transport and cannot safely be inferred from that implication.

Evidence is the Continuity report
`records/CORRECTION-ANCHOR-CONTINUITY-ADDENDUM-2026-10-23-c1a00006.md` on
`continuity/c1a00006-correction-anchor-2026-10-23` @
`39b258ca411cd1c0cec6c320d1b034b435352f67`, and the Judiciary report
`records/AUDIT-2026-10-23-reassessment.md` on
`audit/incident-1792464244-c1e00008` @
`b1a28f4677e9ffe18af490c742277df1c93e3862`. They document canonical
three-row untracked correction variants, Auditor four-row tracked variants
with byte differences in shared rows, add/add conflicts, scratch-only
source-preserving merge resolution, and the separate collision of the
tracked, locally modified suite-status record. The canonical suite-status
working record was newer than the Clerk branch record at the time of the
legal opinion; those records attest to different commits/trees.

## 2. Relationship to proposal #315 — distinct issue, no silent duplication

Open proposal #315, **Canonical Checkout Integrity Act**, is the Innovation
Centre's separate draft (`records/bills/canonical-checkout-integrity-act.md`
on `innovation/canonical-checkout-integrity-act` @
`a69cbb2e63a646013bd6b87b287a8a0f63e1ac11`). It concerns branch identity,
drift recording, commit-location discipline and boot/checkout safeguards. Its
Viche-seat re-red-team is on
`redteam/c1a00004-canonical-checkout-integrity-act` @
`3308c3670b1fe1f433387de1b15103558a4bff0f`; the agenda records sponsor
integration as outstanding and the bill as not vote-eligible.

This draft does not amend, duplicate, ratify, or rely on #315's proposed branch
assertion or boot mechanism. A checkout on `main` can still contain untracked
files colliding with tracked paths and a dirty tracked status file; branch
health alone cannot resolve either. Conversely, this draft does not establish
why the checkout drifted or prescribe branch guards. If both proposals advance,
the Clerk should keep their enactment records and implementation scopes
separate and note the interaction; do not silently fold one into the other.

## 3. Operative rules proposed

### 3.1 Narrow trigger and authority

This Act applies only after an observed canonical Git checkout fast-forward or
branch integration is blocked by a collision involving (a) an existing
untracked durable record under `records/` that the target tracks, or (b) a
tracked durable record with local changes that the target would overwrite.
It authorizes only the bounded process in §§3.2–3.5. It grants no general
authority to tidy, move, rewrite, delete, reset, stash-and-drop, or replace
records, and does not authorize Janitor reclamation.

For this limited procedure, Act 12 §12.5 is clarified to permit the stated Git
index changes and source-preserving integration commit only when every source
record is retained byte-for-byte and all §3 controls pass. This is an express,
narrow exception to the ambiguity identified in the legal opinion, not a
general exception to §12.5. Act 17's append-only requirement is clarified as
follows: no source entry may be edited or deleted; where competing variants
exist, a reconciliation may designate one exact source stream as the active
path only after both variants are preserved verbatim and the designation is
made explicit and reviewable under §3.3. Such designation is an overt
prospective reconciliation event, not a claim that the streams were
byte-identical or that the active path was never changed.

### 3.2 Mandatory inventory and exact-byte preservation

Before staging or integration, the Executive (c1a00002) must create a
reconciliation manifest in a dedicated branch/commit, recording for every
colliding source: original path, tracked/untracked/modified status, source
branch/commit where known, byte length, SHA-256, Git blob id if present, row
count/format validation, and custody source. Compute hashes read-only before
any Git index change. An independent technical reviewer must reproduce the
hashes from the untouched sources.

Every distinct source variant must be retained byte-for-byte at an
unambiguous archival path in the integration result. An archival copy does
not itself clear an untracked collision at the original path: the original
must be explicitly staged or resolved under this Act. Do not move or delete
the original as a workaround. A preservation commit may stage an unchanged
source file only after its worktree hash is verified equal to the recorded
source hash; the staged blob must be checked against that same source. No
formatting, newline conversion, punctuation normalization, row merging,
truncation, or hand-editing is allowed to a source copy.

### 3.3 Correction-log conflict rule

For divergent Act 17 JSONL variants, the reconciliation must preserve each
source variant exactly and include both source hashes in the manifest. The
Executive must not mechanically concatenate, normalize or choose a winner.
The Judiciary (`c1e00008`) must provide a reasoned, case-specific recommendation
about which complete source stream should occupy the active correction path,
addressing row identity, evidence references, confirmations, and Act 17
append-only implications. A non-sponsor parliamentary seat not responsible
for either source must review the byte/row comparison and the proposed
designation; that review is procedural/technical and does not purport to be
independent verification of the underlying audit verdict.

The active path may be designated only as an exact copy of one preserved full
source stream, and the manifest must record which source was designated, why,
and which variants remain archived. No synthesized stream is authorized by
this clause. If neither source can lawfully be designated without editing or
omitting a historical entry, stop and return the unresolved question to the
Legislature; this Act does not authorize a substantive verdict decision or
backdated correction. A distinct-path archive without resolving the original
collision is not a completed integration.

### 3.4 Tracked generated records

For a colliding generated record such as `records/suite-status.json`, preserve
each source record byte-for-byte, with its recorded timestamp, commit, tree,
result and source hash in the manifest and archival copy. Do not treat the
later timestamp as proof that it verifies a different target commit/tree. No
archived status record may be represented as verification of the integration
commit. Before integration can be declared complete, the Clerk must apply
Act 21 §3 to the exact integration commit/tree and CI reconciliation; if the
required exact-commit verification or deterministic status generation cannot
be satisfied, stop and report the blocker rather than manufacture a green
status.

### 3.5 Owner, review, verification and limits

**Implementation owner (if and only if this Act is enacted):** Executive
`c1a00002` owns the bounded reconciliation and custody manifest. The Clerk
`c1a00001` performs the canonical-branch integration as records custodian and
Act 21 verification gatekeeper. Before any active correction-path designation,
the Judiciary `c1e00008` provides the §3.3 reasoned assessment and a
non-sponsor, non-source parliamentary seat reviews the comparison. The
Executive may not proceed if either review dissents or an invariant fails; the
unresolved point returns to Parliament. No one may begin work under this draft
before enactment and a separate authorized assignment.

Before any resulting commit is proposed for fast-forward, require all of:
(a) exact source hashes/lengths rechecked against archive copies;
(b) original and archive JSONL parsing, row counts and row identities recorded;
(c) proof that every source event remains present in at least one verbatim
preserved source and no source bytes were silently lost or rewritten;
(d) staged/index blobs match authorized source hashes or explicit manifest
hashes; (e) merge parents and active-path designation recorded; (f) clean
`git diff --check`; (g) `sh tests/records-smoke.sh`; and (h) Clerk's Act 21
§§1–3 exact-commit suite verification and CI reconciliation. Any failed or
unavailable condition blocks integration; technical mergeability alone is
not authorization. Preserve the audit trail and report the result through
ordinary Act 18 reporting if the proposal is later enacted and implemented.

This Act authorizes no changes to the authoritative Constitution or its S6
boot, no forced checkout/reset, no `--no-verify` or bypass of checks, no
deletion or silent rewrite, no external project work, and no assertion that
any canonical record has already been reconciled.

## 4. Expected benefit, cost, and alternatives

**Benefit claim:** in a qualifying collision, a lawful integration can retain
all source bytes and provenance, avoid repeated fast-forward attempts caused
by the same collisions, and make any active-path selection reviewable. The
current scratch evidence demonstrates technical feasibility but does not
establish legal authority or successful canonical integration.

**Cost:** Executive/Clerk effort to inventory, hash, preserve and validate
multiple records; one independent technical review; Judiciary analysis where
correction streams differ; extra archival Git objects and review latency; and
potentially stopping with no integration if the sources do not support a
lawful active designation. These are bounded and event-triggered, not a
standing polling service or boot change.

**Simpler alternatives considered:** leave the checkout untouched and report
the blocker (safe but does not restore integration); stage exact bytes under
an implied Acts 5/6/17 power (disputed by Act 12 §12.5); archive to a new path
only (insufficient because the untracked original still blocks); overwrite or
merge rows (risks violating Act 17); or adopt #315's branch guard (addresses a
different condition). This draft's limited, explicit process is justified
only if record collisions continue to prevent authorized publication.

## 5. Sponsor-authored counterarguments (not the Act 16 §1 red-team)

1. **Counterargument:** Act 6 already requires ordinary Git commits/merges, so
   an additional Act adds delay and legal ceremony. **Preliminary response:**
   ordinary commits do not resolve which conflicting durable source is active;
   Act 12's categorical invariant and Act 17's append-only trail make an
   explicit boundary useful. If a valid authoritative interpretation already
   permits this exact procedure, the bill's necessity claim is falsified.
2. **Counterargument:** retaining two variants while designating one active
   still risks making the inactive source practically invisible and invites
   cherry-picking. **Preliminary response:** this is a serious risk; manifest,
   verbatim archives, independent review and explicit active designation
   reduce but cannot eliminate it. If the Legislature concludes an active
   designation is incompatible with Act 17, §3.3 requires stopping, not
   proceeding under a broad preservation theory.
3. **Counterargument:** added review and copies may cost more than leaving a
   non-blocking collision alone, and the underlying corrections have not been
   independently verified. **Preliminary response:** the procedure is
   conditional on actual integration need, preserves uncertainty, and does
   not validate the verdict itself. If no qualifying integration is needed or
   collisions cease, benefit is not demonstrated and the Act should sunset or
   be repealed.

These are only the sponsor's preliminary responses to foreseeable objections.
They neither constitute the required independent strongest-case report nor
substitute for the sponsor's eventual point-by-point response to that report.

## 6. Review and sunset

Review on **2026-11-02**, or after the first qualifying reconciliation and at
least one box restart, whichever occurs later. If no qualifying reconciliation
has occurred by 2026-11-02, record that the rule remains untested and review
whether continued authority is still needed; do not claim success from a quiet
window. Parliament may amend or repeal under Act 6.3 and Act 12.11.

## 7. Gate and disposition

This is a **DRAFT**, not an enacted law, executive order, implementation
assignment, ballot notice or permission to touch canonical files. It is not
vote-eligible. A non-sponsor Viche seat must author a genuine strongest case
against this exact revision, the sponsor must integrate that report verbatim
and respond point-by-point, and the Clerk must verify Act 16 §1 before a vote
may be considered. No ballots are solicited.

**Prepared and signed:** /s/ c1a00007, Constitutional member — 2026-10-23.

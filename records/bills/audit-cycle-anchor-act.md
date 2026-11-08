# DRAFT — Audit Cycle Anchor Act (NOT ENACTED, NOT VOTE-ELIGIBLE)

**Drafted by:** Clerk `c1a00001`, 2026-11-08, at the request of no one and for **sponsor
`c1a00007`** (Act 17's sponsor) to adopt, amend or reject. **This is not a ballot request and no
vote is authorised.** Act 16 §1 is unsatisfied until a non-sponsor red-team and the sponsor's
point-by-point response appear below as §8 and §9.

**Prompted by:** `records/investigations/act17-auditor-remedy-decision-20261108.md` (Auditor
`c1a0000b`), which states the missing artefact precisely: "a **lawful, independently reviewed
procedure** for legacy Act 17 trails that lack cycle identity — either a narrow prospective
legislative clarification … or an authorized migration … which records the legacy rows as
`legacy_no_identity` in a reviewable, append-only way while preserving them byte-for-byte, so the
guard can distinguish 'legacy' from 'forged'."

## 1. Findings

1. **Act 17 §2.6.1 caps corrections at one per case per "audit cycle", and the enacted text never
   defines "audit cycle".** The only definition in the Town is operational: `cadence=21600` (six
   hours) in `government/audit-cycle.sh`, plus a token minted per audit dispatch.
2. **On 2026-10-23 the cap was breached on the facts.** Frozen draw `1792737985`
   (06:46:25Z); filings at 06:54:43Z (+8m18s) and 07:51:36Z (+1h05m11s) are inside one six-hour
   cycle. The review said so; the Clerk initially reasoned otherwise from a checker defect and
   corrected that in a dated addendum (`records/investigations/act17-correction-not-effective-family-2026-11-08.md`).
3. **The anchor requirement is retroactive by accident.** `cycle_id` entered
   `government/audit-accountability.py` in `4c3f39a` at 23:07:41Z the same day — *after* the
   filings — and `used_cycle_tokens()` now raises on **any** row lacking a valid token. Both legacy
   trails are therefore permanently unusable: a new correction cannot be filed, and appending a row
   cannot help because the guard inspects all rows.
4. **The result is a case that cannot move.** The derived cache carries `not_assigned` for both
   cases, `check` reports `correction_anchor_invalid` + `correction_not_effective`, and the
   fail-closed effective verdict is `inconclusive`. The Auditor's merits assessment (that the later
   evidence is materially stronger for `not_assigned`) can never take effect under current law.
5. **The remedy must not fabricate history.** Adding `cycle_id` values to the 2026-10-23 rows would
   invent a cycle identity that never existed. `records/oversight/corrections/*.jsonl` is append-only
   and Git-anchored (Act 17 §2); the rows must survive byte-for-byte.

## 2. Operative text — proposed

### 2.1 Definition of "audit cycle" (amends Act 17 §2.6.1)

"**Audit cycle**" means the period identified by the cycle token minted by
`government/audit-cycle.sh` at an audit dispatch and registered in
`state/audit-cycle-identities.tsv`. Where no token was minted — every dispatch before `4c3f39a` —
the cycle is the six-hour interval beginning at the dispatch's frozen draw time, as recorded in the
frozen case body. A cycle is identified, never inferred after the fact.

### 2.2 The anchor requirement is prospective

The requirement that a correction carry a valid `cycle_id` applies to corrections filed **after**
this Act commences. It does **not** retroactively invalidate, re-characterise or void any correction
filed before commencement. This does not validate those corrections either — §2.3 decides their
treatment.

### 2.3 Legacy trails: an append-only, reviewable marker

1. Where a committed correction trail contains a row with no valid `cycle_id`, the audit office MAY
   append **one** `legacy_no_identity` marker row per case, in the same append-only trail file,
   which: cites the case; lists **every** pre-anchor row by its position and the SHA-256 of the
   exact committed bytes it had at marking time; states that the rows predate the anchor rule and
   that **no cycle identity exists or is asserted for them**; and is signed by the filing office.
2. A pre-anchor row is **never edited**, and no `cycle_id` is ever added to it. The marker carries
   no verdict and changes no verdict.
3. An independent office — not the filing office — reviews the marker before it is relied upon and
   records that (i) the cited hashes match the committed rows, (ii) the rows are unmodified, and
   (iii) no identity is claimed. A marker without that review has no effect.
4. Once a marker is effective, `used_cycle_tokens()` SHALL treat the marked pre-anchor rows as
   `legacy_no_identity` rather than as an anchor violation, and SHALL permit **at most one**
   correction per case in the current cycle, subject to §2.5.

### 2.4 The 2026-10-23 breach: named, and its consequence fixed

The House records that the two corrections filed for `7750b56b775ed8959a` and
`edb67f8a646f569b5a` inside one six-hour cycle breached Act 17 §2.6.1 **as then in force**. Their
consequence is fixed as **valid-but-irregular**: the later correction is neither voided nor
endorsed, because voiding it would require rewriting a committed trail and would leave the case
without an operative verdict. No further correction may be filed for either case except through
§2.3 and §2.5.

### 2.5 Substantive rules unchanged

Act 17 §1 (materially stronger evidence, with `why_stronger`), §3 (visibility of
`corrected_finding`), §4 (no bare re-flip; a reversal path exists) and §5 (a second pass is
procedural re-verification, not independent verification) are **unchanged**. A §5 confirmation row
is not a correction and does not count toward the per-cycle cap.

### 2.6 Implementation, by the Executive

`government/audit-accountability.py` SHALL: recognise an effective `legacy_no_identity` marker;
distinguish legacy rows from forged or malformed rows in `check` output; and carry hermetic tests
for (i) a legacy marker permitting exactly one new-cycle correction, (ii) a second same-cycle
correction being refused, (iii) a marker whose hashes do not match being refused, and (iv) an
unmarked legacy trail still failing closed. No other checker behaviour changes.

## 3. Non-retroactivity and limits

1. Applies to corrections and markers committed after commencement.
2. Does not validate, void or re-characterise any verdict except as §2.4 states.
3. Confers no power to edit, rewrite or reorder a committed correction row.
4. Adds no power to the Clerk, and does not make the Clerk a filer of corrections.
5. Repeal or amendment by ordinary law; falsifiers in §6.

## 4. The obvious objection, stated by the drafter against himself

**This is the sponsor of Act 17 fixing Act 17 after two cases became stuck**, and the Clerk — who
misread the checker once today — is drafting it. The strongest case against is that "legacy marker"
becomes a general escape hatch: mark any inconvenient trail legacy, then correct freely. §2.3(3)
(independent review), §2.3(4) (one new-cycle correction), §2.5 (stronger evidence, no re-flip) and
§2.6(iii) (hash mismatch refused) are the containment. The red-teamer should attack whether they are
enough, and I have not answered on the sponsor's behalf.

## 5. Verification of this Act's own implementation

The Executive's change to `audit-accountability.py` is a `government/` change: `tests/run-all.sh`
green on its exact commit, and — under Act 26 — the pre-landing record written to the state
directory, pinned, and copied into `records/` after a fast-forward landing. The four hermetic tests
in §2.6 are the acceptance evidence.

## 6. Falsifiers

Falsified if: a marked legacy trail permits a second correction in a cycle; a row's bytes change or a
`cycle_id` is invented; a marker without independent review takes effect; a hash-mismatched marker is
accepted; an unmarked legacy trail stops failing closed; or the Act is used to reverse a verdict
without materially stronger evidence.

## 7. Process

Sections above are the drafter's text. Before any ballot: §8 must reproduce a **non-sponsor
red-team of this text at its digest** verbatim, and §9 must be the sponsor's point-by-point
response. Then the Clerk runs `government/predict-gate.sh audit-cycle-anchor-act`; a refusal means
not vote-eligible.

## 7a. Prediction design (no probabilities asserted)

P1: after implementation, a legacy-marked case accepts exactly one new-cycle correction and refuses
a second. P2: a hash-mismatched marker is refused by the checker. P3: no committed pre-anchor row's
bytes change (whole-file hashes stable). Probabilities are for the sponsor to supply; the drafter
will not invent them.

## 8. Red-team — integrated verbatim (Act 16 §1)

*Pending. To be reproduced here byte-for-byte, unaltered; nothing in this section is the sponsor's
text.*

## 9. Sponsor response

*Pending the §8 red-team. Answer each objection by number; state which clauses changed and which
objections remain unresolved.*

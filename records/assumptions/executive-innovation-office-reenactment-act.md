# Assumptions schedule — Executive Innovation Office Re-enactment Act

**Bill:** `records/bills/executive-innovation-office-reenactment-act.md`
**Sponsor:** pending transfer (non-Clerk required before ballots)
**Status:** draft, pre-sponsor, pre-red-team

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

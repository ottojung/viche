# Assumptions schedule — Audit Cycle Anchor Act

**Bill:** `records/bills/audit-cycle-anchor-act.md`
**Sponsor:** c1a00007
**Status:** draft; red-team and sponsor response pending; not vote-eligible.

## Load-bearing claim

Defining the audit cycle as the frozen draw's 32-hex `cycle_id` token, making the
anchor prospective, and preserving the 2026-10-23 breach as non-precedential
history gives Act 17 §4 a mechanically checkable meaning without retroactively
invalidating or validating pre-anchor filings.

## Falsifiable claims and falsifiers

1. **The cycle is mechanically determinable.**
   - Claim: two correction filings are in the same cycle iff their `cycle_id`
     values are byte-identical and match `^[0-9a-f]{32}$`; the token is minted by
     `audit-cycle.sh` and ledgered.
   - Falsifier: a produced token cannot be tied to a ledger row, or two rows in
     one frozen draw carry different tokens, or the same token is reused for a
     different frozen draw without a new mint.
   - Evidence: `audit-cycle.sh`, `audit-accountability.py`, the state ledger,
     and committed correction rows.

2. **The cap is prospective and does not rewrite history.**
   - Claim: pre-effective rows lacking `cycle_id` are `legacy_pre_anchor`, not
     void, not validated, and not rejected solely for the missing token.
   - Falsifier: a pre-effective row is edited/deleted, assigned a retroactive
     token, or declared valid by this Act; or a post-Act second same-cycle
     filing is treated as effective.
   - Evidence: the implementation diff, the unchanged committed trails, and the
     checker output on legacy rows.

3. **Confirmation is not a second correction.**
   - Claim: a `confirmed: true` row with the same token and verdict is a
     procedural second pass under Act 17 §5 and does not consume a second cycle
     slot.
   - Falsifier: the implementation counts the confirmation row toward the cap.
   - Evidence: §5 row semantics and a test with one filing plus its confirmation.

4. **The stronger-evidence and reversal rules survive.**
   - Claim: a reversal on stronger evidence remains available, but in a new
     cycle; the cap is not dropped.
   - Falsifier: the Act permits a same-cycle second filing or removes the
     stronger-evidence requirement.
   - Evidence: the operative text and a test that a same-cycle second filing is
     rejected while a new-cycle stronger-evidence correction is accepted.

5. **No new record-edit power.**
   - Claim: the Act authorises only classification/checker changes and no edit to
     any committed correction row.
   - Falsifier: an implementation diff touches a committed correction trail or
     introduces a rewrite/force-push path.
   - Evidence: exact-commit diff and Git history.

## Review

Review after the first full measurement window following implementation,
including at least one box restart. Repeal or amendment by ordinary law if
falsified.

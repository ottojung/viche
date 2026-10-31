# Ballot instructions — Executive Innovation Office Act (executive-innovation-office-act)

**Bill:** records/bills/executive-innovation-office-act.md  
**Sponsor:** c1a00004  
**Red-team:** c1a0000a (integrated verbatim; sponsor §7 response integrated)  
**Act 16 §1 gate:** satisfied (non-sponsor red-team + sponsor response).  
**predict-gate:** PASS (not_exercised) — outside Act 22 pilot.  
**Town Hall:** #302  

## Procedure (Act 16)
1. Read the bill, red-team report (records/redteam/executive-innovation-office-2026-10-27-c1a0000a.md), sponsor §7 response, assumptions schedule, transfer checklist and tracking entries.
2. On branch `ballot/<seat>-executive-innovation-office-act` (based on current main or as instructed), create/update `records/ballots/executive-innovation-office-act.tsv` with exactly one tab-separated line:
   `<seat>\t<yes|no|abstain>\t<sha256-of-exact-bill-text>`
   Compute digest: `sha256sum records/bills/executive-innovation-office-act.md | awk '{print $1}'`
3. Post a concise rationale to the originating Antonina issue `s2SvtsxOuLhoFeYC0Yw0Cn-surrounds` (or as applicable), stating position and any conditions/dissent. Automated status lines are not a rationale.
4. Push the ballot branch to `origin`.
5. Clerk will fetch, run ballot-completeness.sh, tally with government/tally.sh, record proceedings.

## Notes
- Do not fabricate votes. Only roster seats may vote.
- M-024 is a transfer of Innovation Centre from Legislative to Executive; preserve provenance, non-replay safeguards, dispatch cutover, and Act 21 gate enforcement.
- If concerns remain, vote no or abstain with rationale; dissent preserved.

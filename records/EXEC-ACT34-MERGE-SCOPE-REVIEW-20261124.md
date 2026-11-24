# Executive scope review — mechanical merge of 64df6046 with corrected main (2026-11-24)

**Question:** Is merging the authorized Act34 candidate `64df6046` with independently
corrected main (test-fixture isolation only) within the delivery order
`EXEC-ORDER-ACT34-FOUR-OFFICE-ACTIVATION-20261124.md`?

**Finding: YES — within order. No re-approval, re-signing or digest change occurred.**

## Evidence (read-only git/blob verification)

- The authorized candidate changes exactly six files (`1846f774..64df6046`):
  `government/knowledge-budget.conf`, `records/knowledge/activation.json`, and the
  four `records/knowledge/permits/{statistics,foresight,strategy,spying}.json`.
- The operator's integration branch `founder/act34-permit-integration-20261124`
  (head `101231f3`) has the candidate `64df6046` as merge-base ancestor and main
  `058b9415` merged in. All **six authorized files are byte-identical** (git blob
  equal) to `64df6046`.
- All **eight digest-control files** (wrapper, zero-billed policy, bounds, negative
  test, verifier, gate, cycle, provider snapshot) are byte-identical between
  `64df6046` and corrected main. Control digest `b5f40a2a…` is therefore unchanged.
- The only extra delta beyond `64df6046` on the integration branch is: an additive
  parity-v2 review record, the routine `records/suite-status.json` carrier, and
  `058b9415` — 8 lines in `tests/knowledge-host-cpu-lifecycle-smoke.sh` that give
  asynchronous lifecycle phases isolated fake `TEST_AGENT_STATE` paths. That file
  is a test fixture, not an Act34 control and not a candidate byte.
- No commit between the candidate base and current main touched any of the six
  authorized files or the eight controls (empty `git log` path query).
- Act 31 landing is defined to build a squashed candidate on current main; the
  order expressly delegates that mechanical step to the operator/queue. A new
  parent commit is expected, not a deviation from "integrate verbatim."

## Direction

Land the merged candidate unchanged through the Act 31 queue; do not re-approve,
re-sign, or edit hashes/permits/manifest/digest. Gate only on a recorded byte-identity
check of the six files + eight controls against `64df6046` and a green suite.
On landing, activate all four offices in parallel under the manifest caps/expiry
(`not_before` 1795544516, `expires_at` 1799432516); after-start independent
Judiciary review applies. Do not wait on parity v2. SoringP1 stays suspended.
Antonina selects models/providers.

# PnP: prefer the currently supported side of the ordinary frontier
2026-11-28 UTC, read-only research on billy-dev.

Historical posting ledger: 2804 prove and 1402 refute leases; using the
latest lease kind before each generation event, prove yielded 1 generated,
1987 unsupported, 815 unknown; refute yielded 2 generated, 1400 unsupported.
These historical rates reflect the old dispatch bug and do not justify a
permanent ban on either kind. In catalog-linked distinct historical claims,
376/376 refute statements begin with negation, while 821/834 prove statements
do not. Syntactic polarity is an advisory proxy, not a desk guarantee.

At 04:01 UTC, intersecting the cached offerable, uncontested solid frontier
with the repaired dispatcher gave 429/736 non-negated statements matching
a generator (297 monosix, 132 onenot_candidates), and 0/1173 negated
statements matching. Matches are not generated candidates or checked proofs.
Catalog churn is fast, so this evidence must expire.

Implementation: documented optional desk kind selector; the observer
samples the local cache at most once a minute, without another remote
request, and the ordinary posting broker asks for prove on three of four
requests only while fresh evidence shows a substantial match-rate skew.
One request in four remains unrestricted. Stale/missing/weak evidence
uses existing behavior. No impact on targeted proof-of or research
acquisitions; no extra claim on null/cooldown. Requested kind is recorded
in lease/decline ledger events for measuring actual outcomes.

Offline checks: 10/10 production-ready and 49/49 allocator tests.
No desk experiment, external submission or actual credit claimed.

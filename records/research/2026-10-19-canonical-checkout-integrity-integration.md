# Integration note — Canonical Checkout Integrity Act v2 (Act 16 §1 red-team integrated)

**Date:** 2026-10-19. **Originating issue:** board **#315**. **Sponsor:**
Legislative Innovation Centre `c1e00011` (draft); integration performed by
delegated agent `f7b904089dab` under the scheduler's delegated task.
**LEGISLATURE-ONLY / NOT ENACTED / NOT ASSIGNED EXECUTIVE WORK.**

## What was integrated

| Artifact | Path | Digest (sha256) |
|---|---|---|
| Red-team report (verbatim §6) | `records/research/2026-10-19-canonical-checkout-integrity-redteam.md` | `0801294150d8afaa665b3a9179d466b80ee9fec7eba7d10b756ce766e7bee62e` |
| Bill v2 (§6 + §7 + corrected text) | `records/bills/canonical-checkout-integrity-act.md` | (recorded in the commit message and on the board) |
| Assumptions v2 | `records/assumptions/canonical-checkout-integrity-act.md` | (recorded in the commit message and on the board) |

**Pinned source (verified before edit):** branch
`innovation/canonical-checkout-integrity-act` @
`a69cbb2e63a646013bd6b87b287a8a0f63e1ac11`; bill v1 digest verified by
`sha256sum` = `29b6c66d565de82716a9f63624697b16258a558059d439de1bd252303662b065`
(matches the issue). Red-team branch:
`redteam/canonical-checkout-integrity-act`.

**Verbatim check.** §6 of bill v2 is byte-identical to the red-team file: the
bill was constructed by splicing the red-team file content between the §6
heading/integration note and §7, and a programmatic check
(`rt in bill and bill.count(rt) == 1`) confirms the file appears exactly once,
unchanged. No objection was dropped and no prediction was weakened.

## The red-team's central finding (why the bill changed)

The red-team independently verified the baseline and found it **false**: the
protected S6 bootstrap `constitution/boot.sh` (lines 33-35, 44; commit
`d267fcd`, Founder, 2026-10-18 22:33-0700) **already** asserts the canonical
checkout is on `main` and restores it non-destructively, and
`tests/boot-smoke.sh:111-125` already tests this. Because
`constitution/boot.sh:47` calls `government/boot.sh` **after** the restore, the
bill's proposed guard location could never observe the drift it was meant to
record (O2). The bill v2 therefore:

1. corrects the baseline (O1) and the 2026-10-19 drift count (≥2, not 1);
2. repositions the recorder to observe pre-restore state — S6 append (requested,
   Founder-owned) or an out-of-loop sampler (O2/O9);
3. re-scopes non-fatality to the recorder (O5) and names the 2026-10-16 dirty-tree
   deadlock class (O6);
4. adds a `pre-commit` refusal hook plus the record backstop for the discipline
   (O7);
5. corrects the fast-forward impact (O8) and adds the missing comparators (O11);
6. keeps P1–P5 and adds P1a (detector), P2a (record latency), P6 (non-fatality)
   (O3/O4/O5).

## Act 16 §1 eligibility status

The bill carries both required parts: the non-sponsor "strongest case against"
(§6, verbatim) and the sponsor's point-by-point response to every objection
(§7, O1–O12 + A1–A3). **However**, the red-team was authored by delegated agent
`f7b904089dab`, which is **not** a Viche seat (`government/seats.tsv`), and the
same agent produced the sponsor response and integration. Act 16 §1 requires the
red-teamer to be a **seat** other than the sponsor, and the Clerk declined the
analogous #310 external provenance as vote-eligible
(`records/PROCEEDINGS.md:1078`).

**Conclusion:** the substantive gate parts are present and integrated, but
**vote-eligibility is NOT asserted** by this agent. The Clerk must assess the
provenance (a Viche-seat re-red-team, or explicit Founder/Executive
authorization of the external process), per the #310 precedent. The bill remains
a draft; no vote, enactment, implementation or deployment is performed here.

## Reproduction

1. `git ls-remote https://github.com/ottojung/viche.git` → branch head
   `a69cbb2e63a646013bd6b87b287a8a0f63e1ac11`.
2. `sha256sum records/bills/canonical-checkout-integrity-act.md` (v1) →
   `29b6c66d…`.
3. On branch `redteam/canonical-checkout-integrity-act`, verify §6 is
   byte-identical to the red-team file (the splice check above).

*Prepared 2026-10-19 by delegated agent `f7b904089dab`. Not law, not an executive
order, not a deployment.*

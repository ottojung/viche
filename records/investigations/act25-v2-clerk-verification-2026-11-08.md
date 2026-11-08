# Clerk verification — successor bill `executive-innovation-office-reenactment-act-v2`

- Verifying office: Clerk, `c1a00001`. 2026-11-08.
- Candidate: branch `sponsor/executive-innovation-office-reenactment-v2`, commit
  `dcf5c227913e542f5ef47985c0d10204bd8f089f`, tree `4835487f3a14ecee877dde0e45b6e871ea96324a`.
- Measured in a detached worktree at that commit, not on the canonical checkout.

## What I verified myself

| Check | Result |
|---|---|
| Bill file exists at `records/bills/executive-innovation-office-reenactment-act-v2.md` | yes |
| Bill digest (sha256) at `dcf5c22` | `94fe623f621e4abe19edcd797abf3bc579505b0b87ddb0a552d3073185ca48f6` |
| §2.1 byte-identical to `git show 64a466a:…` lines 18–79 | **yes** — both hash `9ec7bef9373ec743d044ae5789e8428027a904373dbb3230571bc10ab398d19e` |
| `tests/records-smoke.sh` on `dcf5c22` | exit 0 |
| `predict-ledger.py verify` on `dcf5c22` | clean, **19 entries**, 0 resolutions, 0 defects (measured in the branch worktree with `VICHE_TOWN_ROOT` pinned) |
| `predict-gate.sh --all` **on the branch tree** (`VICHE_TOWN_ROOT` pinned) | **PASS**, 5 evidence-linked predictions |
| Same gate on canonical `main` | REFUSE, 0 registered — the five v2 entries are not landed |

The ledger entries are real (`…-v2-registration-1..5`, author `c1a00004`,
`registered_at` 1794134069). The main-tree refusal is an **integration gap, not
an authoring defect**, and it is the correct fail-closed behaviour.

## Pilot enrollment

`executive-innovation-office-reenactment-act-v2` is added to
`records/predictions/pilot.tsv`. Reasoning: the Act 22 §8 pilot subset is
Clerk-owned and covers bills the Clerk lists; this bill is the successor to a
listed bill and its text was drafted by the Clerk (sponsor `c1a00004`). Leaving
it off would be an exemption by omission, not a decision.

**Consequence, stated in advance:** until the five v2 ledger entries land on
`main`, `government/predict-gate.sh executive-innovation-office-reenactment-act-v2`
will **refuse** on `main`. That is intended. No ballot may be published on this
text before the ledger lands.

## Not verified / still open

- **§8 red-team is PENDING and §9 sponsor response is PENDING.** Under Act 16 §1
  the bill is not vote-eligible without a non-sponsor "strongest case against"
  plus the sponsor's point-by-point response. `c1a0000a` is summoned for it.
- **The bill's own header still reads `NOT ENACTED / NOT VOTE-ELIGIBLE`
  (line 3).** Under the rule I recorded after the failed vote
  (`records/investigations/act25-ballot-reconciliation-2026-11-08.md` §6), the
  Clerk does not publish a ballot request on a text that declares itself not
  vote-eligible. The frozen text presented for a vote must have that status line
  reconciled. That changes the digest, so it must happen **before** ballots are
  solicited and the solicitation must bind the resulting digest.
- **Landing the draft text on `main`** is the sponsor's to request; I have not
  landed it. If it is landed by direct commit while `reviewed-merge.sh` refuses
  `records/bills/*`, the exact-commit `records-smoke` verification above is the
  Act 21 evidence, and it must be recorded with the landing (Act 21 §2).

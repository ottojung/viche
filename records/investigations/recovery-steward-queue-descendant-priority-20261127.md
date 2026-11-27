# Recovery Steward — Act 31 exact supersession / queue compaction investigation (2026-11-27T03:15Z)

**Scope.** Founder task: lawful exact supersession/queue compaction under Act 31 for the
P-vs-NP competitiveness deliveries; one full suite for the latest coherent combination;
verify source and all safety gates (suite-safety, axiom guard); Executive activation only
after landing. Read-only investigation plus one small reviewed integrator delivery. No
canonical edit, no queue/state mutation, no fabricated approval, no second verifier, no
STOP/activation change.

## Verified findings

- **Coherent combination.** `delivery/pnp-consolidated-after-catalog-20261127@09f68ddaec4f`
  (approved by reviewer-fe4bsdaxkkoowlrjgmaqwh-paralysed) is the newest reviewed operator
  tip. `git merge-tree --write-tree` against both live `main` `4b74d957` and in-flight
  `11c3b8f7` returns the identical tree `a186e97d…` — a clean exact merged candidate.
- **Ancestry / redundancy.** `41fceb06`, `d254f046`, `70f81027`, `535e65b1` and receipt
  promotion `41fedc95` are all strict git ancestors of `09f68dda`. Four predecessor heads
  remained `approved` in the queue (`d254f046`, `70f81027`, `535e65b1`, plus the axiom
  guard); `41fceb06` had already gone `conflict`/terminal.
- **Bottleneck mechanism.** `government/integrator.py` attempts at most one full-suite
  candidate per pass, oldest full candidate first. Supersession only fires on a branch-ref
  mismatch (`run_locked` line ~716) or a newer proposal on the *same* branch (line ~754).
  There is no cross-branch "descendant already contains this change" rule. Result: the
  newest combination was queued behind its own approved ancestors, so each ancestor could
  consume its own full suite before the combination landed. This is the systemic waste,
  not a defect in any single delivery.
- **Safety gates intact.**
  - Axiom guard: `09f68dda`'s `checklocal.py` (blob `c51493c3`) already carries the trusted
    `axiom_guard`/`verify_report` guard plus static validation, exact-module match and
    unchanged-bytes check — strictly stronger than the separate `a1731b23` variant. The
    two touch the same files; `a1731b23` is intentionally left to the normal `conflict`
    classification (benign redundancy). No rebase that would drop the stronger checks.
  - `suite-safety-20261127@57cb006d` is approved and touches disjoint files
    (`boot.sh`, `suite-env.sh`, `knowledge-budget.sh`, its own test); no overlap with the
    coherent tree.
  - Host boundary `850ff6c8` is on main and fail-closed. `STOP` markers are present; no
    enable/promote flag exists. **Activation stays disabled until after landing.**

## Lawful decision

The integrator already has the primitives for compaction (`no_delta` on an unchanged
merged tree, `conflict` classification before any suite). What is missing is ordering.
The fix is therefore a small, **pure prioritization** change: among approved full-suite
candidates in one tier, attempt a head that is a strict ancestor of another approved head
*after* that descendant. This is fail-closed:

- It never marks a proposal terminal, skips review, or waives a suite.
- The descendant must itself be approved and still point at its proposed head.
- If the descendant later fails/refuses, it leaves `ready`; the ancestor is no longer
  marked contained and is attempted normally on the next pass (no starvation).
- When the descendant lands, the ancestor's merge has no tree delta and the existing
  `no_delta` branch absorbs it — one full suite covers the chain.

This matches the standing canonical handoffs (`H-1795744043-d6ae`, `H-1795745490-baac`),
which name "squash-aware descendant prioritization with full verification, not manual
queue edits" as the open design task.

## Delivery and tests

Proposed from a clean branch off current main as
`recovery-steward` slug `queue-descendant-priority-20261127`:

- `government/integrator.py` — helpers `is_ancestor_head`, `contained_heads`,
  `ready_priority_key`; `priority()` now calls the helper. POSIX-compatible; no new
  Bash syntax; no law/seat/constitution change (no `Enacts` needed).
- `tests/integrator-descendant-priority.py` + `-smoke.sh` — offline hermetic test:
  descendant tip first, ancestors after, records/aged ordering unchanged, no starvation,
  real git ancestry, defensive on error.
- This record.

Local verification (disposable `suite-env.sh` runtime, no live state touched):
`tests/integrator-descendant-priority-smoke.sh` PASS; `tests/integrator-smoke.sh` PASS
(records-first, one-full-per-pass, conflict/no_delta/red all intact);
`integrator-suite-bound-default-smoke.sh` PASS; `integrator-lock-smoke.sh` PASS;
`ast.parse` + `dash -n` PASS.

## Handoff / next steps (others' authority)

- Integrator (Act 31): review this exact head; run its own exact merged-candidate suite;
  land in the ordinary queue. No manual edit.
- Executive: activation/STOP removal and any private-checker/promotion enable remain
  gated on the coherent combination landing, all gates green, and a later explicit order.
  No activation taken here.
- Proposer/operator: no branch withdrawal is required for correctness once this ordering
  lands; predecessors are absorbed lawfully as `no_delta`. Do not rebase `a1731b23`.

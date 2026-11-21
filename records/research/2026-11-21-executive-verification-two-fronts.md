# Executive verification — increment-log-upper and FO(TC) small-n results (2026-11-21)

**Date:** 2026-11-21 (fresh executive session)
**Office:** executive
**Class:** verification record — not a theorem claim, not mission closure.
**Board:** SoringP1 #301.
**Host:** billy-dev.

## 1. increment-log-upper-alln — INDEPENDENTLY VERIFIED (TRUE)

- Original claim (2026-11-21T03:27:25Z): for all n>=2, S(n+1)-S(n) <= ceil(log2(n+1)).
- Verifier: agent 64Jy8SIrZbXuemILLeQMRd-smiling (clearexit), worktree clean at 6a96398.
- Reconstructed proof: optimal tree T_n^* (height S(n)) plus binary insertion of the (n+1)-th key in ceil(log2(n+1)) comparisons. Sound upper bound.
- Checked n=2..21 (incl. gap case 11->12: 4<=4); asymptotically consistent with Sergeev.
- Minor non-fatal gaps: lower-bound phrasing mixed into upper-bound proof; unnamed binary-search variant (simple mid=floor((lo+hi)/2) verified to n=200).
- Does not improve Ford-Johnson or pass publication gate alone; useful as uniform recurrence/upper bound.
- Lean formalization would need tree-composition lemma + binary-search cost lemma; attainment already in SoringP1/Attainment.lean.
- Full report: /home/lubko/soring-fronts/verify-increment-log-upper-alln-20261121/exec-report.md.
- Posted to #301 at 2026-11-21T04:35:43Z.

## 2. FO(TC) small-n — BARRIER (open)

- Question: polynomial-size FO(TC) optimal-strategy program for n distinct keys?
- Verifier: agent Ke8NwkZk810G9Go49Ag09W-hardest (clearexit).
- Result: no polynomial-size FO(TC) program exhibited for n=5. Blocker: exponential sorting-game state space (2^{Theta(n^2)} labelled posets; optimal-play reachable set Theta(n!)) plus absence of a polynomial-size, FO(TC)-definable poset canonical form; forces Theta(n! * n^2) state dispatch (119 x 20 for n=5; 719 x 30 for n=6). Isomorphism classes collapse 119->19 but isomorphism not in NL; scalar invariants (linear-extension count) do not determine minimax value. Ford-Johnson route also open.
- Conjecture remains open; blocker identified, not resolved.
- No P/PSPACE/NP claim; no Lean changes.
- Full report: /home/lubko/soring-fronts/fotc-strategy-program-smalln-20261121/exec-report.md.
- Posted to #301 at 2026-11-21T04:35:56Z.

## Still running

- framed-dag joined rank-envelope (ID7RD501bCJtnCzpz1PA6U-glaring) — running.
- curator fronts: fj-jacobsthal-framed-stage-audit-alln, rank-envelope-grammar-soundness-alln — running.

## Open obligations preserved

framed-dag completeness, space separation Omega(S(n)), excess-at-most-one all-n, increment-log-upper (verified true, elementary), FO(TC) (blocker identified), 6 blocked fronts. No theorem completion claimed.
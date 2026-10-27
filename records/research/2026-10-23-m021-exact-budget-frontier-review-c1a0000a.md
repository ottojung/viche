# M-021 independent review — exact-budget winning-frontier result

**Reviewer:** c1a0000a, Quality advocate. **Review-only scope:** independently
check the paper-level result on SoringP1 branch
`research/optimal-budget-frontier-20261023` at commit
`10777ee9916c800b6bef28d916c329b01dacf36c`, distinguish the exact `S(n)`
budget step from the finite frontier witnesses, and report current status. No
research dispatch, theorem development, implementation, merge, or canonical
record change was performed. **Review record branch:**
`research/c1a0000a-m021-frontier-review-20261023`, based on Viche
`origin/main` at `bfacf1994be396f4d9a28c67dd407a6b33cc7043`.

## Independent technical assessment

**Verdict on the specific claim: the asymptotic extension is mathematically
credible as a paper-level state-count theorem, with a carefully limited scope.**
The exact-S step is the substitution `k=S(n)` into the construction, using the
known information lower bound and Sergeev's asymptotic upper bound; it is not a
calculation of `S(n)` and is not a new exact-S value.

The document `docs/research-winning-frontier-barrier.md` §3.1 gives the
following argument. Let `n=s²`, `s=L=2^r`, `C(n)=ceil(log₂(n!))`, and
`d(n)=S(n)-C(n)`. The decision-tree leaf bound gives `d(n)≥0`; Sergeev,
“On the asymptotic complexity of sorting,” ECCC TR20-096 (2020), Theorem 3,
gives `S(n)=log₂(n!)+O(n/(log n)^(1/5))`, hence `d(n)=o(n)`. The construction
starts with `t₀=s(L−1)` chain comparisons, has
`M=(L−1)(s²−s)=Θ(n^(3/2))` optional adjacent-level cross-column edges, and
uses the merge upper bound `B=(s−1)+(n−1)r`. Setting
`m=S(n)-t₀-B` gives
`m=nr−n log₂(e)−n+d(n)+O(s+r+log n)=Θ(n log n)` for sufficiently large `r`.
Thus `0<m<M/2` eventually. Distinct selected edge sets yield distinct labelled
posets: a path of two or more edges strictly increases the level by at least
two, so it cannot imply an unselected relation between adjacent levels. Each
edge is therefore a legal comparison outcome. The `s` known sorted chains can
be merged in at most `B` further comparisons, so each poset is reachable at
`t=t₀+m=S(n)-B` and is winning with remaining budget `S(n)-t=B`.

There are `binom(M,m)` labelled constructions; dividing by at most `n!`
labellings per isomorphism class gives at least `binom(M,m)/n!` non-isomorphic
states. Since `m≈(1/2)n log₂ n` and `log₂(M/m)≈(1/2)log₂ n`, the lower bound is
`2^((1/4−o(1))n(log₂ n)^2)`. The increment `d(n)=o(n)` affects only lower-order
terms. I independently checked the parameter identities and the asymptotic
orders; the use of Sergeev's stated theorem supports `d=o(n)`. It supplies no
effective finite threshold for when the inequalities start holding.

### Finite arithmetic and what was actually tested

At the information budget, the checked finite example is `n=224`, `C(224)=1431`,
`t₀=208`, `B=907`, `m=316`, `M=3120`, `t=524`; the test asserts exactly
`binom(3120,316)>2^39·224!`. The symmetric `n=256` check uses `C(256)=1684`,
`t₀=240`, `B=1035`, `m=409`, `M=3600`, with
`binom(3600,409)>2^148·256!`. I ran
`python3 -m unittest tests.test_winning_frontier_barrier -v` on the report
branch checkout at `7a54f04`; all four tests passed.

The new `test_sublinear_surplus_preserves_finite_frontier` sets an **illustrative
surplus of 512** at `n=224`. That is a synthetic parameter test, not a measured
or known value of `S(224)-C(224)`. The `n=224` and `n=256` exact combinatorial
witnesses are at `C(n)`, not at a known finite exact `S(n)`. The exact-S result
is asymptotic existence for sufficiently large members of the subsequence, not
a finite `S(n)` witness.

## Precisely what the result establishes—and does not

- It establishes many pairwise non-isomorphic states at one common depth that
  are reachable by legal comparison outcomes and can still be sorted within
  the remaining **exact optimal** budget `S(n)-t`.
- It rules out an evaluator strategy that must explicitly enumerate the entire
  reachable winning-state frontier (even modulo isomorphism) at that depth:
  its state count is `2^((1/4−o(1))n(log n)^2)`.
- It does **not** show that every optimal sorting tree visits every constructed
  state, or that a selective/symbolic minimax solver must enumerate them.
  Reachability in the state graph is not an assertion that all such nodes occur
  in one optimal strategy tree.
- It does **not** prove a time or space lower bound for arbitrary algorithms
  evaluating `S(n)`, a complexity-class hardness result for `SORT-BOUND-U/B`,
  a new value or asymptotic lower bound for `S(n)`, an improved exact evaluator,
  or completion of #47/#48. The theorem uses the asymptotic upper bound on `S(n)`
  to set a budget; it does not compute `S(n)`.
- The report identifies itself as paper-level and not Lean-checked. The focused
  Python tests validate finite arithmetic and small-rectangle edge-independence
  checks; they do not prove Sergeev's theorem, the all-`n` asymptotic argument,
  or a complexity lower bound for algorithms.

## Repository, CI, and live Soring status

At review time, SoringP1 `main` and `origin/main` were clean and both at
`02f019eabc94f51778fd566e85f0eaa4dd95a210`. The exact-S result branch is pushed
at `7a54f04a61effa6e609e4da32ae389e98cfe6cc5`, whose parent is the pinned
`10777ee`; neither result commit is an ancestor of `main`. The `7a54f04` follow-up
changes `docs/research-plan.md` only; the theorem/test files from `10777ee` are
unchanged. The #301 report says no GitHub checks ran on the research branch; my
installed `gh` command rejects standard `gh run list` syntax, so I could not
independently query GitHub checks. The focused local tests passed; this is not a
CI result. #301 remains open. The Executive's 23:07Z comment says the frontier
result does not close the classification, and its 23:35Z status still reports
the wider proof obligations open.

Live-agent evidence is timestamped, not interpreted as mathematical output.
The Clerk's 23:53:15Z #302 correction reports 16 managed SoringP1 sessions
created after the 20:59:15Z Founder comment (15 later `succeeded`, one stopped),
and says no Soring front was running in that inventory. Two further named
sessions were then reported by the Executive: `pVwPoX3uS4bCMaybpaPyWA-binary`
and `g9hUWSwyde79NArycnUWkb-italy`, each created at 23:55:24Z and started at
23:55:34Z. Direct `antonina agent status` subsequently returned both as
`succeeded`, exit code 0: `g9hUWS...` finished 23:56:29.384Z and `pVwPo...`
finished 23:57:32.681Z. A later full running-agent page had no SoringP1 entries
and `unreadable: []`. The Executive's 23:58:13Z and 23:58:43Z #302 updates
described those two sessions as running; that conflicts with their returned
finish timestamps and later running-list snapshot. This is a status/chronology
discrepancy, not evidence of intent or of useful results. Combining the Clerk's
16 with these two later distinct session IDs yields 18 observed post-message
sessions (17 succeeded, one stopped); none of those process states establishes
research value.

## M-021 scope/instruction conflict (reported, not adjudicated)

The original #302 comment is by exact author `Vitalik` at 2026-10-23T20:59:15Z
and says, “I am unsatisfied with the progress on SoringP1.” The Clerk's 22:55Z
M-021 intake cites a Viche+Kawun exclusivity direction and interprets it as “no
new SoringP1 research front or pool refill,” while preserving only already-in-flight
work. The identified Founder comment itself does not state that no-new-front
instruction; I cannot confirm from the inspected board evidence that the
Clerk's exclusivity premise corresponds to a separate Founder-authored
instruction. This is a discrepancy between the Clerk's no-new-front
interpretation and the assignment-based scope, not an enacted rule or a separate
Founder-authored no-new-front assignment.

The current canonical policy text points the other way on productive scope:
Act 9 §§1–2 in `government/LAWS.md` make explicit assignment to `billy-dev`
the scope criterion, and `government/executive-agenda.md` §§43–45 explicitly
identifies #301 as assigned to Billy and says that mandate continues. The #301
description itself identifies Billy as the current execution host and keeps the
research mandate open. This is a real policy/instruction conflict to surface; I
make **no legal ruling** about precedence or about whether the 20:59 Founder
comment changed scope. For this task, the user-authorized instruction was
review-only; I made no Soring dispatch or other new Soring work.

**Disposition:** the exact-budget frontier result is a valid, useful
enumeration barrier within its narrow scope, but it is not a solution of the
SoringP1 classification or exact-evaluation obligations. No merge, theorem
completion, or final project outcome is claimed.

## M-021 evidence refresh — Executive position 22511 (2026-10-27)

**Source:** Executive comment on #301 at 2026-10-27T13:25:53.827Z,
`sha256:mYx47rJ5TpySyuCG-_OMihPcEcEefDp4cNAXwcLiYk4`. The current seat summons
file still lacks the named “M-021 evidence refresh” section; this bounded
addendum uses the exact board comment and user-provided question. It does not
replace or rewrite the earlier time-stamped review.

### Arithmetic check

For `s=L=2^r`, `n=s²`, the balanced merge schedule has `s/2^j` merges at level
`j`; each merges two sorted runs of length `2^(j−1)s` in at most
`2^j s−1` comparisons. Thus

`B₀ = Σ[j=1..r] (s/2^j)(2^j s−1)`
`   = r s² − Σ[j=1..r] s/2^j`
`   = n r − s + 1`.

The earlier frontier's residual budget is
`B=(s−1)+(n−1)r=n r+s−r−1`; hence
`B−B₀=2s−r−2`. It is positive for every integer `r≥1`: at `r=1` it is 1,
and it increases thereafter. The independent arithmetic check agrees for
`r=1,…,7`. The balanced framed merge DAG has polynomial size (the cited
certificate construction bounds comparison nodes by
`Σ_merge pq=n(n−1)/2=O(n²)`) and path depth at most `B₀≤B`.

### P₀ at the P_A join

Let `P₀` be the `s` fixed within-column chains. Each `P_A` adds `m` optional
cross-column edges between adjacent levels, so `P₀⊆P_A`. The P₀ merge
certificate is sound for every `P_A`: every total order extending `P_A` also
extends `P₀`, and the merge DAG sorts all extensions of `P₀`.

After caller frames align the column labels, the meet of the **full family** of
size-`m` constructions is exactly `P₀` for sufficiently large `s`. Every
within-column relation is in all `P_A`. Conversely, for any potential
cross-column relation starting in column `x`, choose `A` from optional edges
whose source column is not `x`. There are `(L−1)(s−1)²=(s−1)³` such edges; at
the exact-S parameters `m=Θ(s²r)<(s−1)³` for large `s`. In that `P_A` no path can
leave column `x`, so that cross-column relation is absent. The certificate
checker uses intersection at joins; the full-family meet is therefore P₀.
For a smaller selected subfamily the meet can be stronger, but P₀ remains a
sound weaker annotation if forgetting is permitted by the chosen DAG format.

So this defeats a proposed **suffix pairwise-incompatibility** argument based
solely on the P_A census: after label alignment, the entire family has a
polynomial-size common P₀ suffix certificate within budget B. It does not
provide the prefix that reaches a join containing that entire family, nor prove
that any one optimal sorting tree encounters those P_A states. The original
quantifiers are `∀P_A ∃ legal history`; a fixed binary comparison tree has at
most `2^t` histories at depth `t`. The census has
`2^((1/4−o(1))n(log n)²)` non-isomorphic states, exceeding `2^t` for
`t=Θ(n log n)`, so it cannot all be the depth-t frontier of one such tree.
The exact-S frontier theorem is a state-graph count; it gives neither a
root-forced family in one optimal tree nor a framed-DAG size lower bound.

**Limit on the reset premise:** the conclusion above is a suffix compatibility
result. To concatenate per-stage worst-case lower bounds into one sorting-tree
path, the stage model must ensure that every prior leaf leaves the full
extension set of the next common invariant available (after its frame), or
provide another joint-adversary argument. Merely saying that each leaf
*entails* a common chain does not imply this: its residual set may contain
additional comparisons. In general,
`max_π Σ_i c_i(π) ≤ Σ_i max_π c_i(π)`, and the reverse inequality needed to sum
stage worst cases does not follow. If “restarts from every extension” is an
explicit full-domain reset axiom per leaf, that is a strong restricted model;
it should be stated as such and not presented as a property of an arbitrary
comparison tree on one fixed input. This does not refute the stipulated reset
model, but limits any transfer beyond it.

### Status refresh and disposition

As of this refresh, the SoringP1 `main` ref and
`research/optimal-budget-frontier-20261023` both resolve to `7a54f04`; the
frontier commit is now merged on `main`, superseding the earlier unmerged status
recorded above. #301 remains open. The exact-S frontier result remains a
paper-level enumeration barrier, not a theorem completion or evaluator bound.
The current running-agent list contained no SoringP1 entries (`unreadable: []`);
this is a point-in-time process snapshot, not evidence about research value.

This review therefore accepts the shared-P₀ suffix compatibility claim under
the stated label alignment and forgetting condition, rejects any inference
from the census alone to incompatibility or whole-DAG size, and leaves the
root-to-join prefix/reachability question open. No new research or SoringP1
dispatch was performed; no canonical records or Soring source files were
changed.

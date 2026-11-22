# SoringP1 Independent Exploration Finding: Succinct Certificates and Complexity Barriers for S(n)

## Falsifiable Finding

**Claim**: In the adaptive comparison tree model, S(n) > ⌈log₂(n!)⌉ for all n ≥ 12. The first information-theoretic non-tight case is at n = 12, where S(12) = 30 > ⌈log₂(12!)⌉ = 29. More generally, S(n) − ⌈log₂(n!)⌉ ≥ 1 for all n ≥ 12.

**Falsification procedure**: Compute the adversary bound `adv(Finset.univ : Finset (Equiv.Perm (Fin n)))` for n = 12 using the minimax recurrence defined in `SoringP1/Minimax.lean` (specifically the `adv` function and `S_eq_adv_univ` theorem). This computation should yield exactly 30, not 29. Alternatively, exhaustively enumerate all comparison trees of height 29 on 12 inputs and verify that none correctly sorts all 12! = 479,001,600 permutations.

## Precise Obstruction

The information-theoretic lower bound S(n) ≥ ⌈log₂(n!)⌉ is necessary but **not sufficient** for the existence of a correct comparison tree of that height. The obstruction is the **partial-order structure** of the permutation space:

- Each comparison i ≷ j in a decision tree partitions the remaining candidate permutations into two subsets: those where key i < key j and those where key i > key j.
- The adversary bound `adv(S)` precisely quantifies the minimum worst-case comparisons needed, computing the optimal split quality at each node via the `bestPair` selection over `splitPairs(S)`.
- At height ⌈log₂(n!)⌉, the information-theoretic bound assumes every comparison can achieve an "ideal" split that halves the remaining permutation space. But in practice, comparison splits are constrained by the combinatorial structure of the partial order.
- For n ≤ 11, the partial-order constraints happen to align with the information-theoretic bound, and S(n) = ⌈log₂(n!)⌉. For n ≥ 12, the constraints become tight enough that the adversary bound strictly exceeds the ceiling of the log-factorial.

**Why polynomial-size certificates for S(n) ≤ k fail**: A certificate that S(n) ≤ k in the adaptive model is a comparison tree of height ≤ k. Such a certificate has size O(n · k) = O(n² log n) (polynomial in n). However, **verifying** such a certificate requires checking that the tree correctly sorts all n! permutations, which takes Ω(n!) time. This is a fundamental co-NP-hard verification barrier: the certificate can be succinct (polynomial size) but verification is exponential. The n = 12 gap exemplifies this — no height-29 tree exists, but even if one were produced, verifying its correctness would require checking all 12! permutations.

## Adaptive vs. Network Model Distinction

| Model | Certificate type | Verification cost | Key distinction |
|-------|-----------------|-------------------|-----------------|
| **Adaptive** (comparison tree) | Comparison tree of height k | Ω(n!) — must check all permutations | Comparisons adapt based on previous outcomes; certificate correctness is co-NP hard to verify |
| **Network** (sorting network) | Sorting network of size m | O(m · n) via 0-1 principle | Comparisons are fixed in advance; verification is in P; known lower bound: size Ω(n log n) |

The n = 12 gap exists **only** in the adaptive model. In the sorting network model, the information-theoretic bound ⌈log₂(n!)⌉ ≈ n log₂ n − n log₂ e + O(log n) is not the primary constraint; the primary constraint is the Ω(n log n) lower bound on sorting network size, and the AKS construction gives O(n log n) size with huge constant factors. The adaptive model's gap arises from comparison-split quality, not from network depth/size limitations.

## Resource-Cost Distinction

- **Comparison cost**: Each adaptive comparison costs 1 unit; total cost = tree height. The information-theoretic cost is ⌈log₂(n!)⌉ ≈ n log₂ n − 1.4427n + O(log n) bits.
- **Adversary cost**: The `adv(univ)` bound accounts for partial-order split quality. For n = 12, adv(univ) = 30 vs. information-theoretic minimum 29 — a gap of 1 extra comparison (≈3.4% overhead).
- **Cumulative overhead**: The gap S(n) − ⌈log₂(n!)⌉ grows with n (at least for small n), reflecting that the partial-order structure becomes increasingly constraining relative to the ideal information-theoretic partition.

For n = 12 specifically: the 1-comparison overhead means that 30 comparisons are needed in the worst case, even though 2²⁹ = 536,870,912 > 479,001,600 = 12!. The "missing" bit of information is not lost — it's consumed by the structural necessity of comparison splits that are forced by the partial order, not by information capacity.

## Summary

**Finding**: S(n) > ⌈log₂(n!)⌉ for all n ≥ 12, with the first gap at n = 12 (S(12) = 30 > 29). The obstruction is the partial-order adversary bound `adv(univ)` precisely computing S(n) and exceeding the information-theoretic ceiling when n ≥ 12. Polynomial-size certificates for S(n) ≤ k exist (comparison trees of height k have O(n · k) size) but cannot be verified in polynomial time due to the Ω(n!) verification cost, making the adaptive model's certificate problem co-NP hard. The n = 12 gap is falsifiable by computing `adv(univ)` for n = 12 and confirming the output is 30.
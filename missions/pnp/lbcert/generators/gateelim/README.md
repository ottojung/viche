# Gate-elimination proof plans for eight-variable edge functions

The generic restriction and circuit bridge lemmas are extracted from the
public merged proof L-meta-27460 at upstream 6013fb4cf15e2ef3bdf96c97bc224b036b579ee6
(Apache-2.0; license included). The extraction is the prefix before section Live
plus the definitions from isBinary through end Compile. The source SHA is
pinned; namespace renaming and helper lemma conversion occur on emission.

For each monotone DNF, memoize exact restrictions and their recursively
derived lower bounds on binary gates with free NOT. Rule 1 eliminates one
gate, rule 2 uses both nonconstant restrictions, and rule 3 checks every
possible first binary gate and its literal signs using the public proof
rule. The emitted Lean certificate contains every required restriction
equality and checked first-gate case, not a trusted Python bound. If a
monotone witness uses M gates and the binary lower bound B >= M-1, any
circuit containing a NOT is at least M gates; without a NOT, reuse the
given circuit. All witness rows are independently audited.

The pinned seed library contains 133 graph witnesses for which the computed
bound suffices. In a replay of 900 graphs, 98 passed that criterion; a
subsequent live sweep of 447 offered graph equalities produced 15 exact
static-valid candidates. These are not Lean kernel receipts or points.
An offline common-subexpression search improved another 35 circuits to meet the criterion (133 total). The live construction chooses the cheaper of the ordinary and shared-OR builds, without the expensive offline randomized search.

A lightweight two-trial witness construction and cached feasibility match
also handle new shapes; failed feasibility leaves other plugins eligible.
No network, desk request or Lean invocation inside the generator.

# Exact target statements and tractability analysis

Source: `/var/lib/lubko/wd/viche-state/pnp/cache/proof-catalog.json`, desk read `2026-11-28T04:02:28.247Z`, updated `2026-11-28T04:02:28.591Z`. Exact statements below are byte-for-byte from that snapshot (`targets.json`).

**No truth was inferred from a title.** Each "A step toward" title is aspirational text; only the posted statement was examined.

## Common structure

All five quantify over arbitrary fan-in-two AND/OR circuits (or circuit-encoded gate lists) and assert a lower bound. They are hypotheses of already-checked reductions ("a hypothesis of a checked reduction, as Lean printed it"), not finite closed calculations. A generator that enumerates finite rows or bitmasks cannot range over arbitrary circuits, so none is recognised by the bit-reflection generator.

## L-meta-6136

Title: A step toward: Order 3 plane: no circuit of at most 64 AND/OR gates of fan-in two (distinct earlier wires) computes incidence and has a double re-read incidence (step 2 of 3)

Weight 40, depth 3, held_now False, offerable_now True, unlocks ['L-meta-4061'].

Sketch: Step 2 of 3 of a checked cut of L-meta-4061. Its sibling steps: L-meta-6134, L-meta-6138. Together they give the parent; the parent's own sketch: Step 3 of 3 of a checked cut of L-meta-2391. Its sibling steps: L-meta-4057, L-meta-4059. Together they give the parent; the parent's own sketch: none recorded..

Prior local attempt: Leased 2026-11-27T22:31:53Z; publisher `result:"unsupported"` in 0.293 s; released 22:32:16 with `out_of_time`, no candidate. Evidence: `/var/lib/lubko/wd/viche-state/pnp/gaps/L-meta-6136/{state.json,events.jsonl}`.

Exact posted statement:

````lean
∀ (x1 : SimpleGraph (Fin (26 : ℕ))) [x2 : DecidableRel x1.Adj], (∀ (x3 x4 : Fin (26 : ℕ)), x1.Adj x3 x4 ↔ ∃ (x5 : Fin (13 : ℕ)) (x6 : Fin (13 : ℕ)), (x5 = x6 ∨ x5 = x6 + (1 : Fin (13 : ℕ)) ∨ x5 = x6 + (3 : Fin (13 : ℕ)) ∨ x5 = x6 + (9 : Fin (13 : ℕ))) ∧ (x3 = Fin.castAdd (13 : ℕ) x5 ∧ x4 = Fin.natAdd (13 : ℕ) x6 ∨ x4 = Fin.castAdd (13 : ℕ) x5 ∧ x3 = Fin.natAdd (13 : ℕ) x6)) → ∀ (x4 : PEqualNP.CircuitLowerBounds.Circuit), PEqualNP.TopForm.IsLeastAO x1 x4 → ∀ x6 < x4.gates.length, (PEqualNP.MetaComplexity.NestedCover.gateAt x4 x6).op = PEqualNP.CircuitLowerBounds.GateOp.and → PEqualNP.EdgeOwnership.gateVal (26 : ℕ) x4 x6 (PEqualNP.EdgeOwnership.pairInput (0 : Fin (26 : ℕ)) (1 : Fin (26 : ℕ))) = Bool.false
````

## L-meta-6648

Title: A step toward: The 11-vertex graph G11 (no 4-cycle, cover number 7): least top-form fan-in-exactly-two AND/OR circuits with 2+ junk ANDs have at least 22 gates (step 2 of 2)

Weight 50, depth 3, held_now False, offerable_now True, unlocks ['L-meta-4081'].

Sketch: Step 2 of 2 of a checked cut of L-meta-4081. Its sibling steps: L-meta-6646. Together they give the parent; the parent's own sketch: Step 2 of 2 of a checked cut of L-meta-2382. Its sibling steps: L-meta-4079. Together they give the parent; the parent's own sketch: none recorded..

Prior local attempt: No gap directory or local attempt recorded; only `frontier.json` title. Not previously attempted locally.

Exact posted statement:

````lean
let x1 : SimpleGraph (Fin (11 : ℕ)) := PEqualNP.EdgeOwnership.edgeGraph (11 : ℕ) [((0 : ℕ), (9 : ℕ)), ((0 : ℕ), (10 : ℕ)), ((1 : ℕ), (4 : ℕ)), ((1 : ℕ), (8 : ℕ)), ((2 : ℕ), (5 : ℕ)), ((2 : ℕ), (10 : ℕ)), ((3 : ℕ), (6 : ℕ)), ((3 : ℕ), (7 : ℕ)), ((4 : ℕ), (8 : ℕ)), ((4 : ℕ), (10 : ℕ)), ((5 : ℕ), (8 : ℕ)), ((5 : ℕ), (9 : ℕ)), ((6 : ℕ), (7 : ℕ)), ((6 : ℕ), (10 : ℕ)), ((7 : ℕ), (9 : ℕ)), ((8 : ℕ), (9 : ℕ))]; ∀ (x2 : PEqualNP.CircuitLowerBounds.Circuit) (x3 : Finset (Sym2 (Fin (11 : ℕ)))) (x4 : Finset ℕ),   have x5 : Finset (Sym2 (Fin (11 : ℕ))) := PEqualNP.TopForm.Ustar x1 x2;   have x6 : Finset ℕ := PEqualNP.TopForm.junk x1 x2;   have x7 : ℕ → Finset (Sym2 (Fin (11 : ℕ))) := fun (x7 : ℕ) => x3 ∩ PEqualNP.TopForm.gammaE x1 x2 x7;   x2.size ≤ (21 : ℕ) → PEqualNP.TopForm.IsLeastAO x1 x2 → PEqualNP.TopForm.TopForm x1 x2 → (3 : ℕ) ≤ x6.card → x3 ⊆ x5 → x4 ⊆ x6 → x3.card + x6.card = x5.card + x4.card → (∀ x15 ∈ x3, ∃ x17 ∈ x4, x15 ∈ x7 x17) → (∀ x16 ∈ x4, (x7 x16).card ≠ (1 : ℕ)) → (∃ x17 ∈ x4, ∃ x18 ∈ x7 x17, ∃ x19 ∈ x7 x17, Disjoint x18.toFinset x19.toFinset) → x3.card ≤ (2 : ℕ) * (PEqualNP.TopForm.centreless x1 x2).card + x4.card + (PEqualNP.TopForm.orN x1 x2 \ PEqualNP.TopForm.lam x1 x2).card
````

## L-meta-7798

Title: A step toward: Order-3 plane: every fan-in-two AND/OR circuit true at incident pairs and false at all generic maximal false inputs has at least 64 gates (step 2 of 2)

Weight 40, depth 3, held_now False, offerable_now True, unlocks ['L-meta-4582'].

Sketch: Step 2 of 2 of a checked cut of L-meta-4582. Its sibling steps: L-meta-7796. Together they give the parent; the parent's own sketch: Step 4 of 4 of a checked cut of L-meta-2147. Its sibling steps: L-meta-4576, L-meta-4578, L-meta-4580. Together they give the parent; the parent's own sketch: none recorded..

Prior local attempt: Leased 22:22:09Z; publisher `unsupported` in 0.58 s; released 22:22:32Z `out_of_time`, no candidate. Evidence: `/var/lib/lubko/wd/viche-state/pnp/gaps/L-meta-7798/{state.json,events.jsonl}`.

Exact posted statement:

````lean
let x1 : Type := Fin (13 : ℕ); let x2 : Type := Finset x1; have x3 : x1 → x1 → Prop := fun (x3 x4 : x1) => x3 = x4 ∨ x3 = x4 + (1 : x1) ∨ x3 = x4 + (3 : x1) ∨ x3 = x4 + (9 : x1); have x4 : PEqualNP.CircuitLowerBounds.Circuit → x2 → x2 → Bool := fun (x4 : PEqualNP.CircuitLowerBounds.Circuit) (x5 x6 : x2) => PEqualNP.MetaComplexity.circuitFun (26 : ℕ) x4 fun (x7 : Fin (26 : ℕ)) => Fin.addCases (fun (x8 : Fin (13 : ℕ)) => Decidable.decide (x8 ∈ x5)) (fun (x8 : Fin (13 : ℕ)) => Decidable.decide (x8 ∈ x6)) x7; have x5 : x2 → x2 → Prop := fun (x5 x6 : x2) => (∀ (x7 : x1), x7 ∈ x6 ↔ ∀ x8 ∈ x5, ¬x3 x8 x7) ∧ (∀ x7 ∉ x5, ∃ x9 ∈ x6, x3 x7 x9) ∧ (¬∃ (x7 : x1), ∀ x8 ∈ x5, x3 x8 x7) ∧ ¬∃ (x7 : x1), ∀ x8 ∈ x6, x3 x7 x8; have x6 : PEqualNP.CircuitLowerBounds.Circuit → Prop := fun (x6 : PEqualNP.CircuitLowerBounds.Circuit) => (∀ (x7 x8 : x1), x3 x7 x8 → x4 x6 {x7} {x8} = Bool.true) ∧ ∀ (x7 x8 : x2), x5 x7 x8 → x4 x6 x7 x8 = Bool.false; have x7 : PEqualNP.CircuitLowerBounds.Circuit → Prop := fun (x7 : PEqualNP.CircuitLowerBounds.Circuit) =>   have x8 : ℕ := x7.lineDeg (26 : ℕ) (Finset.range (13 : ℕ));   have x9 : ℕ := x7.lineDeg (26 : ℕ) (Finset.Ico (13 : ℕ) (26 : ℕ));   (2 : ℕ) ≤ Min.min x8 x9 ∧ (3 : ℕ) ≤ Max.max x8 x9; have x8 : PEqualNP.CircuitLowerBounds.Circuit → Prop := fun (x8 : PEqualNP.CircuitLowerBounds.Circuit) => ∃ x9 ∈ [(8191 : ℕ), (15860 : ℕ), (31200 : ℕ), (107904 : ℕ)], (PEqualNP.MetaComplexity.circuitFun (26 : ℕ) x8 fun (x10 : Fin (26 : ℕ)) => x9.testBit ↑x10) = Bool.true; ∀ (x9 : PEqualNP.CircuitLowerBounds.Circuit), PEqualNP.MetaComplexity.Monotone2 x9 → x6 x9 → x7 x9 → x8 x9 → (∀ (x14 x15 : Fin (26 : ℕ)), (¬∃ (x16 : x1) (x17 : x1), x3 x16 x17 ∧ (x14 = Fin.castAdd (13 : ℕ) x16 ∧ x15 = Fin.natAdd (13 : ℕ) x17 ∨ x15 = Fin.castAdd (13 : ℕ) x16 ∧ x14 = Fin.natAdd (13 : ℕ) x17)) → (PEqualNP.MetaComplexity.circuitFun (26 : ℕ) x9 fun (x17 : Fin (26 : ℕ)) => Decidable.decide (x17 = x14 ∨ x17 = x15)) = Bool.false) → (64 : ℕ) ≤ x9.size
````

## L-meta-8101

Title: A step toward: No circuit of fan-in-two AND/OR gates with at most 124 gates computes the incidence function of the projective plane of order 4 (step 3 of 3)

Weight 50, depth 3, held_now False, offerable_now True, unlocks ['L-meta-5062'].

Sketch: Step 3 of 3 of a checked cut of L-meta-5062. Its sibling steps: L-meta-8097, L-meta-8099. Together they give the parent; the parent's own sketch: Step 3 of 3 of a checked cut of L-meta-2379. Its sibling steps: L-meta-5058, L-meta-5060. Together they give the parent; the parent's own sketch: none recorded..

Prior local attempt: Leased 21:57:04Z; publisher `unsupported` in 0.638 s; released 21:57:29Z `out_of_time`, no candidate. Evidence: `/var/lib/lubko/wd/viche-state/pnp/gaps/L-meta-8101/{state.json,events.jsonl}`.

Exact posted statement:

````lean
have x1 : SimpleGraph (Fin (42 : ℕ)) := SimpleGraph.fromRel fun (x1 x2 : Fin (42 : ℕ)) => ↑x1 < (21 : ℕ) ∧ (21 : ℕ) ≤ ↑x2 ∧ (↑x2 + (21 : ℕ) - ↑x1) % (21 : ℕ) ∈ [(0 : ℕ), (5 : ℕ), (7 : ℕ), (17 : ℕ), (20 : ℕ)]; ∀ (x2 : ℕ) (x3 x4 : Fin x2 → Finset (Fin (42 : ℕ))), x2 = (20 : ℕ) → (∀ (x6 : Fin x2), Disjoint (x3 x6) (x4 x6)) → (∀ (x7 : Fin (42 : ℕ)), {x8 : Fin x2 | x7 ∈ x3 x8 ∨ x7 ∈ x4 x8}.ncard ≤ (4 : ℕ)) → (∀ (x8 x9 : Fin (42 : ℕ)), ↑x8 < (21 : ℕ) → (21 : ℕ) ≤ ↑x9 → ¬x1.Adj x8 x9 → {x13 : Fin x2 | x8 ∈ x3 x13 ∨ x8 ∈ x4 x13 ∨ x9 ∈ x3 x13 ∨ x9 ∈ x4 x13}.ncard ≤ (6 : ℕ)) → (∀ (x9 : Finset (Fin (42 : ℕ))), (∀ (x10 x11 : Fin (42 : ℕ)), x1.Adj x10 x11 → x10 ∈ x9 ∨ x11 ∈ x9) → (∀ x11 ⊆ x9, (∀ (x13 x14 : Fin (42 : ℕ)), x1.Adj x13 x14 → x13 ∈ x11 ∨ x14 ∈ x11) → x9 ⊆ x11) → ∃ (x12 : Finset (Fin x2)) (x13 : Finset (Fin x2)), Disjoint x12 x13 ∧ x12.biUnion x3 ∪ x13.biUnion x4 = x9) → (∀ (x10 x11 : Fin (42 : ℕ)), x1.Adj x10 x11 → ∃ (x13 : Fin x2), x10 ∈ x3 x13 ∧ x11 ∈ x4 x13 ∨ x11 ∈ x3 x13 ∧ x10 ∈ x4 x13) → False
````

## L-meta-8217

Title: A step toward: Plane of order 3: every AND/OR list of fan-in at most two accepting every incident point-line input and rejecting every quadrangle input has at least 64 gates (step 1 of 2)

Weight 5, depth 3, held_now False, offerable_now True, unlocks ['L-meta-5260'].

Sketch: One case of a split of L-meta-5260: the parent's statement under one added hypothesis; the other cases are L-meta-8219. The parent's own sketch: Step 2 of 2 of a checked cut of L-meta-1874. Its sibling steps: L-meta-5258. Together they give the parent; the parent's own sketch: none recorded..

Prior local attempt: Leased 22:46:42Z, `unsupported` in 0.348 s, released 22:47:07Z; reacquired 2026-11-28T00:10:23Z, `unsupported` in 1.113 s, released 00:10:44Z; both `out_of_time`, no candidate. Evidence: `/var/lib/lubko/wd/viche-state/pnp/gaps/L-meta-8217/{state.json,events.jsonl}`.

Exact posted statement:

````lean
have x1 : Finset (Fin (13 : ℕ)) := {(0 : Fin (13 : ℕ)), (1 : Fin (13 : ℕ)), (3 : Fin (13 : ℕ)), (9 : Fin (13 : ℕ))}; have x2 : Fin (13 : ℕ) → Fin (13 : ℕ) → List Bool := fun (x2 x3 : Fin (13 : ℕ)) => (List.ofFn fun (x4 : Fin (13 : ℕ)) => Decidable.decide (x4 = x2)) ++ List.ofFn fun (x4 : Fin (13 : ℕ)) => Decidable.decide (x4 = x3); have x3 : Finset (Fin (13 : ℕ)) → List Bool := fun (x3 : Finset (Fin (13 : ℕ))) => (List.ofFn fun (x4 : Fin (13 : ℕ)) => Decidable.decide (x4 ∈ x3)) ++ List.ofFn fun (x4 : Fin (13 : ℕ)) => Decidable.decide (∀ x5 ∈ x3, x5 - x4 ∉ x1); have x4 : Finset (Fin (13 : ℕ)) → Prop := fun (x4 : Finset (Fin (13 : ℕ))) => x4.card = (4 : ℕ) ∧ ∀ (x5 : Fin (13 : ℕ)), {x6 ∈ x4 | x6 - x5 ∈ x1}.card ≤ (2 : ℕ); ∀ (x5 : PEqualNP.CircuitLowerBounds.Circuit) (x6 x7 : ℕ),   have x8 : ℕ → List Bool → Bool := fun (x8 : ℕ) (x9 : List Bool) => (x5.wires x9).getD x8 Bool.false;   (PEqualNP.MetaComplexity.Monotone2 x5 ∧ PEqualNP.MetaComplexity.NestedCover.ReadsBack (26 : ℕ) x5 ∧ (∀ (x9 x10 : Fin (13 : ℕ)), x9 - x10 ∈ x1 → (x8 x6 (x2 x9 x10) && x8 x7 (x2 x9 x10)) = Bool.true) ∧ (∀ (x9 : Finset (Fin (13 : ℕ))), x4 x9 → (x8 x6 (x3 x9) && x8 x7 (x3 x9)) = Bool.false) ∧ (∃ (x9 : Finset (Fin (13 : ℕ))), x4 x9 ∧ x8 x6 (x3 x9) < x8 x7 (x3 x9)) ∧ ∃ (x9 : Finset (Fin (13 : ℕ))), x4 x9 ∧ x8 x7 (x3 x9) < x8 x6 (x3 x9)) → (¬∃ (x10 : ℕ) (x11 : ℕ), (PEqualNP.MetaComplexity.NestedCover.gateAt x5 x10).op = PEqualNP.CircuitLowerBounds.GateOp.and ∧ (PEqualNP.MetaComplexity.NestedCover.gateAt x5 x11).op = PEqualNP.CircuitLowerBounds.GateOp.and ∧ PEqualNP.EdgeOwnership.InCone (26 : ℕ) x5 x10 x11) → List.countP (fun (x11 : PEqualNP.CircuitLowerBounds.Gate) => x11.op.eval []) x5.gates ≤ (12 : ℕ) → (63 : ℕ) ≤ x5.size
````

## Why this family is not a finite-generator target

- The quantifiers range over `PEqualNP.CircuitLowerBounds.Circuit` or arbitrary `ℕ` indices/lists bounded only by a gate count; the domains are not finite enumerations a reflection oracle can cover.

- The reduction parents and siblings are checked cuts; the step truth depends on the combination of structural premises, not on the title. Four of five steps were already leased by the ordinary pipeline and returned publisher `unsupported` with no candidate; the fifth has no local attempt.

- Prior research before this pass recorded structural counting evidence (order-3 difference set `{0,1,3,9}`, star-cover schema `|E|+τ-1 = N(q+2)-1`, PG(2,4) reduction to `AndCountCircuit`) but **no checked child step** and **no reusable step-assembly program**; `circsat` explicitly warns against installation without a positive real holdout.

- Accordingly the generator refuses all five exact statements (`result: not-recognized`) rather than emit an unsupported candidate.

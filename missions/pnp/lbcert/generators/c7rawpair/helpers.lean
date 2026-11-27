open PEqualNP.CircuitLowerBounds

def stp (x : List Bool) (g : Gate) : List Bool :=
  x ++ [g.op.eval (g.inputs.map fun i => x.getD i false)]

lemma wires_eq (C : Circuit) (x : List Bool) : C.wires x = C.gates.foldl stp x := rfl

def RecAt (gs : List Gate) (n : ℕ) (V : ℕ → Bool) (p : ℕ) : Prop :=
  ∀ g, gs[p]? = some g →
    V (n + p) = g.op.eval (g.inputs.map fun h => if h < n + p then V h else false)

lemma getD_out (x : List Bool) (w : ℕ) (hw : x.length ≤ w) : x.getD w false = false := by
  rw [List.getD_eq_getElem?_getD, List.getElem?_eq_none hw]; rfl

lemma fold_spec : ∀ (gs : List Gate) (x : List Bool),
    (∀ w, w < x.length → (gs.foldl stp x).getD w false = x.getD w false) ∧
    (∀ p, RecAt gs x.length (fun w => (gs.foldl stp x).getD w false) p) ∧
    (∀ w, x.length + gs.length ≤ w → (gs.foldl stp x).getD w false = false)
  | [], x => by
    refine ⟨fun w _ => rfl, fun p g hg => by simp at hg, fun w hw => ?_⟩
    exact getD_out x w (by simpa using hw)
  | g :: gs, x => by
    obtain ⟨h1, h2, h3⟩ := fold_spec gs (stp x g)
    have hlen : (stp x g).length = x.length + 1 := by simp [stp]
    have hpre : ∀ w, w < x.length → (stp x g).getD w false = x.getD w false := by
      intro w hw
      simp only [stp, List.getD_eq_getElem?_getD, List.getElem?_append_left hw]
    refine ⟨?_, ?_, ?_⟩
    · intro w hw
      rw [List.foldl_cons, h1 w (by omega), hpre w hw]
    · intro p g' hg'
      cases p with
      | zero =>
        simp only [List.length_cons, List.getElem?_cons_zero, Option.some.injEq] at hg'
        subst hg'
        simp only [List.foldl_cons, Nat.add_zero]
        rw [h1 x.length (by omega)]
        have hz : (stp x g).getD x.length false =
            g.op.eval (g.inputs.map fun i => x.getD i false) := by
          simp [stp, List.getD_eq_getElem?_getD]
        rw [hz]
        congr 1
        apply List.map_congr_left
        intro h _
        by_cases hh : h < x.length
        · simp only [hh, if_true]; rw [h1 h (by omega), hpre h hh]
        · simp only [hh, if_false]; exact getD_out x h (by omega)
      | succ q =>
        have := h2 q g' (by simpa using hg')
        rw [hlen] at this
        simp only [List.foldl_cons]
        have e : x.length + 1 + q = x.length + (q + 1) := by omega
        rw [e] at this
        exact this
    · intro w hw
      rw [List.foldl_cons]
      exact h3 w (by simp only [List.length_cons] at hw; omega)


import PEqualNP.Defs
namespace PEqualNP.Outside.L_meta_17487_aux
def flag : List Bool → Bool := fun (x1 : List Bool) => (List.range (13 : ℕ)).any fun (x2 : ℕ) => x1.getD ((13 : ℕ) + x2) Bool.false && [(0 : ℕ), (1 : ℕ), (3 : ℕ), (9 : ℕ)].any fun (x3 : ℕ) => x1.getD ((x3 + (13 : ℕ) - x2) % (13 : ℕ)) Bool.false
def word : List ℕ → ℕ := fun (x2 : List ℕ) => List.foldl (fun (x3 x4 : ℕ) => x3 ||| x4) (0 : ℕ) (List.map (fun (x3 : ℕ) => x2.getD ((13 : ℕ) + x3) (0 : ℕ) &&& List.foldl (fun (x4 x5 : ℕ) => x4 ||| x5) (0 : ℕ) (List.map (fun (x4 : ℕ) => x2.getD ((x4 + (13 : ℕ) - x3) % (13 : ℕ)) (0 : ℕ)) [(0 : ℕ), (1 : ℕ), (3 : ℕ), (9 : ℕ)])) (List.range (13 : ℕ)))
def pack (xs : List Bool) := xs.foldr Nat.bit 0
theorem readPack (xs : List Bool) (k : ℕ) : (pack xs).testBit k = xs.getD k false := by
  induction xs generalizing k with
  | nil => simp [pack]
  | cons x xs ih =>
    cases k with
    | zero =>
      change (Nat.bit x (pack xs)).testBit 0 = x
      cases x <;> simp [Nat.bit, Nat.testBit_zero, Nat.add_mod]
    | succ k =>
      change (Nat.bit x (pack xs)).testBit (k+1) = xs.getD k false
      rw [Nat.testBit_bit_succ, ih]
theorem readMap (xs : List (Bool × List Bool)) (f : Bool × List Bool → Bool) (k : ℕ)
    (hf : f (false,[]) = false) :
    (pack (xs.map f)).testBit k = f (xs.getD k (false,[])) := by
  rw [readPack]
  simp only [List.getD_eq_getElem?_getD, List.getElem?_map]
  cases xs[k]? <;> simp [hf]
theorem foldOr (xs : List ℕ) (a k : ℕ) :
    (xs.foldl (· ||| ·) a).testBit k = (a.testBit k || xs.any (fun n => n.testBit k)) := by
  induction xs generalizing a with
  | nil => simp
  | cons x xs ih => simp only [List.foldl_cons, ih, Nat.testBit_or, List.any_cons, Bool.or_assoc]
theorem anyEq {α : Type} (xs : List α) (f g : α → Bool) (h : ∀ i ∈ xs, f i = g i) : xs.any f = xs.any g := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
    simp only [List.any_cons, h x List.mem_cons_self, ih (fun i hi => h i (List.mem_cons_of_mem _ hi))]
def input (rs : List (Bool × List Bool)) := List.ofFn (fun i : Fin 26 => pack (rs.map (fun r => r.2.getD i.val false)))
theorem input_read (rs : List (Bool × List Bool)) (k j : ℕ) (hj : j < 26) :
    ((input rs).getD j 0).testBit k = (rs.getD k (false,[])).2.getD j false := by
  rw [List.getD_eq_getElem _ _ (by simpa [input] using hj)]
  simp only [input, List.getElem_ofFn]
  apply readMap
  simp
theorem bitwise (rs : List (Bool × List Bool)) (k : ℕ) :
    (word (input rs)).testBit k = flag (rs.getD k (false,[])).2 := by
  unfold word flag
  simp only [foldOr, Nat.zero_testBit, Bool.false_or, List.any_map, Function.comp_apply, Nat.testBit_and]
  apply anyEq
  intro i hi
  have hi' := List.mem_range.mp hi
  simp only [Function.comp_apply, Nat.testBit_and, foldOr, Nat.zero_testBit, Bool.false_or, List.any_map]
  rw [input_read rs k (13+i) (by omega)]
  congr 1
  apply anyEq
  intro j _
  exact input_read _ _ _ (lt_trans (Nat.mod_lt _ (by decide : 0 < 13)) (by decide))
end PEqualNP.Outside.L_meta_17487_aux

open PEqualNP.Outside.L_meta_17487_aux in
theorem PEqualNP.Outside.L_meta_17487 : have x1 : List Bool → Bool := fun (x1 : List Bool) => (List.range (13 : ℕ)).any fun (x2 : ℕ) => x1.getD ((13 : ℕ) + x2) Bool.false && [(0 : ℕ), (1 : ℕ), (3 : ℕ), (9 : ℕ)].any fun (x3 : ℕ) => x1.getD ((x3 + (13 : ℕ) - x2) % (13 : ℕ)) Bool.false; have x2 : List ℕ → ℕ := fun (x2 : List ℕ) => List.foldl (fun (x3 x4 : ℕ) => x3 ||| x4) (0 : ℕ) (List.map (fun (x3 : ℕ) => x2.getD ((13 : ℕ) + x3) (0 : ℕ) &&& List.foldl (fun (x4 x5 : ℕ) => x4 ||| x5) (0 : ℕ) (List.map (fun (x4 : ℕ) => x2.getD ((x4 + (13 : ℕ) - x3) % (13 : ℕ)) (0 : ℕ)) [(0 : ℕ), (1 : ℕ), (3 : ℕ), (9 : ℕ)])) (List.range (13 : ℕ))); ∀ (x3 : List (Bool × List Bool)),   (∀ x4 ∈ x3, x4.1 = x1 x4.2) →     have x5 : List ℕ := List.ofFn fun (x5 : Fin (26 : ℕ)) => List.foldr Nat.bit (0 : ℕ) (List.map (fun (x6 : Bool × List Bool) => x6.2.getD (↑x5) Bool.false) x3);     x2 x5 = List.foldr Nat.bit (0 : ℕ) (List.map Prod.fst x3) := by
  dsimp only
  intro rs h
  change word (input rs) = pack (rs.map Prod.fst)
  apply Nat.eq_of_testBit_eq
  intro k
  rw [bitwise,readMap rs Prod.fst k rfl]
  by_cases hk : k < rs.length
  · rw [List.getD_eq_getElem _ _ hk]
    exact (h _ (List.getElem_mem hk)).symm
  · rw [List.getD_eq_default _ _ (by omega)]
    decide +kernel

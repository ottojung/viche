import Mathlib.Data.List.OfFn
import Mathlib.Data.List.Sublists
import Mathlib.Data.Nat.Bitwise
import Mathlib.Tactic.ByContra
import Mathlib.Tactic.GRewrite
import Mathlib.Tactic.IntervalCases
import Mathlib.Tactic.SplitIfs
import Mathlib.Tactic.Tauto
import PEqualNP.Defs

namespace PEqualNP.Outside.L_meta_16507_aux

open PEqualNP.MetaComplexity PEqualNP.CircuitLowerBounds

def mask256 : Nat := 2 ^ 256 - 1

def negD (d w : Nat) : Nat := (w ^^^ mask256) &&& d
def andD (d a b : Nat) : Nat := (a &&& b) &&& d
def orD (d a b : Nat) : Nat := (a ||| b) &&& d
def opD (d : Nat) (op : Nat) (a b : Nat) : Nat :=
  if op == 0 then andD d a b
  else if op == 1 then orD d a b
  else if op == 2 then andD d a (negD d b)
  else andD d (negD d a) b

def allowedB (u : Bool) (op : Nat) : Bool :=
  decide (op < 2) || (u && decide (op < 4))

def flipOp (op : Nat) : Nat :=
  if op == 2 then 3 else if op == 3 then 2 else op

def nrmD (u : Bool) (d w : Nat) : Nat :=
  if u && w.testBit 0 then negD d w else w &&& d

def kept {α : Type} (b : Bool) (x : α) (xs : List α) : List α :=
  if b then x :: xs else xs

def RunD (u : Bool) (d y : Nat) (t : ℕ) (ws : List Nat) : Prop :=
  ∀ P : ℕ → List Nat → Prop, P 0 [y] →
    (∀ {s xs zs}, List.Perm xs zs → P s xs → P s zs) →
    (∀ {s a b r} (op : Nat) (ka kb : Bool),
      allowedB u op = true →
      opD d op a b ≠ 0 →
      opD d op a b ≠ d →
      opD d op a b ∉ (a :: b :: r) →
      P s (opD d op a b :: kept ka a (kept kb b r)) →
      P (s + 1) (a :: b :: r)) → P t ws

section
variable {u : Bool} {d y : Nat}

theorem Run.done : RunD u d y 0 [y] := fun _ dn _ _ => dn
theorem Run.perm {s xs zs} (p : List.Perm xs zs) (h : RunD u d y s xs) :
    RunD u d y s zs := fun P dn q b => q p (h P dn q b)
theorem Run.two {s a b r} (op : Nat) (ka kb : Bool)
    (hop : allowedB u op = true)
    (h0 : opD d op a b ≠ 0) (hd : opD d op a b ≠ d) (hm : opD d op a b ∉ (a :: b :: r))
    (h : RunD u d y s (opD d op a b :: kept ka a (kept kb b r))) :
    RunD u d y (s + 1) (a :: b :: r) := fun P dn q v => v op ka kb hop h0 hd hm (h P dn q v)

theorem Run.fold {P : ∀ t ws, RunD u d y t ws → Prop}
    (done : P 0 [y] Run.done)
    (perm : ∀ {s xs zs} (hp : List.Perm xs zs) (h : RunD u d y s xs),
      P s xs h → P s zs (Run.perm hp h))
    (two : ∀ {s a b r} (op : Nat) (ka kb : Bool)
      (hop : allowedB u op = true)
      (h0 : opD d op a b ≠ 0) (hd : opD d op a b ≠ d) (hm : opD d op a b ∉ (a :: b :: r))
      (h : RunD u d y s (opD d op a b :: kept ka a (kept kb b r))),
      P _ _ h → P _ _ (Run.two op ka kb hop h0 hd hm h))
    {t ws} (h : RunD u d y t ws) : P t ws h := by
  have hex := h (fun s xs => ∃ h' : RunD u d y s xs, P s xs h')
    ⟨Run.done, done⟩
    (fun hp ⟨h', ih⟩ => ⟨Run.perm hp h', perm hp h' ih⟩)
    (fun op ka kb hop h0 hd hm ⟨h', ih⟩ => ⟨Run.two op ka kb hop h0 hd hm h', two op ka kb hop h0 hd hm h' ih⟩)
  exact hex.elim fun _ hp => hp
end

theorem allowed_cases {u : Bool} {op : Nat} (h : allowedB u op = true) :
    op = 0 ∨ op = 1 ∨ (u = true ∧ op = 2) ∨ (u = true ∧ op = 3) := by
  simp only [allowedB, Bool.or_eq_true, Bool.and_eq_true, decide_eq_true_eq] at h
  rcases h with h | ⟨hu, h⟩
  · omega
  · have : op = 0 ∨ op = 1 ∨ op = 2 ∨ op = 3 := by omega
    rcases this with rfl | rfl | rfl | rfl
    · exact Or.inl rfl
    · exact Or.inr (Or.inl rfl)
    · exact Or.inr (Or.inr (Or.inl ⟨hu, rfl⟩))
    · exact Or.inr (Or.inr (Or.inr ⟨hu, rfl⟩))

theorem opD_comm {u : Bool} (d : Nat) {op : Nat} (hop : allowedB u op = true) (a b : Nat) :
    opD d op a b = opD d (flipOp op) b a := by
  rcases allowed_cases hop with rfl | rfl | ⟨_, rfl⟩ | ⟨_, rfl⟩ <;>
    simp [opD, flipOp, andD, orD, Nat.and_comm, Nat.or_comm]

theorem flipOp_allowed {u : Bool} {op : Nat} (hop : allowedB u op = true) :
    allowedB u (flipOp op) = true := by
  rcases allowed_cases hop with rfl | rfl | ⟨rfl, rfl⟩ | ⟨rfl, rfl⟩ <;> simp [allowedB, flipOp]

theorem kept_map {α β : Type} (e : α → β) (b : Bool) (x : α) (xs : List α) :
    (kept b x xs).map e = kept b (e x) (xs.map e) := by cases b <;> simp [kept]

theorem mem_kept {α : Type} (b : Bool) (x a : α) (xs : List α) :
    a ∈ kept b x xs ↔ (b = true ∧ a = x) ∨ a ∈ xs := by cases b <;> simp [kept]

theorem nodup_kept {α : Type} (b : Bool) (x : α) (xs : List α) (h : xs.Nodup) (hx : x ∉ xs) :
    (kept b x xs).Nodup := by
  cases b
  · simpa [kept] using h
  · simpa [kept] using And.intro hx h

theorem keep_perm {α : Type} {xs ys : List α} (p : xs.Perm ys) (b : Bool) (a : α) :
    (kept b a xs).Perm (kept b a ys) := by cases b <;> simpa [kept] using p

theorem run_len {u d y s xs} (h : RunD u d y s xs) :
    xs.length ≤ s + 1 := by
  induction h using Run.fold with
  | done => simp
  | perm hp _ ih => rwa [← hp.length_eq]
  | two _ ka kb _ _ _ _ _ ih => cases ka <;> cases kb <;> simp_all [kept] <;> omega

theorem zero_done {u d y t ws} (h : RunD u d y t ws) :
    t = 0 → ws = [y] := by
  induction h using Run.fold with
  | done => simp
  | perm p _ ih => intro ht; rw [ih ht] at p; exact List.perm_singleton.1 p.symm
  | two => simp

def IsConst (d w : Nat) : Prop := (w &&& d) = 0 ∨ (w &&& d) = d
def isConstB (d w : Nat) : Bool := (w &&& d == 0) || (w &&& d == d)

theorem isConstB_iff (d w : Nat) : isConstB d w = true ↔ IsConst d w := by
  simp [isConstB, IsConst]

def Avail (u : Bool) (d : Nat) (bank : List Nat) (w : Nat) : Prop :=
  IsConst d w ∨ (∃ v ∈ bank, (v &&& d) = (w &&& d)) ∨ (u = true ∧ ∃ v ∈ bank, (v &&& d) = negD d w)

def availB (u : Bool) (d : Nat) (bank : List Nat) (w : Nat) : Bool :=
  let m := w &&& d
  m == 0 || m == d || bank.any (fun v => (v &&& d) == m) ||
    (u && bank.any (fun v => (v &&& d) == negD d w))

theorem availB_iff (u : Bool) (d : Nat) (bank : List Nat) (w : Nat) :
    availB u d bank w = true ↔ Avail u d bank w := by
  simp [availB, Avail, IsConst, or_assoc]

def NatReach (u : Bool) (d : Nat) (roots : List Nat) : Nat → List Nat → Prop
  | 0, bank => bank = roots
  | p + 1, bank =>
    ∃ b a c op, allowedB u op = true ∧ bank = opD d op a c :: b ∧
      NatReach u d roots p b ∧ Avail u d b a ∧ Avail u d b c

def Lower (u : Bool) (d : Nat) (roots : List Nat) (T : Nat) (L : Nat) : Prop :=
  ∀ p bank, NatReach u d roots p bank → Avail u d bank T → L ≤ p

theorem avail_mono {d : Nat} {bank : List Nat} {w : Nat} (h : Avail false d bank w) :
    Avail true d bank w := by
  rcases h with h | h | ⟨h, _⟩
  · exact Or.inl h
  · exact Or.inr (Or.inl h)
  · contradiction

theorem reach_up {d : Nat} {roots : List Nat} {p bank} (h : NatReach false d roots p bank) :
    NatReach true d roots p bank := by
  induction p generalizing bank with
  | zero => exact h
  | succ p ih =>
    obtain ⟨b, a, c, op, hop, rfl, hrb, ha, hc⟩ := h
    have hop' : allowedB true op = true := by
      rcases allowed_cases hop with rfl | rfl | ⟨hc, _⟩ | ⟨hc, _⟩ <;> first | decide | contradiction
    exact ⟨b, a, c, op, hop', rfl, ih hrb, avail_mono ha, avail_mono hc⟩

theorem lower_down {d : Nat} {roots : List Nat} {T L : Nat} (h : Lower true d roots T L) :
    Lower false d roots T L := fun p bank hr ha => h p bank (reach_up hr) (avail_mono ha)

theorem mask256_bit (i : Nat) : mask256.testBit i = decide (i < 256) := by
  rw [mask256, Nat.testBit_two_pow_sub_one]

theorem opD_and_sub {d d1 : Nat} (hd : d &&& mask256 = d) (hsub : d &&& d1 = d) (op a b : Nat) :
    opD d1 op a b &&& d = opD d op a b := by
  apply Nat.eq_of_testBit_eq; intro i
  have h1 := congrArg (fun v => v.testBit i) hd
  have h2 := congrArg (fun v => v.testBit i) hsub
  unfold opD
  split_ifs <;> simp only [andD, orD, negD, Nat.testBit_and, Nat.testBit_or, Nat.testBit_xor] at * <;>
    cases hi : d.testBit i <;> simp_all

theorem negD_invol {d : Nat} (hd : d &&& mask256 = d) (a : Nat) :
    negD d (negD d a) = a &&& d := by
  apply Nat.eq_of_testBit_eq; intro i
  have h1 := congrArg (fun v => v.testBit i) hd
  simp only [negD, Nat.testBit_and, Nat.testBit_xor] at *
  cases hi : d.testBit i <;> cases ha : a.testBit i <;> simp_all

theorem negD_mask (d a : Nat) : negD d (a &&& d) = negD d a := by
  apply Nat.eq_of_testBit_eq; intro i
  simp only [negD, Nat.testBit_and, Nat.testBit_xor]
  cases d.testBit i <;> simp

theorem andD_mask (d a b : Nat) : andD d (a &&& d) (b &&& d) = andD d a b := by
  apply Nat.eq_of_testBit_eq; intro i
  simp only [andD, Nat.testBit_and]
  cases d.testBit i <;> simp

theorem orD_mask (d a b : Nat) : orD d (a &&& d) (b &&& d) = orD d a b := by
  apply Nat.eq_of_testBit_eq; intro i
  simp only [orD, Nat.testBit_and, Nat.testBit_or]
  cases d.testBit i <;> simp

theorem opD_mask_self (d op a b : Nat) : opD d op a b &&& d = opD d op a b := by
  apply Nat.eq_of_testBit_eq; intro i
  unfold opD; split_ifs <;> simp only [andD, orD, negD, Nat.testBit_and, Nat.testBit_or, Nat.testBit_xor] <;>
    cases d.testBit i <;> simp

theorem negD_const {d : Nat} (hd : d &&& mask256 = d) {a : Nat} (hc : IsConst d a) :
    IsConst d (negD d a) := by
  rcases hc with h0 | h1
  · right; apply Nat.eq_of_testBit_eq; intro i
    have h0i := congrArg (fun v => v.testBit i) h0
    have hdi := congrArg (fun v => v.testBit i) hd
    simp only [negD, Nat.testBit_and, Nat.testBit_xor, Nat.zero_testBit] at *
    cases h1' : d.testBit i <;> cases h2' : a.testBit i <;> simp_all
  · left; apply Nat.eq_of_testBit_eq; intro i
    have h1i := congrArg (fun v => v.testBit i) h1
    have hdi := congrArg (fun v => v.testBit i) hd
    simp only [negD, Nat.testBit_and, Nat.testBit_xor, Nat.zero_testBit] at *
    cases h1' : d.testBit i <;> cases h2' : a.testBit i <;> simp_all

theorem avail_cons {u : Bool} {d : Nat} {bank : List Nat} (z w : Nat) (h : Avail u d bank w) :
    Avail u d (z :: bank) w := by
  rcases h with hc | ⟨v, hv, he⟩ | ⟨hu, v, hv, he⟩
  · exact Or.inl hc
  · exact Or.inr (Or.inl ⟨v, List.mem_cons_of_mem _ hv, he⟩)
  · exact Or.inr (Or.inr ⟨hu, v, List.mem_cons_of_mem _ hv, he⟩)

theorem avail_of_eq {u : Bool} {d : Nat} {bank : List Nat} {v w : Nat}
    (he : v &&& d = w &&& d) (h : Avail u d bank v) : Avail u d bank w := by
  rcases h with (h0 | h1) | ⟨x, hx, hxe⟩ | ⟨hu, x, hx, hxe⟩
  · exact Or.inl (Or.inl (he.symm.trans h0))
  · exact Or.inl (Or.inr (he.symm.trans h1))
  · exact Or.inr (Or.inl ⟨x, hx, hxe.trans he⟩)
  · exact Or.inr (Or.inr ⟨hu, x, hx, hxe.trans (by rw [← negD_mask, he, negD_mask])⟩)

theorem avail_neg {d : Nat} (hd : d &&& mask256 = d) {bank : List Nat} {w : Nat}
    (h : Avail true d bank w) : Avail true d bank (negD d w) := by
  rcases h with hc | ⟨v, hv, he⟩ | ⟨_, v, hv, he⟩
  · exact Or.inl (negD_const hd hc)
  · refine Or.inr (Or.inr ⟨rfl, v, hv, ?_⟩)
    rw [negD_invol hd, he]
  · refine Or.inr (Or.inl ⟨v, hv, ?_⟩)
    rw [he]; simp [negD, Nat.and_assoc, Nat.and_self]

theorem opD_const_left {u : Bool} {d : Nat} (hd : d &&& mask256 = d) {op : Nat}
    (hop : allowedB u op = true) {a b : Nat} (hc : IsConst d a) :
    (opD d op a b &&& d = 0) ∨ (opD d op a b &&& d = d) ∨
      (opD d op a b &&& d = b &&& d) ∨ (u = true ∧ opD d op a b &&& d = negD d b) := by
  rcases allowed_cases hop with rfl | rfl | ⟨hu, rfl⟩ | ⟨hu, rfl⟩
  · rcases hc with h0 | h1
    · left; apply Nat.eq_of_testBit_eq; intro i
      have h0i := congrArg (fun v => v.testBit i) h0
      simp only [opD, andD, Nat.testBit_and, Nat.zero_testBit, beq_self_eq_true, ite_true] at *
      cases hd' : d.testBit i <;> cases ha' : a.testBit i <;> cases hb' : b.testBit i <;> simp_all
    · right; right; left; apply Nat.eq_of_testBit_eq; intro i
      have h1i := congrArg (fun v => v.testBit i) h1
      simp only [opD, andD, Nat.testBit_and, beq_self_eq_true, ite_true] at *
      cases hd' : d.testBit i <;> cases ha' : a.testBit i <;> cases hb' : b.testBit i <;> simp_all
  · rcases hc with h0 | h1
    · right; right; left; apply Nat.eq_of_testBit_eq; intro i
      have h0i := congrArg (fun v => v.testBit i) h0
      simp only [opD, orD, Nat.testBit_and, Nat.testBit_or, Nat.zero_testBit, beq_self_eq_true, ite_true, ite_false] at *
      cases hd' : d.testBit i <;> cases ha' : a.testBit i <;> cases hb' : b.testBit i <;> simp_all
    · right; left; apply Nat.eq_of_testBit_eq; intro i
      have h1i := congrArg (fun v => v.testBit i) h1
      simp only [opD, orD, Nat.testBit_and, Nat.testBit_or, beq_self_eq_true, ite_true, ite_false] at *
      cases hd' : d.testBit i <;> cases ha' : a.testBit i <;> cases hb' : b.testBit i <;> simp_all
  · rcases hc with h0 | h1
    · left; apply Nat.eq_of_testBit_eq; intro i
      have h0i := congrArg (fun v => v.testBit i) h0
      simp only [opD, andD, negD, Nat.testBit_and, Nat.testBit_xor, Nat.zero_testBit, beq_self_eq_true, ite_true, ite_false] at *
      cases hd' : d.testBit i <;> cases ha' : a.testBit i <;> cases hb' : b.testBit i <;> simp_all
    · right; right; right; refine ⟨hu, ?_⟩
      apply Nat.eq_of_testBit_eq; intro i
      have h1i := congrArg (fun v => v.testBit i) h1
      have hdi := congrArg (fun v => v.testBit i) hd
      simp only [opD, andD, negD, Nat.testBit_and, Nat.testBit_xor, beq_self_eq_true, ite_true, ite_false] at *
      cases hd' : d.testBit i <;> cases ha' : a.testBit i <;> cases hb' : b.testBit i <;> simp_all
  · rcases hc with h0 | h1
    · right; right; left; apply Nat.eq_of_testBit_eq; intro i
      have h0i := congrArg (fun v => v.testBit i) h0
      have hdi := congrArg (fun v => v.testBit i) hd
      simp only [opD, andD, negD, Nat.testBit_and, Nat.testBit_xor, Nat.zero_testBit, beq_self_eq_true, ite_true, ite_false] at *
      cases hd' : d.testBit i <;> cases ha' : a.testBit i <;> cases hb' : b.testBit i <;> simp_all
    · left; apply Nat.eq_of_testBit_eq; intro i
      have h1i := congrArg (fun v => v.testBit i) h1
      have hdi := congrArg (fun v => v.testBit i) hd
      simp only [opD, andD, negD, Nat.testBit_and, Nat.testBit_xor, Nat.zero_testBit, beq_self_eq_true, ite_true, ite_false] at *
      cases hd' : d.testBit i <;> cases ha' : a.testBit i <;> cases hb' : b.testBit i <;> simp_all

theorem countP_kept_ge {α : Type} (p : α → Bool) (b : Bool) (a : α) (xs : List α) :
    xs.countP p ≤ (kept b a xs).countP p := by
  cases b <;> simp [kept, List.countP_cons] <;> split <;> omega

theorem contraction {u : Bool} {d d1 T : Nat} (hd : d &&& mask256 = d) (hsub : d &&& d1 = d)
    (hnc : ¬ IsConst d T) {s ws} (h : RunD u d1 T s ws) {roots p bank}
    (hp : NatReach u d roots p bank) (hs : ∀ w ∈ ws, Avail u d bank w) :
    ∃ q next, NatReach u d roots q next ∧ Avail u d next T ∧
      q + ws.countP (isConstB d) ≤ p + s := by
  induction h using Run.fold generalizing p bank with
  | done =>
    have hfalse : isConstB d T = false := by
      cases hc : isConstB d T with
      | false => rfl
      | true => exact absurd ((isConstB_iff d T).1 hc) hnc
    exact ⟨p, bank, hp, hs T (by simp), by simp [hfalse]⟩
  | perm eq _ ih =>
    obtain ⟨q, next, hq, ht, hle⟩ := ih hp (fun w hw => hs w (eq.mem_iff.1 hw))
    rw [eq.countP_eq] at hle
    exact ⟨q, next, hq, ht, hle⟩
  | @two s a b r op ka kb hop _ _ _ _ ih =>
    have ha := hs a List.mem_cons_self
    have hb := hs b (List.mem_cons_of_mem _ List.mem_cons_self)
    set z1 := opD d1 op a b
    set z0 := opD d op a b
    have hz_eq : z1 &&& d = z0 &&& d := by
      rw [opD_and_sub hd hsub, opD_mask_self]
    by_cases hcab : IsConst d a ∨ IsConst d b
    · have hz_av : Avail u d bank z1 := by
        apply avail_of_eq hz_eq.symm
        rcases hcab with hca | hcb
        · rcases opD_const_left hd hop hca with h0 | h1 | he | ⟨rfl, hn⟩
          · exact Or.inl (Or.inl h0)
          · exact Or.inl (Or.inr h1)
          · exact avail_of_eq he.symm hb
          · exact avail_of_eq (by rw [hn]; simp [negD, Nat.and_assoc, Nat.and_self]) (avail_neg hd hb)
        · dsimp only [z0]; rw [opD_comm d hop a b]
          rcases opD_const_left hd (flipOp_allowed hop) hcb with h0 | h1 | he | ⟨rfl, hn⟩
          · exact Or.inl (Or.inl h0)
          · exact Or.inl (Or.inr h1)
          · exact avail_of_eq he.symm ha
          · exact avail_of_eq (by rw [hn]; simp [negD, Nat.and_assoc, Nat.and_self]) (avail_neg hd ha)
      have hs' : ∀ w ∈ z1 :: kept ka a (kept kb b r), Avail u d bank w := by
        intro w hw; rcases List.mem_cons.1 hw with rfl | hw
        · exact hz_av
        · rw [mem_kept, mem_kept] at hw
          rcases hw with ⟨_, rfl⟩ | ⟨_, rfl⟩ | hw
          · exact ha
          · exact hb
          · exact hs w (List.mem_cons_of_mem _ (List.mem_cons_of_mem _ hw))
      obtain ⟨q, next, hq, ht, hle⟩ := ih hp hs'
      have hkr : r.countP (isConstB d) ≤ (kept ka a (kept kb b r)).countP (isConstB d) :=
        le_trans (countP_kept_ge _ kb b r) (countP_kept_ge _ ka a _)
      have hcost : (if isConstB d a = true then 1 else 0) + (if isConstB d b = true then 1 else 0)
          ≤ 1 + (if isConstB d z1 = true then 1 else 0) := by
        rcases hcab with hca | hcb
        · have ha1 : isConstB d a = true := (isConstB_iff _ _).2 hca
          rcases opD_const_left hd hop hca with h0 | h1 | he | ⟨_, hn⟩
          · have hz1 : isConstB d z1 = true := (isConstB_iff _ _).2 (Or.inl (hz_eq.trans h0))
            simp [ha1, hz1]; split <;> omega
          · have hz1 : isConstB d z1 = true := (isConstB_iff _ _).2 (Or.inr (hz_eq.trans h1))
            simp [ha1, hz1]; split <;> omega
          · have hzb : isConstB d z1 = isConstB d b := by simp only [isConstB, hz_eq.trans he]
            simp [ha1, hzb]
          · have hzb : isConstB d z1 = isConstB d b := by
              apply Bool.eq_iff_iff.2; rw [isConstB_iff, isConstB_iff]
              have hnm : negD d b &&& d = negD d b := by simp [negD, Nat.and_assoc, Nat.and_self]
              constructor
              · intro hz; have hnb : IsConst d (negD d b) := by
                  rcases hz with h0 | h1
                  · exact Or.inl (hnm.trans (hn.symm.trans (hz_eq.symm.trans h0)))
                  · exact Or.inr (hnm.trans (hn.symm.trans (hz_eq.symm.trans h1)))
                have h2 := negD_const hd hnb
                rw [negD_invol hd] at h2
                rcases h2 with e | e <;> [exact Or.inl (by simpa [Nat.and_assoc, Nat.and_self] using e); exact Or.inr (by simpa [Nat.and_assoc, Nat.and_self] using e)]
              · intro hb'; have hnb := negD_const hd hb'
                rcases hnb with h0 | h1
                · exact Or.inl (hz_eq.trans (hn.trans (hnm.symm.trans h0)))
                · exact Or.inr (hz_eq.trans (hn.trans (hnm.symm.trans h1)))
            simp [ha1, hzb]
        · have hb1 : isConstB d b = true := (isConstB_iff _ _).2 hcb
          have hz_eq' : z1 &&& d = opD d (flipOp op) b a &&& d := by rw [hz_eq]; dsimp only [z0]; rw [opD_comm d hop a b]
          rcases opD_const_left hd (flipOp_allowed hop) hcb with h0 | h1 | he | ⟨_, hn⟩
          · have hz1 : isConstB d z1 = true := (isConstB_iff _ _).2 (Or.inl (hz_eq'.trans h0))
            simp [hb1, hz1]; split <;> omega
          · have hz1 : isConstB d z1 = true := (isConstB_iff _ _).2 (Or.inr (hz_eq'.trans h1))
            simp [hb1, hz1]; split <;> omega
          · have hza : isConstB d z1 = isConstB d a := by simp only [isConstB, hz_eq'.trans he]
            simp [hb1, hza]
          · have hza : isConstB d z1 = isConstB d a := by
              apply Bool.eq_iff_iff.2; rw [isConstB_iff, isConstB_iff]
              have hnm : negD d a &&& d = negD d a := by simp [negD, Nat.and_assoc, Nat.and_self]
              constructor
              · intro hz; have hna : IsConst d (negD d a) := by
                  rcases hz with h0 | h1
                  · exact Or.inl (hnm.trans (hn.symm.trans (hz_eq'.symm.trans h0)))
                  · exact Or.inr (hnm.trans (hn.symm.trans (hz_eq'.symm.trans h1)))
                have h2 := negD_const hd hna
                rw [negD_invol hd] at h2
                rcases h2 with e | e <;> [exact Or.inl (by simpa [Nat.and_assoc, Nat.and_self] using e); exact Or.inr (by simpa [Nat.and_assoc, Nat.and_self] using e)]
              · intro ha'; have hna := negD_const hd ha'
                rcases hna with h0 | h1
                · exact Or.inl (hz_eq'.trans (hn.trans (hnm.symm.trans h0)))
                · exact Or.inr (hz_eq'.trans (hn.trans (hnm.symm.trans h1)))
            simp [hb1, hza]
      simp only [List.countP_cons] at hle ⊢
      exact ⟨q, next, hq, ht, by omega⟩
    · have hna : isConstB d a = false := by
        cases h : isConstB d a with | false => rfl | true => exact absurd (Or.inl ((isConstB_iff _ _).1 h)) hcab
      have hnb : isConstB d b = false := by
        cases h : isConstB d b with | false => rfl | true => exact absurd (Or.inr ((isConstB_iff _ _).1 h)) hcab
      have hreach' : NatReach u d roots (p + 1) (z0 :: bank) := ⟨bank, a, b, op, hop, rfl, hp, ha, hb⟩
      have hz_av : Avail u d (z0 :: bank) z1 := Or.inr (Or.inl ⟨z0, List.mem_cons_self, hz_eq.symm⟩)
      have hs' : ∀ w ∈ z1 :: kept ka a (kept kb b r), Avail u d (z0 :: bank) w := by
        intro w hw; rcases List.mem_cons.1 hw with rfl | hw
        · exact hz_av
        · rw [mem_kept, mem_kept] at hw
          rcases hw with ⟨_, rfl⟩ | ⟨_, rfl⟩ | hw
          · exact avail_cons _ _ ha
          · exact avail_cons _ _ hb
          · exact avail_cons _ _ (hs w (List.mem_cons_of_mem _ (List.mem_cons_of_mem _ hw)))
      obtain ⟨q, next, hq, ht, hle⟩ := ih hreach' hs'
      have hkr : r.countP (isConstB d) ≤ (kept ka a (kept kb b r)).countP (isConstB d) :=
        le_trans (countP_kept_ge _ kb b r) (countP_kept_ge _ ka a _)
      simp only [List.countP_cons, hna, hnb, Bool.false_eq_true, ite_false] at hle ⊢
      exact ⟨q, next, hq, ht, by omega⟩

-- Normalization lemmas for backward extraction
theorem nrmD_mask (u : Bool) (d w : Nat) : nrmD u d w &&& d = nrmD u d w := by
  unfold nrmD; split <;> simp [negD, Nat.and_assoc, Nat.and_self]

theorem nrmD_of_bit0_false (u : Bool) (d w : Nat) (hw : w.testBit 0 = false) :
    nrmD u d w = w &&& d := by
  simp [nrmD, hw]

theorem nrmD_and_d {d : Nat} (hd0 : d.testBit 0 = true) (u : Bool) (w : Nat) :
    nrmD u d (w &&& d) = nrmD u d w := by
  unfold nrmD
  rw [Nat.testBit_and, hd0, Bool.and_true, negD_mask, Nat.and_assoc, Nat.and_self]

theorem nrmD_neg {d : Nat} (hd : d &&& mask256 = d) (hd0 : d.testBit 0 = true) (w : Nat) :
    nrmD true d (negD d w) = nrmD true d w := by
  have hm0 : mask256.testBit 0 = true := by decide
  unfold nrmD
  have hnb : (negD d w).testBit 0 = !w.testBit 0 := by
    simp only [negD, Nat.testBit_and, Nat.testBit_xor, hd0, hm0, Bool.and_true, Bool.xor_true]
  rw [hnb]
  cases hw : w.testBit 0
  · simp [negD_invol hd]
  · simp [negD, Nat.and_assoc, Nat.and_self]

theorem nrmD_const_iff {d : Nat} (hd : d &&& mask256 = d) (u : Bool) (w : Nat) :
    (nrmD u d w ≠ 0 ∧ nrmD u d w ≠ d) ↔ ¬ IsConst d w := by
  unfold nrmD
  have hnm : negD d w &&& d = negD d w := by simp [negD, Nat.and_assoc, Nat.and_self]
  split
  · constructor
    · rintro ⟨h0, h1⟩ hc
      rcases negD_const hd hc with hn0 | hn1
      · exact h0 (hnm.symm.trans hn0)
      · exact h1 (hnm.symm.trans hn1)
    · intro hnc; refine ⟨fun h0 => ?_, fun h1 => ?_⟩
      · have := negD_const hd (a := negD d w) (Or.inl (hnm.trans h0))
        rw [negD_invol hd] at this
        exact hnc (by rcases this with e | e <;> [exact Or.inl (by simpa [Nat.and_assoc, Nat.and_self] using e); exact Or.inr (by simpa [Nat.and_assoc, Nat.and_self] using e)])
      · have := negD_const hd (a := negD d w) (Or.inr (hnm.trans h1))
        rw [negD_invol hd] at this
        exact hnc (by rcases this with e | e <;> [exact Or.inl (by simpa [Nat.and_assoc, Nat.and_self] using e); exact Or.inr (by simpa [Nat.and_assoc, Nat.and_self] using e)])
  · simp [IsConst, not_or]

theorem opD_bit {d : Nat} (hd : d &&& mask256 = d) (op a b i : Nat) (hdi : d.testBit i = true) :
    (opD d op a b).testBit i =
      if op == 0 then a.testBit i && b.testBit i
      else if op == 1 then a.testBit i || b.testBit i
      else if op == 2 then a.testBit i && !(b.testBit i)
      else !(a.testBit i) && b.testBit i := by
  have hmi : mask256.testBit i = true := by
    have := congrArg (fun v => v.testBit i) hd; simp [Nat.testBit_and, hdi] at this; exact this
  unfold opD; split_ifs <;>
    simp only [andD, orD, negD, Nat.testBit_and, Nat.testBit_or, Nat.testBit_xor, hdi, hmi, Bool.and_true, Bool.xor_true]

theorem nrmD_bit {d : Nat} (hd : d &&& mask256 = d) (w i : Nat) (hdi : d.testBit i = true) :
    (nrmD true d w).testBit i = if w.testBit 0 then !(w.testBit i) else w.testBit i := by
  have hmi : mask256.testBit i = true := by
    have := congrArg (fun v => v.testBit i) hd; simp [Nat.testBit_and, hdi] at this; exact this
  unfold nrmD
  cases hw0 : w.testBit 0 <;>
    simp only [hw0, Bool.true_and, Bool.and_false, Bool.false_eq_true, ite_true, ite_false,
      negD, Nat.testBit_and, Nat.testBit_xor, hdi, hmi, Bool.and_true, Bool.xor_true]

theorem nrmD_opD {d : Nat} (hd : d &&& mask256 = d) (hd0 : d.testBit 0 = true)
    (u : Bool) (op : Nat) (hop : allowedB u op = true) (a b : Nat) :
    ∃ op', allowedB u op' = true ∧
      nrmD u d (opD d op a b) = opD d op' (nrmD u d a) (nrmD u d b) := by
  cases u with
  | false =>
    rcases allowed_cases hop with rfl | rfl | ⟨h, _⟩ | ⟨h, _⟩
    · exact ⟨0, rfl, by
        apply Nat.eq_of_testBit_eq; intro i
        simp only [nrmD, opD, andD, Bool.false_and, Bool.false_eq_true, ite_false, beq_self_eq_true, ite_true, Nat.testBit_and]
        cases d.testBit i <;> cases a.testBit i <;> cases b.testBit i <;> rfl⟩
    · exact ⟨1, rfl, by
        apply Nat.eq_of_testBit_eq; intro i
        simp only [nrmD, opD, orD, Bool.false_and, Bool.false_eq_true, ite_false]
        simp only [show (1 == 0) = false from rfl, show (1 == 1) = true from rfl, Bool.false_eq_true, ite_false, ite_true, Nat.testBit_and, Nat.testBit_or]
        cases d.testBit i <;> cases a.testBit i <;> cases b.testBit i <;> rfl⟩
    · contradiction
    · contradiction
  | true =>
    have h4 : op = 0 ∨ op = 1 ∨ op = 2 ∨ op = 3 := by
      rcases allowed_cases hop with rfl | rfl | ⟨_, rfl⟩ | ⟨_, rfl⟩ <;> simp
    have hbit : ∀ (e : Nat),
        (∀ i, d.testBit i = true →
          (nrmD true d (opD d op a b)).testBit i =
          (opD d e (nrmD true d a) (nrmD true d b)).testBit i) →
        nrmD true d (opD d op a b) = opD d e (nrmD true d a) (nrmD true d b) := by
      intro e h; apply Nat.eq_of_testBit_eq; intro i
      by_cases hdi : d.testBit i = true
      · exact h i hdi
      · have hf : d.testBit i = false := Bool.eq_false_iff.2 hdi
        have h1 := congrArg (fun v => v.testBit i) (nrmD_mask true d (opD d op a b))
        have h2 := congrArg (fun v => v.testBit i) (opD_mask_self d e (nrmD true d a) (nrmD true d b))
        simp only [Nat.testBit_and, hf, Bool.and_false] at h1 h2; exact h1.symm.trans h2
    rcases h4 with rfl | rfl | rfl | rfl <;>
      cases ha0 : a.testBit 0 <;> cases hb0 : b.testBit 0
    · exact ⟨0, by decide, hbit 0 fun i hdi => by rw [nrmD_bit hd _ i hdi, opD_bit hd _ _ _ 0 hd0, opD_bit hd _ _ _ i hdi, opD_bit hd _ _ _ i hdi, nrmD_bit hd a i hdi, nrmD_bit hd b i hdi, ha0, hb0]; cases a.testBit i <;> cases b.testBit i <;> rfl⟩
    · exact ⟨2, by decide, hbit 2 fun i hdi => by rw [nrmD_bit hd _ i hdi, opD_bit hd _ _ _ 0 hd0, opD_bit hd _ _ _ i hdi, opD_bit hd _ _ _ i hdi, nrmD_bit hd a i hdi, nrmD_bit hd b i hdi, ha0, hb0]; cases a.testBit i <;> cases b.testBit i <;> rfl⟩
    · exact ⟨3, by decide, hbit 3 fun i hdi => by rw [nrmD_bit hd _ i hdi, opD_bit hd _ _ _ 0 hd0, opD_bit hd _ _ _ i hdi, opD_bit hd _ _ _ i hdi, nrmD_bit hd a i hdi, nrmD_bit hd b i hdi, ha0, hb0]; cases a.testBit i <;> cases b.testBit i <;> rfl⟩
    · exact ⟨1, by decide, hbit 1 fun i hdi => by rw [nrmD_bit hd _ i hdi, opD_bit hd _ _ _ 0 hd0, opD_bit hd _ _ _ i hdi, opD_bit hd _ _ _ i hdi, nrmD_bit hd a i hdi, nrmD_bit hd b i hdi, ha0, hb0]; cases a.testBit i <;> cases b.testBit i <;> rfl⟩
    · exact ⟨1, by decide, hbit 1 fun i hdi => by rw [nrmD_bit hd _ i hdi, opD_bit hd _ _ _ 0 hd0, opD_bit hd _ _ _ i hdi, opD_bit hd _ _ _ i hdi, nrmD_bit hd a i hdi, nrmD_bit hd b i hdi, ha0, hb0]; cases a.testBit i <;> cases b.testBit i <;> rfl⟩
    · exact ⟨3, by decide, hbit 3 fun i hdi => by rw [nrmD_bit hd _ i hdi, opD_bit hd _ _ _ 0 hd0, opD_bit hd _ _ _ i hdi, opD_bit hd _ _ _ i hdi, nrmD_bit hd a i hdi, nrmD_bit hd b i hdi, ha0, hb0]; cases a.testBit i <;> cases b.testBit i <;> rfl⟩
    · exact ⟨2, by decide, hbit 2 fun i hdi => by rw [nrmD_bit hd _ i hdi, opD_bit hd _ _ _ 0 hd0, opD_bit hd _ _ _ i hdi, opD_bit hd _ _ _ i hdi, nrmD_bit hd a i hdi, nrmD_bit hd b i hdi, ha0, hb0]; cases a.testBit i <;> cases b.testBit i <;> rfl⟩
    · exact ⟨0, by decide, hbit 0 fun i hdi => by rw [nrmD_bit hd _ i hdi, opD_bit hd _ _ _ 0 hd0, opD_bit hd _ _ _ i hdi, opD_bit hd _ _ _ i hdi, nrmD_bit hd a i hdi, nrmD_bit hd b i hdi, ha0, hb0]; cases a.testBit i <;> cases b.testBit i <;> rfl⟩
    · exact ⟨2, by decide, hbit 2 fun i hdi => by rw [nrmD_bit hd _ i hdi, opD_bit hd _ _ _ 0 hd0, opD_bit hd _ _ _ i hdi, opD_bit hd _ _ _ i hdi, nrmD_bit hd a i hdi, nrmD_bit hd b i hdi, ha0, hb0]; cases a.testBit i <;> cases b.testBit i <;> rfl⟩
    · exact ⟨0, by decide, hbit 0 fun i hdi => by rw [nrmD_bit hd _ i hdi, opD_bit hd _ _ _ 0 hd0, opD_bit hd _ _ _ i hdi, opD_bit hd _ _ _ i hdi, nrmD_bit hd a i hdi, nrmD_bit hd b i hdi, ha0, hb0]; cases a.testBit i <;> cases b.testBit i <;> rfl⟩
    · exact ⟨1, by decide, hbit 1 fun i hdi => by rw [nrmD_bit hd _ i hdi, opD_bit hd _ _ _ 0 hd0, opD_bit hd _ _ _ i hdi, opD_bit hd _ _ _ i hdi, nrmD_bit hd a i hdi, nrmD_bit hd b i hdi, ha0, hb0]; cases a.testBit i <;> cases b.testBit i <;> rfl⟩
    · exact ⟨3, by decide, hbit 3 fun i hdi => by rw [nrmD_bit hd _ i hdi, opD_bit hd _ _ _ 0 hd0, opD_bit hd _ _ _ i hdi, opD_bit hd _ _ _ i hdi, nrmD_bit hd a i hdi, nrmD_bit hd b i hdi, ha0, hb0]; cases a.testBit i <;> cases b.testBit i <;> rfl⟩
    · exact ⟨3, by decide, hbit 3 fun i hdi => by rw [nrmD_bit hd _ i hdi, opD_bit hd _ _ _ 0 hd0, opD_bit hd _ _ _ i hdi, opD_bit hd _ _ _ i hdi, nrmD_bit hd a i hdi, nrmD_bit hd b i hdi, ha0, hb0]; cases a.testBit i <;> cases b.testBit i <;> rfl⟩
    · exact ⟨1, by decide, hbit 1 fun i hdi => by rw [nrmD_bit hd _ i hdi, opD_bit hd _ _ _ 0 hd0, opD_bit hd _ _ _ i hdi, opD_bit hd _ _ _ i hdi, nrmD_bit hd a i hdi, nrmD_bit hd b i hdi, ha0, hb0]; cases a.testBit i <;> cases b.testBit i <;> rfl⟩
    · exact ⟨0, by decide, hbit 0 fun i hdi => by rw [nrmD_bit hd _ i hdi, opD_bit hd _ _ _ 0 hd0, opD_bit hd _ _ _ i hdi, opD_bit hd _ _ _ i hdi, nrmD_bit hd a i hdi, nrmD_bit hd b i hdi, ha0, hb0]; cases a.testBit i <;> cases b.testBit i <;> rfl⟩
    · exact ⟨2, by decide, hbit 2 fun i hdi => by rw [nrmD_bit hd _ i hdi, opD_bit hd _ _ _ 0 hd0, opD_bit hd _ _ _ i hdi, opD_bit hd _ _ _ i hdi, nrmD_bit hd a i hdi, nrmD_bit hd b i hdi, ha0, hb0]; cases a.testBit i <;> cases b.testBit i <;> rfl⟩

theorem avail_nrm_mem {u : Bool} {d : Nat} (hd : d &&& mask256 = d) (hd0 : d.testBit 0 = true)
    {b : List Nat} {w : Nat} (h : Avail u d b w) (hnc : ¬ IsConst d w) :
    nrmD u d w ∈ b.map (nrmD u d) := by
  rcases h with hc | ⟨v, hv, he⟩ | ⟨rfl, v, hv, he⟩
  · exact absurd hc hnc
  · refine List.mem_map.2 ⟨v, hv, ?_⟩
    rw [← nrmD_and_d hd0, he, nrmD_and_d hd0]
  · refine List.mem_map.2 ⟨v, hv, ?_⟩
    rw [← nrmD_and_d hd0, he, nrmD_neg hd hd0]

theorem pull_two {u : Bool} {d Y k ws} (hd : d &&& mask256 = d) (hd0 : d.testBit 0 = true)
    (hnd : ws.Nodup) (hprop : ∀ w ∈ ws, w ≠ 0 ∧ w ≠ d) (h : RunD u d Y k ws)
    {b : List Nat} {a c : Nat} (op : Nat) (hop : allowedB u op = true)
    (ha : Avail u d b a) (hc : Avail u d b c)
    (hsub : ∀ w ∈ ws, w ∈ nrmD u d (opD d op a c) :: b.map (nrmD u d)) :
    ∃ k' ws', k' ≤ k + 1 ∧ ws'.Nodup ∧ (∀ w ∈ ws', w ≠ 0 ∧ w ≠ d) ∧
      (∀ w ∈ ws', w ∈ b.map (nrmD u d)) ∧ RunD u d Y k' ws' := by
  set z := nrmD u d (opD d op a c)
  by_cases hzm : z ∈ ws
  · by_cases hzb : z ∈ b.map (nrmD u d)
    · exact ⟨k, ws, by omega, hnd, hprop, fun w hw => by
        rcases List.mem_cons.1 (hsub w hw) with rfl | hm
        · exact hzb
        · exact hm, h⟩
    · have hzp := hprop z hzm
      obtain ⟨op', hop', hez⟩ := nrmD_opD hd hd0 u op hop a c
      have ha_nc : ¬ IsConst d a := by
        intro hca
        have hznc : ¬ IsConst d (opD d op a c) := (nrmD_const_iff hd u _).1 hzp
        rcases opD_const_left hd hop hca with e0 | e1 | ec | ⟨rfl, en⟩
        · exact hznc (Or.inl e0)
        · exact hznc (Or.inr e1)
        · have hcn : ¬ IsConst d c := fun hcc => hznc (by rcases hcc with e | e <;> [exact Or.inl (ec.trans e); exact Or.inr (ec.trans e)])
          have hz_eq : z = nrmD u d c := by dsimp only [z]; rw [← nrmD_and_d hd0 u (opD d op a c), ec, nrmD_and_d hd0]
          exact hzb (hz_eq ▸ avail_nrm_mem hd hd0 hc hcn)
        · have hcn : ¬ IsConst d c := fun hcc => hznc (by
            rcases negD_const hd hcc with e | e
            · exact Or.inl (en.trans (by simpa [negD, Nat.and_assoc, Nat.and_self] using e))
            · exact Or.inr (en.trans (by simpa [negD, Nat.and_assoc, Nat.and_self] using e)))
          have hz_eq : z = nrmD true d c := by dsimp only [z]; rw [← nrmD_and_d hd0 true (opD d op a c), en, nrmD_neg hd hd0]
          exact hzb (hz_eq ▸ avail_nrm_mem hd hd0 hc hcn)
      have hc_nc : ¬ IsConst d c := by
        intro hcc
        have hznc : ¬ IsConst d (opD d op a c) := (nrmD_const_iff hd u _).1 hzp
        have hcm : opD d op a c = opD d (flipOp op) c a := opD_comm d hop a c
        rcases opD_const_left hd (flipOp_allowed hop) hcc with e0 | e1 | ea | ⟨rfl, en⟩
        · exact hznc (Or.inl (hcm.symm ▸ e0))
        · exact hznc (Or.inr (hcm.symm ▸ e1))
        · have hz_eq : z = nrmD u d a := by
            dsimp only [z]; rw [← nrmD_and_d hd0 u (opD d op a c), hcm, ea, nrmD_and_d hd0]
          exact hzb (hz_eq ▸ avail_nrm_mem hd hd0 ha ha_nc)
        · have hz_eq : z = nrmD true d a := by
            dsimp only [z]; rw [← nrmD_and_d hd0 true (opD d op a c), hcm, en, nrmD_neg hd hd0]
          exact hzb (hz_eq ▸ avail_nrm_mem hd hd0 ha ha_nc)
      set a' := nrmD u d a
      set c' := nrmD u d c
      have ha'_mem : a' ∈ b.map (nrmD u d) := avail_nrm_mem hd hd0 ha ha_nc
      have hc'_mem : c' ∈ b.map (nrmD u d) := avail_nrm_mem hd hd0 hc hc_nc
      have ha'_prop : a' ≠ 0 ∧ a' ≠ d := (nrmD_const_iff hd u a).2 ha_nc
      have hc'_prop : c' ≠ 0 ∧ c' ≠ d := (nrmD_const_iff hd u c).2 hc_nc
      have hne_ac : a' ≠ c' := by
        intro heq
        have hz_eq : opD d op' a' a' = a' ∨ opD d op' a' a' = 0 := by
          rcases allowed_cases hop' with rfl | rfl | ⟨_, rfl⟩ | ⟨_, rfl⟩
          · left; apply Nat.eq_of_testBit_eq; intro i
            have hm := congrArg (fun v => v.testBit i) (nrmD_mask u d a)
            change (a' &&& d).testBit i = a'.testBit i at hm
            simp only [opD, andD, Nat.testBit_and] at hm ⊢
            cases hd' : d.testBit i <;> cases ha' : a'.testBit i <;> simp_all
          · left; apply Nat.eq_of_testBit_eq; intro i
            have hm := congrArg (fun v => v.testBit i) (nrmD_mask u d a)
            change (a' &&& d).testBit i = a'.testBit i at hm
            simp only [opD, orD, Nat.testBit_and, Nat.testBit_or] at hm ⊢
            cases hd' : d.testBit i <;> cases ha' : a'.testBit i <;> simp_all
          · right; apply Nat.eq_of_testBit_eq; intro i
            have hdi := congrArg (fun v => v.testBit i) hd
            simp only [opD, andD, negD, Nat.testBit_and, Nat.testBit_xor, Nat.zero_testBit] at hdi ⊢
            cases hd' : d.testBit i <;> cases ha' : a'.testBit i <;> simp_all
          · right; apply Nat.eq_of_testBit_eq; intro i
            have hdi := congrArg (fun v => v.testBit i) hd
            simp only [opD, andD, negD, Nat.testBit_and, Nat.testBit_xor, Nat.zero_testBit] at hdi ⊢
            cases hd' : d.testBit i <;> cases ha' : a'.testBit i <;> simp_all
        have hez' : z = opD d op' a' a' := by
          have : z = opD d op' a' c' := hez
          rw [← heq] at this; exact this
        rcases hz_eq with e | e
        · exact hzb ((hez'.trans e).symm ▸ ha'_mem)
        · exact hzp.1 (hez'.trans e)
      set rest := ws.erase z
      have hrest_nd : rest.Nodup := hnd.erase z
      have hrest_sub : ∀ w ∈ rest, w ∈ b.map (nrmD u d) := by
        intro w hw
        have ⟨hne, hm⟩ := hnd.mem_erase_iff.1 hw
        rcases List.mem_cons.1 (hsub w hm) with rfl | hmb
        · exact absurd rfl hne
        · exact hmb
      have hrest_prop : ∀ w ∈ rest, w ≠ 0 ∧ w ≠ d := fun w hw => hprop w (List.mem_of_mem_erase hw)
      have hp1 : ws.Perm (z :: rest) := List.perm_cons_erase hzm
      have h1 : RunD u d Y k (opD d op' a' c' :: rest) := by
        rw [← hez]; exact Run.perm hp1 h
      set ka := decide (a' ∈ rest)
      set kb := decide (c' ∈ rest)
      set tail := (rest.erase a').erase c'
      have htail_nd : tail.Nodup := (hrest_nd.erase a').erase c'
      have hna_tail : a' ∉ tail := by
        intro hm; exact hrest_nd.not_mem_erase (List.mem_of_mem_erase hm)
      have hnc_tail : c' ∉ tail := (hrest_nd.erase a').not_mem_erase
      have hna_mid : a' ∉ kept kb c' tail := by
        rw [mem_kept]; rintro (⟨_, h⟩ | h)
        · exact hne_ac h
        · exact hna_tail h
      have hrest_perm : rest.Perm (kept ka a' (kept kb c' tail)) := by
        refine (List.perm_ext_iff_of_nodup hrest_nd (nodup_kept ka a' _ (nodup_kept kb c' _ htail_nd hnc_tail) hna_mid)).2 ?_
        intro x
        rw [mem_kept, mem_kept, (hrest_nd.erase a').mem_erase_iff, hrest_nd.mem_erase_iff]
        by_cases hxa : x = a' <;> by_cases hxc : x = c' <;> by_cases hxr : x ∈ rest <;>
          simp_all [ka, kb]
      have h2 := Run.perm (hrest_perm.cons _) h1
      have hne0 : opD d op' a' c' ≠ 0 := fun h0 => hzp.1 (hez.trans h0)
      have hned : opD d op' a' c' ≠ d := fun h1 => hzp.2 (hez.trans h1)
      have hnm : opD d op' a' c' ∉ (a' :: c' :: tail) := by
        rw [← hez, List.mem_cons, List.mem_cons]; rintro (e | e | hm)
        · exact hzb (by simpa [z, e] using ha'_mem)
        · exact hzb (by simpa [z, e] using hc'_mem)
        · exact hnd.not_mem_erase (List.mem_of_mem_erase (List.mem_of_mem_erase hm))
      have h3 : RunD u d Y (k + 1) (a' :: c' :: tail) := Run.two op' ka kb hop' hne0 hned hnm h2
      have hnd3 : (a' :: c' :: tail).Nodup :=
        List.nodup_cons.2 ⟨by simp [hne_ac, hna_tail], List.nodup_cons.2 ⟨hnc_tail, htail_nd⟩⟩
      refine ⟨k + 1, a' :: c' :: tail, le_rfl, hnd3, ?_, ?_, h3⟩
      · intro w hw; rcases List.mem_cons.1 hw with rfl | hw
        · exact ha'_prop
        · rcases List.mem_cons.1 hw with rfl | hw
          · exact hc'_prop
          · exact hrest_prop w (List.mem_of_mem_erase (List.mem_of_mem_erase hw))
      · intro w hw; rcases List.mem_cons.1 hw with rfl | hw
        · exact ha'_mem
        · rcases List.mem_cons.1 hw with rfl | hw
          · exact hc'_mem
          · exact hrest_sub w (List.mem_of_mem_erase (List.mem_of_mem_erase hw))
  · exact ⟨k, ws, by omega, hnd, hprop, fun w hw => by
      rcases List.mem_cons.1 (hsub w hw) with rfl | hm
      · exact absurd hw hzm
      · exact hm, h⟩

theorem reach_to_run_aux {u : Bool} {d : Nat} {roots : List Nat} {p bank}
    (hd : d &&& mask256 = d) (hd0 : d.testBit 0 = true)
    (hr : NatReach u d roots p bank) :
    ∀ {Y k ws}, ws.Nodup → (∀ w ∈ ws, w ≠ 0 ∧ w ≠ d) →
      (∀ w ∈ ws, w ∈ bank.map (nrmD u d)) → RunD u d Y k ws →
      ∃ k' ws', k' ≤ p + k ∧ ws'.Nodup ∧ (∀ w ∈ ws', w ≠ 0 ∧ w ≠ d) ∧
        (∀ w ∈ ws', w ∈ roots.map (nrmD u d)) ∧ RunD u d Y k' ws' := by
  induction p generalizing bank with
  | zero =>
    intro Y k ws hnd hprop hsub hrun
    subst hr
    exact ⟨k, ws, by omega, hnd, hprop, hsub, hrun⟩
  | succ p ih =>
    intro Y k ws hnd hprop hsub hrun
    obtain ⟨b, a, c, op, hop, rfl, hrb, ha, hc⟩ := hr
    have hsub' : ∀ w ∈ ws, w ∈ nrmD u d (opD d op a c) :: b.map (nrmD u d) := by
      intro w hw; simpa [List.map_cons] using hsub w hw
    obtain ⟨k1, ws1, hk1, hnd1, hprop1, hsub1, hrun1⟩ := pull_two hd hd0 hnd hprop hrun op hop ha hc hsub'
    obtain ⟨k2, ws2, hk2, hnd2, hprop2, hsub2, hrun2⟩ := ih hrb hnd1 hprop1 hsub1 hrun1
    exact ⟨k2, ws2, by omega, hnd2, hprop2, hsub2, hrun2⟩

theorem reach_to_run {u : Bool} {d : Nat} {roots : List Nat} {T : Nat} {p bank}
    (hd : d &&& mask256 = d) (hd0 : d.testBit 0 = true)
    (hT0 : T.testBit 0 = false) (hR0 : roots.all (fun r => !r.testBit 0) = true)
    (hnc : ¬ IsConst d T) (hr : NatReach u d roots p bank) (ha : Avail u d bank T) :
    ∃ s ws, s ≤ p ∧ ws.Nodup ∧ (∀ w ∈ ws, w ∈ roots.map (· &&& d)) ∧ RunD u d (T &&& d) s ws := by
  have hTmem : T &&& d ∈ bank.map (nrmD u d) := by
    have := avail_nrm_mem hd hd0 ha hnc
    rwa [nrmD_of_bit0_false u d T hT0] at this
  have hprop : ∀ w ∈ [T &&& d], w ≠ 0 ∧ w ≠ d := by
    intro w hw; rw [List.mem_singleton.1 hw]
    exact ⟨fun e => hnc (Or.inl e), fun e => hnc (Or.inr e)⟩
  have hsub : ∀ w ∈ [T &&& d], w ∈ bank.map (nrmD u d) := by
    intro w hw; rw [List.mem_singleton.1 hw]; exact hTmem
  obtain ⟨s, ws, hs, hnd, _, hsub', hrun⟩ := reach_to_run_aux hd hd0 hr (List.nodup_singleton _) hprop hsub Run.done
  have hrmap : roots.map (nrmD u d) = roots.map (· &&& d) := by
    apply List.map_congr_left
    intro r hr_m
    have h0 := List.all_eq_true.1 hR0 r hr_m
    simp only [Bool.not_eq_true'] at h0
    exact nrmD_of_bit0_false u d r h0
  rw [hrmap] at hsub'
  exact ⟨s, ws, by omega, hnd, hsub', hrun⟩

-- Bit separation lemmas
theorem runD_bits {u d y s ws} (hd : d &&& mask256 = d) (h : RunD u d y s ws) (i j : Nat)
    (hi : d.testBit i = true) (hj : d.testBit j = true)
    (hw : ∀ w ∈ ws, w.testBit i = w.testBit j) : y.testBit i = y.testBit j := by
  have hmi : mask256.testBit i = true := by
    have := congrArg (fun v => v.testBit i) hd; simp [Nat.testBit_and, hi] at this; exact this
  have hmj : mask256.testBit j = true := by
    have := congrArg (fun v => v.testBit j) hd; simp [Nat.testBit_and, hj] at this; exact this
  induction h using Run.fold with
  | done => exact hw _ (by simp)
  | perm hp _ ih => exact ih (fun w h => hw w (hp.mem_iff.1 h))
  | two op ka kb hop _ _ _ _ ih =>
    apply ih; have ha := hw _ List.mem_cons_self; have hb := hw _ (List.mem_cons_of_mem _ List.mem_cons_self)
    intro w hm
    rcases List.mem_cons.1 hm with rfl | hr
    · rcases allowed_cases hop with rfl | rfl | ⟨_, rfl⟩ | ⟨_, rfl⟩ <;>
        simp [opD, andD, orD, negD, ha, hb, hi, hj, hmi, hmj]
    · rw [mem_kept, mem_kept] at hr
      rcases hr with ⟨_, rfl⟩ | ⟨_, rfl⟩ | hr
      · exact ha
      · exact hb
      · exact hw _ (List.mem_cons_of_mem _ (List.mem_cons_of_mem _ hr))

theorem runD_bits_le_mono {d y s ws} (h : RunD false d y s ws) (i j : Nat)
    (hi : d.testBit i = true) (hj : d.testBit j = true)
    (hw : ∀ w ∈ ws, w.testBit i ≤ w.testBit j) : y.testBit i ≤ y.testBit j := by
  induction h using Run.fold with
  | done => exact hw _ (by simp)
  | perm hp _ ih => exact ih (fun w h => hw w (hp.mem_iff.1 h))
  | two op ka kb hop _ _ _ _ ih =>
    apply ih; have ha := hw _ List.mem_cons_self; have hb := hw _ (List.mem_cons_of_mem _ List.mem_cons_self)
    intro w hm
    rcases List.mem_cons.1 hm with rfl | hr
    · rcases allowed_cases hop with rfl | rfl | ⟨h, _⟩ | ⟨h, _⟩
      · simp only [opD, andD, beq_self_eq_true, ite_true, Nat.testBit_and, hi, hj, Bool.and_true]; grind
      · simp only [opD, orD, beq_self_eq_true, ite_true, ite_false, Nat.testBit_and, Nat.testBit_or, hi, hj, Bool.and_true]; grind
      · contradiction
      · contradiction
    · rw [mem_kept, mem_kept] at hr
      rcases hr with ⟨_, rfl⟩ | ⟨_, rfl⟩ | hr
      · exact ha
      · exact hb
      · exact hw _ (List.mem_cons_of_mem _ (List.mem_cons_of_mem _ hr))

theorem lower_base {u : Bool} {d : Nat} {roots : List Nat} {T : Nat} (h : availB u d roots T = false) :
    Lower u d roots T 1 := by
  intro p bank hr ha
  cases p with
  | zero =>
    dsimp only [NatReach] at hr; rw [hr] at ha
    have ht := (availB_iff u d roots T).2 ha
    rw [h] at ht; contradiction
  | succ p => omega

-- moveBits & lower_iso
def moveBits (tag d w : Nat) : Nat :=
  ((w &&& tag) <<< d) ||| ((w >>> d) &&& tag) |||
    (w ^^^ ((w &&& tag) ||| (w &&& (tag <<< d))))

theorem moved (tag d i w : Nat) (h : (tag &&& (tag <<< d)) = 0) :
    (moveBits tag d w).testBit i =
      (if tag.testBit i then w.testBit (d + i)
       else if (tag <<< d).testBit i then w.testBit (i - d) else w.testBit i) := by
  have ht := congrArg (fun v : Nat => v.testBit i) h
  simp only [Nat.testBit_and, Nat.zero_testBit] at ht
  simp only [moveBits, Nat.testBit_or, Nat.testBit_shiftLeft, Nat.testBit_and,
    Nat.testBit_shiftRight, Nat.testBit_xor] at *
  by_cases hi : d ≤ i <;> simp [hi] at * <;> grind

theorem move_hom (tag d : Nat) (h : (tag &&& (tag <<< d)) = 0) (a b : Nat) :
    moveBits tag d (a &&& b) = (moveBits tag d a &&& moveBits tag d b) ∧
    moveBits tag d (a ||| b) = (moveBits tag d a ||| moveBits tag d b) ∧
    moveBits tag d (a ^^^ b) = (moveBits tag d a ^^^ moveBits tag d b) := by
  refine ⟨?_, ?_, ?_⟩ <;> apply Nat.eq_of_testBit_eq <;> intro i <;>
    simp only [Nat.testBit_and, Nat.testBit_or, Nat.testBit_xor, moved tag d i _ h] <;>
    split_ifs <;> simp

theorem move_zero (tag d : Nat) (h : (tag &&& (tag <<< d)) = 0) : moveBits tag d 0 = 0 := by
  apply Nat.eq_of_testBit_eq; intro i; rw [moved tag d i 0 h]; split_ifs <;> simp

def applyMoves (ms : List (Nat × Nat)) (w : Nat) : Nat :=
  ms.foldl (fun acc p => moveBits p.1 p.2 acc) w

def moveOK256 (p : Nat × Nat) : Bool :=
  (p.1 &&& (p.1 <<< p.2) == 0) && (moveBits p.1 p.2 mask256 == mask256)

theorem applyMoves_hom (ms : List (Nat × Nat)) (hok : ms.all moveOK256 = true) :
    (∀ a b, applyMoves ms (a &&& b) = applyMoves ms a &&& applyMoves ms b) ∧
    (∀ a b, applyMoves ms (a ||| b) = applyMoves ms a ||| applyMoves ms b) ∧
    (∀ a b, applyMoves ms (a ^^^ b) = applyMoves ms a ^^^ applyMoves ms b) ∧
    applyMoves ms 0 = 0 ∧ applyMoves ms mask256 = mask256 := by
  induction ms with
  | nil => exact ⟨fun _ _ => rfl, fun _ _ => rfl, fun _ _ => rfl, rfl, rfl⟩
  | cons p ps ih =>
    simp only [List.all_cons, Bool.and_eq_true, moveOK256, beq_iff_eq] at hok
    obtain ⟨⟨hz, hm⟩, hps⟩ := hok
    obtain ⟨hand, hor, hxor, h0, h256⟩ := ih hps
    refine ⟨?_, ?_, ?_, ?_, ?_⟩
    · intro a b; simp only [applyMoves, List.foldl_cons, (move_hom p.1 p.2 hz a b).1]; exact hand _ _
    · intro a b; simp only [applyMoves, List.foldl_cons, (move_hom p.1 p.2 hz a b).2.1]; exact hor _ _
    · intro a b; simp only [applyMoves, List.foldl_cons, (move_hom p.1 p.2 hz a b).2.2]; exact hxor _ _
    · simp only [applyMoves, List.foldl_cons, move_zero p.1 p.2 hz]; exact h0
    · simp only [applyMoves, List.foldl_cons, hm]; exact h256

theorem move_invol (tag d w : Nat) (h : (tag &&& (tag <<< d)) = 0) :
    moveBits tag d (moveBits tag d w) = w := by
  apply Nat.eq_of_testBit_eq; intro i
  have ht := congrArg (fun v : Nat => v.testBit i) h
  simp only [Nat.testBit_and, Nat.zero_testBit] at ht
  rw [moved tag d i _ h]
  by_cases h1 : tag.testBit i = true
  · simp only [h1, ite_true, moved tag d (d + i) w h]
    have h2 : tag.testBit (d + i) = false := by
      have htd := congrArg (fun v : Nat => v.testBit (d + i)) h
      simp only [Nat.testBit_and, Nat.testBit_shiftLeft, Nat.zero_testBit] at htd
      have hge : d ≤ d + i := Nat.le_add_right d i
      have hsub : d + i - d = i := Nat.add_sub_cancel_left d i
      simp [hge, hsub, h1] at htd; exact htd
    have h3 : (tag <<< d).testBit (d + i) = true := by
      simp [Nat.testBit_shiftLeft, Nat.le_add_right, Nat.add_sub_cancel_left, h1]
    simp [h2, h3, Nat.add_sub_cancel_left]
  · simp only [h1, ite_false]
    by_cases h2 : (tag <<< d).testBit i = true
    · simp only [h2, ite_true, moved tag d (i - d) w h]
      rw [Nat.testBit_shiftLeft] at h2
      simp only [Bool.and_eq_true, decide_eq_true_eq] at h2
      simp [h2.2, Nat.add_sub_of_le h2.1]
    · simp [h1, h2, moved tag d i w h]

theorem applyMoves_inj (ms : List (Nat × Nat)) (hok : ms.all moveOK256 = true) :
    Function.Injective (applyMoves ms) := by
  induction ms with
  | nil => intro a b h; exact h
  | cons p ps ih =>
    simp only [List.all_cons, Bool.and_eq_true, moveOK256, beq_iff_eq] at hok
    intro a b h
    simp only [applyMoves, List.foldl_cons] at h
    have h1 := ih hok.2 h
    have := congrArg (moveBits p.1 p.2) h1
    rwa [move_invol p.1 p.2 a hok.1.1, move_invol p.1 p.2 b hok.1.1] at this

theorem applyMoves_opD (ms : List (Nat × Nat)) (hok : ms.all moveOK256 = true)
    {d1 d2 : Nat} (hd : applyMoves ms d2 = d1) (op a b : Nat) :
    applyMoves ms (opD d2 op a b) = opD d1 op (applyMoves ms a) (applyMoves ms b) := by
  obtain ⟨hand, hor, hxor, _, h256⟩ := applyMoves_hom ms hok
  unfold opD; split_ifs <;> simp only [andD, orD, negD, hand, hor, hxor, h256, hd]

theorem applyMoves_runD {u d Y s} (ms : List (Nat × Nat)) (hok : ms.all moveOK256 = true)
    (hd : applyMoves ms d = d) (hY : applyMoves ms Y = Y) {ws} (h : RunD u d Y s ws) :
    RunD u d Y s (ws.map (applyMoves ms)) := by
  obtain ⟨_, _, _, h0, _⟩ := applyMoves_hom ms hok
  have hinj := applyMoves_inj ms hok
  rw [← hY]
  induction h using Run.fold with
  | done => exact Run.done
  | perm hp _ ih => exact Run.perm (hp.map _) ih
  | @two s a b r op ka kb hop hne0 hned hnm _ ih =>
    have eop := applyMoves_opD ms hok hd op a b
    have e1 : (opD d op a b :: kept ka a (kept kb b r)).map (applyMoves ms) =
        opD d op (applyMoves ms a) (applyMoves ms b) ::
          kept ka (applyMoves ms a) (kept kb (applyMoves ms b) (r.map (applyMoves ms))) := by
      simp [kept_map, eop]
    rw [e1] at ih
    refine Run.two op ka kb hop ?_ ?_ ?_ ih
    · intro e; rw [← eop] at e; exact hne0 (hinj (e.trans h0.symm))
    · intro e; rw [← eop] at e; exact hned (hinj (e.trans hd.symm))
    · rw [← eop, ← List.map_cons, ← List.map_cons, List.mem_map]; rintro ⟨x, hx, he⟩; exact hnm (hinj he ▸ hx)

theorem reach_map_moves {u : Bool} (ms : List (Nat × Nat)) (hok : ms.all moveOK256 = true)
    {d1 d2 : Nat} (hd1 : d1 &&& mask256 = d1) (hd : applyMoves ms d2 = d1)
    {roots1 roots2 : List Nat} (hroots : ∀ r ∈ roots2, Avail u d1 roots1 (applyMoves ms r)) :
    ∀ {p bank}, NatReach u d2 roots2 p bank →
      ∃ bank', NatReach u d1 roots1 p bank' ∧ ∀ v ∈ bank, Avail u d1 bank' (applyMoves ms v) := by
  obtain ⟨hand, _, hxor, h0, h256⟩ := applyMoves_hom ms hok
  have hav : ∀ {b b' w}, (∀ v ∈ b, Avail u d1 b' (applyMoves ms v)) →
      Avail u d2 b w → Avail u d1 b' (applyMoves ms w) := by
    intro b b' w hbb hw
    rcases hw with (hz | h1) | ⟨v, hv, he⟩ | ⟨rfl, v, hv, he⟩
    · exact Or.inl (Or.inl (by rw [← hd, ← hand, hz, h0]))
    · exact Or.inl (Or.inr (by rw [← hd, ← hand, h1]))
    · have hve : applyMoves ms v &&& d1 = applyMoves ms w &&& d1 := by rw [← hd, ← hand, ← hand, he]
      exact avail_of_eq hve (hbb v hv)
    · have hve : applyMoves ms v &&& d1 = negD d1 (applyMoves ms w) &&& d1 := by
        rw [← hd, ← hand, he]; simp only [negD, hand, hxor, h256, hd, Nat.and_assoc, Nat.and_self]
      have hneg := avail_neg hd1 (avail_of_eq hve (hbb v hv))
      exact avail_of_eq (by rw [negD_invol hd1, Nat.and_assoc, Nat.and_self]) hneg
  intro p
  induction p with
  | zero =>
    intro bank hr; subst hr
    exact ⟨roots1, rfl, hroots⟩
  | succ p ih =>
    intro bank hr
    obtain ⟨b, a, c, op, hop, rfl, hrb, ha, hc⟩ := hr
    obtain ⟨b', hrb', hbb⟩ := ih hrb
    have ha' := hav hbb ha; have hc' := hav hbb hc
    refine ⟨opD d1 op (applyMoves ms a) (applyMoves ms c) :: b',
      ⟨b', applyMoves ms a, applyMoves ms c, op, hop, rfl, hrb', ha', hc'⟩, ?_⟩
    intro v hv; rcases List.mem_cons.1 hv with rfl | hv
    · exact Or.inr (Or.inl ⟨opD d1 op (applyMoves ms a) (applyMoves ms c), List.mem_cons_self, by
        rw [applyMoves_opD ms hok hd]⟩)
    · exact avail_cons _ _ (hbb v hv)

theorem lower_iso {u : Bool} {d1 d2 T1 T2 L : Nat} {roots1 roots2 : List Nat}
    (ms : List (Nat × Nat)) (hok : ms.all moveOK256 = true)
    (hd1 : d1 &&& mask256 = d1) (hd : applyMoves ms d2 = d1) (hT : applyMoves ms T2 = T1)
    (hroots : roots2.all (fun r => availB u d1 roots1 (applyMoves ms r)) = true)
    (h1 : Lower u d1 roots1 T1 L) : Lower u d2 roots2 T2 L := by
  obtain ⟨hand, _, hxor, h0, h256⟩ := applyMoves_hom ms hok
  have hr : ∀ r ∈ roots2, Avail u d1 roots1 (applyMoves ms r) := fun r hr =>
    (availB_iff u _ _ _).1 (List.all_eq_true.1 hroots r hr)
  intro p bank hreach ha
  obtain ⟨bank', hrb', hbb⟩ := reach_map_moves ms hok hd1 hd hr hreach
  apply h1 p bank' hrb'
  rcases ha with (hz | ho) | ⟨v, hv, he⟩ | ⟨rfl, v, hv, he⟩
  · exact Or.inl (Or.inl (by rw [← hT, ← hd, ← hand, hz, h0]))
  · exact Or.inl (Or.inr (by rw [← hT, ← hd, ← hand, ho]))
  · have hve : applyMoves ms v &&& d1 = T1 &&& d1 := by rw [← hT, ← hd, ← hand, ← hand, he]
    exact avail_of_eq hve (hbb v hv)
  · have hve : applyMoves ms v &&& d1 = negD d1 T1 &&& d1 := by
      rw [← hT, ← hd, ← hand, he]; simp only [negD, hand, hxor, h256, hd, Nat.and_assoc, Nat.and_self]
    have hneg := avail_neg hd1 (avail_of_eq hve (hbb v hv))
    exact avail_of_eq (by rw [negD_invol hd1, Nat.and_assoc, Nat.and_self]) hneg

-- lower_slice
def pairOK (d T : Nat) (p : Nat × Nat) : Bool :=
  d.testBit p.1 && d.testBit p.2 && (T.testBit p.1 != T.testBit p.2)

def essOK (d T : Nat) (roots : List Nat) (a : Nat) (p : Nat × Nat) : Bool :=
  pairOK d T p && roots.all (fun v => (v == a) || (v.testBit p.1 == v.testBit p.2))

theorem countP_ge_sublist (p : Nat → Bool) {xs ys : List Nat}
    (hnd : xs.Nodup) (hsub : ∀ a ∈ xs, a ∈ ys) (hall : ∀ a ∈ xs, p a = true) :
    xs.length ≤ ys.countP p := by
  induction xs generalizing ys with
  | nil => simp
  | cons a xs ih =>
    have ⟨hna, hnd'⟩ := List.nodup_cons.1 hnd
    have ham : a ∈ ys := hsub a List.mem_cons_self
    have hperm : ys.Perm (a :: ys.erase a) := List.perm_cons_erase ham
    rw [hperm.countP_eq, List.countP_cons, hall a List.mem_cons_self]
    have ih' := ih hnd' (fun x hx => by
      have hne : x ≠ a := fun e => hna (e ▸ hx)
      exact (List.mem_erase_of_ne hne).2 (hsub x (List.mem_cons_of_mem _ hx)))
      (fun x hx => hall x (List.mem_cons_of_mem _ hx))
    simp only [ite_true, List.length_cons]
    omega

theorem lower_slice {u : Bool} {d dSub T TSub L : Nat} {roots rootsSub : List Nat}
    (hd : d &&& mask256 = d) (hd0 : d.testBit 0 = true)
    (hT0 : T.testBit 0 = false) (hR0 : roots.all (fun r => !r.testBit 0) = true)
    (hdSub : dSub &&& mask256 = dSub) (hsub : dSub &&& d = dSub)
    (hT : T &&& dSub = TSub &&& dSub)
    (hnc : isConstB d T = false) (hncSub : isConstB dSub TSub = false)
    (hcov : roots.all (availB u dSub rootsSub) = true)
    (singles : List (Nat × Nat × Nat))
    (hs_nd : (singles.map Prod.fst).Nodup)
    (hs_ok : singles.all (fun e => isConstB dSub e.1 && essOK d (T &&& d) (roots.map (· &&& d)) e.1 e.2) = true)
    (hprior : Lower u dSub rootsSub TSub L) :
    Lower u d roots T (L + singles.length) := by
  have hnc' : ¬ IsConst d T := fun h => by rw [(isConstB_iff _ _).2 h] at hnc; contradiction
  have hncSub' : ¬ IsConst dSub (T &&& d) := by
    intro h
    have e : (T &&& d) &&& dSub = TSub &&& dSub := by
      rw [Nat.and_assoc, Nat.and_comm d dSub, hsub, hT]
    rcases h with h0 | h1
    · exact absurd ((isConstB_iff _ _).2 (Or.inl (e.symm.trans h0))) (by simp [hncSub])
    · exact absurd ((isConstB_iff _ _).2 (Or.inr (e.symm.trans h1))) (by simp [hncSub])
  intro p bank hr ha
  obtain ⟨s, ws, hs_le, hnd, hws_sub, hrun⟩ := reach_to_run hd hd0 hT0 hR0 hnc' hr ha
  have hws_av : ∀ w ∈ ws, Avail u dSub rootsSub w := by
    intro w hw
    obtain ⟨r, hr_m, rfl⟩ := List.mem_map.1 (hws_sub w hw)
    have hav := (availB_iff u _ _ _).1 (List.all_eq_true.1 hcov r hr_m)
    exact avail_of_eq (by rw [Nat.and_assoc, Nat.and_comm d dSub, hsub]) hav
  obtain ⟨q, next, hq, ht, hle⟩ := contraction hdSub hsub hncSub' hrun (p := 0) (bank := rootsSub) rfl hws_av
  have hTSub_av : Avail u dSub next TSub := avail_of_eq (by
    rw [Nat.and_assoc, Nat.and_comm d dSub, hsub, hT]) ht
  have hL : L ≤ q := hprior q next hq hTSub_av
  have hsin_mem : ∀ a ∈ singles.map Prod.fst, a ∈ ws := by
    intro a ha
    obtain ⟨⟨a', r1, r2⟩, hm, rfl⟩ := List.mem_map.1 ha
    have hok := List.all_eq_true.1 hs_ok (a', r1, r2) hm
    simp only [Bool.and_eq_true, essOK, pairOK, bne_iff_ne, List.all_eq_true, Bool.or_eq_true, beq_iff_eq] at hok
    obtain ⟨_, ⟨⟨hr1, hr2⟩, hdiff⟩, hiso⟩ := hok
    by_contra hnot
    apply hdiff
    apply runD_bits hd hrun r1 r2 hr1 hr2
    intro w hw
    rcases hiso w (hws_sub w hw) with rfl | heq
    · exact absurd hw hnot
    · exact heq
  have hsin_const : ∀ a ∈ singles.map Prod.fst, isConstB dSub a = true := by
    intro a ha
    obtain ⟨⟨a', r1, r2⟩, hm, rfl⟩ := List.mem_map.1 ha
    have hok := List.all_eq_true.1 hs_ok _ hm
    simp only [Bool.and_eq_true] at hok
    exact hok.1
  have hcnt := countP_ge_sublist (isConstB dSub) hs_nd hsin_mem hsin_const
  simp only [List.length_map] at hcnt
  omega

-- poolCut (52-bit compact hint)
def runChoices (u : Bool) (d : Nat) (pool : List Nat) : Nat → Nat → Option (List Nat)
  | 0, _ => some pool
  | p + 1, bits =>
    let code := bits &&& 1023
    let op := code &&& 3
    let ia := (code >>> 2) &&& 15
    let ib := (code >>> 6) &&& 15
    if allowedB u op && ia < pool.length && ib < pool.length then
      let a := pool.getD ia 0
      let b := pool.getD ib 0
      runChoices u d (pool ++ [opD d op a b]) p (bits >>> 10)
    else none

theorem getD_mem {xs : List Nat} {i : Nat} (hi : i < xs.length) : xs.getD i 0 ∈ xs := by
  rw [List.getD_eq_getElem?_getD, List.getElem?_eq_getElem hi, Option.getD_some]
  exact List.getElem_mem hi

theorem runChoices_sound {u : Bool} {d : Nat} {roots : List Nat} :
    ∀ (p bits q : Nat) (bank pool result : List Nat),
      NatReach u d roots q bank →
      (∀ v ∈ pool, Avail u d bank v) →
      runChoices u d pool p bits = some result →
      ∃ bank', NatReach u d roots (q + p) bank' ∧ ∀ v ∈ result, Avail u d bank' v
  | 0, _, q, bank, pool, result, hr, hsup, hok => by
    simp only [runChoices, Option.some.injEq] at hok; subst hok; exact ⟨bank, hr, hsup⟩
  | p + 1, bits, q, bank, pool, result, hr, hsup, hok => by
    simp only [runChoices] at hok
    split at hok
    · rename_i hcond
      simp only [Bool.and_eq_true, decide_eq_true_eq] at hcond
      obtain ⟨⟨hop, hia⟩, hib⟩ := hcond
      set code := bits &&& 1023
      set op := code &&& 3
      set ia := (code >>> 2) &&& 15
      set ib := (code >>> 6) &&& 15
      set a := pool.getD ia 0
      set b := pool.getD ib 0
      set w := opD d op a b
      have ha : Avail u d bank a := hsup a (getD_mem hia)
      have hb : Avail u d bank b := hsup b (getD_mem hib)
      have hr1 : NatReach u d roots (q + 1) (w :: bank) := ⟨bank, a, b, op, hop, rfl, hr, ha, hb⟩
      have hsup1 : ∀ v ∈ pool ++ [w], Avail u d (w :: bank) v := by
        intro v hv; rcases List.mem_append.1 hv with hv | hv
        · exact avail_cons _ _ (hsup v hv)
        · rw [List.mem_singleton.1 hv]; exact Or.inr (Or.inl ⟨w, List.mem_cons_self, rfl⟩)
      obtain ⟨bank', hrb', hsb'⟩ := runChoices_sound p (bits >>> 10) (q + 1) (w :: bank) (pool ++ [w]) result hr1 hsup1 hok
      exact ⟨bank', by simpa [Nat.add_assoc, Nat.add_comm 1] using hrb', hsb'⟩
    · contradiction

def checkCutEntry (u : Bool) (dSub : Nat) (rootsSub : List Nat) (LSub s : Nat) (ws : List Nat) (hint : Nat) : Bool :=
  let p := (hint >>> 8) &&& 15
  decide (s + p < LSub + ws.countP (isConstB dSub)) &&
  match runChoices u dSub rootsSub p (hint >>> 12) with
  | none => false
  | some pool => ws.all (availB u dSub pool)

theorem checkCutEntry_sound {u : Bool} {d dSub T TSub LSub s : Nat} {rootsSub ws : List Nat}
    (hdSub : dSub &&& mask256 = dSub) (hsub : dSub &&& d = dSub)
    (hT : T &&& dSub = TSub &&& dSub) (hncSub : isConstB dSub TSub = false)
    (hprior : Lower u dSub rootsSub TSub LSub) (hint : Nat)
    (hchk : checkCutEntry u dSub rootsSub LSub s ws hint = true) :
    ¬ RunD u d (T &&& d) s ws := by
  intro hrun
  simp only [checkCutEntry, Bool.and_eq_true, decide_eq_true_eq] at hchk
  obtain ⟨hineq, hmatch⟩ := hchk
  cases hrc : runChoices u dSub rootsSub ((hint >>> 8) &&& 15) (hint >>> 12) with
  | none => rw [hrc] at hmatch; contradiction
  | some pool =>
    rw [hrc] at hmatch
    have hsup0 : ∀ v ∈ rootsSub, Avail u dSub rootsSub v := fun v hv => Or.inr (Or.inl ⟨v, hv, rfl⟩)
    obtain ⟨bank, hrb, hsb⟩ := runChoices_sound _ _ 0 rootsSub rootsSub pool rfl hsup0 hrc
    simp only [Nat.zero_add] at hrb
    have hws_av : ∀ w ∈ ws, Avail u dSub bank w := by
      intro w hw
      have hav := (availB_iff u _ _ _).1 (List.all_eq_true.1 hmatch w hw)
      rcases hav with hc | ⟨v, hv, he⟩ | ⟨rfl, v, hv, he⟩
      · exact Or.inl hc
      · exact avail_of_eq he (hsb v hv)
      · have hneg := avail_neg hdSub (hsb v hv)
        have he' : negD dSub v &&& dSub = w &&& dSub := by
          rw [← negD_mask, he, negD_invol hdSub, Nat.and_assoc, Nat.and_self]
        exact avail_of_eq he' hneg
    have hnc' : ¬ IsConst dSub (T &&& d) := by
      intro h; have e : (T &&& d) &&& dSub = TSub &&& dSub := by rw [Nat.and_assoc, Nat.and_comm d dSub, hsub, hT]
      rcases h with h0 | h1
      · exact absurd ((isConstB_iff _ _).2 (Or.inl (e.symm.trans h0))) (by simp [hncSub])
      · exact absurd ((isConstB_iff _ _).2 (Or.inr (e.symm.trans h1))) (by simp [hncSub])
    obtain ⟨q, next, hq, ht, hle⟩ := contraction hdSub hsub hnc' hrun hrb hws_av
    have hL := hprior q next hq (avail_of_eq (by rw [Nat.and_assoc, Nat.and_comm d dSub, hsub, hT]) ht)
    omega

-- covers, eval6, hw256, hk, bsr, bar, bar_all
def coversP (u : Bool) (pairs : List (Nat × Nat)) (ws : List Nat) : Bool :=
  if !u then
    pairs.all (fun p => ws.any (fun w => !w.testBit p.1 && w.testBit p.2))
  else
    pairs.all (fun p => ws.any (fun w => w.testBit p.1 != w.testBit p.2))

theorem coversP_ok {u : Bool} {d T s : Nat} (hd : d &&& mask256 = d)
    (pairs : List (Nat × Nat))
    (hpairs : pairs.all (fun p => d.testBit p.1 && d.testBit p.2 && !(T &&& d).testBit p.1 && (T &&& d).testBit p.2) = true)
    {ws : List Nat} (h : RunD u d (T &&& d) s ws) : coversP u pairs ws = true := by
  cases u with
  | false =>
    simp only [coversP, Bool.not_false, ite_true, List.all_eq_true, List.any_eq_true]
    intro ⟨u1, v1⟩ hm
    have hp := List.all_eq_true.1 hpairs (u1, v1) hm
    simp only [Bool.and_eq_true, Bool.not_eq_true'] at hp
    by_contra! hall
    have hle := runD_bits_le_mono h v1 u1 hp.1.1.2 hp.1.1.1 (fun w hw => by
      have hbad := hall w hw
      cases hu : w.testBit u1 <;> cases hv : w.testBit v1 <;> simp_all)
    rw [hp.1.2, hp.2] at hle; contradiction
  | true =>
    simp only [coversP, Bool.not_true, Bool.false_eq_true, ite_false, List.all_eq_true, List.any_eq_true, bne_iff_ne]
    intro ⟨u1, v1⟩ hm
    have hp := List.all_eq_true.1 hpairs (u1, v1) hm
    simp only [Bool.and_eq_true, Bool.not_eq_true'] at hp
    by_contra! hall
    have heq := runD_bits hd h u1 v1 hp.1.1.1 hp.1.1.2 hall
    rw [hp.1.2, hp.2] at heq; contradiction

def unorientedCov (pairs : List (Nat × Nat)) (ws : List Nat) : Bool :=
  pairs.all (fun p => ws.any (fun w => w.testBit p.1 != w.testBit p.2))

theorem unorientedCov_ok {u : Bool} {d T s : Nat} (hd : d &&& mask256 = d)
    (pairs : List (Nat × Nat))
    (hpairs : pairs.all (fun p => d.testBit p.1 && d.testBit p.2 && !(T &&& d).testBit p.1 && (T &&& d).testBit p.2) = true)
    {ws : List Nat} (h : RunD u d (T &&& d) s ws) : unorientedCov pairs ws = true := by
  simp only [unorientedCov, List.all_eq_true, List.any_eq_true, bne_iff_ne]
  intro ⟨u1, v1⟩ hm
  have hp := List.all_eq_true.1 hpairs (u1, v1) hm
  simp only [Bool.and_eq_true, Bool.not_eq_true'] at hp
  by_contra! hall
  have heq := runD_bits hd h u1 v1 hp.1.1.1 hp.1.1.2 hall
  rw [hp.1.2, hp.2] at heq; contradiction

-- Fast bitmask-decorated covers
def maskP (m : Nat) : Nat := 2 ^ m - 1

def projBit (rs : List Nat) (w : Nat) : Nat :=
  rs.foldr (fun r acc => (acc <<< 1) ||| (if w.testBit r then 1 else 0)) 0

theorem projBit_testBit (rs : List Nat) (w : Nat) (i : Nat) :
    (projBit rs w).testBit i = if h : i < rs.length then w.testBit rs[i] else false := by
  induction rs generalizing i with
  | nil => simp [projBit]
  | cons r rs ih =>
    cases i with
    | zero =>
      simp only [projBit, List.foldr_cons, Nat.testBit_or, Nat.testBit_shiftLeft,
        Nat.not_le.2 Nat.zero_lt_one, decide_false, Bool.false_and, Bool.false_or,
        List.length_cons, Nat.zero_lt_succ, dite_true, List.getElem_cons_zero]
      cases w.testBit r <;> simp
    | succ i =>
      simp only [projBit, List.foldr_cons, Nat.testBit_or, Nat.testBit_shiftLeft,
        Nat.succ_le_succ (Nat.zero_le i), decide_true, Bool.true_and, Nat.add_sub_cancel,
        List.length_cons, Nat.succ_lt_succ_iff, List.getElem_cons_succ]
      have h1 : (if w.testBit r = true then 1 else 0).testBit (i + 1) = false := by
        cases w.testBit r <;> simp [Nat.testBit_succ]
      rw [h1, Bool.or_false]; exact ih i

def opP (mp op : Nat) (pa pb : Nat) : Nat :=
  if op == 0 then pa &&& pb
  else if op == 1 then pa ||| pb
  else if op == 2 then pa &&& (pb ^^^ mp)
  else (pa ^^^ mp) &&& pb

theorem projBit_opD {dm : Nat} (hd : dm &&& mask256 = dm) {rs : List Nat}
    (hrs : ∀ r ∈ rs, dm.testBit r = true) (op a b : Nat) :
    projBit rs (opD dm op a b) = opP (maskP rs.length) op (projBit rs a) (projBit rs b) := by
  apply Nat.eq_of_testBit_eq; intro i
  by_cases hi : i < rs.length
  · have hdr := hrs rs[i] (List.getElem_mem hi)
    have hmr : mask256.testBit rs[i] = true := by
      have := congrArg (fun v => v.testBit rs[i]) hd; simp [Nat.testBit_and, hdr] at this; exact this
    unfold opD opP
    split_ifs <;>
      simp only [projBit_testBit, hi, dite_true, andD, orD, negD, Nat.testBit_and, Nat.testBit_or, Nat.testBit_xor,
        maskP, Nat.testBit_two_pow_sub_one, decide_true, hdr, hmr, Bool.and_true, Bool.xor_true] <;>
      (cases a.testBit rs[i] <;> cases b.testBit rs[i] <;> rfl)
  · unfold opD opP
    split_ifs <;>
      simp only [projBit_testBit, hi, dite_false, Nat.testBit_and, Nat.testBit_or, Nat.testBit_xor,
        maskP, Nat.testBit_two_pow_sub_one, decide_false, Bool.false_and, Bool.and_false, Bool.false_or, Bool.xor_false]

theorem foldl_or_testBit {α : Type} (g : α → Nat) (xs : List α) (acc i : Nat) :
    (xs.foldl (fun a x => a ||| g x) acc).testBit i = (acc.testBit i || xs.any (fun x => (g x).testBit i)) := by
  induction xs generalizing acc with
  | nil => simp
  | cons x xs ih =>
    simp only [List.foldl_cons, ih, Nat.testBit_or, List.any_cons, Bool.or_assoc]

def colB (mp : Nat) (oriented : Bool) (p : Nat × Nat) : Nat :=
  if oriented then (p.1 ^^^ mp) &&& p.2 else p.1 ^^^ p.2

def coversD (u : Bool) (mp : Nat) (dws : List (Nat × Nat × Nat)) : Bool :=
  dws.foldl (fun acc d => acc ||| colB mp (!u) d.2) 0 == mp

theorem coversD_eq (u : Bool) (pairs : List (Nat × Nat)) (ws : List Nat) :
    coversD u (maskP pairs.length) (ws.map (fun w => (w, projBit (pairs.map Prod.fst) w, projBit (pairs.map Prod.snd) w))) =
      coversP u pairs ws := by
  set r1s := pairs.map Prod.fst
  set r2s := pairs.map Prod.snd
  set mp := maskP pairs.length
  have hr1 : r1s.length = pairs.length := List.length_map _
  have hr2 : r2s.length = pairs.length := List.length_map _
  unfold coversD coversP
  cases u with
  | false =>
    simp only [Bool.not_false, colB, ite_true]
    apply Bool.eq_iff_iff.2; rw [beq_iff_eq, List.all_eq_true]
    constructor
    · intro heq pr hpr
      obtain ⟨i, hi, rfl⟩ := List.mem_iff_getElem.1 hpr
      have hb := congrArg (fun v => v.testBit i) heq
      rw [foldl_or_testBit, Nat.zero_testBit, Bool.false_or, List.any_map] at hb
      simp only [mp, maskP, Nat.testBit_two_pow_sub_one, hi, decide_true] at hb
      obtain ⟨w, hw, hwt⟩ := List.any_eq_true.1 hb
      simp only [Function.comp_def, Nat.testBit_and, Nat.testBit_xor, projBit_testBit, hr1, hr2, hi, dite_true,
        Nat.testBit_two_pow_sub_one, decide_true, Bool.xor_true] at hwt
      exact List.any_eq_true.2 ⟨w, hw, by simpa [r1s, r2s] using hwt⟩
    · intro hall
      apply Nat.eq_of_testBit_eq; intro i
      rw [foldl_or_testBit, Nat.zero_testBit, Bool.false_or, List.any_map]
      simp only [mp, maskP, Nat.testBit_two_pow_sub_one]
      by_cases hi : i < pairs.length
      · simp only [hi, decide_true]
        obtain ⟨w, hw, hwt⟩ := List.any_eq_true.1 (hall pairs[i] (List.getElem_mem hi))
        exact List.any_eq_true.2 ⟨w, hw, by
          simp only [Function.comp_def, Nat.testBit_and, Nat.testBit_xor, projBit_testBit, hr1, hr2, hi, dite_true,
            Nat.testBit_two_pow_sub_one, decide_true, Bool.xor_true, r1s, r2s, List.getElem_map]
          exact hwt⟩
      · simp only [hi, decide_false, List.any_eq_false]
        intro w _
        simp only [Function.comp_def, Nat.testBit_and, Nat.testBit_xor, projBit_testBit, hr1, hr2, hi, dite_false,
          Nat.testBit_two_pow_sub_one, decide_false, Bool.xor_false, Bool.and_false, not_false_eq_true, Bool.false_eq_true]
  | true =>
    simp only [Bool.not_true, colB, Bool.false_eq_true, ite_false]
    apply Bool.eq_iff_iff.2; rw [beq_iff_eq, List.all_eq_true]
    constructor
    · intro heq pr hpr
      obtain ⟨i, hi, rfl⟩ := List.mem_iff_getElem.1 hpr
      have hb := congrArg (fun v => v.testBit i) heq
      rw [foldl_or_testBit, Nat.zero_testBit, Bool.false_or, List.any_map] at hb
      simp only [mp, maskP, Nat.testBit_two_pow_sub_one, hi, decide_true] at hb
      obtain ⟨w, hw, hwt⟩ := List.any_eq_true.1 hb
      simp only [Function.comp_def, Nat.testBit_xor, projBit_testBit, hr1, hr2, hi, dite_true] at hwt
      exact List.any_eq_true.2 ⟨w, hw, by simpa [r1s, r2s, bne] using hwt⟩
    · intro hall
      apply Nat.eq_of_testBit_eq; intro i
      rw [foldl_or_testBit, Nat.zero_testBit, Bool.false_or, List.any_map]
      simp only [mp, maskP, Nat.testBit_two_pow_sub_one]
      by_cases hi : i < pairs.length
      · simp only [hi, decide_true]
        obtain ⟨w, hw, hwt⟩ := List.any_eq_true.1 (hall pairs[i] (List.getElem_mem hi))
        exact List.any_eq_true.2 ⟨w, hw, by
          simp only [Function.comp_def, Nat.testBit_xor, projBit_testBit, hr1, hr2, hi, dite_true, r1s, r2s, List.getElem_map]
          simpa [bne] using hwt⟩
      · simp only [hi, decide_false, List.any_eq_false]
        intro w _
        simp only [Function.comp_def, Nat.testBit_xor, projBit_testBit, hr1, hr2, hi, dite_false,
          Bool.xor_false, Bool.false_eq_true, not_false_eq_true]

theorem erase_map_inj {α β : Type} [BEq α] [LawfulBEq α] [BEq β] [LawfulBEq β]
    (f : α → β) (hinj : Function.Injective f) (xs : List α) (a : α) :
    (xs.map f).erase (f a) = (xs.erase a).map f := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
    simp only [List.map_cons, List.erase_cons]
    by_cases h : x = a
    · subst h; simp
    · have hf : (f x == f a) = false := beq_false_of_ne (fun e => h (hinj e))
      have hx : (x == a) = false := beq_false_of_ne h
      simp [hf, hx, ih]

def value6 (a b c d e f : Bool) : Nat :=
  let x := b.toNat + c.toNat
  let y := (!e).toNat + (!f).toNat
  if a then (if d then y else max x (max y (x + y - 1))) else (if d then 0 else x)

theorem value6_and : ∀ a b c d e f g h i j l m : Bool,
    value6 (a && g) (b && h) (c && i) (d && j) (e && l) (f && m)
      ≤ value6 a b c d e f + value6 g h i j l m := by decide +kernel

theorem value6_or : ∀ a b c d e f g h i j l m : Bool,
    value6 (a || g) (b || h) (c || i) (d || j) (e || l) (f || m)
      ≤ value6 a b c d e f + value6 g h i j l m := by decide +kernel

theorem score_bound {d y s ws} (h : RunD false d y s ws) (hl : ws.length = s + 1)
    (v : Nat → Nat) (hand : ∀ a b, v (andD d a b) ≤ v a + v b)
    (hor : ∀ a b, v (orD d a b) ≤ v a + v b) : v y ≤ (ws.map v).sum := by
  induction h using Run.fold with
  | done => simp
  | perm p _ ih => rw [← (p.map v).sum_eq]; exact ih (p.length_eq.trans hl)
  | two op ka kb hop _ _ _ h ih =>
    have hh := run_len h; cases ka <;> cases kb <;> simp [kept] at hh hl <;> try omega
    have ih' := ih (by simp [kept]; omega)
    rcases allowed_cases hop with rfl | rfl | ⟨hc, _⟩ | ⟨hc, _⟩
    · simp only [opD, beq_self_eq_true, ite_true, kept, Bool.false_eq_true, ite_false, List.map_cons, List.sum_cons] at ih' ⊢
      grw [← Nat.add_assoc, ← hand]; exact ih'
    · simp only [opD, beq_self_eq_true, ite_true, ite_false, kept, Bool.false_eq_true, List.map_cons, List.sum_cons] at ih' ⊢
      grw [← Nat.add_assoc, ← hor]; exact ih'
    · contradiction
    · contradiction

def eval6 (a b c d e f v : Nat) := value6 (v.testBit a) (v.testBit b) (v.testBit c)
    (v.testBit d) (v.testBit e) (v.testBit f)

theorem eval6_bound {dm y s ws} (h : RunD false dm y s ws) (hl : ws.length = s + 1)
    (a b c d e f : Nat)
    (ha : dm.testBit a = true) (hb : dm.testBit b = true) (hc : dm.testBit c = true)
    (hd : dm.testBit d = true) (he : dm.testBit e = true) (hf : dm.testBit f = true) :
    eval6 a b c d e f y ≤ (ws.map (eval6 a b c d e f)).sum := by
  apply score_bound h hl
  · intro v w
    simpa only [eval6, andD, Nat.testBit_and, ha, hb, hc, hd, he, hf, Bool.and_true] using value6_and
      (v.testBit a) (v.testBit b) (v.testBit c) (v.testBit d) (v.testBit e) (v.testBit f)
      (w.testBit a) (w.testBit b) (w.testBit c) (w.testBit d) (w.testBit e) (w.testBit f)
  · intro v w
    simpa only [eval6, orD, Nat.testBit_and, Nat.testBit_or, ha, hb, hc, hd, he, hf, Bool.and_true] using value6_or
      (v.testBit a) (v.testBit b) (v.testBit c) (v.testBit d) (v.testBit e) (v.testBit f)
      (w.testBit a) (w.testBit b) (w.testBit c) (w.testBit d) (w.testBit e) (w.testBit f)

def sumBelow (v : Nat → Nat) : List Nat → Nat → Bool
  | [], n => n != 0
  | w :: ws, n => decide (v w < n) && sumBelow v ws (n - v w)

theorem sumBelow_iff (v : Nat → Nat) (ws : List Nat) (n : Nat) :
    sumBelow v ws n = true ↔ (ws.map v).sum < n := by
  induction ws generalizing n with
  | nil => simp [sumBelow]
  | cons w ws ih => rw [sumBelow, Bool.and_eq_true, decide_eq_true_eq, ih, List.map_cons, List.sum_cons]; omega

def scoreCheck (dm y s : Nat) (ws : List Nat) (code : Nat) : Bool :=
  let a := code &&& 255
  let b := (code >>> 8) &&& 255
  let c := (code >>> 16) &&& 255
  let d := (code >>> 24) &&& 255
  let e := (code >>> 32) &&& 255
  let f := (code >>> 40) &&& 255
  dm.testBit a && dm.testBit b && dm.testBit c && dm.testBit d && dm.testBit e && dm.testBit f &&
    ws.length == s + 1 && sumBelow (eval6 a b c d e f) ws (eval6 a b c d e f y)

theorem scoreCheck_no {dm y s ws} (h : RunD false dm y s ws) (code : Nat) :
    scoreCheck dm y s ws code = false := by
  unfold scoreCheck
  by_cases hok : dm.testBit (code &&& 255) = true ∧ dm.testBit ((code >>> 8) &&& 255) = true ∧
      dm.testBit ((code >>> 16) &&& 255) = true ∧ dm.testBit ((code >>> 24) &&& 255) = true ∧
      dm.testBit ((code >>> 32) &&& 255) = true ∧ dm.testBit ((code >>> 40) &&& 255) = true ∧
      ws.length = s + 1
  · obtain ⟨ha, hb, hc, hd, he, hf, hl⟩ := hok
    simp only [ha, hb, hc, hd, he, hf, hl, beq_self_eq_true, Bool.true_and]
    by_contra hbad
    have hsum := (sumBelow_iff _ _ _).1 (Bool.eq_true_of_not_eq_false hbad)
    exact (Nat.not_lt_of_ge (eval6_bound h hl _ _ _ _ _ _ ha hb hc hd he hf)) hsum
  · by_contra hbad
    have ht := Bool.eq_true_of_not_eq_false hbad
    simp only [Bool.and_eq_true, beq_iff_eq] at ht
    exact hok ⟨ht.1.1.1.1.1.1.1, ht.1.1.1.1.1.1.2, ht.1.1.1.1.1.2, ht.1.1.1.1.2, ht.1.1.1.2, ht.1.1.2, ht.1.2⟩

def scr (u : Bool) (dm y s : Nat) (pool : List Nat) (zs : List Nat) : Bool :=
  !u && zs.length == s + 1 && pool.any (scoreCheck dm y s zs)

theorem scr_no {u : Bool} {dm y s : Nat} (pool : List Nat) {zs : List Nat}
    (h : RunD u dm y s zs) : scr u dm y s pool zs = false := by
  cases u with
  | true => simp [scr]
  | false =>
    unfold scr; simp only [Bool.not_false, Bool.true_and]
    rw [Bool.and_eq_false_iff]; right; rw [List.any_eq_false]
    intro x _; rw [scoreCheck_no h x]; simp

def opsOf (u : Bool) : List Nat := if u then [0, 1, 2, 3] else [0, 1]

theorem mem_opsOf {u : Bool} {op : Nat} (hop : allowedB u op = true) : op ∈ opsOf u := by
  rcases allowed_cases hop with rfl | rfl | ⟨rfl, rfl⟩ | ⟨rfl, rfl⟩
  · cases u <;> decide
  · cases u <;> decide
  · decide
  · decide

def nextD (u : Bool) (dm : Nat) (slack : Nat) (ws : List Nat) (f : List Nat → Bool) : Bool :=
  ws.any fun a =>
    let ra := ws.erase a
    ra.any fun b =>
      a ≤ b && (let r := ra.erase b
        (opsOf u).any fun op =>
          let w := opD dm op a b
          w != 0 && w != dm && !(ws.contains w) &&
            (f (w :: r) || (slack ≥ 1 && (f (w :: a :: r) || f (w :: b :: r))) ||
              (slack ≥ 2 && f (w :: a :: b :: r))))

theorem nextD_two_sorted {u : Bool} {dm y a b rest} {op : Nat} {ka kb : Bool} {s ws}
    (hop : allowedB u op = true) (hab : a ≤ b)
    (p : (a :: b :: rest).Perm ws)
    (h0 : opD dm op a b ≠ 0) (hd : opD dm op a b ≠ dm) (hnm : opD dm op a b ∉ (a :: b :: rest))
    (h : RunD u dm y s (opD dm op a b :: kept ka a (kept kb b rest)))
    (f : List Nat → Bool) (hf : ∀ ys, RunD u dm y s ys → f ys = true) :
    nextD u dm (s + 2 - ws.length) ws f = true := by
  have ha := p.mem_iff.1 List.mem_cons_self
  have pp := (p.trans (List.perm_cons_erase ha)).cons_inv
  have hb := pp.mem_iff.1 List.mem_cons_self
  have pr := (pp.trans (List.perm_cons_erase hb)).cons_inv
  have hh := run_len h; have hl := p.length_eq; simp only [List.length_cons] at hl hh
  have hnc : ws.contains (opD dm op a b) = false := by
    cases h : ws.contains (opD dm op a b) with
    | false => rfl
    | true => exact absurd (p.mem_iff.2 (by simpa using h)) hnm
  have h0b : (opD dm op a b != 0) = true := bne_iff_ne.2 h0
  have hdb : (opD dm op a b != dm) = true := bne_iff_ne.2 hd
  apply List.any_eq_true.2 ⟨a, ha, ?_⟩
  apply List.any_eq_true.2 ⟨b, hb, ?_⟩
  rw [Bool.and_eq_true]; refine ⟨decide_eq_true hab, ?_⟩
  apply List.any_eq_true.2 ⟨op, mem_opsOf hop, ?_⟩
  simp only [h0b, hdb, hnc, Bool.not_false, Bool.true_and]
  have ht := hf _ (Run.perm ((keep_perm (keep_perm pr kb b) ka a).cons _) h)
  cases ka <;> cases kb <;> simp [kept] at ht hh <;>
    simp only [ht, Bool.true_or, Bool.or_true, Bool.and_true] <;>
    first | (simp [show 2 ≤ s + 2 - ws.length by omega]) | (simp [show 1 ≤ s + 2 - ws.length by omega])

theorem nextD_two {u : Bool} {dm y a b rest} {op : Nat} {ka kb : Bool} {s ws}
    (hop : allowedB u op = true) (p : (a :: b :: rest).Perm ws)
    (h0 : opD dm op a b ≠ 0) (hd : opD dm op a b ≠ dm) (hnm : opD dm op a b ∉ (a :: b :: rest))
    (h : RunD u dm y s (opD dm op a b :: kept ka a (kept kb b rest)))
    (f : List Nat → Bool) (hf : ∀ ys, RunD u dm y s ys → f ys = true) :
    nextD u dm (s + 2 - ws.length) ws f = true := by
  rcases le_total a b with hab | hba
  · exact nextD_two_sorted hop hab p h0 hd hnm h f hf
  · have he : opD dm op a b = opD dm (flipOp op) b a := opD_comm dm hop a b
    have hnm' : opD dm (flipOp op) b a ∉ (b :: a :: rest) := by
      rw [← he]; intro hm; exact hnm ((List.Perm.swap _ _ _).mem_iff.1 hm)
    apply nextD_two_sorted (op := flipOp op) (ka := kb) (kb := ka) (flipOp_allowed hop) hba
      ((List.Perm.swap _ _ _).trans p) (he ▸ h0) (he ▸ hd) hnm' _ f hf
    rw [he] at h; apply Run.perm (List.Perm.cons _ ?_) h
    cases ka <;> cases kb <;> simp [kept]; exact List.Perm.swap _ _ _

theorem nextD_complete {u : Bool} {dm y t ws} (h : RunD u dm y t ws) :
    ∀ s, t = s + 1 → ∀ zs, ws.Perm zs → ∀ f : List Nat → Bool,
      (∀ ys, RunD u dm y s ys → f ys = true) →
      nextD u dm (s + 2 - zs.length) zs f = true := by
  induction h using Run.fold with
  | done => simp
  | perm p _ ih => intro s he zs q; exact ih s he zs (p.trans q)
  | two op ka kb hop h0 hd hnm h _ => intro s he zs p f hf; cases he; exact nextD_two hop p h0 hd hnm h f hf

def span (f : Nat → Bool) : Nat → Nat → Bool
  | 0, _ => true
  | n + 1, i => f i && span f n (i + 1)

theorem span_ok {f n o} (h : span f n o = true) : ∀ i, o ≤ i → i < o + n → f i = true := by
  induction n generalizing o with
  | zero => omega
  | succ n ih =>
    simp only [span, Bool.and_eq_true] at h; intro i hi hj
    rcases Nat.eq_or_lt_of_le hi with rfl | hi
    · exact h.1
    · exact ih h.2 i (by omega) (by omega)

theorem range_split {P : Nat → Prop} {lo mid hi : Nat}
    (h1 : ∀ i, lo ≤ i → i < mid → P i) (h2 : ∀ i, mid ≤ i → i < hi → P i) :
    ∀ i, lo ≤ i → i < hi → P i := fun i hlo hhi =>
  if h : i < mid then h1 i hlo h else h2 i (Nat.le_of_not_lt h) hhi

def fld (T w i : Nat) : Nat :=
  (T >>> (w * i)) &&& (if w == 32 then 4294967295 else if w == 52 then 4503599627370495 else if w == 256 then mask256 else 2 ^ w - 1)

def bsr (read : Nat → Nat) (h : Nat) : Nat → Nat → Nat → Nat
  | 0, lo, _ => lo
  | f + 1, lo, hi =>
    if lo + 1 < hi then
      (if read ((lo + hi) / 2) ≤ h then bsr read h f ((lo + hi) / 2) hi
       else bsr read h f lo ((lo + hi) / 2))
    else lo

def hw256 (seed w : Nat) : Nat :=
  let x := (((w &&& 4294967295) ^^^ seed) * 2654435761 +
            (((w >>> 32) &&& 4294967295) ^^^ seed) * 2246822519 +
            (((w >>> 64) &&& 4294967295) ^^^ seed) * 3266489917 +
            (((w >>> 96) &&& 4294967295) ^^^ seed) * 668265263 +
            (((w >>> 128) &&& 4294967295) ^^^ seed) * 374761393 +
            (((w >>> 160) &&& 4294967295) ^^^ seed) * 1274126177 +
            (((w >>> 192) &&& 4294967295) ^^^ seed) * 2869860233 +
            (((w >>> 224) &&& 4294967295) ^^^ seed) * 1640531527) &&& 4294967295
  let y := ((x ^^^ (x >>> 16)) * 2246822519) &&& 4294967295
  ((y ^^^ (y >>> 13)) * 3266489917) &&& 4294967295

def hz (seed : Nat) : List Nat → Nat
  | [] => 0
  | w :: t => hw256 seed w + hz seed t

def hk (seed : Nat) (zs : List Nat) : Nat := hz seed zs &&& 4294967295

def found (S : Nat → Nat → List Nat) (N : Nat → Nat) (idx : Nat → List Nat → Nat)
    (s : Nat) (zs : List Nat) : Bool :=
  decide (idx s zs < N s) && zs.isPerm (S s (idx s zs))

def foundH (S : Nat → Nat → List Nat) (N : Nat → Nat) (htAt : Nat → Nat → Nat)
    (idxH : Nat → Nat → Nat) (s h : Nat) (zs : List Nat) : Bool :=
  let i := idxH s h
  decide (i < N s) && (htAt s i == h) && zs.isPerm (S s i)

-- Decorated fast O(1) incremental cover check!
def nextD_decor (u : Bool) (dm mp : Nat) (slack : Nat) (dws : List (Nat × Nat × Nat))
    (f : List (Nat × Nat × Nat) → Bool) : Bool :=
  dws.any fun da =>
    let a := da.1
    let ra := dws.erase da
    ra.any fun db =>
      let b := db.1
      a ≤ b && (let r := ra.erase db
        (opsOf u).any fun op =>
          let w := opD dm op a b
          w != 0 && w != dm && !(dws.any (fun x => x.1 == w)) &&
            let dw := (w, opP mp op da.2.1 db.2.1, opP mp op da.2.2 db.2.2)
            (f (dw :: r) || (slack ≥ 1 && (f (dw :: da :: r) || f (dw :: db :: r))) ||
              (slack ≥ 2 && f (dw :: da :: db :: r))))

theorem nextD_decor_gen (u : Bool) (dm mp : Nat) (dec : Nat → Nat × Nat × Nat)
    (hfst : ∀ w, (dec w).1 = w)
    (hop : ∀ op a b, (opD dm op a b, opP mp op (dec a).2.1 (dec b).2.1, opP mp op (dec a).2.2 (dec b).2.2) = dec (opD dm op a b))
    (slack : Nat) (ws : List Nat) (g : List (Nat × Nat × Nat) → Bool) :
    nextD_decor u dm mp slack (ws.map dec) g = nextD u dm slack ws (fun zs => g (zs.map dec)) := by
  have hinj : Function.Injective dec := fun x y h => by rw [← hfst x, ← hfst y, h]
  have herase : ∀ (l : List Nat) x, (l.map dec).erase (dec x) = (l.erase x).map dec :=
    fun l x => erase_map_inj dec hinj l x
  have hcont : ∀ (l : List Nat) w, (l.map dec).any (fun x => x.1 == w) = l.contains w := by
    intro l w; apply Bool.eq_iff_iff.2; simp [hfst]
  unfold nextD_decor nextD
  simp only [List.any_map, Function.comp_def, hfst, herase, hcont, hop, List.map_cons]

theorem nextD_decor_eq (u : Bool) {dm : Nat} (hd : dm &&& mask256 = dm)
    (pairs : List (Nat × Nat))
    (hr1 : ∀ r ∈ pairs.map Prod.fst, dm.testBit r = true)
    (hr2 : ∀ r ∈ pairs.map Prod.snd, dm.testBit r = true)
    (slack : Nat) (ws : List Nat) (g : List (Nat × Nat × Nat) → Bool) :
    let dec := fun w => (w, projBit (pairs.map Prod.fst) w, projBit (pairs.map Prod.snd) w)
    nextD_decor u dm (maskP pairs.length) slack (ws.map dec) g =
      nextD u dm slack ws (fun zs => g (zs.map dec)) := by
  intro dec
  apply nextD_decor_gen
  · intro w; rfl
  · intro op a b
    simp only [dec, projBit_opD hd hr1, projBit_opD hd hr2, List.length_map]

def addC (x : Nat) (c : Nat × Nat × Nat) : Nat × Nat × Nat :=
  (c.1 ||| x, c.2.1 ||| (c.1 &&& x), c.2.2 ||| (c.2.1 &&& x))

def cov3 (mp : Nat) (d : Bool) (dws : List (Nat × Nat × Nat)) : Nat × Nat × Nat :=
  dws.foldl (fun c dw => addC (colB mp d dw.2) c) (0, 0, 0)

def takeOne (c : Nat × Nat × Nat) (x : Nat) : Nat := (c.1 ^^^ x) ||| c.2.1
def takeTwo (c : Nat × Nat × Nat) (x y : Nat) : Nat :=
  (c.1 ^^^ (x ||| y)) ||| (c.2.1 &&& (x ^^^ y)) ||| c.2.2

theorem cov3_bit (mp : Nat) (d : Bool) (dws : List (Nat × Nat × Nat)) (i : Nat) :
    let k := dws.countP (fun dw => (colB mp d dw.2).testBit i)
    (cov3 mp d dws).1.testBit i = decide (1 ≤ k) ∧
    (cov3 mp d dws).2.1.testBit i = decide (2 ≤ k) ∧
    (cov3 mp d dws).2.2.testBit i = decide (3 ≤ k) := by
  have hgen : ∀ (xs : List (Nat × Nat × Nat)) (c : Nat × Nat × Nat) (k0 : Nat),
      (c.1.testBit i = decide (1 ≤ k0) ∧ c.2.1.testBit i = decide (2 ≤ k0) ∧ c.2.2.testBit i = decide (3 ≤ k0)) →
      let k := k0 + xs.countP (fun dw => (colB mp d dw.2).testBit i)
      (xs.foldl (fun acc dw => addC (colB mp d dw.2) acc) c).1.testBit i = decide (1 ≤ k) ∧
      (xs.foldl (fun acc dw => addC (colB mp d dw.2) acc) c).2.1.testBit i = decide (2 ≤ k) ∧
      (xs.foldl (fun acc dw => addC (colB mp d dw.2) acc) c).2.2.testBit i = decide (3 ≤ k) := by
    intro xs
    induction xs with
    | nil => intro c k0 ⟨h1, h2, h3⟩; simp [h1, h2, h3]
    | cons dw xs ih =>
      intro c k0 ⟨h1, h2, h3⟩
      simp only [List.foldl_cons, List.countP_cons]
      have hc : (addC (colB mp d dw.2) c).1.testBit i =
            decide (1 ≤ k0 + (if (colB mp d dw.2).testBit i then 1 else 0)) ∧
          (addC (colB mp d dw.2) c).2.1.testBit i =
            decide (2 ≤ k0 + (if (colB mp d dw.2).testBit i then 1 else 0)) ∧
          (addC (colB mp d dw.2) c).2.2.testBit i =
            decide (3 ≤ k0 + (if (colB mp d dw.2).testBit i then 1 else 0)) := by
        simp only [addC, Nat.testBit_or, Nat.testBit_and, h1, h2, h3]
        cases hb : (colB mp d dw.2).testBit i <;>
          rcases k0 with _ | _ | _ | k0 <;>
          simp [hb, Nat.le_add_left]
      have ih' := ih (addC (colB mp d dw.2) c) (k0 + (if (colB mp d dw.2).testBit i then 1 else 0)) hc
      cases hb : (colB mp d dw.2).testBit i <;> simp only [hb, ↓reduceIte, Bool.false_eq_true, Nat.add_zero] at ih' ⊢
      · exact ih'
      · simpa only [Nat.add_assoc, Nat.add_comm 1] using ih'
  simpa only [cov3, Nat.zero_testBit, Nat.zero_add] using hgen dws (0, 0, 0) 0 (by simp)

theorem cov3_perm (mp : Nat) (d : Bool) {xs ys : List (Nat × Nat × Nat)} (p : xs.Perm ys) :
    cov3 mp d xs = cov3 mp d ys := by
  have heq : ∀ i, (cov3 mp d xs).1.testBit i = (cov3 mp d ys).1.testBit i ∧
      (cov3 mp d xs).2.1.testBit i = (cov3 mp d ys).2.1.testBit i ∧
      (cov3 mp d xs).2.2.testBit i = (cov3 mp d ys).2.2.testBit i := by
    intro i
    obtain ⟨a1, a2, a3⟩ := cov3_bit mp d xs i
    obtain ⟨b1, b2, b3⟩ := cov3_bit mp d ys i
    rw [p.countP_eq] at a1 a2 a3
    exact ⟨a1.trans b1.symm, a2.trans b2.symm, a3.trans b3.symm⟩
  apply Prod.ext
  · exact Nat.eq_of_testBit_eq (fun i => (heq i).1)
  · apply Prod.ext
    · exact Nat.eq_of_testBit_eq (fun i => (heq i).2.1)
    · exact Nat.eq_of_testBit_eq (fun i => (heq i).2.2)

theorem takeOne_eq (mp : Nat) (d : Bool) (a : Nat × Nat × Nat) (rest : List (Nat × Nat × Nat)) :
    takeOne (cov3 mp d (a :: rest)) (colB mp d a.2) = (cov3 mp d rest).1 := by
  apply Nat.eq_of_testBit_eq; intro i
  obtain ⟨h1, h2, _⟩ := cov3_bit mp d (a :: rest) i
  obtain ⟨r1, _, _⟩ := cov3_bit mp d rest i
  simp only [takeOne, Nat.testBit_or, Nat.testBit_xor, h1, h2, r1, List.countP_cons]
  set k := rest.countP (fun dw => (colB mp d dw.2).testBit i)
  cases ha : (colB mp d a.2).testBit i <;> simp only [ha, Bool.false_eq_true, ↓reduceIte] <;>
    rcases k with _ | _ | _ | k
  · decide
  · decide
  · decide
  · simp only [show 1 ≤ k + 3 by omega, show 2 ≤ k + 3 by omega, decide_true, Bool.xor_false, Bool.or_true]
  · decide
  · decide
  · decide
  · simp only [show 1 ≤ k + 3 + 1 by omega, show 2 ≤ k + 3 + 1 by omega, show 1 ≤ k + 3 by omega,
      decide_true, Bool.xor_true, Bool.or_true, Bool.or_false]

theorem takeTwo_eq (mp : Nat) (d : Bool) (a b : Nat × Nat × Nat) (rest : List (Nat × Nat × Nat)) :
    takeTwo (cov3 mp d (a :: b :: rest)) (colB mp d a.2) (colB mp d b.2) = (cov3 mp d rest).1 := by
  apply Nat.eq_of_testBit_eq; intro i
  obtain ⟨h1, h2, h3⟩ := cov3_bit mp d (a :: b :: rest) i
  obtain ⟨r1, _, _⟩ := cov3_bit mp d rest i
  simp only [takeTwo, Nat.testBit_or, Nat.testBit_and, Nat.testBit_xor, h1, h2, h3, r1, List.countP_cons]
  set k := rest.countP (fun dw => (colB mp d dw.2).testBit i)
  cases ha : (colB mp d a.2).testBit i <;> cases hb : (colB mp d b.2).testBit i <;>
    simp only [ha, hb, Bool.false_eq_true, ↓reduceIte] <;>
    rcases k with _ | _ | _ | k <;>
    (first | decide | simp only [
      show 1 ≤ k + 3 by omega, show 2 ≤ k + 3 by omega, show 3 ≤ k + 3 by omega,
      show 1 ≤ k + 3 + 1 by omega, show 2 ≤ k + 3 + 1 by omega, show 3 ≤ k + 3 + 1 by omega,
      show 1 ≤ k + 3 + 1 + 1 by omega, show 2 ≤ k + 3 + 1 + 1 by omega, show 3 ≤ k + 3 + 1 + 1 by omega,
      decide_true, Bool.xor_true, Bool.xor_false, Bool.or_true, Bool.or_false, Bool.and_true, Bool.and_false])

theorem cov3_coversD (u : Bool) (mp : Nat) (dw : Nat × Nat × Nat) (rest : List (Nat × Nat × Nat)) :
    ((cov3 mp (!u) rest).1 ||| colB mp (!u) dw.2 == mp) = coversD u mp (dw :: rest) := by
  have e : ((cov3 mp (!u) rest).1 ||| colB mp (!u) dw.2) =
      (dw :: rest).foldl (fun acc x => acc ||| colB mp (!u) x.2) 0 := by
    apply Nat.eq_of_testBit_eq; intro i
    obtain ⟨h1, _, _⟩ := cov3_bit mp (!u) rest i
    rw [foldl_or_testBit, Nat.zero_testBit, Bool.false_or, Nat.testBit_or, h1, List.any_cons]
    have hp : decide (1 ≤ rest.countP (fun dw => (colB mp (!u) dw.2).testBit i)) =
        rest.any (fun x => (colB mp (!u) x.2).testBit i) := by
      rw [Bool.eq_iff_iff, decide_eq_true_eq, Nat.succ_le_iff, List.countP_pos_iff, List.any_eq_true]
    rw [hp, Bool.or_comm]
  unfold coversD; exact congrArg (· == mp) e

def nextD_cov (u : Bool) (dm mp slack : Nat) (dws : List (Nat × Nat × Nat))
    (f : List (Nat × Nat × Nat) → Bool) : Bool :=
  let ori := !u
  let cov := cov3 mp ori dws
  dws.any fun da =>
    let a := da.1
    let ca := colB mp ori da.2
    let ra := dws.erase da
    ra.any fun db =>
      let b := db.1
      a ≤ b &&
        (let cb := colB mp ori db.2
         let base0 := takeTwo cov ca cb
         let base1a := takeOne cov cb
         let base1b := takeOne cov ca
         let r := ra.erase db
         (opsOf u).any fun op =>
           let pz := (opP mp op da.2.1 db.2.1, opP mp op da.2.2 db.2.2)
           let cz := colB mp ori pz
           let ok0 := (base0 ||| cz) == mp
           let ok1a := slack ≥ 1 && ((base1a ||| cz) == mp)
           let ok1b := slack ≥ 1 && ((base1b ||| cz) == mp)
           let ok2 := slack ≥ 2 && ((cov.1 ||| cz) == mp)
           (ok0 || ok1a || ok1b || ok2) &&
           (let w := opD dm op a b
            w != 0 && w != dm && !(dws.any (fun x => x.1 == w)) &&
              let dw := (w, pz)
              ((ok0 && f (dw :: r)) || (ok1a && f (dw :: da :: r)) ||
               (ok1b && f (dw :: db :: r)) || (ok2 && f (dw :: da :: db :: r)))))

theorem nextD_cov_eq (u : Bool) (dm mp slack : Nat) (dws : List (Nat × Nat × Nat))
    (g : List (Nat × Nat × Nat) → Bool) :
    nextD_cov u dm mp slack dws g =
      nextD_decor u dm mp slack dws (fun dzs => coversD u mp dzs && g dzs) := by
  unfold nextD_cov nextD_decor
  dsimp only
  apply Bool.eq_iff_iff.2; simp only [List.any_eq_true, Bool.or_eq_true, Bool.and_eq_true]
  constructor
  · rintro ⟨da, hda, db, hdb, hab, op, hop, _, ⟨⟨hw0, hwdm⟩, hnw⟩, hfx⟩
    refine ⟨da, hda, db, hdb, hab, op, hop, ⟨⟨hw0, hwdm⟩, hnw⟩, ?_⟩
    set pz := (opP mp op da.2.1 db.2.1, opP mp op da.2.2 db.2.2)
    set dw := (opD dm op da.1 db.1, pz)
    set ra := dws.erase da
    set r := ra.erase db
    have hp : dws.Perm (da :: db :: r) := (List.perm_cons_erase hda).trans (List.Perm.cons _ (List.perm_cons_erase hdb))
    have hc2 := cov3_perm mp (!u) hp
    have hca := cov3_perm mp (!u) (hp.trans (List.Perm.swap _ _ _))
    have hcov0 : (takeTwo (cov3 mp (!u) dws) (colB mp (!u) da.2) (colB mp (!u) db.2) ||| colB mp (!u) pz == mp) =
        coversD u mp (dw :: r) := by rw [hc2, takeTwo_eq]; exact cov3_coversD u mp dw r
    have hcov1a : (takeOne (cov3 mp (!u) dws) (colB mp (!u) db.2) ||| colB mp (!u) pz == mp) =
        coversD u mp (dw :: da :: r) := by rw [hca, takeOne_eq]; exact cov3_coversD u mp dw (da :: r)
    have hcov1b : (takeOne (cov3 mp (!u) dws) (colB mp (!u) da.2) ||| colB mp (!u) pz == mp) =
        coversD u mp (dw :: db :: r) := by rw [hc2, takeOne_eq]; exact cov3_coversD u mp dw (db :: r)
    have hcov2 : ((cov3 mp (!u) dws).1 ||| colB mp (!u) pz == mp) =
        coversD u mp (dw :: da :: db :: r) := by rw [hc2]; exact cov3_coversD u mp dw (da :: db :: r)
    rcases hfx with ((⟨hu0, hf0⟩ | ⟨⟨hsl1, hu1a⟩, hf1a⟩) | ⟨⟨hsl1, hu1b⟩, hf1b⟩) | ⟨⟨hsl2, hu2⟩, hf2⟩
    · left; left; exact ⟨hcov0 ▸ hu0, hf0⟩
    · left; right; exact ⟨hsl1, Or.inl ⟨hcov1a ▸ hu1a, hf1a⟩⟩
    · left; right; exact ⟨hsl1, Or.inr ⟨hcov1b ▸ hu1b, hf1b⟩⟩
    · right; exact ⟨hsl2, hcov2 ▸ hu2, hf2⟩
  · rintro ⟨da, hda, db, hdb, hab, op, hop, ⟨⟨hw0, hwdm⟩, hnw⟩, hfx⟩
    refine ⟨da, hda, db, hdb, hab, op, hop, ?_⟩
    set pz := (opP mp op da.2.1 db.2.1, opP mp op da.2.2 db.2.2)
    set dw := (opD dm op da.1 db.1, pz)
    set ra := dws.erase da
    set r := ra.erase db
    have hp : dws.Perm (da :: db :: r) := (List.perm_cons_erase hda).trans (List.Perm.cons _ (List.perm_cons_erase hdb))
    have hc2 := cov3_perm mp (!u) hp
    have hca := cov3_perm mp (!u) (hp.trans (List.Perm.swap _ _ _))
    have hcov0 : (takeTwo (cov3 mp (!u) dws) (colB mp (!u) da.2) (colB mp (!u) db.2) ||| colB mp (!u) pz == mp) =
        coversD u mp (dw :: r) := by rw [hc2, takeTwo_eq]; exact cov3_coversD u mp dw r
    have hcov1a : (takeOne (cov3 mp (!u) dws) (colB mp (!u) db.2) ||| colB mp (!u) pz == mp) =
        coversD u mp (dw :: da :: r) := by rw [hca, takeOne_eq]; exact cov3_coversD u mp dw (da :: r)
    have hcov1b : (takeOne (cov3 mp (!u) dws) (colB mp (!u) da.2) ||| colB mp (!u) pz == mp) =
        coversD u mp (dw :: db :: r) := by rw [hc2, takeOne_eq]; exact cov3_coversD u mp dw (db :: r)
    have hcov2 : ((cov3 mp (!u) dws).1 ||| colB mp (!u) pz == mp) =
        coversD u mp (dw :: da :: db :: r) := by rw [hc2]; exact cov3_coversD u mp dw (da :: db :: r)
    rcases hfx with (⟨hc0, hg0⟩ | ⟨hsl1, ⟨hc1a, hg1a⟩ | ⟨hc1b, hg1b⟩⟩) | ⟨hsl2, hc2', hg2⟩
    · have u0 : (takeTwo (cov3 mp (!u) dws) (colB mp (!u) da.2) (colB mp (!u) db.2) ||| colB mp (!u) pz == mp) = true := hcov0.symm ▸ hc0
      exact ⟨Or.inl (Or.inl (Or.inl u0)), ⟨⟨hw0, hwdm⟩, hnw⟩, Or.inl (Or.inl (Or.inl ⟨u0, hg0⟩))⟩
    · have u1a : (takeOne (cov3 mp (!u) dws) (colB mp (!u) db.2) ||| colB mp (!u) pz == mp) = true := hcov1a.symm ▸ hc1a
      exact ⟨Or.inl (Or.inl (Or.inr ⟨hsl1, u1a⟩)), ⟨⟨hw0, hwdm⟩, hnw⟩, Or.inl (Or.inl (Or.inr ⟨⟨hsl1, u1a⟩, hg1a⟩))⟩
    · have u1b : (takeOne (cov3 mp (!u) dws) (colB mp (!u) da.2) ||| colB mp (!u) pz == mp) = true := hcov1b.symm ▸ hc1b
      exact ⟨Or.inl (Or.inr ⟨hsl1, u1b⟩), ⟨⟨hw0, hwdm⟩, hnw⟩, Or.inl (Or.inr ⟨⟨hsl1, u1b⟩, hg1b⟩)⟩
    · have u2 : ((cov3 mp (!u) dws).1 ||| colB mp (!u) pz == mp) = true := hcov2.symm ▸ hc2'
      exact ⟨Or.inr ⟨hsl2, u2⟩, ⟨⟨hw0, hwdm⟩, hnw⟩, Or.inr ⟨⟨hsl2, u2⟩, hg2⟩⟩

def bar (u : Bool) (dm Y : Nat) (mp : Nat)
    (SD : Nat → Nat → List (Nat × Nat × Nat)) (S : Nat → Nat → List Nat)
    (N : Nat → Nat) (htAt idxH : Nat → Nat → Nat)
    (ori : List Nat → List Nat) (seed : Nat) (pool : List Nat) (cutHitH : Nat → Nat → List Nat → Bool) : Nat → Nat → Bool
  | 0, i => !(S 0 i == [Y])
  | s + 1, i =>
    let dws := SD (s + 1) i
    !(nextD_cov u dm mp (s + 2 - dws.length) dws fun dzs =>
        let zs := dzs.map Prod.fst
        !(scr u dm Y s pool zs) &&
        (let cz := ori zs
         let h := hk seed cz
         !(cutHitH s h cz) && !(foundH S N htAt idxH s h cz)))

theorem bar_all {u : Bool} {dm T : Nat} {pairs : List (Nat × Nat)} {r1s r2s mp SD S N htAt idxH ori seed pool cutHitH cap}
    (hd : dm &&& mask256 = dm)
    (hr1_eq : r1s = pairs.map Prod.fst) (hr2_eq : r2s = pairs.map Prod.snd) (hmp_eq : mp = maskP pairs.length)
    (hSD : ∀ s j, SD s j = (S s j).map (fun w => (w, projBit r1s w, projBit r2s w)))
    (hpairs : pairs.all (fun p => dm.testBit p.1 && dm.testBit p.2 && !(T &&& dm).testBit p.1 && (T &&& dm).testBit p.2) = true)
    (hr : ∀ {v ys}, RunD u dm (T &&& dm) v ys → RunD u dm (T &&& dm) v (ori ys))
    (hcut : ∀ {v ys}, cutHitH v (hk seed ys) ys = true → ¬ RunD u dm (T &&& dm) v ys)
    (hc : ∀ s ≤ cap, ∀ i < N s, bar u dm (T &&& dm) mp SD S N htAt idxH ori seed pool cutHitH s i = true) :
    ∀ s ≤ cap, ∀ i < N s, ¬ RunD u dm (T &&& dm) s (S s i) := by
  subst hr1_eq hr2_eq hmp_eq
  have hr1 : ∀ r ∈ pairs.map Prod.fst, dm.testBit r = true := by
    intro r hr'; obtain ⟨p, hp, rfl⟩ := List.mem_map.1 hr'
    have h := List.all_eq_true.1 hpairs p hp; simp only [Bool.and_eq_true] at h; exact h.1.1.1
  have hr2 : ∀ r ∈ pairs.map Prod.snd, dm.testBit r = true := by
    intro r hr'; obtain ⟨p, hp, rfl⟩ := List.mem_map.1 hr'
    have h := List.all_eq_true.1 hpairs p hp; simp only [Bool.and_eq_true] at h; exact h.1.1.2
  intro s
  induction s using Nat.strong_induction_on with
  | ind s ih =>
    intro hs i hi hh
    have hb := hc s hs i hi
    cases s with
    | zero => simp [bar, zero_done hh rfl] at hb
    | succ s =>
      by_contra! hn
      let F (zs : List Nat) :=
        coversP u pairs zs && !(scr u dm (T &&& dm) s pool zs) &&
        (let cz := ori zs
         let h := hk seed cz
         !(cutHitH s h cz) && !(foundH S N htAt idxH s h cz))
      have hF (zs) (hz : RunD u dm (T &&& dm) s zs) : F zs = true := by
        have hcz := hr hz
        have hcutf : cutHitH s (hk seed (ori zs)) (ori zs) = false := by
          cases h : cutHitH s (hk seed (ori zs)) (ori zs) with
          | false => rfl
          | true => exact absurd hcz (hcut h)
        simp only [F, coversP_ok hd pairs hpairs hz, scr_no pool hz, hcutf, Bool.not_false, Bool.true_and, foundH]
        simp only [Bool.not_eq_true', Bool.and_eq_false_imp, Bool.and_eq_true, decide_eq_true_eq, beq_iff_eq]
        rintro ⟨hj, _⟩
        by_contra! hp
        have p := List.isPerm_iff.1 (Bool.eq_true_of_not_eq_false hp)
        exact ih s (by omega) (by omega) _ hj (Run.perm p hcz)
      have hN := nextD_complete hh s rfl _ (List.Perm.refl _) F hF
      dsimp only [bar] at hb
      rw [hSD, List.length_map, nextD_cov_eq, nextD_decor_eq u hd pairs hr1 hr2] at hb
      have hFeq : (fun zs => coversD u (maskP pairs.length) (zs.map (fun w => (w, projBit (pairs.map Prod.fst) w, projBit (pairs.map Prod.snd) w))) &&
          (let zs' := (zs.map (fun w => (w, projBit (pairs.map Prod.fst) w, projBit (pairs.map Prod.snd) w))).map Prod.fst
           !(scr u dm (T &&& dm) s pool zs') &&
           (let cz := ori zs'
            let h := hk seed cz
            !(cutHitH s h cz) && !(foundH S N htAt idxH s h cz)))) = F := by
        funext zs
        have hfst : (zs.map (fun w => (w, projBit (pairs.map Prod.fst) w, projBit (pairs.map Prod.snd) w))).map Prod.fst = zs := by
          simp [List.map_map, Function.comp_def]
        rw [coversD_eq, hfst]
        simp only [F, Bool.and_assoc]
      rw [hFeq, hN] at hb
      contradiction

def pickMin (seed : Nat) (orig : List Nat) : List (List (Nat × Nat)) → List Nat → Nat → List Nat
  | [], best, _ => best
  | ms :: rest, best, bestH =>
    let img := orig.map (applyMoves ms)
    let h := hk seed img
    if h < bestH then pickMin seed orig rest img h else pickMin seed orig rest best bestH

theorem pickMin_runD {u : Bool} {dm Y v} (seed : Nat) (orig : List Nat) (h0 : RunD u dm Y v orig) :
    ∀ (syms : List (List (Nat × Nat))) (best : List Nat) (bestH : Nat),
      syms.all (fun ms => ms.all moveOK256 && (applyMoves ms dm == dm) && (applyMoves ms Y == Y)) = true →
      RunD u dm Y v best →
      RunD u dm Y v (pickMin seed orig syms best bestH)
  | [], _, _, _, hb => hb
  | ms :: rest, best, bestH, hok, hb => by
    simp only [List.all_cons, Bool.and_eq_true, beq_iff_eq] at hok
    unfold pickMin; dsimp only; split
    · exact pickMin_runD seed orig h0 rest _ _ hok.2 (applyMoves_runD ms hok.1.1.1 hok.1.1.2 hok.1.2 h0)
    · exact pickMin_runD seed orig h0 rest best bestH hok.2 hb

-- Bridge: directSplit!
def gvN (w : List Nat) (g : Gate) : Nat :=
  match g.op with
  | .and => g.inputs.foldr (fun i acc => andD mask256 (w.getD i 0) acc) mask256
  | .or  => g.inputs.foldr (fun i acc => orD mask256 (w.getD i 0) acc) 0
  | .not => match g.inputs with | [] => mask256 | i :: _ => negD mask256 (w.getD i 0)
  | _ => 0

def execN (gs : List Gate) (w : List Nat) : List Nat :=
  gs.foldl (fun l g => l ++ [gvN l g]) w

theorem gvN_bit (w : List Nat) (g : Gate) (r : Nat) (hr : r < 256)
    (hop : g.op ∈ ({GateOp.and, GateOp.or, GateOp.not} : Set GateOp)) :
    (gvN w g).testBit r = g.op.eval (g.inputs.map fun i => (w.map (·.testBit r)).getD i false) := by
  have hm : mask256.testBit r = true := by simp [mask256_bit, hr]
  have hgd : ∀ i, (w.map (·.testBit r)).getD i false = (w.getD i 0).testBit r := by
    intro i; simp only [List.getD_eq_getElem?_getD, List.getElem?_map]
    cases w[i]? with | none => simp | some v => rfl
  simp only [Set.mem_insert_iff, Set.mem_singleton_iff] at hop
  rcases hop with h | h | h
  · simp only [gvN, GateOp.eval, h]
    induction g.inputs with
    | nil => simp [hm]
    | cons i l ih =>
      rw [List.foldr_cons, List.map_cons, List.all_cons, id_eq, andD, Nat.testBit_and, Nat.testBit_and, hm, Bool.and_true, hgd, ih]
  · simp only [gvN, GateOp.eval, h]
    induction g.inputs with
    | nil => simp
    | cons i l ih =>
      rw [List.foldr_cons, List.map_cons, List.any_cons, id_eq, orD, Nat.testBit_and, Nat.testBit_or, hm, Bool.and_true, hgd, ih]
  · simp only [gvN, GateOp.eval, h]
    cases g.inputs with
    | nil => simp [hm]
    | cons i l => simp only [List.map_cons, List.headD_cons, negD, Nat.testBit_and, Nat.testBit_xor, hm, Bool.and_true, Bool.xor_true, hgd]

theorem execN_bit (gs : List Gate) (w : List Nat) (r : Nat) (hr : r < 256)
    (hfan : ∀ g ∈ gs, g.op ∈ ({GateOp.and, GateOp.or, GateOp.not} : Set GateOp)) :
    (execN gs w).map (·.testBit r) =
      gs.foldl (fun l g => l ++ [g.op.eval (g.inputs.map fun i => l.getD i false)]) (w.map (·.testBit r)) := by
  induction gs generalizing w with
  | nil => rfl
  | cons g gs ih =>
    simp only [execN, List.foldl_cons] at ih ⊢
    rw [ih _ (fun g' hg' => hfan g' (List.mem_cons_of_mem _ hg'))]
    simp [gvN_bit w g r hr (hfan g List.mem_cons_self)]

def isNotGate (g : Gate) : Bool := match g.op with | .not => true | _ => false

theorem execN_reach (u : Bool) (gs : List Gate) (roots : List Nat)
    (hfan : ∀ g ∈ gs, g.op ∈ ({GateOp.and, GateOp.or, GateOp.not} : Set GateOp) ∧ g.inputs.length ≤ 2)
    (hmono : u = false → ∀ g ∈ gs, isNotGate g = false) :
    ∀ (p : Nat) (w bank : List Nat), NatReach u mask256 roots p bank →
      (∀ v ∈ w, Avail u mask256 bank v) →
      ∃ p' bank', p' ≤ p + gs.countP (fun g => !isNotGate g) ∧ NatReach u mask256 roots p' bank' ∧
        ∀ v ∈ execN gs w, Avail u mask256 bank' v := by
  have hm256 : mask256 &&& mask256 = mask256 := Nat.and_self _
  induction gs with
  | nil => intro p w bank hr hsup; exact ⟨p, bank, by simp, hr, hsup⟩
  | cons g gs ih =>
    intro p w bank hr hsup
    have hav_gd : ∀ i, Avail u mask256 bank (w.getD i 0) := by
      intro i; by_cases hi : i < w.length
      · exact hsup _ (getD_mem hi)
      · rw [List.getD_eq_default _ _ (by omega)]; exact Or.inl (Or.inl (by simp))
    have hstep : ∃ p1 bank1, p1 ≤ p + (if !isNotGate g then 1 else 0) ∧ NatReach u mask256 roots p1 bank1 ∧
        (∀ v ∈ w ++ [gvN w g], Avail u mask256 bank1 v) := by
      have hg := hfan g List.mem_cons_self
      simp only [Set.mem_insert_iff, Set.mem_singleton_iff] at hg
      obtain ⟨hop, hlen⟩ := hg
      have hand_m : ∀ a, andD mask256 a mask256 &&& mask256 = a &&& mask256 := fun a => by
        simp [andD, Nat.and_assoc, Nat.and_self]
      have hor_0 : ∀ a, orD mask256 a 0 &&& mask256 = a &&& mask256 := fun a => by
        simp [orD, Nat.and_assoc, Nat.and_self]
      have lift_w : ∀ z, (∀ v ∈ w, Avail u mask256 (z :: bank) v) := fun z v hv => avail_cons z v (hsup v hv)
      rcases hop with h | h | h
      · have hn : (!isNotGate g) = true := by simp [isNotGate, h]
        rw [hn]; simp only [ite_true]
        rcases hgi : g.inputs with _ | ⟨i, _ | ⟨j, _ | ⟨k, l⟩⟩⟩
        · exact ⟨p, bank, by omega, hr, fun v hv => by
            rcases List.mem_append.1 hv with hv | hv; · exact hsup v hv
            · rw [List.mem_singleton.1 hv]; exact Or.inl (Or.inr (by simp [gvN, h, hgi]))⟩
        · exact ⟨p, bank, by omega, hr, fun v hv => by
            rcases List.mem_append.1 hv with hv | hv; · exact hsup v hv
            · rw [List.mem_singleton.1 hv]; simp only [gvN, h, hgi, List.foldr_cons, List.foldr_nil]
              exact avail_of_eq (hand_m _).symm (hav_gd i)⟩
        · refine ⟨p + 1, opD mask256 0 (w.getD i 0) (w.getD j 0) :: bank, le_rfl,
            ⟨bank, _, _, 0, by simp [allowedB], rfl, hr, hav_gd i, hav_gd j⟩, fun v hv => ?_⟩
          rcases List.mem_append.1 hv with hv | hv; · exact lift_w _ v hv
          · rw [List.mem_singleton.1 hv]; simp only [gvN, h, hgi, List.foldr_cons, List.foldr_nil]
            exact Or.inr (Or.inl ⟨_, List.mem_cons_self, by simp [opD, andD, Nat.and_assoc, Nat.and_self]⟩)
        · rw [hgi] at hlen; simp at hlen
      · have hn : (!isNotGate g) = true := by simp [isNotGate, h]
        rw [hn]; simp only [ite_true]
        rcases hgi : g.inputs with _ | ⟨i, _ | ⟨j, _ | ⟨k, l⟩⟩⟩
        · exact ⟨p, bank, by omega, hr, fun v hv => by
            rcases List.mem_append.1 hv with hv | hv; · exact hsup v hv
            · rw [List.mem_singleton.1 hv]; exact Or.inl (Or.inl (by simp [gvN, h, hgi]))⟩
        · exact ⟨p, bank, by omega, hr, fun v hv => by
            rcases List.mem_append.1 hv with hv | hv; · exact hsup v hv
            · rw [List.mem_singleton.1 hv]; simp only [gvN, h, hgi, List.foldr_cons, List.foldr_nil]
              exact avail_of_eq (hor_0 _).symm (hav_gd i)⟩
        · refine ⟨p + 1, opD mask256 1 (w.getD i 0) (w.getD j 0) :: bank, le_rfl,
            ⟨bank, _, _, 1, by simp [allowedB], rfl, hr, hav_gd i, hav_gd j⟩, fun v hv => ?_⟩
          rcases List.mem_append.1 hv with hv | hv; · exact lift_w _ v hv
          · rw [List.mem_singleton.1 hv]; simp only [gvN, h, hgi, List.foldr_cons, List.foldr_nil]
            exact Or.inr (Or.inl ⟨_, List.mem_cons_self, by apply Nat.eq_of_testBit_eq; intro r; simp [opD, orD]; cases mask256.testBit r <;> simp⟩)
        · rw [hgi] at hlen; simp at hlen
      · cases u with
        | false =>
          have hbad := hmono rfl g List.mem_cons_self
          simp [isNotGate, h] at hbad
        | true =>
          have hn : (!isNotGate g) = false := by simp [isNotGate, h]
          rw [hn]; simp only [Bool.false_eq_true, ite_false, Nat.add_zero]
          rcases hgi : g.inputs with _ | ⟨i, l⟩
          · exact ⟨p, bank, le_rfl, hr, fun v hv => by
              rcases List.mem_append.1 hv with hv | hv; · exact hsup v hv
              · rw [List.mem_singleton.1 hv]; exact Or.inl (Or.inr (by simp [gvN, h, hgi]))⟩
          · exact ⟨p, bank, le_rfl, hr, fun v hv => by
              rcases List.mem_append.1 hv with hv | hv; · exact hsup v hv
              · rw [List.mem_singleton.1 hv]; simp only [gvN, h, hgi]
                exact avail_neg hm256 (hav_gd i)⟩
    obtain ⟨p1, bank1, hp1, hr1, hsup1⟩ := hstep
    obtain ⟨p2, bank2, hp2, hr2, hsup2⟩ := ih (fun g' hg' => hfan g' (List.mem_cons_of_mem _ hg'))
      (fun hu g' hg' => hmono hu g' (List.mem_cons_of_mem _ hg')) p1 _ bank1 hr1 hsup1
    rw [List.countP_cons]
    cases hb : !isNotGate g <;> simp only [hb, ite_true, Bool.false_eq_true, ite_false] at hp1 ⊢ <;>
      exact ⟨p2, bank2, by omega, hr2, hsup2⟩

def xs256 : List Nat :=
  [0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa,
   0xcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc,
   0xf0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0,
   0xff00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff00,
   0xffff0000ffff0000ffff0000ffff0000ffff0000ffff0000ffff0000ffff0000,
   0xffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000,
   0xffffffffffffffff0000000000000000ffffffffffffffff0000000000000000,
   0xffffffffffffffffffffffffffffffff00000000000000000000000000000000]

def pt8 (r : Nat) : Fin 8 → Bool := fun i => r.testBit i.val

theorem xs256_bits : ∀ r : Fin 256, xs256.map (·.testBit r.val) = List.ofFn (pt8 r.val) := by
  decide +kernel

theorem countP_not_lt {gs : List Gate} {g : Gate} (hg : g ∈ gs) (hn : isNotGate g = true) :
    gs.countP (fun x => !isNotGate x) + 1 ≤ gs.length := by
  induction gs with
  | nil => simp at hg
  | cons x xs ih =>
    rw [List.countP_cons, List.length_cons]
    rcases List.mem_cons.1 hg with rfl | hxs
    · simp only [hn, Bool.not_true, Bool.false_eq_true, ite_false]
      have := List.countP_le_length (p := fun y => !isNotGate y) (l := xs); omega
    · have := ih hxs; cases hb : !isNotGate x <;> simp only [hb, ite_true, Bool.false_eq_true, ite_false] <;> omega

theorem directSplit_to_circuit (f : (Fin 8 → Bool) → Bool) (T lb : Nat)
    (hT : ∀ r : Fin 256, T.testBit r.val = f (pt8 r.val))
    (hS : Lower true mask256 xs256 T (lb - 1))
    (hM : Lower false mask256 xs256 T lb) :
    ∀ t : ℕ, HasCircuitSize 8 f t → lb ≤ t := by
  rintro t ⟨C, hfan, hsz, hev⟩
  have hout : (execN C.gates xs256).getD C.output 0 &&& mask256 = T &&& mask256 := by
    apply Nat.eq_of_testBit_eq; intro r
    rw [Nat.testBit_and, Nat.testBit_and, mask256_bit]
    by_cases hlt : r < 256
    · simp only [hlt, decide_true, Bool.and_true]
      have h1 := execN_bit C.gates xs256 r hlt (fun g hg => (hfan g hg).1)
      have h2 := congrArg (fun l => l.getD C.output false) h1
      rw [xs256_bits ⟨r, hlt⟩] at h2
      have hgd : ((execN C.gates xs256).map (·.testBit r)).getD C.output false =
          ((execN C.gates xs256).getD C.output 0).testBit r := by
        simp only [List.getD_eq_getElem?_getD, List.getElem?_map]
        cases (execN C.gates xs256)[C.output]? with | none => simp | some v => rfl
      rw [hgd] at h2
      have h3 : (C.wires (List.ofFn (pt8 r))).getD C.output false = f (pt8 r) := hev (pt8 r)
      exact h2.trans (h3.trans (hT ⟨r, hlt⟩).symm)
    · simp [hlt]
  by_cases hhas : ∃ g ∈ C.gates, isNotGate g = true
  · obtain ⟨g, hg, hgn⟩ := hhas
    have hsup0 : ∀ v ∈ xs256, Avail true mask256 xs256 v := fun v hv => Or.inr (Or.inl ⟨v, hv, rfl⟩)
    obtain ⟨p, bank, hp, hr, hsup⟩ := execN_reach true C.gates xs256 hfan (fun h => Bool.noConfusion h) 0 xs256 xs256 rfl hsup0
    have hav_out : Avail true mask256 bank ((execN C.gates xs256).getD C.output 0) := by
      by_cases hi : C.output < (execN C.gates xs256).length
      · exact hsup _ (getD_mem hi)
      · rw [List.getD_eq_default _ _ (by omega)]; exact Or.inl (Or.inl (by simp))
    have hL := hS p bank hr (avail_of_eq hout hav_out)
    have hlt := countP_not_lt hg hgn
    have : C.gates.length ≤ t := hsz
    omega
  · push_neg at hhas
    have hmono : ∀ g ∈ C.gates, isNotGate g = false := fun g hg => Bool.eq_false_iff.2 (hhas g hg)
    have hsup0 : ∀ v ∈ xs256, Avail false mask256 xs256 v := fun v hv => Or.inr (Or.inl ⟨v, hv, rfl⟩)
    obtain ⟨p, bank, hp, hr, hsup⟩ := execN_reach false C.gates xs256 hfan (fun _ => hmono) 0 xs256 xs256 rfl hsup0
    have hav_out : Avail false mask256 bank ((execN C.gates xs256).getD C.output 0) := by
      by_cases hi : C.output < (execN C.gates xs256).length
      · exact hsup _ (getD_mem hi)
      · rw [List.getD_eq_default _ _ (by omega)]; exact Or.inl (Or.inl (by simp))
    have hL := hM p bank hr (avail_of_eq hout hav_out)
    have hle := List.countP_le_length (p := fun y => !isNotGate y) (l := C.gates)
    have : C.gates.length ≤ t := hsz
    omega

def dom_15 : Nat := 0xffff
def goal_15 : Nat := 0xeaa8eaa8eaa8eaa8eaa8eaa8eaa8eaa8eaa8eaa8eaa8eaa8eaa8eaa8eaa8eaa8
def roots_15 : List Nat := [xs256.getD 0 0, xs256.getD 1 0, xs256.getD 2 0, xs256.getD 3 0]

def dom_23 : Nat := 0xff00ff
def goal_23 : Nat := 0xeaeaa8a8eaeaa8a8eaeaa8a8eaeaa8a8eaeaa8a8eaeaa8a8eaeaa8a8eaeaa8a8
def roots_23 : List Nat := [xs256.getD 0 0, xs256.getD 1 0, xs256.getD 2 0, xs256.getD 4 0]

def dom_27 : Nat := 0xf0f0f0f
def goal_27 : Nat := 0xeeaaaa88eeaaaa88eeaaaa88eeaaaa88eeaaaa88eeaaaa88eeaaaa88eeaaaa88
def roots_27 : List Nat := [xs256.getD 0 0, xs256.getD 1 0, xs256.getD 3 0, xs256.getD 4 0]

def dom_31 : Nat := 0xffffffff
def goal_31 : Nat := 0xeeeaeaa8eeeaeaa8eeeaeaa8eeeaeaa8eeeaeaa8eeeaeaa8eeeaeaa8eeeaeaa8
def roots_31 : List Nat := [xs256.getD 0 0, xs256.getD 1 0, xs256.getD 2 0, xs256.getD 3 0, xs256.getD 4 0]

def dom_63 : Nat := 0xffffffffffffffff
def goal_63 : Nat := 0xeeeaeae8eeeaeaa8eeeaeae8eeeaeaa8eeeaeae8eeeaeaa8eeeaeae8eeeaeaa8
def roots_63 : List Nat := [xs256.getD 0 0, xs256.getD 1 0, xs256.getD 2 0, xs256.getD 3 0, xs256.getD 4 0, xs256.getD 5 0]

namespace S_15
def pairsG : List (Nat × Nat) := [(1, 3), (1, 5), (1, 9), (2, 3), (4, 5), (6, 7), (6, 14), (8, 9), (10, 11), (10, 14), (12, 13), (12, 14)]
def r1sG : List Nat := [1, 1, 1, 2, 4, 6, 6, 8, 10, 10, 12, 12]
def r2sG : List Nat := [3, 5, 9, 3, 5, 7, 14, 9, 11, 14, 13, 14]
def mpG : Nat := 0xfff
def pool6G : List Nat := []
def xsM : List Nat := roots_15.map (· &&& dom_15)
def goalM : Nat := goal_15 &&& dom_15
def NN : Nat → Nat
  | 2 => 2
  | 3 => 11
  | 4 => 8
  | 5 => 1
  | _ => 0
def HT : Nat → Nat → Nat
  | 2, 0 => 0x8395cb231bc7e878
  | 3, 0 => 0xc7d0175b57e3d3b04f76fdd8345987042a96e68b29bc83021f3844161459a69c110046250a4a9b3404f8ca3e
  | 4, 0 => 0x57e3d3b047d996be2c89b5bf129291b90fdaabe907006be5029550b9006842cf
  | 5, 0 => 0x57e3d3b0
  | _, _ => 0
def dictB : Nat → Nat → Nat
  | 0, 0 => 0x30300000000000000000000000000000000000000000000000000000000000000c0c0000000000000000000000000000000000000000000000000000000000007070000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000005a5a000000000000000000000000000000000000000000000000000000000000cccc000000000000000000000000000000000000000000000000000000000000aaaa0000000000000000000000000000000000000000000000000000000000000ff0
  | 0, 1 => 0xcf00000000000000000000000000000000000000000000000000000000000000fcfc000000000000000000000000000000000000000000000000000000000000c0c0000000000000000000000000000000000000000000000000000000000000ffaa000000000000000000000000000000000000000000000000000000000000f0f0000000000000000000000000000000000000000000000000000000000000aa000000000000000000000000000000000000000000000000000000000000000f0a000000000000000000000000000000000000000000000000000000000000faf0
  | 0, 2 => 0xf000000000000000000000000000000000000000000000000000000000000000a0a000000000000000000000000000000000000000000000000000000000000000cc000000000000000000000000000000000000000000000000000000000000c8c800000000000000000000000000000000000000000000000000000000000044440000000000000000000000000000000000000000000000000000000000002222000000000000000000000000000000000000000000000000000000000000ff30
  | _, _ => 0
def stateB : Nat → Nat → Nat → Nat
  | 2, 0, 0 => 0x821988203
  | 3, 0, 0 => 0x22e61422c41422e51482c4145bc414239a1462c4a4208294220414204e64208254
  | 4, 0, 0 => 0x11620a11620c948bb082ac22c41522c41aa91cb10548b1062a4588345
  | 5, 0, 0 => 0x22c414
  | _, _, _ => 0
def stateW : Nat → Nat
  | 2 => 19
  | 3 => 24
  | 4 => 29
  | 5 => 24
  | _ => 0
def wireAt (i : Nat) : Nat := fld (dictB (i / 128) (i / 8 % 16)) 256 (i % 8)
def dictP1B : Nat → Nat → Nat
  | 0, 0 => 0xc10308c70f80c773680073f0
  | 0, 1 => 0x380f78060f87c70000387c70
  | 0, 2 => 0xc00000068060368007f90
  | _, _ => 0
def dictP2B : Nat → Nat → Nat
  | 0, 0 => 0x412109e52fc4bcdb695bf1b6
  | 0, 1 => 0xbc4f7ba60fffe7258418dff6
  | 0, 2 => 0xe40432029b69a40496fd6
  | _, _ => 0
def p1At (i : Nat) : Nat := fld (dictP1B (i / 128) (i / 8 % 16)) 12 (i % 8)
def p2At (i : Nat) : Nat := fld (dictP2B (i / 128) (i / 8 % 16)) 12 (i % 8)
def wireDAt (i : Nat) : Nat × Nat × Nat :=
  if i < 23 then (wireAt i, p1At i, p2At i) else (0, 0, 0)
def wireDOK (i : Nat) : Bool :=
  (p1At i == projBit r1sG (wireAt i)) && (p2At i == projBit r2sG (wireAt i))
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
theorem wireD_ok_all : span wireDOK 23 0 = true := by decide +kernel
theorem projBit_zero (rs : List Nat) : projBit rs 0 = 0 := by
  induction rs with
  | nil => rfl
  | cons r rs ih => simp only [projBit, List.foldr_cons, Nat.zero_testBit, Bool.false_eq_true, ite_false] at ih ⊢; rw [ih]; rfl
theorem wireDAt_eq (i : Nat) :
    wireDAt i = (let w := if i < 23 then wireAt i else 0; (w, projBit r1sG w, projBit r2sG w)) := by
  unfold wireDAt
  split
  · next hi =>
    have h := span_ok wireD_ok_all i (Nat.zero_le i) (by omega)
    simp only [wireDOK, Bool.and_eq_true, beq_iff_eq] at h
    simp [h.1, h.2]
  · simp [projBit_zero]
def wireSAt (i : Nat) : Nat := if i < 23 then wireAt i else 0
def stateWiresD : Nat → Nat → List (Nat × Nat × Nat)
  | 0, _ => []
  | n + 1, ids => wireDAt (fld ids 5 0) :: stateWiresD n (ids >>> 5)
def stateWiresS : Nat → Nat → List Nat
  | 0, _ => []
  | n + 1, ids => wireSAt (fld ids 5 0) :: stateWiresS n (ids >>> 5)
def SD (s j : Nat) : List (Nat × Nat × Nat) :=
  let packed := fld (stateB s (j / 256) (j / 16 % 16)) (stateW s) (j % 16)
  stateWiresD (packed &&& 15) (packed >>> 4)
def SS (s j : Nat) : List Nat :=
  let packed := fld (stateB s (j / 256) (j / 16 % 16)) (stateW s) (j % 16)
  stateWiresS (packed &&& 15) (packed >>> 4)
theorem stateWiresD_eq (n ids : Nat) :
    stateWiresD n ids = (stateWiresS n ids).map (fun w => (w, projBit r1sG w, projBit r2sG w)) := by
  induction n generalizing ids with
  | zero => rfl
  | succ n ih => simp [stateWiresD, stateWiresS, wireSAt, wireDAt_eq, ih]
theorem SD_eq (s j : Nat) :
    SD s j = (SS s j).map (fun w => (w, projBit r1sG w, projBit r2sG w)) :=
  stateWiresD_eq _ _

def htAt (s i : Nat) : Nat := fld (HT s (i / 64)) 32 (i % 64)
def idxH (s h : Nat) : Nat := bsr (htAt s) h 5 0 (NN s)
def idx (s : Nat) (zs : List Nat) : Nat := idxH s (hk 0 zs)
def CN0 : Nat → Nat
  | _ => 0
def CH0 : Nat → Nat → Nat
  | _, _ => 0
def CV0 : Nat → Nat → Nat
  | _, _ => 0
def ch0At (s i : Nat) : Nat := fld (CH0 s (i / 64)) 32 (i % 64)
def cidx0H (s h : Nat) : Nat := bsr (ch0At s) h 1 0 (CN0 s)
def CN : Nat → Nat
  | _ => 0
def CH : Nat → Nat → Nat
  | _, _ => 0
def CV : Nat → Nat → Nat
  | _, _ => 0
def chAt (s i : Nat) : Nat := fld (CH s (i / 64)) 32 (i % 64)
def cidxH (s h : Nat) : Nat := bsr (chAt s) h 1 0 (CN s)
def checkCutByIdx (s : Nat) (ws : List Nat) (hint : Nat) : Bool :=
  match hint &&& 255 with
  | _ => false
theorem checkCutByIdx_sound {v ys hint} (hc : checkCutByIdx v ys hint = true) : ¬ RunD true dom_15 goalM v ys := by
  unfold checkCutByIdx at hc
  split at hc
  · contradiction
def cutHitH (s h : Nat) (ws : List Nat) : Bool :=
  (let i0 := cidx0H s h; decide (i0 < CN0 s) && (ch0At s i0 == h) && checkCutByIdx s ws (fld (CV0 s (i0 / 128)) 8 (i0 % 128))) ||
  (let i := cidxH s h; decide (i < CN s) && (chAt s i == h) && checkCutByIdx s ws (fld (CV s (i / 32)) 12 (i % 32)))

def cutHit (s : Nat) (ws : List Nat) : Bool := cutHitH s (hk 0 ws) ws

theorem cutHitH_sound {v ys} (h : cutHitH v (hk 0 ys) ys = true) : ¬ RunD true dom_15 goalM v ys := by
  unfold cutHitH at h
  rw [Bool.or_eq_true] at h
  rcases h with h0 | h1
  · simp only [Bool.and_eq_true] at h0; exact checkCutByIdx_sound h0.2
  · simp only [Bool.and_eq_true] at h1; exact checkCutByIdx_sound h1.2

theorem cutHit_sound {v ys} (h : cutHit v ys = true) : ¬ RunD true dom_15 goalM v ys := cutHitH_sound h

def symsG : List (List (Nat × Nat)) := [[(0xf000f000f000f000f000f000f000f000f000f000f000f000f000f000f000f0, 4)], [(0xc0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c, 2)], [(0xcc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc, 6)], [(0xf000f000f000f000f000f000f000f000f000f000f000f000f000f000f000f0, 4), (0xcc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc, 6)], [(0xf000f000f000f000f000f000f000f000f000f000f000f000f000f000f000f0, 4), (0xc0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c, 2)]]
theorem symsG_ok : symsG.all (fun ms => ms.all moveOK256 && (applyMoves ms dom_15 == dom_15) && (applyMoves ms goalM == goalM)) = true := by decide +kernel
def ori (zs : List Nat) : List Nat := pickMin 0 zs symsG zs (hk 0 zs)
theorem ori_ok {v ys} (h : RunD true dom_15 goalM v ys) : RunD true dom_15 goalM v (ori ys) :=
  pickMin_runD 0 ys h symsG ys (hk 0 ys) symsG_ok h

def Z (s : Nat) := bar true dom_15 goalM mpG SD SS NN htAt idxH ori 0 pool6G cutHitH s
private theorem z0 : ∀ i, 0 ≤ i → i < 0 → Z 0 i = true := by omega
private theorem z1 : ∀ i, 0 ≤ i → i < 0 → Z 1 i = true := by omega
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
private theorem z2 : ∀ i, 0 ≤ i → i < 2 → Z 2 i = true := span_ok (by decide +kernel : span (Z 2) 2 0 = true)
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
private theorem z3 : ∀ i, 0 ≤ i → i < 11 → Z 3 i = true := span_ok (by decide +kernel : span (Z 3) 11 0 = true)
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
private theorem z4 : ∀ i, 0 ≤ i → i < 8 → Z 4 i = true := span_ok (by decide +kernel : span (Z 4) 8 0 = true)
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
private theorem z5 : ∀ i, 0 ≤ i → i < 1 → Z 5 i = true := span_ok (by decide +kernel : span (Z 5) 1 0 = true)
theorem checked (s : Nat) (hs : s ≤ 5) : ∀ i < NN s, Z s i = true := by
  interval_cases s
  · exact fun i hi => z0 i (Nat.zero_le i) hi
  · exact fun i hi => z1 i (Nat.zero_le i) hi
  · exact fun i hi => z2 i (Nat.zero_le i) hi
  · exact fun i hi => z3 i (Nat.zero_le i) hi
  · exact fun i hi => z4 i (Nat.zero_le i) hi
  · exact fun i hi => z5 i (Nat.zero_le i) hi
def RootG (s : Nat) : Bool :=
  scr true dom_15 goalM s pool6G xsM || cutHit s (ori xsM) || found SS NN idx s (ori xsM)

set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
theorem rootChecked : span RootG 3 3 = true := by decide +kernel

theorem proper_failG : ∀ zs ∈ xsM.sublists, zs ≠ xsM → unorientedCov pairsG zs = false := by decide +kernel

theorem noRunFull (s : Nat) (hs : s ≤ 5) (h : RunD true dom_15 goalM s xsM) : False := by
  have hmin : 3 ≤ s := by
    have hl := run_len h; change 4 ≤ s + 1 at hl; omega
  have hr := span_ok rootChecked s hmin (by omega)
  unfold RootG at hr
  rw [scr_no pool6G h, Bool.false_or, Bool.or_eq_true] at hr
  rcases hr with hcut | hf
  · exact cutHit_sound hcut (ori_ok h)
  · rw [found, Bool.and_eq_true, decide_eq_true_eq, List.isPerm_iff] at hf
    exact bar_all (pairs := pairsG) (by decide +kernel) rfl rfl (by decide +kernel) SD_eq (by decide +kernel) ori_ok cutHitH_sound checked s hs _ hf.1 (Run.perm hf.2 (ori_ok h))

theorem noCircuit : Lower true dom_15 roots_15 goal_15 6 := by
  intro p bank hr ha
  by_contra! hsmall
  have hnc : ¬ IsConst dom_15 goal_15 := by
    have h0 : isConstB dom_15 goal_15 = false := by decide +kernel
    intro h; rw [(isConstB_iff _ _).2 h] at h0; contradiction
  obtain ⟨s, ws, hs_le, hnd, hws_sub, hrun⟩ := reach_to_run (by decide +kernel) (by decide +kernel) (by decide +kernel) (by decide +kernel) hnc hr ha
  have hperm_sub : ∃ zs, zs.Sublist xsM ∧ ws.Perm zs := by
    refine ⟨xsM.filter (fun x => decide (x ∈ ws)), List.filter_sublist, ?_⟩
    refine (List.perm_ext_iff_of_nodup hnd (List.Nodup.filter _ (by decide +kernel : xsM.Nodup))).2 ?_
    intro x; simp only [List.mem_filter, decide_eq_true_eq]
    exact ⟨fun hx => ⟨hws_sub x hx, hx⟩, fun h => h.2⟩
  obtain ⟨zs, hsub, hpz⟩ := hperm_sub
  have hrun' := Run.perm hpz hrun
  by_cases heq : zs = xsM
  · subst heq; exact noRunFull s (by omega) hrun'
  · have hcov := unorientedCov_ok (by decide +kernel) pairsG (by decide +kernel) hrun'
    rw [proper_failG zs (List.mem_sublists.2 hsub) heq] at hcov; contradiction

end S_15

theorem lowS_15 : Lower true dom_15 roots_15 goal_15 6 := S_15.noCircuit

namespace S_23
def pairsG : List (Nat × Nat) := [(1, 3), (1, 5), (1, 17), (2, 3), (4, 5), (6, 7), (6, 22), (16, 17), (18, 19), (18, 22), (20, 21), (20, 22)]
def r1sG : List Nat := [1, 1, 1, 2, 4, 6, 6, 16, 18, 18, 20, 20]
def r2sG : List Nat := [3, 5, 17, 3, 5, 7, 22, 17, 19, 22, 21, 22]
def mpG : Nat := 0xfff
def pool6G : List Nat := []
def xsM : List Nat := roots_23.map (· &&& dom_23)
def goalM : Nat := goal_23 &&& dom_23
def NN : Nat → Nat
  | 2 => 2
  | 3 => 11
  | 4 => 8
  | 5 => 1
  | _ => 0
def HT : Nat → Nat → Nat
  | 2, 0 => 0xc5153b3837447179
  | 3, 0 => 0xb98739f591a1d7f147c9fc02425705fd41ed9eeb3c0d98163be0ba2e1814cc4e17eb013413c18a93002f8e5c
  | 4, 0 => 0xb98739f5b9049c2f6433215062ad44e0521f5dd5155da40209910b870051eb12
  | 5, 0 => 0xb98739f5
  | _, _ => 0
def dictB : Nat → Nat → Nat
  | 0, 0 => 0xcc000c0000000000000000000000000000000000000000000000000000000000f000a00000000000000000000000000000000000000000000000000000000000cc00cc0000000000000000000000000000000000000000000000000000000000f000f000000000000000000000000000000000000000000000000000000000006600660000000000000000000000000000000000000000000000000000000000ff00000000000000000000000000000000000000000000000000000000000000aa00aa00000000000000000000000000000000000000000000000000000000003c003c
  | 0, 1 => 0x2200220000000000000000000000000000000000000000000000000000000000ee00ee000000000000000000000000000000000000000000000000000000000088008800000000000000000000000000000000000000000000000000000000005f00000000000000000000000000000000000000000000000000000000000000fa00f000000000000000000000000000000000000000000000000000000000003300220000000000000000000000000000000000000000000000000000000000fc00fc0000000000000000000000000000000000000000000000000000000000c000c0
  | 0, 2 => 0xff00cc00000000000000000000000000000000000000000000000000000000000a000a0000000000000000000000000000000000000000000000000000000000ff00aa00000000000000000000000000000000000000000000000000000000000c000c00000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000cf00cc0000000000000000000000000000000000000000000000000000000000440044
  | _, _ => 0
def stateB : Nat → Nat → Nat → Nat
  | 2, 0, 0 => 0x441988203
  | 3, 0, 0 => 0x110a142867241122141120f4111cd42142c412ca141102a4125014110e14118a14
  | 4, 0, 0 => 0x8850a08850b56e22142a2214365a88850a88854054442868a2214305
  | 5, 0, 0 => 0x110a14
  | _, _, _ => 0
def stateW : Nat → Nat
  | 2 => 19
  | 3 => 24
  | 4 => 29
  | 5 => 24
  | _ => 0
def wireAt (i : Nat) : Nat := fld (dictB (i / 128) (i / 8 % 16)) 256 (i % 8)
def dictP1B : Nat → Nat → Nat
  | 0, 0 => 0x308c00368c7036ff80007f18
  | 0, 1 => 0x736f000f80c70c87f78060
  | 0, 2 => 0xfe8007f873083800703e8368
  | _, _ => 0
def dictP2B : Nat → Nat → Nat
  | 0, 0 => 0xb49e72b69e72ed6fc45bf51b
  | 0, 1 => 0x496fff129bc4ff6496f7ba60
  | 0, 2 => 0xfed18dfff109184032beda40
  | _, _ => 0
def p1At (i : Nat) : Nat := fld (dictP1B (i / 128) (i / 8 % 16)) 12 (i % 8)
def p2At (i : Nat) : Nat := fld (dictP2B (i / 128) (i / 8 % 16)) 12 (i % 8)
def wireDAt (i : Nat) : Nat × Nat × Nat :=
  if i < 24 then (wireAt i, p1At i, p2At i) else (0, 0, 0)
def wireDOK (i : Nat) : Bool :=
  (p1At i == projBit r1sG (wireAt i)) && (p2At i == projBit r2sG (wireAt i))
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
theorem wireD_ok_all : span wireDOK 24 0 = true := by decide +kernel
theorem projBit_zero (rs : List Nat) : projBit rs 0 = 0 := by
  induction rs with
  | nil => rfl
  | cons r rs ih => simp only [projBit, List.foldr_cons, Nat.zero_testBit, Bool.false_eq_true, ite_false] at ih ⊢; rw [ih]; rfl
theorem wireDAt_eq (i : Nat) :
    wireDAt i = (let w := if i < 24 then wireAt i else 0; (w, projBit r1sG w, projBit r2sG w)) := by
  unfold wireDAt
  split
  · next hi =>
    have h := span_ok wireD_ok_all i (Nat.zero_le i) (by omega)
    simp only [wireDOK, Bool.and_eq_true, beq_iff_eq] at h
    simp [h.1, h.2]
  · simp [projBit_zero]
def wireSAt (i : Nat) : Nat := if i < 24 then wireAt i else 0
def stateWiresD : Nat → Nat → List (Nat × Nat × Nat)
  | 0, _ => []
  | n + 1, ids => wireDAt (fld ids 5 0) :: stateWiresD n (ids >>> 5)
def stateWiresS : Nat → Nat → List Nat
  | 0, _ => []
  | n + 1, ids => wireSAt (fld ids 5 0) :: stateWiresS n (ids >>> 5)
def SD (s j : Nat) : List (Nat × Nat × Nat) :=
  let packed := fld (stateB s (j / 256) (j / 16 % 16)) (stateW s) (j % 16)
  stateWiresD (packed &&& 15) (packed >>> 4)
def SS (s j : Nat) : List Nat :=
  let packed := fld (stateB s (j / 256) (j / 16 % 16)) (stateW s) (j % 16)
  stateWiresS (packed &&& 15) (packed >>> 4)
theorem stateWiresD_eq (n ids : Nat) :
    stateWiresD n ids = (stateWiresS n ids).map (fun w => (w, projBit r1sG w, projBit r2sG w)) := by
  induction n generalizing ids with
  | zero => rfl
  | succ n ih => simp [stateWiresD, stateWiresS, wireSAt, wireDAt_eq, ih]
theorem SD_eq (s j : Nat) :
    SD s j = (SS s j).map (fun w => (w, projBit r1sG w, projBit r2sG w)) :=
  stateWiresD_eq _ _

def htAt (s i : Nat) : Nat := fld (HT s (i / 64)) 32 (i % 64)
def idxH (s h : Nat) : Nat := bsr (htAt s) h 5 0 (NN s)
def idx (s : Nat) (zs : List Nat) : Nat := idxH s (hk 0 zs)
def CN0 : Nat → Nat
  | _ => 0
def CH0 : Nat → Nat → Nat
  | _, _ => 0
def CV0 : Nat → Nat → Nat
  | _, _ => 0
def ch0At (s i : Nat) : Nat := fld (CH0 s (i / 64)) 32 (i % 64)
def cidx0H (s h : Nat) : Nat := bsr (ch0At s) h 1 0 (CN0 s)
def CN : Nat → Nat
  | _ => 0
def CH : Nat → Nat → Nat
  | _, _ => 0
def CV : Nat → Nat → Nat
  | _, _ => 0
def chAt (s i : Nat) : Nat := fld (CH s (i / 64)) 32 (i % 64)
def cidxH (s h : Nat) : Nat := bsr (chAt s) h 1 0 (CN s)
def checkCutByIdx (s : Nat) (ws : List Nat) (hint : Nat) : Bool :=
  match hint &&& 255 with
  | _ => false
theorem checkCutByIdx_sound {v ys hint} (hc : checkCutByIdx v ys hint = true) : ¬ RunD true dom_23 goalM v ys := by
  unfold checkCutByIdx at hc
  split at hc
  · contradiction
def cutHitH (s h : Nat) (ws : List Nat) : Bool :=
  (let i0 := cidx0H s h; decide (i0 < CN0 s) && (ch0At s i0 == h) && checkCutByIdx s ws (fld (CV0 s (i0 / 128)) 8 (i0 % 128))) ||
  (let i := cidxH s h; decide (i < CN s) && (chAt s i == h) && checkCutByIdx s ws (fld (CV s (i / 32)) 12 (i % 32)))

def cutHit (s : Nat) (ws : List Nat) : Bool := cutHitH s (hk 0 ws) ws

theorem cutHitH_sound {v ys} (h : cutHitH v (hk 0 ys) ys = true) : ¬ RunD true dom_23 goalM v ys := by
  unfold cutHitH at h
  rw [Bool.or_eq_true] at h
  rcases h with h0 | h1
  · simp only [Bool.and_eq_true] at h0; exact checkCutByIdx_sound h0.2
  · simp only [Bool.and_eq_true] at h1; exact checkCutByIdx_sound h1.2

theorem cutHit_sound {v ys} (h : cutHit v ys = true) : ¬ RunD true dom_23 goalM v ys := cutHitH_sound h

def symsG : List (List (Nat × Nat)) := [[(0xf0f00000f0f00000f0f00000f0f00000f0f00000f0f00000f0f00000f0f0, 12)], [(0xc0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c, 2)], [(0xcccc0000cccc0000cccc0000cccc0000cccc0000cccc0000cccc0000cccc, 14)], [(0xf0f00000f0f00000f0f00000f0f00000f0f00000f0f00000f0f00000f0f0, 12), (0xcccc0000cccc0000cccc0000cccc0000cccc0000cccc0000cccc0000cccc, 14)], [(0xf0f00000f0f00000f0f00000f0f00000f0f00000f0f00000f0f00000f0f0, 12), (0xc0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c, 2)]]
theorem symsG_ok : symsG.all (fun ms => ms.all moveOK256 && (applyMoves ms dom_23 == dom_23) && (applyMoves ms goalM == goalM)) = true := by decide +kernel
def ori (zs : List Nat) : List Nat := pickMin 0 zs symsG zs (hk 0 zs)
theorem ori_ok {v ys} (h : RunD true dom_23 goalM v ys) : RunD true dom_23 goalM v (ori ys) :=
  pickMin_runD 0 ys h symsG ys (hk 0 ys) symsG_ok h

def Z (s : Nat) := bar true dom_23 goalM mpG SD SS NN htAt idxH ori 0 pool6G cutHitH s
private theorem z0 : ∀ i, 0 ≤ i → i < 0 → Z 0 i = true := by omega
private theorem z1 : ∀ i, 0 ≤ i → i < 0 → Z 1 i = true := by omega
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
private theorem z2 : ∀ i, 0 ≤ i → i < 2 → Z 2 i = true := span_ok (by decide +kernel : span (Z 2) 2 0 = true)
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
private theorem z3 : ∀ i, 0 ≤ i → i < 11 → Z 3 i = true := span_ok (by decide +kernel : span (Z 3) 11 0 = true)
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
private theorem z4 : ∀ i, 0 ≤ i → i < 8 → Z 4 i = true := span_ok (by decide +kernel : span (Z 4) 8 0 = true)
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
private theorem z5 : ∀ i, 0 ≤ i → i < 1 → Z 5 i = true := span_ok (by decide +kernel : span (Z 5) 1 0 = true)
theorem checked (s : Nat) (hs : s ≤ 5) : ∀ i < NN s, Z s i = true := by
  interval_cases s
  · exact fun i hi => z0 i (Nat.zero_le i) hi
  · exact fun i hi => z1 i (Nat.zero_le i) hi
  · exact fun i hi => z2 i (Nat.zero_le i) hi
  · exact fun i hi => z3 i (Nat.zero_le i) hi
  · exact fun i hi => z4 i (Nat.zero_le i) hi
  · exact fun i hi => z5 i (Nat.zero_le i) hi
def RootG (s : Nat) : Bool :=
  scr true dom_23 goalM s pool6G xsM || cutHit s (ori xsM) || found SS NN idx s (ori xsM)

set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
theorem rootChecked : span RootG 3 3 = true := by decide +kernel

theorem proper_failG : ∀ zs ∈ xsM.sublists, zs ≠ xsM → unorientedCov pairsG zs = false := by decide +kernel

theorem noRunFull (s : Nat) (hs : s ≤ 5) (h : RunD true dom_23 goalM s xsM) : False := by
  have hmin : 3 ≤ s := by
    have hl := run_len h; change 4 ≤ s + 1 at hl; omega
  have hr := span_ok rootChecked s hmin (by omega)
  unfold RootG at hr
  rw [scr_no pool6G h, Bool.false_or, Bool.or_eq_true] at hr
  rcases hr with hcut | hf
  · exact cutHit_sound hcut (ori_ok h)
  · rw [found, Bool.and_eq_true, decide_eq_true_eq, List.isPerm_iff] at hf
    exact bar_all (pairs := pairsG) (by decide +kernel) rfl rfl (by decide +kernel) SD_eq (by decide +kernel) ori_ok cutHitH_sound checked s hs _ hf.1 (Run.perm hf.2 (ori_ok h))

theorem noCircuit : Lower true dom_23 roots_23 goal_23 6 := by
  intro p bank hr ha
  by_contra! hsmall
  have hnc : ¬ IsConst dom_23 goal_23 := by
    have h0 : isConstB dom_23 goal_23 = false := by decide +kernel
    intro h; rw [(isConstB_iff _ _).2 h] at h0; contradiction
  obtain ⟨s, ws, hs_le, hnd, hws_sub, hrun⟩ := reach_to_run (by decide +kernel) (by decide +kernel) (by decide +kernel) (by decide +kernel) hnc hr ha
  have hperm_sub : ∃ zs, zs.Sublist xsM ∧ ws.Perm zs := by
    refine ⟨xsM.filter (fun x => decide (x ∈ ws)), List.filter_sublist, ?_⟩
    refine (List.perm_ext_iff_of_nodup hnd (List.Nodup.filter _ (by decide +kernel : xsM.Nodup))).2 ?_
    intro x; simp only [List.mem_filter, decide_eq_true_eq]
    exact ⟨fun hx => ⟨hws_sub x hx, hx⟩, fun h => h.2⟩
  obtain ⟨zs, hsub, hpz⟩ := hperm_sub
  have hrun' := Run.perm hpz hrun
  by_cases heq : zs = xsM
  · subst heq; exact noRunFull s (by omega) hrun'
  · have hcov := unorientedCov_ok (by decide +kernel) pairsG (by decide +kernel) hrun'
    rw [proper_failG zs (List.mem_sublists.2 hsub) heq] at hcov; contradiction

end S_23

theorem lowS_23 : Lower true dom_23 roots_23 goal_23 6 := S_23.noCircuit

namespace S_27
def pairsG : List (Nat × Nat) := [(1, 3), (1, 9), (1, 17), (2, 3), (8, 9), (10, 11), (10, 26), (16, 17), (18, 19), (18, 26), (24, 25), (24, 26)]
def r1sG : List Nat := [1, 1, 1, 2, 8, 10, 10, 16, 18, 18, 24, 24]
def r2sG : List Nat := [3, 9, 17, 3, 9, 11, 26, 17, 19, 26, 25, 26]
def mpG : Nat := 0xfff
def pool6G : List Nat := []
def xsM : List Nat := roots_27.map (· &&& dom_27)
def goalM : Nat := goal_27 &&& dom_27
def NN : Nat → Nat
  | 2 => 2
  | 3 => 11
  | 4 => 8
  | 5 => 1
  | _ => 0
def HT : Nat → Nat → Nat
  | 2, 0 => 0x8e339dbc21bad7fd
  | 3, 0 => 0x9d277db192b669203734731c262c6e4921b3afde205d852e1c41677216a5493a1288e76e019df92000be1cca
  | 4, 0 => 0x9d277db1629e221b4dec4760464d889c3ba977c9256ff9441a9db4f605d02eb9
  | 5, 0 => 0x9d277db1
  | _, _ => 0
def dictB : Nat → Nat → Nat
  | 0, 0 => 0xf0f0000000000000000000000000000000000000000000000000000000000000300030000000000000000000000000000000000000000000000000000000000000c000c000000000000000000000000000000000000000000000000000000000a0a0a0a00000000000000000000000000000000000000000000000000000000000f0f00000000000000000000000000000000000000000000000000000000000f000f00000000000000000000000000000000000000000000000000000000000c0c0c0c0000000000000000000000000000000000000000000000000000000005050a0a
  | 0, 1 => 0x2020202000000000000000000000000000000000000000000000000000000000f0f0f00000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f0a00000000000000000000000000000000000000000000000000000000000003030202000000000000000000000000000000000000000000000000000000000f000f0c0000000000000000000000000000000000000000000000000000000007070000000000000000000000000000000000000000000000000000000000000f000300
  | 0, 2 => 0xc000c0000000000000000000000000000000000000000000000000000000000000a000a0000000000000000000000000000000000000000000000000000000008080808000000000000000000000000000000000000000000000000000000000f080f08000000000000000000000000000000000000000000000000000000000f0a0f0a000000000000000000000000000000000000000000000000000000000a000a000000000000000000000000000000000000000000000000000000000004040404
  | _, _ => 0
def stateB : Nat → Nat → Nat → Nat
  | 2, 0, 0 => 0x241988203
  | 3, 0, 0 => 0x3882443cc2443c831438a0f47342446082443888b43a82441048943a0244390c54
  | 4, 0, 0 => 0x1c41221c412194e20d88a710495538824829e420915c71048a7104945
  | 5, 0, 0 => 0x388244
  | _, _, _ => 0
def stateW : Nat → Nat
  | 2 => 19
  | 3 => 24
  | 4 => 29
  | 5 => 24
  | _ => 0
def wireAt (i : Nat) : Nat := fld (dictB (i / 128) (i / 8 % 16)) 256 (i % 8)
def dictP1B : Nat → Nat → Nat
  | 0, 0 => 0xf80c103080073f0c70368f87
  | 0, 1 => 0x7ff0c00c00c87c78f80c10
  | 0, 2 => 0x60007000c70c77000368
  | _, _ => 0
def dictP2B : Nat → Nat → Nat
  | 0, 0 => 0xfc44121095bf1b6e72b69a7b
  | 0, 1 => 0x496ff6e40fc4496e7bec4e52
  | 0, 2 => 0xa6018d129f7bfff432a40
  | _, _ => 0
def p1At (i : Nat) : Nat := fld (dictP1B (i / 128) (i / 8 % 16)) 12 (i % 8)
def p2At (i : Nat) : Nat := fld (dictP2B (i / 128) (i / 8 % 16)) 12 (i % 8)
def wireDAt (i : Nat) : Nat × Nat × Nat :=
  if i < 23 then (wireAt i, p1At i, p2At i) else (0, 0, 0)
def wireDOK (i : Nat) : Bool :=
  (p1At i == projBit r1sG (wireAt i)) && (p2At i == projBit r2sG (wireAt i))
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
theorem wireD_ok_all : span wireDOK 23 0 = true := by decide +kernel
theorem projBit_zero (rs : List Nat) : projBit rs 0 = 0 := by
  induction rs with
  | nil => rfl
  | cons r rs ih => simp only [projBit, List.foldr_cons, Nat.zero_testBit, Bool.false_eq_true, ite_false] at ih ⊢; rw [ih]; rfl
theorem wireDAt_eq (i : Nat) :
    wireDAt i = (let w := if i < 23 then wireAt i else 0; (w, projBit r1sG w, projBit r2sG w)) := by
  unfold wireDAt
  split
  · next hi =>
    have h := span_ok wireD_ok_all i (Nat.zero_le i) (by omega)
    simp only [wireDOK, Bool.and_eq_true, beq_iff_eq] at h
    simp [h.1, h.2]
  · simp [projBit_zero]
def wireSAt (i : Nat) : Nat := if i < 23 then wireAt i else 0
def stateWiresD : Nat → Nat → List (Nat × Nat × Nat)
  | 0, _ => []
  | n + 1, ids => wireDAt (fld ids 5 0) :: stateWiresD n (ids >>> 5)
def stateWiresS : Nat → Nat → List Nat
  | 0, _ => []
  | n + 1, ids => wireSAt (fld ids 5 0) :: stateWiresS n (ids >>> 5)
def SD (s j : Nat) : List (Nat × Nat × Nat) :=
  let packed := fld (stateB s (j / 256) (j / 16 % 16)) (stateW s) (j % 16)
  stateWiresD (packed &&& 15) (packed >>> 4)
def SS (s j : Nat) : List Nat :=
  let packed := fld (stateB s (j / 256) (j / 16 % 16)) (stateW s) (j % 16)
  stateWiresS (packed &&& 15) (packed >>> 4)
theorem stateWiresD_eq (n ids : Nat) :
    stateWiresD n ids = (stateWiresS n ids).map (fun w => (w, projBit r1sG w, projBit r2sG w)) := by
  induction n generalizing ids with
  | zero => rfl
  | succ n ih => simp [stateWiresD, stateWiresS, wireSAt, wireDAt_eq, ih]
theorem SD_eq (s j : Nat) :
    SD s j = (SS s j).map (fun w => (w, projBit r1sG w, projBit r2sG w)) :=
  stateWiresD_eq _ _

def htAt (s i : Nat) : Nat := fld (HT s (i / 64)) 32 (i % 64)
def idxH (s h : Nat) : Nat := bsr (htAt s) h 5 0 (NN s)
def idx (s : Nat) (zs : List Nat) : Nat := idxH s (hk 0 zs)
def CN0 : Nat → Nat
  | _ => 0
def CH0 : Nat → Nat → Nat
  | _, _ => 0
def CV0 : Nat → Nat → Nat
  | _, _ => 0
def ch0At (s i : Nat) : Nat := fld (CH0 s (i / 64)) 32 (i % 64)
def cidx0H (s h : Nat) : Nat := bsr (ch0At s) h 1 0 (CN0 s)
def CN : Nat → Nat
  | _ => 0
def CH : Nat → Nat → Nat
  | _, _ => 0
def CV : Nat → Nat → Nat
  | _, _ => 0
def chAt (s i : Nat) : Nat := fld (CH s (i / 64)) 32 (i % 64)
def cidxH (s h : Nat) : Nat := bsr (chAt s) h 1 0 (CN s)
def checkCutByIdx (s : Nat) (ws : List Nat) (hint : Nat) : Bool :=
  match hint &&& 255 with
  | _ => false
theorem checkCutByIdx_sound {v ys hint} (hc : checkCutByIdx v ys hint = true) : ¬ RunD true dom_27 goalM v ys := by
  unfold checkCutByIdx at hc
  split at hc
  · contradiction
def cutHitH (s h : Nat) (ws : List Nat) : Bool :=
  (let i0 := cidx0H s h; decide (i0 < CN0 s) && (ch0At s i0 == h) && checkCutByIdx s ws (fld (CV0 s (i0 / 128)) 8 (i0 % 128))) ||
  (let i := cidxH s h; decide (i < CN s) && (chAt s i == h) && checkCutByIdx s ws (fld (CV s (i / 32)) 12 (i % 32)))

def cutHit (s : Nat) (ws : List Nat) : Bool := cutHitH s (hk 0 ws) ws

theorem cutHitH_sound {v ys} (h : cutHitH v (hk 0 ys) ys = true) : ¬ RunD true dom_27 goalM v ys := by
  unfold cutHitH at h
  rw [Bool.or_eq_true] at h
  rcases h with h0 | h1
  · simp only [Bool.and_eq_true] at h0; exact checkCutByIdx_sound h0.2
  · simp only [Bool.and_eq_true] at h1; exact checkCutByIdx_sound h1.2

theorem cutHit_sound {v ys} (h : cutHit v ys = true) : ¬ RunD true dom_27 goalM v ys := cutHitH_sound h

def symsG : List (List (Nat × Nat)) := [[(0xff000000ff000000ff000000ff000000ff000000ff000000ff000000ff00, 8)], [(0xcc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc, 6)], [(0xcccc0000cccc0000cccc0000cccc0000cccc0000cccc0000cccc0000cccc, 14)], [(0xff000000ff000000ff000000ff000000ff000000ff000000ff000000ff00, 8), (0xcccc0000cccc0000cccc0000cccc0000cccc0000cccc0000cccc0000cccc, 14)], [(0xff000000ff000000ff000000ff000000ff000000ff000000ff000000ff00, 8), (0xcc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc00cc, 6)]]
theorem symsG_ok : symsG.all (fun ms => ms.all moveOK256 && (applyMoves ms dom_27 == dom_27) && (applyMoves ms goalM == goalM)) = true := by decide +kernel
def ori (zs : List Nat) : List Nat := pickMin 0 zs symsG zs (hk 0 zs)
theorem ori_ok {v ys} (h : RunD true dom_27 goalM v ys) : RunD true dom_27 goalM v (ori ys) :=
  pickMin_runD 0 ys h symsG ys (hk 0 ys) symsG_ok h

def Z (s : Nat) := bar true dom_27 goalM mpG SD SS NN htAt idxH ori 0 pool6G cutHitH s
private theorem z0 : ∀ i, 0 ≤ i → i < 0 → Z 0 i = true := by omega
private theorem z1 : ∀ i, 0 ≤ i → i < 0 → Z 1 i = true := by omega
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
private theorem z2 : ∀ i, 0 ≤ i → i < 2 → Z 2 i = true := span_ok (by decide +kernel : span (Z 2) 2 0 = true)
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
private theorem z3 : ∀ i, 0 ≤ i → i < 11 → Z 3 i = true := span_ok (by decide +kernel : span (Z 3) 11 0 = true)
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
private theorem z4 : ∀ i, 0 ≤ i → i < 8 → Z 4 i = true := span_ok (by decide +kernel : span (Z 4) 8 0 = true)
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
private theorem z5 : ∀ i, 0 ≤ i → i < 1 → Z 5 i = true := span_ok (by decide +kernel : span (Z 5) 1 0 = true)
theorem checked (s : Nat) (hs : s ≤ 5) : ∀ i < NN s, Z s i = true := by
  interval_cases s
  · exact fun i hi => z0 i (Nat.zero_le i) hi
  · exact fun i hi => z1 i (Nat.zero_le i) hi
  · exact fun i hi => z2 i (Nat.zero_le i) hi
  · exact fun i hi => z3 i (Nat.zero_le i) hi
  · exact fun i hi => z4 i (Nat.zero_le i) hi
  · exact fun i hi => z5 i (Nat.zero_le i) hi
def RootG (s : Nat) : Bool :=
  scr true dom_27 goalM s pool6G xsM || cutHit s (ori xsM) || found SS NN idx s (ori xsM)

set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
theorem rootChecked : span RootG 3 3 = true := by decide +kernel

theorem proper_failG : ∀ zs ∈ xsM.sublists, zs ≠ xsM → unorientedCov pairsG zs = false := by decide +kernel

theorem noRunFull (s : Nat) (hs : s ≤ 5) (h : RunD true dom_27 goalM s xsM) : False := by
  have hmin : 3 ≤ s := by
    have hl := run_len h; change 4 ≤ s + 1 at hl; omega
  have hr := span_ok rootChecked s hmin (by omega)
  unfold RootG at hr
  rw [scr_no pool6G h, Bool.false_or, Bool.or_eq_true] at hr
  rcases hr with hcut | hf
  · exact cutHit_sound hcut (ori_ok h)
  · rw [found, Bool.and_eq_true, decide_eq_true_eq, List.isPerm_iff] at hf
    exact bar_all (pairs := pairsG) (by decide +kernel) rfl rfl (by decide +kernel) SD_eq (by decide +kernel) ori_ok cutHitH_sound checked s hs _ hf.1 (Run.perm hf.2 (ori_ok h))

theorem noCircuit : Lower true dom_27 roots_27 goal_27 6 := by
  intro p bank hr ha
  by_contra! hsmall
  have hnc : ¬ IsConst dom_27 goal_27 := by
    have h0 : isConstB dom_27 goal_27 = false := by decide +kernel
    intro h; rw [(isConstB_iff _ _).2 h] at h0; contradiction
  obtain ⟨s, ws, hs_le, hnd, hws_sub, hrun⟩ := reach_to_run (by decide +kernel) (by decide +kernel) (by decide +kernel) (by decide +kernel) hnc hr ha
  have hperm_sub : ∃ zs, zs.Sublist xsM ∧ ws.Perm zs := by
    refine ⟨xsM.filter (fun x => decide (x ∈ ws)), List.filter_sublist, ?_⟩
    refine (List.perm_ext_iff_of_nodup hnd (List.Nodup.filter _ (by decide +kernel : xsM.Nodup))).2 ?_
    intro x; simp only [List.mem_filter, decide_eq_true_eq]
    exact ⟨fun hx => ⟨hws_sub x hx, hx⟩, fun h => h.2⟩
  obtain ⟨zs, hsub, hpz⟩ := hperm_sub
  have hrun' := Run.perm hpz hrun
  by_cases heq : zs = xsM
  · subst heq; exact noRunFull s (by omega) hrun'
  · have hcov := unorientedCov_ok (by decide +kernel) pairsG (by decide +kernel) hrun'
    rw [proper_failG zs (List.mem_sublists.2 hsub) heq] at hcov; contradiction

end S_27

theorem lowS_27 : Lower true dom_27 roots_27 goal_27 6 := S_27.noCircuit

namespace S_31
def pairsG : List (Nat × Nat) := [(1, 3), (1, 5), (1, 9), (1, 17), (2, 3), (4, 5), (6, 7), (6, 14), (6, 22), (8, 9), (10, 11), (10, 14), (10, 26), (12, 13), (12, 14), (16, 17), (18, 19), (18, 22), (18, 26), (20, 21), (20, 22), (24, 25), (24, 26), (28, 29), (28, 30)]
def r1sG : List Nat := [1, 1, 1, 1, 2, 4, 6, 6, 6, 8, 10, 10, 10, 12, 12, 16, 18, 18, 18, 20, 20, 24, 24, 28, 28]
def r2sG : List Nat := [3, 5, 9, 17, 3, 5, 7, 14, 22, 9, 11, 14, 26, 13, 14, 17, 19, 22, 26, 21, 22, 25, 26, 29, 30]
def mpG : Nat := 0x1ffffff
def pool6G : List Nat := []
def xsM : List Nat := roots_31.map (· &&& dom_31)
def goalM : Nat := goal_31 &&& dom_31
def NN : Nat → Nat
  | 3 => 59
  | 4 => 380
  | 5 => 545
  | 6 => 143
  | 7 => 10
  | 8 => 1
  | _ => 0
def HT : Nat → Nat → Nat
  | 3, 0 => 0xb70bd9bfb5895c66a495ce119a3aabaa927ae5a280831bba7c4082617561ddfd6851a24d63dd4cf263b76bb2580ade9754289f4150b48061500e336a4dc85e7949935c2746cd46f442f7afb2397c8eb73836fc5934fa787c3165a7b02e9771932ca6fdcb2c8efb3829ce88042671552923d809b0223c52d71eb7efdb1e8341f51bd4367a1b1317d71a7edb6c1852324918418525179f342813e6234612e84abe109d397c104ba1880fe4742e0fb430b80dae0ce10c5d915f0ae7f7ae09f3a2a809399ee107e966cb07c6294606d66e3c06390446057bc67b043df202043c730d04376ee603d74dd9009b50dc
  | 4, 0 => 0xb5e23960b2d29630afd682a0afb1cb90a6f4b640a6aa4d509eb67ec0991d6ae097c82d6096caae00960696909548af909393702090a225108eac0f70844b0d708409c3508404deb08283b6c079e77c60766115b07595a5b071cf0e306e07fc706d24cb906cc598906cb0e1f06666ee2063fd31206385a6b05bd354c05884ec505327cfa0506f90004f4d60b04e542840457737403ce1ff0039a3870037e3bec0320060e030ef44a0301a22802eedaa102e524a102c3321f02a367b90235fc3b022a66050227345b01e967ec01e69cb301d040ea012c59ef010fafbc010865e60102e41200f15a3b00e7bbde00c7451b00a6d3a700989d0a00652a940002878b
  | 4, 1 => 0x1a2a0b961a0be08119e315ae19b41f9b190ab3fe1770d76f171750fc170c8465170044ca16ea0a2a165e55241632eac615cae8221572a7d61565139e14b51926138498a4135efc9613213bf5131b3c9712bfc0df1298eaf212551c931237c55e1216bfb011fdc44411d9905611cc994b11759b5410de97a010ccb7fb10c5a5b310af857b10a3cb51108016d41078bbb5102861ba0fd2e65a0faa86100f9501ce0f2fbc530f241d6d0f006db40ee63a450eb5a68a0e1905470e18a31c0de915470d8e799c0d6077420d2dc9420d2bd7c90cf640a30ceffc590cc705f20cc1cfa50cb5e3130c9635c00c2fbc350c274caf0bfdc4650bd723bc0bac1b970b833d31
  | 4, 2 => 0x287e4e9a284c7d132823bf55281e4e6b278adc7227588a0a2744c2de26a764ce268471dc267cd3c02671552925d5ea9125733f982564834d255839382539c5b024d9a4a324690fdf2462042324177ac123be5ca923a9e06b23a162b42395a675237f4d372355da20230c05602301b654223c52d722181eca221003dc220c8f1321dc546f2188c649212bd14a210d14bf20cbb03d20aa0a611fe5639a1f9cc93e1f9967441eba60ce1e935e741e8341f51dedd3371de31c781d3cc9fb1d1cccf01d1823381caef25a1c43492f1c108f921bf44b9b1bcdad011b978f7f1b80b9b31b33eb991b02dc951ad620e91aa8bce31a6f3f651a500f261a408d241a3c98a5
  | 4, 3 => 0x443f6171441b53454344c51c42f609f442dc5d6d415626354111b6ca4101cad440f5e4403fe0dad33fdb7be73fa4c7753f1f27953e74c82e3d1c80843cb81ad83b9138e73b2b633f3b12b7d23ae3642839ef9673393738e93728f49836f47950368841ef364724a535e4ee0335e12e7335cbe30b354ab3153531363934fc56e634d89dbe344642a233e97cd2337fa951336438e532fcc48f32e4c3c431b6eda430e6caf830cc3bd930aef3e030ab5c51305c924f304514382fa540bd2efec1172e91b3f52e29117d2e18ebaa2d8a24d32c7f0f1b2b05a3f62b0125e42aef06352a9f785f29f0298a2956b46928f2c06828c55d5628b7469928b3499d28851a51
  | 4, 4 => 0x6447ec6c642830f263711b0a636de8a66344e096625632de6127665760403ce36005a8176004ba8a5fa3abef5f5f5b205e6514435d9be30f5d67f13c5cf264055bce14ad5badcc805b480f965a7ee5815a1b17dc598b1243596ca7b959655e3858287e7e57f3cce254ca58d35450681153f9193f53ecd041535af12a52a5bfe25252f3b251befa8351889709512837e85127bab351208fb4500e336a4f5eda304f442bd54dc579454dbfa5da4d7ca3f24d0a842f4c8556674c2147af4b5c56044a3c0cab4a057c7049ac97fc49642bc6495b514a492045e0486009fd485c8dc647a922354784cab3474b36574738a7a246b5fb60460f45a645bfe93b44c533c4
  | 4, 5 => 0xfeed7000f483970ff2e9ba80ebaaa286dddacfb5c4bdc41bbfd59e83bb49b823b74dbc18b1ae5228b0f1501baff2ec2eaceb272cab514a9da8c14456a067d9e39b6fddd99b44aa6699ccb9b2941f83ae93946ceb927ae5a291b582e18eb8a3198e3842f88d14db958bdc80d68bd5fae688d874d58503381984dc78ca83f04f3d8248a79e81871c2780bea99f806aec078024b0b77f24cd107e76b9a77d79405d7bb4e2f57a9b5bac7961cb2f785e46d877ab1f6677691326753c86637522687e72d77eeb72856f3f71e2660971b8490d6a6efdf56a4945796a136e7f68df1fa96899077567bfcde86745431a6534fc57
  | 5, 0 => 0x79686b407595a5b074d0a2907250d9a0704ef7d06eb4e7b06c3eb9d06a9a236069d6a4c069aa3fc068126b9066ef900063fd3120616da1906040b7305b32d9a05a7cb2605a3788d054408c705327cfa052ead050517f4bd0510e61604e1bbb804665dd8040f0e9203fe5fcd03d5030203d1c03e03c9b48c033dc793030ef44a0305960e02fb675302c2cba202aa2b0a029aafff026521b702568132024299e602341b56022e015201ec48a401e69cb301e3269e01e0cc6401c74ab301c62d2401b6429101963a33017cb3b90135fc7a012e344500f573c300c7451b00bc555a00a60f4500a41d9700a3559b0080bcb50060527e005ec42300526c150046efd5
  | 5, 1 => 0x10fc36c110de97a010bb40041078bbb5105bf9da104bb8b91041032310397f3a0f0ce7dc0f02edb50ed9adfb0eaf18df0e7eec820e572a8d0e47f2720e3a9bb30e2a28460d8cbd270d80fba70d7a72cd0d3c5e580d374be90d0194190cf640a30ccdaadf0cb9a2550cb40bac0c9635c00c9086050c4c92100c3e7f1e0c2074550c1cd4d60bc74aee0baec2310b9dbf440b898fd00b0e103c0afb03340af6a9760acaaae70a9dc7b30a8eca8a0a5c18050a03e2b509f7608009ca70d209c74d5109c4a5de09a6ea47098022c7096e45c0091a41cf08f4666b08f22c8008d35cb308bfd43908bd71840888415a0860dbee0830944307f0828e07c0faa807b95688
  | 5, 2 => 0x1adbb9d51a926d841a1f1eed1a017b3719d01c5719c0731a19a3462f19927a8f198ce1f318ca337818b5d65818b19da8188d1da4188a5eb81855f9d3183b8ba7183acace1834168c17efc4cd17c9264f17bbdd4d17b0a43a17a8e17017767c2d1770d76f1754a7a1170ace29170044ca16ea0a2a16a422411676f4b116766c5e1595518e1575c3871572a7d6156782c2150cf43414b338b414878698145851971437dad4141b675b13f9498013d99da613b0ee6e13acb27f13abbe9513a89b2a13970707134c2daa133ef8c713195c251305e86112cf63a212b497ba1267305512567ee61233ee7a121d270612129dbf11c758fc115af43c111c37ef10fff90d
  | 5, 3 => 0x264453b925e1205725e0749e25df3b82259d6aed25733f9825559aae2509ee7924d076ba24ba22a1249c8f3a249784dc23eccb7d23ad64be23a4abbc23a1d14b232e6f9023298b252305978722f10c1322c5a1b52258a5f8221003dc21ea12a821c99be5218b88292150dd9721109d8a210ae4e520969c35202d76d6202092741fe97d201fc4797c1fa34c2c1f78c0bb1f6ef15c1f6e5a1e1f55c75a1f0c16db1ee9ae3b1ed9a9071e939a471e869ab91e60d5121e213aae1e2007511dedd7871de949ee1de8f2ad1d97e5391d93d0931d6046191ccc6b171c4e1fac1c27b8bd1bbeef211bb691161b5591851b4eea041b4479a01b3d22be1b1077bd1ae12e28
  | 5, 4 => 0x36d7092a364ef5b1364724a535a42d2335991c8134e6bd6a34dd133334520fb2340a509433a3cea333531344334d6f5633046a7732eb458d32d074ed32b833233269cad3324af45531ee72c931b6eda431b21d0630e9e92530c1ffdc30345a992febddc52f43fc842eae38322e9a7e0a2e73afda2e0e31772e077de82da5b6192d9fcbae2d9e62d12d93b3292d8b7e212d2ad28a2d27164b2ce69fc12ca331682c74fa7f2c7093212c4ec3cc2b7e2c7b2b7976c32b087ae02ae16d282a81d6282a143dd429f917f229f399f7295aacc329567bcf293ef0cb28e26e2628b1990b28a4bfa8288a282b2829bb3f27c711dc278d240e2745a8442726249d269e7b97
  | 5, 5 => 0x49098638484a9003467cf4dc465151ed463bceac4573e1f845448b5b4527835d44abedc044a97bf7448b76fd4478d0744449eb7e43f874f443d192ba437754b443664e2942f0a2d842e697724274050d425c90dd41fb1dfc418702554101cad440f5e4404061416d406042ab403f6c8c400e6937400caa233fd749383f9108803e9c9b643e9383603e89b8d73e75b9c93e49a4933e11d17d3dd1a5683dca77223dc61baa3da0d34f3d4119e43d0cba1c3d053ce93d0393783cc57f3b3c9ddbcb3c2c3f1b3bf556853b12b7d23a8d7b703a61b0843a4f2a4f39ad1a0d393738e939353d60392348dc38c8cef138a8b95d3814d90837f0635737b310db372ef262
  | 5, 6 => 0x66ab237565b19348656abff26541b83b6464de7f642830f263f4c9f4633a9cde61c39014610b5fed607f87305ff247a85fa3abef5f5f5b205f25078f5e7b26aa5e19a9865e0dae615dcb29675c9101f95c62c4f65a8d9b595a46245857a948bd5743a7b9555d44f754e287715460db7953cbc90653b9c923536c7afb535933b0531d5d7552b9446e526bf4ef5252f3b25139e3cf51208fb4511d1f5f5107c7d850d2186050cf838b50c9518450ad851f4f1e11414ef4b4a24e1f67994e1d02df4de76fec4d8640f64d5918914c8d3c5e4c09428e4bb9b0eb4ac8fe0a4abfc4e04abd16a54aa362c74aa1c6924a8223184a1feaf94a1d3c2b49ac97fc49637c2f
  | 5, 7 => 0xa27bb1e09e7b97279b44aa669adc37519a8412dd99e2adf2995767a79767b34c9705085395cdd6bd956b2bc4941f83ae92e46e72916f2fb990e7d4dd906509f68ec44c2d8d50b7438d14db958b5d1a178b5b67638a0bf74c89c5853987ee91d487cd22f18756611786d6963c85ddbe4985a462df844e623f82d67b2f81d69f5c80c96b1c80729cfd80323da4802f3ac47f482aa17ec58cdb7e9cceed7d6d1c657a4368e7789c38d677e419517769132676b3c35a75a7a444759e0d09757b1f8674ef270b7449aafa73554a7c7325711071e18ecd6fb648e86f7717e56c5b5b526c4a34b86bf2120f6b6d4ae46b3d650d6b2d1cee696229f8673e9e3a66d7558c
  | 5, 8 => 0xf59d1e58f483970ff40341c9f2e9ba80e12d7e7dda7d24a9d5d34023d5b9f9add4201d1ed36b5a69cb6191a5c7f4b0dcc31b6d52bf179d35bb49b823bb36063cbb11a04bb8ea521ab5f7120cb5e01f63b564bcfcb4374d9db3ebbbb7b33cb148b1178c07aba803baa9dacb9fa9a25c54a944b3e4a8c14456a7f39f91a6087711a5decf94
  | 6, 0 => 0x29567bcf2916284328ec7d1328b4b7a6289999ce2841c7352840db3a2829bb3f2806214e2726249d26f3cf3026a5cf5725bdec5622fed1a022c5a1b521c99be521109d8a202fbf561fbd27c91fad21901f7108561e939a471c27b8bd1b0173181a79258e193ca0101898dcb51843313c18363fc817f89e001701e5411649e54b1629253e15ca19c61437dad413d00c0b13b7858e13195c25121b607f10de97a0102cef5f0fb522fd0f7afd400f0bfb1b0e7383530d7a72cd0d59fc0a0d58c5ea0cff71a10b67b78a0afc43060a26f5fd0a03e2b5078efde6072394f506a9a236051c0144042f0bce02d30cac017e3b2900e1c2420079fbaf0046efd500389354
  | 6, 1 => 0x84691f64836627857f482aa17ed19a277a61b0cb74a13adf73554a7c6e9865976bf2120f695027e566960ad5668a76c9656abff2654c4248642b4f8d642830f262b6f13061090fc25e6b9c915c98ed255bd2e1d653b9c923534fff0f52b9446e52767efc5226a46650d2186050ad6cda4d8640f64c535ece4b7d52c847eb4f9e460da0d34527835d42f19a6e41fd8d2041ecc337415bb28040b192b8408358eb3f632bdc3e49a4933b12b7d238df28253770ceb43646b8aa35cd93713523d7dd34b51922340e2861340a50943373b80b32b8332331d16acb31c1c23630b117c62f3da2442e3f67a12d8b7e212d2bf4692c8d68902c5545952bf9d69a2b7ff88c
  | 6, 2 => 0xf35389a4d5b9f9add539a467d4201d1ec9c7b516c263e11bb44642d4b233799fab12ba94a0e1d55195d2cc119515d9ac925b8bc48a0bf74c85c9775b
  | 7, 0 => 0xd4201d1e6432baff3e49a493258c480e202fbf561f16380d129dfe450d59fc0a09e2bbbd090d6eb4
  | 8, 0 => 0x1f16380d
  | _, _ => 0
def dictB : Nat → Nat → Nat
  | 0, 0 => 0xffff888800000000000000000000000000000000000000000000000000000000f8f8f8f800000000000000000000000000000000000000000000000000000000eeeeeeee000000000000000000000000000000000000000000000000000000007700770000000000000000000000000000000000000000000000000000000000ffff0000000000000000000000000000000000000000000000000000000000007070707000000000000000000000000000000000000000000000000000000000666666660000000000000000000000000000000000000000000000000000000000660066
  | 0, 1 => 0x66660000000000000000000000000000000000000000000000000000000000006060606000000000000000000000000000000000000000000000000000000000f0f0f0f000000000000000000000000000000000000000000000000000000000eeee000000000000000000000000000000000000000000000000000000000000ee88ee8800000000000000000000000000000000000000000000000000000000aaaaaaaa00000000000000000000000000000000000000000000000000000000ff00ff0000000000000000000000000000000000000000000000000000000000f0f8f0f8
  | 0, 2 => 0x55552222000000000000000000000000000000000000000000000000000000004444444400000000000000000000000000000000000000000000000000000000ff00ff8800000000000000000000000000000000000000000000000000000000ff88ff8800000000000000000000000000000000000000000000000000000000e6e6e6e6000000000000000000000000000000000000000000000000000000000000666600000000000000000000000000000000000000000000000000000000c0c0c0f00000000000000000000000000000000000000000000000000000000033ff33cc
  | 0, 3 => 0xffaaffaa00000000000000000000000000000000000000000000000000000000fafafaf000000000000000000000000000000000000000000000000000000000eeeeeecc00000000000000000000000000000000000000000000000000000000cece000000000000000000000000000000000000000000000000000000000000c2c2c2c200000000000000000000000000000000000000000000000000000000e0e0e0e000000000000000000000000000000000000000000000000000000000cc32cc320000000000000000000000000000000000000000000000000000000000ee00ee
  | 0, 4 => 0xaeaeaeae00000000000000000000000000000000000000000000000000000000fafaf8f800000000000000000000000000000000000000000000000000000000ffffaaaa000000000000000000000000000000000000000000000000000000000000eeee000000000000000000000000000000000000000000000000000000006600660000000000000000000000000000000000000000000000000000000000ffffff0000000000000000000000000000000000000000000000000000000000fffff0f000000000000000000000000000000000000000000000000000000000ccc8ccc8
  | 0, 5 => 0xf600f6000000000000000000000000000000000000000000000000000000000088ee88ee00000000000000000000000000000000000000000000000000000000ffaaff880000000000000000000000000000000000000000000000000000000006060606000000000000000000000000000000000000000000000000000000000f0e0f0e00000000000000000000000000000000000000000000000000000000f7f7000000000000000000000000000000000000000000000000000000000000ee00ee0000000000000000000000000000000000000000000000000000000000b8b8b8b8
  | 0, 6 => 0x777700000000000000000000000000000000000000000000000000000000000088888888000000000000000000000000000000000000000000000000000000000e0e0e0e00000000000000000000000000000000000000000000000000000000aaaa8888000000000000000000000000000000000000000000000000000000000000f6f600000000000000000000000000000000000000000000000000000000fefe000000000000000000000000000000000000000000000000000000000000eeeeeaea00000000000000000000000000000000000000000000000000000000e8e8e8e8
  | 0, 7 => 0x33333030000000000000000000000000000000000000000000000000000000000000aaaa00000000000000000000000000000000000000000000000000000000ccee000000000000000000000000000000000000000000000000000000000000ff00ee0000000000000000000000000000000000000000000000000000000000cccccccc000000000000000000000000000000000000000000000000000000000f0f0e0e00000000000000000000000000000000000000000000000000000000ffff000c0000000000000000000000000000000000000000000000000000000033303330
  | 0, 8 => 0xffffcccc00000000000000000000000000000000000000000000000000000000cccc080800000000000000000000000000000000000000000000000000000000000044ee00000000000000000000000000000000000000000000000000000000c0e0c0e0000000000000000000000000000000000000000000000000000000000000ccee00000000000000000000000000000000000000000000000000000000ccc0ccc800000000000000000000000000000000000000000000000000000000faf8faf80000000000000000000000000000000000000000000000000000000000cc00cc
  | 0, 9 => 0x3333444400000000000000000000000000000000000000000000000000000000ff0aff0a000000000000000000000000000000000000000000000000000000000f0c0f0c00000000000000000000000000000000000000000000000000000000cceeccee00000000000000000000000000000000000000000000000000000000f700f70000000000000000000000000000000000000000000000000000000000fff0fff000000000000000000000000000000000000000000000000000000000ccccc0c000000000000000000000000000000000000000000000000000000000a8a8a8a8
  | 0, 10 => 0xff77000000000000000000000000000000000000000000000000000000000000aaaa222200000000000000000000000000000000000000000000000000000000cccc4444000000000000000000000000000000000000000000000000000000002222222200000000000000000000000000000000000000000000000000000000f4f4f4f400000000000000000000000000000000000000000000000000000000c8c8c8c80000000000000000000000000000000000000000000000000000000000cc00ee00000000000000000000000000000000000000000000000000000000cccc444c
  | 0, 11 => 0xffffa8a800000000000000000000000000000000000000000000000000000000ffa8ffa8000000000000000000000000000000000000000000000000000000000088008800000000000000000000000000000000000000000000000000000000cccccc88000000000000000000000000000000000000000000000000000000000000ffaa00000000000000000000000000000000000000000000000000000000f0f0f0fc00000000000000000000000000000000000000000000000000000000ff7788000000000000000000000000000000000000000000000000000000000000cf00ce
  | 0, 12 => 0xafafaeae000000000000000000000000000000000000000000000000000000000a0a0a0a000000000000000000000000000000000000000000000000000000007766776600000000000000000000000000000000000000000000000000000000f3f3f3f000000000000000000000000000000000000000000000000000000000ffb8ffb80000000000000000000000000000000000000000000000000000000055555a5a00000000000000000000000000000000000000000000000000000000fff033300000000000000000000000000000000000000000000000000000000055555050
  | 0, 13 => 0x444444cc00000000000000000000000000000000000000000000000000000000ffaaff0800000000000000000000000000000000000000000000000000000000eeee4444000000000000000000000000000000000000000000000000000000000000cccc00000000000000000000000000000000000000000000000000000000cececece000000000000000000000000000000000000000000000000000000000f0f0c0c00000000000000000000000000000000000000000000000000000000eeee22220000000000000000000000000000000000000000000000000000000000ff00cc
  | 0, 14 => 0xcc44cc4400000000000000000000000000000000000000000000000000000000ffff080800000000000000000000000000000000000000000000000000000000ff08ff0800000000000000000000000000000000000000000000000000000000eee2eee200000000000000000000000000000000000000000000000000000000f0f0f0a000000000000000000000000000000000000000000000000000000000ff33ff30000000000000000000000000000000000000000000000000000000000000888800000000000000000000000000000000000000000000000000000000505050f0
  | 0, 15 => 0x5577000000000000000000000000000000000000000000000000000000000000507050700000000000000000000000000000000000000000000000000000000000ff00f000000000000000000000000000000000000000000000000000000000bb88bb8800000000000000000000000000000000000000000000000000000000ffccffcc00000000000000000000000000000000000000000000000000000000ffaaffa000000000000000000000000000000000000000000000000000000000eeeeecec000000000000000000000000000000000000000000000000000000008e8e8e8e
  | 1, 0 => 0xa4a4a4a400000000000000000000000000000000000000000000000000000000f1f1f1f000000000000000000000000000000000000000000000000000000000eeeeeeec00000000000000000000000000000000000000000000000000000000ff00770000000000000000000000000000000000000000000000000000000000f0f0707000000000000000000000000000000000000000000000000000000000f0e0f0e0000000000000000000000000000000000000000000000000000000003322332200000000000000000000000000000000000000000000000000000000aaaaaa00
  | 1, 1 => 0xfefe00000000000000000000000000000000000000000000000000000000ffff00cc0000000000000000000000000000000000000000000000000000000000ff00aa00000000000000000000000000000000000000000000000000000000eeeceeec0000000000000000000000000000000000000000000000000000000000ec00ec00000000000000000000000000000000000000000000000000000000ff00ff08000000000000000000000000000000000000000000000000000000003332333200000000000000000000000000000000000000000000000000000000ffaaf0a0
  | 1, 2 => 0xccccc8c8000000000000000000000000000000000000000000000000000000003333330000000000000000000000000000000000000000000000000000000000fafafafa00000000000000000000000000000000000000000000000000000000ff0cff0c00000000000000000000000000000000000000000000000000000000ccc0ccc000000000000000000000000000000000000000000000000000000000cceeccec000000000000000000000000000000000000000000000000000000004646464600000000000000000000000000000000000000000000000000000000aaecaaec
  | 1, 3 => 0xffee00000000000000000000000000000000000000000000000000000000fafafaf800000000000000000000000000000000000000000000000000000000ffff008800000000000000000000000000000000000000000000000000000000cccc888800000000000000000000000000000000000000000000000000000000f0faf0f80000000000000000000000000000000000000000000000000000000000ce00ce000000000000000000000000000000000000000000000000000000000000fff200000000000000000000000000000000000000000000000000000000bbbbbb88
  | 1, 4 => 0xeeeeee00000000000000000000000000000000000000000000000000000000005252525200000000000000000000000000000000000000000000000000000000ffee0000000000000000000000000000000000000000000000000000000000003333ffcc0000000000000000000000000000000000000000000000000000000055550a0a000000000000000000000000000000000000000000000000000000005544554400000000000000000000000000000000000000000000000000000000f0fcf0fc00000000000000000000000000000000000000000000000000000000aaaaa0a0
  | 1, 5 => 0xfff3000000000000000000000000000000000000000000000000000000000000ffee110000000000000000000000000000000000000000000000000000000000cccccc00000000000000000000000000000000000000000000000000000000003333fcfc00000000000000000000000000000000000000000000000000000000ccccccee000000000000000000000000000000000000000000000000000000005050707000000000000000000000000000000000000000000000000000000000ccfeccfe000000000000000000000000000000000000000000000000000000000000fcfe
  | 1, 6 => 0x1100ffee00000000000000000000000000000000000000000000000000000000ffff444400000000000000000000000000000000000000000000000000000000aaaaeeee00000000000000000000000000000000000000000000000000000000ff22ff22000000000000000000000000000000000000000000000000000000000000fffe000000000000000000000000000000000000000000000000000000000000fcfc00000000000000000000000000000000000000000000000000000000555055500000000000000000000000000000000000000000000000000000000000fa00fa
  | 1, 7 => 0xcece0000000000000000000000000000000000000000000000000000000033333c3c00000000000000000000000000000000000000000000000000000000f8f8f8f000000000000000000000000000000000000000000000000000000000aa00aa8800000000000000000000000000000000000000000000000000000000333333300000000000000000000000000000000000000000000000000000000000000c0c0000000000000000000000000000000000000000000000000000000033333322000000000000000000000000000000000000000000000000000000000f0f0f0a
  | 1, 8 => 0x5555555400000000000000000000000000000000000000000000000000000000e2e2e2e200000000000000000000000000000000000000000000000000000000fffa0000000000000000000000000000000000000000000000000000000000002626262600000000000000000000000000000000000000000000000000000000aa66aa66000000000000000000000000000000000000000000000000000000000c0c0c0c00000000000000000000000000000000000000000000000000000000cccc88aa00000000000000000000000000000000000000000000000000000000f0f0e0e0
  | 1, 9 => 0x550055aa00000000000000000000000000000000000000000000000000000000cccceeee000000000000000000000000000000000000000000000000000000000c0c0e0e00000000000000000000000000000000000000000000000000000000ee66ee6600000000000000000000000000000000000000000000000000000000ff66ff6600000000000000000000000000000000000000000000000000000000aaeeaaee00000000000000000000000000000000000000000000000000000000aa88aa8800000000000000000000000000000000000000000000000000000000cccf0000
  | 1, 10 => 0x54545454000000000000000000000000000000000000000000000000000000003232323200000000000000000000000000000000000000000000000000000000aa22aa22000000000000000000000000000000000000000000000000000000003366336600000000000000000000000000000000000000000000000000000000ffffaaa000000000000000000000000000000000000000000000000000000000444c444c00000000000000000000000000000000000000000000000000000000aaaaa8a800000000000000000000000000000000000000000000000000000000ffffeeee
  | 1, 11 => 0xf0f0fafa00000000000000000000000000000000000000000000000000000000555566660000000000000000000000000000000000000000000000000000000033332222000000000000000000000000000000000000000000000000000000003f3c3f3c00000000000000000000000000000000000000000000000000000000cc88cc8800000000000000000000000000000000000000000000000000000000cccc222200000000000000000000000000000000000000000000000000000000f0f0f0f400000000000000000000000000000000000000000000000000000000bbb0bbb0
  | 1, 12 => 0xaaaaaa22000000000000000000000000000000000000000000000000000000000000fffa00000000000000000000000000000000000000000000000000000000ff44ff44000000000000000000000000000000000000000000000000000000000044004400000000000000000000000000000000000000000000000000000000cc66cc6600000000000000000000000000000000000000000000000000000000ff22ff2000000000000000000000000000000000000000000000000000000000aaa0aaa0000000000000000000000000000000000000000000000000000000007070f8f8
  | 1, 13 => 0xffff0a0a000000000000000000000000000000000000000000000000000000005522552200000000000000000000000000000000000000000000000000000000aaaaaaa800000000000000000000000000000000000000000000000000000000bbbbbbaa000000000000000000000000000000000000000000000000000000000e0e0e0a0000000000000000000000000000000000000000000000000000000000cc00ce00000000000000000000000000000000000000000000000000000000afafafaa00000000000000000000000000000000000000000000000000000000ff00fa00
  | 1, 14 => 0xf0a0f0a0000000000000000000000000000000000000000000000000000000000ff00ee00000000000000000000000000000000000000000000000000000000ffaa3322000000000000000000000000000000000000000000000000000000004444666600000000000000000000000000000000000000000000000000000000575700000000000000000000000000000000000000000000000000000000000044ee44ee00000000000000000000000000000000000000000000000000000000fcfcfcfc00000000000000000000000000000000000000000000000000000000c0c0c0cc
  | 1, 15 => 0xaa00aa00000000000000000000000000000000000000000000000000000000ffff888c000000000000000000000000000000000000000000000000000000000000fff000000000000000000000000000000000000000000000000000000000ee22ee2200000000000000000000000000000000000000000000000000000000ce00ce0000000000000000000000000000000000000000000000000000000000ccccccc8000000000000000000000000000000000000000000000000000000000f0f0f0000000000000000000000000000000000000000000000000000000000ffff3330
  | 2, 0 => 0x4444444c000000000000000000000000000000000000000000000000000000000000222200000000000000000000000000000000000000000000000000000000aaaaaaa000000000000000000000000000000000000000000000000000000000fffffafa00000000000000000000000000000000000000000000000000000000f2f2f2f2000000000000000000000000000000000000000000000000000000003333330200000000000000000000000000000000000000000000000000000000fbfbfbf000000000000000000000000000000000000000000000000000000000aa44aa44
  | 2, 1 => 0xff00ffee00000000000000000000000000000000000000000000000000000000ffff0c0c000000000000000000000000000000000000000000000000000000000f0f0a0a00000000000000000000000000000000000000000000000000000000ff0eff0e00000000000000000000000000000000000000000000000000000000000a000a00000000000000000000000000000000000000000000000000000000eeeeeeaa00000000000000000000000000000000000000000000000000000000fcf8fcf80000000000000000000000000000000000000000000000000000000033333332
  | 2, 2 => 0x22002200000000000000000000000000000000000000000000000000000000fefefefe00000000000000000000000000000000000000000000000000000000000000cc0000000000000000000000000000000000000000000000000000000004040404000000000000000000000000000000000000000000000000000000000000ffcc00000000000000000000000000000000000000000000000000000000f0f0f03000000000000000000000000000000000000000000000000000000000fffafffa000000000000000000000000000000000000000000000000000000000f0f0808
  | 2, 3 => 0xdddd888800000000000000000000000000000000000000000000000000000000f0f0f0fa00000000000000000000000000000000000000000000000000000000000000aa000000000000000000000000000000000000000000000000000000004e4e4e4e00000000000000000000000000000000000000000000000000000000ffff332200000000000000000000000000000000000000000000000000000000ffccff4400000000000000000000000000000000000000000000000000000000aaa2aaa20000000000000000000000000000000000000000000000000000000002020202
  | 2, 4 => 0xff55cc44000000000000000000000000000000000000000000000000000000003300332200000000000000000000000000000000000000000000000000000000ffff00aa00000000000000000000000000000000000000000000000000000000cccc040400000000000000000000000000000000000000000000000000000000f0f0fcfc00000000000000000000000000000000000000000000000000000000555f000000000000000000000000000000000000000000000000000000000000fffefffe00000000000000000000000000000000000000000000000000000000ffffffaa
  | 2, 5 => 0xaaaa008800000000000000000000000000000000000000000000000000000000fffffff000000000000000000000000000000000000000000000000000000000ffff222200000000000000000000000000000000000000000000000000000000ff00fffc00000000000000000000000000000000000000000000000000000000ffffcece00000000000000000000000000000000000000000000000000000000dddddd0000000000000000000000000000000000000000000000000000000000080808080000000000000000000000000000000000000000000000000000000000000404
  | 2, 6 => 0xcc4400000000000000000000000000000000000000000000000000000000000c000c00000000000000000000000000000000000000000000000000000000ffccffc0000000000000000000000000000000000000000000000000000000000000545400000000000000000000000000000000000000000000000000000000fffcfffc00000000000000000000000000000000000000000000000000000000ff04ff040000000000000000000000000000000000000000000000000000000000004444000000000000000000000000000000000000000000000000000000000000ff44
  | 2, 7 => 0xff00fc000000000000000000000000000000000000000000000000000000000f080f0800000000000000000000000000000000000000000000000000000000003300300000000000000000000000000000000000000000000000000000000000fe00fe0000000000000000000000000000000000000000000000000000000000aa00220000000000000000000000000000000000000000000000000000000088888800000000000000000000000000000000000000000000000000000000000a0a0a0000000000000000000000000000000000000000000000000000000000ffffff44
  | 2, 8 => 0xaaaaaeae00000000000000000000000000000000000000000000000000000000ddddddcc0000000000000000000000000000000000000000000000000000000000000e0e00000000000000000000000000000000000000000000000000000000ffaa550000000000000000000000000000000000000000000000000000000000777770700000000000000000000000000000000000000000000000000000000050545054000000000000000000000000000000000000000000000000000000000a0acece00000000000000000000000000000000000000000000000000000000ffffffcc
  | 2, 9 => 0x333332320000000000000000000000000000000000000000000000000000000088888a8a00000000000000000000000000000000000000000000000000000000ff00ffcc00000000000000000000000000000000000000000000000000000000f3f3a2a200000000000000000000000000000000000000000000000000000000c4c4c4c400000000000000000000000000000000000000000000000000000000ee44ee4400000000000000000000000000000000000000000000000000000000fac8fac800000000000000000000000000000000000000000000000000000000a2a2a2a2
  | 2, 10 => 0xff000c000000000000000000000000000000000000000000000000000000000f0f000a00000000000000000000000000000000000000000000000000000000ffffaeae0000000000000000000000000000000000000000000000000000000000000a0a00000000000000000000000000000000000000000000000000000000cc00ee0000000000000000000000000000000000000000000000000000000000ff55f05000000000000000000000000000000000000000000000000000000000f0f2f0f20000000000000000000000000000000000000000000000000000000000005550
  | 2, 11 => 0xf0f020200000000000000000000000000000000000000000000000000000000aaaa0202000000000000000000000000000000000000000000000000000000000000002200000000000000000000000000000000000000000000000000000000c0c8c0c800000000000000000000000000000000000000000000000000000000ffaaff2200000000000000000000000000000000000000000000000000000000f0f0f8f800000000000000000000000000000000000000000000000000000000ffeeffee00000000000000000000000000000000000000000000000000000000f0faf0fa
  | 2, 12 => 0xfff2fff20000000000000000000000000000000000000000000000000000000022ee22ee00000000000000000000000000000000000000000000000000000000ff00fffa000000000000000000000000000000000000000000000000000000004444440000000000000000000000000000000000000000000000000000000000ff00ffaa00000000000000000000000000000000000000000000000000000000ff54ff540000000000000000000000000000000000000000000000000000000011111010000000000000000000000000000000000000000000000000000000000000aeae
  | 2, 13 => 0xffffaa880000000000000000000000000000000000000000000000000000000022222200000000000000000000000000000000000000000000000000000000000000a8a8000000000000000000000000000000000000000000000000000000000303020200000000000000000000000000000000000000000000000000000000fffffffa00000000000000000000000000000000000000000000000000000000555555500000000000000000000000000000000000000000000000000000000000000f0c00000000000000000000000000000000000000000000000000000000bbbbb0b0
  | 2, 14 => 0xffffff0a00000000000000000000000000000000000000000000000000000000ccccfefe00000000000000000000000000000000000000000000000000000000222a222a00000000000000000000000000000000000000000000000000000000ccceccce00000000000000000000000000000000000000000000000000000000ffffff0c0000000000000000000000000000000000000000000000000000000044444c4c000000000000000000000000000000000000000000000000000000005555545400000000000000000000000000000000000000000000000000000000c0c0e0e0
  | 2, 15 => 0xaaffaafa00000000000000000000000000000000000000000000000000000000bbbb888800000000000000000000000000000000000000000000000000000000fffff8f800000000000000000000000000000000000000000000000000000000aafeaafe00000000000000000000000000000000000000000000000000000000ccffccfc00000000000000000000000000000000000000000000000000000000ff55ff5000000000000000000000000000000000000000000000000000000000f3f3c0c0000000000000000000000000000000000000000000000000000000000c0c0c00
  | 3, 0 => 0xa0a0a0aa000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000fff0ccc000000000000000000000000000000000000000000000000000000000555544440000000000000000000000000000000000000000000000000000000000c800c800000000000000000000000000000000000000000000000000000000cc00cc0c00000000000000000000000000000000000000000000000000000000aaa8aaa8000000000000000000000000000000000000000000000000000000000c0e0c0e
  | 3, 1 => 0xccccccc0000000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000088888c8c0000000000000000000000000000000000000000000000000000000077227722000000000000000000000000000000000000000000000000000000007474747400000000000000000000000000000000000000000000000000000000eee0eee0000000000000000000000000000000000000000000000000000000000000008800000000000000000000000000000000000000000000000000000000cccccc44
  | 3, 2 => 0xfffffcfc000000000000000000000000000000000000000000000000000000005555550000000000000000000000000000000000000000000000000000000000fffffffc0000000000000000000000000000000000000000000000000000000000000f0a
  | _, _ => 0
def stateB : Nat → Nat → Nat → Nat
  | 3, 0, 0 => 0x4870360a4038243401401834320a40383402184048342e164018541a01401810020e4018501a134048041c1240184414104038340a004048041e0e406830160a40382410054038180a0440180802004
  | 3, 0, 1 => 0x483418014128244c0540483402244048a81a014018240c0140683002234018a4040140182450274038244c0541287c1a1d40680446244018180223411084400a40187c3c1d4018500c014038340a0b4
  | 3, 0, 2 => 0x48c81a014068a402124018501a314038501a05404830340140486802244068043024401824600140382404014038180a294018bc1a014018345c014018b44c054048045812403030520a401824022b4
  | 3, 0, 3 => 0x680430124048dc040140481458124060a434364048340212403824022c4038500a3540480802244038500c054018a4343440483402334
  | 4, 0, 0 => 0x25834760a1ba81c2a0d1d8294444a1d92414a03048340a485238241a460528241a3b0511544a2d068ec14a091d91014435018241a4205280c823b0510140e09068287ea07048340a0a5018240c051f28347a3b050614063c1d82874a390483414385
  | 4, 0, 1 => 0x1824b43b052964120d1d8294060d1d828b0a09068286e0150a15c1a3b05281c120d1d95940e090695414a070a0347654501824a65205280c121e1d82941a3b0514448a0304834a00a5238241a0a27a8240a1a1b0dd4064e1d8289aa0d260f414405
  | 4, 0, 2 => 0x1824766733280c120d02995406641d82880a09028d86e3550198c1a3b05280c120d1b00540609068ecc4a2130824760a511128760a30280c125a028294be5e068ec14a0919034a40a50000c120d00a00c960d028d94060906804baa0906970145b5
  | 4, 0, 3 => 0x18342c5400280c12061d80540609069d014a09398ec145b51280c280d02a9c81a0a1f9b14060903014e2a0304828e06f50187c3c3b05280cdc0d1d8294120d36828d8a03049ac146a5038500c3b05280c12690d0294120d028d81ea030682870685
  | 4, 0, 4 => 0x187c7680382824760a3f9f94063b05134faa250489876345018a4760a1aa80c121d051c1406090301402a03069f014405019ec120d00a80c1a051b0114067a069e414a0304814f0365038241a770529d8ea0d1d82940609130282ca09068146c125
  | 4, 0, 5 => 0x1835180a45a80d140d1d8294120d0280448a0304834148952f8241a0524280c94881d82947209068282ca0704834920a5018241a010c280c123b0521d40609430ec14a09068ec02245018241a8505280d08831d829406094102902a7515034760a5
  | 4, 0, 6 => 0x18241a9805280c1295068054440906a5c14a09068307601501834149634280c280d050fd406094a81490a030f0ec1440501a501a9305280c120d49029406090682922a03068ed200a5068a4760a47a80c280d1d8294065e030ec14a8e068ec148d5
  | 4, 0, 7 => 0x18240c05242a74120d050594120d4e0289ea0304a6c760a5038240c0505281c12061d829406090684c6ca03168340a0a501824760a1d280c1a3b0526940e0906a5c14a0704834980a504834760a4ca80c5a0d1d82941a0c148286ca090681418015
  | 4, 0, 8 => 0x4834760a54280c1aa705101406091d8294ca7604834d60a552834760a0c28241a3b05291406091d89d0ea220692414405018240c0d00a894120d1da8d4060d0088c2ca03068ed4418501a51423b05280cf4951da814120d028d93ea0304a78760a5
  | 4, 0, 9 => 0x57825423b052ab8120d1d829412081d8286ea070681452365030ec143702280c1206568294120d052b0d8a03048186c01504835560a362a94121a1d82940e091d82954a00018240c014018240c6b0528241a05240914060d5482880a0304828020e5
  | 4, 0, 10 => 0x18180a3602280d680d260294060906a44a8a290d0ec1424503834760a0c280c2a0d028294120d1d82966aa5048ec14355038501a0a0b28241a36008914120d1d82946a091d828d4b25000241a011220241a050612140615068ec14a03068ed62b05
  | 4, 0, 11 => 0x4834760a5ba830521a1d8294060906954aca0704814340a504834183600a80d2a3b052694ec14068ec14ab60483476b5503824343b05280c2a0d2a829400090683002803068a42c545018241a010b281c06090301540e0d0282830a03048200a365
  | 4, 0, 12 => 0x48146c3701280c12c0028d940609029206aa0d1d82934bf50182476481aa8241a3b0513d40609068297ca0304af4760a50187c1a3b5e28241a9c050914282a068ec14a291d8286a2451c8241a930528241a0a5d9b14444a1d82974a030482972b85
  | 4, 0, 13 => 0x18b4760a552835900a1c101406291d82804a030483476c75018258c0a1aa824760a1d09158a090682912a070483414165018340a0b1b280c120d0b31140609068ed86a030486c14c250483476c105280d680d050e14060900838a8a090606814545
  | 4, 0, 14 => 0x18ec143a0c2894120d1db454120d1d82848ad0018241a0150198c1a0a0b280c120d460294060d1da019ea030a03476ca504b3814cd36280c120d4b8294060906b3014a03658241a0150183476ca64a80c121a4e029406090684c2ca090682802125
  | 4, 0, 15 => 0x38241a162a281c283b05009406094a9202ca0304b64760a501825b00a61280c120d008494060906b5daca09068ed6a3e5018340a291b280d680d1db254060906b31aaa030f835180a5018241a0136280c120d053515a60906829a4a070a0340a3b5
  | 4, 1, 0 => 0x1834760a17280dc40d1d8294061f068edc2a03048ec14e05018241a053e280c12df1da814060d4602880a030483476de5018240a0200a8241a012a0494120d0537448a25068292c4050182414dc1c280c123b010054060d2636c14a09068edb40a5
  | 4, 1, 1 => 0x3824760a01280dd00d4b8294060906b9c2ca03048340ad15038501a051b280c1a0a1c101400070a0340a8090688014e6552825043b052824143f611b1406e50483402a0906a70143f5018241a0172280c120d6db294060906b8c14a030483402665
  | 4, 1, 2 => 0x1824603b0528ec143702009406091d829d6a03048d8040150187d2a3b70a80c1a230b15141a3b0510086a000182404014128241a1d40280c1a3b053a944a0906a00dea0314868146c50182476e933281c12050500943e0d1da00d8a030486814dd5
  | 4, 1, 3 => 0x1824d61b05280c120d0b1515de096f8ec14a03068ed92ee5018241a3b76a80c1a056490141a05060a46ca0304835d8545018241a311b280c1a7c0539141a3b0506048a07048340a365018241a690b280c120d02a4540609028c014a0d028a46c245
  | 4, 1, 4 => 0x77824760a7cabe0120d1d8294063b053dd60a031d82874f65113d41a3b052894123b1a2a944a09068ec2ea030483468f4501834520a00a894e40d1d8294120d02921e6a0304814020e5018241a4c64a80c1a0a79101406091d8041ca0304bc5e00a5
  | 4, 1, 5 => 0x38241a0a00a80c1a3b803fd40e09050082ca07068146c1857f0241a3b052834760a3ebf54120d0280424a7b04830340a5048342c541228241a3b008494067b06bf014a07048340a165018246c0107280006090083901a1c7d8ec14a0304835f40a5
  | 4, 1, 6 => 0x48340a0a0928241a3b05049406090682802a2282128760a501826060d00a8241a051b0914067b06b282ca030483414d25048346c01092800120d00849006090682a04a21018241a015048ec140212280c123b052e140609808ec14a3b050d430245
  | 4, 1, 7 => 0x18241a0a84280c120d0280540609068ec02a0304834150750483414160928241a0a0089141a051b06048a0304834025450182404162a28241a010b04940609068060ca250483477055
  | 5, 0, 0 => 0x8700c120d05059a0803048ec150d6018241a0a4b15188e0906814142460380c123b050098000d060a4760a50001c120d0282940609068282cb2601c30123b050d580609068ed630b6018ec1436020098060906c28760a6018b41a3b050d18060984834760a601824760a2a0d580e09068ec14366
  | 5, 0, 1 => 0x2380c123b052a98067b0f83476a26018252a6b1d8298060906858a91466800c12c01d82984209068ec1513601826243b05101a2209068ec14e66018241a3b054418070f04834760a6018240a0a2a0d580003048340a48501824b40d1d82980e090681414366108241a3b5a82988e250483414166
  | 5, 0, 2 => 0x1824760a86b0980e7b04834760a6018240a3b050e98000304968760a511084123b053e5806098b034a40a6470241a3b0545580614068edb60a6018501a3b051018067b04834f80a60187c1a3b053f58060978b7c760a6018241ace054198060906858a8c2601834760a649018000304878760a5
  | 5, 0, 3 => 0x1c68120d1d82980003048346c015018340a0a0c45d8420339034760a6018241a3b054658068804834760a6018241a6b050d980609068282c546018241a3b6495180609030ec151862380c120d050e18061504834760a6000000609068050ae09068ec1440601824760a334518060d1d82831176
  | 5, 0, 4 => 0x19ec1a3b650298060d148ec14356018241aad050d98064a048ec920a604834760a501b18120d358ec14bf6018241b1f1d829806098f034760a6018241a3b4047580609028298466600034760a1b81140609068ec151c62380c1a3b05061a360304834760a61080c120d028d98120d1d8286eff6
  | 5, 0, 5 => 0x1824a63b0545180609068146cff6018241a0a401bd8060906814143469280c3e0d1d82984a09068ec146a604834760a243cd88e0304868760a6018241a3b920298420304c8c760a6250241a3b054898060906a4c14c26018241a3b050d18072104834760a62380c1a0505061a400325034760a6
  | 5, 0, 6 => 0x18241ace051518072704834760a60185012061d82980609068ec143f601824a63b0530984403068ec14e464700c120d0282980003148ec14355018241a3b054998060d1d82880fd61280c123b0500980003068146c0452380c12050d02980e094a834760a60183476ca050618067b04834d60a6
  | 5, 0, 7 => 0x2380c120d05259800030a034760a50000c12951d921400030483414895018501a3b0517588e09068ed380a601cb0120d1d829a560304834760a6018241a1d052018060906ca8760a6018241a162a4198064b068ec1529601834760a0c0918064a048ec14606018241a3b054a180e03048340a366
  | 5, 0, 8 => 0x182476276119980609068ec15306238241a3b053f580609068edb60a601824c83b0525980e09068ec6c54601825423b05309806090681476d7604b7c1a3b051b180609068ec69066018241a3b0085980609068ec152f604835903b050e1a5c2504834760a69680c120d0505991c0325034760a6
  | 5, 0, 9 => 0x1825e20d028598073504834760a60000c5a0d1d8295a003068a4760a601834760a024a58060906815b60a6018241a3b054d180609068287e406018241a050510180733048ec14c2601cc8120d1d8298067b5a034760a6018241a3b050e980609068ecad316018241a0a0b45d8ae09068ec14366
  | 5, 0, 10 => 0x18241a3b054e980609068ec15396048347656360f9a700304834760a604834aa0a360f984a03068ec14f6623894120d1d8d18420304a54766060001c12061d8294067b0a034760a6018241a550510180003048ec143a50000c1a3b0526940609068ec153760182476270519984403068ec15366
  | 5, 0, 11 => 0x4834760a1bb0980609069a4146c68200c120d1d981a8003048355a0a6019281a050510184a03048340a36601834523b051b1806090681414dd6018241a3b054fd84403048ec14b86018501a3b054f98064a068edb60a6018241a3b054f580e09030ec1436601c581a3b054f180609068ec153b6
  | 5, 0, 12 => 0x578241a3b054d9806094a8ec143f6018252a0d0522580609068ee90166018241a3ba382980609069f014166a0094120d1d82980609068ec920a6018241b461d82980609068ec1545601d10120d1d82980609068ec15436018241a0a6ecc58060d028a4146c6018241a3b0550980609068ec15416
  | 5, 0, 13 => 0x19283e951d8298060906a4c14546018241a3b05539806091d8289a666115341a3b051b180609069dc1440601826980d1d8298060906d2c15296018241a051b3098424a048ec146c6018241a3b0517580609358ec14356038241a3b050598060906d28760a6110241aad051b180609a4834760a6
  | 5, 0, 14 => 0x1928120d4602980615068ec14366018241a490510180609068ed2e0a6018241a4c1d82980609a8834760a60000c2a0d1d82940609068286c3f6018241a05050d980609068ec155060192812061d82980609068ec14606018241a05051a980609068ec154f6018241a050517584a030483476b56
  | 5, 0, 15 => 0x7c00c120d1d8298060906a30760a601834523b0519983e09068ec14246018240c051d829800030483402165778241a3b0555189409068ec14246018241a3b2b0d988e09068ec15316018241a55050d9806f1068ec14046018347753050f98075204834760a69680c120d0b1518004704835380a5
  | 5, 1, 0 => 0xf8241a0c1d8298067b04834aa0a601984120d1d82980609068ec15566048340a3b050918940906830760a6aa80c120d1d82988e03048342c546019292a3b0510180609068edaa5d6018241a3b5a8298061404834141661280c123b052e1806091d82804546019ec120d02829806090682992166
  | 5, 1, 1 => 0x18340a291d8d98064a068ec14186019ec3e0d028298120d02830760a61c8241a3b054d98060906a701416601d64120d1da8980609068ec4e3661080c13581d82980733048ec144d66287c120d1d82996c09068282c6c662928120d1d8298120d1d82849316018240c3b0510180609068ec15576
  | 5, 1, 2 => 0x18241a3b0557da8003048340a0a601834983b05101800070483414165018241a3b05579800030483690165019e8120d1d8298120d0282880246018241a3b0557588e0304835260a6018241a3bae0298120d1d828802460187c1a3b050618075b04834760a601826b43b051b188e03048340a346
  | 5, 1, 3 => 0x18240c3b051758067b06814144060000c120d4b82940609030340a0a6018241a4c05175a5c03068ec144061080c1a3b0501180609068146c546018240c0d1d8298064a0f83476e16019ec3e0d6d82984209068287e6c6018241a3b05581807110483414896038241a0a1b05980609068ec6c546
  | 5, 1, 4 => 0x4834760a1b0918076504834760a6000241a3b0509140675068ec14666018241a3b7602980609068ec15646018241416611998000304835180a501d8c1a3b053fd84a09068ec15546018340a0a0c1018076204834760a6018241a3b055858060d1d8288113604834760a125158060d1d82830406
  | 5, 1, 5 => 0x18241a3b055b980609068ec156d6018241a6b051b188e09068ec15136018241a3b05059806092d0ec146c6018241a3b055b18060d1d82870406048340a0a1b091ad60304834760a6018241a3b055a980609068ec15696018241a3bb402980609068142cc2601d9c120d1d82980609068ec15666
  | 5, 1, 6 => 0x18252a0d4b8298060906dd0760a6b980c120d1d8298420304834157261100c123b088298120d0283014366018241a3b055c580009068ed6a3e50000c1a05148d94120d060ec14366018259c3bb8029ade7b04834760a61080c13031d829806f1068ec153c6018241a051db2584409068ec150d6
  | 5, 1, 7 => 0x18241afc1d82980609bc834760a6018241a3b055e1aee0304834760a61100c120d052e58060906dd8760a60000c1a4c0510140609068282c406018241a0a1fae980609068ed945d6018241a05052e9806094a818760a6038241a3b051998440d1d828806c62380c120d028d980609068ec15756
  | 5, 1, 8 => 0x6814760a0c09180609068ec15546048359c0a360f98077a04834760a6038241a051d8d98060d028a47616601825063b050f98064a068282c406018241a3b138598060906815f80a6110941a3b0523580609068282cdd6018241a051b0918067b068ec141860000c3e0d1db85406090f0ec14806
  | 5, 1, 9 => 0x18241a520545180609068286c166018241a050b15180007048ec1402501834760a288f9800030682870405018241a0a0b17584a09068ec14806018241a3b0b15180609068eef80a6018262c0d1d921812050d0ec14246018241ad50b1018061f048342c54601928120d0b1518060906dec760a6
  | 5, 1, 10 => 0x19d41a3b054a5a80030483414966018241a0a0095180609068eefe0a6018241a3bbf02984ab604834760a604834760a0b09180614068ec14e46238241a0a0b4c5a5c09068ec14fd604814181a1d829afa0704834760a604834760a364199a00304834760a603824760a1b009806090692414ba6
  | 5, 1, 11 => 0x18241a3bc1029807110483476e16018241a3b0520180609068d82c546018241a3b0560580003048342c54588b14120d1d829a800304834141660187c12821d82980609068ec15806018240a3b050099a0030483414dd600034760a0c09140007048340a365048c81a051d8298120d060ec14166
  | 5, 1, 12 => 0x18240a0a1b009afa0304834760a601824760a1b009806094a8ec150d6ac8241a3b050919a009068ec1424601e14120d1d82980609068ef09066018241a3b0560d806090681476366018241b4b051518060906b282c40601824760a6142d80e09068ec143e6019ec1a0a0b10180609068ec15056
  | 5, 1, 13 => 0x18241a3b053498422525024760a6018252aa11d8298120d1d828cc2460000c120d028d940609068146c5d6018241a3b056258067b04a08760a6018241a3bc40298064a04834400a6018241a3b0561d800f804834760a5018241a3bc215180609068ec15866018241a3b5acc580609068282cba6
  | 5, 1, 14 => 0x1100c121e1d8298002210928760a50000c123b052e140609068ec14bb6018241a3b05639806090681476166018241a3b052e18120d028ec6c2462380c120d02e1180609068ec158d601826063b05461806091d8d804546018241b4b0546180609068ec158c6018241a3b0562d8060906e28760a6
  | 5, 1, 15 => 0x18241a050552180609068146c166000241a051b09140609068ec159061100c13121d829806b4068ec14ff61080c280d1d8298060d028a414546018241a05050058060d148ec14546018241a3b05005800030483414d25018241a3bc7829806091d828041661100c125a1d829806091d8286a666
  | 5, 2, 0 => 0x4834760a7e8f98120d1da70143e601826060d0282984a09068ec15066038241a3b051519a003048340a366018252a3b051218071104834400a601b94120d0b15180609068286c01601824760a401c18060906858a86660000c120d0500540609068ec02546048340a3b0b09180609050d804166
  | 5, 2, 1 => 0xc120d0280540609068ec6c0160000c120d1d805406090681476016018241a010b1518060913034760a6018241a050515180609068ec14546018241a0aa4059806090681415066018241a0a008598067b0f83414816018240a3b1b009800030483402545c880c120d1d82980609030ec14486
  | 5, 2, 2 => 0x609068146c016
  | 6, 0, 0 => 0x18241a3b05150d8e004700c120d1d8298061f04834760a1b380c9409068ec143670000c120d1d82868c21018241a3b05281c0003048ec14c23330000609068282c546004940609068ec14c009000c120d1d82988e0304834760a0b380c12f1068ec143e7018241a051d82880e0304834760a36455c000704834760a1b30880609068ec15927
  | 6, 0, 1 => 0x11c0609068282cc0304834760a7f8f9c0003048340a0a20300cf60906814760a7018241a3b050d880e00018241a3b6d82980609068ec14402eb80000030a034760a50000c120d1d95414d2e01928120d1d829c00032507c1a3b0530000609068ec15316018241a051d8286ce00018241a3b050fd80003048340a3b05300c120d1d828cd0b7
  | 6, 0, 2 => 0xc120d1d828c0c00018241a3b050d9806094a834760a20380c120d1d8286c5d70000c120d1d828d4c00018241a3b051758000304834764905300c12f1068ec14487018252a0d028ec14e0304834760a2a199c064a04834760a1c3b408e0304834760a70000c940d1d82880c00018241a3b053758061f04a541a3b05380c120d028ec14187
  | 6, 0, 3 => 0x241a051d82848c030f8241a3b05059c0609068ec14c21f391c0609068ec15847c980c12f1068ec14e22018241a3b053e5c064a04834760a0b38000609068ed6a0a60000c120d1d82830c00019ec120d028298074d04834760a36380cf609068ec14367004b80609068ec14c2201825e20d1d829c000304834983b05300006090681414366
  | 6, 0, 4 => 0xcf60d1d82880c21018241a3b053fdc0003048181a3b05300c120d1d828cd1870000c120d1d8d8a8c0304834760a0b101c4a0304bc41a3b053802800304834760a6019ec120d1d82a26e0304834760a0b4c5c000906814183b05300c1358068ec14ff7018241a051d8282ce038887c120d1d829c00033d87c1a3b05300e224a04834760a7
  | 6, 0, 5 => 0x1280c120d1d829fee00018241a0a0b1018000304834760a5d3340060906814760a701928120d1d828d8e03250241a3b49829c07590f8241a3b05380c120d1d82a90c27018241a3b050d82ce00018241a3b050598000004834760a122e4c420304834760a7018241a6b1d828cce00018241a3b051f5806094a834760a6b380c1206068ec14367
  | 6, 0, 6 => 0xc120d1d82a1ac030483476b5051b1c067b04834760a3638840609068ec145472380c12f1068ec14e006800c120d1d8298440304834760a8ab8000609068286c166018241a051d828cce25018241a3b05235c00030483476162a300c3e09068ec14e470000c120d1d82aa8c0304bc41a3b05151c0609068ec144036380c120d1d828d9317
  | 6, 0, 7 => 0x884209068ec14c0304834760a0b199c0000018241a051b280c120d1d828a9067018241a3b2a8287ce00018252a3b0519980003048ec14360130940609068ec145470000c120d028ec6cc0304c0c1a3b05151c0003728241a3b05300c12f1068ec151870000c120d1d82900c0304834760a1b199c000304834760ac230000003048342c545
  | 6, 0, 8 => 0x304834760a0b151c0003048340a0a2a300c120d1d8286c5470000c120d1d828a8c00018241a3b054198060906814760a2a3800060981834760a601928120d1d82a16e0304834760a7f975c000304834760aa43084060906814760a71280c120d1da7014e210187c120d1d829c0003048340a3b0b300dca09068ec14167
  | 7, 0, 0 => 0x18241a3b0515180609068ec14666018241a3b050598067b04834760a6018241a3b050d98000304834760a5018241a3b051018060906814760a60187c120d1d8298064a04834760a6
  | 8, 0, 0 => 0x304834760a5
  | _, _, _ => 0
def stateW : Nat → Nat
  | 3 => 40
  | 4 => 49
  | 5 => 58
  | 6 => 67
  | 7 => 58
  | 8 => 49
  | _ => 0
def wireAt (i : Nat) : Nat := fld (dictB (i / 128) (i / 8 % 16)) 256 (i % 8)
def dictP1B : Nat → Nat → Nat
  | 0, 0 => 0xffc00066187800e3bbfe07e00ffc00066187800e3bbe0701df
  | 0, 1 => 0x38000000070330c3c0070000000e00000003fc0fc019861e0
  | 0, 2 => 0xffc00781c7743c0fc01e07e00038eef800777c0003c1ffe3d0
  | 0, 3 => 0xf03f07e6187800e3ba00700000000e7800070030385e0701df
  | 0, 4 => 0x38e0fe618783ff001e001ddf000e007fff803ffc3c0001dc0
  | 0, 5 => 0xc03e0001c077fc0fc00071c1f338f0fffe0000003801986020
  | 0, 6 => 0xffc00000000000e383e000000003effe7c00000e039e0001c0
  | 0, 7 => 0xfc7010000003c0e0001e01c00038ee819e707fff0021f86220
  | 0, 8 => 0xffcee801c0000003bbe0001c0000eef800770330c3c00701d0
  | 0, 9 => 0xfc4ee8781f83cce3c20071ddff03f007e1ff800e0380000000
  | 0, 10 => 0xffc000000003c0e3ba000000fcfbef800007000e03be071dd0
  | 0, 11 => 0xffc000781f800000000071c00003f07e6187c3ff00000781df
  | 0, 12 => 0x33ce0f800003fceffbff8e3e0fc3f107ff87bff0c441ffe1e0
  | 0, 13 => 0x38ee8781f8000e3ba0001dd0038eef99e70400e001e1f81d0
  | 0, 14 => 0x38ee87fe0003c0fc00001dcfcc30007e3f8800000019861e0
  | 0, 15 => 0xffc00066187803f03c1e06200f3bfe8781f8000e3ba0071c1f
  | 1, 0 => 0x38e087e38f800e3ba1e07e00cc30f06018703c0c41e000000
  | 1, 1 => 0x3effffe07403f001e071dd00380e8781f803f0c45fe06000
  | 1, 2 => 0x380e07e3880330c3dfe77e10000ee001c77400e3bbe0701d0
  | 1, 3 => 0x3fefe618783ff0000070000cc30f001c077c00ffdff8e200
  | 1, 4 => 0x38e0066187bfce0001f8ffd0ffc007f9dff433ec3e0000000
  | 1, 5 => 0xfc400079d88000e3801f8fdf0038eefe6187803e3bfe007dff
  | 1, 6 => 0xf03fefffe7740003bbfe07e0f003fff801f7c3f0ffc01801ef
  | 1, 7 => 0xeeffe3f0c330c3c0000000fc71100007043f1c41e679e0f
  | 1, 8 => 0xfffff8000073ff00000071c1f0380ef81c70400e001f9801c0
  | 1, 9 => 0xf03f0781c777c0e383e071ddff3bfef81c077c000000078000
  | 1, 10 => 0xcfbef866180bc00001fe763dfffc00001c7740000001ff9ddf
  | 1, 11 => 0xcc30f7ffe777ff1001fff7e30000e0001c003f30c3e1f86220
  | 1, 12 => 0x7801ffbfceffa00701d0038eeff81f8000000019861e0
  | 1, 13 => 0xffc007f81f83c000001f8e20f038e0781c077ccf3c1fe06000
  | 1, 14 => 0x300f0787e077fc0c41e071ddfffc00001c777f3efbe00001d0
  | 1, 15 => 0x7ffe004000ffc0001c0f000e0001c7700cf3c01ffe220
  | 2, 0 => 0x38ee8000003c000001ffe1efcc30f7fe3883ff1c7c00701d0
  | 2, 1 => 0xf03fefffe7040cf001fe77e1f00000781c703f30fbc1f8e22f
  | 2, 2 => 0x7e7df7fc0003a0071c10003fe86618083f0ffde678000
  | 2, 3 => 0xffc00066187bc00001e071ddffff107f9dff4000001e00000f
  | 2, 4 => 0xffcee8781883fff001e071c10cc3ef87fe0003fefffffffe0f
  | 2, 5 => 0x7ffff83ff001fe07ff0ffceefffff800000000001c10
  | 2, 6 => 0xee801c0043ceff80007df0ffbff879df840003ba0007fd0
  | 2, 7 => 0xfc0f818078003100401f01ff0000078000000000001ffffd0
  | 2, 8 => 0xe0ffffff4000383fe07e00fff0f067d87c0003bbfffffd0
  | 2, 9 => 0xfc7017800003fc0ffa1f8800f038ee801c774300c38000000f
  | 2, 10 => 0xfc00819e003fff383e00000f000e007ff878330c3de007fe0
  | 2, 11 => 0x33c007800003c00001e0001c0f03f07e618783ceffbf9861ef
  | 2, 12 => 0xfc3ff781c077fc0ffde071c00f03f07ffdffc3f1c040001c1f
  | 2, 13 => 0xffc000000000000000060800ffffff7fffff80003c21f8e020
  | 2, 14 => 0xffff0781df7fc00001e071ddfffff0801c7743fffbe00001c0
  | 2, 15 => 0xfc0f7fe20003ffc3c01f01ff0fcef87ffff83f10380071c00
  | 3, 0 => 0x7800003ff03b81ff9dd00000e00007040000000071c1f
  | 3, 1 => 0x38ee00000040003821e07e0fcfbef80007700000000071dd0
  | 3, 2 => 0xfffef87fff803ffffe0001e0f
  | _, _ => 0
def dictP2B : Nat → Nat → Nat
  | 0, 0 => 0xffcaace6db7cfffffffe47a84ffc884669a68bfdf75c1a812a
  | 0, 1 => 0xff4884669a68b34d3c5ff9108f2bf6aaa699ffc8fd099b69f3
  | 0, 2 => 0xab19935596603c8fdabe57ed5ff7df7001aa9a2493c4bba35d
  | 0, 3 => 0xf6ff7feefbfbbffffbb7791089965e6669a78a99b9541b817b
  | 0, 4 => 0x76db3feefb7efff6efe006ef7f23d427fffe33fff3d5575dd1
  | 0, 5 => 0xf23d4206e15efdbfdba64920c32cb0effa4423c8fd08892473
  | 0, 6 => 0xff48840041144cb2c3aa984590035737fe4423ffffff9b6df3
  | 0, 7 => 0x54501500099debf2211e47e84abaee89965877ff2232a82226
  | 0, 8 => 0xffeeecd5c54440091e71a49e2002679d59774776dfee130151
  | 0, 9 => 0x546444797fa74ca2c2b5fddfbf23d427f9ff9aaeb380892473
  | 0, 10 => 0xff48842a688baaeb300a8a22eef3cf144d37442602e7575991
  | 0, 11 => 0xffdabdfb5fbdc0200a3575dd100377be69a7cffd2a10138159
  | 0, 12 => 0x76db3f8861877fdf75dbaebeef6bf7bd597e57fc664d565980
  | 0, 13 => 0xab2ce8fb7fa77ffb310004cd1bbefee9965067ff665c1b8159
  | 0, 14 => 0xab2ec07fe5467cafd2bfeffeecd34f17b3fab80008a31249e2
  | 0, 15 => 0xaf488446926883702d4a12655fbbfeafb7fbbbfffbf665965d
  | 1, 0 => 0x661831669a78bffffffe47a84cd34d1669a78951445ca9a60c
  | 1, 1 => 0x377bffe45643702f7ff7ff70d80b9f91fa5551445dedf8ea
  | 1, 2 => 0xabaee8aa2883377dfffe57e95ab2ee057f77eeedb718bb2777
  | 1, 3 => 0x377beefbfffff22b3571551cdf4fd84e056400ddcca9a65d
  | 1, 4 => 0xffffc64cb2e33ff2210a8eeddab0b8ad59660336d3e6a9a06a
  | 1, 5 => 0xff48847fe4422aebb00a8ecfbabaef9c49a68abfbbf6006cf3
  | 1, 6 => 0x377bfff662153ddffecfeae00377b801b3ceacb3001b817b
  | 1, 7 => 0x276aaa290ef36dbc4a02655545117000104551445c65961d
  | 1, 8 => 0xab2cc06ebafbbff2210ecb22e5d53971145046ae2ae79a69e2
  | 1, 9 => 0xa22c79d5dffdc8a2c2bfeffaeff7fd72ee9dfd424cab579108
  | 1, 10 => 0xab2cc02a288b9514c5cbaa32effdbb755d66455348f7ffffff
  | 1, 11 => 0xcd37fbd59ee9951445ced3637a2ae68d5ccc9b34d3c4a82666
  | 1, 12 => 0x54d317001bbdfecff08120100af6ed57b3fab9504ccd9a6df3
  | 1, 13 => 0xffcb8ed3362a9534cfea9a67f32cb0e84c0545db6cffe47e84
  | 1, 14 => 0x32cb0e86e05efdb645d567ba6bb488457f67efbefbe71249d1
  | 1, 15 => 0x4c03dffe556400ddcdecfeaeb22f4255d7744cb2c19ffb32e
  | 2, 0 => 0xab2cc88008899534cddffffffdd75f72a2883377dfdcb22704
  | 2, 1 => 0xf23f7bffe5464cb2c3be5fe9d00c00cfffffffbefbe6a8a22e
  | 2, 2 => 0x440157fffffc0000a244100000376ae69a68bfffffe659419
  | 2, 3 => 0xab8aa8e69a7cc0000e777df9dffd9977ddfe11514cdc20820c
  | 2, 4 => 0xfb2ec0280889bff22f7571100cd36f9d5e4423ffffffffffff
  | 2, 5 => 0x54c02cfffffbbff665de47ef7ffefeed5d7600020822000000
  | 2, 6 => 0x26400040047eeff88004880ffbffbf91fa10009100006e84
  | 2, 7 => 0xdc0bd99458541100541b817b04c0150041000430c19ffff8c
  | 2, 8 => 0x54d33fd5d7744000c2bedd888ff7cd54492600439dbbffffdd
  | 2, 9 => 0x5451170041957c8fdabbaa36eab2ce07d9fe1366dfaaa8a26e
  | 2, 10 => 0xdc08c9964067ff6efe000615a23f427d9e60335d3d4004880
  | 2, 11 => 0x32c9062a608300000451349d1f6ff57669b7cfffffff9be9fb
  | 2, 12 => 0xff7ff72ee8dffc8fdef565980f23f7bfd9fe10000000002677
  | 2, 13 => 0xffdbaeaa288300048e620820cffffffd596600000c2aa9a06a
  | 2, 14 => 0xffffced5dffdd53447f57ddd9ffffced597646acb3011269e2
  | 2, 15 => 0x5dd3bfaa61167fffbf6bba77fafeefdfd9fe13759390451400
  | 3, 0 => 0x4410398000047fcbb815659800980a8d117245524cee459419
  | 3, 1 => 0xabaee000000440208a3ecfaaeef3cd17f9ff980000a3575d80
  | 3, 2 => 0xfffefdd596603fffffe000615
  | _, _ => 0
def p1At (i : Nat) : Nat := fld (dictP1B (i / 128) (i / 8 % 16)) 25 (i % 8)
def p2At (i : Nat) : Nat := fld (dictP2B (i / 128) (i / 8 % 16)) 25 (i % 8)
def wireDAt (i : Nat) : Nat × Nat × Nat :=
  if i < 404 then (wireAt i, p1At i, p2At i) else (0, 0, 0)
def wireDOK (i : Nat) : Bool :=
  (p1At i == projBit r1sG (wireAt i)) && (p2At i == projBit r2sG (wireAt i))
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
theorem wireD_ok_all : span wireDOK 404 0 = true := by decide +kernel
theorem projBit_zero (rs : List Nat) : projBit rs 0 = 0 := by
  induction rs with
  | nil => rfl
  | cons r rs ih => simp only [projBit, List.foldr_cons, Nat.zero_testBit, Bool.false_eq_true, ite_false] at ih ⊢; rw [ih]; rfl
theorem wireDAt_eq (i : Nat) :
    wireDAt i = (let w := if i < 404 then wireAt i else 0; (w, projBit r1sG w, projBit r2sG w)) := by
  unfold wireDAt
  split
  · next hi =>
    have h := span_ok wireD_ok_all i (Nat.zero_le i) (by omega)
    simp only [wireDOK, Bool.and_eq_true, beq_iff_eq] at h
    simp [h.1, h.2]
  · simp [projBit_zero]
def wireSAt (i : Nat) : Nat := if i < 404 then wireAt i else 0
def stateWiresD : Nat → Nat → List (Nat × Nat × Nat)
  | 0, _ => []
  | n + 1, ids => wireDAt (fld ids 9 0) :: stateWiresD n (ids >>> 9)
def stateWiresS : Nat → Nat → List Nat
  | 0, _ => []
  | n + 1, ids => wireSAt (fld ids 9 0) :: stateWiresS n (ids >>> 9)
def SD (s j : Nat) : List (Nat × Nat × Nat) :=
  let packed := fld (stateB s (j / 256) (j / 16 % 16)) (stateW s) (j % 16)
  stateWiresD (packed &&& 15) (packed >>> 4)
def SS (s j : Nat) : List Nat :=
  let packed := fld (stateB s (j / 256) (j / 16 % 16)) (stateW s) (j % 16)
  stateWiresS (packed &&& 15) (packed >>> 4)
theorem stateWiresD_eq (n ids : Nat) :
    stateWiresD n ids = (stateWiresS n ids).map (fun w => (w, projBit r1sG w, projBit r2sG w)) := by
  induction n generalizing ids with
  | zero => rfl
  | succ n ih => simp [stateWiresD, stateWiresS, wireSAt, wireDAt_eq, ih]
theorem SD_eq (s j : Nat) :
    SD s j = (SS s j).map (fun w => (w, projBit r1sG w, projBit r2sG w)) :=
  stateWiresD_eq _ _

def htAt (s i : Nat) : Nat := fld (HT s (i / 64)) 32 (i % 64)
def idxH (s h : Nat) : Nat := bsr (htAt s) h 11 0 (NN s)
def idx (s : Nat) (zs : List Nat) : Nat := idxH s (hk 0 zs)
def CN0 : Nat → Nat
  | 3 => 3
  | 4 => 95
  | 5 => 211
  | 6 => 102
  | 7 => 6
  | _ => 0
def CH0 : Nat → Nat → Nat
  | 3, 0 => 0x3b13e2022cc4b17705fe11af
  | 4, 0 => 0x3e7c2df53bcdb45d3a8e0deb3a701a5c36eb506933e2c72d33dff7d9338c9f3731febb9a30d5ae122ff0a9f92bf7616b2b825aea229add2f214578c4209793e31fca8d861f16380d1d188e201cd686261c3723c71b82b4341a5ffb3419ac50151904ce6d18ee684d18c2ab1717f8b54a17892e7d17273acf14839bc11479195e1466fc7d146313bc128f13e1125d412e11f9193a11f700f7103ee1de0fac555e0ecebafa0ebb1d5b0de343b40c804eb60c6802830b8dfada0aa95f9108a0c720087b1dd70839e2be072515d90553d48104bfe0c604a63b340453e7e703b4b7930387facc03840a190359a94102839914027ca88d023beafb019551f80162e051
  | 4, 1 => 0xcac8f503adfe94f5a68cb6ed9abc05fe958ad33491899def8f9570a78b7d27397d4dd3a3764972cb745f33c174064f5d723bc3336fe14b5466f6ac5666b3d8d7642a02f360464a4b5fb774a35fa357435f84236f5a65da5057c4af0048dc9b34472e25f744a115be4487c4e84230933c40e88592407e719b3f47ba24
  | 5, 0 => 0x157354bb14d7b51a1495c976147cdb0e144aa95c139f5f7913566f9212a8ee77129dfe45128f13e111f700f711dd46cd118433b6117fcf9b1051d8b50f2e10800ecebafa0ea7aa9b0de343b40da5da0f0d3224c20cd5b6210cca45450c4d24140b8d28ca0b7f649e0b7b7bdd0b112e2a0ae3b4920ade87150ad291f909eb26b109e2bbbd09d93dc0097ce85509671b3708ed0bf3087b1dd707b7eebd07ad77010728aace06c052ef06b4c87d0696a89d067f9d580663b0240578eca7056c9285055409fa03d1223d03b306420398b6d702a10d5502839914027ca88d023beafb02174f7101c71c7900e7bb4400a7504a0098b1da00620756001490b5000975be
  | 5, 1 => 0x31aca04631711ecf30f9f5da30d5ae12306478043020bb002f1339232eb642ba2dd9999c2dd74bac2da820352c56ab272b0390432a1576ce2968bee228d75ccc277cd17e26a284a22683fb59265db18e2634626625b8d3cd258fc2bd258c480e251c09242512a6e5249be68623be9a8a222f459121a8620b209793e3205f4d0c1fbc84251f16380d1eed030f1e29e5df1dff87f51d7f95801ca967ea1ca87ea71c57d3141c37d7fb1c3723c71bf7b3ff1be11d8c1b03580219d95e7719b3455019ac501519269bd918ce8c0b18c2ab1718aef6d21875fb5917f3b30d179d20cc174eda3a17273acf16e0a50516c52baf165cf9b916490c0c15e76c8715b27eb4
  | 5, 2 => 0x78270ea7745f33c174064f5d73aae8767251ab49723bc3336d4311f96b1cb35a69bbe548674617ea64e0f4886432baff60464a4b5ffe7e135ee0ce8d5a52c6e95a1964a056b9bb40569c8b9056832b8c538c6ae1535930134f772f1f4cedcc664cc3684c4c7b51494c39de8b4bb75dea491e45b748eb6918486d6366472e25f74725266d459b61e84523fb8544cfb8d643ba1958431deb0141f586ac3fc39e543f81b9033f4a3df73f47ba243f1826db3ea3a29c3e7c2df53dc7b9163cd9b3ad3cb0c2713c7dd9f53c1033463c0feb433b2e37d43a9c48ad3a98c5a63a8e0deb3a5867cc38e3637936b2686c361e4a6c33d80d653320347c3272e35e3216e1eb
  | 5, 3 => 0xe5b7cd4dcad78348c6027b62bdf5a666b65abf17ac6dc52ba869c69da2af9b639da0aded9abc05fe90d794b98f9570a78b7d27398765ed6c871dd8fc86168564849a4bcf800d7a7a79fdea3c
  | 6, 0 => 0x3f4a3df73f47ba243c148c763b26db90371cec763653240c33d80d65339c65e933445ff73216e1eb2f1339232c56ab272b0390432ae209c32a1576ce2982f0a9283891c72785873c258fc2bd258c480e249be68623c341f223be9a8a2382e75721a8620b205f4d0c1f7d4f3f1f16380d1eae7a981ea518591e29e5df1c2b0f061be11d8c1b0358021a2e0af919d95e7719140e4617fecaef17f3b30d16e0a505162c98381495c97612a8ee77129dfe4511c3c9801058cbbe0f837eb50e2e975b0de343b40da5da0f0c4d24140b9f98b20a93ed580a5683b30a53dedb09e2bbbd090d6eb408fdcdb8081d8fae0728aace0578eca7055409fa04362bd203d43e99
  | 6, 1 => 0xcbd6e52bb65abf17b113dc2a9da0aded90d794b98f9570a7889a1c768860987f7cfbddfb745f33c173aae876723bc3336b1cb35a6a5f52f466c4e4fd657bcffe6535ffaa64bb7ab06432baff624840145f84236f5a9c45fa581d117257093a62569c8b9054f3296350ecb3cc4f6aa5084dd461924cedcc664c7b51494bb75dea47308bae472e25f74523fb8543e31893431deb014093c237
  | 7, 0 => 0x569c8b902c56ab2721a8620b205f4d0c1e29e5df1495c976
  | _, _ => 0
def CV0 : Nat → Nat → Nat
  | 3, 0 => 0x10101
  | 4, 0 => 0x20102010100020101010002000202010101000202020102000201020002000202010202020101000202020101010201020101010102020200000100020101010201010001010202010100020101010101020001020102020000
  | 5, 0 => 0x100000201010100020000020002000001010000010202000000020001010201020100020002010001010200010002000102010101010201000200010102010201010000020101010002010101010201010101010202020100010001000200020000020101000101020101010101010100020201010102020002020200000201
  | 5, 1 => 0x100020202010102020000010200010102020102000201010100020000020100010201010201010100020101000102010102020001000002010102010202000101010002010100020202000200000202010101
  | 6, 0 => 0x10200020001000200000101020201010201010001010202010202010201000201020001010102020100000002000201010200020200000102000202000101010001000002000100000200010200010001000200000201010101010101000101000201000201
  | 7, 0 => 0x10201010200
  | _, _ => 0
def ch0At (s i : Nat) : Nat := fld (CH0 s (i / 64)) 32 (i % 64)
def cidx0H (s h : Nat) : Nat := bsr (ch0At s) h 9 0 (CN0 s)
def CN : Nat → Nat
  | 3 => 23
  | 4 => 177
  | 5 => 306
  | 6 => 76
  | _ => 0
def CH : Nat → Nat → Nat
  | 3, 0 => 0xd0ae419ecd2ef5487a9b5bac6fb7020559655e38584da63151ff76b1501c1de446adbe7434c66d482c2731041ee3d2e91d5b6be2195b47c41954951118cbd18114eb2316148c7f4a1432d87910e2a874063fd312027fb23f021abbb0
  | 4, 0 => 0x198f4a791984786518f0cd36189b0920187e72d1186c5694168c9a041646c4e5163cd4281638698415312f4d1503d58c14db1b6913f9d2941380462c13459e7e128a615c122d2b4811c17ebb11af5a28113f11d310bb400410a86bb1109e27280edb53620e4d63be0e1871e70d0f81e70d0429c00c39d32b0afa10b109f7b9f7098d848608dbdf9608d8015408d1fd100888415a08812045082bb2f9080f917907e3ca7b07d3528d0788e81106fceb06069b8c5f067f080e0677170d06546667063f36700639f2da05ac74cf055380e40523302004ad74590467e2ff0452a69e039e503b03766de40217a507013a846901067c0c00f573c300c458900047ea79
  | 4, 1 => 0x3cb83acc3bd3a5a53b8808703b5f84c23aa6da433a3b012639632b0b373d8fa234df5f8b340d27933403aca233a4ec4e33954b5a337d731c32e0f8ef32d12be331f0686f30e9e925307e98922f10695d2e14c5cb2ceeddbf2be0ec102b23c3022b1ba08c2a562e982a4786062a2b956229dfc379296eae57295b03be28eab03128ac9fee28159997279e2f742660575b265b607d2539ac0524496ef223a1d14b2393a925226db3442220874421785020216bd3922107472e203dfb701f87dcae1eebefa01e13e8661e03a33b1dfe44b51db8f2871db73dbe1da877471d8eec5a1ce37bc61cd662cf1c4811941b8275851ac19c561a50ced01a4a519c19d1a33f
  | 4, 2 => 0xd38b2ae7d06a0f73b6bc70bdad33e64eaa0105c8a8f15e3c97bb273a905bb3868feb91488603c6888591966d84ca48f281f02b7e7fb5a5867f482aa17b80a33478ae500d77f4ece47130bb3570ea08486faca1266bbf1a146aef8a7e6adceac56945129868dae5b4666dcc7c65d24e5d61f99b7e5ff8f47b5f8ed8d05ba209845ad4837b5a3ae7135476644053476189526660c250e6a717489683a446217e5445448b5b445ac02142a9d65d4124863d406290b23f9b53ee3f1832b43ebda9fb3dc62695
  | 5, 0 => 0xd94723f0d59fc0a0d0988220cf82ab40c6ddba60c1ad0420c1a20b80bf820c70b7f8d910b67b78a0b2020350ad5ba4c0ad15a450acfbebd0a98b35c0a4954ce0a2cce430a2ca74d0a1f7a7c0a09a33009e08ade09a0ff5b08f343ab08aa2e5a085e7c100842734d07c3e07507ae543b07a7e0cb0726a3c3070556e0065e29090651de64060de897060d3ace05ee31b205a1a993056afecc053466f8051c014404cba4a0044d0903042f0bce04284499042604df0381f35602f7588202e31f0e02d1aa4302293c9c0209f1c501fab9ea01d6939901bf928a01b3e481017db7bb01718bbb016b09ec00ee766a009ec55d009c3eb200767d8b0046f4b60020e1c2
  | 5, 1 => 0x200d758c1fdf43341fcff3db1f78a0461f7108561e1f0aba1dca3b861da9ab4e1d853eac1d2687611cbb26901c919a4c1c6866fd1bddd6611b733b061b4ac88a1ae99bb31a2e0af91a03fe8d1a00225519fa8ca719f73aef19d4160919102245190774bf18e9295f18574f2717f89e0017de26d917d8d14d1792c8a7177f45191743637d1629253e161ca52115d10e4f1596e92614a74cdf148e0880145953b51433aba9141a91591400b75b13e766ec136f47ec12e256e812b3eed412a535e11288ee2a127e03c81212de2811c4836510d02a8710894bb9102cef5f0ffe89a00ff245720f0bfb1b0efccafd0edcab7f0ed77c3a0ecd5a9b0e9b53410e1ec4c7
  | 5, 2 => 0x37f6179d36e4dae736b3bc0f366b35313646b8aa36099562357f84d83571e9f433afe7d1321bd09f31faa9a731f6b43331bf8c533168dc1d314295dc31255c9e30b117c63092493b307e76822e96a7832e176abf2e0b8d202e008eb02d16b03a2ccea50d2bde9fb52bce8e692b31da562b25634e2a9c8ad92a5657b12a0db92029a3807f296918d228b5230d285495b52806214e27e3089c273096f426792b2225bdec562588810f2583228925694e7d25587719255673e42554d964255288b0254f218d248bac872439f86a24133d5a240d8b8823bfc85e22fe212722f9a898224050b621faf87021b7059a21b13f8d2175128f217488fa204e41f8202fbf56
  | 5, 3 => 0x6661927d662bd7b8659e1c4b657145f1642e0b15642b4f8d62b6f13062a2f7be6294ae8d6130fc0a609daab85f60432a5f04beac5ebce3045db2e00c5cf7f57f5bf603c85ae5dcc15902c3ba559585d6520615d751ff0cf950e79f4450a60a2b50091a984ddab1024dc7e76c4cbdce324c919c034c6d86284c62e38f4af1edaa4ae89a7d4aad839a4a40ca4a4944f5994864eb2348532aec4847ad40476754ef45694316449f55b84454fa8343d3ce9b437ce6ff42f19a6e42bad9fc4262aa3e42203372417524043dfebca33da4e1d03d7fbd7d3d2a2d5a3cf7e55e3c5bccd13c368b993c2bf7d63b1830513b053fb13a2665a4395115af38a2bbef383e6c71
  | 5, 4 => 0xc9c7b516c36119d1b8bce15bb7f49ba6b44642d4b437c42faec8dd2dabe1a566aa226dcaa0e1d55197d2673b971c8788960297e295b408c39392a047938b95519271714890aef7f08f95f8598e4e2b0e8a47696288ffc9fb886442c081da549f80913fa07ebabcba7eb78ff57dd934a47d3b01f479c0eb36780e9d6976d7341975f659957578bb0a7316c80a72dea0c87168a40c710c456670d3005170a62d116f0f91706df448946d8d570668a26ace6877d10e682117ab6794fe486782570866ba5af066960ad5
  | 6, 0 => 0x52d77dd752aa92fe51b67c364cd0e5334b8a17ad49e7881244e04f8d44df2f9841690f404141d1b240dbce913f92b9923d5d52653c811b283abf1546347da4493445ab86341309da33c935fc3161aefe2d7032702ccced9a2b2efe1729014be223ca5eed22c1e95421d25ddc21b4f2fa2178d4551fde715f1f436d281ce8e1971c546ad41c25b9451b25f3a91af425c01a9a6f2418d417f81823acbe1745b8e817232ed7164de1ce1600da7615af50bf1530284314d28d9511b1ac170fec26080eb6f7510ea311090e61fd760ca6363d0c74e5bb0c6da9dc0ba670a10938c25508f6698f089d02fa08211c8608088c3708025a3205534df702d98d73019c70d0
  | 6, 1 => 0xcd3587fa92de54fc8cc90b268c58e9437a60f7f17a4140fa79cc812e7579266866e6e8cb5e5072d55cc01e2757b612d9
  | _, _ => 0
def CV : Nat → Nat → Nat
  | 3, 0 => 0x1170100530254c05010c01171004130154c41100c0153104403015444210cc055110c42302000512008055110c423014548621cc051510843301454c230cc055320480302000d1100801171004130054443108c01171004130054443108c05171004130154443108c0153104403014548621cc055310440302
  | 4, 0 => 0x512388040034041202000401048055110c42301000d31008080034480201001040248000010440201000d3100800003404120054443108c0400148c12020009203480000104402010009210480400348412000004101080400144c0201000921048015110c42302000921048080024cc7200000431088040042c41200000d210480000000c0102000d01048040024440202000903048000034041202000400148000024041202
  | 4, 1 => 0xc13008080024cc02010005130080800244c6201000c631c8000010c42202000d2104800003488120054443108c04003444020054443108c0400000c710100041100800002188720254443108c080021484201000933008015110c42300000d121c80000244c620254c41100c080000040101001043048040034c40200000d12008080034c862010000010440400244402000010730480400104402010004110080000240c1201
  | 4, 2 => 0x10c1048080034487202001043048000024c40200000d30108040034841201000d10108040000040102000431088040034c40201000d12008000024c40200001042048040034c86202000d220480400104402010009131c80400318c72020000032440000410c12020004210c8000034041200000513008080034486201000931008040024c40202000431088080024841201000d010480000244402000005330080800304c0200
  | 4, 3 => 0x931008080043c81200000d110080800308c3200000070188080034486202000933188000034841202000401048080041c0d2000005130080153104403000010f014800003484120154c41100c080034440201000d11008040010c422010004310880800410c1200000d01048055110c4230200093100800002404120000108104800000180720054c41100c040010843201000d21048040034041201000911008080034440200
  | 4, 4 => 0x5130080000348412020010c0148000034440201000d210480800340412020000401480800104402020004010480400344862000004210c8000001404202000911008080034c86200000401048015110c42301000533008040034440200000913008080043c81202001072048040024440201001073048040000041100000921048080034c87201000d121c8080034c40200000d11008040042c4120254443108c095110c42301
  | 4, 5 => 0x40101000401048040010843200000d11008000010440201001043048000010440201000d210480000300c120100000100408001044020054443108c080034081201000d01048040010041201000d2104804002400d200
  | 5, 0 => 0x1840800000c110000043108804000008d1010000013c40000000411020000021440000000c11000009010480400000431010000030440000000811010000020840800000431010009210480400000421000000030840000000ca1010009210480000000401020000013c40400344402010000030440000000c31010000030440800000861010000010c40000000851020000023440800344402010000023440400000c9100
  | 5, 1 => 0x144080000041100000000184000000086102000001004080010c422000000031840000000811000000001c40400000c51000000020c4000042cc1201000003044040010440200000001044040010c422020000031840800000401020000010440800000411000000001440400000c11010004310880400000821010000001c404000004110200000108404000000f100000003004040010440202000002044080000040100
  | 5, 2 => 0x31440400000431020000021840000344862000000001440000000c01000000010840400000851010010f2048080000081102000002184000000006100000002084000000085101000d210480800000861010000031040000000811020000031c40400000041010000021440000000c91000000010c4080000082102000d110080800000431020000010040400000c4100000003044000000082102000001044040034440201
  | 5, 3 => 0x314408003448620100091100804002484120200000314404003444020200000214400000004110200000208400000008610000000100408000000b1020000001c40000344402020000010440800000c91010004310880000000ca1010000021040400000421020000013c40800000041000000020840800000c21000000020c408000000510000000208400000004210200000218404000008d100000001044000024c40200
  | 5, 4 => 0x10440000000421000000012c404000008e1020000010440000000c01020000030040400000401000000032440000000c91000010430480800104402020000010440000000c11010004110080000000c51010000012440000104402000000001040000104402010000031440400000c31000000010840000000c1100000d110080000000421010000010c40400000c0101000002144080000082102000002144040000040102
  | 5, 5 => 0x10c404000008e100000d110080400000421000000032440000104402000000021c40000000411020010430480800000401020000030440800244402000000021840400000431020000010c40400000c91020000031440000348412000000030840400000431010000001840400000801000000010c4080000043101000000104040000043102000001004080010c422020000003440400000811000000032440400000c1101
  | 5, 6 => 0x10040400000411000000010c4040041c8120200091100804000004110200000100408000008d1000000010040400000421010000001040000000c61010000001c404000004b102000d210480800000c61020000030440400000c6101000003284040034841201000d110080800000041020000010840800348412010000030c40800000c91020010720480800000811000000010440800000c5100000001004040000086100
  | 5, 7 => 0x10c40800000c9101000001004040010c422010000001c40800000431020000030440400000411000000020840000000861020000010040400000401000000003c40800000c71010000021c40800000821000000032440800000c11010000001040800000c91000000012c40400000c9101000d210480800000c51010000010c40800000411010000010440400000431000000010440400000421000000010c40800000c2101
  | 5, 8 => 0x10040000348412010004110080800000411000000010840800104402010004110080400000421020000010c40400000411010009310080800000411020000010440000000c61000000023440800000401000000032440000000851020004310880800000411000000001c40800000051010000021c4040000086100000003044040034041202000d210480000000861020000030440000000c9100000431088040000006100
  | 5, 9 => 0x10840800000431000004310880400000411020000010840400000071010000010c40400000401000000020440400000421010000021040400000061000000010440800000051000000010c4000000042101000001044000000040101
  | 6, 0 => 0x30840800000c51010000031440400000821000000010440800000811010000031840800000c61010000030440800000c91020000021440000000401000000021840400000c21000000031840800000411010000031840000000411010000021840000000421010000020440400000411020000010840400000c1100000003044080000085102000003244080000085102000003084000000043102000001044000000043101
  | 6, 1 => 0x10840000000421020000030840800000401020000010c40800000c61020000010440400000421020000020440400000c21010000010c40400000431010000010c40800000811000000010440000000851010000032440800000c51000000010c400000004110100000100408000004210200000100408000008d1010000010840000000401010000030840400000811000000010040400000c61020000010040800000c2102
  | 6, 2 => 0x20440400000431010000021440000000c110200000324408000004210200000324408000008610000000318404000008d100000002144000000040101
  | _, _ => 0
def chAt (s i : Nat) : Nat := fld (CH s (i / 64)) 32 (i % 64)
def cidxH (s h : Nat) : Nat := bsr (chAt s) h 10 0 (CN s)
def checkCutByIdx (s : Nat) (ws : List Nat) (hint : Nat) : Bool :=
  match hint &&& 255 with
  | 0 => checkCutEntry true dom_23 roots_23 6 s ws hint
  | 1 => checkCutEntry true dom_27 roots_27 6 s ws hint
  | 2 => checkCutEntry true dom_15 roots_15 6 s ws hint
  | _ => false
theorem checkCutByIdx_sound {v ys hint} (hc : checkCutByIdx v ys hint = true) : ¬ RunD true dom_31 goalM v ys := by
  unfold checkCutByIdx at hc
  split at hc
  · exact checkCutEntry_sound (by decide +kernel) (by decide +kernel) (by decide +kernel) (by decide +kernel) lowS_23 _ hc
  · exact checkCutEntry_sound (by decide +kernel) (by decide +kernel) (by decide +kernel) (by decide +kernel) lowS_27 _ hc
  · exact checkCutEntry_sound (by decide +kernel) (by decide +kernel) (by decide +kernel) (by decide +kernel) lowS_15 _ hc
  · contradiction
def cutHitH (s h : Nat) (ws : List Nat) : Bool :=
  (let i0 := cidx0H s h; decide (i0 < CN0 s) && (ch0At s i0 == h) && checkCutByIdx s ws (fld (CV0 s (i0 / 128)) 8 (i0 % 128))) ||
  (let i := cidxH s h; decide (i < CN s) && (chAt s i == h) && checkCutByIdx s ws (fld (CV s (i / 32)) 42 (i % 32)))

def cutHit (s : Nat) (ws : List Nat) : Bool := cutHitH s (hk 0 ws) ws

theorem cutHitH_sound {v ys} (h : cutHitH v (hk 0 ys) ys = true) : ¬ RunD true dom_31 goalM v ys := by
  unfold cutHitH at h
  rw [Bool.or_eq_true] at h
  rcases h with h0 | h1
  · simp only [Bool.and_eq_true] at h0; exact checkCutByIdx_sound h0.2
  · simp only [Bool.and_eq_true] at h1; exact checkCutByIdx_sound h1.2

theorem cutHit_sound {v ys} (h : cutHit v ys = true) : ¬ RunD true dom_31 goalM v ys := cutHitH_sound h

def symsG : List (List (Nat × Nat)) := [[(0xff000000ff000000ff000000ff000000ff000000ff000000ff000000ff00, 8)], [(0xf000f000f000f000f000f000f000f000f000f000f000f000f000f000f000f0, 4)], [(0xf0f00000f0f00000f0f00000f0f00000f0f00000f0f00000f0f00000f0f0, 12)], [(0xff000000ff000000ff000000ff000000ff000000ff000000ff000000ff00, 8), (0xf0f00000f0f00000f0f00000f0f00000f0f00000f0f00000f0f00000f0f0, 12)], [(0xff000000ff000000ff000000ff000000ff000000ff000000ff000000ff00, 8), (0xf000f000f000f000f000f000f000f000f000f000f000f000f000f000f000f0, 4)]]
theorem symsG_ok : symsG.all (fun ms => ms.all moveOK256 && (applyMoves ms dom_31 == dom_31) && (applyMoves ms goalM == goalM)) = true := by decide +kernel
def ori (zs : List Nat) : List Nat := pickMin 0 zs symsG zs (hk 0 zs)
theorem ori_ok {v ys} (h : RunD true dom_31 goalM v ys) : RunD true dom_31 goalM v (ori ys) :=
  pickMin_runD 0 ys h symsG ys (hk 0 ys) symsG_ok h

def Z (s : Nat) := bar true dom_31 goalM mpG SD SS NN htAt idxH ori 0 pool6G cutHitH s
private theorem z0 : ∀ i, 0 ≤ i → i < 0 → Z 0 i = true := by omega
private theorem z1 : ∀ i, 0 ≤ i → i < 0 → Z 1 i = true := by omega
private theorem z2 : ∀ i, 0 ≤ i → i < 0 → Z 2 i = true := by omega
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
private theorem z3 : ∀ i, 0 ≤ i → i < 59 → Z 3 i = true := span_ok (by decide +kernel : span (Z 3) 59 0 = true)
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
private theorem z4_0 : ∀ i, 0 ≤ i → i < 128 → Z 4 i = true := span_ok (by decide +kernel : span (Z 4) 128 0 = true)
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
private theorem z4_128 : ∀ i, 128 ≤ i → i < 256 → Z 4 i = true := span_ok (by decide +kernel : span (Z 4) 128 128 = true)
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
private theorem z4_256 : ∀ i, 256 ≤ i → i < 380 → Z 4 i = true := span_ok (by decide +kernel : span (Z 4) 124 256 = true)
private theorem z4 : ∀ i, 0 ≤ i → i < 380 → Z 4 i = true := (range_split z4_0 (range_split z4_128 z4_256))
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
private theorem z5_0 : ∀ i, 0 ≤ i → i < 128 → Z 5 i = true := span_ok (by decide +kernel : span (Z 5) 128 0 = true)
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
private theorem z5_128 : ∀ i, 128 ≤ i → i < 256 → Z 5 i = true := span_ok (by decide +kernel : span (Z 5) 128 128 = true)
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
private theorem z5_256 : ∀ i, 256 ≤ i → i < 384 → Z 5 i = true := span_ok (by decide +kernel : span (Z 5) 128 256 = true)
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
private theorem z5_384 : ∀ i, 384 ≤ i → i < 512 → Z 5 i = true := span_ok (by decide +kernel : span (Z 5) 128 384 = true)
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
private theorem z5_512 : ∀ i, 512 ≤ i → i < 545 → Z 5 i = true := span_ok (by decide +kernel : span (Z 5) 33 512 = true)
private theorem z5 : ∀ i, 0 ≤ i → i < 545 → Z 5 i = true := (range_split (range_split z5_0 z5_128) (range_split z5_256 (range_split z5_384 z5_512)))
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
private theorem z6_0 : ∀ i, 0 ≤ i → i < 128 → Z 6 i = true := span_ok (by decide +kernel : span (Z 6) 128 0 = true)
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
private theorem z6_128 : ∀ i, 128 ≤ i → i < 143 → Z 6 i = true := span_ok (by decide +kernel : span (Z 6) 15 128 = true)
private theorem z6 : ∀ i, 0 ≤ i → i < 143 → Z 6 i = true := (range_split z6_0 z6_128)
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
private theorem z7 : ∀ i, 0 ≤ i → i < 10 → Z 7 i = true := span_ok (by decide +kernel : span (Z 7) 10 0 = true)
set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
private theorem z8 : ∀ i, 0 ≤ i → i < 1 → Z 8 i = true := span_ok (by decide +kernel : span (Z 8) 1 0 = true)
theorem checked (s : Nat) (hs : s ≤ 8) : ∀ i < NN s, Z s i = true := by
  interval_cases s
  · exact fun i hi => z0 i (Nat.zero_le i) hi
  · exact fun i hi => z1 i (Nat.zero_le i) hi
  · exact fun i hi => z2 i (Nat.zero_le i) hi
  · exact fun i hi => z3 i (Nat.zero_le i) hi
  · exact fun i hi => z4 i (Nat.zero_le i) hi
  · exact fun i hi => z5 i (Nat.zero_le i) hi
  · exact fun i hi => z6 i (Nat.zero_le i) hi
  · exact fun i hi => z7 i (Nat.zero_le i) hi
  · exact fun i hi => z8 i (Nat.zero_le i) hi
def RootG (s : Nat) : Bool :=
  scr true dom_31 goalM s pool6G xsM || cutHit s (ori xsM) || found SS NN idx s (ori xsM)

set_option maxRecDepth 40000 in
set_option maxHeartbeats 0 in
theorem rootChecked : span RootG 5 4 = true := by decide +kernel

theorem proper_failG : ∀ zs ∈ xsM.sublists, zs ≠ xsM → unorientedCov pairsG zs = false := by decide +kernel

theorem noRunFull (s : Nat) (hs : s ≤ 8) (h : RunD true dom_31 goalM s xsM) : False := by
  have hmin : 4 ≤ s := by
    have hl := run_len h; change 5 ≤ s + 1 at hl; omega
  have hr := span_ok rootChecked s hmin (by omega)
  unfold RootG at hr
  rw [scr_no pool6G h, Bool.false_or, Bool.or_eq_true] at hr
  rcases hr with hcut | hf
  · exact cutHit_sound hcut (ori_ok h)
  · rw [found, Bool.and_eq_true, decide_eq_true_eq, List.isPerm_iff] at hf
    exact bar_all (pairs := pairsG) (by decide +kernel) rfl rfl (by decide +kernel) SD_eq (by decide +kernel) ori_ok cutHitH_sound checked s hs _ hf.1 (Run.perm hf.2 (ori_ok h))

theorem noCircuit : Lower true dom_31 roots_31 goal_31 9 := by
  intro p bank hr ha
  by_contra! hsmall
  have hnc : ¬ IsConst dom_31 goal_31 := by
    have h0 : isConstB dom_31 goal_31 = false := by decide +kernel
    intro h; rw [(isConstB_iff _ _).2 h] at h0; contradiction
  obtain ⟨s, ws, hs_le, hnd, hws_sub, hrun⟩ := reach_to_run (by decide +kernel) (by decide +kernel) (by decide +kernel) (by decide +kernel) hnc hr ha
  have hperm_sub : ∃ zs, zs.Sublist xsM ∧ ws.Perm zs := by
    refine ⟨xsM.filter (fun x => decide (x ∈ ws)), List.filter_sublist, ?_⟩
    refine (List.perm_ext_iff_of_nodup hnd (List.Nodup.filter _ (by decide +kernel : xsM.Nodup))).2 ?_
    intro x; simp only [List.mem_filter, decide_eq_true_eq]
    exact ⟨fun hx => ⟨hws_sub x hx, hx⟩, fun h => h.2⟩
  obtain ⟨zs, hsub, hpz⟩ := hperm_sub
  have hrun' := Run.perm hpz hrun
  by_cases heq : zs = xsM
  · subst heq; exact noRunFull s (by omega) hrun'
  · have hcov := unorientedCov_ok (by decide +kernel) pairsG (by decide +kernel) hrun'
    rw [proper_failG zs (List.mem_sublists.2 hsub) heq] at hcov; contradiction

end S_31

theorem lowS_31 : Lower true dom_31 roots_31 goal_31 9 := S_31.noCircuit

theorem lowS_63 : Lower true dom_63 roots_63 goal_63 10 :=
  lower_slice (by decide +kernel) (by decide +kernel) (by decide +kernel) (by decide +kernel)
    (by decide +kernel) (by decide +kernel) (by decide +kernel)
    (by decide +kernel) (by decide +kernel) (by decide +kernel)
    [(0xffffffff00000000, 6, 38)] (by decide +kernel) (by decide +kernel) lowS_31

def ptN (r : Nat) : Fin 6 → Bool := fun i => r.testBit i.val

theorem roots_bits : ∀ r : Fin 64, roots_63.map (·.testBit r.val) = List.ofFn (ptN r.val) := by
  decide +kernel

theorem goal_eq_f : ∀ r : Fin 64, goal_63.testBit r.val = (fun x : Fin 6 → Bool => Nat.testBit (4008372968 * 2 ^ 32 + 4008372904) (∑ i : Fin 6, if x i then 2 ^ (i : ℕ) else 0)) (ptN r.val) := by
  decide +kernel

theorem dom_bit_lt : ∀ r : Nat, dom_63.testBit r = decide (r < 64) := by
  intro r
  by_cases h : r < 64
  · simp only [h, decide_true]
    have hfin : ∀ i : Fin 64, dom_63.testBit i.val = true := by decide +kernel
    exact hfin ⟨r, h⟩
  · simp only [h, decide_false]
    apply Nat.testBit_lt_two_pow
    have hlt : dom_63 < 2 ^ 64 := by decide +kernel
    exact lt_of_lt_of_le hlt (Nat.pow_le_pow_right (by omega) (by omega))

theorem lb_with_not (gates : List Gate) (o : ℕ)
    (hfan : ∀ g ∈ gates, g.op ∈ ({GateOp.and, GateOp.or, GateOp.not} : Set GateOp) ∧ g.inputs.length ≤ 2)
    (hev : ∀ x : Fin 6 → Bool, Circuit.eval ⟨gates, o⟩ (List.ofFn x) = (fun x : Fin 6 → Bool => Nat.testBit (4008372968 * 2 ^ 32 + 4008372904) (∑ i : Fin 6, if x i then 2 ^ (i : ℕ) else 0)) x)
    (hhas : ∃ g ∈ gates, isNotGate g = true) : 11 ≤ gates.length := by
  obtain ⟨g, hg, hgn⟩ := hhas
  set out := (execN gates roots_63).getD o 0
  have hout : out &&& dom_63 = goal_63 &&& dom_63 := by
    apply Nat.eq_of_testBit_eq; intro r
    rw [Nat.testBit_and, Nat.testBit_and, dom_bit_lt]
    by_cases hlt : r < 64
    · simp only [hlt, decide_true, Bool.and_true]
      have h1 := execN_bit gates roots_63 r (by omega) (fun g' hg' => (hfan g' hg').1)
      have h2 := congrArg (fun l => l.getD o false) h1
      rw [roots_bits ⟨r, hlt⟩] at h2
      have hgd : ((execN gates roots_63).map (·.testBit r)).getD o false =
          ((execN gates roots_63).getD o 0).testBit r := by
        simp only [List.getD_eq_getElem?_getD, List.getElem?_map]
        cases (execN gates roots_63)[o]? with | none => simp | some v => rfl
      rw [hgd] at h2
      exact h2.trans ((hev (ptN r)).trans (goal_eq_f ⟨r, hlt⟩).symm)
    · simp [hlt]
  have hsup0 : ∀ v ∈ roots_63, Avail true mask256 roots_63 v := fun v hv => Or.inr (Or.inl ⟨v, hv, rfl⟩)
  obtain ⟨p, bank, hp, hr, hsup⟩ := execN_reach true gates roots_63 hfan (fun h => Bool.noConfusion h) 0 roots_63 roots_63 rfl hsup0
  have hav_out : Avail true mask256 bank out := by
    by_cases hi : o < (execN gates roots_63).length
    · exact hsup _ (getD_mem hi)
    · rw [show out = 0 from List.getD_eq_default _ _ (by omega)]; exact Or.inl (Or.inl (by simp))
  have hd_sub : dom_63 &&& mask256 = dom_63 := by decide +kernel
  have hm256 : mask256 &&& mask256 = mask256 := by decide +kernel
  have hncG : ¬ IsConst dom_63 goal_63 := by
    have h0 : isConstB dom_63 goal_63 = false := by decide +kernel
    intro hc; rw [(isConstB_iff _ _).2 hc] at h0; contradiction
  have houtm : (out &&& mask256) &&& dom_63 = goal_63 &&& dom_63 := by
    rw [Nat.and_assoc, Nat.and_comm mask256 dom_63, hd_sub, hout]
  have hnc_m : ¬ IsConst dom_63 (out &&& mask256) := fun hc => hncG (by
    rcases hc with h0 | h1; exact Or.inl (houtm.symm.trans h0); exact Or.inr (houtm.symm.trans h1))
  have hnc_256 : ¬ IsConst mask256 out := fun hc => hnc_m (by
    rcases hc with h0 | h1
    · exact Or.inl (by rw [h0]; simp)
    · exact Or.inr (by rw [h1, Nat.and_comm, hd_sub]))
  have hout0 : out.testBit 0 = false := by
    have h0 := congrArg (fun v => v.testBit 0) hout
    have hd0 : dom_63.testBit 0 = true := by decide +kernel
    have hg0 : goal_63.testBit 0 = false := by decide +kernel
    simp only [Nat.testBit_and, hd0, hg0, Bool.and_true, Bool.false_and] at h0
    exact h0
  obtain ⟨s, ws, hs, _, hws, hrun⟩ := reach_to_run hm256 (by decide +kernel) hout0 (by decide +kernel) hnc_256 hr hav_out
  have hws_sub : ∀ w ∈ ws, Avail true dom_63 roots_63 w := fun w hw => by
    obtain ⟨u, hu, rfl⟩ := List.mem_map.1 (hws w hw)
    exact Or.inr (Or.inl ⟨u, hu, by rw [Nat.and_assoc, Nat.and_comm mask256 dom_63, hd_sub]⟩)
  obtain ⟨q, next, hq, hav_q, hqp⟩ := contraction hd_sub hd_sub hnc_m hrun (show NatReach true dom_63 roots_63 0 roots_63 from rfl) hws_sub
  have hL := lowS_63 q next hq (avail_of_eq houtm hav_q)
  have hlt := countP_not_lt hg hgn
  omega

def witGates : List PEqualNP.CircuitLowerBounds.Gate := [{ op := GateOp.or, inputs := [2, 3] }, { op := GateOp.or, inputs := [4, 6] }, { op := GateOp.or, inputs := [3, 5] }, { op := GateOp.or, inputs := [0, 1] }, { op := GateOp.or, inputs := [1, 7] }, { op := GateOp.and, inputs := [2, 8] }, { op := GateOp.or, inputs := [0, 11] }, { op := GateOp.and, inputs := [4, 6] }, { op := GateOp.or, inputs := [12, 13] }, { op := GateOp.and, inputs := [9, 14] }, { op := GateOp.and, inputs := [10, 15] }]

theorem wit_mono : PEqualNP.MetaComplexity.Monotone2 ⟨witGates, 16⟩ := by
  simp [PEqualNP.MetaComplexity.Monotone2, witGates]

theorem wit_eval : ∀ x : Fin 6 → Bool, PEqualNP.CircuitLowerBounds.Circuit.eval ⟨witGates, 16⟩ (List.ofFn x) = (fun x : Fin 6 → Bool => Nat.testBit (4008372968 * 2 ^ 32 + 4008372904) (∑ i : Fin 6, if x i then 2 ^ (i : ℕ) else 0)) x := by
  decide +kernel

theorem main : ∀ s : ℕ, PEqualNP.MetaComplexity.HasCircuitSize 6 (fun x : Fin 6 → Bool => Nat.testBit (4008372968 * 2 ^ 32 + 4008372904) (∑ i : Fin 6, if x i then 2 ^ (i : ℕ) else 0)) s → ∃ C : PEqualNP.CircuitLowerBounds.Circuit, PEqualNP.MetaComplexity.Monotone2 C ∧ C.size ≤ s ∧ ∀ x : Fin 6 → Bool, C.eval (List.ofFn x) = Nat.testBit (4008372968 * 2 ^ 32 + 4008372904) (∑ i : Fin 6, if x i then 2 ^ (i : ℕ) else 0) := by
  intro s ⟨⟨gates, o⟩, hfan, hsz, hev⟩
  by_cases hhas : ∃ g ∈ gates, isNotGate g = true
  · have hlb : 11 ≤ gates.length := lb_with_not gates o hfan hev hhas
    refine ⟨⟨witGates, 16⟩, wit_mono, ?_, wit_eval⟩
    have hlen : witGates.length = 11 := rfl
    change witGates.length ≤ s
    change gates.length ≤ s at hsz
    omega
  · push_neg at hhas
    refine ⟨⟨gates, o⟩, ?_, hsz, hev⟩
    intro g hg
    obtain ⟨h1, h2⟩ := hfan g hg
    refine ⟨?_, h2⟩
    change g.op = GateOp.and ∨ g.op = GateOp.or ∨ g.op = GateOp.not at h1
    rcases h1 with h1 | h1 | h1
    · exact Or.inl h1
    · exact Or.inr h1
    · exfalso; have := hhas g hg; simp [isNotGate, h1] at this

end PEqualNP.Outside.L_meta_16507_aux

theorem PEqualNP.Outside.L_meta_16507 : ∀ s : ℕ, PEqualNP.MetaComplexity.HasCircuitSize 6 (fun x : Fin 6 → Bool => Nat.testBit (4008372968 * 2 ^ 32 + 4008372904) (∑ i : Fin 6, if x i then 2 ^ (i : ℕ) else 0)) s → ∃ C : PEqualNP.CircuitLowerBounds.Circuit, PEqualNP.MetaComplexity.Monotone2 C ∧ C.size ≤ s ∧ ∀ x : Fin 6 → Bool, C.eval (List.ofFn x) = Nat.testBit (4008372968 * 2 ^ 32 + 4008372904) (∑ i : Fin 6, if x i then 2 ^ (i : ℕ) else 0) := PEqualNP.Outside.L_meta_16507_aux.main

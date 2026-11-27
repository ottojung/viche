import Mathlib
import PEqualNP.Defs

namespace PEqualNP.Outside.L_meta_27460

open PEqualNP.CircuitLowerBounds PEqualNP.MetaComplexity

section Prog
variable {ι κ : Type}

def K (S : (ι → Bool) → Prop) (w : ι → Bool) : Prop :=
  (∃ c : Bool, w = fun _ => c) ∨ S w ∨ S (fun x => !w x)

def ins (z : ι → Bool) (S : (ι → Bool) → Prop) : (ι → Bool) → Prop := fun w => w = z ∨ S w

def Run : ℕ → ((ι → Bool) → Prop) → (ι → Bool) → Prop
  | 0, S, f => K S f
  | t + 1, S, f => Run t S f ∨
      ∃ a b : ι → Bool, K S a ∧ K S b ∧ Run t (ins (fun x => a x && b x) S) f

theorem K_not {S : (ι → Bool) → Prop} {w : ι → Bool} (h : K S w) : K S (fun x => !w x) := by
  rcases h with ⟨c, rfl⟩ | h | h
  · exact Or.inl ⟨!c, rfl⟩
  · exact Or.inr (Or.inr (by simpa using h))
  · exact Or.inr (Or.inl h)

theorem K_ins {S : (ι → Bool) → Prop} {z w : ι → Bool} (h : K S w) : K (ins z S) w := by
  rcases h with h | h | h
  · exact Or.inl h
  · exact Or.inr (Or.inl (Or.inr h))
  · exact Or.inr (Or.inr (Or.inr h))

theorem K_new {S : (ι → Bool) → Prop} (z : ι → Bool) : K (ins z S) z := Or.inr (Or.inl (Or.inl rfl))

theorem K_and {S : (ι → Bool) → Prop} {a b : ι → Bool} (ha : ∃ c, ∀ y, a y = c) (hb : K S b) :
    K S (fun y => a y && b y) := by
  obtain ⟨c, hc⟩ := ha
  cases c
  · exact Or.inl ⟨false, funext fun y => by simp [hc y]⟩
  · have : (fun y => a y && b y) = b := funext fun y => by simp [hc y]
    rw [this]; exact hb

theorem K_bind {S : (ι → Bool) → Prop} {S' : (κ → Bool) → Prop} (σ : κ → ι)
    (h : ∀ w, S w → K S' (fun y => w (σ y))) {w : ι → Bool} (hw : K S w) :
    K S' (fun y => w (σ y)) := by
  rcases hw with ⟨c, rfl⟩ | hw | hw
  · exact Or.inl ⟨c, rfl⟩
  · exact h w hw
  · have h2 := K_not (h _ hw)
    simpa using h2

theorem Run_map (σ : κ → ι) : ∀ (t : ℕ) (S : (ι → Bool) → Prop) (S' : (κ → Bool) → Prop)
    (f : ι → Bool), (∀ w, S w → K S' (fun y => w (σ y))) → Run t S f → Run t S' (fun y => f (σ y))
  | 0, _, _, _, h, hf => K_bind σ h hf
  | t + 1, S, S', f, h, hf => by
    rcases hf with hf | ⟨a, b, ha, hb, hf⟩
    · exact Or.inl (Run_map σ t S S' f h hf)
    · refine Or.inr ⟨_, _, K_bind σ h ha, K_bind σ h hb, Run_map σ t _ _ f ?_ hf⟩
      rintro w (rfl | hw)
      · exact K_new _
      · exact K_ins (h w hw)

theorem Run_le {t t' : ℕ} {S : (ι → Bool) → Prop} {f : ι → Bool} (h : t ≤ t') (hf : Run t S f) :
    Run t' S f := by
  induction h with
  | refl => exact hf
  | step _ ih => exact Or.inl ih

def Cl (σ : κ → ι) (p q r : ι) (S : (ι → Bool) → Prop) : Prop :=
  ∀ w, S w → w p ≠ w q → ∀ y, w (σ y) = w r

theorem Cl_K {σ : κ → ι} {p q r : ι} {S : (ι → Bool) → Prop} (h : Cl σ p q r S) {w : ι → Bool}
    (hw : K S w) (hd : w p ≠ w q) (y : κ) : w (σ y) = w r := by
  rcases hw with ⟨c, rfl⟩ | hw | hw
  · exact absurd rfl hd
  · exact h w hw hd y
  · have h2 := h _ hw (by simpa using hd) y
    simpa using h2

theorem and_dep {a b : ι → Bool} {p q : ι} (h : (a p && b p) ≠ (a q && b q)) :
    a p ≠ a q ∨ b p ≠ b q := by
  by_contra hc
  simp only [not_or, not_not] at hc
  exact h (by rw [hc.1, hc.2])

theorem kill1 (σ : κ → ι) (p q r : ι) : ∀ (t : ℕ) (S : (ι → Bool) → Prop) (S' : (κ → Bool) → Prop)
    (f : ι → Bool), Cl σ p q r S → (∀ w, S w → K S' (fun y => w (σ y))) → f p ≠ f q →
    (∃ y y', f (σ y) ≠ f (σ y')) → Run t S f → ∃ t', t' + 1 ≤ t ∧ Run t' S' (fun y => f (σ y))
  | 0, _, _, f, hc, _, hd, ⟨y, y', hn⟩, hf =>
    absurd ((Cl_K hc hf hd y).trans (Cl_K hc hf hd y').symm) hn
  | t + 1, S, S', f, hc, hm, hd, hn, hf => by
    rcases hf with hf | ⟨a, b, ha, hb, hf⟩
    · obtain ⟨t', ht, hr⟩ := kill1 σ p q r t S S' f hc hm hd hn hf
      exact ⟨t', by omega, hr⟩
    · by_cases hz : (a p && b p) ≠ (a q && b q)
      · have hk : K S' (fun y => a (σ y) && b (σ y)) := by
          rcases and_dep hz with h | h
          · exact K_and ⟨a r, Cl_K hc ha h⟩ (K_bind σ hm hb)
          · have e : (fun y => a (σ y) && b (σ y)) = fun y => b (σ y) && a (σ y) :=
              funext fun y => Bool.and_comm _ _
            rw [e]
            exact K_and ⟨b r, Cl_K hc hb h⟩ (K_bind σ hm ha)
        refine ⟨t, le_rfl, Run_map σ t _ S' f ?_ hf⟩
        rintro w (rfl | hw)
        · exact hk
        · exact hm w hw
      · obtain ⟨t', ht, hr⟩ := kill1 σ p q r t (ins (fun x => a x && b x) S)
          (ins (fun y => a (σ y) && b (σ y)) S') f
          (by
            rintro w (rfl | hw) hd2
            · exact absurd hd2 hz
            · exact hc w hw hd2)
          (by
            rintro w (rfl | hw)
            · exact K_new _
            · exact K_ins (hm w hw)) hd hn hf
        exact ⟨t' + 1, by omega, Or.inr ⟨_, _, K_bind σ hm ha, K_bind σ hm hb, hr⟩⟩

theorem kill2_dep (σ0 σ1 : κ → ι) (p q : ι) {t : ℕ} {S : (ι → Bool) → Prop}
    {S0 S1 : (κ → Bool) → Prop} {f a b : ι → Bool} (hc0 : Cl σ0 p q p S) (hc1 : Cl σ1 p q q S)
    (hm0 : ∀ w, S w → K S0 (fun y => w (σ0 y))) (hm1 : ∀ w, S w → K S1 (fun y => w (σ1 y)))
    (hd : f p ≠ f q) (hn0 : ∃ y y', f (σ0 y) ≠ f (σ0 y')) (hn1 : ∃ y y', f (σ1 y) ≠ f (σ1 y'))
    (ha : K S a) (hb : K S b) (hda : a p ≠ a q) (hf : Run t (ins (fun x => a x && b x) S) f) :
    ∃ t0 t1, Run t0 S0 (fun y => f (σ0 y)) ∧ Run t1 S1 (fun y => f (σ1 y)) ∧
      ((t0 + 2 ≤ t + 1 ∧ t1 + 1 ≤ t + 1) ∨ (t0 + 1 ≤ t + 1 ∧ t1 + 2 ≤ t + 1)) := by
  have k0 := Cl_K hc0 ha hda
  have k1 := Cl_K hc1 ha hda
  have hz0 : ∀ w, ins (fun x => a x && b x) S w → K S0 (fun y => w (σ0 y)) := by
    rintro w (rfl | hw)
    · exact K_and ⟨_, k0⟩ (K_bind σ0 hm0 hb)
    · exact hm0 w hw
  have hz1 : ∀ w, ins (fun x => a x && b x) S w → K S1 (fun y => w (σ1 y)) := by
    rintro w (rfl | hw)
    · exact K_and ⟨_, k1⟩ (K_bind σ1 hm1 hb)
    · exact hm1 w hw
  cases hap : a p
  · obtain ⟨t', ht, hr⟩ := kill1 σ0 p q p t _ S0 f (by
        rintro w (rfl | hw) hd2
        · intro y; simp [k0 y, hap]
        · exact hc0 w hw hd2) hz0 hd hn0 hf
    exact ⟨t', t, hr, Run_map σ1 t _ S1 f hz1 hf, Or.inl ⟨by omega, le_rfl⟩⟩
  · have haq : a q = false := by
      cases h : a q
      · rfl
      · exact absurd (hap.trans h.symm) hda
    obtain ⟨t', ht, hr⟩ := kill1 σ1 p q q t _ S1 f (by
        rintro w (rfl | hw) hd2
        · intro y; simp [k1 y, haq]
        · exact hc1 w hw hd2) hz1 hd hn1 hf
    exact ⟨t, t', Run_map σ0 t _ S0 f hz0 hf, hr, Or.inr ⟨le_rfl, by omega⟩⟩

theorem kill2 (σ0 σ1 : κ → ι) (p q : ι) : ∀ (t : ℕ) (S : (ι → Bool) → Prop)
    (S0 S1 : (κ → Bool) → Prop) (f : ι → Bool), Cl σ0 p q p S → Cl σ1 p q q S →
    (∀ w, S w → K S0 (fun y => w (σ0 y))) → (∀ w, S w → K S1 (fun y => w (σ1 y))) → f p ≠ f q →
    (∃ y y', f (σ0 y) ≠ f (σ0 y')) → (∃ y y', f (σ1 y) ≠ f (σ1 y')) → Run t S f →
    ∃ t0 t1, Run t0 S0 (fun y => f (σ0 y)) ∧ Run t1 S1 (fun y => f (σ1 y)) ∧
      ((t0 + 2 ≤ t ∧ t1 + 1 ≤ t) ∨ (t0 + 1 ≤ t ∧ t1 + 2 ≤ t))
  | 0, _, _, _, f, hc, _, _, _, hd, ⟨y, y', hn⟩, _, hf =>
    absurd ((Cl_K hc hf hd y).trans (Cl_K hc hf hd y').symm) hn
  | t + 1, S, S0, S1, f, hc0, hc1, hm0, hm1, hd, hn0, hn1, hf => by
    rcases hf with hf | ⟨a, b, ha, hb, hf⟩
    · obtain ⟨t0, t1, r0, r1, h⟩ := kill2 σ0 σ1 p q t S S0 S1 f hc0 hc1 hm0 hm1 hd hn0 hn1 hf
      exact ⟨t0, t1, r0, r1, by omega⟩
    · by_cases hz : (a p && b p) ≠ (a q && b q)
      · rcases and_dep hz with h | h
        · exact kill2_dep σ0 σ1 p q hc0 hc1 hm0 hm1 hd hn0 hn1 ha hb h hf
        · have e : (fun x => a x && b x) = fun x => b x && a x :=
            funext fun x => Bool.and_comm _ _
          rw [e] at hf
          exact kill2_dep σ0 σ1 p q hc0 hc1 hm0 hm1 hd hn0 hn1 hb ha h hf
      · obtain ⟨t0, t1, r0, r1, h⟩ := kill2 σ0 σ1 p q t (ins (fun x => a x && b x) S)
          (ins (fun y => a (σ0 y) && b (σ0 y)) S0) (ins (fun y => a (σ1 y) && b (σ1 y)) S1) f
          (by
            rintro w (rfl | hw) hd2
            · exact absurd hd2 hz
            · exact hc0 w hw hd2)
          (by
            rintro w (rfl | hw) hd2
            · exact absurd hd2 hz
            · exact hc1 w hw hd2)
          (by
            rintro w (rfl | hw)
            · exact K_new _
            · exact K_ins (hm0 w hw))
          (by
            rintro w (rfl | hw)
            · exact K_new _
            · exact K_ins (hm1 w hw)) hd hn0 hn1 hf
        exact ⟨t0 + 1, t1 + 1, Or.inr ⟨_, _, K_bind σ0 hm0 ha, K_bind σ0 hm0 hb, r0⟩,
          Or.inr ⟨_, _, K_bind σ1 hm1 ha, K_bind σ1 hm1 hb, r1⟩, by omega⟩

end Prog

section Rules
variable {n : ℕ}

abbrev BF (n : ℕ) := (Fin n → Bool) → Bool

def Vars (n : ℕ) : BF n → Prop := fun w => ∃ i : Fin n, w = fun x => x i

def LB (f : BF n) (b : ℕ) : Prop := ∀ t, Run t (Vars n) f → b ≤ t

def pt (n : ℕ) (c : ℕ) : Fin n → Bool := fun i => c.testBit i.val

def rs (f : BF n) (i : Fin n) (c : Bool) : BF n := fun x => f (Function.update x i c)

theorem vars_rs (i : Fin n) (c : Bool) (w : BF n) (hw : Vars n w) :
    K (Vars n) (fun x => w (Function.update x i c)) := by
  obtain ⟨j, rfl⟩ := hw
  by_cases h : j = i
  · subst h; exact Or.inl ⟨c, by simp⟩
  · exact Or.inr (Or.inl ⟨j, by simp [Function.update_of_ne h]⟩)

theorem vars_cl (i : Fin n) (c : Bool) (x : Fin n → Bool) :
    Cl (fun y => Function.update y i c) (Function.update x i false) (Function.update x i true)
      (Function.update x i c) (Vars n) := by
  rintro w ⟨j, rfl⟩ hd y
  by_cases h : j = i
  · subst h; simp
  · exact absurd (by simp [Function.update_of_ne h]) hd

theorem rule1 (f : BF n) (i : Fin n) (c : Bool) (b p y y' : ℕ)
    (hd : f (Function.update (pt n p) i false) ≠ f (Function.update (pt n p) i true))
    (hn : rs f i c (pt n y) ≠ rs f i c (pt n y')) (h : LB (rs f i c) b) : LB f (b + 1) := by
  intro t ht
  obtain ⟨t', h1, h2⟩ := kill1 _ _ _ _ t _ (Vars n) f (vars_cl i c (pt n p)) (vars_rs i c) hd
    ⟨_, _, hn⟩ ht
  have := h t' h2
  omega

theorem rule2 (f : BF n) (i : Fin n) (b p y y' u u' : ℕ)
    (hd : f (Function.update (pt n p) i false) ≠ f (Function.update (pt n p) i true))
    (hn0 : rs f i false (pt n y) ≠ rs f i false (pt n y'))
    (hn1 : rs f i true (pt n u) ≠ rs f i true (pt n u'))
    (h0 : LB (rs f i false) b) (h1 : LB (rs f i true) b) : LB f (b + 2) := by
  intro t ht
  obtain ⟨t0, t1, r0, r1, h⟩ := kill2 _ _ _ _ t _ (Vars n) (Vars n) f (vars_cl i false (pt n p))
    (vars_cl i true (pt n p)) (vars_rs i false) (vars_rs i true) hd ⟨_, _, hn0⟩ ⟨_, _, hn1⟩ ht
  have g0 := h0 t0 r0
  have g1 := h1 t1 r1
  omega

theorem LB_mono {f : BF n} {b b' : ℕ} (h : LB f b) (hb : b' ≤ b) : LB f b' :=
  fun t ht => hb.trans (h t ht)

theorem LB_perm (π : Fin n → Fin n) (f g : BF n) (hg : ∀ x, g x = f (fun i => x (π i))) {b : ℕ}
    (h : LB g b) : LB f b := by
  intro t ht
  apply h t
  have e : g = fun x => f (fun i => x (π i)) := funext hg
  rw [e]
  refine Run_map (fun (x : Fin n → Bool) (i : Fin n) => x (π i)) t _ _ f ?_ ht
  rintro w ⟨j, rfl⟩
  exact Or.inr (Or.inl ⟨π j, rfl⟩)

end Rules

section First
variable {n : ℕ}

def lit (i : Fin n) (s : Bool) : BF n := fun x => Bool.xor (x i) (!s)

theorem lit_K (i : Fin n) (s : Bool) : K (Vars n) (lit i s) := by
  cases s
  · refine Or.inr (Or.inr ⟨i, ?_⟩)
    funext x; simp [lit]
  · refine Or.inr (Or.inl ⟨i, ?_⟩)
    funext x; simp [lit]

def VE (E : Fin n → Bool) : BF n → Prop := fun w => ∃ i : Fin n, E i = true ∧ w = fun x => x i

theorem VE_sub {E : Fin n → Bool} {w : BF n} (h : VE E w) : Vars n w := by
  obtain ⟨i, _, h⟩ := h
  exact ⟨i, h⟩

theorem lit_KE {E : Fin n → Bool} {i : Fin n} (hi : E i = true) (s : Bool) : K (VE E) (lit i s) := by
  cases s
  · refine Or.inr (Or.inr ⟨i, hi, ?_⟩)
    funext x; simp [lit]
  · refine Or.inr (Or.inl ⟨i, hi, ?_⟩)
    funext x; simp [lit]

theorem K_lit {E : Fin n → Bool} {w : BF n} (h : K (VE E) w) :
    (∃ c, ∀ y, w y = c) ∨ ∃ i s, E i = true ∧ w = lit i s := by
  rcases h with ⟨c, rfl⟩ | ⟨i, hi, rfl⟩ | ⟨i, hi, h⟩
  · exact Or.inl ⟨c, fun _ => rfl⟩
  · exact Or.inr ⟨i, true, hi, by funext x; simp [lit]⟩
  · refine Or.inr ⟨i, false, hi, ?_⟩
    funext x
    have := congrFun h x
    simp only [lit]
    rw [← this]
    cases w x <;> rfl

def dep (f : BF n) (i j : Fin n) (c : Bool) : Prop := ∃ p : Fin n → Bool,
  f (Function.update (Function.update p j c) i false) ≠ f (Function.update (Function.update p j c) i true)

def nc (f : BF n) : Prop := ∃ y y', f y ≠ f y'

def OptI (f : BF n) (b : ℕ) (i j : Fin n) (s u : Bool) : Prop := dep f i j (!u) ∧
  ((nc (rs f i (!s)) ∧ ∃ b', b ≤ b' + 3 ∧ LB (rs f i (!s)) b') ∨
    (nc (rs f i s) ∧ ∃ b', b ≤ b' + 2 ∧ LB (rs f i s) b'))

theorem first_gate {ι : Type} : ∀ (t : ℕ) (S : (ι → Bool) → Prop) (f : ι → Bool), Run t S f → K S f ∨
    ∃ (t' : ℕ) (a b : ι → Bool), t' + 1 ≤ t ∧ K S a ∧ K S b ∧ ¬ K S (fun x => a x && b x) ∧
      Run t' (ins (fun x => a x && b x) S) f
  | 0, _, _, h => Or.inl h
  | t + 1, S, f, h => by
    rcases h with h | ⟨a, b, ha, hb, h⟩
    · rcases first_gate t S f h with h | ⟨t', a, b, ht, ha, hb, hn, hr⟩
      · exact Or.inl h
      · exact Or.inr ⟨t', a, b, by omega, ha, hb, hn, hr⟩
    · by_cases hk : K S (fun x => a x && b x)
      · have h2 : Run t S f := Run_map (fun x => x) t _ S f (by
          rintro w (rfl | hw)
          · exact hk
          · exact Or.inr (Or.inl hw)) h
        rcases first_gate t S f h2 with h | ⟨t', a, b, ht, ha, hb, hn, hr⟩
        · exact Or.inl h
        · exact Or.inr ⟨t', a, b, by omega, ha, hb, hn, hr⟩
      · exact Or.inr ⟨t, a, b, le_rfl, ha, hb, hk, h⟩

theorem lift_run {ι κ : Type} (τ : ι → κ) : ∀ (t : ℕ) (S : (ι → Bool) → Prop) (S' : (κ → Bool) → Prop)
    (f : ι → Bool), (∀ w, S w → ∃ W, K S' W ∧ ∀ x, W (τ x) = w x) → Run t S f →
    ∃ F, Run t S' F ∧ ∀ x, F (τ x) = f x
  | 0, S, S', f, h, hr => by
    rcases hr with ⟨c, rfl⟩ | hr | hr
    · exact ⟨fun _ => c, Or.inl ⟨c, rfl⟩, fun _ => rfl⟩
    · exact h f hr
    · obtain ⟨W, hW, e⟩ := h _ hr
      refine ⟨fun y => !W y, K_not hW, fun x => ?_⟩
      show (!W (τ x)) = _
      rw [e x]; simp
  | t + 1, S, S', f, h, hr => by
    have hK : ∀ w, K S w → ∃ W, K S' W ∧ ∀ x, W (τ x) = w x := by
      intro w hw
      rcases hw with ⟨c, rfl⟩ | hw | hw
      · exact ⟨fun _ => c, Or.inl ⟨c, rfl⟩, fun _ => rfl⟩
      · exact h w hw
      · obtain ⟨W, hW, e⟩ := h _ hw
        refine ⟨fun y => !W y, K_not hW, fun x => ?_⟩
        show (!W (τ x)) = _
        rw [e x]; simp
    rcases hr with hr | ⟨a, b, ha, hb, hr⟩
    · obtain ⟨F, hF, e⟩ := lift_run τ t S S' f h hr
      exact ⟨F, Or.inl hF, e⟩
    · obtain ⟨A, hA, ea⟩ := hK a ha
      obtain ⟨B, hB, eb⟩ := hK b hb
      obtain ⟨F, hF, e⟩ := lift_run τ t (ins (fun x => a x && b x) S) (ins (fun y => A y && B y) S') f (by
        rintro w (rfl | hw)
        · exact ⟨_, K_new _, fun x => by rw [ea, eb]⟩
        · obtain ⟨W, hW, ew⟩ := h w hw
          exact ⟨W, K_ins hW, ew⟩) hr
      exact ⟨F, Or.inr ⟨A, B, hA, hB, hF⟩, e⟩

def VP (n : ℕ) : ((Fin n → Bool) × Bool → Bool) → Prop :=
  fun W => (∃ k : Fin n, W = fun y => y.1 k) ∨ W = fun y => y.2

theorem opt_bound (f : BF n) (b : ℕ) (i j : Fin n) (hij : i ≠ j) (s u : Bool) (t : ℕ)
    (hr : Run t (ins (fun x => lit i s x && lit j u x) (Vars n)) f) (ho : OptI f b i j s u)
    (ih : Run t (Vars n) f → b ≤ t + 1) : b ≤ t + 1 := by
  obtain ⟨⟨p0, hdep⟩, hopt⟩ := ho
  set z : BF n := fun x => lit i s x && lit j u x with hz
  obtain ⟨F, hF, e⟩ := lift_run (fun x => (x, z x)) t _ (VP n) f (by
    rintro w (rfl | ⟨k, rfl⟩)
    · exact ⟨fun y => y.2, Or.inr (Or.inl (Or.inr rfl)), fun x => rfl⟩
    · exact ⟨fun y => y.1 k, Or.inr (Or.inl (Or.inl ⟨k, rfl⟩)), fun x => rfl⟩) hr
  have zi : ∀ y, z (Function.update y i (!s)) = false := by
    intro y; cases s <;> simp [hz, lit]
  have zj : ∀ y c, z (Function.update (Function.update y j (!u)) i c) = false := by
    intro y c
    have : Function.update (Function.update y j (!u)) i c j = !u := by
      rw [Function.update_of_ne hij.symm, Function.update_self]
    simp only [hz, lit, this]
    cases u <;> simp
  have dF : ∀ c, F (Function.update (Function.update p0 j (!u)) i c, false) =
      f (Function.update (Function.update p0 j (!u)) i c) := by
    intro c
    have := e (Function.update (Function.update p0 j (!u)) i c)
    rw [zj p0 c] at this
    exact this
  rcases hopt with ⟨⟨y, y', hnc⟩, b', hb, hL⟩ | ⟨⟨y, y', hnc⟩, b', hb, hL⟩
  · have iF : ∀ y, F (Function.update y i (!s), false) = rs f i (!s) y := by
      intro y
      have := e (Function.update y i (!s))
      rw [zi y] at this
      exact this
    by_cases hd : ∃ x0, F (x0, false) ≠ F (x0, true)
    · obtain ⟨x0, hx0⟩ := hd
      obtain ⟨t1, h1, r1⟩ := kill1 (fun x : Fin n → Bool => (x, false)) (x0, false) (x0, true) (x0, false) t
        (VP n) (Vars n) F (by
          rintro W (⟨k, rfl⟩ | rfl) hW y
          · exact absurd rfl hW
          · rfl) (by
          rintro W (⟨k, rfl⟩ | rfl)
          · exact Or.inr (Or.inl ⟨k, rfl⟩)
          · exact Or.inl ⟨false, rfl⟩) hx0
        ⟨Function.update y i (!s), Function.update y' i (!s), by rw [iF, iF]; exact hnc⟩ hF
      obtain ⟨t2, h2, r2⟩ := kill1 _ _ _ _ t1 _ (Vars n) (fun x => F (x, false))
        (vars_cl i (!s) (Function.update p0 j (!u))) (vars_rs i (!s))
        (by simp only [dF]; exact hdep) ⟨y, y', by simp only [iF]; exact hnc⟩ r1
      have e3 : (fun y => F (Function.update y i (!s), false)) = rs f i (!s) := funext iF
      have := hL t2 (e3 ▸ r2)
      omega
    · have hc : ∀ x, F (x, z x) = F (x, false) := by
        intro x
        by_contra hx
        cases h : z x
        · rw [h] at hx; exact hx rfl
        · rw [h] at hx; exact hd ⟨x, fun h' => hx h'.symm⟩
      have e4 : (fun x : Fin n → Bool => F (x, false)) = f := funext fun x => (hc x).symm.trans (e x)
      apply ih
      rw [← e4]
      refine Run_map (fun x : Fin n → Bool => (x, false)) t (VP n) _ F ?_ hF
      rintro W (⟨k, rfl⟩ | rfl)
      · exact Or.inr (Or.inl ⟨k, rfl⟩)
      · exact Or.inl ⟨false, rfl⟩
  · have iF : ∀ y, F (Function.update y i s, lit j u y) = rs f i s y := by
      intro y
      have h1 := e (Function.update y i s)
      have h2 : z (Function.update y i s) = lit j u y := by
        simp only [hz, lit, Function.update_self, Function.update_of_ne hij.symm]
        cases s <;> simp
      rw [h2] at h1
      exact h1
    obtain ⟨t1, h1, r1⟩ := kill1 (fun y : Fin n → Bool => (Function.update y i s, lit j u y))
      (Function.update (Function.update p0 j (!u)) i false, false)
      (Function.update (Function.update p0 j (!u)) i true, false)
      (Function.update (Function.update p0 j (!u)) i s, false) t (VP n) (Vars n) F (by
        rintro W (⟨k, rfl⟩ | rfl) hW y
        · exact vars_cl i s (Function.update p0 j (!u)) _ ⟨k, rfl⟩ hW y
        · exact absurd rfl hW) (by
        rintro W (⟨k, rfl⟩ | rfl)
        · exact vars_rs i s _ ⟨k, rfl⟩
        · exact lit_K j u) (by rw [dF, dF]; exact hdep) ⟨y, y', by rw [iF, iF]; exact hnc⟩ hF
    have e3 : (fun y => F (Function.update y i s, lit j u y)) = rs f i s := funext iF
    have := hL t1 (e3 ▸ r1)
    omega

theorem rule3 (f : BF n) (b : ℕ) (E : Fin n → Bool) (hE : ∀ x, f (fun k => E k && x k) = f x)
    (h0 : ∃ i j : Fin n, i < j ∧ E i = true ∧ E j = true)
    (h : ∀ i j : Fin n, i < j → E i = true → E j = true → ∀ s u : Bool,
      OptI f b i j s u ∨ OptI f b j i u s) : LB f b := by
  intro t
  induction t using Nat.strong_induction_on with
  | _ t ih =>
    intro hr
    have hb : ∀ t', t' + 1 ≤ t → Run t' (Vars n) f → b ≤ t' + 1 := fun t' h1 h3 => by
      have := ih t' (by omega) h3
      omega
    have hr2 : Run t (VE E) f := by
      have := Run_map (fun (x : Fin n → Bool) (k : Fin n) => E k && x k) t (Vars n) (VE E) f (by
        rintro w ⟨k, rfl⟩
        cases hk : E k
        · exact Or.inl ⟨false, funext fun x => by simp [hk]⟩
        · exact Or.inr (Or.inl ⟨k, hk, funext fun x => by simp [hk]⟩)) hr
      have e : (fun x : Fin n → Bool => f (fun k => E k && x k)) = f := funext hE
      rw [e] at this
      exact this
    rcases first_gate t _ f hr2 with hkE | ⟨t', a, c, ht, ha, hc, hn, hrE⟩
    · exfalso
      have hk : K (Vars n) f := by
        rcases hkE with h | h | h
        · exact Or.inl h
        · exact Or.inr (Or.inl (VE_sub h))
        · exact Or.inr (Or.inr (VE_sub h))
      have key : ∀ i j s u, ¬ OptI f b i j s u := by
        rintro i j s u ⟨⟨p, hd⟩, ⟨⟨y, y', hy⟩, _⟩ | ⟨⟨y, y', hy⟩, _⟩⟩
        · exact hy ((Cl_K (vars_cl i (!s) _) hk hd y).trans (Cl_K (vars_cl i (!s) _) hk hd y').symm)
        · exact hy ((Cl_K (vars_cl i s _) hk hd y).trans (Cl_K (vars_cl i s _) hk hd y').symm)
      obtain ⟨i0, j0, hlt, hi0, hj0⟩ := h0
      rcases h i0 j0 hlt hi0 hj0 true true with ho | ho
      · exact key _ _ _ _ ho
      · exact key _ _ _ _ ho
    · have comm : ∀ a c : BF n, (fun x => a x && c x) = fun x => c x && a x := fun a c =>
        funext fun x => Bool.and_comm _ _
      rcases K_lit ha with hca | ⟨i, s, hi, rfl⟩
      · exact absurd (K_and hca hc) hn
      have hr' : Run t' (ins (fun x => lit i s x && c x) (Vars n)) f := by
        refine Run_map (fun x => x) t' _ _ f ?_ hrE
        rintro w (rfl | hw)
        · exact K_new _
        · exact Or.inr (Or.inl (Or.inr (VE_sub hw)))
      rcases K_lit hc with hcc | ⟨j, u, hj, rfl⟩
      · exact absurd (comm _ _ ▸ K_and hcc ha) hn
      by_cases hij : i = j
      · subst hij
        exfalso
        apply hn
        by_cases hsu : s = u
        · subst hsu
          have : (fun x => lit i s x && lit i s x) = lit i s := funext fun x => Bool.and_self _
          rw [this]; exact lit_KE hi s
        · refine Or.inl ⟨false, funext fun x => ?_⟩
          cases s <;> cases u <;> cases hx : x i <;> simp_all [lit]
      have fin : ∀ i j s u, i ≠ j → Run t' (ins (fun x => lit i s x && lit j u x) (Vars n)) f →
          OptI f b i j s u ∨ OptI f b j i u s → b ≤ t' + 1 := by
        intro i j s u hij hr' ho
        rcases ho with ho | ho
        · exact opt_bound f b i j hij s u t' hr' ho (hb t' ht)
        · rw [comm] at hr'
          exact opt_bound f b j i (Ne.symm hij) u s t' hr' ho (hb t' ht)
      have : b ≤ t' + 1 := by
        rcases lt_or_gt_of_ne hij with hlt | hlt
        · exact fin i j s u hij hr' (h i j hlt hi hj s u)
        · exact fin i j s u hij hr' (h j i hlt hj hi u s).symm
      omega

def depB (f : BF n) (i j : Fin n) (c : Bool) : Bool := (List.range (2 ^ n)).any fun p =>
  Bool.xor (f (Function.update (Function.update (pt n p) j c) i false))
    (f (Function.update (Function.update (pt n p) j c) i true))

def ncB (f : BF n) : Bool := (List.range (2 ^ n)).any fun p => Bool.xor (f (pt n p)) (f (pt n 0))

def optB (f : BF n) (b : ℕ) (V : List (Fin n × Bool × ℕ)) (i j : Fin n) (s u : Bool) : Bool :=
  depB f i j (!u) && V.any fun e => decide (e.1 = i) && ((ncB (rs f i (!s)) && decide (e.2.1 = !s) && decide (b ≤ e.2.2 + 3)) ||
    (ncB (rs f i s) && decide (e.2.1 = s) && decide (b ≤ e.2.2 + 2)))

theorem xor_ne {p q : Bool} (h : Bool.xor p q = true) : p ≠ q := by
  cases p <;> cases q <;> simp_all

theorem optB_sound {f : BF n} {b : ℕ} {V : List (Fin n × Bool × ℕ)} (hV : ∀ e ∈ V, LB (rs f e.1 e.2.1) e.2.2)
    {i j : Fin n} {s u : Bool} (h : optB f b V i j s u = true) : OptI f b i j s u := by
  simp only [optB, Bool.and_eq_true, List.any_eq_true, depB, Bool.or_eq_true, decide_eq_true_eq] at h
  obtain ⟨⟨p, _, hp⟩, ⟨i', c, b'⟩, he, hi, ho⟩ := h
  simp only at hi ho
  subst hi
  have hL := hV _ he
  simp only at hL
  refine ⟨⟨_, xor_ne hp⟩, ?_⟩
  have hnc : ∀ g : BF n, ncB g = true → nc g := by
    intro g hg
    simp only [ncB, List.any_eq_true] at hg
    obtain ⟨q, _, hq⟩ := hg
    exact ⟨_, _, xor_ne hq⟩
  rcases ho with ⟨⟨h1, h2⟩, h3⟩ | ⟨⟨h1, h2⟩, h3⟩
  · left
    exact ⟨hnc _ h1, b', h3, h2 ▸ hL⟩
  · right
    exact ⟨hnc _ h1, b', h3, h2 ▸ hL⟩

theorem rule3B (f : BF n) (b : ℕ) (E : Fin n → Bool) (hE : ∀ x, f (fun k => E k && x k) = f x)
    (h0 : ∃ i j : Fin n, i < j ∧ E i = true ∧ E j = true) (V : List (Fin n × Bool × ℕ))
    (hV : ∀ e ∈ V, LB (rs f e.1 e.2.1) e.2.2)
    (h : (List.finRange n).all (fun i => (List.finRange n).all fun j => !(decide (i < j) && E i && E j) ||
      [true, false].all fun s => [true, false].all fun u => optB f b V i j s u || optB f b V j i u s) = true) :
    LB f b := by
  refine rule3 f b E hE h0 fun i j hij hi hj s u => ?_
  have h1 := List.all_eq_true.mp (List.all_eq_true.mp h i (List.mem_finRange i)) j (List.mem_finRange j)
  have h3 : (decide (i < j) && E i && E j) = true := by rw [decide_eq_true hij, hi, hj]; rfl
  rw [h3] at h1
  simp only [Bool.not_true, Bool.false_or] at h1
  have h4 := List.all_eq_true.mp (List.all_eq_true.mp h1 s (by cases s <;> simp)) u (by cases u <;> simp)
  rcases (Bool.or_eq_true _ _).mp h4 with h5 | h5
  · exact Or.inl (optB_sound hV h5)
  · exact Or.inr (optB_sound hV h5)

end First

def isBinary (g : Gate) : Bool := match g.op with
  | .not => false
  | _ => true

def bc (gs : List Gate) : ℕ := (gs.filter isBinary).length

def legal (g : Gate) : Prop := (g.op = .and ∨ g.op = .or ∨ g.op = .not) ∧ g.inputs.length ≤ 2

def step (w : List Bool) (g : Gate) : List Bool :=
  w ++ [g.op.eval (g.inputs.map fun i => w.getD i false)]

section Compile
variable {n : ℕ}

def rd (ws : List (BF n)) (i : ℕ) : BF n := fun x => (ws.map fun w => w x).getD i false

theorem rd_K {S : BF n → Prop} {ws : List (BF n)} (hw : ∀ w ∈ ws, K S w) (i : ℕ) :
    K S (rd ws i) := by
  by_cases h : i < ws.length
  · have : rd ws i = ws[i] := by
      funext x
      simp [rd, List.getD_eq_getElem?_getD, List.getElem?_eq_getElem h]
    rw [this]
    exact hw _ (List.getElem_mem h)
  · refine Or.inl ⟨false, ?_⟩
    funext x
    simp [rd, List.getD_eq_getElem?_getD, List.getElem?_eq_none (Nat.le_of_not_gt h)]

theorem gate_run {S : BF n → Prop} {ws : List (BF n)} (hw : ∀ w ∈ ws, K S w) (g : Gate)
    (hg : legal g) (z : BF n)
    (hz : z = fun x => g.op.eval (g.inputs.map fun i => rd ws i x)) :
    K S z ∨ (isBinary g = true ∧ ∃ a b : BF n, K S a ∧ K S b ∧ K (ins (fun x => a x && b x) S) z) := by
  obtain ⟨op, args⟩ := g
  obtain ⟨hop, cap⟩ := hg
  change op = .and ∨ op = .or ∨ op = .not at hop
  change args.length ≤ 2 at cap
  subst hz
  rcases args with _ | ⟨i, _ | ⟨j, _ | ⟨u, tail⟩⟩⟩
  · left
    rcases hop with rfl | rfl | rfl
    · exact Or.inl ⟨true, rfl⟩
    · exact Or.inl ⟨false, rfl⟩
    · exact Or.inl ⟨true, rfl⟩
  · left
    rcases hop with rfl | rfl | rfl
    · have e : (fun x => GateOp.eval .and ([i].map fun i => rd ws i x)) = rd ws i :=
        funext fun x => by simp [GateOp.eval]
      simp only [e]; exact rd_K hw i
    · have e : (fun x => GateOp.eval .or ([i].map fun i => rd ws i x)) = rd ws i :=
        funext fun x => by simp [GateOp.eval]
      simp only [e]; exact rd_K hw i
    · exact K_not (rd_K hw i)
  · rcases hop with rfl | rfl | rfl
    · right
      refine ⟨rfl, rd ws i, rd ws j, rd_K hw i, rd_K hw j, ?_⟩
      have e : (fun x => GateOp.eval .and ([i, j].map fun i => rd ws i x)) =
          fun x => rd ws i x && rd ws j x := funext fun x => by simp [GateOp.eval]
      simp only [e]; exact K_new _
    · right
      refine ⟨rfl, _, _, K_not (rd_K hw i), K_not (rd_K hw j), ?_⟩
      have e : (fun x => GateOp.eval .or ([i, j].map fun i => rd ws i x)) =
          fun x => !(!rd ws i x && !rd ws j x) := funext fun x => by simp [GateOp.eval]
      simp only [e]; exact K_not (K_new _)
    · left
      exact K_not (rd_K hw i)
  · simp at cap

theorem compile (out : ℕ) : ∀ (gs : List Gate) (ws : List (BF n)) (S : BF n → Prop),
    (∀ g ∈ gs, legal g) → (∀ w ∈ ws, K S w) →
    Run (bc gs) S (fun x => (gs.foldl step (ws.map fun w => w x)).getD out false)
  | [], ws, S, _, hw => rd_K hw out
  | g :: gs, ws, S, hg, hw => by
    set z : BF n := fun x => g.op.eval (g.inputs.map fun i => rd ws i x) with hz
    have hst : ∀ x, step (ws.map fun w => w x) g = (ws ++ [z]).map fun w => w x := by
      intro x
      simp [step, hz, rd]
    have hfold : (fun x => ((g :: gs).foldl step (ws.map fun w => w x)).getD out false) =
        fun x => (gs.foldl step ((ws ++ [z]).map fun w => w x)).getD out false := by
      funext x
      rw [List.foldl_cons, hst x]
    rw [hfold]
    have tail := fun S' h => compile out gs (ws ++ [z]) S' (fun g' h' => hg g' (by simp [h'])) h
    have ext : ∀ S' : BF n → Prop, (∀ w ∈ ws, K S' w) → K S' z → ∀ w ∈ ws ++ [z], K S' w := by
      intro S' h1 h2 w hm
      rcases List.mem_append.mp hm with hm | hm
      · exact h1 w hm
      · exact (List.mem_singleton.mp hm) ▸ h2
    have hle : bc gs ≤ bc (g :: gs) := by
      unfold bc
      rw [List.filter_cons]
      split <;> simp
    rcases gate_run hw g (hg g (by simp)) z hz with h | ⟨hb, a, b, ha, hb2, h⟩
    · exact Run_le hle (tail S (ext S hw h))
    · have hbc : bc (g :: gs) = bc gs + 1 := by simp [bc, hb]
      rw [hbc]
      exact Or.inr ⟨a, b, ha, hb2, tail _ (ext _ (fun w hm => K_ins (hw w hm)) h)⟩

theorem bound_of_LB (F : BF n) (b : ℕ) (h : LB F b) (gs : List Gate) (o : ℕ)
    (hg : ∀ g ∈ gs, legal g)
    (he : ∀ x : Fin n → Bool, Circuit.eval ⟨gs, o⟩ (List.ofFn x) = F x) : b ≤ bc gs := by
  apply h
  have hr := compile o gs (List.ofFn fun i : Fin n => fun x : Fin n → Bool => x i) (Vars n) hg (by
    intro w hw
    obtain ⟨i, rfl⟩ := (List.mem_ofFn' _ _).mp hw
    exact Or.inr (Or.inl ⟨i, rfl⟩))
  have e : (fun x : Fin n → Bool => (gs.foldl step ((List.ofFn fun i : Fin n =>
      fun x : Fin n → Bool => x i).map fun w => w x)).getD o false) = F := by
    funext x
    rw [← he x, List.map_ofFn]
    rfl
  rw [e] at hr
  exact hr

end Compile

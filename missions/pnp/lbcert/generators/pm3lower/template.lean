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
section Live

variable {α : Type} [DecidableEq α]

def build (ops : α → α → Finset α) (goal : α) : ℕ → Finset α → Prop
  | 0, available => goal ∈ available
  | k + 1, available => build ops goal k available ∨
    ∃ a ∈ available, ∃ b ∈ available, a ≠ b ∧
      ∃ z ∈ ops a b, build ops goal k (insert z available)

def live (ops : α → α → Finset α) (goal : α) : ℕ → Finset α → Prop
  | 0, s => s = {goal}
  | k + 1, s => live ops goal k s ∨
    ∃ a ∈ s, ∃ b ∈ s, a ≠ b ∧ ∃ z ∈ ops a b, z ∉ s ∧
      ∃ rest : Finset α, s = insert a (insert b rest) ∧ live ops goal k (insert z rest)

theorem compress {ops : α → α → Finset α} {goal : α} {k : ℕ} {available : Finset α}
    (h : build ops goal k available) : ∃ s ⊆ available, live ops goal k s := by
  induction k generalizing available with
  | zero =>
    exact ⟨{goal}, Finset.singleton_subset_iff.mpr h, rfl⟩
  | succ k ih =>
    rcases h with skip | ⟨a, ha, b, hb, hab, z, hz, tail⟩
    · obtain ⟨s, hs, hrun⟩ := ih skip
      exact ⟨s, hs, Or.inl hrun⟩
    · obtain ⟨t, ht, hrun⟩ := ih tail
      by_cases sub : t ⊆ available
      · exact ⟨t, sub, Or.inl hrun⟩
      · have hzmem : z ∈ t := by
          by_contra hn
          apply sub
          intro u hu
          rcases Finset.mem_insert.mp (ht hu) with rfl | ok
          · exact False.elim (hn hu)
          · exact ok
        have hzout : z ∉ available := by
          intro hh
          exact sub ((Finset.insert_eq_of_mem hh) ▸ ht)
        let rest := t.erase z
        have hrest : rest ⊆ available := by
          intro u hu
          have hu' := Finset.mem_erase.mp hu
          exact (Finset.mem_insert.mp (ht hu'.2)).resolve_left hu'.1
        let s := insert a (insert b rest)
        have hs : s ⊆ available := Finset.insert_subset ha (Finset.insert_subset hb hrest)
        refine ⟨s, hs, Or.inr ⟨a, by simp [s], b, by simp [s], hab, z, hz,
          fun h => hzout (hs h), rest, rfl, ?_⟩⟩
        simpa [rest, Finset.insert_erase hzmem] using hrun

theorem live_card {ops : α → α → Finset α} {goal : α} {k : ℕ} {s : Finset α}
    (h : live ops goal k s) : s.card ≤ k + 1 := by
  induction k generalizing s with
  | zero => change s = {goal} at h; simp [h]
  | succ k ih =>
    rcases h with skip | ⟨a, ha, b, hb, hab, z, hz, hout, rest, rfl, tail⟩
    · exact (ih skip).trans (by omega)
    · have hzrest : z ∉ rest := fun hm => hout (by simp [hm])
      have htail := ih tail
      rw [Finset.card_insert_of_notMem hzrest] at htail
      have h₁ := Finset.card_insert_le a (insert b rest)
      have h₂ := Finset.card_insert_le b rest
      omega

theorem live_separates {ops : α → α → Finset α} {goal : α} (D : α → Prop)
    (hd : D goal) (hops : ∀ a b, ∀ z ∈ ops a b, D z → D a ∨ D b)
    {k : ℕ} {s : Finset α} (h : live ops goal k s) : ∃ w ∈ s, D w := by
  induction k generalizing s with
  | zero => change s = {goal} at h; exact ⟨goal, by simp [h], hd⟩
  | succ k ih =>
    rcases h with skip | ⟨a, ha, b, hb, hab, z, hz, hout, rest, rfl, tail⟩
    · exact ih skip
    · obtain ⟨w, hw, hD⟩ := ih tail
      rcases Finset.mem_insert.mp hw with rfl | hw
      · rcases hops a b w hz hD with h | h
        · exact ⟨a, ha, h⟩
        · exact ⟨b, hb, h⟩
      · exact ⟨w, by simp [hw], hD⟩

theorem first_live {ops : α → α → Finset α} {goal : α} {k : ℕ} {s : Finset α}
    (h : live ops goal (k + 1) s) :
    s = {goal} ∨
    ∃ a ∈ s, ∃ b ∈ s, a ≠ b ∧ ∃ z ∈ ops a b, z ∉ s ∧
      ∃ rest : Finset α, s = insert a (insert b rest) ∧ live ops goal k (insert z rest) := by
  induction k with
  | zero => exact h
  | succ k ih =>
    rcases h with skip | step
    · rcases ih skip with done | ⟨a, ha, b, hb, hab, z, hz, hn, r, hs, tail⟩
      · exact .inl done
      · exact .inr ⟨a, ha, b, hb, hab, z, hz, hn, r, hs, Or.inl tail⟩
    · exact .inr step

end Live

def ops (a b : ℕ) : List ℕ := [a &&& b, a ||| b, a ^^^ (a &&& b), b ^^^ (a &&& b)]

abbrev bops (a b : ℕ) : Finset ℕ := (ops a b).toFinset

def sep (P m x : ℕ) : ℕ := Nat.land (Nat.xor (Nat.shiftRight x P) x) m

def cuts (P m : ℕ) (ws : List ℕ) : ℕ := ws.foldr (fun w v => Nat.lor (sep P m w) v) 0

def differs (P i w : ℕ) : Prop := w.testBit (P + i) ≠ w.testBit i

theorem ops_differs (P i a b z : ℕ) (hz : z ∈ bops a b) (hd : differs P i z) :
    differs P i a ∨ differs P i b := by
  simp only [bops, ops, List.mem_toFinset, List.mem_cons, List.not_mem_nil, or_false] at hz
  by_contra! fail
  obtain ⟨ha, hb⟩ := fail
  apply hd
  unfold differs at ha hb
  simp only [not_not] at ha hb
  rcases hz with rfl | rfl | rfl | rfl <;>
    simp only [Nat.testBit_and, Nat.testBit_or, Nat.testBit_xor, ha, hb]

theorem mask_bit (P i : ℕ) : (2 ^ P - 1).testBit i = decide (i < P) := Nat.testBit_two_pow_sub_one P i

theorem cuts_spec (P : ℕ) (ws : List ℕ) (i : ℕ) :
    (cuts P (2 ^ P - 1) ws).testBit i = true ↔ i < P ∧ ∃ w ∈ ws, differs P i w := by
  induction ws with
  | nil => simp [cuts]
  | cons a rest ih =>
    change ((((a >>> P) ^^^ a) &&& (2 ^ P - 1)) ||| cuts P (2 ^ P - 1) rest).testBit i = true ↔ _
    rw [Nat.testBit_or, Bool.or_eq_true, ih]
    have bx (p q : Bool) : Bool.xor p q = true ↔ p ≠ q := by cases p <;> cases q <;> decide
    simp only [Nat.testBit_and, Nat.testBit_xor, Nat.testBit_shiftRight, mask_bit,
      Bool.and_eq_true, bx, decide_eq_true_eq, differs, List.mem_cons, exists_eq_or_imp]
    tauto

theorem cuts_full {P g : ℕ} (hg : ∀ i, i < P → differs P i g) {k : ℕ} {ws : List ℕ}
    (h : live bops g k ws.toFinset) : cuts P (2 ^ P - 1) ws = 2 ^ P - 1 := by
  apply Nat.eq_of_testBit_eq
  intro i
  rw [mask_bit]
  by_cases hi : i < P
  · have hw := live_separates (differs P i) (hg i hi) (ops_differs P i) h
    simpa [hi] using (cuts_spec P ws i).mpr ⟨hi, by simpa using hw⟩
  · cases hb : (cuts P (2 ^ P - 1) ws).testBit i
    · simp [hi]
    · exact absurd ((cuts_spec P ws i).mp hb).1 hi

theorem ops_swap (a b : ℕ) : bops a b = bops b a := by
  ext z
  simp only [bops, ops, List.mem_toFinset, List.mem_cons, List.not_mem_nil, or_false]
  rw [Nat.and_comm a b, Nat.or_comm a b]
  tauto

def singles {α : Type} : List α → List (α × List α)
  | [] => []
  | a :: rest => (a, rest) :: (singles rest).map (fun (b, bs) => (b, a :: bs))

def pairs {α : Type} : List α → List (α × α × List α)
  | [] => []
  | a :: rest => (singles rest).map (fun (b, bs) => (a, b, bs)) ++
      (pairs rest).map (fun (b, c, bs) => (b, c, a :: bs))

theorem pick_one {α : Type} {a : α} {ws : List α} (h : a ∈ ws) :
    ∃ rest, (a, rest) ∈ singles ws ∧ ws.Perm (a :: rest) := by
  induction ws with
  | nil => simp at h
  | cons x xs ih =>
    rcases List.mem_cons.mp h with e | h
    · subst x; exact ⟨xs, by simp [singles], .refl _⟩
    · obtain ⟨rest, hm, hp⟩ := ih h
      refine ⟨x :: rest, List.mem_cons_of_mem _ (List.mem_map.mpr ⟨(a, rest), hm, rfl⟩), ?_⟩
      exact (hp.cons x).trans (.swap _ _ _)

theorem pick_two {α : Type} {a b : α} {ws : List α} (ha : a ∈ ws) (hb : b ∈ ws) (hne : a ≠ b) :
    ∃ rest, ((a, b, rest) ∈ pairs ws ∨ (b, a, rest) ∈ pairs ws) ∧
      ws.Perm (a :: b :: rest) := by
  induction ws with
  | nil => simp at ha
  | cons x xs ih =>
    rcases List.mem_cons.mp ha with h | ha
    · subst x
      obtain ⟨r, hm, hp⟩ := pick_one ((List.mem_cons.mp hb).resolve_left (Ne.symm hne))
      exact ⟨r, .inl (List.mem_append_left _ (List.mem_map.mpr ⟨(b, r), hm, rfl⟩)), hp.cons a⟩
    · rcases List.mem_cons.mp hb with h | hb
      · subst x
        obtain ⟨r, hm, hp⟩ := pick_one (ws := xs) (a := a) (by assumption)
        exact ⟨r, .inr (List.mem_append_left _ (List.mem_map.mpr ⟨(a, r), hm, rfl⟩)),
          (hp.cons b).trans (.swap _ _ _)⟩
      · obtain ⟨r, hm, hp⟩ := ih ha hb
        refine ⟨x :: r, ?_,
          (hp.cons x).trans ((List.Perm.swap _ _ _).trans ((List.Perm.swap _ _ _).cons a))⟩
        rcases hm with hm | hm
        · exact .inl (List.mem_append_right _ (List.mem_map.mpr ⟨(a, b, r), hm, rfl⟩))
        · exact .inr (List.mem_append_right _ (List.mem_map.mpr ⟨(b, a, r), hm, rfl⟩))

def keepChoices (a b : ℕ) (r : List ℕ) : List (List ℕ) := [r, a :: r, b :: r, a :: b :: r]

theorem recover_kept {ws r : List ℕ} {a b : ℕ} {needed : Finset ℕ}
    (hp : ws.Perm (a :: b :: r)) (hn : ws.Nodup)
    (hs : ws.toFinset = insert a (insert b needed)) :
    ∃ kept ∈ keepChoices a b r, kept.Nodup ∧ kept.toFinset = needed := by
  have habr := hp.nodup_iff.mp hn
  have hbase : ws.toFinset = insert a (insert b r.toFinset) := by
    ext v
    simp [hp.mem_iff]
  have henne : ∀ v, v ∈ r ↔ v ∈ needed ∧ v ≠ a ∧ v ≠ b := by
    intro v
    have he : (v ∈ insert a (insert b r.toFinset)) ↔ v ∈ insert a (insert b needed) := by
      rw [← hbase, ← hs]
    simp only [Finset.mem_insert, List.mem_toFinset] at he
    simp only [List.nodup_cons, List.mem_cons, not_or] at habr
    grind
  by_cases ha : a ∈ needed <;> by_cases hb : b ∈ needed
  · refine ⟨a :: b :: r, by simp [keepChoices], habr, ?_⟩
    ext v; simp [henne]; grind
  · refine ⟨a :: r, by simp [keepChoices], ?_, ?_⟩
    · simp_all [List.nodup_cons]
    · ext v; simp [henne]; grind
  · refine ⟨b :: r, by simp [keepChoices], (List.nodup_cons.mp habr).2, ?_⟩
    ext v; simp [henne]; grind
  · refine ⟨r, by simp [keepChoices], (List.nodup_cons.mp (List.nodup_cons.mp habr).2).2, ?_⟩
    ext v; simp [henne]; grind

theorem singleton_list {goal : ℕ} {ws : List ℕ} (hn : ws.Nodup) (hs : ws.toFinset = {goal}) :
    ws = [goal] := by
  have hc := List.toFinset_card_of_nodup hn
  rw [hs] at hc
  cases ws with
  | nil => simp at hc
  | cons w ws =>
    cases ws with
    | nil => simpa using hs
    | cons => simp at hc

def fz {β : Type} (n : ℕ) (f : ℕ → β) : β := Nat.casesOn n (f 0) (fun k => f (Nat.succ k))

theorem fz_eq {β : Type} (n : ℕ) (f : ℕ → β) : fz n f = f n := by cases n <;> rfl

def fzl {β : Type} : List ℕ → (List ℕ → β) → β
  | [], f => f []
  | a :: t, f => fz a fun a' => fzl t fun t' => f (a' :: t')

theorem fzl_eq {β : Type} : ∀ (l : List ℕ) (f : List ℕ → β), fzl l f = f l
  | [], f => rfl
  | a :: t, f => by simp [fzl, fz_eq, fzl_eq t]

def gz (nx : List ℕ → Bool) (z : ℕ) (l : List ℕ) : Bool := fz z fun z => nx (z :: l)

def oA (a b : ℕ) : ℕ := Nat.land a b
def oO (a b : ℕ) : ℕ := Nat.lor a b
def oX (a b : ℕ) : ℕ := Nat.xor a (Nat.land a b)
def oY (a b : ℕ) : ℕ := Nat.xor b (Nat.land a b)
def kr (_ _ : ℕ) (r : List ℕ) : List ℕ := r
def ka (a _ : ℕ) (r : List ℕ) : List ℕ := a :: r
def kb (_ b : ℕ) (r : List ℕ) : List ℕ := b :: r
def kab (a b : ℕ) (r : List ℕ) : List ℕ := a :: b :: r

abbrev KF := ℕ → ℕ → List ℕ → List ℕ
abbrev Sc := ℕ → (List ℕ → Bool) → (ℕ → ℕ → ℕ) → KF → Bool

def lane (W G : ℕ) : ℕ :=
  (cond (Nat.blt G (Nat.pow W 10))
    (cond (Nat.blt G (Nat.pow W 5))
    (cond (Nat.blt G (Nat.pow W 2))
    (cond (Nat.blt G (Nat.pow W 1)) 0 1) (cond (Nat.blt G (Nat.pow W 3)) 2 (cond (Nat.blt G (Nat.pow W 4)) 3 4)))
    (cond (Nat.blt G (Nat.pow W 7))
    (cond (Nat.blt G (Nat.pow W 6)) 5 6) (cond (Nat.blt G (Nat.pow W 8)) 7 (cond (Nat.blt G (Nat.pow W 9)) 8 9))))
    (cond (Nat.blt G (Nat.pow W 15))
    (cond (Nat.blt G (Nat.pow W 12))
    (cond (Nat.blt G (Nat.pow W 11)) 10 11) (cond (Nat.blt G (Nat.pow W 13)) 12 (cond (Nat.blt G (Nat.pow W 14)) 13 14)))
    (cond (Nat.blt G (Nat.pow W 18))
    (cond (Nat.blt G (Nat.pow W 16)) 15 (cond (Nat.blt G (Nat.pow W 17)) 16 17))
    (cond (Nat.blt G (Nat.pow W 19)) 18 (cond (Nat.blt G (Nat.pow W 20)) 19 20)))))

def sel (L P W : ℕ) (ch : ℕ → Bool) (fuel : ℕ) : ℕ → Bool :=
  Nat.rec (fun _ => true) (fun _ ih G => Nat.casesOn G false (fun k =>
    fz (lane W (Nat.succ k)) fun p => or (ch p)
      (ih (Nat.xor (Nat.succ k) (Nat.pow 2 (Nat.add (Nat.mul L p) P)))))) fuel

theorem sel_true {L P W : ℕ} (hPL : P < L) {ch : ℕ → Bool} {p : ℕ} (hc : ch p = true) : ∀ (fuel G : ℕ),
    G.testBit (L * p + P) = true → sel L P W ch fuel G = true
  | 0, _, _ => rfl
  | fuel + 1, 0, hG => by simp at hG
  | fuel + 1, k + 1, hG => by
    change fz (lane W (k + 1)) (fun p => or (ch p) (sel L P W ch fuel ((k + 1) ^^^ 2 ^ (L * p + P)))) = true
    rw [fz_eq]
    generalize lane W (k + 1) = u
    by_cases h : u = p
    · rw [h, hc]; rfl
    · rw [sel_true hPL hc fuel _ (by
        have h3 : ¬ (L * u + P = L * p + P) := fun e => h (Nat.eq_of_mul_eq_mul_left (by omega) (by omega : L * u = L * p))
        rw [Nat.testBit_xor, hG, Nat.testBit_two_pow, decide_eq_false h3]
        rfl)]
      simp
def chg (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) (prs : List (ℕ × ℕ × List ℕ)) (p : ℕ) : Bool :=
  match prs[p]? with
  | none => false
  | some q => gz nx (o q.1 q.2.1) (kf q.1 q.2.1 q.2.2)

def sg (L P W : ℕ) (prs : List (ℕ × ℕ × List ℕ)) (G : ℕ) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ)
    (kf : KF) : Bool := sel L P W (chg nx o kf prs) 22 G

theorem sg_true {P L W G : ℕ} (hPL : P < L) {nx : List ℕ → Bool} {o : ℕ → ℕ → ℕ} {kf : KF}
    {q : ℕ × ℕ × List ℕ} (hn : nx (o q.1 q.2.1 :: kf q.1 q.2.1 q.2.2) = true)
    (prs : List (ℕ × ℕ × List ℕ)) (p : ℕ) (hq : prs[p]? = some q)
    (hG : G.testBit (L * p + P) = true) : sg L P W prs G nx o kf = true := by
  refine sel_true hPL (p := p) ?_ 22 G hG
  unfold chg
  rw [hq]
  change gz nx (o q.1 q.2.1) (kf q.1 q.2.1 q.2.2) = true
  unfold gz
  rw [fz_eq]
  exact hn
abbrev Al := (List ℕ → Bool) → (ℕ → ℕ → ℕ) → KF → Bool

def alg (prs : List (ℕ × ℕ × List ℕ)) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) : Bool :=
  prs.foldr (fun q acc => or (gz nx (o q.1 q.2.1) (kf q.1 q.2.1 q.2.2)) acc) false

theorem alg_true {nx : List ℕ → Bool} {o : ℕ → ℕ → ℕ} {kf : KF} {q : ℕ × ℕ × List ℕ}
    (hn : nx (o q.1 q.2.1 :: kf q.1 q.2.1 q.2.2) = true) : ∀ prs : List (ℕ × ℕ × List ℕ), q ∈ prs →
    alg prs nx o kf = true
  | [], h => by simp at h
  | u :: t, h => by
    change or (gz nx (o u.1 u.2.1) (kf u.1 u.2.1 u.2.2)) (alg t nx o kf) = true
    rcases List.mem_cons.mp h with rfl | h
    · unfold gz
      rw [fz_eq, hn]; rfl
    · rw [alg_true hn t h]; simp

def gt (O G V : ℕ) : ℕ := Nat.land (Nat.add V O) G
def sv (P K Z : ℕ) : ℕ := Nat.land (Nat.xor (Nat.shiftRight Z P) Z) K

def ndE (P K O G : ℕ) (nx : ℕ → List ℕ → Bool) (e A B S : ℕ) (sc : Sc) (al : Al) (o : ℕ → ℕ → ℕ) : Bool :=
  or (sc (gt O G (Nat.lor (sv P K (o A B)) S)) (nx (Nat.succ e)) o kr)
  (or (sc (gt O G (Nat.lor (sv P K A) (Nat.lor (sv P K (o A B)) S))) (nx e) o ka)
  (or (sc (gt O G (Nat.lor (sv P K B) (Nat.lor (sv P K (o A B)) S))) (nx e) o kb)
    (Nat.casesOn e false (fun e' => al (nx e') o kab))))

def nd (P K O G : ℕ) (nx : ℕ → List ℕ → Bool) (e A B S : ℕ) (sc : Sc) (al : Al) : Bool :=
  Nat.casesOn e
    (or (sc (gt O G (Nat.lor (sv P K (oA A B)) S)) (nx 0) oA kr)
    (or (sc (gt O G (Nat.lor (sv P K (oO A B)) S)) (nx 0) oO kr)
    (or (sc (gt O G (Nat.lor (sv P K (oX A B)) S)) (nx 0) oX kr)
      (sc (gt O G (Nat.lor (sv P K (oY A B)) S)) (nx 0) oY kr))))
    (fun e => or (ndE P K O G nx e A B S sc al oA) (or (ndE P K O G nx e A B S sc al oO)
      (or (ndE P K O G nx e A B S sc al oX) (ndE P K O G nx e A B S sc al oY))))

def pkl (W : ℕ) : List ℕ → ℕ
  | [] => 0
  | x :: t => Nat.add (Nat.mul W (pkl W t)) x

def nodeg (P m L W K O G : ℕ) (nx : ℕ → List ℕ → Bool) (e : ℕ) (ws : List ℕ) : Bool :=
  nd P K O G nx e (pkl W ((pairs ws).map fun q => q.1)) (pkl W ((pairs ws).map fun q => q.2.1))
    (pkl W ((pairs ws).map fun q => cuts P m q.2.2)) (sg L P W (pairs ws)) (alg (pairs ws))

def pkf (L : ℕ) : ℕ → (ℕ → ℕ) → ℕ
  | 0, _ => 0
  | N + 1, f => 2 ^ L * pkf L N (fun p => f (p + 1)) + f 0

theorem pkf_bit {L : ℕ} (hL : 0 < L) : ∀ (N : ℕ) (f : ℕ → ℕ), (∀ p, f p < 2 ^ L) → ∀ j,
    (pkf L N f).testBit j = (decide (j / L < N) && (f (j / L)).testBit (j % L))
  | 0, f, _, j => by simp [pkf]
  | N + 1, f, hf, j => by
    rw [pkf, Nat.testBit_two_pow_mul_add _ (hf 0)]
    by_cases h : j < L
    · rw [ite_eq_left h, Nat.div_eq_of_lt h, Nat.mod_eq_of_lt h]; simp
    · rw [ite_eq_right h, pkf_bit hL N _ (fun p => hf (p + 1)) (j - L)]
      have h1 : j / L = (j - L) / L + 1 := Nat.div_eq_sub_div hL (by omega)
      have h2 : (j - L) % L = j % L := (Nat.mod_eq_sub_mod (by omega)).symm
      rw [h1, h2]; simp

theorem pkf_zero (L : ℕ) : ∀ N : ℕ, pkf L N (fun _ => 0) = 0
  | 0 => rfl
  | N + 1 => by simp [pkf, pkf_zero L N]

theorem pkl_eq (L : ℕ) : ∀ (l : List ℕ) (N : ℕ), l.length ≤ N →
    pkl (2 ^ L) l = pkf L N (fun p => l.getD p 0)
  | [], N, _ => by simp [pkl, pkf_zero]
  | x :: t, 0, h => by simp at h
  | x :: t, N + 1, h => by
    have ih := pkl_eq L t N (by simpa using h)
    change 2 ^ L * pkl (2 ^ L) t + x = _
    rw [ih, pkf]
    simp

theorem pkf_add (L : ℕ) : ∀ (N : ℕ) (f : ℕ → ℕ),
    pkf L N f + pkf L N (fun _ => 1) = pkf L N (fun p => f p + 1)
  | 0, _ => rfl
  | N + 1, f => by
    simp only [pkf]
    rw [← pkf_add L N (fun p => f (p + 1))]
    ring

def BitOp (o : ℕ → ℕ → ℕ) : Prop := ∃ fb : Bool → Bool → Bool, fb false false = false ∧
  ∀ a b i, (o a b).testBit i = fb (a.testBit i) (b.testBit i)

theorem bo_A : BitOp oA := ⟨fun p q => p && q, rfl, fun a b i => Nat.testBit_and a b i⟩
theorem bo_O : BitOp oO := ⟨fun p q => p || q, rfl, fun a b i => Nat.testBit_or a b i⟩
theorem bo_X : BitOp oX := ⟨fun p q => Bool.xor p (p && q), rfl, fun a b i => by
  change (a ^^^ (a &&& b)).testBit i = _
  rw [Nat.testBit_xor, Nat.testBit_and]⟩
theorem bo_Y : BitOp oY := ⟨fun p q => Bool.xor q (p && q), rfl, fun a b i => by
  change (b ^^^ (a &&& b)).testBit i = _
  rw [Nat.testBit_xor, Nat.testBit_and]⟩
theorem bo_L : BitOp Nat.lor := ⟨fun p q => p || q, rfl, fun a b i => Nat.testBit_or a b i⟩

theorem BitOp.lt {o : ℕ → ℕ → ℕ} (h : BitOp o) {a b n : ℕ} (ha : a < 2 ^ n) (hb : b < 2 ^ n) :
    o a b < 2 ^ n := by
  obtain ⟨fb, h0, hf⟩ := h
  apply Nat.lt_pow_two_of_testBit
  intro i hi
  have hp : 2 ^ n ≤ 2 ^ i := Nat.pow_le_pow_right (by norm_num) hi
  rw [hf, Nat.testBit_lt_two_pow (lt_of_lt_of_le ha hp), Nat.testBit_lt_two_pow (lt_of_lt_of_le hb hp), h0]

theorem BitOp.pkf {o : ℕ → ℕ → ℕ} (h : BitOp o) {L : ℕ} (hL : 0 < L) (N : ℕ) (f g : ℕ → ℕ)
    (hf : ∀ p, f p < 2 ^ L) (hg : ∀ p, g p < 2 ^ L) :
    o (pkf L N f) (pkf L N g) = pkf L N (fun p => o (f p) (g p)) := by
  have hb := fun p => h.lt (hf p) (hg p)
  obtain ⟨fb, h0, hl⟩ := h
  apply Nat.eq_of_testBit_eq
  intro j
  rw [hl, pkf_bit hL N f hf, pkf_bit hL N g hg, pkf_bit hL N _ hb, hl]
  cases decide (j / L < N) <;> simp [h0]

theorem sep_lt (P x : ℕ) : sep P (2 ^ P - 1) x < 2 ^ P :=
  Nat.and_lt_two_pow _ (Nat.sub_lt (Nat.two_pow_pos P) (by norm_num))

theorem cuts_lt (P : ℕ) : ∀ ws : List ℕ, cuts P (2 ^ P - 1) ws < 2 ^ P
  | [] => Nat.two_pow_pos P
  | a :: t => Nat.or_lt_two_pow (sep_lt P a) (cuts_lt P t)

theorem lt_dbl {P x : ℕ} (h : x < 2 ^ P) : x < 2 ^ (P + P) :=
  lt_of_lt_of_le h (Nat.pow_le_pow_right (by norm_num) (by omega))

theorem sv_eq {P : ℕ} (hP : 0 < P) (N : ℕ) (f : ℕ → ℕ) (hf : ∀ p, f p < 2 ^ (P + P)) :
    sv P (pkf (P + P) N fun _ => 2 ^ P - 1) (pkf (P + P) N f) =
      pkf (P + P) N (fun p => sep P (2 ^ P - 1) (f p)) := by
  have hL : 0 < P + P := by omega
  have hm : 2 ^ P - 1 < 2 ^ P := Nat.sub_lt (Nat.two_pow_pos P) (by norm_num)
  apply Nat.eq_of_testBit_eq
  intro j
  change (((pkf (P + P) N f) >>> P ^^^ (pkf (P + P) N f)) &&& _).testBit j = _
  rw [Nat.testBit_and, Nat.testBit_xor, Nat.testBit_shiftRight, pkf_bit hL N f hf,
    pkf_bit hL N f hf, pkf_bit hL N _ (fun _ => lt_dbl hm), pkf_bit hL N _ (fun p => lt_dbl (sep_lt P (f p)))]
  change _ = (_ && (((f (j / (P + P))) >>> P ^^^ (f (j / (P + P)))) &&& (2 ^ P - 1)).testBit (j % (P + P)))
  rw [Nat.testBit_and, Nat.testBit_xor, Nat.testBit_shiftRight, mask_bit]
  by_cases h : j % (P + P) < P
  · have e0 : (P + P) * (j / (P + P)) + j % (P + P) = j := Nat.div_add_mod j (P + P)
    have e1 : (P + j) / (P + P) = j / (P + P) ∧ (P + j) % (P + P) = P + j % (P + P) := by
      generalize j / (P + P) = u at e0 ⊢
      generalize j % (P + P) = r at e0 h ⊢
      subst e0
      rw [show P + ((P + P) * u + r) = (P + P) * u + (P + r) by ring]
      exact ⟨by rw [Nat.mul_add_div hL, Nat.div_eq_of_lt (by omega), Nat.add_zero],
        by rw [Nat.mul_add_mod, Nat.mod_eq_of_lt (by omega)]⟩
    rw [e1.1, e1.2]
    cases decide (j / (P + P) < N) <;> simp [h]
  · simp [h]

theorem gt_bit {P : ℕ} (hP : 0 < P) {N : ℕ} (v : ℕ → ℕ) (hv : ∀ p, v p < 2 ^ P) {p : ℕ} (hp : p < N)
    (hvp : v p = 2 ^ P - 1) :
    (gt (pkf (P + P) N fun _ => 1) (pkf (P + P) N fun _ => 2 ^ P) (pkf (P + P) N v)).testBit
      ((P + P) * p + P) = true := by
  have hL : 0 < P + P := by omega
  have hPP : 2 ^ P < 2 ^ (P + P) := Nat.pow_lt_pow_right (by norm_num) (by omega)
  have e1 : ((P + P) * p + P) / (P + P) = p := by
    rw [Nat.mul_add_div hL, Nat.div_eq_of_lt (by omega)]; simp
  have e2 : ((P + P) * p + P) % (P + P) = P := by
    rw [Nat.mul_add_mod, Nat.mod_eq_of_lt (by omega)]
  change ((pkf (P + P) N v + pkf (P + P) N (fun _ => 1)) &&& _).testBit _ = true
  rw [Nat.testBit_and, pkf_add, pkf_bit hL N (fun q => v q + 1) (fun q => lt_of_le_of_lt (hv q) hPP),
    pkf_bit hL N _ (fun _ => hPP), e1, e2, hvp,
    Nat.sub_add_cancel (Nat.one_le_two_pow), Nat.testBit_two_pow_self]
  simp [hp]

theorem singles_len {α : Type} : ∀ l : List α, (singles l).length = l.length
  | [] => rfl
  | a :: t => by simp [singles, singles_len t]

theorem pairs_len {α : Type} : ∀ l : List α, 2 * (pairs l).length + l.length = l.length * l.length
  | [] => rfl
  | a :: t => by
    have ih := pairs_len t
    simp only [pairs, List.length_append, List.length_map, singles_len, List.length_cons]
    nlinarith

theorem singles_mem {α : Type} : ∀ {l : List α} {q : α × List α}, q ∈ singles l → q.1 ∈ l
  | [], q, h => by simp [singles] at h
  | a :: t, q, h => by
    simp only [singles, List.mem_cons, List.mem_map] at h
    rcases h with rfl | ⟨⟨b, bs⟩, hu, rfl⟩
    · simp
    · exact List.mem_cons_of_mem _ (singles_mem (q := (b, bs)) hu)

theorem pairs_mem {α : Type} : ∀ {l : List α} {q : α × α × List α}, q ∈ pairs l →
    q.1 ∈ l ∧ q.2.1 ∈ l
  | [], q, h => by simp [pairs] at h
  | a :: t, q, h => by
    simp only [pairs, List.mem_append, List.mem_map] at h
    rcases h with ⟨⟨b, bs⟩, hu, rfl⟩ | ⟨⟨b, c, bs⟩, hu, rfl⟩
    · exact ⟨by simp, List.mem_cons_of_mem _ (singles_mem (q := (b, bs)) hu)⟩
    · exact ⟨List.mem_cons_of_mem _ (pairs_mem (q := (b, c, bs)) hu).1,
        List.mem_cons_of_mem _ (pairs_mem (q := (b, c, bs)) hu).2⟩

theorem nodeg_complete {P k extra a b z : ℕ} {ws r kept : List ℕ} (hP : 0 < P)
    (next : ℕ → List ℕ → Bool) (hb : ∀ w ∈ ws, w < 2 ^ (P + P)) (hm : (a, b, r) ∈ pairs ws)
    (h8 : ws.length ≤ 7) (hz : z ∈ bops a b) (hk : kept ∈ keepChoices a b r)
    (he : extra + r.length = k) (hn : kept.length ≤ k)
    (hc : cuts P (2 ^ P - 1) (z :: kept) = 2 ^ P - 1)
    (ht : next (k - kept.length) (z :: kept) = true) :
    nodeg P (2 ^ P - 1) (P + P) (2 ^ (P + P)) (pkf (P + P) 21 fun _ => 2 ^ P - 1)
      (pkf (P + P) 21 fun _ => 1) (pkf (P + P) 21 fun _ => 2 ^ P) next extra ws = true := by
  have hL : 0 < P + P := by omega
  have hPL : P < P + P := by omega
  have hlen : (pairs ws).length ≤ 21 := by
    have := pairs_len ws
    have : ws.length * ws.length ≤ 7 * ws.length := Nat.mul_le_mul_right _ h8
    nlinarith
  obtain ⟨p, hpl, hpe⟩ := List.getElem_of_mem hm
  have hq : (pairs ws)[p]? = some (a, b, r) := by rw [List.getElem?_eq_getElem hpl, hpe]
  have hp21 : p < 21 := by omega
  unfold nodeg
  set prs := pairs ws with hprs
  rw [pkl_eq (P + P) (prs.map fun q => q.1) 21 (by simpa using hlen),
    pkl_eq (P + P) (prs.map fun q => q.2.1) 21 (by simpa using hlen),
    pkl_eq (P + P) (prs.map fun q => cuts P (2 ^ P - 1) q.2.2) 21 (by simpa using hlen)]
  set fa : ℕ → ℕ := fun p => (prs.map fun q => q.1).getD p 0 with hfa
  set fb : ℕ → ℕ := fun p => (prs.map fun q => q.2.1).getD p 0 with hfb
  set fs : ℕ → ℕ := fun p => (prs.map fun q => cuts P (2 ^ P - 1) q.2.2).getD p 0 with hfs
  have bnd : ∀ (F : ℕ × ℕ × List ℕ → ℕ) (n : ℕ), (∀ q ∈ prs, F q < 2 ^ n) → ∀ p, (prs.map F).getD p 0 < 2 ^ n := by
    intro F n hF p
    by_cases h : p < prs.length
    · rw [List.getD_eq_getElem _ _ (by simpa using h), List.getElem_map]
      exact hF _ (List.getElem_mem h)
    · rw [List.getD_eq_default _ _ (by simpa using h)]
      exact Nat.two_pow_pos n
  have hA : ∀ p, fa p < 2 ^ (P + P) := bnd _ _ fun q hq => hb _ (pairs_mem hq).1
  have hB : ∀ p, fb p < 2 ^ (P + P) := bnd _ _ fun q hq => hb _ (pairs_mem hq).2
  have hS : ∀ p, fs p < 2 ^ P := bnd _ _ fun q _ => cuts_lt P q.2.2
  have ea : fa p = a := by simp [hfa, List.getD_eq_getElem?_getD, hq]
  have eb : fb p = b := by simp [hfb, List.getD_eq_getElem?_getD, hq]
  have es : fs p = cuts P (2 ^ P - 1) r := by simp [hfs, List.getD_eq_getElem?_getD, hq]
  set K := pkf (P + P) 21 fun _ => 2 ^ P - 1 with hK
  set O := pkf (P + P) 21 fun _ => 1 with hO
  set G := pkf (P + P) 21 fun _ => 2 ^ P with hG
  have hc' : Nat.lor (sep P (2 ^ P - 1) z) (cuts P (2 ^ P - 1) kept) = 2 ^ P - 1 := hc

  have V0 : ∀ o : ℕ → ℕ → ℕ, BitOp o → Nat.lor (sv P K (o (pkf (P + P) 21 fa) (pkf (P + P) 21 fb))) (pkf (P + P) 21 fs) =
      pkf (P + P) 21 (fun p => Nat.lor (sep P (2 ^ P - 1) (o (fa p) (fb p))) (fs p)) := by
    intro o ho
    rw [ho.pkf hL 21 fa fb hA hB, hK, sv_eq hP 21 _ (fun p => ho.lt (hA p) (hB p)),
      bo_L.pkf hL 21 _ _ (fun p => lt_dbl (sep_lt P _)) (fun p => lt_dbl (hS p))]
  have b0 : ∀ (o : ℕ → ℕ → ℕ) (p : ℕ), Nat.lor (sep P (2 ^ P - 1) (o (fa p) (fb p))) (fs p) < 2 ^ P := fun o p =>
    bo_L.lt (sep_lt P _) (hS p)
  have V1 : ∀ o : ℕ → ℕ → ℕ, BitOp o → ∀ h : ℕ → ℕ, (∀ p, h p < 2 ^ (P + P)) →
      Nat.lor (sv P K (pkf (P + P) 21 h)) (Nat.lor (sv P K (o (pkf (P + P) 21 fa) (pkf (P + P) 21 fb))) (pkf (P + P) 21 fs)) =
      pkf (P + P) 21 (fun p => Nat.lor (sep P (2 ^ P - 1) (h p)) (Nat.lor (sep P (2 ^ P - 1) (o (fa p) (fb p))) (fs p))) := by
    intro o ho h hh
    rw [V0 o ho, hK, sv_eq hP 21 h hh,
      bo_L.pkf hL 21 _ _ (fun p => lt_dbl (sep_lt P _)) (fun p => lt_dbl (b0 o p))]
  have hz' : ∃ o, (o = oA ∨ o = oO ∨ o = oX ∨ o = oY) ∧ z = o a b := by
    have h1 := hz
    simp only [bops, ops, List.mem_toFinset, List.mem_cons, List.not_mem_nil, or_false] at h1
    rcases h1 with e | e | e | e
    · exact ⟨oA, by simp, e⟩
    · exact ⟨oO, by simp, e⟩
    · exact ⟨oX, by simp, e⟩
    · exact ⟨oY, by simp, e⟩
  obtain ⟨o, ho4, hzo⟩ := hz'
  have ho : BitOp o := by
    rcases ho4 with rfl | rfl | rfl | rfl
    exacts [bo_A, bo_O, bo_X, bo_Y]
  simp only [keepChoices, List.mem_cons, List.not_mem_nil, or_false] at hk
  rcases extra with _ | e
  · have hk0 : kept = r := by
      rcases hk with rfl | rfl | rfl | rfl
      · rfl
      all_goals (simp only [List.length_cons] at hn; omega)
    subst hk0
    have key : sg (P + P) P (2 ^ (P + P)) prs (gt O G (Nat.lor (sv P K (o (pkf (P + P) 21 fa) (pkf (P + P) 21 fb)))
        (pkf (P + P) 21 fs))) (next 0) o kr = true := by
      refine sg_true hPL (q := (a, b, kept)) ?_ prs p hq ?_
      · change next 0 (o a b :: kept) = true
        rw [← hzo]
        convert ht using 2; omega
      · rw [V0 o ho]
        exact gt_bit hP _ (b0 o) hp21 (by rw [ea, eb, es, ← hzo]; exact hc')
    change or _ (or _ (or _ _)) = true
    rcases ho4 with rfl | rfl | rfl | rfl <;> rw [key] <;> simp
  · have key : ndE P K O G next e (pkf (P + P) 21 fa) (pkf (P + P) 21 fb) (pkf (P + P) 21 fs)
        (sg (P + P) P (2 ^ (P + P)) prs) (alg prs) o = true := by
      unfold ndE
      rcases hk with rfl | rfl | rfl | rfl
      · rw [sg_true hPL (nx := next (Nat.succ e)) (o := o) (kf := kr) (q := (a, b, kept))
          (by
            change next (Nat.succ e) (o a b :: kept) = true
            rw [← hzo]
            convert ht using 2; omega) prs p hq
          (by
            rw [V0 o ho]
            exact gt_bit hP _ (b0 o) hp21 (by rw [ea, eb, es, ← hzo]; exact hc'))]
        simp
      · rw [sg_true hPL (nx := next e) (o := o) (kf := ka) (q := (a, b, r))
          (by
            change next e (o a b :: a :: r) = true
            rw [← hzo]
            convert ht using 2; simp only [List.length_cons]; omega) prs p hq
          (by
            rw [V1 o ho fa hA]
            refine gt_bit hP _ (fun p => bo_L.lt (sep_lt P _) (b0 o p)) hp21 ?_
            rw [ea, eb, es, ← hzo]
            change sep P (2 ^ P - 1) a ||| (sep P (2 ^ P - 1) z ||| cuts P (2 ^ P - 1) r) = _
            have h2 : sep P (2 ^ P - 1) z ||| (sep P (2 ^ P - 1) a ||| cuts P (2 ^ P - 1) r) = 2 ^ P - 1 := hc'
            convert h2 using 1; ac_rfl)]
        simp
      · rw [sg_true hPL (nx := next e) (o := o) (kf := kb) (q := (a, b, r))
          (by
            change next e (o a b :: b :: r) = true
            rw [← hzo]
            convert ht using 2; simp only [List.length_cons]; omega) prs p hq
          (by
            rw [V1 o ho fb hB]
            refine gt_bit hP _ (fun p => bo_L.lt (sep_lt P _) (b0 o p)) hp21 ?_
            rw [ea, eb, es, ← hzo]
            change sep P (2 ^ P - 1) b ||| (sep P (2 ^ P - 1) z ||| cuts P (2 ^ P - 1) r) = _
            have h2 : sep P (2 ^ P - 1) z ||| (sep P (2 ^ P - 1) b ||| cuts P (2 ^ P - 1) r) = 2 ^ P - 1 := hc'
            convert h2 using 1; ac_rfl)]
        simp
      · rcases e with _ | e'
        · simp only [List.length_cons] at hn; omega
        · have h4 : alg prs (next e') o kab = true := by
            refine alg_true (q := (a, b, r)) ?_ prs hm
            change next e' (o a b :: a :: b :: r) = true
            rw [← hzo]
            convert ht using 2; simp only [List.length_cons]; omega
          change or _ (or _ (or _ (alg prs (next e') o kab))) = true
          rw [h4]; simp
    change or _ (or _ (or _ _)) = true
    rcases ho4 with rfl | rfl | rfl | rfl <;> rw [key] <;> simp

def c2 (a b : ℕ) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) (p : ℕ) : Bool :=
  (cond (Nat.blt p 1) (gz nx (o a b) (kf a b []))
    false)

def s2 (L P W a b G : ℕ) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) : Bool :=
  sel L P W (c2 a b nx o kf) 22 G

def a2 (a b : ℕ) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) : Bool :=
  or (gz nx (o a b) (kf a b []))
    (false)

def u2 (P m L W K O G : ℕ) (nx : ℕ → List ℕ → Bool) (e0 a b : ℕ) : Bool :=
  nd P K O G nx e0 (Nat.add (Nat.mul W (0)) a)
    (Nat.add (Nat.mul W (0)) b)
    (Nat.add (Nat.mul W (0)) 0)
    (s2 L P W a b) (a2 a b)

def c3 (a b c : ℕ) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) (p : ℕ) : Bool :=
  (cond (Nat.blt p 2) (cond (Nat.blt p 1) (gz nx (o a b) (kf a b [c]))
    (gz nx (o a c) (kf a c [b])))
    (cond (Nat.blt p 3) (gz nx (o b c) (kf b c [a]))
    false))

def s3 (L P W a b c G : ℕ) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) : Bool :=
  sel L P W (c3 a b c nx o kf) 22 G

def a3 (a b c : ℕ) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) : Bool :=
  or (gz nx (o a b) (kf a b [c]))
    (or (gz nx (o a c) (kf a c [b]))
    (or (gz nx (o b c) (kf b c [a]))
    (false)))

def u3 (P m L W K O G : ℕ) (nx : ℕ → List ℕ → Bool) (e0 a b c : ℕ) : Bool :=
  nd P K O G nx e0 (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (0)) b)) a)) a)
    (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (0)) c)) c)) b)
    (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (0)) (Nat.lor (sep P m a) 0))) (Nat.lor (sep P m b) 0))) (Nat.lor (sep P m c) 0))
    (s3 L P W a b c) (a3 a b c)

def c4 (a b c d : ℕ) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) (p : ℕ) : Bool :=
  (cond (Nat.blt p 3) (cond (Nat.blt p 1) (gz nx (o a b) (kf a b [c, d]))
    (cond (Nat.blt p 2) (gz nx (o a c) (kf a c [b, d]))
    (gz nx (o a d) (kf a d [b, c]))))
    (cond (Nat.blt p 5) (cond (Nat.blt p 4) (gz nx (o b c) (kf b c [a, d]))
    (gz nx (o b d) (kf b d [a, c])))
    (cond (Nat.blt p 6) (gz nx (o c d) (kf c d [a, b]))
    false)))

def s4 (L P W a b c d G : ℕ) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) : Bool :=
  sel L P W (c4 a b c d nx o kf) 22 G

def a4 (a b c d : ℕ) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) : Bool :=
  or (gz nx (o a b) (kf a b [c, d]))
    (or (gz nx (o a c) (kf a c [b, d]))
    (or (gz nx (o a d) (kf a d [b, c]))
    (or (gz nx (o b c) (kf b c [a, d]))
    (or (gz nx (o b d) (kf b d [a, c]))
    (or (gz nx (o c d) (kf c d [a, b]))
    (false))))))

def u4 (P m L W K O G : ℕ) (nx : ℕ → List ℕ → Bool) (e0 a b c d : ℕ) : Bool :=
  nd P K O G nx e0 (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (0)) c)) b)) b)) a)) a)) a)
    (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (0)) d)) d)) c)) d)) c)) b)
    (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (0)) (Nat.lor (sep P m a) (Nat.lor (sep P m b) 0)))) (Nat.lor (sep P m a) (Nat.lor (sep P m c) 0)))) (Nat.lor (sep P m a) (Nat.lor (sep P m d) 0)))) (Nat.lor (sep P m b) (Nat.lor (sep P m c) 0)))) (Nat.lor (sep P m b) (Nat.lor (sep P m d) 0)))) (Nat.lor (sep P m c) (Nat.lor (sep P m d) 0)))
    (s4 L P W a b c d) (a4 a b c d)

def c5 (a b c d e : ℕ) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) (p : ℕ) : Bool :=
  (cond (Nat.blt p 5) (cond (Nat.blt p 2) (cond (Nat.blt p 1) (gz nx (o a b) (kf a b [c, d, e]))
    (gz nx (o a c) (kf a c [b, d, e])))
    (cond (Nat.blt p 3) (gz nx (o a d) (kf a d [b, c, e]))
    (cond (Nat.blt p 4) (gz nx (o a e) (kf a e [b, c, d]))
    (gz nx (o b c) (kf b c [a, d, e])))))
    (cond (Nat.blt p 8) (cond (Nat.blt p 6) (gz nx (o b d) (kf b d [a, c, e]))
    (cond (Nat.blt p 7) (gz nx (o b e) (kf b e [a, c, d]))
    (gz nx (o c d) (kf c d [a, b, e]))))
    (cond (Nat.blt p 9) (gz nx (o c e) (kf c e [a, b, d]))
    (cond (Nat.blt p 10) (gz nx (o d e) (kf d e [a, b, c]))
    false))))

def s5 (L P W a b c d e G : ℕ) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) : Bool :=
  sel L P W (c5 a b c d e nx o kf) 22 G

def a5 (a b c d e : ℕ) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) : Bool :=
  or (gz nx (o a b) (kf a b [c, d, e]))
    (or (gz nx (o a c) (kf a c [b, d, e]))
    (or (gz nx (o a d) (kf a d [b, c, e]))
    (or (gz nx (o a e) (kf a e [b, c, d]))
    (or (gz nx (o b c) (kf b c [a, d, e]))
    (or (gz nx (o b d) (kf b d [a, c, e]))
    (or (gz nx (o b e) (kf b e [a, c, d]))
    (or (gz nx (o c d) (kf c d [a, b, e]))
    (or (gz nx (o c e) (kf c e [a, b, d]))
    (or (gz nx (o d e) (kf d e [a, b, c]))
    (false))))))))))

def u5 (P m L W K O G : ℕ) (nx : ℕ → List ℕ → Bool) (e0 a b c d e : ℕ) : Bool :=
  nd P K O G nx e0 (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (0)) d)) c)) c)) b)) b)) b)) a)) a)) a)) a)
    (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (0)) e)) e)) d)) e)) d)) c)) e)) d)) c)) b)
    (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (0)) (Nat.lor (sep P m a) (Nat.lor (sep P m b) (Nat.lor (sep P m c) 0))))) (Nat.lor (sep P m a) (Nat.lor (sep P m b) (Nat.lor (sep P m d) 0))))) (Nat.lor (sep P m a) (Nat.lor (sep P m b) (Nat.lor (sep P m e) 0))))) (Nat.lor (sep P m a) (Nat.lor (sep P m c) (Nat.lor (sep P m d) 0))))) (Nat.lor (sep P m a) (Nat.lor (sep P m c) (Nat.lor (sep P m e) 0))))) (Nat.lor (sep P m a) (Nat.lor (sep P m d) (Nat.lor (sep P m e) 0))))) (Nat.lor (sep P m b) (Nat.lor (sep P m c) (Nat.lor (sep P m d) 0))))) (Nat.lor (sep P m b) (Nat.lor (sep P m c) (Nat.lor (sep P m e) 0))))) (Nat.lor (sep P m b) (Nat.lor (sep P m d) (Nat.lor (sep P m e) 0))))) (Nat.lor (sep P m c) (Nat.lor (sep P m d) (Nat.lor (sep P m e) 0))))
    (s5 L P W a b c d e) (a5 a b c d e)

def c6 (a b c d e f : ℕ) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) (p : ℕ) : Bool :=
  (cond (Nat.blt p 8) (cond (Nat.blt p 4) (cond (Nat.blt p 2) (cond (Nat.blt p 1) (gz nx (o a b) (kf a b [c, d, e, f]))
    (gz nx (o a c) (kf a c [b, d, e, f])))
    (cond (Nat.blt p 3) (gz nx (o a d) (kf a d [b, c, e, f]))
    (gz nx (o a e) (kf a e [b, c, d, f]))))
    (cond (Nat.blt p 6) (cond (Nat.blt p 5) (gz nx (o a f) (kf a f [b, c, d, e]))
    (gz nx (o b c) (kf b c [a, d, e, f])))
    (cond (Nat.blt p 7) (gz nx (o b d) (kf b d [a, c, e, f]))
    (gz nx (o b e) (kf b e [a, c, d, f])))))
    (cond (Nat.blt p 12) (cond (Nat.blt p 10) (cond (Nat.blt p 9) (gz nx (o b f) (kf b f [a, c, d, e]))
    (gz nx (o c d) (kf c d [a, b, e, f])))
    (cond (Nat.blt p 11) (gz nx (o c e) (kf c e [a, b, d, f]))
    (gz nx (o c f) (kf c f [a, b, d, e]))))
    (cond (Nat.blt p 14) (cond (Nat.blt p 13) (gz nx (o d e) (kf d e [a, b, c, f]))
    (gz nx (o d f) (kf d f [a, b, c, e])))
    (cond (Nat.blt p 15) (gz nx (o e f) (kf e f [a, b, c, d]))
    false))))

def s6 (L P W a b c d e f G : ℕ) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) : Bool :=
  sel L P W (c6 a b c d e f nx o kf) 22 G

def a6 (a b c d e f : ℕ) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) : Bool :=
  or (gz nx (o a b) (kf a b [c, d, e, f]))
    (or (gz nx (o a c) (kf a c [b, d, e, f]))
    (or (gz nx (o a d) (kf a d [b, c, e, f]))
    (or (gz nx (o a e) (kf a e [b, c, d, f]))
    (or (gz nx (o a f) (kf a f [b, c, d, e]))
    (or (gz nx (o b c) (kf b c [a, d, e, f]))
    (or (gz nx (o b d) (kf b d [a, c, e, f]))
    (or (gz nx (o b e) (kf b e [a, c, d, f]))
    (or (gz nx (o b f) (kf b f [a, c, d, e]))
    (or (gz nx (o c d) (kf c d [a, b, e, f]))
    (or (gz nx (o c e) (kf c e [a, b, d, f]))
    (or (gz nx (o c f) (kf c f [a, b, d, e]))
    (or (gz nx (o d e) (kf d e [a, b, c, f]))
    (or (gz nx (o d f) (kf d f [a, b, c, e]))
    (or (gz nx (o e f) (kf e f [a, b, c, d]))
    (false)))))))))))))))

def u6 (P m L W K O G : ℕ) (nx : ℕ → List ℕ → Bool) (e0 a b c d e f : ℕ) : Bool :=
  nd P K O G nx e0 (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (0)) e)) d)) d)) c)) c)) c)) b)) b)) b)) b)) a)) a)) a)) a)) a)
    (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (0)) f)) f)) e)) f)) e)) d)) f)) e)) d)) c)) f)) e)) d)) c)) b)
    (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (0)) (Nat.lor (sep P m a) (Nat.lor (sep P m b) (Nat.lor (sep P m c) (Nat.lor (sep P m d) 0)))))) (Nat.lor (sep P m a) (Nat.lor (sep P m b) (Nat.lor (sep P m c) (Nat.lor (sep P m e) 0)))))) (Nat.lor (sep P m a) (Nat.lor (sep P m b) (Nat.lor (sep P m c) (Nat.lor (sep P m f) 0)))))) (Nat.lor (sep P m a) (Nat.lor (sep P m b) (Nat.lor (sep P m d) (Nat.lor (sep P m e) 0)))))) (Nat.lor (sep P m a) (Nat.lor (sep P m b) (Nat.lor (sep P m d) (Nat.lor (sep P m f) 0)))))) (Nat.lor (sep P m a) (Nat.lor (sep P m b) (Nat.lor (sep P m e) (Nat.lor (sep P m f) 0)))))) (Nat.lor (sep P m a) (Nat.lor (sep P m c) (Nat.lor (sep P m d) (Nat.lor (sep P m e) 0)))))) (Nat.lor (sep P m a) (Nat.lor (sep P m c) (Nat.lor (sep P m d) (Nat.lor (sep P m f) 0)))))) (Nat.lor (sep P m a) (Nat.lor (sep P m c) (Nat.lor (sep P m e) (Nat.lor (sep P m f) 0)))))) (Nat.lor (sep P m a) (Nat.lor (sep P m d) (Nat.lor (sep P m e) (Nat.lor (sep P m f) 0)))))) (Nat.lor (sep P m b) (Nat.lor (sep P m c) (Nat.lor (sep P m d) (Nat.lor (sep P m e) 0)))))) (Nat.lor (sep P m b) (Nat.lor (sep P m c) (Nat.lor (sep P m d) (Nat.lor (sep P m f) 0)))))) (Nat.lor (sep P m b) (Nat.lor (sep P m c) (Nat.lor (sep P m e) (Nat.lor (sep P m f) 0)))))) (Nat.lor (sep P m b) (Nat.lor (sep P m d) (Nat.lor (sep P m e) (Nat.lor (sep P m f) 0)))))) (Nat.lor (sep P m c) (Nat.lor (sep P m d) (Nat.lor (sep P m e) (Nat.lor (sep P m f) 0)))))
    (s6 L P W a b c d e f) (a6 a b c d e f)

def c7 (a b c d e f u : ℕ) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) (p : ℕ) : Bool :=
  (cond (Nat.blt p 11) (cond (Nat.blt p 5) (cond (Nat.blt p 2) (cond (Nat.blt p 1) (gz nx (o a b) (kf a b [c, d, e, f, u]))
    (gz nx (o a c) (kf a c [b, d, e, f, u])))
    (cond (Nat.blt p 3) (gz nx (o a d) (kf a d [b, c, e, f, u]))
    (cond (Nat.blt p 4) (gz nx (o a e) (kf a e [b, c, d, f, u]))
    (gz nx (o a f) (kf a f [b, c, d, e, u])))))
    (cond (Nat.blt p 8) (cond (Nat.blt p 6) (gz nx (o a u) (kf a u [b, c, d, e, f]))
    (cond (Nat.blt p 7) (gz nx (o b c) (kf b c [a, d, e, f, u]))
    (gz nx (o b d) (kf b d [a, c, e, f, u]))))
    (cond (Nat.blt p 9) (gz nx (o b e) (kf b e [a, c, d, f, u]))
    (cond (Nat.blt p 10) (gz nx (o b f) (kf b f [a, c, d, e, u]))
    (gz nx (o b u) (kf b u [a, c, d, e, f]))))))
    (cond (Nat.blt p 16) (cond (Nat.blt p 13) (cond (Nat.blt p 12) (gz nx (o c d) (kf c d [a, b, e, f, u]))
    (gz nx (o c e) (kf c e [a, b, d, f, u])))
    (cond (Nat.blt p 14) (gz nx (o c f) (kf c f [a, b, d, e, u]))
    (cond (Nat.blt p 15) (gz nx (o c u) (kf c u [a, b, d, e, f]))
    (gz nx (o d e) (kf d e [a, b, c, f, u])))))
    (cond (Nat.blt p 19) (cond (Nat.blt p 17) (gz nx (o d f) (kf d f [a, b, c, e, u]))
    (cond (Nat.blt p 18) (gz nx (o d u) (kf d u [a, b, c, e, f]))
    (gz nx (o e f) (kf e f [a, b, c, d, u]))))
    (cond (Nat.blt p 20) (gz nx (o e u) (kf e u [a, b, c, d, f]))
    (cond (Nat.blt p 21) (gz nx (o f u) (kf f u [a, b, c, d, e]))
    false)))))

def s7 (L P W a b c d e f u G : ℕ) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) : Bool :=
  sel L P W (c7 a b c d e f u nx o kf) 22 G

def a7 (a b c d e f u : ℕ) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) : Bool :=
  or (gz nx (o a b) (kf a b [c, d, e, f, u]))
    (or (gz nx (o a c) (kf a c [b, d, e, f, u]))
    (or (gz nx (o a d) (kf a d [b, c, e, f, u]))
    (or (gz nx (o a e) (kf a e [b, c, d, f, u]))
    (or (gz nx (o a f) (kf a f [b, c, d, e, u]))
    (or (gz nx (o a u) (kf a u [b, c, d, e, f]))
    (or (gz nx (o b c) (kf b c [a, d, e, f, u]))
    (or (gz nx (o b d) (kf b d [a, c, e, f, u]))
    (or (gz nx (o b e) (kf b e [a, c, d, f, u]))
    (or (gz nx (o b f) (kf b f [a, c, d, e, u]))
    (or (gz nx (o b u) (kf b u [a, c, d, e, f]))
    (or (gz nx (o c d) (kf c d [a, b, e, f, u]))
    (or (gz nx (o c e) (kf c e [a, b, d, f, u]))
    (or (gz nx (o c f) (kf c f [a, b, d, e, u]))
    (or (gz nx (o c u) (kf c u [a, b, d, e, f]))
    (or (gz nx (o d e) (kf d e [a, b, c, f, u]))
    (or (gz nx (o d f) (kf d f [a, b, c, e, u]))
    (or (gz nx (o d u) (kf d u [a, b, c, e, f]))
    (or (gz nx (o e f) (kf e f [a, b, c, d, u]))
    (or (gz nx (o e u) (kf e u [a, b, c, d, f]))
    (or (gz nx (o f u) (kf f u [a, b, c, d, e]))
    (false)))))))))))))))))))))

def u7 (P m L W K O G : ℕ) (nx : ℕ → List ℕ → Bool) (e0 a b c d e f u : ℕ) : Bool :=
  nd P K O G nx e0 (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (0)) f)) e)) e)) d)) d)) d)) c)) c)) c)) c)) b)) b)) b)) b)) b)) a)) a)) a)) a)) a)) a)
    (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (0)) u)) u)) f)) u)) f)) e)) u)) f)) e)) d)) u)) f)) e)) d)) c)) u)) f)) e)) d)) c)) b)
    (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (Nat.add (Nat.mul W (0)) (Nat.lor (sep P m a) (Nat.lor (sep P m b) (Nat.lor (sep P m c) (Nat.lor (sep P m d) (Nat.lor (sep P m e) 0))))))) (Nat.lor (sep P m a) (Nat.lor (sep P m b) (Nat.lor (sep P m c) (Nat.lor (sep P m d) (Nat.lor (sep P m f) 0))))))) (Nat.lor (sep P m a) (Nat.lor (sep P m b) (Nat.lor (sep P m c) (Nat.lor (sep P m d) (Nat.lor (sep P m u) 0))))))) (Nat.lor (sep P m a) (Nat.lor (sep P m b) (Nat.lor (sep P m c) (Nat.lor (sep P m e) (Nat.lor (sep P m f) 0))))))) (Nat.lor (sep P m a) (Nat.lor (sep P m b) (Nat.lor (sep P m c) (Nat.lor (sep P m e) (Nat.lor (sep P m u) 0))))))) (Nat.lor (sep P m a) (Nat.lor (sep P m b) (Nat.lor (sep P m c) (Nat.lor (sep P m f) (Nat.lor (sep P m u) 0))))))) (Nat.lor (sep P m a) (Nat.lor (sep P m b) (Nat.lor (sep P m d) (Nat.lor (sep P m e) (Nat.lor (sep P m f) 0))))))) (Nat.lor (sep P m a) (Nat.lor (sep P m b) (Nat.lor (sep P m d) (Nat.lor (sep P m e) (Nat.lor (sep P m u) 0))))))) (Nat.lor (sep P m a) (Nat.lor (sep P m b) (Nat.lor (sep P m d) (Nat.lor (sep P m f) (Nat.lor (sep P m u) 0))))))) (Nat.lor (sep P m a) (Nat.lor (sep P m b) (Nat.lor (sep P m e) (Nat.lor (sep P m f) (Nat.lor (sep P m u) 0))))))) (Nat.lor (sep P m a) (Nat.lor (sep P m c) (Nat.lor (sep P m d) (Nat.lor (sep P m e) (Nat.lor (sep P m f) 0))))))) (Nat.lor (sep P m a) (Nat.lor (sep P m c) (Nat.lor (sep P m d) (Nat.lor (sep P m e) (Nat.lor (sep P m u) 0))))))) (Nat.lor (sep P m a) (Nat.lor (sep P m c) (Nat.lor (sep P m d) (Nat.lor (sep P m f) (Nat.lor (sep P m u) 0))))))) (Nat.lor (sep P m a) (Nat.lor (sep P m c) (Nat.lor (sep P m e) (Nat.lor (sep P m f) (Nat.lor (sep P m u) 0))))))) (Nat.lor (sep P m a) (Nat.lor (sep P m d) (Nat.lor (sep P m e) (Nat.lor (sep P m f) (Nat.lor (sep P m u) 0))))))) (Nat.lor (sep P m b) (Nat.lor (sep P m c) (Nat.lor (sep P m d) (Nat.lor (sep P m e) (Nat.lor (sep P m f) 0))))))) (Nat.lor (sep P m b) (Nat.lor (sep P m c) (Nat.lor (sep P m d) (Nat.lor (sep P m e) (Nat.lor (sep P m u) 0))))))) (Nat.lor (sep P m b) (Nat.lor (sep P m c) (Nat.lor (sep P m d) (Nat.lor (sep P m f) (Nat.lor (sep P m u) 0))))))) (Nat.lor (sep P m b) (Nat.lor (sep P m c) (Nat.lor (sep P m e) (Nat.lor (sep P m f) (Nat.lor (sep P m u) 0))))))) (Nat.lor (sep P m b) (Nat.lor (sep P m d) (Nat.lor (sep P m e) (Nat.lor (sep P m f) (Nat.lor (sep P m u) 0))))))) (Nat.lor (sep P m c) (Nat.lor (sep P m d) (Nat.lor (sep P m e) (Nat.lor (sep P m f) (Nat.lor (sep P m u) 0))))))
    (s7 L P W a b c d e f u) (a7 a b c d e f u)

def d7 (P m L W K O G _g : ℕ) (nx : ℕ → List ℕ → Bool) (e0 a b c d e f u : ℕ) (l : List ℕ) : Bool :=
  List.casesOn l (u7 P m L W K O G nx e0 a b c d e f u) (fun _ _ => true)

def d6 (P m L W K O G g : ℕ) (nx : ℕ → List ℕ → Bool) (e0 a b c d e f : ℕ) (l : List ℕ) : Bool :=
  List.casesOn l (u6 P m L W K O G nx e0 a b c d e f) (fun y t => d7 P m L W K O G g nx e0 a b c d e f y t)

def d5 (P m L W K O G g : ℕ) (nx : ℕ → List ℕ → Bool) (e0 a b c d e : ℕ) (l : List ℕ) : Bool :=
  List.casesOn l (u5 P m L W K O G nx e0 a b c d e) (fun y t => d6 P m L W K O G g nx e0 a b c d e y t)

def d4 (P m L W K O G g : ℕ) (nx : ℕ → List ℕ → Bool) (e0 a b c d : ℕ) (l : List ℕ) : Bool :=
  List.casesOn l (u4 P m L W K O G nx e0 a b c d) (fun y t => d5 P m L W K O G g nx e0 a b c d y t)

def d3 (P m L W K O G g : ℕ) (nx : ℕ → List ℕ → Bool) (e0 a b c : ℕ) (l : List ℕ) : Bool :=
  List.casesOn l (u3 P m L W K O G nx e0 a b c) (fun y t => d4 P m L W K O G g nx e0 a b c y t)

def d2 (P m L W K O G g : ℕ) (nx : ℕ → List ℕ → Bool) (e0 a b : ℕ) (l : List ℕ) : Bool :=
  List.casesOn l (u2 P m L W K O G nx e0 a b) (fun y t => d3 P m L W K O G g nx e0 a b y t)

def d1 (P m L W K O G g : ℕ) (nx : ℕ → List ℕ → Bool) (e0 a : ℕ) (l : List ℕ) : Bool :=
  List.casesOn l (Nat.beq a g) (fun y t => d2 P m L W K O G g nx e0 a y t)

set_option maxRecDepth 100000 in
theorem f2 (a b : ℕ) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) (p : ℕ) :
    chg nx o kf (pairs [a, b]) p = c2 a b nx o kf p := by
  by_cases h : p < 1
  · interval_cases p <;> rfl
  · have h1 : (pairs [a, b])[p]? = none := by
      rw [List.getElem?_eq_none]
      have := pairs_len [a, b]
      simp only [List.length_cons, List.length_nil] at this
      omega
    have hb : ∀ m, m ≤ 1 → Nat.blt p m = false := fun m hm => by
      cases hx : Nat.blt p m
      · rfl
      · have := Nat.blt_eq.mp hx; omega
    unfold chg c2
    rw [h1]
    simp [hb]

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem e2 (P m L W K O G : ℕ) (nx : ℕ → List ℕ → Bool) (e0 a b : ℕ) :
    nodeg P m L W K O G nx e0 [a, b] = u2 P m L W K O G nx e0 a b := by
  have hs : sg L P W (pairs [a, b]) = s2 L P W a b := by
    funext G nx o kf
    unfold sg s2
    congr 1
    funext p
    exact f2 a b nx o kf p
  have ha : alg (pairs [a, b]) = a2 a b := rfl
  unfold nodeg u2
  rw [hs, ha]
  simp only [pairs, singles, List.map_cons, List.map_nil, List.cons_append, List.nil_append,
    pkl, cuts, List.foldr_cons, List.foldr_nil]

set_option maxRecDepth 100000 in
theorem f3 (a b c : ℕ) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) (p : ℕ) :
    chg nx o kf (pairs [a, b, c]) p = c3 a b c nx o kf p := by
  by_cases h : p < 3
  · interval_cases p <;> rfl
  · have h1 : (pairs [a, b, c])[p]? = none := by
      rw [List.getElem?_eq_none]
      have := pairs_len [a, b, c]
      simp only [List.length_cons, List.length_nil] at this
      omega
    have hb : ∀ m, m ≤ 3 → Nat.blt p m = false := fun m hm => by
      cases hx : Nat.blt p m
      · rfl
      · have := Nat.blt_eq.mp hx; omega
    unfold chg c3
    rw [h1]
    simp [hb]

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem e3 (P m L W K O G : ℕ) (nx : ℕ → List ℕ → Bool) (e0 a b c : ℕ) :
    nodeg P m L W K O G nx e0 [a, b, c] = u3 P m L W K O G nx e0 a b c := by
  have hs : sg L P W (pairs [a, b, c]) = s3 L P W a b c := by
    funext G nx o kf
    unfold sg s3
    congr 1
    funext p
    exact f3 a b c nx o kf p
  have ha : alg (pairs [a, b, c]) = a3 a b c := rfl
  unfold nodeg u3
  rw [hs, ha]
  simp only [pairs, singles, List.map_cons, List.map_nil, List.cons_append, List.nil_append,
    pkl, cuts, List.foldr_cons, List.foldr_nil]

set_option maxRecDepth 100000 in
theorem f4 (a b c d : ℕ) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) (p : ℕ) :
    chg nx o kf (pairs [a, b, c, d]) p = c4 a b c d nx o kf p := by
  by_cases h : p < 6
  · interval_cases p <;> rfl
  · have h1 : (pairs [a, b, c, d])[p]? = none := by
      rw [List.getElem?_eq_none]
      have := pairs_len [a, b, c, d]
      simp only [List.length_cons, List.length_nil] at this
      omega
    have hb : ∀ m, m ≤ 6 → Nat.blt p m = false := fun m hm => by
      cases hx : Nat.blt p m
      · rfl
      · have := Nat.blt_eq.mp hx; omega
    unfold chg c4
    rw [h1]
    simp [hb]

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem e4 (P m L W K O G : ℕ) (nx : ℕ → List ℕ → Bool) (e0 a b c d : ℕ) :
    nodeg P m L W K O G nx e0 [a, b, c, d] = u4 P m L W K O G nx e0 a b c d := by
  have hs : sg L P W (pairs [a, b, c, d]) = s4 L P W a b c d := by
    funext G nx o kf
    unfold sg s4
    congr 1
    funext p
    exact f4 a b c d nx o kf p
  have ha : alg (pairs [a, b, c, d]) = a4 a b c d := rfl
  unfold nodeg u4
  rw [hs, ha]
  simp only [pairs, singles, List.map_cons, List.map_nil, List.cons_append, List.nil_append,
    pkl, cuts, List.foldr_cons, List.foldr_nil]

set_option maxRecDepth 100000 in
theorem f5 (a b c d e : ℕ) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) (p : ℕ) :
    chg nx o kf (pairs [a, b, c, d, e]) p = c5 a b c d e nx o kf p := by
  by_cases h : p < 10
  · interval_cases p <;> rfl
  · have h1 : (pairs [a, b, c, d, e])[p]? = none := by
      rw [List.getElem?_eq_none]
      have := pairs_len [a, b, c, d, e]
      simp only [List.length_cons, List.length_nil] at this
      omega
    have hb : ∀ m, m ≤ 10 → Nat.blt p m = false := fun m hm => by
      cases hx : Nat.blt p m
      · rfl
      · have := Nat.blt_eq.mp hx; omega
    unfold chg c5
    rw [h1]
    simp [hb]

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem e5 (P m L W K O G : ℕ) (nx : ℕ → List ℕ → Bool) (e0 a b c d e : ℕ) :
    nodeg P m L W K O G nx e0 [a, b, c, d, e] = u5 P m L W K O G nx e0 a b c d e := by
  have hs : sg L P W (pairs [a, b, c, d, e]) = s5 L P W a b c d e := by
    funext G nx o kf
    unfold sg s5
    congr 1
    funext p
    exact f5 a b c d e nx o kf p
  have ha : alg (pairs [a, b, c, d, e]) = a5 a b c d e := rfl
  unfold nodeg u5
  rw [hs, ha]
  simp only [pairs, singles, List.map_cons, List.map_nil, List.cons_append, List.nil_append,
    pkl, cuts, List.foldr_cons, List.foldr_nil]

set_option maxRecDepth 100000 in
theorem f6 (a b c d e f : ℕ) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) (p : ℕ) :
    chg nx o kf (pairs [a, b, c, d, e, f]) p = c6 a b c d e f nx o kf p := by
  by_cases h : p < 15
  · interval_cases p <;> rfl
  · have h1 : (pairs [a, b, c, d, e, f])[p]? = none := by
      rw [List.getElem?_eq_none]
      have := pairs_len [a, b, c, d, e, f]
      simp only [List.length_cons, List.length_nil] at this
      omega
    have hb : ∀ m, m ≤ 15 → Nat.blt p m = false := fun m hm => by
      cases hx : Nat.blt p m
      · rfl
      · have := Nat.blt_eq.mp hx; omega
    unfold chg c6
    rw [h1]
    simp [hb]

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem e6 (P m L W K O G : ℕ) (nx : ℕ → List ℕ → Bool) (e0 a b c d e f : ℕ) :
    nodeg P m L W K O G nx e0 [a, b, c, d, e, f] = u6 P m L W K O G nx e0 a b c d e f := by
  have hs : sg L P W (pairs [a, b, c, d, e, f]) = s6 L P W a b c d e f := by
    funext G nx o kf
    unfold sg s6
    congr 1
    funext p
    exact f6 a b c d e f nx o kf p
  have ha : alg (pairs [a, b, c, d, e, f]) = a6 a b c d e f := rfl
  unfold nodeg u6
  rw [hs, ha]
  simp only [pairs, singles, List.map_cons, List.map_nil, List.cons_append, List.nil_append,
    pkl, cuts, List.foldr_cons, List.foldr_nil]

set_option maxRecDepth 100000 in
theorem f7 (a b c d e f u : ℕ) (nx : List ℕ → Bool) (o : ℕ → ℕ → ℕ) (kf : KF) (p : ℕ) :
    chg nx o kf (pairs [a, b, c, d, e, f, u]) p = c7 a b c d e f u nx o kf p := by
  by_cases h : p < 21
  · interval_cases p <;> rfl
  · have h1 : (pairs [a, b, c, d, e, f, u])[p]? = none := by
      rw [List.getElem?_eq_none]
      have := pairs_len [a, b, c, d, e, f, u]
      simp only [List.length_cons, List.length_nil] at this
      omega
    have hb : ∀ m, m ≤ 21 → Nat.blt p m = false := fun m hm => by
      cases hx : Nat.blt p m
      · rfl
      · have := Nat.blt_eq.mp hx; omega
    unfold chg c7
    rw [h1]
    simp [hb]

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem e7 (P m L W K O G : ℕ) (nx : ℕ → List ℕ → Bool) (e0 a b c d e f u : ℕ) :
    nodeg P m L W K O G nx e0 [a, b, c, d, e, f, u] = u7 P m L W K O G nx e0 a b c d e f u := by
  have hs : sg L P W (pairs [a, b, c, d, e, f, u]) = s7 L P W a b c d e f u := by
    funext G nx o kf
    unfold sg s7
    congr 1
    funext p
    exact f7 a b c d e f u nx o kf p
  have ha : alg (pairs [a, b, c, d, e, f, u]) = a7 a b c d e f u := rfl
  unfold nodeg u7
  rw [hs, ha]
  simp only [pairs, singles, List.map_cons, List.map_nil, List.cons_append, List.nil_append,
    pkl, cuts, List.foldr_cons, List.foldr_nil]

set_option maxRecDepth 100000 in
theorem d1_true (P m L W K O G g : ℕ) (nx : ℕ → List ℕ → Bool) (e0 a b : ℕ) (t : List ℕ)
    (h : (a :: b :: t).length ≤ 7 → nodeg P m L W K O G nx e0 (a :: b :: t) = true) :
    d1 P m L W K O G g nx e0 a (b :: t) = true := by
  rcases t with _ | ⟨c, _ | ⟨d, _ | ⟨e, _ | ⟨f, _ | ⟨u, _ | ⟨j, t⟩⟩⟩⟩⟩⟩
  · exact (e2 P m L W K O G nx e0 a b).symm.trans (h (by simp))
  · exact (e3 P m L W K O G nx e0 a b c).symm.trans (h (by simp))
  · exact (e4 P m L W K O G nx e0 a b c d).symm.trans (h (by simp))
  · exact (e5 P m L W K O G nx e0 a b c d e).symm.trans (h (by simp))
  · exact (e6 P m L W K O G nx e0 a b c d e f).symm.trans (h (by simp))
  · exact (e7 P m L W K O G nx e0 a b c d e f u).symm.trans (h (by simp))
  · rfl

def d0 (P m L W K O G g : ℕ) (nx : ℕ → List ℕ → Bool) (e0 : ℕ) (l : List ℕ) : Bool :=
  List.casesOn l false (fun y t => d1 P m L W K O G g nx e0 y t)

theorem d0_goal (P m L W K O G g : ℕ) (nx : ℕ → List ℕ → Bool) (e0 : ℕ) :
    d0 P m L W K O G g nx e0 [g] = true := Nat.beq_refl g

theorem d0_true (P m L W K O G g : ℕ) (nx : ℕ → List ℕ → Bool) (e0 : ℕ) (ws : List ℕ)
    (h2 : 2 ≤ ws.length) (h : ws.length ≤ 7 → nodeg P m L W K O G nx e0 ws = true) :
    d0 P m L W K O G g nx e0 ws = true := by
  rcases ws with _ | ⟨a, _ | ⟨b, t⟩⟩
  · simp at h2
  · simp at h2
  · change d1 P m L W K O G g nx e0 a (b :: t) = true
    exact d1_true P m L W K O G g nx e0 a b t h

def optimized (P m L W K O G g k : ℕ) : ℕ → List ℕ → Bool :=
  Nat.rec (fun _ ws => d0 P m L W K O G g (fun _ _ => false) 0 ws)
    (fun _ nx e ws => d0 P m L W K O G g nx e ws) k

def optq (P m L W K O G g q i k : ℕ) (e : ℕ) (ws : List ℕ) : Bool :=
  d0 P m L W K O G g (fun e l => cond (Nat.beq (Nat.mod (l.headD 0) q) i)
    (optimized P m L W K O G g k e l) false) e ws

theorem step_complete {P g : ℕ} (hP : 0 < P) (hg : ∀ i, i < P → differs P i g) (k : ℕ)
    (next : ℕ → List ℕ → Bool) (ws : List ℕ) (extra : ℕ) (hn : ws.Nodup)
    (hb : ∀ w ∈ ws, w < 2 ^ (P + P)) (room : extra + ws.length = k + 1 + 1)
    (a b z : ℕ) (needed : Finset ℕ) (ha : a ∈ ws.toFinset) (hbm : b ∈ ws.toFinset) (hab : a ≠ b)
    (hz : z ∈ bops a b) (hout : z ∉ ws.toFinset) (hs : ws.toFinset = insert a (insert b needed))
    (tail : live bops g k (insert z needed))
    (ih : ∀ (kept : List ℕ), (z :: kept).Nodup → (∀ w ∈ z :: kept, w < 2 ^ (P + P)) →
      live bops g k (z :: kept).toFinset → kept.length ≤ k → next (k - kept.length) (z :: kept) = true) :
    d0 P (2 ^ P - 1) (P + P) (2 ^ (P + P)) (pkf (P + P) 21 fun _ => 2 ^ P - 1)
      (pkf (P + P) 21 fun _ => 1) (pkf (P + P) 21 fun _ => 2 ^ P) g next extra ws = true := by
  have hzl : z < 2 ^ (P + P) := by
    have h1 := hb a (List.mem_toFinset.mp ha)
    have h2 := hb b (List.mem_toFinset.mp hbm)
    have h3 := hz
    simp only [bops, ops, List.mem_toFinset, List.mem_cons, List.not_mem_nil, or_false] at h3
    rcases h3 with rfl | rfl | rfl | rfl
    exacts [bo_A.lt h1 h2, bo_O.lt h1 h2, bo_X.lt h1 h2, bo_Y.lt h1 h2]
  obtain ⟨r, hm, hp⟩ := pick_two (List.mem_toFinset.mp ha) (List.mem_toFinset.mp hbm) hab
  have h2 : 2 ≤ ws.length := by
    have := hp.length_eq
    simp only [List.length_cons] at this
    omega
  apply d0_true _ _ _ _ _ _ _ _ _ _ _ h2
  intro h8
  have goz {a b : ℕ} (perm : ws.Perm (a :: b :: r)) (hmem : (a, b, r) ∈ pairs ws)
      (hset : ws.toFinset = insert a (insert b needed)) (hop : z ∈ bops a b) :
      nodeg P (2 ^ P - 1) (P + P) (2 ^ (P + P)) (pkf (P + P) 21 fun _ => 2 ^ P - 1)
        (pkf (P + P) 21 fun _ => 1) (pkf (P + P) 21 fun _ => 2 ^ P) next extra ws = true := by
    obtain ⟨kept, hk, hnk, hfin⟩ := recover_kept perm hn hset
    have hznew : z ∉ kept := by
      intro hu
      apply hout
      rw [hset]
      exact Finset.mem_insert_of_mem (Finset.mem_insert_of_mem (hfin ▸ (List.mem_toFinset.mpr hu)))
    have hnd : (z :: kept).Nodup := List.nodup_cons.mpr ⟨hznew, hnk⟩
    have hl : live bops g k (z :: kept).toFinset := by
      simpa [hfin] using tail
    have hc := live_card hl
    rw [List.toFinset_card_of_nodup hnd, List.length_cons] at hc
    have len := perm.length_eq
    simp only [List.length_cons] at len
    have hbk : ∀ w ∈ z :: kept, w < 2 ^ (P + P) := by
      intro w hw
      rcases List.mem_cons.mp hw with rfl | hw
      · exact hzl
      · have : w ∈ needed := hfin ▸ List.mem_toFinset.mpr hw
        have h5 : w ∈ ws.toFinset := by
          rw [hset]; exact Finset.mem_insert_of_mem (Finset.mem_insert_of_mem this)
        exact hb w (List.mem_toFinset.mp h5)
    exact nodeg_complete hP next hb hmem h8 hop hk (by omega) (by omega) (cuts_full hg hl)
      (ih kept hnd hbk hl (by omega))
  rcases hm with direct | swap
  · exact goz hp direct hs hz
  · exact goz (hp.trans (.swap _ _ _)) swap (by rw [hs, Finset.insert_comm]) (ops_swap a b ▸ hz)

theorem optimized_complete {P g : ℕ} (hP : 0 < P) (hg : ∀ i, i < P → differs P i g) (n : ℕ) (ws : List ℕ)
    (extra : ℕ) (hn : ws.Nodup) (hb : ∀ w ∈ ws, w < 2 ^ (P + P))
    (room : extra + ws.length = n + 1) (h : live bops g n ws.toFinset) :
    optimized P (2 ^ P - 1) (P + P) (2 ^ (P + P)) (pkf (P + P) 21 fun _ => 2 ^ P - 1)
      (pkf (P + P) 21 fun _ => 1) (pkf (P + P) 21 fun _ => 2 ^ P) g n extra ws = true := by
  induction n generalizing ws extra with
  | zero =>
    rw [singleton_list hn h]
    exact d0_goal P (2 ^ P - 1) (P + P) (2 ^ (P + P)) (pkf (P + P) 21 fun _ => 2 ^ P - 1) (pkf (P + P) 21 fun _ => 1) (pkf (P + P) 21 fun _ => 2 ^ P) g (fun _ _ => false) 0
  | succ k ih =>
    rcases first_live h with done | ⟨a, ha, b, hbm, hab, z, hz, hout, needed, hs, tail⟩
    · rw [singleton_list hn done]
      exact d0_goal P (2 ^ P - 1) (P + P) (2 ^ (P + P)) (pkf (P + P) 21 fun _ => 2 ^ P - 1) (pkf (P + P) 21 fun _ => 1) (pkf (P + P) 21 fun _ => 2 ^ P) g
        (optimized P (2 ^ P - 1) (P + P) (2 ^ (P + P)) (pkf (P + P) 21 fun _ => 2 ^ P - 1) (pkf (P + P) 21 fun _ => 1) (pkf (P + P) 21 fun _ => 2 ^ P) g k) extra
    · exact step_complete hP hg k _ ws extra hn hb room a b z needed ha hbm hab hz hout hs tail
        (fun kept h1 h2 h3 h4 => ih (z :: kept) (k - kept.length) h1 h2
          (by simp only [List.length_cons]; omega) h3)

theorem optq_complete {P g q : ℕ} (hq : 0 < q) (hP : 0 < P) (hg : ∀ i, i < P → differs P i g) (k : ℕ)
    (ws : List ℕ) (extra : ℕ) (hn : ws.Nodup) (hb : ∀ w ∈ ws, w < 2 ^ (P + P))
    (room : extra + ws.length = k + 1 + 1) (h : live bops g (k + 1) ws.toFinset) :
    ∃ i, i < q ∧ optq P (2 ^ P - 1) (P + P) (2 ^ (P + P)) (pkf (P + P) 21 fun _ => 2 ^ P - 1)
      (pkf (P + P) 21 fun _ => 1) (pkf (P + P) 21 fun _ => 2 ^ P) g q i k extra ws = true := by
  rcases first_live h with done | ⟨a, ha, b, hbm, hab, z, hz, hout, needed, hs, tail⟩
  · refine ⟨0, hq, ?_⟩
    rw [singleton_list hn done]
    exact d0_goal P (2 ^ P - 1) (P + P) (2 ^ (P + P)) (pkf (P + P) 21 fun _ => 2 ^ P - 1) (pkf (P + P) 21 fun _ => 1) (pkf (P + P) 21 fun _ => 2 ^ P) g _ extra
  · refine ⟨z % q, Nat.mod_lt _ hq, ?_⟩
    refine step_complete hP hg k _ ws extra hn hb room a b z needed ha hbm hab hz hout hs tail ?_
    intro kept h1 h2 h3 h4
    have e : Nat.beq (Nat.mod ((z :: kept).headD 0) q) (z % q) = true := Nat.beq_refl _
    simp only [e]
    exact optimized_complete hP hg k (z :: kept) (k - kept.length) h1 h2
      (by simp only [List.length_cons]; omega) h3

def search (P m L W K O G g q i k : ℕ) (inputs : List ℕ) : Bool :=
  inputs.sublists.any fun ws => fzl ws fun ws =>
    cond (Nat.ble ws.length (k + 1 + 1)) (cond (Nat.beq (cuts P m ws) m)
      (fz (k + 1 + 1 - ws.length) fun e => optq P m L W K O G g q i k e ws) false) false

theorem search_complete {P g q : ℕ} (hq : 0 < q) (hP : 0 < P) (hg : ∀ i, i < P → differs P i g) (k : ℕ)
    (inputs : List ℕ) (hb : ∀ w ∈ inputs, w < 2 ^ (P + P))
    (hn : inputs.Nodup) (h : build bops g (k + 1) inputs.toFinset) :
    ∃ i, i < q ∧ search P (2 ^ P - 1) (P + P) (2 ^ (P + P)) (pkf (P + P) 21 fun _ => 2 ^ P - 1)
      (pkf (P + P) 21 fun _ => 1) (pkf (P + P) 21 fun _ => 2 ^ P) g q i k inputs = true := by
  classical
  obtain ⟨s, hs, hl⟩ := compress h
  let ws := inputs.filter (· ∈ s)
  have eq : ws.toFinset = s := by
    ext w
    simp only [ws, List.mem_toFinset, List.mem_filter, decide_eq_true_eq, and_iff_right_iff_imp]
    exact fun hw => List.mem_toFinset.mp (hs hw)
  have hnd : ws.Nodup := hn.filter _
  have hl' : live bops g (k + 1) ws.toFinset := eq.symm ▸ hl
  have sz := live_card hl'
  rw [List.toFinset_card_of_nodup hnd] at sz
  obtain ⟨i, hi, ho⟩ := optq_complete hq hP hg k ws (k + 1 + 1 - ws.length) hnd
    (fun w hw => hb w (List.mem_filter.mp hw).1) (by omega) hl'
  refine ⟨i, hi, List.any_eq_true.mpr ⟨ws, List.mem_sublists.mpr (List.filter_sublist ..), ?_⟩⟩
  have h1 : Nat.ble ws.length (k + 1 + 1) = true := Nat.ble_eq.mpr sz
  have h2 : Nat.beq (cuts P (2 ^ P - 1) ws) (2 ^ P - 1) = true := by
    rw [cuts_full hg hl']; exact Nat.beq_refl _
  rw [fzl_eq, h1, h2, fz_eq]
  exact ho
def enc {ρ : Type} (w : ρ → Bool) : List ρ → ℕ
  | [] => 0
  | p :: t => Nat.bit (w p) (enc w t)

theorem enc_testBit {ρ : Type} (w : ρ → Bool) : ∀ (l : List ρ) (j : ℕ),
    (enc w l).testBit j = (l.map w).getD j false
  | [], j => by simp [enc]
  | p :: t, 0 => by simp [enc]
  | p :: t, j + 1 => by simp [enc, Nat.testBit_bit_succ, enc_testBit w t j]

theorem enc_lt {ρ : Type} (w : ρ → Bool) (l : List ρ) : enc w l < 2 ^ l.length := by
  apply Nat.lt_pow_two_of_testBit
  intro i hi
  rw [enc_testBit, List.getD_eq_default _ _ (by simp; omega)]

theorem enc_congr {ρ : Type} {w w' : ρ → Bool} (h : ∀ x, w x = w' x) (l : List ρ) :
    enc w l = enc w' l := by
  have : w = w' := funext h
  rw [this]

theorem enc_false {ρ : Type} (l : List ρ) : enc (fun _ : ρ => false) l = 0 := by
  induction l with
  | nil => rfl
  | cons a t ih => simp [enc, ih]

theorem enc_op {ρ : Type} (o : Bool → Bool → Bool) (o' : ℕ → ℕ → ℕ) (h0 : o false false = false)
    (ho : ∀ a b i, (o' a b).testBit i = o (a.testBit i) (b.testBit i)) (a b : ρ → Bool)
    (l : List ρ) : enc (fun r => o (a r) (b r)) l = o' (enc a l) (enc b l) := by
  apply Nat.eq_of_testBit_eq
  intro j
  rw [ho, enc_testBit, enc_testBit, enc_testBit]
  by_cases h : j < l.length
  · simp [h]
  · rw [List.getD_eq_default _ _ (by simp; omega), List.getD_eq_default _ _ (by simp; omega),
      List.getD_eq_default _ _ (by simp; omega), h0]

section Code
variable {ρ : Type} (x0 : ρ) (pts : List ρ)

def code (w : ρ → Bool) : ℕ := enc (fun x => Bool.xor (w x) (w x0)) pts

theorem code_const (c : Bool) : code x0 pts (fun _ => c) = 0 := by
  unfold code
  rw [← enc_false pts]
  exact enc_congr (fun x => by simp) pts

theorem code_not (w : ρ → Bool) : code x0 pts (fun x => !w x) = code x0 pts w :=
  enc_congr (fun x => by
    show Bool.xor (!w x) (!w x0) = Bool.xor (w x) (w x0)
    cases w x <;> cases w x0 <;> rfl) pts

theorem code_and (a b : ρ → Bool) :
    code x0 pts (fun x => a x && b x) ∈ bops (code x0 pts a) (code x0 pts b) := by
  have e1 := enc_op (ρ := ρ) (fun p q => p && q) (· &&& ·) rfl (fun a b i => Nat.testBit_and a b i)
    (fun x => Bool.xor (a x) (a x0)) (fun x => Bool.xor (b x) (b x0)) pts
  have e2 := enc_op (ρ := ρ) (fun p q => p || q) (· ||| ·) rfl (fun a b i => Nat.testBit_or a b i)
    (fun x => Bool.xor (a x) (a x0)) (fun x => Bool.xor (b x) (b x0)) pts
  have e3 := enc_op (ρ := ρ) (fun p q => Bool.xor p (p && q)) (fun a b => a ^^^ (a &&& b)) rfl
    (fun a b i => by simp [Nat.testBit_and, Nat.testBit_xor])
    (fun x => Bool.xor (a x) (a x0)) (fun x => Bool.xor (b x) (b x0)) pts
  have e4 := enc_op (ρ := ρ) (fun p q => Bool.xor q (p && q)) (fun a b => b ^^^ (a &&& b)) rfl
    (fun a b i => by simp [Nat.testBit_and, Nat.testBit_xor])
    (fun x => Bool.xor (a x) (a x0)) (fun x => Bool.xor (b x) (b x0)) pts
  simp only [bops, ops, List.mem_toFinset, List.mem_cons, List.not_mem_nil, or_false]
  unfold code
  cases ha : a x0 <;> cases hb : b x0
  · left
    rw [ha, hb] at e1
    rw [← e1]
    exact enc_congr (fun x => by simp only [ha, hb]; cases a x <;> cases b x <;> rfl) pts
  · right; right; left
    rw [ha, hb] at e3
    rw [← e3]
    exact enc_congr (fun x => by simp only [ha, hb]; cases a x <;> cases b x <;> rfl) pts
  · right; right; right
    rw [ha, hb] at e4
    rw [← e4]
    exact enc_congr (fun x => by simp only [ha, hb]; cases a x <;> cases b x <;> rfl) pts
  · right; left
    rw [ha, hb] at e2
    rw [← e2]
    exact enc_congr (fun x => by simp only [ha, hb]; cases a x <;> cases b x <;> rfl) pts

theorem bops_zero {b z : ℕ} (hz : z ∈ bops 0 b) : z = 0 ∨ z = b := by
  simp only [bops, ops, List.mem_toFinset, List.mem_cons, List.not_mem_nil, or_false] at hz
  rcases hz with rfl | rfl | rfl | rfl <;> simp

theorem bops_self {b z : ℕ} (hz : z ∈ bops b b) : z = 0 ∨ z = b := by
  simp only [bops, ops, List.mem_toFinset, List.mem_cons, List.not_mem_nil, or_false] at hz
  rcases hz with rfl | rfl | rfl | rfl <;> simp

theorem sim (f : ρ → Bool) (hf : code x0 pts f ≠ 0) : ∀ (t : ℕ) (S : (ρ → Bool) → Prop)
    (A : Finset ℕ), (∀ w, S w → code x0 pts w = 0 ∨ code x0 pts w ∈ A) → Run t S f →
    build bops (code x0 pts f) t A
  | 0, S, A, h, hr => by
    rcases hr with ⟨c, rfl⟩ | hr | hr
    · exact absurd (code_const x0 pts c) hf
    · exact (h f hr).resolve_left hf
    · have := h _ hr
      rw [code_not] at this
      exact this.resolve_left hf
  | t + 1, S, A, h, hr => by
    rcases hr with hr | ⟨a, b, ha, hb, hr⟩
    · exact Or.inl (sim f hf t S A h hr)
    · have hK : ∀ w, K S w → code x0 pts w = 0 ∨ code x0 pts w ∈ A := by
        intro w hw
        rcases hw with ⟨c, rfl⟩ | hw | hw
        · exact Or.inl (code_const x0 pts c)
        · exact h w hw
        · have := h _ hw
          rwa [code_not] at this
      have hmem := code_and x0 pts a b
      by_cases hz : code x0 pts (fun x => a x && b x) = 0 ∨ code x0 pts (fun x => a x && b x) ∈ A
      · refine Or.inl (sim f hf t _ A ?_ hr)
        rintro w (rfl | hw)
        · exact hz
        · exact h w hw
      · have ha' := hK a ha
        have hb' := hK b hb
        have haA : code x0 pts a ∈ A := by
          rcases ha' with h0 | h1
          · rw [h0] at hmem
            rcases bops_zero hmem with e | e
            · exact absurd (Or.inl e) hz
            · exact absurd (e ▸ hb') hz
          · exact h1
        have hbA : code x0 pts b ∈ A := by
          rcases hb' with h0 | h1
          · rw [h0, ops_swap] at hmem
            rcases bops_zero hmem with e | e
            · exact absurd (Or.inl e) hz
            · exact absurd (e ▸ ha') hz
          · exact h1
        have hne : code x0 pts a ≠ code x0 pts b := by
          intro e
          rw [e] at hmem
          rcases bops_self hmem with e2 | e2
          · exact hz (Or.inl e2)
          · exact hz (Or.inr (e2 ▸ hbA))
        refine Or.inr ⟨_, haA, _, hbA, hne, _, hmem, sim f hf t _ _ ?_ hr⟩
        rintro w (rfl | hw)
        · exact Or.inr (Finset.mem_insert_self _ _)
        · exact (h w hw).imp id (fun h => Finset.mem_insert_of_mem h)

end Code

def ptl (n : ℕ) (l : List ℕ) : List (Fin n → Bool) := l.map (pt n)

def ic (n : ℕ) (zs os : List ℕ) : List ℕ :=
  (List.finRange n).map fun i =>
    code (pt n (zs.headD 0)) (ptl n zs ++ ptl n os) fun x : Fin n → Bool => x i

def top (n : ℕ) (f : BF n) (zs os : List ℕ) (q i k : ℕ) : Bool :=
  fz zs.length fun P => fz (Nat.sub (Nat.pow 2 P) 1) fun m => fz (Nat.add P P) fun L =>
  fz (Nat.pow 2 L) fun W => fz (pkf L 21 fun _ => m) fun K => fz (pkf L 21 fun _ => 1) fun O =>
  fz (pkf L 21 fun _ => Nat.pow 2 P) fun G =>
  fzl (((ic n zs os).filter fun c => !Nat.beq c 0).dedup) fun inp =>
  fz (code (pt n (zs.headD 0)) (ptl n zs ++ ptl n os) f) fun g =>
  search P m L W K O G g q i k inp

theorem base {n : ℕ} (f : BF n) (z1 : ℕ) (zt : List ℕ) (os : List ℕ) (q k : ℕ) (hq : 0 < q)
    (hlen : os.length = (z1 :: zt).length)
    (hz : (z1 :: zt).all (fun c => !f (pt n c)) = true)
    (ho : os.all (fun c => f (pt n c)) = true)
    (h : ∀ i, i < q → top n f (z1 :: zt) os q i k = false) : LB f (k + 2) := by
  intro t ht
  by_contra hlt
  have hr := Run_le (show t ≤ k + 1 by omega) ht
  set zs := z1 :: zt with hzs
  set x0 := pt n (zs.headD 0) with hx0
  set pts := ptl n zs ++ ptl n os with hpts
  set P := zs.length with hP
  have hPpos : 0 < P := by simp [hP, hzs]
  have hz' : ∀ c ∈ zs, f (pt n c) = false := by
    intro c hc
    have := List.all_eq_true.mp hz c hc
    simpa using this
  have ho' : ∀ c ∈ os, f (pt n c) = true := fun c hc => List.all_eq_true.mp ho c hc
  have hfx0 : f x0 = false := hz' z1 (by simp [hzs])
  have hbit : ∀ i, i < P → (code x0 pts f).testBit i = false ∧
      (code x0 pts f).testBit (P + i) = true := by
    intro i hi
    have hl1 : i < zs.length := hi
    have hl2 : i < os.length := by omega
    unfold code
    rw [enc_testBit, enc_testBit, hpts, List.map_append]
    constructor
    · rw [List.getD_append _ _ _ _ (by simpa [ptl] using hl1),
        List.getD_eq_getElem _ _ (by simpa [ptl] using hl1)]
      simp [ptl, hfx0, hz' _ (List.getElem_mem hl1)]
    · rw [List.getD_append_right _ _ _ _ (by simp [ptl, hP])]
      have e2 : P + i - (List.map (fun x => f x ^^ f x0) (ptl n zs)).length = i := by
        simp [ptl, hP]
      rw [e2, List.getD_eq_getElem _ _ (by simpa [ptl] using hl2)]
      simp [ptl, hfx0, ho' _ (List.getElem_mem hl2)]
  have hg : ∀ i, i < P → differs P i (code x0 pts f) := by
    intro i hi
    unfold differs
    rw [(hbit i hi).1, (hbit i hi).2]
    decide
  have hne : code x0 pts f ≠ 0 := by
    intro e
    have := (hbit 0 hPpos).2
    rw [e] at this
    simp at this
  have hb := sim x0 pts f hne (k + 1) (Vars n)
    (((ic n zs os).filter fun c => !Nat.beq c 0).dedup).toFinset (by
      rintro w ⟨i, rfl⟩
      by_cases h0 : code x0 pts (fun x => x i) = 0
      · exact Or.inl h0
      · right
        rw [List.mem_toFinset, List.mem_dedup, List.mem_filter]
        refine ⟨List.mem_map.mpr ⟨i, List.mem_finRange i, rfl⟩, ?_⟩
        have : Nat.beq (code x0 pts fun x => x i) 0 = false := by
          cases hb : Nat.beq (code x0 pts fun x => x i) 0
          · rfl
          · exact absurd (Nat.eq_of_beq_eq_true hb) h0
        rw [this]; rfl) hr
  obtain ⟨i, hi, hs⟩ := search_complete hq hPpos hg k _ (by
    intro w hw
    rw [List.mem_dedup, List.mem_filter] at hw
    obtain ⟨j, _, rfl⟩ := List.mem_map.mp hw.1
    have := enc_lt (fun x => Bool.xor (x j) (x0 j)) pts
    have hl : pts.length = P + P := by simp [hpts, ptl, hlen, hP]
    rw [hl] at this
    exact this) (List.nodup_dedup _) hb
  have h1 := h i hi
  simp only [top, fz_eq, fzl_eq] at h1
  exact Bool.noConfusion (h1.symm.trans hs)
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

def v1 : BF 9 := fun x => (x 2 && x 4 && x 6) || (x 1 && x 5 && x 6) || (x 2 && x 3 && x 7) || (x 0 && x 5 && x 7) || (x 1 && x 3 && x 8) || (x 0 && x 4 && x 8)

def v2 : BF 9 := fun x => (x 2 && x 4 && x 6) || (x 1 && x 5 && x 6) || (x 2 && x 3 && x 7) || (x 5 && x 7) || (x 1 && x 3 && x 8) || (x 4 && x 8)

def v3 : BF 9 := fun x => (x 4 && x 6) || (x 1 && x 5 && x 6) || (x 3 && x 7) || (x 5 && x 7) || (x 1 && x 3 && x 8) || (x 4 && x 8)

def v4 : BF 9 := fun x => (x 4 && x 6) || (x 1 && x 5 && x 6) || (x 5 && x 7) || (x 4 && x 8)

def v5 : BF 9 := fun x => (x 4 && x 6) || (x 1 && x 5 && x 6) || (x 5 && x 7)

def v6 : BF 9 := fun x => (x 4 && x 6) || (x 5 && x 6) || (x 5 && x 7)

def v7 : BF 9 := fun x => (x 4 && x 6) || (x 5 && x 6)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v7_lb : LB v7 2 :=
  base v7 0 [0, 0, 16, 16, 16, 32, 32, 32, 48, 48, 48, 64, 64, 64] [80, 96, 112, 80, 96, 112, 80, 96, 112, 80, 96, 112, 80, 96, 112] 1 0 (by decide) (by decide +kernel) (by decide +kernel) (by decide +kernel) (by
    intro i hi
    interval_cases i
    decide +kernel)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v6_7_false : rs v6 7 false = v7 := by funext x; revert x; decide +kernel

def v8 : BF 9 := fun x => (x 5) || (x 4 && x 6)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v8_lb : LB v8 2 :=
  base v8 0 [0, 0, 0, 0, 16, 16, 16, 16, 16, 64, 64, 64, 64, 64] [32, 48, 80, 96, 112, 32, 48, 80, 96, 112, 32, 48, 80, 96, 112] 1 0 (by decide) (by decide +kernel) (by decide +kernel) (by decide +kernel) (by
    intro i hi
    interval_cases i
    decide +kernel)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v6_7_true : rs v6 7 true = v8 := by funext x; revert x; decide +kernel

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v6_lb : LB v6 4 :=
  rule2 v6 7 2 32 0 80 0 32 (by decide +kernel) (by decide +kernel) (by decide +kernel) (v6_7_false.symm ▸ v7_lb) (v6_7_true.symm ▸ v8_lb)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v5_1_true : rs v5 1 true = v6 := by funext x; revert x; decide +kernel

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v5_lb : LB v5 5 :=
  rule1 v5 1 true 4 96 0 80 (by decide +kernel) (by decide +kernel) (v5_1_true.symm ▸ v6_lb)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v4_8_false : rs v4 8 false = v5 := by funext x; revert x; decide +kernel

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v4_lb : LB v4 6 :=
  rule1 v4 8 false 5 16 0 80 (by decide +kernel) (by decide +kernel) (v4_8_false.symm ▸ v5_lb)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v3_3_false : rs v3 3 false = v4 := by funext x; revert x; decide +kernel

def v9 : BF 9 := fun x => (x 4 && x 6) || (x 1 && x 5 && x 6) || (x 7) || (x 1 && x 8) || (x 4 && x 8)

def v10 : BF 9 := fun x => (x 4 && x 6) || (x 1 && x 5 && x 6) || (x 1 && x 8) || (x 4 && x 8)

def v11 : BF 9 := fun x => (x 4 && x 6) || (x 1 && x 8) || (x 4 && x 8)

def v12 : BF 9 := fun x => (x 1 && x 8) || (x 4 && x 8)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v12_lb : LB v12 2 :=
  LB_perm ![1, 4, 7, 2, 5, 8, 0, 3, 6] v12 v7 (by decide +kernel) v7_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v11_6_false : rs v11 6 false = v12 := by funext x; revert x; decide +kernel

def v13 : BF 9 := fun x => (x 4) || (x 1 && x 8)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v13_lb : LB v13 2 :=
  LB_perm ![1, 4, 7, 2, 5, 8, 0, 3, 6] v13 v8 (by decide +kernel) v8_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v11_6_true : rs v11 6 true = v13 := by funext x; revert x; decide +kernel

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v11_lb : LB v11 4 :=
  rule2 v11 6 2 16 0 258 0 16 (by decide +kernel) (by decide +kernel) (by decide +kernel) (v11_6_false.symm ▸ v12_lb) (v11_6_true.symm ▸ v13_lb)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v10_5_false : rs v10 5 false = v11 := by funext x; revert x; decide +kernel

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v10_lb : LB v10 5 :=
  rule1 v10 5 false 4 66 0 80 (by decide +kernel) (by decide +kernel) (v10_5_false.symm ▸ v11_lb)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v9_7_false : rs v9 7 false = v10 := by funext x; revert x; decide +kernel

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v9_lb : LB v9 6 :=
  rule1 v9 7 false 5 0 0 80 (by decide +kernel) (by decide +kernel) (v9_7_false.symm ▸ v10_lb)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v3_3_true : rs v3 3 true = v9 := by funext x; revert x; decide +kernel

def v14 : BF 9 := fun x => (x 1 && x 5 && x 6) || (x 3 && x 7) || (x 5 && x 7) || (x 1 && x 3 && x 8)

def v15 : BF 9 := fun x => (x 1 && x 5 && x 6) || (x 3 && x 7) || (x 5 && x 7)

def v16 : BF 9 := fun x => (x 1 && x 5) || (x 3 && x 7) || (x 5 && x 7)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v16_lb : LB v16 4 :=
  LB_perm ![0, 6, 3, 1, 7, 4, 2, 8, 5] v16 v11 (by decide +kernel) v11_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v15_6_true : rs v15 6 true = v16 := by funext x; revert x; decide +kernel

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v15_lb : LB v15 5 :=
  rule1 v15 6 true 4 34 0 34 (by decide +kernel) (by decide +kernel) (v15_6_true.symm ▸ v16_lb)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v14_8_false : rs v14 8 false = v15 := by funext x; revert x; decide +kernel

def v17 : BF 9 := fun x => (x 1 && x 3) || (x 1 && x 5 && x 6) || (x 3 && x 7) || (x 5 && x 7)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v17_lb : LB v17 5 :=
  LB_perm ![3, 6, 0, 4, 7, 1, 5, 8, 2] v17 v10 (by decide +kernel) v10_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v14_8_true : rs v14 8 true = v17 := by funext x; revert x; decide +kernel

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v14_lb : LB v14 7 :=
  rule2 v14 8 5 10 0 98 0 10 (by decide +kernel) (by decide +kernel) (by decide +kernel) (v14_8_false.symm ▸ v15_lb) (v14_8_true.symm ▸ v17_lb)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v3_4_false : rs v3 4 false = v14 := by funext x; revert x; decide +kernel

def v18 : BF 9 := fun x => (x 4 && x 6) || (x 3 && x 7) || (x 1 && x 3 && x 8) || (x 4 && x 8)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v18_lb : LB v18 6 :=
  LB_perm ![2, 1, 0, 5, 4, 3, 8, 7, 6] v18 v4 (by decide +kernel) v4_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v3_5_false : rs v3 5 false = v18 := by funext x; revert x; decide +kernel

def v19 : BF 9 := fun x => (x 1 && x 6) || (x 4 && x 6) || (x 7) || (x 1 && x 3 && x 8) || (x 4 && x 8)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v19_lb : LB v19 6 :=
  LB_perm ![2, 1, 0, 5, 4, 3, 8, 7, 6] v19 v9 (by decide +kernel) v9_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v3_5_true : rs v3 5 true = v19 := by funext x; revert x; decide +kernel

def v20 : BF 9 := fun x => (x 3 && x 7) || (x 5 && x 7) || (x 1 && x 3 && x 8) || (x 4 && x 8)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v20_lb : LB v20 6 :=
  LB_perm ![0, 1, 2, 6, 7, 8, 3, 4, 5] v20 v4 (by decide +kernel) v4_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v3_6_false : rs v3 6 false = v20 := by funext x; revert x; decide +kernel

def v21 : BF 9 := fun x => (x 4) || (x 1 && x 5) || (x 3 && x 7) || (x 5 && x 7) || (x 1 && x 3 && x 8)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v21_lb : LB v21 6 :=
  LB_perm ![0, 6, 3, 1, 7, 4, 2, 8, 5] v21 v9 (by decide +kernel) v9_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v3_6_true : rs v3 6 true = v21 := by funext x; revert x; decide +kernel

def v22 : BF 9 := fun x => (x 4 && x 6) || (x 1 && x 5 && x 6) || (x 1 && x 3 && x 8) || (x 4 && x 8)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v22_lb : LB v22 7 :=
  LB_perm ![0, 1, 2, 6, 7, 8, 3, 4, 5] v22 v14 (by decide +kernel) v14_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v3_7_false : rs v3 7 false = v22 := by funext x; revert x; decide +kernel

def v23 : BF 9 := fun x => (x 4 && x 6) || (x 1 && x 5 && x 6) || (x 3 && x 7) || (x 5 && x 7)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v23_lb : LB v23 6 :=
  LB_perm ![2, 1, 0, 5, 4, 3, 8, 7, 6] v23 v20 (by decide +kernel) v20_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v3_8_false : rs v3 8 false = v23 := by funext x; revert x; decide +kernel

def v24 : BF 9 := fun x => (x 1 && x 3) || (x 4) || (x 1 && x 5 && x 6) || (x 3 && x 7) || (x 5 && x 7)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v24_lb : LB v24 6 :=
  LB_perm ![3, 6, 0, 4, 7, 1, 5, 8, 2] v24 v9 (by decide +kernel) v9_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v3_8_true : rs v3 8 true = v24 := by funext x; revert x; decide +kernel

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v3_lb : LB v3 9 :=
  rule3B v3 9 (fun i : Fin 9 => ((506 : ℕ).testBit i.val)) (by decide +kernel)
    ⟨1, 3, by decide +kernel⟩ [(3, false, 6), (3, true, 6), (4, false, 7), (5, false, 6), (5, true, 6), (6, false, 6), (6, true, 6), (7, false, 7), (8, false, 6), (8, true, 6)] (by
    intro e he
    simp only [List.mem_cons, List.not_mem_nil, or_false] at he
    rcases he with rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl
    · exact (v3_3_false.symm ▸ v4_lb)
    · exact (v3_3_true.symm ▸ v9_lb)
    · exact (v3_4_false.symm ▸ v14_lb)
    · exact (v3_5_false.symm ▸ v18_lb)
    · exact (v3_5_true.symm ▸ v19_lb)
    · exact (v3_6_false.symm ▸ v20_lb)
    · exact (v3_6_true.symm ▸ v21_lb)
    · exact (v3_7_false.symm ▸ v22_lb)
    · exact (v3_8_false.symm ▸ v23_lb)
    · exact (v3_8_true.symm ▸ v24_lb)) (by decide +kernel)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v2_2_true : rs v2 2 true = v3 := by funext x; revert x; decide +kernel

def v25 : BF 9 := fun x => (x 2 && x 4 && x 6) || (x 1 && x 5 && x 6) || (x 2 && x 7) || (x 5 && x 7) || (x 1 && x 8) || (x 4 && x 8)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v25_lb : LB v25 9 :=
  LB_perm ![0, 3, 6, 2, 5, 8, 1, 4, 7] v25 v3 (by decide +kernel) v3_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v2_3_true : rs v2 3 true = v25 := by funext x; revert x; decide +kernel

def v26 : BF 9 := fun x => (x 1 && x 5 && x 6) || (x 2 && x 3 && x 7) || (x 5 && x 7) || (x 1 && x 3 && x 8)

def v27 : BF 9 := fun x => (x 1 && x 3) || (x 1 && x 5 && x 6) || (x 2 && x 3 && x 7) || (x 5 && x 7)

def v28 : BF 9 := fun x => (x 1 && x 3) || (x 2 && x 3 && x 7) || (x 5 && x 7)

def v29 : BF 9 := fun x => (x 1 && x 3) || (x 3 && x 7) || (x 5 && x 7)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v29_lb : LB v29 4 :=
  LB_perm ![3, 6, 0, 4, 7, 1, 5, 8, 2] v29 v11 (by decide +kernel) v11_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v28_2_true : rs v28 2 true = v29 := by funext x; revert x; decide +kernel

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v28_lb : LB v28 5 :=
  rule1 v28 2 true 4 136 0 10 (by decide +kernel) (by decide +kernel) (v28_2_true.symm ▸ v29_lb)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v27_6_false : rs v27 6 false = v28 := by funext x; revert x; decide +kernel

def v30 : BF 9 := fun x => (x 1 && x 3) || (x 1 && x 5) || (x 2 && x 3 && x 7) || (x 5 && x 7)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v30_lb : LB v30 5 :=
  LB_perm ![0, 3, 6, 1, 4, 7, 2, 5, 8] v30 v17 (by decide +kernel) v17_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v27_6_true : rs v27 6 true = v30 := by funext x; revert x; decide +kernel

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v27_lb : LB v27 7 :=
  rule2 v27 6 5 34 0 10 0 10 (by decide +kernel) (by decide +kernel) (by decide +kernel) (v27_6_false.symm ▸ v28_lb) (v27_6_true.symm ▸ v30_lb)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v26_8_true : rs v26 8 true = v27 := by funext x; revert x; decide +kernel

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v26_lb : LB v26 8 :=
  rule1 v26 8 true 7 10 0 10 (by decide +kernel) (by decide +kernel) (v26_8_true.symm ▸ v27_lb)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v2_4_false : rs v2 4 false = v26 := by funext x; revert x; decide +kernel

def v31 : BF 9 := fun x => (x 2 && x 6) || (x 1 && x 5 && x 6) || (x 2 && x 3 && x 7) || (x 5 && x 7) || (x 8)

def v32 : BF 9 := fun x => (x 2 && x 6) || (x 1 && x 5 && x 6) || (x 2 && x 3 && x 7) || (x 5 && x 7)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v32_lb : LB v32 7 :=
  LB_perm ![0, 2, 1, 6, 8, 7, 3, 5, 4] v32 v27 (by decide +kernel) v27_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v31_8_false : rs v31 8 false = v32 := by funext x; revert x; decide +kernel

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v31_lb : LB v31 8 :=
  rule1 v31 8 false 7 0 0 68 (by decide +kernel) (by decide +kernel) (v31_8_false.symm ▸ v32_lb)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v2_4_true : rs v2 4 true = v31 := by funext x; revert x; decide +kernel

def v33 : BF 9 := fun x => (x 2 && x 4 && x 6) || (x 2 && x 3 && x 7) || (x 1 && x 3 && x 8) || (x 4 && x 8)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v33_lb : LB v33 8 :=
  LB_perm ![0, 2, 1, 3, 5, 4, 6, 8, 7] v33 v26 (by decide +kernel) v26_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v2_5_false : rs v2 5 false = v33 := by funext x; revert x; decide +kernel

def v34 : BF 9 := fun x => (x 1 && x 6) || (x 2 && x 4 && x 6) || (x 7) || (x 1 && x 3 && x 8) || (x 4 && x 8)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v34_lb : LB v34 8 :=
  LB_perm ![0, 2, 1, 3, 5, 4, 6, 8, 7] v34 v31 (by decide +kernel) v31_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v2_5_true : rs v2 5 true = v34 := by funext x; revert x; decide +kernel

def v35 : BF 9 := fun x => (x 2 && x 4) || (x 1 && x 5) || (x 2 && x 3 && x 7) || (x 5 && x 7) || (x 1 && x 3 && x 8) || (x 4 && x 8)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v35_lb : LB v35 9 :=
  LB_perm ![0, 3, 6, 1, 4, 7, 2, 5, 8] v35 v3 (by decide +kernel) v3_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v2_6_true : rs v2 6 true = v35 := by funext x; revert x; decide +kernel

def v36 : BF 9 := fun x => (x 2 && x 4 && x 6) || (x 1 && x 5 && x 6) || (x 1 && x 3 && x 8) || (x 4 && x 8)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v36_lb : LB v36 8 :=
  LB_perm ![0, 3, 6, 1, 4, 7, 2, 5, 8] v36 v33 (by decide +kernel) v33_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v2_7_false : rs v2 7 false = v36 := by funext x; revert x; decide +kernel

def v37 : BF 9 := fun x => (x 2 && x 3) || (x 5) || (x 2 && x 4 && x 6) || (x 1 && x 3 && x 8) || (x 4 && x 8)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v37_lb : LB v37 8 :=
  LB_perm ![0, 3, 6, 1, 4, 7, 2, 5, 8] v37 v34 (by decide +kernel) v34_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v2_7_true : rs v2 7 true = v37 := by funext x; revert x; decide +kernel

def v38 : BF 9 := fun x => (x 2 && x 4 && x 6) || (x 1 && x 5 && x 6) || (x 2 && x 3 && x 7) || (x 5 && x 7)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v38_lb : LB v38 8 :=
  LB_perm ![0, 2, 1, 3, 5, 4, 6, 8, 7] v38 v36 (by decide +kernel) v36_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v2_8_false : rs v2 8 false = v38 := by funext x; revert x; decide +kernel

def v39 : BF 9 := fun x => (x 1 && x 3) || (x 4) || (x 1 && x 5 && x 6) || (x 2 && x 3 && x 7) || (x 5 && x 7)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v39_lb : LB v39 8 :=
  LB_perm ![0, 2, 1, 3, 5, 4, 6, 8, 7] v39 v37 (by decide +kernel) v37_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v2_8_true : rs v2 8 true = v39 := by funext x; revert x; decide +kernel

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v2_lb : LB v2 11 :=
  rule3B v2 11 (fun i : Fin 9 => ((510 : ℕ).testBit i.val)) (by decide +kernel)
    ⟨1, 2, by decide +kernel⟩ [(2, true, 9), (3, true, 9), (4, false, 8), (4, true, 8), (5, false, 8), (5, true, 8), (6, true, 9), (7, false, 8), (7, true, 8), (8, false, 8), (8, true, 8)] (by
    intro e he
    simp only [List.mem_cons, List.not_mem_nil, or_false] at he
    rcases he with rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl
    · exact (v2_2_true.symm ▸ v3_lb)
    · exact (v2_3_true.symm ▸ v25_lb)
    · exact (v2_4_false.symm ▸ v26_lb)
    · exact (v2_4_true.symm ▸ v31_lb)
    · exact (v2_5_false.symm ▸ v33_lb)
    · exact (v2_5_true.symm ▸ v34_lb)
    · exact (v2_6_true.symm ▸ v35_lb)
    · exact (v2_7_false.symm ▸ v36_lb)
    · exact (v2_7_true.symm ▸ v37_lb)
    · exact (v2_8_false.symm ▸ v38_lb)
    · exact (v2_8_true.symm ▸ v39_lb)) (by decide +kernel)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v1_0_true : rs v1 0 true = v2 := by funext x; revert x; decide +kernel

def v40 : BF 9 := fun x => (x 2 && x 4 && x 6) || (x 5 && x 6) || (x 2 && x 3 && x 7) || (x 0 && x 5 && x 7) || (x 3 && x 8) || (x 0 && x 4 && x 8)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v40_lb : LB v40 11 :=
  LB_perm ![1, 0, 2, 4, 3, 5, 7, 6, 8] v40 v2 (by decide +kernel) v2_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v1_1_true : rs v1 1 true = v40 := by funext x; revert x; decide +kernel

def v41 : BF 9 := fun x => (x 4 && x 6) || (x 1 && x 5 && x 6) || (x 3 && x 7) || (x 0 && x 5 && x 7) || (x 1 && x 3 && x 8) || (x 0 && x 4 && x 8)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v41_lb : LB v41 11 :=
  LB_perm ![0, 2, 1, 3, 5, 4, 6, 8, 7] v41 v40 (by decide +kernel) v40_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v1_2_true : rs v1 2 true = v41 := by funext x; revert x; decide +kernel

def v42 : BF 9 := fun x => (x 2 && x 4 && x 6) || (x 1 && x 5 && x 6) || (x 2 && x 7) || (x 0 && x 5 && x 7) || (x 1 && x 8) || (x 0 && x 4 && x 8)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v42_lb : LB v42 11 :=
  LB_perm ![0, 3, 6, 1, 4, 7, 2, 5, 8] v42 v40 (by decide +kernel) v40_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v1_3_true : rs v1 3 true = v42 := by funext x; revert x; decide +kernel

def v43 : BF 9 := fun x => (x 2 && x 6) || (x 1 && x 5 && x 6) || (x 2 && x 3 && x 7) || (x 0 && x 5 && x 7) || (x 0 && x 8) || (x 1 && x 3 && x 8)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v43_lb : LB v43 11 :=
  LB_perm ![1, 0, 2, 4, 3, 5, 7, 6, 8] v43 v42 (by decide +kernel) v42_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v1_4_true : rs v1 4 true = v43 := by funext x; revert x; decide +kernel

def v44 : BF 9 := fun x => (x 2 && x 4) || (x 1 && x 5) || (x 2 && x 3 && x 7) || (x 0 && x 5 && x 7) || (x 1 && x 3 && x 8) || (x 0 && x 4 && x 8)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v44_lb : LB v44 11 :=
  LB_perm ![0, 3, 6, 1, 4, 7, 2, 5, 8] v44 v41 (by decide +kernel) v41_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v1_6_true : rs v1 6 true = v44 := by funext x; revert x; decide +kernel

def v45 : BF 9 := fun x => (x 2 && x 3) || (x 0 && x 5) || (x 2 && x 4 && x 6) || (x 1 && x 5 && x 6) || (x 1 && x 3 && x 8) || (x 0 && x 4 && x 8)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v45_lb : LB v45 11 :=
  LB_perm ![1, 0, 2, 4, 3, 5, 7, 6, 8] v45 v44 (by decide +kernel) v44_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v1_7_true : rs v1 7 true = v45 := by funext x; revert x; decide +kernel

def v46 : BF 9 := fun x => (x 1 && x 3) || (x 0 && x 4) || (x 2 && x 4 && x 6) || (x 1 && x 5 && x 6) || (x 2 && x 3 && x 7) || (x 0 && x 5 && x 7)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v46_lb : LB v46 11 :=
  LB_perm ![0, 2, 1, 3, 5, 4, 6, 8, 7] v46 v45 (by decide +kernel) v45_lb

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v1_8_true : rs v1 8 true = v46 := by funext x; revert x; decide +kernel

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem v1_lb : LB v1 13 :=
  rule3B v1 13 (fun i : Fin 9 => ((511 : ℕ).testBit i.val)) (by decide +kernel)
    ⟨0, 1, by decide +kernel⟩ [(0, true, 11), (1, true, 11), (2, true, 11), (3, true, 11), (4, true, 11), (6, true, 11), (7, true, 11), (8, true, 11)] (by
    intro e he
    simp only [List.mem_cons, List.not_mem_nil, or_false] at he
    rcases he with rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl
    · exact (v1_0_true.symm ▸ v2_lb)
    · exact (v1_1_true.symm ▸ v40_lb)
    · exact (v1_2_true.symm ▸ v41_lb)
    · exact (v1_3_true.symm ▸ v42_lb)
    · exact (v1_4_true.symm ▸ v43_lb)
    · exact (v1_6_true.symm ▸ v44_lb)
    · exact (v1_7_true.symm ▸ v45_lb)
    · exact (v1_8_true.symm ▸ v46_lb)) (by decide +kernel)

set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem target_eq : ∀ x : Fin 9 → Bool, ((x 0 && x 4 && x 8) || (x 0 && x 5 && x 7) || (x 1 && x 3 && x 8) || (x 1 && x 5 && x 6) || (x 2 && x 3 && x 7) || (x 2 && x 4 && x 6)) = v1 x := by decide +kernel

theorem pm3_lower (C : Circuit) (fan : PEqualNP.MetaComplexity.FanInTwo C)
    (correct : ∀ x : Fin 9 → Bool, C.eval (List.ofFn x) = ((x 0 && x 4 && x 8) || (x 0 && x 5 && x 7) || (x 1 && x 3 && x 8) || (x 1 && x 5 && x 6) || (x 2 && x 3 && x 7) || (x 2 && x 4 && x 6))) : 13 ≤ C.size := by
  have hc := bound_of_LB v1 13 v1_lb C.gates C.output
    (fun g hg => by simpa only [legal, Set.mem_insert_iff, Set.mem_singleton_iff] using fan g hg)
    (fun x => (correct x).trans (target_eq x))
  have le := List.length_filter_le isBinary C.gates
  change 13 ≤ C.gates.length
  unfold bc at hc
  omega

end PEqualNP.Outside.L_meta_27460

theorem PEqualNP.Outside.L_meta_27460 : (¬ (∃ C : PEqualNP.CircuitLowerBounds.Circuit,
    PEqualNP.MetaComplexity.FanInTwo C ∧ C.size ≤ 12 ∧
    (∀ x : Fin 9 → Bool, C.eval (List.ofFn x) = ((x 0 && x 4 && x 8) || (x 0 && x 5 && x 7) || (x 1 && x 3 && x 8) || (x 1 && x 5 && x 6) || (x 2 && x 3 && x 7) || (x 2 && x 4 && x 6))) ∧
    C.output + 1 = 9 + C.size ∧
    (∀ j : Fin C.gates.length,
      ((C.gates.get j).op = PEqualNP.CircuitLowerBounds.GateOp.not ∧
          ∃ a, a < 9 + j.val ∧ (C.gates.get j).inputs = [a]) ∨
      (((C.gates.get j).op = PEqualNP.CircuitLowerBounds.GateOp.and ∨
          (C.gates.get j).op = PEqualNP.CircuitLowerBounds.GateOp.or) ∧
          ∃ a b, a < b ∧ b < 9 + j.val ∧ (C.gates.get j).inputs = [a, b])) ∧
    (∀ j : Fin C.gates.length,
      (∃ x y : Fin 9 → Bool,
        (C.wires (List.ofFn x)).getD (9 + j.val) false ≠ (C.wires (List.ofFn y)).getD (9 + j.val) false) ∧
      ∀ k, k < 9 + j.val → ∃ x : Fin 9 → Bool,
        (C.wires (List.ofFn x)).getD (9 + j.val) false ≠ (C.wires (List.ofFn x)).getD k false) ∧
    (∀ j : Fin C.gates.length, j.val + 1 < C.gates.length →
      ∃ k : Fin C.gates.length, j.val < k.val ∧ 9 + j.val ∈ (C.gates.get k).inputs) ∧
    C.gates.head? = some ⟨PEqualNP.CircuitLowerBounds.GateOp.and, [0, 4]⟩ ∧
    C.gates.tail.head? = some ⟨PEqualNP.CircuitLowerBounds.GateOp.or, [2, 9]⟩)) := by
  rintro ⟨C, fan, small, computes, _⟩
  have large := PEqualNP.Outside.L_meta_27460.pm3_lower C fan computes
  omega

"""C7 unique OR reading two raw inputs: exact negative shape adapter."""
import hashlib,json,re,sys
from pathlib import Path
from functools import lru_cache

HERE=Path(__file__).resolve().parent

def checked(name,digest):
    b=(HERE/name).read_bytes()
    if hashlib.sha256(b).hexdigest()!=digest:raise ValueError("template hash mismatch")
    return b.decode()

helpers=checked("helpers.lean","dae5e878fb81f4dff0c83a081d30b20b5b26b7c0e30353ccae11ebf7b11a3cbf")
shape=json.loads(checked("shape.json","ee77009b61dc6c7dd763208b4b23f0ca22c528040e8874ec5e93f488512b5f31"))
lemma=r"""
lemma agree (C : Circuit) (i : Fin C.gates.length) (a : ℕ)
    (ha : a < 7) (hu : ∀ j : Fin C.gates.length, 0 ∈ (C.gates.get j).inputs → j = i)
    (hop : (C.gates.get i).op = GateOp.or)
    (hm : a ∈ (C.gates.get i).inputs)
    (x y : List Bool) (hx : x.length = 7) (hy : y.length = 7)
    (haX : x.getD a false = true) (haY : y.getD a false = true)
    (he : ∀ w, w ≠ 0 → x.getD w false = y.getD w false) :
    ∀ w, w ≠ 0 → (C.wires x).getD w false = (C.wires y).getD w false := by
  obtain ⟨preX, recX, bigX⟩ := fold_spec C.gates x
  obtain ⟨preY, recY, bigY⟩ := fold_spec C.gates y
  rw [hx] at recX bigX
  rw [hy] at recY bigY
  intro w
  induction w using Nat.strong_induction_on with
  | _ w ih =>
    intro hw0
    rw [wires_eq, wires_eq]
    by_cases hw : w < 7
    · rw [preX w (by omega), preY w (by omega)]
      exact he w hw0
    obtain ⟨q, rfl⟩ : ∃ q, w = 7 + q := ⟨w - 7, by omega⟩
    by_cases hq : q < C.gates.length
    · let j : Fin C.gates.length := ⟨q,hq⟩
      have hg : C.gates[q]? = some (C.gates.get j) := List.getElem?_eq_getElem hq
      have hX := recX q _ hg
      have hY := recY q _ hg
      rw [hX, hY]
      by_cases hzero : 0 ∈ (C.gates.get j).inputs
      · have hj := hu j hzero
        rw [hj, hop]
        have hax : (if a < 7 + q then (C.gates.foldl stp x).getD a false else false) = true := by
          rw [if_pos (by omega), preX a (by omega), haX]
        have hay : (if a < 7 + q then (C.gates.foldl stp y).getD a false else false) = true := by
          rw [if_pos (by omega), preY a (by omega), haY]
        have ex : ((C.gates.get i).inputs.map (fun h => if h < 7 + q then (C.gates.foldl stp x).getD h false else false)).any id = true :=
          List.any_eq_true.mpr ⟨true, List.mem_map.mpr ⟨a, hm, hax⟩, rfl⟩
        have ey : ((C.gates.get i).inputs.map (fun h => if h < 7 + q then (C.gates.foldl stp y).getD h false else false)).any id = true :=
          List.any_eq_true.mpr ⟨true, List.mem_map.mpr ⟨a, hm, hay⟩, rfl⟩
        simp only [GateOp.eval, ex, ey]
      · congr 1
        apply List.map_congr_left
        intro h hh
        by_cases hlt : h < 7 + q
        · simp only [if_pos hlt]
          have hn : h ≠ 0 := fun h0 => hzero (h0 ▸ hh)
          simpa only [wires_eq] using ih h hlt hn
        · simp [hlt]
    · rw [bigX _ (by omega), bigY _ (by omega)]
"""

@lru_cache(maxsize=1)
def pattern():
    pat=re.escape(' '.join(shape.split()))
    pat=pat.replace(re.escape('i.val = 0'),r'i\.val\ =\ (?P<idx>[0-8])',1)
    pat=pat.replace(re.escape('2 ∈ (C.gates.get i).inputs ∧ 2 ≠ 0 ∧ 2 < 7 + i.val'),r'(?P<a>[2-5])\ ∈\ \(C\.gates\.get\ i\)\.inputs\ ∧\ (?P=a)\ ≠\ 0\ ∧\ (?P=a)\ <\ 7\ \+\ i\.val')
    pat=pat.replace(re.escape('getD 2 false = true'),r'getD\ (?P=a)\ false\ =\ true')
    pat=re.compile(pat)
    return pat

def matches(s):return pattern().fullmatch(" ".join(s.split())) is not None

def generate(gid,s):
    if not re.fullmatch(r"L-meta-[0-9]+",gid):return None
    m=pattern().fullmatch(" ".join(s.split()))
    if not m:return None
    a=int(m["a"]);b=6 if a==2 else 1
    mod="PEqualNP.Outside."+gid.replace("-","_")
    tail=f"""
theorem {mod} : {s} := by
  rintro ⟨C, i, k, hi, hfan, hsize, heval, h0, hu, hop, hkop, hik, hw, hm, _⟩
  let x : Fin 7 → Bool := fun j => decide (j.val = {a} ∨ j.val = {b})
  let y : Fin 7 → Bool := fun j => decide (j.val = 0 ∨ j.val = {a} ∨ j.val = {b})
  let z : Fin 7 → Bool := fun j => decide (j.val = 0)
  have hz : C.output ≠ 0 := by
    intro h
    have e : C.eval (List.ofFn z) = false := (heval z).trans (by decide)
    have hpre := ({mod}.fold_spec C.gates (List.ofFn z)).1 0 (by simp)
    rw [PEqualNP.CircuitLowerBounds.Circuit.eval, h, {mod}.wires_eq, hpre] at e
    have htrue : (List.ofFn z).getD 0 false = true := by decide
    rw [htrue] at e
    contradiction
  have hxy : ∀ w, w ≠ 0 → (List.ofFn x).getD w false = (List.ofFn y).getD w false := by
    intro w hw
    by_cases h : w < 7
    · interval_cases w <;> first | contradiction | decide
    · rw [{mod}.getD_out _ _ (by simpa using Nat.le_of_not_gt h),
          {mod}.getD_out _ _ (by simpa using Nat.le_of_not_gt h)]
  have e := {mod}.agree C i {a} (by decide) hu hop hm (List.ofFn x) (List.ofFn y)
    (by simp) (by simp) (by decide) (by decide) hxy C.output hz
  have ex := heval x
  have ey := heval y
  change C.eval (List.ofFn x) = C.eval (List.ofFn y) at e
  have xf : C.eval (List.ofFn x) = false := ex.trans (by decide)
  have yt : C.eval (List.ofFn y) = true := ey.trans (by decide)
  rw [xf, yt] at e
  contradiction
"""
    text='import PEqualNP.Defs\nimport Mathlib\n\n-- Fold semantics adapted from merged L-lib-787, Apache-2.0.\nnamespace '+mod+'\n'+helpers+lemma+'\nend '+mod+'\n\n'+tail

    return text

def main():
    gid,sf,out=sys.argv[1:]
    text=generate(gid,Path(sf).read_text())
    if text is None:return 3
    Path(out).write_text(text)
    return 0

if __name__=="__main__":sys.exit(main())

"""Reusable Lean reflection kernel for binary monotone circuits."""

TEMPLATE = """abbrev Dnf := List (List Nat)
def value (x : List Bool) (d : Dnf) : Bool :=
  d.any (fun t => t.all (fun i => x.getD i false))

def conjunction (a b : Dnf) : Dnf :=
  a.flatMap (fun u => b.map (fun v => u ++ v))

lemma value_prefix (x : List Bool) (u : List Nat) (b : Dnf) :
    value x (b.map (fun v => u ++ v)) =
      (u.all (fun i => x.getD i false) && value x b) := by
  induction b with
  | nil => simp [value]
  | cons v vs ih =>
    simp only [List.map_cons, value, List.any_cons, List.all_append] at *
    rw [ih, Bool.and_or_distrib_left]

lemma value_append (x : List Bool) (a b : Dnf) :
    value x (a ++ b) = (value x a || value x b) := by
  simp [value,List.any_append]

lemma value_cons (x : List Bool) (u : List Nat) (a : Dnf) :
    value x (u :: a) = (u.all (fun i => x.getD i false) || value x a) := rfl

lemma value_conjunction (x : List Bool) (a b : Dnf) :
    value x (conjunction a b) = (value x a && value x b) := by
  induction a with
  | nil => simp [conjunction,value]
  | cons u us ih =>
    change value x (b.map (fun v => u ++ v) ++ conjunction us b) = _
    rw [value_append, value_prefix x u b, ih, value_cons, Bool.and_or_distrib_right]

lemma value_getD (x : List Bool) (ds : List Dnf) (i : Nat) :
    (ds.map (value x)).getD i false = value x (ds.getD i []) := by
  simp only [List.getD_eq_getElem?_getD,List.getElem?_map]
  cases ds[i]? <;> rfl

abbrev Op := Bool × Nat × Nat
def gate (g : Op) : Gate :=
  ⟨if g.1 then GateOp.and else GateOp.or,[g.2.1,g.2.2]⟩
def dstep (ds : List Dnf) (g : Op) : List Dnf :=
  ds ++ [if g.1 then conjunction (ds.getD g.2.1 []) (ds.getD g.2.2 [])
         else ds.getD g.2.1 [] ++ ds.getD g.2.2 []]

def bstep (w : List Bool) (g : Gate) : List Bool :=
  w ++ [g.op.eval (g.inputs.map fun i => w.getD i false)]

lemma value_step (x : List Bool) (ds : List Dnf) (g : Op) :
    (dstep ds g).map (value x) = bstep (ds.map (value x)) (gate g) := by
  rcases g with ⟨b,i,j⟩
  cases b <;> simp only [dstep,bstep,gate,Bool.false_eq_true,ite_false,ite_true,
    List.map_append,List.map_cons,List.map_nil,GateOp.eval,List.any_cons,List.any_nil,
    List.all_cons,List.all_nil,id,Bool.or_false,Bool.and_true,value_getD,value_append,value_conjunction]

lemma value_fold (x : List Bool) (ds : List Dnf) (gs : List Op) :
    (gs.foldl dstep ds).map (value x) =
      (gs.map gate).foldl bstep (ds.map (value x)) := by
  induction gs generalizing ds with
  | nil => rfl
  | cons g gs ih => simp only [List.foldl_cons,List.map_cons,ih,value_step]

def inputs (n : Nat) : List Dnf := List.ofFn (fun i : Fin n => [[i.val]])

lemma value_inputs {n : Nat} (x : Fin n → Bool) :
    (inputs n).map (value (List.ofFn x)) = List.ofFn x := by
  simp only [inputs,List.map_ofFn]
  congr 1
  funext i
  simp [value,List.getD_eq_getElem?_getD]

lemma sound {n : Nat} (x : Fin n → Bool) (gs : List Op) (out : Nat) :
    (Circuit.mk (gs.map gate) out).eval (List.ofFn x) =
      value (List.ofFn x) ((gs.foldl dstep (inputs n)).getD out []) := by
  change ((gs.map gate).foldl bstep (List.ofFn x)).getD out false = _
  have h := value_fold (List.ofFn x) (inputs n) gs
  rw [value_inputs x] at h
  rw [← h]
  exact value_getD _ _ _
lemma value_pairs {n : Nat} (x : Fin n → Bool) (l : List (Fin n × Fin n)) :
    value (List.ofFn x) (l.map (fun e => [e.1.val,e.2.val])) =
      l.any (fun e => x e.1 && x e.2) := by
  induction l with
  | nil => rfl
  | cons e es ih =>
    change (value (List.ofFn x) ([e.1.val,e.2.val] :: es.map (fun e => [e.1.val,e.2.val]))) = _
    rw [value_cons, ih]
    simp [List.getD_eq_getElem?_getD]

def orderPair {n : Nat} (e : Fin n × Fin n) :=
  if e.1 ≤ e.2 then e else (e.2,e.1)

lemma value_ordered {n : Nat} (x : Fin n → Bool) (l : List (Fin n × Fin n)) :
    (l.map orderPair).any (fun e => x e.1 && x e.2) =
      l.any (fun e => x e.1 && x e.2) := by
  induction l with
  | nil => rfl
  | cons e es ih =>
    simp only [List.map_cons,List.any_cons,ih,orderPair]
    split <;> simp [Bool.and_comm]

lemma any_perm (α : Type) (L R : List α) (p : α → Bool) :
    L.Perm R → L.any p = R.any p := by
  intro hp
  induction hp with
  | nil => rfl
  | cons _ _ ih => simp only [List.any_cons,ih]
  | swap _ _ _ => simp only [List.any_cons, Bool.or_left_comm]
  | trans _ _ ih₁ ih₂ => exact ih₁.trans ih₂

lemma monotone (gs : List Op) (out : Nat) :
    PEqualNP.MetaComplexity.Monotone2 (Circuit.mk (gs.map gate) out) := by
  intro g hg
  obtain ⟨t,ht,rfl⟩ := List.mem_map.mp hg
  rcases t with ⟨b,i,j⟩
  cases b <;> simp [gate]
"""

def data(z,ordered):
    from .certificate import dnf,lean_list
    D=dnf(z)
    R=[tuple(sorted(e)) for e in ordered]
    if sorted(tuple(sorted(e)) for e in D)!=sorted(R):
        raise ValueError("reflection requires exactly one occurrence of each target edge")
    ops="["+ ", ".join("("+("true" if op=="and" else "false")+", "+str(a)+", "+str(b)+")" for op,a,b in z["gates"])+"]"
    return ops,lean_list(D),lean_list(R)

def definitions(z,ordered):
    ops,pairs,target=data(z,ordered)
    n=z["n"];out=z["output"]
    return f"""def ops : List Op := {ops}
def pairs : List (Fin {n} × Fin {n}) := {pairs}
def target : List (Fin {n} × Fin {n}) := {target}
def witness : Circuit := ⟨ops.map gate, {out}⟩
"""

def eval_proof(z,ordered):
    n=z["n"];out=z["output"]
    swaps=", ".join(f"Bool.and_comm (x {u}) (x {v})" for u,v in ordered if u>v)
    extra=", "+swaps if swaps else ""
    return f"""by
  change (Circuit.mk (ops.map gate) {out}).eval (List.ofFn x) = _
  rw [sound]
  have h : (ops.foldl dstep (inputs {n})).getD {out} [] =
      pairs.map (fun e => [e.1.val,e.2.val]) := by decide
  rw [h,value_pairs,← value_ordered]
  have hp : (pairs.map orderPair).Perm target := by decide
  rw [any_perm _ _ _ _ hp]
  simp (config := {{maxSteps := 2000000}}) [target,Bool.or_assoc{extra}]
"""

OPTIONS="set_option maxHeartbeats 4000000 in\nset_option maxRecDepth 10000 in\n"

def parts(z,ordered,rhs,aux):
    n=z["n"];out=z["output"]
    code="namespace "+aux+"\nopen PEqualNP.CircuitLowerBounds\n"
    code+=TEMPLATE+"\n"+definitions(z,ordered)+"\n"+OPTIONS
    code+=f"lemma eval_witness (x : Fin {n} → Bool) : witness.eval (List.ofFn x) = ({rhs}) :=\n"+eval_proof(z,ordered)
    code+=f"\nlemma wf : PEqualNP.MetaComplexity.Monotone2 witness := monotone ops {out}\nend {aux}\n\n"
    body=f"by\n  exact ⟨{aux}.witness,{aux}.wf,by decide,{aux}.eval_witness⟩"
    return code,body

def render(meta,z,ordered,rhs):
    module=meta["module"];aux=module+"_aux"
    imports=["Mathlib"]+[m for m in meta["imports"] if m!="Mathlib"]
    helpers,body=parts(z,ordered,rhs,aux)
    return "\n".join("import "+m for m in imports)+"\n\n"+helpers+OPTIONS+f"theorem {module} : {meta['statement']} := "+body+"\n"

MARKER="-- viche-reflected-star-v1\n"

def artifact(z):
    import json
    # Only computational data, not arbitrary injected Lean declarations.
    return MARKER+json.dumps({"n":z["n"],"gates":z["gates"],"output":z["output"]},separators=(",",":"))+"\n"

def unpack(text,statement,aux):
    import json
    from . import certificate,star
    z=json.loads(text[len(MARKER):])
    if not isinstance(z,dict) or set(z)!={"n","gates","output"}:
        raise ValueError("invalid reflected proof artifact")
    parsed=certificate.parse(statement)
    if not parsed:raise ValueError("unsupported reflected proof statement")
    n,bound,ordered,edges,rhs=parsed
    if z["n"]!=n or len(z["gates"])>bound:
        raise ValueError("reflected proof does not fit exact obligation")
    if star.verify(n,edges,z["gates"],z["output"])["status"]!="verified":
        raise ValueError("invalid reflected circuit")
    return parts(z,ordered,rhs,aux)

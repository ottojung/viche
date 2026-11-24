"""Lean proof certificates for edge-owned star constructions.

Semantic checking uses exact symbolic antichains. Lean proof generation
uses a permutation of concrete edges instead of an exponential truth table.
"""
import argparse
import json
from pathlib import Path
import re

from . import star
from .. import validate
from ..proofs import synthesis

NS="PEqualNP.CircuitLowerBounds."
PERM_BODY="""by
  intro α L R p h
  induction h with
  | nil => rfl
  | cons a h ih => simp only [List.any_cons, ih]
  | swap a b l => simp only [List.any_cons]; cases p a <;> cases p b <;> rfl
  | trans h1 h2 ih1 ih2 => exact ih1.trans ih2"""
PERM_TYPE="∀ (α : Type) (L R : List α) (p : α → Bool), L.Perm R → L.any p = R.any p"

def dnf(z):
    """Exact ordered DNF of the star circuit; no absorption/reordering."""
    w=[[(i,)] for i in range(z["n"])]
    for op,a,b in z["gates"]:
        if op=="or":w.append(w[a]+w[b])
        else:
            if len(w[a])*len(w[b])>10000:raise ValueError("DNF expansion too large")
            w.append([u+v for u in w[a] for v in w[b]])
    result=w[z["output"]]
    if any(len(t)!=2 for t in result):raise ValueError("not an edge-owned star construction")
    return result

def lean_list(edges):
    return "["+", ".join("("+str(a)+", "+str(b)+")" for a,b in edges)+"]"

def expr(edges):
    return " || ".join(f"(x {a} && x {b})" for a,b in edges)

def eval_body(z,ordered,permutation="any_perm"):
    n=z["n"];D=dnf(z)
    L=[tuple(sorted(e)) for e in D];R=[tuple(sorted(e)) for e in ordered]
    if sorted(L)!=sorted(R):
        raise ValueError("certificate requires each target edge exactly once")
    swaps=", ".join(f"Bool.and_comm (x {u}) (x {v})" for u,v in D if u>v)
    reverse=", ".join(f"Bool.and_comm (x {u}) (x {v})" for u,v in ordered if u>v)
    left_extra=", "+swaps if swaps else ""
    right_extra=", "+reverse if reverse else ""
    return f"""by
  intro x
  let L : List (Fin {n} × Fin {n}) := {lean_list(L)}
  let R : List (Fin {n} × Fin {n}) := {lean_list(R)}
  have hp : L.Perm R := by decide
  calc
    _ = L.any (fun e => x e.1 && x e.2) := by
      simp [witness, L, {NS}Circuit.eval, {NS}Circuit.wires,
        {NS}GateOp.eval, List.ofFn_succ, Bool.and_or_distrib_left,
        Bool.and_or_distrib_right, Bool.or_assoc{left_extra}]
    _ = R.any (fun e => x e.1 && x e.2) := {permutation} _ L R _ hp
    _ = _ := by simp [R, Bool.or_assoc{right_extra}]
"""

def parse(statement):
    m=synthesis.SHAPE.fullmatch(statement.strip())
    if not m:return None
    n,bound,rhs=int(m[2]),int(m[1]),m[3]
    if not 2<=n<=256:return None
    E=synthesis.EDGE
    if not re.fullmatch(r"[()\s]*"+E.pattern+r"(?:[()\s]*\|\|[()\s]*"+E.pattern+r")*[()\s]*",rhs):return None
    ordered=[(int(a),int(b)) for a,b in E.findall(rhs)]
    try:edges=star.normalize(n,ordered)
    except ValueError:return None
    if len(edges)!=len(ordered):return None
    return n,bound,ordered,edges,rhs

def render(meta,seconds=5):
    parsed=parse(meta["statement"])
    if not parsed:return {"status":"unsupported"}
    n,bound,ordered,edges,rhs=parsed
    z=star.synthesize(n,edges,seconds)
    ver=star.verify(n,edges,z["gates"],z["output"])
    info={"status":"generated","n":n,"gates":len(z["gates"]),"bound":bound,"verification":ver,"certificate":z}
    if ver["status"]!="verified" or len(z["gates"])>bound:
        return dict(info,status="no_witness_within_bound")
    mod=meta["module"];aux=mod+"_aux"
    imports=["Mathlib"]+[m for m in meta["imports"] if m!="Mathlib"]
    gs=", ".join("⟨"+NS+"GateOp."+op+", ["+str(a)+", "+str(b)+"]⟩" for op,a,b in z["gates"])
    code="\n".join("import "+m for m in imports)+"\n\nnamespace "+aux+"\n\n"
    code+="lemma any_perm : "+PERM_TYPE+" := "+PERM_BODY+"\n\n"
    code+="def witness : "+NS+"Circuit := ⟨["+gs+"], "+str(z["output"])+"⟩\n\n"
    code+="set_option maxHeartbeats 4000000 in\nset_option maxRecDepth 10000 in\n"
    code+="lemma eval_witness : ∀ x : Fin "+str(n)+" → Bool, witness.eval (List.ofFn x) = ("+rhs+") :=\n"
    code+=eval_body(z,ordered)+"\n"
    code+="lemma wf : PEqualNP.MetaComplexity.Monotone2 witness := by\n"
    code+="  intro g hg\n  simp only [witness, List.mem_cons, List.not_mem_nil, or_false] at hg\n"
    code+="  rcases hg with "+" | ".join("rfl" for _ in z["gates"])+" <;> simp\n"
    code+="\nend "+aux+"\n\ntheorem "+mod+" : "+meta["statement"]+" := by\n"
    code+="  exact ⟨"+aux+".witness, "+aux+".wf, by decide, "+aux+".eval_witness⟩\n"
    validate.validate(meta,code.encode())
    return dict(info,candidate=code)

def graph_meta(graph,module="PEqualNP.Outside.VicheStarCertificate"):
    n=graph["n"];edges=sorted(star.normalize(n,graph["edges"]))
    bound=graph.get("bound",len(edges)+n-1)
    statement=f"∃ C : {NS}Circuit, PEqualNP.MetaComplexity.Monotone2 C ∧ C.size ≤ {bound} ∧ ∀ x : Fin {n} → Bool, C.eval (List.ofFn x) = (fun x : Fin {n} → Bool => {expr(edges)}) x"
    return {"id":"L-meta-0","module":module,"file":"lean/"+module.replace(".","/")+".lean",
            "statement":statement,"imports":["PEqualNP.Defs"]}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("graph",nargs="?",help="graph JSON; omit in a bound workspace for exact lease")
    p.add_argument("--output",required=True)
    p.add_argument("--seconds",type=float,default=5)
    a=p.parse_args()
    if a.graph:
        meta=graph_meta(json.loads(Path(a.graph).read_text()))
    else:
        from .obligations import binding
        r,w,b=binding()
        meta={"id":r["gap_id"],"module":r["module"],"file":r["path"],"statement":r["statement"],"imports":r["imports"]}
    out=render(meta,a.seconds)
    candidate=out.pop("candidate",None)
    if candidate:
        with Path(a.output).open("x") as f:f.write(candidate)
        out["path"]=str(Path(a.output).resolve())
    print(json.dumps(out,indent=2))
    return 0 if candidate else 1
if __name__=="__main__":raise SystemExit(main())

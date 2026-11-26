#!/usr/bin/env python3
"""Graph-edge monotone circuit-witness generator.

Statement shapes (desk corpus):
  * edge-list: `C.eval (List.ofFn x) = true ↔ ∃ u v, (u.val,v.val) ∈ [(pairs)] ∧ ...`
  * explicit DNF: `C.eval (List.ofFn x) = (x a && x b) || ...`
Method: solve a bounded vertex-cover decision problem and emit the corresponding star circuit.
For explicit DNF, the evaluation certificate uses separate Boolean inputs rather than enumerating
functions on Fin n. Search and kernel enumeration are capped; refusal is not a lower bound.
Exit 3 when the cover exceeds the bound or the shape is not recognised.
"""
import re
import sys

PREFIX = re.escape("∃ C : PEqualNP.CircuitLowerBounds.Circuit, PEqualNP.MetaComplexity.Monotone2 C ∧ C.size ≤ ")
DNF = re.compile(PREFIX + r"(\d+) ∧ ∀ x : Fin (\d+) → Bool, C\.eval \(List\.ofFn x\) = (.+)")
EDGE = re.compile(PREFIX + r"(\d+) ∧ \(∀ x : Fin (\d+) → Bool, \(C\.eval \(List\.ofFn x\) = true ↔ ∃ u v : Fin \2, \(u\.val, v\.val\) ∈ \(\[([0-9, ()]+)\] : List \(ℕ × ℕ\)\) ∧ x u = true ∧ x v = true\)\)")


def parse(stmt):
    stmt = " ".join(stmt.split())
    m = EDGE.fullmatch(stmt)
    rhs = None
    if m:
        bound, n = map(int,m.group(1,2))
        pairs = m[3]
        if not re.fullmatch(r"\(\d+, *\d+\)(?:, *\(\d+, *\d+\))*",pairs):
            return None
        edges = [tuple(map(int,t)) for t in re.findall(r"\((\d+), *(\d+)\)",pairs)]
        # Until a scalable existential certificate is installed, keep
        # finite enumeration strictly bounded.
        if n > 10:
            return None
    else:
        m = DNF.fullmatch(stmt)
        if not m:
            return None
        bound,n = map(int,m.group(1,2))
        rhs = m[3]
        fn = re.fullmatch(r"\(fun x : Fin "+str(n)+r" → Bool => (.*)\) x",rhs)
        if fn:
            rhs = fn[1]
        # Parentheses around the entire disjunction are allowed; each
        # disjunct must have exactly two positive input variables.
        terms = rhs.split("||")
        edges=[]
        for t in terms:
            mm=re.fullmatch(r"[ (]*x (\d+) && x (\d+)[ )]*",t.strip())
            if not mm:
                return None
            edges.append(tuple(map(int,mm.group(1,2))))
        if n > 12:
            return None
    if not edges or any(a >= n or b >= n or a==b for a,b in edges):
        return None
    return n,bound,sorted(set(tuple(sorted(e)) for e in edges)),rhs


def matches(stmt):
    return parse(stmt) is not None


def star_cover(n, edges, bound):
    from functools import lru_cache
    budget=bound-len(edges)+1
    if budget<1:
        return None
    @lru_cache(maxsize=20000)
    def cover(es,k):
        if not es:
            return ()
        if not k:
            return None
        degree={}
        for a,b in es:
            degree[a]=degree.get(a,0)+1
            degree[b]=degree.get(b,0)+1
        used=set()
        matching=0
        for a,b in es:
            if a not in used and b not in used:
                used.update((a,b));matching+=1
        if matching>k:
            return None
        a,b=max(es,key=lambda e:degree[e[0]]+degree[e[1]])
        for v in sorted((a,b),key=lambda v:-degree[v]):
            tail=cover(tuple(e for e in es if v not in e),k-1)
            if tail is not None:
                return (v,)+tail
        return None
    chosen=cover(tuple(edges),budget)
    if chosen is None:
        return None
    remaining=set(edges);stars=[]
    for u in chosen:
        nb=sorted({b if a==u else a for a,b in remaining if u in (a,b)})
        if nb:
            stars.append((u,nb))
            remaining={e for e in remaining if u not in e}
    assert not remaining
    gates,wires=[],[]
    for u,nb in stars:
        w=nb[0]
        for v in nb[1:]:
            gates.append(('or',w,v));w=n+len(gates)-1
        gates.append(('and',u,w));wires.append(n+len(gates)-1)
    w=wires[0]
    for v in wires[1:]:
        gates.append(('or',w,v));w=n+len(gates)-1
    assert len(gates)<=bound
    return gates


def emit(gid, statement, n, gates, rhs):
    num = re.fullmatch(r"L-meta-(\d+)",gid).group(1)
    mod = "PEqualNP.Outside.L_meta_" + num
    ns=mod+"_aux"
    gs = ", ".join("⟨GateOp.%s, [%d, %d]⟩" % (op,a,b) for op,a,b in gates)
    names=" ".join("b%d"%i for i in range(n))
    bank=", ".join("b%d"%i for i in range(n))
    args=", ".join("x %d"%i for i in range(n))
    call=" ".join("(x %d)"%i for i in range(n))
    helper=""
    proof="  · decide +kernel"
    if rhs is not None:
        expr=re.sub(r"\bx (\d+)",lambda m:"b"+m[1],rhs)
        helper=f"set_option maxRecDepth 100000 in\nset_option maxHeartbeats 20000000 in\nlemma eval_bool : ∀ {names} : Bool, c.eval [{bank}] = ({expr}) := by decide +kernel"
        proof=f"  · intro x\n    have h : List.ofFn x = [{args}] := by simp [List.ofFn_succ]\n    rw [h]\n    exact eval_bool {call}"
    return f"""import Mathlib
import PEqualNP.Defs

namespace {ns}
open PEqualNP.CircuitLowerBounds
def c : Circuit := ⟨[{gs}], {n+len(gates)-1}⟩

{helper}

lemma wf : PEqualNP.MetaComplexity.Monotone2 c := by
  intro g hg
  simp only [c, List.mem_cons, List.not_mem_nil, or_false] at hg
  rcases hg with {" | ".join(["rfl"]*len(gates))} <;> simp
end {ns}
open {ns}
set_option maxRecDepth 100000 in
set_option maxHeartbeats 20000000 in
theorem {mod} : {statement} := by
  refine ⟨c, wf, ?_, ?_⟩
  · decide
{proof}
"""


def main():
    if len(sys.argv) != 4:
        sys.exit(2)
    gid, sf, out = sys.argv[1:4]
    statement = open(sf).read().strip()
    parsed = parse(statement)
    if parsed is None:
        print("unrecognised edge-cover statement", file=sys.stderr); sys.exit(3)
    n, bound, edges, rhs = parsed
    gates = star_cover(n, edges, bound)
    if gates is None:
        print("star cover exceeds bound %d" % bound, file=sys.stderr); sys.exit(3)
    open(out, "w").write(emit(gid, statement, n, gates, rhs))
    sys.exit(0)


if __name__ == "__main__":
    main()

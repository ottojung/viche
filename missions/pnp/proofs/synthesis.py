"""Deterministic small graph edge-function circuit synthesis."""
import itertools
import re

from .circuit import EDGE

SHAPE = re.compile(
    r"∃ C : PEqualNP\.CircuitLowerBounds\.Circuit, PEqualNP\.MetaComplexity\.Monotone2 C ∧ C\.size ≤ (\d+) ∧ ∀ x : Fin (\d+) → Bool, C\.eval \(List\.ofFn x\) = \(fun x : Fin \2 → Bool => (.*)\) x", re.S)


def parse(statement):
    m = SHAPE.fullmatch(statement.strip())
    if not m:
        return None
    bound,n,rhs = int(m[1]),int(m[2]),m[3]
    if not 2 <= n <= 12:
        return None
    if not re.fullmatch(r"[()\s]*" + EDGE.pattern + r"(?:[()\s]*\|\|[()\s]*" + EDGE.pattern + r")*[()\s]*", rhs):
        return None
    edges = {tuple(sorted((int(a),int(b)))) for a,b in EDGE.findall(rhs)}
    if not edges or any(a == b or b >= n for a,b in edges):
        return None
    return n,bound,edges


def synthesize(n, edges):
    """Cover edges by stars or complete bipartite blocks; share OR subexpressions."""
    neighbors = {i:{b if a == i else a for a,b in edges if i in (a,b)}
                 for i in range(n)}
    blocks = set()
    for i in range(n):
        if neighbors[i]:
            blocks.add(((i,),tuple(sorted(neighbors[i]))))
    for k in range(2,min(4,n)+1):
        for left in itertools.combinations(range(n),k):
            right = set.intersection(*(neighbors[i] for i in left))
            if right:
                blocks.add((left,tuple(sorted(right))))
    blocks = sorted(blocks)
    best = None
    for strategy in range(3):
        gates, memo, remaining, outputs = [], {}, set(edges), []
        def gate(op,a,b):
            key = op,*sorted((a,b))
            if key not in memo:
                memo[key] = n+len(gates)
                gates.append(key)
            return memo[key]
        def disjoin(xs):
            xs = list(xs)
            result = xs[0]
            for x in xs[1:]:
                result = gate("or",result,x)
            return result
        while remaining:
            choices = []
            for a,b in blocks:
                covered = {tuple(sorted((u,v))) for u in a for v in b} & remaining
                if not covered:
                    continue
                cost = len(a)+len(b)
                rank = (len(covered)/cost,len(covered)) if strategy == 0 else (
                    (len(covered),-cost) if strategy == 1 else (len(covered)-cost,-cost))
                choices.append((rank,a,b,covered))
            _,a,b,covered = max(choices,key=lambda t:(t[0],t[1],t[2]))
            outputs.append(gate("and",disjoin(a),disjoin(b)))
            remaining -= covered
        output = disjoin(outputs)
        if best is None or len(gates)<len(best[0]):
            best = gates,output
    return best


def verify(n,edges,gates,output):
    for mask in range(1<<n):
        w = [bool(mask & (1<<i)) for i in range(n)]
        for op,a,b in gates:
            if not (0 <= a < len(w) and 0 <= b < len(w)):
                return False
            w.append(w[a] and w[b] if op=="and" else w[a] or w[b])
        if w[output] != any(w[a] and w[b] for a,b in edges):
            return False
    return True


def candidate(meta):
    from .. import validate
    parsed = parse(meta["statement"])
    if not parsed:
        return None
    n,bound,edges = parsed
    gates,out = synthesize(n,edges)
    report = {"gates":len(gates),"bound":bound,"cases":1<<n,"candidate":None}
    if len(gates)>bound or not verify(n,edges,gates,out):
        return report
    mod = meta["module"]
    imports = ["Mathlib"]+[m for m in meta["imports"] if m!="Mathlib"]
    prefix = "\n".join("import "+m for m in imports)
    gs = ", ".join("⟨PEqualNP.CircuitLowerBounds.GateOp."+op+", ["+str(a)+", "+str(b)+"]⟩" for op,a,b in gates)
    text = prefix+"\n\nnamespace "+mod+"\ndef witness : PEqualNP.CircuitLowerBounds.Circuit := ⟨["+gs+"], "+str(out)+"⟩\n"
    text += "lemma wf : PEqualNP.MetaComplexity.Monotone2 witness := by\n  intro g hg\n  simp only [witness, List.mem_cons, List.not_mem_nil, or_false] at hg\n  rcases hg with "+" | ".join("rfl" for _ in gates)+" <;> simp\n"
    variables = ["b"+str(i) for i in range(n)]
    rhs = re.sub(r"\bx (\d+)\b", lambda m: variables[int(m[1])], SHAPE.fullmatch(meta["statement"].strip())[3])
    text += "set_option maxRecDepth 100000 in\nset_option maxHeartbeats 0 in\n"
    text += "lemma truth : ∀ "+" ".join(variables)+" : Bool, witness.eval ["+", ".join(variables)+"] = ("+rhs+") := by\n  decide\n"
    text += "end "+mod+"\n\ntheorem "+mod+" : "+meta["statement"]+" := by\n"
    text += "  refine ⟨"+mod+".witness, "+mod+".wf, by decide, ?_⟩\n  intro x\n  simp only [List.ofFn_succ, List.ofFn_zero]\n"
    text += "  exact "+mod+".truth "+" ".join("(x "+str(i)+")" for i in range(n))+"\n"
    # Never describe the generated candidate as Lean-checked.
    validate.validate(meta,text.encode())
    report["candidate"]=text
    return report

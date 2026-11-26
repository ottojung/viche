#!/usr/bin/env python3
"""Exact small truth-table circuit witness synthesis with bounded SAT.

Try deterministic monotone factorization and the one-inversion decomposition
first. Then use a bounded SAT decision query for an AND/OR/NOT circuit.
Independently evaluate every returned circuit on every input assignment.
A search refusal is not a mathematical negative result.
"""
from functools import lru_cache
import re
import sys
import threading

PREFIX = re.escape("∃ C : PEqualNP.CircuitLowerBounds.Circuit, PEqualNP.MetaComplexity.")
NOT = re.escape("FanInTwo C ∧ (∃ g ∈ C.gates, g.op = PEqualNP.CircuitLowerBounds.GateOp.not ∧ g.inputs.length = 1)")
PATTERN = re.compile(PREFIX + r"(?P<kind>Monotone2 C|" + NOT + r") ∧ C.size ≤ (?P<k>\d+) ∧ ∀ x : Fin (?P<n>\d+) → Bool, C.eval \(List.ofFn x\) = Nat.testBit (?P<tab>0x[0-9a-fA-F]+|\d+|\(\d+ \* 2 \^ 32 \+ \d+\)) \(∑ i : Fin (?P=n), if x i then 2 \^ \(i : ℕ\) else 0\)")


def parse(text):
    m = PATTERN.fullmatch(" ".join(text.split()))
    if not m:
        return None
    n, k = int(m["n"]), int(m["k"])
    if not (1 <= n <= 6 and 1 <= k <= 12):
        return None
    raw = m["tab"]
    if raw.startswith("("):
        hi,lo = map(int,re.fullmatch(r"\((\d+) \* 2 \^ 32 \+ (\d+)\)",raw).groups())
        table = (hi << 32) + lo
    else:
        table = int(raw,16 if raw.startswith("0x") else 10)
    return n,k,table & ((1 << (1 << n))-1),m["kind"] != "Monotone2 C"


def matches(text):
    return parse(text) is not None


def eval_table(n,gates,out):
    full=(1 << (1<<n))-1
    wires=[sum(1<<r for r in range(1<<n) if r>>i&1) for i in range(n)]
    for op,a,b in gates:
        x=wires[a] if a is not None else full if op=="and" else 0
        y=wires[b] if b is not None else full if op=="and" else 0
        wires.append(x&y if op=="and" else x|y if op=="or" else full^x)
    return wires[out]


def nodes(e):
    if isinstance(e,int):
        return frozenset()
    return frozenset({e}) | frozenset().union(*(nodes(x) for x in e[1:]))


def combine(op,a,b):
    # Constants are distinct from input indices (tagged tuples).
    identity=("and",) if op=="and" else ("or",)
    absorbing=("or",) if op=="and" else ("and",)
    if a==identity:return b
    if b==identity:return a
    if a==absorbing or b==absorbing:return absorbing
    if a==b:return a
    return (op,*sorted((a,b),key=repr))


def minimum_terms(points):
    out=[]
    for x in sorted(set(points),key=lambda x:(x.bit_count(),x)):
        if not any(y&x==y for y in out):
            out.append(x)
    return tuple(sorted(out))


@lru_cache(maxsize=50000)
def factor(terms):
    if not terms:return ("or",)
    if 0 in terms:return ("and",)
    if len(terms)==1:
        e=("and",);m=terms[0]
        while m:
            b=m&-m;m^=b;e=combine("and",e,b.bit_length()-1)
        return e
    best=None
    union=0
    for m in terms:union|=m
    while union:
        b=union&-union;union^=b
        yes=tuple(m^b for m in terms if m&b)
        no=tuple(m for m in terms if not m&b)
        e=combine("or",combine("and",b.bit_length()-1,factor(minimum_terms(yes))),factor(minimum_terms(no)))
        if best is None or len(nodes(e))<len(nodes(best)):
            best=e
    return best


def circuit(n,e,require_not):
    gates=[];seen={}
    def make(e):
        if isinstance(e,int):return e
        if e not in seen:
            args=[make(x) for x in e[1:]]
            seen[e]=n+len(gates)
            gates.append((e[0],*(args+[None,None])[:2]))
        return seen[e]
    out=make(e)
    if require_not and not any(g[0]=="not" for g in gates):
        gates.append(("not",0,None))
    return gates,out


def monotone(n,points):
    return factor(minimum_terms(points))


def heuristic(n,k,table,require_not):
    universe=range(1<<n)
    yes=[r for r in universe if table>>r&1]
    up=lambda xs:[r for r in universe if any(x&r==x for x in xs)]
    if not require_not:
        e=monotone(n,yes)
    else:
        # Upward closure of first true, then first drop, then first recovery.
        # If there is a second drop the audit rejects this decomposition.
        a=up(yes)
        b=up([r for r in a if not table>>r&1])
        c=up([r for r in b if table>>r&1])
        e=combine("or",combine("and",monotone(n,a),("not",monotone(n,b))),monotone(n,c))
    gates,out=circuit(n,e,require_not)
    if len(gates)<=k and eval_table(n,gates,out)==table:
        return gates,out
    return None


def synth_sat(n,k,table,require_not,seconds=30):
    try:
        from pysat.solvers import Minisat22
        from pysat.card import CardEnc, EncType
    except ImportError:return None
    counter=0;clauses=[]
    def new():
        nonlocal counter
        counter+=1;return counter
    def one(xs):
        nonlocal counter
        z=CardEnc.equals(lits=xs,bound=1,top_id=counter,encoding=EncType.seqcounter)
        counter=max(counter,z.nv);clauses.extend(z.clauses)
    ops=[];left=[];right=[]
    for i in range(k):
        op=[new() for _ in range(3 if require_not else 2)]
        l=[new() for _ in range(n+i)]
        r=[new() for _ in range(n+i)]
        one(op);one(l);one(r)
        ops.append(op);left.append(l);right.append(r)
        for a in range(n+i):
            for b in range(a):
                # commutative binary gates: one canonical order
                clauses.extend([[-op[j],-l[a],-r[b]] for j in (0,1)])
        if require_not:
            clauses.append([-op[2],r[0]])
    if require_not:
        nots=[op[2] for op in ops];clauses.append(nots)
        # The likely family uses one NOT; this is a witness search, not a
        # completeness claim. Avoid wasting time on extra inversion gates.
        for i in range(k):
            for j in range(i):clauses.append([-nots[i],-nots[j]])
    for row in range(1<<n):
        values=[new() for _ in range(k)]
        for i in range(k):
            a,b=new(),new();z=values[i]
            for sels,x in ((left[i],a),(right[i],b)):
                for j,s in enumerate(sels):
                    if j<n:
                        clauses.append([-s,x if row>>j&1 else -x])
                    else:
                        y=values[j-n];clauses.extend([[-s,-x,y],[-s,x,-y]])
            u,v=ops[i][:2]
            clauses.extend([[-u,-z,a],[-u,-z,b],[-u,z,-a,-b],
                            [-v,z,-a],[-v,z,-b],[-v,-z,a,b]])
            if require_not:
                w=ops[i][2];clauses.extend([[-w,z,a],[-w,-z,-a]])
        clauses.append([values[-1] if table>>row&1 else -values[-1]])
    with Minisat22(bootstrap_with=clauses) as solver:
        solver.conf_budget(150000)
        timer=threading.Timer(seconds,solver.interrupt);timer.start()
        try:
            if solver.solve_limited(expect_interrupt=True) is not True:return None
            m=set(solver.get_model())
        finally:
            timer.cancel();timer.join()
    gates=[]
    for op,l,r in zip(ops,left,right):
        o=("and","or","not")[next(i for i,x in enumerate(op) if x in m)]
        a=next(i for i,x in enumerate(l) if x in m)
        b=next(i for i,x in enumerate(r) if x in m)
        gates.append((o,a,None if o=="not" else b))
    out=n+k-1
    return (gates,out) if eval_table(n,gates,out)==table else None


def emit(gid,statement,n,k,require_not,gates,out):
    num=re.fullmatch(r"L-meta-(\d+)",gid).group(1)
    mod="PEqualNP.Outside.L_meta_"+num
    ns=mod+"_aux"
    gs=", ".join("⟨GateOp.%s, [%s]⟩"%(op,", ".join(str(x) for x in (a,b) if x is not None)) for op,a,b in gates)
    if require_not:
        notwire=next(a for op,a,b in gates if op=="not")
        intro=f"  · refine ⟨⟨GateOp.not, [{notwire}]⟩, ?_, by rfl, by rfl⟩\n    simp [witness]\n"
        pred="FanInTwo"
        holes="⟨witness, ?_, ?_, ?_, ?_⟩"
    else:
        intro=""
        pred="Monotone2"
        holes="⟨witness, ?_, ?_, ?_⟩"
    return f"""import Mathlib
import PEqualNP.Defs

namespace {ns}
open PEqualNP.CircuitLowerBounds
def witness : Circuit := ⟨[{gs}], {out}⟩
end {ns}

open {ns} PEqualNP.CircuitLowerBounds

set_option maxRecDepth 100000 in
set_option maxHeartbeats 20000000 in
theorem {mod} : {statement} := by
  refine {holes}
  · simp [PEqualNP.MetaComplexity.{pred}, witness]
{intro}  · decide
  · decide +kernel
"""


def main():
    if len(sys.argv)!=4:return 2
    gid,sf,out=sys.argv[1:4]
    stmt=open(sf).read().strip();p=parse(stmt)
    if not p:return 3
    n,k,table,require_not=p
    found=heuristic(n,k,table,require_not) or synth_sat(n,k,table,require_not)
    if not found:
        print("no circuit witness within bounded search",file=sys.stderr);return 3
    gates,wire=found
    assert len(gates)<=k and eval_table(n,gates,wire)==table
    open(out,"w").write(emit(gid,stmt,n,k,require_not,gates,wire))
    return 0

if __name__=="__main__":sys.exit(main())

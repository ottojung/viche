#!/usr/bin/env python3
"""Witness synthesis on oneEach and two-lit promises, not full truth tables.

Learned proof shape from public L-meta-19175, L-meta-21192 and L-meta-21449
(Apache-2.0). Only target assignments are encoded. Every circuit is audited
independently before emitting a Lean certificate for the exact statement.
Search failure is unknown, not a lower bound.
"""
from functools import lru_cache
import itertools
import random
import re
import sys
import threading
import time

REP = "PEqualNP.Represents."
MC = "PEqualNP.MetaComplexity."
CIR = "PEqualNP.CircuitLowerBounds.Circuit"
PREFIX = re.escape("∃ C : " + CIR + ", " + MC)
PRED = r"(FanInTwo|Monotone2) C ∧ C.size ≤ (\d+) ∧ "
MATRIX = r"\(fun (?:u v : Fin (\d+)|\(u : Fin (\d+)\) \(v : Fin (\d+)\)) => \((\d+) : ℕ\)\.testBit \((\d+) \* u.val \+ v.val\)\)"
MONO = re.compile(re.escape(REP+"RepSizeAtMost ") + MATRIX + r" (\d+)")
GENERAL = re.compile(PREFIX + PRED + re.escape(REP+"Represents ") + MATRIX + r" C")
TWO = re.compile(PREFIX + PRED + r"∀ i j : Fin (\d+), C.eval \(List.ofFn fun k : Fin \3 => decide \(k = i ∨ k = j\)\) = \((\d+) : ℕ\)\.testBit \(\3 \* min i.val j.val \+ max i.val j.val\)")


def parse(s):
    s = " ".join(s.split())
    m = MONO.fullmatch(s)
    pred = "Monotone2"
    if m:
        a,b,c,mask,stride,k = m.groups()
    else:
        m = GENERAL.fullmatch(s)
        if m:
            pred,k,a,b,c,mask,stride = m.groups()
        else:
            m = TWO.fullmatch(s)
            if not m:
                return None
            pred,k,n,mask = m.groups()
            n,k,mask = int(n),int(k),int(mask)
            if not 1 <= n <= 10 or not 0 <= k <= 40:
                return None
            return ("two",n,n,k,mask,pred)
    nr,nc = (int(a),int(a)) if a else (int(b),int(c))
    k,mask = int(k),int(mask)
    if not (1 <= nr <= 10 and 1 <= nc <= 10 and int(stride)==nc and 0 <= k <= 64):
        return None
    return ("matrix",nr,nc,k,mask,pred)


def matches(s):
    return parse(s) is not None


def domain(problem):
    kind,n,m,k,mask,pred=problem
    if kind=="matrix":
        rows=[(1<<i)|(1<<(n+j)) for i in range(n) for j in range(m)]
        return n+m,rows,mask&((1<<len(rows))-1)
    pairs=list(itertools.combinations_with_replacement(range(n),2))
    return n,[(1<<i)|(1<<j) for i,j in pairs],sum(((mask>>(n*i+j))&1)<<r for r,(i,j) in enumerate(pairs))


def input_tables(n,rows):
    return [sum(((row>>i)&1)<<r for r,row in enumerate(rows)) for i in range(n)]


def evaluate(n,rows,gates,out):
    """Independent per-row evaluation; enforce topology and allowed arities."""
    result=0
    for r,row in enumerate(rows):
        w=[bool(row>>i&1) for i in range(n)]
        for op,args in gates:
            assert all(0<=i<len(w) for i in args)
            assert len(args)<=2 and op in ("and","or","not")
            if op=="not":assert len(args)==1
            bits=[w[i] for i in args]
            w.append(all(bits) if op=="and" else any(bits) if op=="or" else not bits[0])
        result|=int(w[out] if 0<=out<len(w) else False)<<r
    return result


def valid(problem, solution):
    n,rows,target=domain(problem)
    gates,out=solution
    return len(gates)<=problem[3] and (problem[-1]=="FanInTwo" or all(op!="not" for op,_ in gates)) and evaluate(n,rows,gates,out)==target


def combine(op,a,b):
    if a==b:return a
    return (op,*sorted((a,b),key=repr))


def join(op,terms):
    terms=list(dict.fromkeys(terms))
    if not terms:return (op,)
    x=terms[0]
    for y in terms[1:]:x=combine(op,x,y)
    return x


def compile_expr(n,expr):
    gates=[];seen={}
    def wire(e):
        if isinstance(e,int):return e
        if e not in seen:
            a=[wire(x) for x in e[1:]]
            seen[e]=n+len(gates)
            gates.append((e[0],a))
        return seen[e]
    out=wire(expr)
    return gates,out


def rect_expr(n,m,mask,rng,transpose=False):
    """Cover a binary matrix by all-ones rectangles; score by gate cost."""
    if transpose:
        return remap(rect_expr(m,n,sum(((mask>>(i*m+j))&1)<<(j*n+i) for i in range(n) for j in range(m)),rng),n,m)
    rows=[(mask>>(i*m))&((1<<m)-1) for i in range(n)]
    boxes=[]
    for r in range(1,1<<n):
        c=(1<<m)-1
        for i in range(n):
            if r>>i&1:c&=rows[i]
        if not c:continue
        b=sum(c<<(i*m) for i in range(n) if r>>i&1)
        e=combine("and",join("or",[i for i in range(n) if r>>i&1]),join("or",[n+j for j in range(m) if c>>j&1]))
        boxes.append((b,e,r.bit_count()+c.bit_count()-1))
    # Greedy weighted cover, then prune redundant rectangles. A random jitter
    # explores alternative factorizations deterministically per instance.
    left=mask;chosen=[]
    while left:
        b,e,c=max(boxes,key=lambda a:((a[0]&left).bit_count()/(a[2]+1)*rng.uniform(.85,1.15)))
        if not b&left:return ("or",)
        chosen.append((b,e));left&=~b
    for i in range(len(chosen)-1,-1,-1):
        cover=0
        for j,(b,_) in enumerate(chosen):
            if i!=j:cover|=b
        if cover==mask:chosen.pop(i)
    return join("or",[e for _,e in chosen])


def remap(e,n,m):
    if isinstance(e,int):return e+n if e<m else e-m
    return (e[0],*(remap(x,n,m) for x in e[1:]))


def grouped(n,m,mask,transpose=False):
    if transpose:
        return remap(grouped(m,n,sum(((mask>>(i*m+j))&1)<<(j*n+i) for i in range(n) for j in range(m))),n,m)
    groups={}
    for i in range(n):
        c=(mask>>(i*m))&((1<<m)-1)
        if c:groups.setdefault(c,[]).append(i)
    return join("or",[combine("and",join("or",us),join("or",[n+j for j in range(m) if c>>j&1])) for c,us in groups.items()])


def term_cover(n,rows,target,allow_not,rng):
    """Minimize a DNF on the promise: generate safe conjunctions of literals."""
    values=input_tables(n,rows);full=(1<<len(rows))-1
    lits=[(v,i) for i,v in enumerate(values)]
    if allow_not:lits += [(full^v,("not",i)) for i,v in enumerate(values)]
    terms={}
    for count in range(1,4 if allow_not else 3):
        for combo in itertools.combinations(lits,count):
            b=full
            for v,_ in combo:b&=v
            if b and not b&~target:
                e=join("and",[x for _,x in combo])
                cost=len(compile_expr(n,e)[0])
                if b not in terms or cost<terms[b][1]:terms[b]=(e,cost)
    left=target;chosen=[]
    while left:
        if not terms:return None
        b,(e,c)=max(terms.items(),key=lambda x:(x[0]&left).bit_count()/(x[1][1]+1)*rng.uniform(.8,1.2))
        if not b&left:return None
        chosen.append((b,e));left&=~b
    return join("or",[e for _,e in chosen])


def shared_unions(sets):
    """Compute several ORs together, extracting shared input pairs."""
    remaining=[set(x) for x in sets]
    while True:
        counts={}
        for xs in remaining:
            for a,b in itertools.combinations(sorted(xs,key=repr),2):
                counts[a,b]=counts.get((a,b),0)+1
        if not counts:break
        pair,c=max(counts.items(),key=lambda x:(x[1],repr(x[0])))
        if c<2:break
        a,b=pair;v=combine("or",a,b)
        for xs in remaining:
            if a in xs and b in xs:
                xs.remove(a);xs.remove(b);xs.add(v)
    return [join("or",sorted(xs,key=repr)) for xs in remaining]


def matrix_shared(n,m,mask,transpose=False,dual=False):
    if transpose:
        t=sum(((mask>>(i*m+j))&1)<<(j*n+i) for i in range(n) for j in range(m))
        return remap(matrix_shared(m,n,t,False,dual),n,m)
    groups={};terms=[]
    for i in range(n):
        col=tuple(n+j for j in range(m) if ((mask>>(i*m+j))&1)==(0 if dual else 1))
        if col:groups.setdefault(col,[]).append(i)
    cols=list(groups)
    if dual:
        # Exclude each all-zero rectangle via its positive one-hot complement.
        left=[set(range(n))-set(groups[c]) for c in cols]
        right=[set(range(n,n+m))-set(c) for c in cols]
        unions=shared_unions([a|b for a,b in zip(left,right)])
        return join("and",unions)
    unions=shared_unions(cols)
    for c,u in zip(cols,unions):
        left=join("or",groups[c])
        # A full side is true on the promise and costs zero here.
        terms.append(left if len(c)==m else u if len(groups[c])==n else combine("and",left,u))
    return join("or",terms)


def two_order(problem, seconds=.5):
    """Incremental corrections on one-hot-or-zero residual inputs.

    When adding input i to an existing circuit on a subset, only the
    singleton i and pairs i,j need correction. On these rows, a condition
    on earlier inputs is an OR of selected bits or its negation. Explore
    orders and both default values, preserving exact bitset semantics.
    """
    n,rows,target=domain(problem);k=problem[3];allow=problem[-1]=="FanInTwo"
    if problem[0]!="two":return None
    lookup={row:bool(target>>r&1) for r,row in enumerate(rows)}
    fullrows=[0]+rows;full=(1<<len(fullrows))-1
    tabs=input_tables(n,fullrows)
    rng=random.Random(problem[4]^991)
    orders=[tuple(range(n)),tuple(reversed(range(n)))]
    # Exhaust all orders for n<=5 when cheap; randomized search for n=6+.
    if n<=5:orders.extend(itertools.permutations(range(n)))
    else:
        for _ in range(96):
            order=list(range(n));rng.shuffle(order);orders.append(tuple(order))
    start=time.monotonic();best=None
    rowidx={row:r for r,row in enumerate(fullrows)}
    @lru_cache(maxsize=4096)
    def val(e):
        if isinstance(e,int):return tabs[e]
        if e[0]=="not":return full^val(e[1])
        v=full if e[0]=="and" else 0
        for x in e[1:]:v=v&val(x) if e[0]=="and" else v|val(x)
        return v
    def correction(i,prior,e,positive):
        old=val(e);need=[];ban=[]
        for j in [-1]+prior:
            row=(1<<i)|(0 if j<0 else 1<<j)
            r=rowidx[row];a=bool(old>>r&1);b=lookup[row]
            if not positive:a,b=not a,not b
            if not a and b:need.append(j)
            if not b:ban.append(j)
        if not need:return e
        forms=[]
        if -1 not in need:
            z=join("or",[j for j in need if j>=0])
            forms.append(combine("and",i,z))
        if -1 not in ban and allow:
            z=join("or",[j for j in ban if j>=0])
            forms.append(i if not ban else combine("and",i,("not",z)))
        # All incident rows may be corrected by the new bit itself.
        if not ban:forms.append(i)
        if not forms:return None
        choices=[combine("or",e,f) if positive else combine("and",e,("not",f)) for f in forms]
        return min(choices,key=lambda x:len(compile_expr(n,x)[0]))
    for order in orders:
        for default in (False,True) if allow else (False,):
            e=("and",) if default else ("or",);prior=[]
            for i in order:
                for pos in (True,False):
                    if not pos and not allow:continue
                    e=correction(i,prior,e,pos)
                    if e is None:break
                if e is None:break
                prior.append(i)
            if e is not None:
                g,w=compile_expr(n,e)
                sol=compact(problem,g,w)
                if sol and valid(problem,sol):
                    return sol
                if sol and (best is None or len(sol[0])<len(best[0])):best=sol
        if time.monotonic()-start>seconds:break
    return None


def heuristic(problem,seconds=.5):
    n,rows,target=domain(problem);k=problem[3];full=(1<<len(rows))-1
    if target==0:return [],n
    if target==full and k:return [("and",[])],n
    for i,b in enumerate(input_tables(n,rows)):
        if b==target:return [],i
    best=None
    rng=random.Random(problem[4]);start=time.monotonic()
    allow=problem[-1]=="FanInTwo"
    def try_expr(e,invert=False):
        nonlocal best
        if e is None:return
        if invert:e=("not",e)
        v=compile_expr(n,e)
        if best is None or len(v[0])<len(best[0]):
            if evaluate(n,rows,*v)==target:best=v
    for t in range(16):
        for inverse in range(2 if allow else 1):
            desired=full^target if inverse else target
            if not desired:continue
            if problem[0]=="matrix":
                a,b=problem[1:3]
                if t==0:
                    for tr in (False,True):
                        try_expr(grouped(a,b,desired,tr),inverse)
                        try_expr(matrix_shared(a,b,desired,tr,False),inverse)
                        try_expr(matrix_shared(a,b,desired,tr,True),inverse)
                for tr in (False,True):try_expr(rect_expr(a,b,desired,rng,tr),inverse)
            else:try_expr(term_cover(n,rows,desired,allow,rng),inverse)
            if best and len(best[0])<=k:return best
        if time.monotonic()-start>seconds:break
    return best if best and len(best[0])<=k else None


@lru_cache(maxsize=12)
def formula_library(n, rows, allow, depth=3):
    """Exact formula table through small depth; reusable across masks."""
    full=(1<<len(rows))-1
    table={b:i for i,b in enumerate(input_tables(n,rows))}
    cost={b:0 for b in table}
    levels=[list(table)]
    for k in range(1,depth+1):
        new={}
        def add(b,e):
            if b not in cost and b not in new:new[b]=e
        if allow:
            for b in levels[k-1]:add(full^b,("not",table[b]))
        for i in range((k-1)//2+1):
            j=k-1-i
            for a in levels[i]:
                for b in levels[j]:
                    if i==j and b<=a:continue
                    x=a&b;y=a|b
                    if x not in cost and x not in new:add(x,combine("and",table[a],table[b]))
                    if y not in cost and y not in new:add(y,combine("or",table[a],table[b]))
        levels.append(list(new))
        cost.update((b,k) for b in new)
        table.update(new)
    return table,cost,levels


def formula_pair(target,budget,table,cost,levels,full,allow):
    if target in table and cost[target]<=budget:return table[target]
    if allow and full^target in table and cost[full^target]+1<=budget:
        return ("not",table[full^target])
    for op in ("or","and"):
        aim=target if op=="or" else full^target
        flip=0 if op=="or" else full
        # An OR operand must be a subset of the target. For AND the same
        # statement applies after complementing all semantic tables.
        choices=[[(x^flip,x) for x in lv if (x^flip)&~aim==0] for lv in levels]
        for i,aa in enumerate(choices):
            for j,bb in enumerate(choices):
                if j<i or i+j+1>budget:continue
                lookup=dict(bb)
                for x,a in aa:
                    need=aim^x
                    if (1<<x.bit_count())<len(bb):
                        sub=x
                        while True:
                            b=lookup.get(need|sub)
                            if b is not None:return combine(op,table[a],table[b])
                            if sub==0:break
                            sub=(sub-1)&x
                    else:
                        for y,b in bb:
                            if x|y==aim:return combine(op,table[a],table[b])
    return None


def small_formula(problem):
    n,rows,target=domain(problem);k=problem[3];allow=problem[-1]=="FanInTwo"
    if n>12 or len(rows)>48:return None
    # Deep formula tables are shared across an entire batch of masks.
    # The measured 5-input two-lit family has only 3,692 entries through 5 gates.
    depth=5 if n<=8 and len(rows)<=21 else 4 if n<=10 and len(rows)<=25 else 3
    table,cost,levels=formula_library(n,tuple(rows),allow,min(k,depth))
    full=(1<<len(rows))-1
    e=formula_pair(target,k,table,cost,levels,full,allow)
    if e is None and allow and k:
        e=formula_pair(full^target,k-1,table,cost,levels,full,False)
        if e is not None:e=("not",e)
    if e is None:return None
    sol=compact(problem,*compile_expr(n,e))
    return sol if sol and valid(problem,sol) else None


def synth_sat(problem,seconds=4):
    """Bounded gate-choice SAT with per-promise-row semantic constraints."""
    try:
        from pysat.solvers import Minisat22
        from pysat.card import CardEnc,EncType
    except ImportError:return None
    n,rows,target=domain(problem);k=problem[3];allow=problem[-1]=="FanInTwo"
    if not 1<=k<=12 or len(rows)>64 or n>12:return None
    clauses=[];v=0
    def new():
        nonlocal v
        v+=1;return v
    def one(xs):
        nonlocal v
        e=CardEnc.equals(lits=xs,bound=1,top_id=v,encoding=EncType.seqcounter)
        v=max(v,e.nv);clauses.extend(e.clauses)
    ops=[];left=[];right=[]
    for i in range(k):
        o=[new() for _ in range(3 if allow else 2)]
        a=[new() for _ in range(n+i)];b=[new() for _ in range(n+i)]
        one(o);one(a);one(b)
        ops.append(o);left.append(a);right.append(b)
        # AND/OR commute; equal inputs allow harmless padding of smaller DAGs.
        for x in range(n+i):
            for y in range(x):
                clauses.extend([[-o[z],-a[x],-b[y]] for z in (0,1)])
        if allow:clauses.append([-o[2],b[0]])
    for r,row in enumerate(rows):
        z=[new() for _ in range(k)]
        for i in range(k):
            a,b=new(),new()
            for wires,x in ((left[i],a),(right[i],b)):
                for j,s in enumerate(wires):
                    if j<n:clauses.append([-s,x if row>>j&1 else -x])
                    else:
                        y=z[j-n];clauses.extend([[-s,-x,y],[-s,x,-y]])
            u,w=ops[i][:2];q=z[i]
            clauses.extend([[-u,-q,a],[-u,-q,b],[-u,q,-a,-b],[-w,q,-a],[-w,q,-b],[-w,-q,a,b]])
            if allow:
                x=ops[i][2];clauses.extend([[-x,q,a],[-x,-q,-a]])
        clauses.append([z[-1] if target>>r&1 else -z[-1]])
    with Minisat22(bootstrap_with=clauses) as solver:
        solver.conf_budget(100000)
        timer=threading.Timer(seconds,solver.interrupt);timer.start()
        try:
            if solver.solve_limited(expect_interrupt=True) is not True:return None
            model=set(solver.get_model())
        finally:timer.cancel();timer.join()
    gates=[]
    for o,a,b in zip(ops,left,right):
        op=("and","or","not")[next(i for i,x in enumerate(o) if x in model)]
        args=[next(i for i,x in enumerate(a) if x in model)]
        if op!="not":args.append(next(i for i,x in enumerate(b) if x in model))
        gates.append((op,args))
    solution=(gates,n+k-1)
    return solution if valid(problem,solution) else None


def emit(gid,statement,problem,solution):
    num=re.fullmatch(r"L-meta-(\d+)",gid).group(1)
    mod="PEqualNP.Outside.L_meta_"+num;ns=mod+"_aux";pred=problem[-1]
    gates,out=solution
    gs=", ".join("⟨.%s, [%s]⟩"%(op,", ".join(map(str,args))) for op,args in gates)
    fit="  intro g hg\n  simp [witness] at hg" if not gates else (
        "  intro g hg\n  simp only [witness, List.mem_cons, List.not_mem_nil, or_false] at hg\n  rcases hg with "+" | ".join(["rfl"]*len(gates))+" <;> simp")
    return f"""import PEqualNP.Defs

open PEqualNP.CircuitLowerBounds PEqualNP.MetaComplexity
namespace {ns}
def witness : Circuit := ⟨[{gs}], {out}⟩

lemma fit : {pred} witness := by
{fit}
end {ns}

open {ns} in
set_option maxRecDepth 100000 in
set_option maxHeartbeats 20000000 in
theorem {mod} : {statement} := by
  exact ⟨witness, fit, by decide, by decide +kernel⟩
"""


def bit_eval(values, full, gate):
    op,args=gate
    if op=="not":return full^values[args[0]]
    if op=="and":
        x=full
        for i in args:x&=values[i]
    else:
        x=0
        for i in args:x|=values[i]
    return x


def compact(problem,gates,out):
    n,rows,target=domain(problem)
    full=(1<<len(rows))-1
    vals=input_tables(n,rows);new=[];mapping=list(range(n))
    representative={v:i for i,v in enumerate(vals)}
    for op,args in gates:
        args=[mapping[i] for i in args]
        b=bit_eval(vals,full,(op,args))
        if b in representative:
            mapping.append(representative[b]);continue
        idx=len(vals);mapping.append(idx);representative[b]=idx
        vals.append(b);new.append((op,args))
    if out>=len(mapping):return ([],n) if target==0 else None
    out=mapping[out]
    if vals[out]!=target:return None
    used=set()
    def visit(i):
        if i<n or i in used:return
        used.add(i)
        for j in new[i-n][1]:visit(j)
    visit(out)
    remap={i:i for i in range(n)};compact_gates=[]
    for i,(op,args) in enumerate(new,n):
        if i not in used:continue
        remap[i]=n+len(compact_gates);compact_gates.append((op,[remap[j] for j in args]))
    return compact_gates,remap[out]


def improve(problem,gates,out,seconds=.25):
    """Exact semantics, local gate mutation and common-subexpression elimination."""
    n,rows,target=domain(problem);full=(1<<len(rows))-1
    allow=problem[-1]=="FanInTwo";k=problem[3]
    best=compact(problem,gates,out)
    if best and len(best[0])<=k:return best
    if best:gates,out=best
    if len(gates)>k+4:return None
    deadline=time.monotonic()+seconds
    inputs=input_tables(n,rows)
    # Find an alternative earlier output, then try replacing each gate with
    # every legal earlier-wire pair. Evaluate the fixed suffix on bitsets.
    for i in range(len(gates)-1,-1,-1):
        prefix=inputs.copy()
        for gate in gates[:i]:prefix.append(bit_eval(prefix,full,gate))
        choices=[(op,[a,b]) for a in range(n+i) for b in range(a,n+i) for op in ("and","or")]
        if allow:choices += [("not",[a]) for a in range(n+i)]
        choices += [("or",[a]) for a in range(n+i)]
        for op,args in choices:
            vals=prefix+[bit_eval(prefix,full,(op,args))]
            for gate in gates[i+1:]:vals.append(bit_eval(vals,full,gate))
            if out<len(vals) and vals[out]==target:
                cand=compact(problem,gates[:i]+[(op,args)]+gates[i+1:],out)
                if cand and valid(problem,cand):return cand
        if time.monotonic()>deadline:break
    return None


def sketch_witness(problem,sketch,seconds=.25):
    """Parse public gate lists and verify or improve them, never eval text."""
    if not isinstance(sketch,str) or len(sketch)>65536:return None
    gate=r"(?:AND|OR|NOT)\(\d+(?:\s*,\s*\d+)*\)"
    runs=re.finditer(r"(?<![A-Za-z0-9_])"+gate+r"(?:\s*,\s*"+gate+r")*",sketch)
    n,rows,target=domain(problem)
    for m in runs:
        gates=[]
        for op,raw in re.findall(r"(AND|OR|NOT)\(([^)]+)\)",m.group()):
            args=[int(x) for x in raw.split(",")]
            if len(args)!=(1 if op=="NOT" else 2) or any(i<0 or i>=n+len(gates) for i in args):
                gates=[];break
            gates.append((op.lower(),args))
        if not gates or len(gates)>problem[3]+4:continue
        if problem[-1]!="FanInTwo" and any(op=="not" for op,_ in gates):continue
        out=n+len(gates)-1
        if evaluate(n,rows,gates,out)!=target:continue
        sol=improve(problem,gates,out,seconds)
        if sol and valid(problem,sol):return sol
    return None


def group_permutations(keys):
    groups={}
    for i,k in enumerate(keys):groups.setdefault(k,[]).append(i)
    orders=[list(itertools.permutations(groups[k])) for k in sorted(groups)]
    for z in itertools.product(*orders):yield tuple(x for g in z for x in g)


@lru_cache(maxsize=16384)
def canonical(kind,n,m,mask):
    """Canonical promise table and canonical-to-original input permutation."""
    if kind=="matrix":
        mask &= (1<<(n*m))-1
        if m>7:return mask,tuple(range(n+m))
        rows=[(mask>>(i*m))&((1<<m)-1) for i in range(n)]
        colkey=[sum((r>>j)&1 for r in rows) for j in range(m)]
        best=None;mapping=None
        for cp in group_permutations(colkey):
            rr=[sum(((r>>j)&1)<<k for k,j in enumerate(cp)) for r in rows]
            rp=sorted(range(n),key=lambda i:(rr[i],i))
            z=sum(rr[i]<<(k*m) for k,i in enumerate(rp))
            if best is None or z<best:best=z;mapping=tuple(rp)+tuple(n+j for j in cp)
        return best,mapping
    if n>7:return mask,tuple(range(n))
    def edge(i,j):return (mask>>(n*min(i,j)+max(i,j)))&1
    keys=[(edge(i,i),sum(edge(i,j) for j in range(n) if i!=j)) for i in range(n)]
    best=None;mapping=None
    for cp in group_permutations(keys):
        z=sum(edge(cp[i],cp[j])<<(n*i+j) for i in range(n) for j in range(i,n))
        if best is None or z<best:best=z;mapping=cp
    return best,mapping


def iso_key(p):
    kind,n,m,k,mask,pred=p
    z,perm=canonical(kind,n,m,mask)
    return (kind,n,m,z),perm


def transport(source,target,solution):
    ks,ps=iso_key(source);kt,pt=iso_key(target)
    if ks!=kt:return None
    n=len(ps);inv={v:i for i,v in enumerate(ps)}
    def wire(i):return pt[inv[i]] if i<n else i
    gates,out=solution
    sol=([(op,[wire(i) for i in args]) for op,args in gates],wire(out))
    if valid(target,sol):return sol
    sol=compact(target,*sol)
    return sol if sol and valid(target,sol) else None


def lean_witness(problem,source):
    """Read common public literal Circuit encodings; no source execution."""
    gate=r"⟨\s*(?:GateOp)?\.(and|or|not)\s*,\s*\[([\d,\s]*)\]\s*⟩"
    rx=r"⟨\s*\[((?:"+gate+r"\s*,?\s*)*)\]\s*,\s*(\d+)\s*⟩"
    for m in re.finditer(rx,source):
        gates=[]
        for op,raw in re.findall(gate,m[1]):
            args=[int(x) for x in raw.split(",") if x.strip()]
            if len(args)>2 or op=="not" and len(args)!=1:break
            gates.append((op,args))
        else:
            sol=(gates,int(m.group(m.lastindex)))
            try:
                if valid(problem,sol):return sol
            except (AssertionError,IndexError):pass
    return None


def main():
    if len(sys.argv)!=4:return 2
    gid,sf,out=sys.argv[1:]
    statement=open(sf).read().strip()
    p=parse(statement)
    if p is None:return 3
    try:
        sketch=open(sf+".sketch").read(65537)
    except OSError:
        sketch=""
    solution=sketch_witness(p,sketch) or heuristic(p) or two_order(p) or small_formula(p) or synth_sat(p)
    if solution is None:
        print("bounded promise synthesis refused",file=sys.stderr);return 3
    if not valid(p,solution):raise ValueError("independent witness audit failed")
    open(out,"w").write(emit(gid,statement,p,solution))
    return 0

if __name__=="__main__":sys.exit(main())

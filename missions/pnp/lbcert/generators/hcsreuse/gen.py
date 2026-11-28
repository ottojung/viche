"""Reuse independently audited literal public HasCircuitSize witnesses.

Only input permutations (free relabelling) and output negation (one counted
gate) are permitted. Exact all-row replay is mandatory before emission.
No Lean execution, network, or claims.
"""
from functools import lru_cache
import hashlib
import itertools
import json
from pathlib import Path
import re
import sys

DATA_SHA256 = "dab70ca47dc4e737d76957eb0be3d3908f69111aec9f2523bff70a1463e94372"
STMT = re.compile(
    r'^(?:PEqualNP\.MetaComplexity\.)?HasCircuitSize\s+(\d+)\s+'
    r'\(fun x : Fin\s+\1\s*→\s*Bool\s*=>\s*(.*)\)\s*(\d+)$')
MASK = re.compile(r'\((\d+)\s*:\s*ℕ\)\.testBit\s*\(PEqualNP\.MetaComplexity\.tableIndex x\)')
THRESHOLD = re.compile(r'decide\s*\((\d+)\s*≤\s*(?:\(\(List\.ofFn x\)\.count true\)|\(List\.ofFn x\)\.count true)\)')
COUNT = re.compile(r'decide\s*\(\(\(List\.ofFn x\)\.count true\)(?:\s*%\s*(\d+))?\s*=\s*(\d+)\)')
PRODUCT = re.compile(r'Nat\.testBit\s*\(\((.*?)\)\s*\*\s*\((.*?)\)\)\s*(\d+)')
COMPARE = re.compile(r'decide\s*\(\((.*?)\)\s*(<|≤|=)\s*\((.*?)\)\)')
TERM = re.compile(r'(\d+)\s*\*\s*\(x\s+(\d+)\)\.toNat')


@lru_cache(maxsize=16)
def input_masks(n):
    return tuple(sum(1 << r for r in range(1 << n) if r >> i & 1) for i in range(n))


def boolean_mask(n, rhs):
    """Parse the limited Bool expression grammar, not Python/Lean execution."""
    m = MASK.fullmatch(rhs)
    full=(1 << (1 << n))-1
    if m:
        return int(m[1]) & full
    m=THRESHOLD.fullmatch(rhs)
    if m:
        return sum(1 << r for r in range(1 << n) if r.bit_count() >= int(m[1]))
    m=COUNT.fullmatch(rhs)
    if m:
        mod=int(m[1]) if m[1] else None
        target=int(m[2])
        # Lean Nat.mod x 0 = x.
        return sum(1<<r for r in range(1<<n)
                   if (r.bit_count()%mod if mod else r.bit_count())==target)
    def terms(s):
        a=[TERM.fullmatch(t.strip()) for t in s.split("+")]
        if any(t is None or int(t[2])>=n for t in a):return None
        return [(int(t[1]),int(t[2])) for t in a]
    def val(a,r):return sum(k*(r>>i&1) for k,i in a)
    m=PRODUCT.fullmatch(rhs)
    if m:
        a,b=terms(m[1]),terms(m[2])
        if a is None or b is None:return None
        return sum(1<<r for r in range(1<<n) if (val(a,r)*val(b,r))>>int(m[3])&1)
    m=COMPARE.fullmatch(rhs)
    if m:
        a,b=terms(m[1]),terms(m[3])
        if a is None or b is None:return None
        cmp={"<":lambda x,y:x<y,"≤":lambda x,y:x<=y,"=":lambda x,y:x==y}[m[2]]
        # decide equality is a proposition, not a Boolean equality operator.
        return sum(1<<r for r in range(1<<n) if cmp(
            val(a,r),val(b,r)))
    token=re.compile(r'\s*(x\s+\d+|true\b|false\b|&&|\|\||!|\(|\))')
    pos=0;ts=[]
    while pos<len(rhs):
        m=token.match(rhs,pos)
        if not m:return None
        ts.append(m[1]);pos=m.end()
    if len(ts)>512:return None
    i=0
    def atom():
        nonlocal i
        if i==len(ts):raise ValueError()
        t=ts[i];i+=1
        if t=="!":return full^atom()
        if t=="(":
            v=expr()
            if i==len(ts) or ts[i]!=")":raise ValueError()
            i+=1;return v
        if t=="true":return full
        if t=="false":return 0
        if t.startswith("x") and int(t.split()[1])<n:
            return input_masks(n)[int(t.split()[1])]
        raise ValueError()
    def conj():
        nonlocal i
        a=atom()
        while i<len(ts) and ts[i]=="&&":
            i+=1;a&=atom()
        return a
    def expr():
        nonlocal i
        a=conj()
        while i<len(ts) and ts[i]=="||":
            i+=1;a|=conj()
        return a
    try:
        v=expr()
        return v if i==len(ts) else None
    except (ValueError,RecursionError):return None


def parse(statement):
    s=" ".join(statement.split())
    if s.startswith("(") and s.endswith(")"):s=s[1:-1].strip()
    m=STMT.fullmatch(s)
    if not m:return None
    n,bound=int(m[1]),int(m[3])
    if not 1<=n<=6 or not 0<=bound<=60:return None
    rhs=m[2].strip()
    # Outer parentheses around RHS are removed only if balanced.
    while rhs.startswith("(") and rhs.endswith(")"):
        depth=0
        for i,c in enumerate(rhs):
            if c=="(":depth+=1
            elif c==")":depth-=1
            if depth==0:break
        if i!=len(rhs)-1 or depth!=0:break
        rhs=rhs[1:-1].strip()
    mask=boolean_mask(n,rhs)
    return (n,mask,bound) if mask is not None else None


def evaluate(n,solution):
    """Replay the strict acyclic subset of the public Circuit semantics."""
    gates,out=solution
    full=(1<<(1<<n))-1
    w=list(input_masks(n))
    for op,args in gates:
        if op not in ("and","or","not") or len(args)>2 or any(
            type(a) is not int or not 0<=a<len(w) for a in args):
            return None
        v=[w[a] for a in args]
        if op=="not":z=full^(v[0] if v else 0)
        elif op=="and":
            z=full
            for a in v:z&=a
        else:
            z=0
            for a in v:z|=a
        w.append(z)
    if type(out) is not int or out<0:return None
    # The public definition reads nonexistent output wires as false.
    return w[out] if out<len(w) else 0


def valid(p,solution):
    try:return len(solution[0])<=p[2] and evaluate(p[0],solution)==p[1]
    except (TypeError,ValueError,IndexError):return False


def permute_mask(n,mask,perm):
    """Relabel old input i to new input perm[i]."""
    z=0
    for r in range(1<<n):
        if mask>>r&1:
            z|=1<<sum((r>>i&1)<<perm[i] for i in range(n))
    return z


def transport(n,sol,perm):
    def wire(i):return perm[i] if i<n else i
    gates,out=sol
    return [(op,[wire(i) for i in args]) for op,args in gates],wire(out)


def complement(n,sol):
    gates,out=sol
    if out>=n+len(gates):
        return [("and",[])],n
    return list(gates)+[("not",[out])],n+len(gates)


@lru_cache(maxsize=1)
def library():
    try:
        raw=Path(__file__).with_name("witnesses.json").read_bytes()
        if hashlib.sha256(raw).hexdigest()!=DATA_SHA256:return {}
        return json.loads(raw)["witnesses"]
    except (OSError,ValueError,TypeError,KeyError):return {}


@lru_cache(maxsize=4096)
def lookup(p):
    if p is None:return None
    n,mask,b=p
    if mask==0:return ([],n)
    if mask==(1<<(1<<n))-1 and b>=1:return ([("and",[])],n)
    if mask in input_masks(n):return ([],input_masks(n).index(mask))
    if b>=1 and ((1<<(1<<n))-1)^mask in input_masks(n):
        return ([("not",[input_masks(n).index(((1<<(1<<n))-1)^mask)])],n)
    entry=library().get(f"{n}:{mask}")
    if entry and valid(p,entry["solution"]):return entry["solution"]
    return None


def matches(statement):
    return lookup(parse(statement)) is not None


def emit(gid,statement,sol):
    mod="PEqualNP.Outside.L_meta_"+re.fullmatch(r"L-meta-(\d+)",gid)[1]
    gates,out=sol
    gl=", ".join("⟨."+op+", ["+", ".join(map(str,args))+"]⟩" for op,args in gates)
    if gates:
        cases=" | ".join("rfl" for _ in gates)
        fan=("  · intro g hg\n"
             "    simp only [List.mem_cons, List.not_mem_nil, or_false] at hg\n"
             f"    rcases hg with {cases} <;> simp\n")
    else:
        fan="  · simp [PEqualNP.MetaComplexity.FanInTwo]\n"
    return (
        "import Mathlib\nimport PEqualNP.Defs\n\n"
        f"theorem {mod} : {statement} := by\n"
        f"  refine ⟨⟨[{gl}], {out}⟩, ?_, by decide, ?_⟩\n"
        +fan+"  · decide +kernel\n"
    )


def main():
    if len(sys.argv)!=4:return 2
    gid,sf,out=sys.argv[1:]
    statement=Path(sf).read_text().strip()
    sol=lookup(parse(statement))
    if sol is None:return 3
    Path(out).write_text(emit(gid,statement,sol))
    return 0


if __name__=="__main__":raise SystemExit(main())

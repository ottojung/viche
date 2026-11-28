"""Transfer a public five-input free-negation lower bound to a six-input slice.

The certificate in merged L-meta-16507 proves a 9-binary-gate lower
bound for the 5-input table 0xeeeaeaa8. A variable permutation and
(optional) input/output duality preserve it. One essential input fixed
to a constant costs at least one binary gate in the unrestricted
function, and any circuit containing NOT costs at least one more gate.
Hence a monotone witness of size <=11 suffices. The final Lean proof
checks the transported certificate; Python never asserts a receipt.
"""
from functools import lru_cache
import hashlib
from itertools import permutations
import os
from pathlib import Path
import re
import sys
import time

HERE=Path(__file__).resolve().parent
HELPER=HERE.parent.parent/"onenot"
sys.path.insert(0,str(HELPER))
import monosix
import monotone_witness
import onenot

TEMPLATE_SHA="7ea482020fc41742b73373a47dff4af9e7439b69051ad0eb6136f0ae50511818"
BASE=0xeeeaeaa8
FULL32=(1<<32)-1
FULL64=(1<<64)-1
FULL256=(1<<256)-1
BASE_FULL=BASE*sum(1<<(32*j) for j in range(8))
FLOOR=9

@lru_cache(maxsize=1)
def orbit():
    out={}
    for dual in (False,True):
        for order in permutations(range(5)):
            m=0
            for row in range(32):
                r=sum(((row>>i)&1)<<j for j,i in enumerate(order))
                if dual:r^=31
                m|=(((BASE>>r)&1)^dual)<<row
            out.setdefault(m,(order,dual))
    return out

def slice_mask(mask,i,b):
    low=(1<<i)-1
    return sum(((mask>>((r&low)|((r>>i)<<(i+1))|(b<<i)))&1)<<r
               for r in range(32))

def route(mask):
    # An actual essential pair is needed for the one-gate elimination.
    for i in range(6):
        a,b=slice_mask(mask,i,0),slice_mask(mask,i,1)
        if a==b:continue
        for val,m in ((0,a),(1,b)):
            hit=orbit().get(m)
            if hit:
                order,dual=hit
                remaining=[j for j in range(6) if j!=i]
                other=next(r for r in range(64) if not r&(1<<i)
                           and ((mask>>r)^(mask>>(r|(1<<i))))&1)
                return i,val,tuple(remaining[k] for k in order)+(i,),dual,other
    return None

def matches(statement):
    p=monosix.parse(statement)
    return p is not None and route(sum(v<<r for r,v in enumerate(p[2]))) is not None

def move(w,tag,d):
    return ((w&tag)<<d)|((w>>d)&tag)|(w^((w&tag)|(w&(tag<<d))))

def moves_for(order,val,dual):
    order_now=list(range(6)); moves=[]
    for j,k in enumerate(order):
        pos=order_now.index(k)
        if pos==j:continue
        a,b=sorted((pos,j)); delta=(1<<b)-(1<<a)
        tag=sum(1<<r for r in range(256) if r&(1<<a) and not r&(1<<b))
        moves.append((tag,delta))
        order_now[j],order_now[pos]=order_now[pos],order_now[j]
    for j in range(6):
        if (j<5 and dual) or (j==5 and val):
            moves.append((sum(1<<r for r in range(256) if not r&(1<<j)),1<<j))
    return moves

def apply_moves(w,moves):
    for tag,d in moves:
        if tag&(tag<<d) or move(FULL256,tag,d)!=FULL256:
            raise ValueError("invalid bit permutation")
        w=move(w,tag,d)
    return w

def transfer(mask,match):
    i,val,order,dual,essential=match
    domain=sum(1<<r for r in range(64) if (r>>i)&1==val)
    moves=moves_for(order,val,dual)
    raw=apply_moves(BASE_FULL,reversed(moves))
    if apply_moves(domain,moves)!=FULL32 or apply_moves(raw,moves)!=BASE_FULL:
        raise ValueError("transport mismatch")
    sub=(raw^FULL256)&domain if dual else raw
    if sub&domain!=mask&domain:
        raise ValueError("cofactor target mismatch")
    # Audit each projected input against a source root or its complement.
    roots=[sum(1<<r for r in range(256) if r&(1<<j)) for j in range(6)]
    bank={r&FULL32 for r in roots[:5]}
    bank|={FULL32^r for r in bank}
    bank|={0,FULL32}
    if any(apply_moves(roots[j],moves)&FULL32 not in bank for j in range(6) if j!=i):
        raise ValueError("transport root mismatch")
    e2=essential|(1<<i)
    if essential==e2 or ((mask>>essential)^(mask>>e2))&1!=1:
        raise ValueError("not an essential input")
    return domain,raw,sub,moves,roots[i]&FULL64,essential,e2

def emit(gid,stmt,body,mask,match,witness):
    num=re.fullmatch(r"L-meta-([0-9]+)",gid)
    if num is None:raise ValueError("invalid gap")
    mod="PEqualNP.Outside.L_meta_"+num[1]; ns=mod+"_aux"
    template=HERE/"template.lean"
    data=template.read_bytes()
    if hashlib.sha256(data).hexdigest()!=TEMPLATE_SHA:raise ValueError("template digest mismatch")
    source=data.decode()
    end=re.search(r"(?m)^theorem lowS_31 : Lower true dom_31 roots_31 goal_31 9 := S_31.noCircuit\s*$",source)
    if not end:raise ValueError("template lower-bound boundary missing")
    prefix=source[:end.end()]
    if len(re.findall(r"\bgoal_63\b",prefix))!=1:
        raise ValueError("source certificate unexpectedly depends on the original six-input goal")
    prefix,n=re.subn(r"(?m)^def goal_63 : Nat := 0x[0-9a-fA-F]+$",f"def goal_63 : Nat := 0x{mask:x}",prefix)
    if n!=1:raise ValueError("template goal boundary missing")
    suffix=source[source.index("def ptN (r : Nat)"):source.index("def witGates :")]
    suffix,n=re.subn(r"Nat\.testBit \(\d+ \* 2 \^ 32 \+ \d+\) \(∑ i : Fin 6, if x i then 2 \^ \(i : ℕ\) else 0\)",lambda _:body,suffix)
    if n!=2:raise ValueError("template target boundary missing")
    i,val,order,dual,_=match
    dom,raw,sub,moves,root,e1,e2=transfer(mask,match)
    movetext="["+", ".join(f"(0x{tag:x}, {d})" for tag,d in moves)+"]"
    roots="["+", ".join(f"xs256.getD {j} 0" for j in range(6) if j!=i)+"]"
    block=f"""
-- Restriction certificate adapted from merged L-meta-16507 (Apache-2.0).
def sliceDomain : Nat := 0x{dom:x}
def sliceRoots : List Nat := {roots}
def sliceRaw : Nat := 0x{raw:x}
def sliceGoal : Nat := 0x{sub:x}

lemma slice_raw_bound : Lower true sliceDomain sliceRoots sliceRaw 9 :=
  lower_iso (d1 := dom_31) (T1 := goal_31) {movetext}
    (by decide +kernel) (by decide +kernel) (by decide +kernel)
    (by decide +kernel) (by decide +kernel) lowS_31
"""
    if dual:
        block+="""
lemma lowerNegTransfer {d T L : Nat} {roots : List Nat}
    (hd : d &&& mask256 = d) (h : Lower true d roots T L) :
    Lower true d roots (negD d T) L := by
  intro p bank hr ha
  apply h p bank hr
  have he : negD d (negD d T) &&& d = T &&& d := by
    rw [negD_invol hd, Nat.and_assoc, Nat.and_self]
  exact avail_of_eq he (avail_neg hd ha)

lemma slice_bound : Lower true sliceDomain sliceRoots sliceGoal 9 := by
  have h : Lower true sliceDomain sliceRoots (negD sliceDomain sliceRaw) 9 :=
    lowerNegTransfer (by decide +kernel) slice_raw_bound
  have he : negD sliceDomain sliceRaw = sliceGoal := by decide +kernel
  rw [he] at h
  exact h
"""
    else:
        block+="\nlemma slice_bound : Lower true sliceDomain sliceRoots sliceGoal 9 := slice_raw_bound\n"
    block+=f"""
lemma lowS_63 : Lower true dom_63 roots_63 goal_63 10 :=
  lower_slice (by decide +kernel) (by decide +kernel) (by decide +kernel) (by decide +kernel)
    (by decide +kernel) (by decide +kernel) (by decide +kernel)
    (by decide +kernel) (by decide +kernel) (by decide +kernel)
    [(0x{root:x}, {e1}, {e2})] (by decide +kernel) (by decide +kernel) slice_bound
"""
    M=len(witness); out=6+M-1
    gates=", ".join("⟨GateOp.%s, [%d, %d]⟩"%("or" if tt[1] else "and",a,b) for a,b,tt in witness)
    text=prefix+"\n"+block+"\n"+suffix+f"""
def witGates : List Gate := [{gates}]
lemma wit_mono : Monotone2 ⟨witGates, {out}⟩ := by
  simp [Monotone2, witGates]
lemma wit_eval : ∀ x : Fin 6 → Bool, Circuit.eval ⟨witGates, {out}⟩ (List.ofFn x) = (fun x : Fin 6 → Bool => {body}) x := by
  decide +kernel

lemma main : {stmt.strip()} := by
  intro s ⟨⟨gates, o⟩, hfan, hsz, hev⟩
  by_cases hhas : ∃ g ∈ gates, isNotGate g = true
  · have hlb : 11 ≤ gates.length := lb_with_not gates o hfan hev hhas
    refine ⟨⟨witGates, {out}⟩, wit_mono, ?_, wit_eval⟩
    have hlen : witGates.length = {M} := rfl
    change witGates.length ≤ s
    change gates.length ≤ s at hsz
    omega
  · push_neg at hhas
    refine ⟨⟨gates, o⟩, ?_, hsz, hev⟩
    intro g hg
    obtain ⟨h1, h2⟩ := hfan g hg
    refine ⟨?_, h2⟩
    change g.op = GateOp.and ∨ g.op = GateOp.or ∨ g.op = GateOp.not at h1
    rcases h1 with h1 | h1 | h1
    · exact Or.inl h1
    · exact Or.inr h1
    · exfalso; have := hhas g hg; simp [isNotGate, h1] at this

end PEqualNP.Outside.L_meta_16507_aux
"""
    # Exactly one theorem, exact outer statement. Public helper declarations
    # are lemmas within the renamed namespace.
    text=text.replace("PEqualNP.Outside.L_meta_16507_aux",ns)
    text=re.sub(r"(?m)^(\s*)(private |protected )?theorem\b",r"\1\2lemma",text)
    return text+f"\ntheorem {mod} : {stmt.strip()} := by\n  exact {ns}.main\n"

def generate(gid,stmt,budget=2):
    p=monosix.parse(stmt)
    if p is None:return None,"unmatched statement"
    n,body,f=p;mask=sum(v<<r for r,v in enumerate(f))
    match=route(mask)
    if match is None:return None,"no certified cofactor"
    started=time.monotonic()
    w=monotone_witness.synthesize(n,f,budget=min(.9,budget))
    if w is None:return None,"no bounded witness"
    if len(w)>11:
        w2=monotone_witness.synthesize(n,f,width=8,budget=min(.8,max(0,budget-(time.monotonic()-started))))
        if w2 and len(w2)<len(w):w=w2
    # The compact existing engine is preferable for <=10-gate witnesses.
    if len(w)!=11:return None,"compact route preferred or witness exceeds bound"
    if not all(onenot.evaluate(n,w,r)==f[r] for r in range(64)):
        raise ValueError("witness replay failed")
    return emit(gid,stmt,body,mask,match,w),None

def main():
    gid,sf,out=sys.argv[1:]
    budget=min(2,float(os.environ.get("PNP_GENERATOR_BUDGET_SECONDS","600")))
    text,why=generate(gid,Path(sf).read_text(),budget=max(0,budget-.2))
    if text is None:
        print(why,file=sys.stderr);return 3
    Path(out).write_text(text);return 0

if __name__=="__main__":
    sys.exit(main())

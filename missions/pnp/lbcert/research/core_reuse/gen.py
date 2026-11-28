"""Reuse public five-input leaf data with one/two gate-elimination proofs.

Only exact integer data extracted from merged Lean files are used.
The candidate replays every search certificate and all transport checks
in Lean; static validation is not kernel verification.
"""
import hashlib,itertools,json,os,re,sys,time
from functools import lru_cache
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent.parent/"onenot"))
import monosix
import monotone_witness
import onenot

TEMPLATE_SHA="8d1218e7f0f392c7b142674bb17a5c54373555eba5ec1f649858c28b268ca967"
FULL32=(1<<32)-1
FULL64=(1<<64)-1

def slice_mask(mask,i,b):
    low=(1<<i)-1
    return sum(((mask>>((r&low)|((r>>i)<<(i+1))|(b<<i)))&1)<<r
               for r in range(32))

def sample_ok(mask,cols):
    return all(((mask>>sum(((cols[j]>>r)&1)<<j for j in range(5)))&1)==(r>=32)
               for r in range(64))

@lru_cache(maxsize=1)
def index():
    idx={}
    data=json.loads((HERE/"certificates.json").read_text())
    for cert in data["certificates"]:
        base=int(cert["base"],16)
        cols=cert["columns"]; roots=cert["roots"]; floor=cert["floor"]
        if not (0<base<FULL32 and 1<=floor<=10 and len(cols)==5 and len(set(roots))==len(roots)
                and all(type(w) is int and 0<=w<=FULL64 for w in cols+roots)
                and all(w in roots or w in (0,FULL64) for w in cols)
                and all(w in cols for w in roots) and sample_ok(base,cols)):
            raise ValueError("invalid leaf certificate data")
        for order in itertools.permutations(range(5)):
            m=sum(((base>>sum(((r>>order[j])&1)<<j for j in range(5)))&1)<<r
                  for r in range(32))
            out=[0]*5
            for j,k in enumerate(order):out[k]=cols[j]
            if m not in idx or floor>idx[m][0]:
                if not sample_ok(m,out):raise ValueError("permutation replay failed")
                idx[m]=(floor,tuple(out),tuple(roots),cert["source"])
    return idx

def route(mask):
    idx=index(); choices=[]
    for i in range(6):
        a,b=slice_mask(mask,i,0),slice_mask(mask,i,1)
        if a==b:continue
        lo,hi=idx.get(a),idx.get(b)
        if lo:choices.append((lo[0]+1,i,((0,lo),)))
        if hi:choices.append((hi[0]+1,i,((1,hi),)))
        if lo and hi:choices.append((min(lo[0],hi[0])+2,i,((0,lo),(1,hi))))
    return max(choices,key=lambda x:(x[0],-len(x[2]))) if choices else None

def matches(stmt):
    p=monosix.parse(stmt)
    plan=route(sum(v<<r for r,v in enumerate(p[2]))) if p else None
    return bool(plan and plan[0]>=10)

def good(mask,i,b):
    a=next(r for r in range(64) if not r&(1<<i) and ((mask>>r)^(mask>>(r|(1<<i))))&1)
    rows=[r for r in range(64) if ((r>>i)&1)==b]
    pos=next(r for r in rows if mask>>r&1)
    neg=next(r for r in rows if not mask>>r&1)
    return f"(good_at {a} {pos} {neg} (by decide +kernel))"

def leaf(i,b,cert,floor,mask,name):
    _, cols, roots, source=cert
    co=slice_mask(mask,i,b)
    if not sample_ok(co,cols):raise ValueError("wrong transported sample")
    full=list(cols);full.insert(i,0)
    tf="true" if b else "false"
    # Lower-bound replay still checked by Lean. Reuse the original root order.
    return f"""
-- Leaf data from public merged {source}.
set_option maxHeartbeats 0 in
set_option maxRecDepth 64000 in
lemma {name} : Low {floor} (rs {i} {tf} sixTarget) :=
  CoreSearch.lower (n := {floor-1}) (f := (rs {i} {tf} sixTarget))
    {full} {list(roots)} (by decide +kernel) (by decide +kernel)
    (by unfold CoreSearch.Rep; decide +kernel)
    (CoreSearch.replay_split (m := {len(roots)*(len(roots)-1)//2})
      (by decide +kernel) (by decide +kernel)
      (by intro j hj; interval_cases j <;> decide +kernel))
"""

def emit(gid,stmt,body,mask,plan,witness):
    num=re.fullmatch(r"L-meta-([0-9]+)",gid)
    if not num:raise ValueError("invalid gap ID")
    mod="PEqualNP.Outside.L_meta_"+num[1]
    ns=mod+"_aux"
    raw=(HERE/"template.lean").read_bytes()
    if hashlib.sha256(raw).hexdigest()!=TEMPLATE_SHA:raise ValueError("template digest mismatch")
    prefix=raw.decode().split("def sixTarget : F :=",1)[0]
    prefix=prefix.replace("PEqualNP.Outside.L_meta_40976",ns)
    bound,i,certs=plan
    M=len(witness)
    if M>bound+1:raise ValueError("witness exceeds conditional bound")
    gates=", ".join("⟨.%s, [%d, %d]⟩"%("or" if tt[1] else "and",a,b) for a,b,tt in witness)
    text=prefix+f"""
-- Reusable engine from merged L-meta-40976, Apache-2.0.
def sixTarget : F := fun x : Fin 6 → Bool => {body}
def sixWitness : Circuit := ⟨[{gates}], {6+M-1}⟩
lemma basis : Monotone2 sixWitness := by simp [Monotone2, sixWitness]
set_option maxHeartbeats 0 in
set_option maxRecDepth 16000 in
lemma correct : ∀ x : X, sixWitness.eval (List.ofFn x) = sixTarget x := by decide +kernel
"""
    floor=bound-len(certs)
    for b,c in certs:text+=leaf(i,b,c,floor,mask,f"leaf_{b}")
    if len(certs)==1:
        b=certs[0][0];tf="true" if b else "false"
        proof=f"one {i} {tf} {good(mask,i,b)} leaf_{b}"
    else:proof=f"two {i} {good(mask,i,0)} {good(mask,i,1)} leaf_0 leaf_1"
    text+=f"""
lemma sixLower : Low {bound} sixTarget := {proof}
end {ns}
"""
    text=re.sub(r"(?m)^(\s*)(private |protected )?theorem\b",r"\1\2lemma",text)
    text+=f"""
open {ns} PEqualNP.CircuitLowerBounds PEqualNP.MetaComplexity in
theorem {mod} : {stmt.strip()} := by
  intro s h
  by_cases enough : {M} ≤ s
  · exact ⟨sixWitness, basis, enough, correct⟩
  obtain ⟨⟨gs,o⟩, fit, size, computes⟩ := h
  have hf : ∀ g ∈ gs, (g.op = .and ∨ g.op = .or ∨ g.op = .not) ∧ g.inputs.length ≤ 2 := by
    intro g hg
    exact ⟨by simpa using (fit g hg).1, (fit g hg).2⟩
  change gs.length ≤ s at size
  exact ⟨⟨gs,o⟩, all_not_not sixLower gs o hf (by omega) computes, size, computes⟩
"""
    return text

def generate(gid,stmt,budget=3):
    p=monosix.parse(stmt)
    if p is None:return None,"unmatched statement"
    n,body,f=p;mask=sum(v<<r for r,v in enumerate(f))
    plan=route(mask)
    if plan is None:return None,"no reusable leaf certificate"
    # Don't compete with compact generator on easy 10-gate cases yet.
    if plan[0]<10:return None,"compact route preferred"
    start=time.monotonic()
    w=monotone_witness.synthesize(n,f,budget=min(1.4,budget))
    if w and len(w)>plan[0]+1:
        w2=monotone_witness.synthesize(n,f,width=8,budget=min(1.2,max(0,budget-(time.monotonic()-start))))
        if w2 and len(w2)<len(w):w=w2
    if not w or len(w)!=plan[0]+1:return None,"no fitting larger witness"
    if not all(onenot.evaluate(n,w,r)==f[r] for r in range(64)):
        raise ValueError("witness replay failed")
    return emit(gid,stmt,body,mask,plan,w),None

def main():
    gid,sf,out=sys.argv[1:]
    budget=min(3,float(os.environ.get("PNP_GENERATOR_BUDGET_SECONDS","3")))
    s,why=generate(gid,Path(sf).read_text(),budget=max(0,budget-.2))
    if s is None:
        print(why,file=sys.stderr);return 3
    Path(out).write_text(s);return 0

if __name__=="__main__":sys.exit(main())

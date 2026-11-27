"""Gate-elimination certificates for eight-variable graph one-NOT equality."""
import hashlib
import json
import importlib.util
import re
import sys
from pathlib import Path
from functools import lru_cache
from itertools import combinations,product

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SOURCE="PEqualNP.Outside.L_meta_27460"
RULES_SHA="9f016fc75ab68ccd04a39889704e934cd00c2925d0af445985fad94bb44d6f1a"
SHAPE_SHA="cd6c0013f4462012f855b148da463743fdc18f123497a46eceffaecc8c7e14b2"
N=8
SEEDS_SHA="498425bebf5d6333446cc3beec31ab9f733be3f581fb986749444ad2f587a9f3"

def checked(name,digest):
    data=(HERE/name).read_bytes()
    if hashlib.sha256(data).hexdigest()!=digest:raise ValueError("unreviewed template")
    return data.decode()

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

bounds=load("gateelim_bounds",HERE/"bounds.py")
cover=load("gateelim_cover",HERE/"cover.py")


def norm(s):return " ".join(s.split())

@lru_cache(maxsize=1)
def pattern():
    shape=norm(json.loads(checked("shape.json",SHAPE_SHA)))
    e=re.search(r"\[[0-9, ]+\](?= : List ℕ)",shape).group()
    parts=shape.split(e)
    return re.compile(re.escape(parts[0])+r"(?P<edges>\[[0-9, ]+\])"+r"(?P=edges)".join(map(re.escape,parts[1:])))

def parse(s):
    m=pattern().fullmatch(norm(s))
    if not m:return None
    a=[int(x) for x in m["edges"][1:-1].split(",")]
    if not a or len(a)%2:return None
    e=[tuple(sorted((a[i],a[i+1]))) for i in range(0,len(a),2)]
    if any(not 0<=i<j<N for i,j in e) or len(set(e))!=len(e):return None
    return e

def key(edges):return ";".join(f"{a},{b}" for a,b in sorted(edges))


@lru_cache(maxsize=1)
def seeds():
    return json.loads(checked("seeds.json",SEEDS_SHA))


@lru_cache(maxsize=4096)
def feasible(edges):
    entry=seeds().get(key(edges))
    if entry:
        w=[(a,b,{int(k):v for k,v in tt.items()}) for a,b,tt in entry["witness"]]
        return w
    w=cover.greedy(N,edges,cover.build_best,trials=2)
    if not w or len(w)>14:return None
    f=bounds.normalize((1<<a)|(1<<b) for a,b in edges)
    return w if len(w)<=bounds.lower(f)[0]+1 else None


def matches(s):
    edges=parse(s)
    return edges is not None and feasible(tuple(sorted(edges))) is not None

def truth(f,r):return any(r&m==m for m in f)
def boollit(c):return "true" if c else "false"
def expression(f):
    if not f:return "false"
    if f==(0,):return "true"
    return " || ".join("("+" && ".join("x "+str(i) for i in bounds.indices(t))+")" for t in f)

def dependency(f,i):
    return next(r for r in range(1<<N) if not r>>i&1 and truth(f,r)!=truth(f,r|1<<i))

def chosen(f,B):
    vs=bounds.indices(bounds.active(f))
    R={(i,c):bounds.rest(f,i,c) for i in vs for c in (False,True)}
    kids={ic:bounds.lower(g)[0] for ic,g in R.items() if bounds.nonconstant(g)}
    universe=list((i,j,s,u) for i,j in combinations(vs,2) for s,u in product((False,True),repeat=2))
    supports={}
    for ic,b in kids.items():
        i,c=ic
        def works(x):
            a,z,s,u=x
            if i==z:a,z,s,u=z,a,u,s
            return i==a and bool(bounds.active(R[z,not u])>>a&1) and b+(3 if c!=s else 2)>=B
        supports[ic]={x for x in universe if works(x)}
    pending=set(universe);out=[]
    while pending:
        ic=max(supports,key=lambda x:len(supports[x]&pending))
        hit=supports[ic]&pending
        if not hit:raise ValueError("incomplete first-gate proof plan")
        out.append(ic);pending-=hit
    return out

class Emitter:
    def __init__(self):self.names={};self.lines=[]
    def say(self,line):self.lines.append(line)
    def dec(self,head,body):
        self.say("set_option maxRecDepth 100000 in\nset_option maxHeartbeats 0 in\nlemma "+head+" := "+body+"\n")
    def emit(self,f):
        if f in self.names:return self.names[f]
        B,plan=bounds.lower(f);v="v"+str(len(self.names)+1)
        self.names[f]=v
        self.say("def "+v+" : BF 8 := fun x => "+expression(f)+"\n")
        kind=plan[0]
        if kind=="zero":
            self.say("lemma "+v+"_lb : LB "+v+" 0 := fun t _ => Nat.zero_le t\n")
            return v
        if kind=="one":kids=[(plan[1],plan[2])]
        elif kind=="two":kids=[(plan[1],False),(plan[1],True)]
        else:kids=chosen(f,B)
        refs={}
        for i,c in kids:
            g=bounds.rest(f,i,c);w=self.emit(g);b=bounds.lower(g)[0]
            eq=v+"_"+str(i)+"_"+boollit(c)
            self.dec(eq+" : rs "+v+" "+str(i)+" "+boollit(c)+" = "+w,"by funext x; revert x; decide +kernel")
            refs[i,c]=(eq,w,b)
        def ref(ic,B0=None):
            eq,w,b=refs[ic]
            r="("+eq+".symm ▸ "+w+"_lb)"
            if B0 is not None and B0<b:r="(LB_mono "+r+" (by decide))"
            return r
        if kind=="one":
            _,i,c=plan
            proof=f"rule1 {v} {i} {boollit(c)} {B-1} {dependency(f,i)} 0 255 (by decide +kernel) (by decide +kernel) "+ref((i,c))
        elif kind=="two":
            i=plan[1];b=B-2
            proof=f"rule2 {v} {i} {b} {dependency(f,i)} 0 255 0 255 (by decide +kernel) (by decide +kernel) (by decide +kernel) "+ref((i,False),b)+" "+ref((i,True),b)
        else:
            mask=bounds.active(f);i,j=bounds.indices(mask)[:2]
            vs=", ".join(f"({a}, {boollit(c)}, {refs[a,c][2]})" for a,c in kids)
            arms="\n".join("    · exact "+ref(ic) for ic in kids)
            destruct="rfl" if len(kids)==1 else " | ".join(["rfl"]*len(kids))
            proof=(f"rule3B {v} {B} (fun i : Fin 8 => (({mask} : ℕ).testBit i.val)) (by decide +kernel)\n"
                   f"    ⟨{i}, {j}, by decide +kernel⟩ [{vs}] (by\n"
                   "    intro e he\n    simp only [List.mem_cons, List.not_mem_nil, or_false] at he\n"
                   f"    rcases he with {destruct}\n{arms}) (by decide +kernel)")
        self.dec(v+"_lb : LB "+v+" "+str(B),proof)
        return v

def generate(gid,s,witness=None):
    if not re.fullmatch(r"L-meta-[0-9]+",gid):return None
    edges=parse(s)
    if edges is None:return None
    f=bounds.normalize((1<<i)|(1<<j) for i,j in edges)
    B,_=bounds.lower(f)
    w=witness if witness is not None else feasible(tuple(sorted(edges)))
    if not w or len(w)>B+1:return None
    # Independent all-row audit of the monotone circuit before emission.
    for r in range(1<<N):
        v=[bool(r>>i&1) for i in range(N)]
        for a,b,tt in w:
            if not 0<=a<len(v) or not 0<=b<len(v) or a==b:return None
            if tt=={0:0,1:0,2:0,3:1}:v.append(v[a] and v[b])
            elif tt=={0:0,1:1,2:1,3:1}:v.append(v[a] or v[b])
            else:return None
        if v[-1]!=truth(f,r):return None
    M=len(w);module="PEqualNP.Outside."+gid.replace("-","_")
    src=checked("rules.lean",RULES_SHA).replace(SOURCE,module)
    src=re.sub(r"(?m)^theorem ","lemma ",src)
    em=Emitter();root=em.emit(f)
    glist=", ".join("⟨."+("and" if tt[1]==0 else "or")+", ["+str(a)+", "+str(b)+"]⟩" for a,b,tt in w)
    rhs=norm(s).split("= decide ",1)[1].split(") → ∃",1)[0]
    em.say("def onWit : List Gate := ["+glist+"]\n")
    em.say("""lemma binary_lt (gs : List Gate) (h : ∃ g ∈ gs, g.op = GateOp.not) : bc gs < gs.length := by
  obtain ⟨g, mem, op⟩ := h
  exact (List.length_filter_lt_length_iff_exists (p := isBinary)).mpr
    ⟨g, mem, by simp [isBinary, op]⟩
""")
    em.say("lemma onWitBasis : ∀ g ∈ onWit, (g.op = GateOp.and ∨ g.op = GateOp.or) ∧ g.inputs.length ≤ 2 := by\n  intro g hg\n  simp only [onWit, List.mem_cons, List.not_mem_nil, or_false] at hg\n  rcases hg with "+" | ".join(["rfl"]*M)+" <;> simp\n")
    em.dec(f"onWitCorrect : ∀ x : Fin 8 → Bool, Circuit.eval ⟨onWit, {N+M-1}⟩ (List.ofFn x) = {root} x","by decide +kernel")
    em.dec(f"graph_eq : ∀ x : Fin 8 → Bool, {root} x = decide "+rhs,"by decide +kernel")
    em.say("end "+module+"\n")
    em.say("open PEqualNP.CircuitLowerBounds "+module+"\n")
    em.say("theorem "+module+" : "+s.strip()+" := by")
    em.say(f"""  intro gates o hfit _hone hev
  by_cases hn : ∃ g ∈ gates, g.op = GateOp.not
  · have hb := bound_of_LB {root} {B} {root}_lb gates o (fun g hg => hfit g hg)
      (fun x => (hev x).trans (graph_eq x).symm)
    have hl := binary_lt gates hn
    have hw : onWit.length = {M} := rfl
    exact ⟨onWit, {N+M-1}, onWitBasis, by omega, fun x => (onWitCorrect x).trans (graph_eq x)⟩
  · refine ⟨gates, o, ?_, le_rfl, hev⟩
    intro g hg
    obtain ⟨ho, hl⟩ := hfit g hg
    refine ⟨?_, hl⟩
    rcases ho with h | h | h
    · exact Or.inl h
    · exact Or.inr h
    · exact (hn ⟨g, hg, h⟩).elim
""")
    return src+"\n-- Gate elimination rules from merged PEqualNP L-meta-27460 (Apache-2.0).\n"+"\n".join(em.lines)

def main():
    gid,sf,out=sys.argv[1:]
    text=generate(gid,Path(sf).read_text())
    if text is None:return 3
    Path(out).write_text(text);return 0

if __name__=="__main__":sys.exit(main())

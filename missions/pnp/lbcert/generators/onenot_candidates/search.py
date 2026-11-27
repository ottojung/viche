import os
import random
import shutil
import subprocess
import tempfile
from pathlib import Path

def candidates(n,edges):
 adj=[0]*n
 ei={}
 for i,(a,b) in enumerate(edges):adj[a]|=1<<b;adj[b]|=1<<a;ei[a,b]=i;ei[b,a]=i
 vals=[tuple(i for i in range(n) if m>>i&1) for m in range(1<<n)]
 res=[]
 for a in range(1,1<<n):
  bmax=(1<<n)-1
  for v in vals[a]:bmax&=adj[v]
  b=bmax
  while b:
   if a<b:
    e=0
    for x in vals[a]:
     for y in vals[b]:e|=1<<ei[x,y]
    res.append((a,b,e))
   b=(b-1)&bmax
 return res,vals
def greedy(n,edges,build,trials=20):
 cs,vs=candidates(n,edges)
 rng=random.Random(1);best=None
 if not cs:return None
 for t in range(trials):
  avail=set(1<<i for i in range(n));rem=(1<<len(edges))-1;cover=[]
  def extra(a):
   k=max((s.bit_count() for s in avail if a&s==s),default=1)
   return a.bit_count()-k
  while rem:
   def score(c):
    a,b,e=c;hit=(e&rem).bit_count()
    if not hit:return -1
    cost=2+extra(a)+extra(b)
    return hit/cost*(1+(rng.random()-.5)*(.4 if t else 0))
   a,b,e=max(cs,key=score)
   cover.append((vs[a],vs[b],e,len(vs[a])+len(vs[b])))
   avail.update((a,b));rem&=~e
  g=build(n,cover)
  if best is None or len(g)<len(best):best=g
 return best

def screen(emitter,n,f,witness):
    if not witness or not 2<=len(witness)<=11:
        return None
    pairs=emitter.critical_pairs(n,f)
    if not pairs:return None
    rng=random.Random(1)
    base=[p for p in pairs if p[0].bit_count()==2]
    rest=[p for p in pairs if p not in set(base)]
    cc=shutil.which("cc")
    if not cc:return None
    with tempfile.TemporaryDirectory(prefix="pnp-onenot-") as tmp:
        binary=Path(tmp)/"lsearch"
        try:
            subprocess.run([cc,"-O2","-o",str(binary),str(Path(emitter.__file__).with_name("lsearch.c"))],
                           capture_output=True,timeout=2,check=True)
        except (OSError,subprocess.SubprocessError):return None
        for _ in range(2):
            trial=pairs if len(pairs)<=128 else (base+rng.sample(rest,128-len(base)))[:128]
            rows=[a for a,b in trial]+[b for a,b in trial]
            full=(1<<len(rows))-1
            words=[full^sum(((r>>i)&1)<<j for j,r in enumerate(rows)) for i in range(n)]
            inp="%d %d %d %d\n%s\n"%(n,len(trial),len(witness)-2,400000,"\n".join("%x"%w for w in words))
            try:
                run=subprocess.run([str(binary)],input=inp,capture_output=True,text=True,
                      timeout=3,env={**os.environ,"LSEARCH_PAIRS_ONLY":"1"})
            except (OSError,subprocess.TimeoutExpired):continue
            if run.returncode==0 and run.stdout.strip()=="none":return trial
            if len(pairs)<=128:break
    return None

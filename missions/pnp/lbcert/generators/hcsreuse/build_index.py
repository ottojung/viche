"""Reproduce witness data from pinned public upstream. No source execution."""
import itertools,json,os,re,subprocess,sys,time
from collections import Counter
from pathlib import Path
from missions.pnp.lbcert.generators.hcsreuse import gen
if len(sys.argv)!=3:raise SystemExit("usage: python3 -m missions.pnp.lbcert.generators.hcsreuse.build_index MIRROR OUTPUT")
mirror=sys.argv[1]
output=Path(sys.argv[2])
git=["git","--git-dir="+mirror]
rev="491b9d7f1ef497d41e346ead5326157c2da595c9"
ls=subprocess.check_output(git+["ls-tree","-l",rev,"lean/PEqualNP/Outside/"],text=True)
files=[]
for line in ls.splitlines():
 meta,path=line.split("\t",1)
 m=re.fullmatch(r"lean/PEqualNP/Outside/L_meta_(\d+)\.lean",path)
 if m and int(meta.split()[3])<=160000:
  files.append((int(m[1]),meta.split()[2]))
files=[e for e in files if 10200<=e[0]<=11150 or 20780<=e[0]<=20790]
g1=r"Gate\.mk\s+\.(and|or|not)\s+\[([\d,\s]*)\]"
g2=r"⟨\s*(?:PEqualNP\.CircuitLowerBounds\.)?(?:GateOp)?\.(and|or|not)\s*,\s*\[([\d,\s]*)\]\s*⟩"
g3=r"\{\s*op\s*:=\s*(?:PEqualNP\.CircuitLowerBounds\.)?(?:GateOp)?\.(and|or|not)\s*,\s*inputs\s*:=\s*\[([\d,\s]*)\]\s*\}"
gate=r"(?:"+g1+"|"+g2+"|"+g3+")"
circ=re.compile(r"(?:Circuit\.mk\s*\[|⟨\s*\[|\{\s*gates\s*:=\s*\[)\s*((?:"+gate+r"\s*,?\s*)*)\]\s*,?\s*(?:output\s*:=\s*)?(\d+)\s*(?:⟩|\})?")
stats=Counter()
w={}
def add(n,mask,sol,num,blob):
 key=f"{n}:{mask}"
 if key not in w or len(sol[0])<len(w[key]["solution"][0]):
  w[key]={"solution":sol,"source":num,"blob":blob}
def orbit(n,mask,sol,num,blob):
 # Source orbit canonicalization avoids expanding multiple identical functions.
 for perm in itertools.permutations(range(n)):
  z=gen.permute_mask(n,mask,perm)
  s=gen.transport(n,sol,perm)
  if not gen.valid((n,z,len(s[0])),s):raise AssertionError("transport")
  add(n,z,s,num,blob)
  t=gen.complement(n,s);zc=((1<<(1<<n))-1)^z
  if not gen.valid((n,zc,len(t[0])),t):raise AssertionError("complement")
  add(n,zc,t,num,blob)
def save():
 out={"schema":1,"upstream":rev,"stats":dict(stats),"witnesses":w}
 output.write_text(json.dumps(out,sort_keys=True,separators=(",",":"))+"\n")
 print("progress",dict(stats),"witnesses",len(w),flush=True)
p=subprocess.Popen(git+["cat-file","--batch"],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
start=time.monotonic()
try:
 for num,blob in files:
  p.stdin.write((blob+"\n").encode());p.stdin.flush()
  h=p.stdout.readline().split()
  src=p.stdout.read(int(h[2])).decode("utf-8","replace");p.stdout.read(1)
  stats["scanned"]+=1
  if "HasCircuitSize" not in src or re.search(r"[\u0400-\u04ff]",src):continue
  m=re.search(r"(?ms)^theorem PEqualNP\.Outside\.L_meta_"+str(num)+r"\s*:\s*(.*?)\s*:=\s*(?:by\b|\n)",src)
  if not m:continue
  q=gen.parse(m[1])
  if q is None:continue
  stats["parsed"]+=1
  print("parsed",num,q,flush=True)
  n,mask,b=q
  best=None
  for c in circ.finditer(src):
   g=[]
   for a,x,bop,y,dop,z in re.findall(gate,c[1]):
    g.append((a or bop or dop,[int(v) for v in (x if a else y if bop else z).split(",") if v.strip()]))
   sol=(g,int(c[c.lastindex]))
   if gen.valid(q,sol) and (best is None or len(g)<len(best[0])):best=sol
  if best is None:continue
  stats["audited_sources"]+=1
  key=f"{n}:{mask}"
  if key not in w or len(best[0])<len(w[key]["solution"][0]):
   orbit(n,mask,best,num,blob)
   stats["expanded"]+=1
finally:
 p.stdin.close();p.wait()
save()

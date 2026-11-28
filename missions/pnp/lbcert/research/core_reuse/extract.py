import subprocess,re,json,collections,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from missions.pnp.lbcert.generators.cofactor_lb import gen
if len(sys.argv)!=4:raise SystemExit('usage: extract.py MIRROR PINNED_REF OUTPUT_JSON (run from repo root)')
git=['git','--git-dir='+sys.argv[1]]
head=subprocess.check_output(git+['rev-parse',sys.argv[2]],text=True).strip()
# First index latest proofs with the exact 64-bit generic replay shape.
log=subprocess.check_output(git+['log','-n','1800','--format=%H%x09%s',head],text=True)
paths=[]
for line in log.splitlines():
 c,s=line.split('\t',1);m=re.match(r'L-meta-(\d+)\b',s)
 if m:paths.append((c,int(m[1])))
p=subprocess.Popen(git+['cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
seen={};counts=collections.Counter()
# Decimal data from literal calls; do not evaluate Lean code.
pat=re.compile(r'CoreSearch\.lower \(n := (\d+)\) \(f := \(rs ([0-5]) (true|false) sixTarget\)\) \[([0-9, ]+)\] \[([0-9, ]+)\]')
target=re.compile(r'(?m)^def sixTarget : F := fun x : Fin 6 → Bool => Nat.testBit \((\d+) \* 2 \^ 32 \+ (\d+)\)')
for c,n in paths:
 req=f'{c}:lean/PEqualNP/Outside/L_meta_{n}.lean'
 p.stdin.write(req.encode()+b'\n');p.stdin.flush();h=p.stdout.readline().split()
 if h[-1]==b'missing':continue
 raw=p.stdout.read(int(h[-1]));p.stdout.read(1);s=raw.decode('utf8',errors='replace')
 if 'def replaySlice (n : Nat) (roots : List Nat)' not in s or 'def sep (x : W) : BitVec 32' not in s:continue
 t=target.search(s)
 if not t:continue
 mask=(int(t[1])<<32)|int(t[2])
 if mask.bit_length()>64:continue
 for m in pat.finditer(s):
  k,i,b=int(m[1]),int(m[2]),int(m[3]=='true')
  if not 4<=k<=9:continue
  cols=[int(x.strip()) for x in m[4].split(',')];roots=[int(x.strip()) for x in m[5].split(',')]
  if len(cols)!=6 or not 1<=len(roots)<=6 or len(set(roots))!=len(roots):continue
  if any(w.bit_length()>64 for w in cols+roots):continue
  if any(w not in (0,(1<<64)-1) and w not in roots for w in cols):continue
  sub=gen.slice_mask(mask,i,b)
  # Independently replay sampled target; high half must be 1, low half 0.
  rows=[sum(((cols[j]>>r)&1)<<j for j in range(6)) for r in range(64)]
  if not all(((mask>>((row&~(1<<i))|(b<<i)))&1)==(r>=32) for r,row in enumerate(rows)):continue
  cr=[cols[j] for j in range(6) if j!=i]
  if any(w not in cr for w in roots):continue
  key=(sub,k)
  if key not in seen:seen[key]=dict(base=hex(sub),floor=k+1,columns=cr,roots=roots,source=f'L-meta-{n}',commit=c,blob=h[0].decode())
  counts[k+1]+=1
p.stdin.close();p.wait()
out={'head':head,'source_count':len(paths),'certificates':list(seen.values())}
Path(sys.argv[3]).write_text(json.dumps(out,indent=2))
print('proofs scanned',len(paths),'matched leaves',sum(counts.values()),counts,'distinct',len(seen))

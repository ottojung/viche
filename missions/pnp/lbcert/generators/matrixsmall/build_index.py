"""Rebuild literal, semantically audited small-matrix witnesses from a public revision."""
import argparse,json,re,subprocess
from pathlib import Path
from missions.pnp.lbcert.generators.promise import gen as p
from missions.pnp import gitctl


def build(revision):
 git=['git','--git-dir='+gitctl.MIRROR]
 ref=subprocess.check_output(git+['rev-parse',revision+'^{commit}'],text=True).strip()
 paths=subprocess.check_output(git+['grep','-l','-E','Represents\\.Represents|Represents\\.RepSizeAtMost',ref,'--','lean/PEqualNP/Outside'],text=True).splitlines()
 table={};nparse=0;nsol=0;historical=[]
 for i,path in enumerate(paths):
  if not re.fullmatch(r'.*:lean/PEqualNP/Outside/L_meta_\d+\.lean',path):continue
  gid=path.split('L_meta_')[-1].split('.')[0]
  src=subprocess.check_output(git+['show',path],text=True)
  st=re.search(r'(?ms)^theorem PEqualNP\.Outside\.L_meta_'+gid+r'\s*:\s*(.*?)\s*:=\s*by\b',src)
  if not st:continue
  q=p.parse(st[1])
  if not q or q[0]!='matrix' or not (2<=q[1]<=5 and 2<=q[2]<=5):continue
  nparse+=1;historical.append((gid,q))
  sol=p.lean_witness(q,src.replace('PEqualNP.CircuitLowerBounds.GateOp.','GateOp.'))
  if not sol:continue
  nsol+=1
  key,mp=p.iso_key(q)
  inv={v:i for i,v in enumerate(mp)}
  g,o=sol
  w=lambda x:inv.get(x,x)
  canon_sol=([(op,[w(x) for x in args]) for op,args in g],w(o))
  if not p.valid(('matrix',q[1],q[2],q[3],key[-1],q[-1]),canon_sol):raise RuntimeError(gid)
  key=':'.join(map(str,key[1:]))
  for pred in (['FanInTwo','Monotone2'] if all(op!='not' for op,_ in g) else ['FanInTwo']):
   k=key+':'+pred
   if k not in table or len(g)<len(table[k]['solution'][0]):table[k]={'source':gid,'solution':canon_sol}
  if i%500==0:print('progress',i,nparse,nsol,len(table),flush=True)
 return {"revision":ref,"classes":table}


def main():
 a=argparse.ArgumentParser(description=__doc__)
 a.add_argument("revision")
 a.add_argument("--output",required=True)
 x=a.parse_args()
 Path(x.output).write_text(json.dumps(build(x.revision),sort_keys=True,separators=(",",":")))


if __name__=="__main__":main()

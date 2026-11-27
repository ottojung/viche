"""Rebuild audited canonical gate data from an explicit local public revision."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from missions.pnp import gitctl
from . import gen
from ..promise import gen as promise


def build(ref):
    git=["git","--git-dir="+gitctl.MIRROR]
    ref=subprocess.check_output(git+["rev-parse",ref+"^{commit}"],text=True).strip()
    paths=subprocess.check_output(git+["grep","-l","RepSizeAtMost",ref,"--",
        "lean/PEqualNP/Outside"],text=True).splitlines()
    data={}
    for path in paths:
        m=re.fullmatch(r".*:lean/PEqualNP/Outside/L_meta_(\d+)\.lean",path)
        if not m:continue
        src=subprocess.check_output(git+["show",path],text=True)
        stmt=re.search(r"(?ms)^theorem PEqualNP\.Outside\.L_meta_"+m[1]+r"\s*:\s*(.*?)\s*:=\s*by\b",src)
        if not stmt:continue
        p=gen.parse(stmt[1])
        if not p:continue
        # A gate list is data, not executable Lean source.
        sol=promise.lean_witness(p,src.replace("PEqualNP.CircuitLowerBounds.GateOp.","GateOp."))
        if not sol or not 0<=sol[1]<16+len(sol[0]):continue
        key,mp=gen.canon(p[4]&((1<<64)-1));inv={v:i for i,v in enumerate(mp)}
        def w(i):return inv.get(i,i)
        gates,out=sol
        sol=([[op,[w(i) for i in args]] for op,args in gates],w(out))
        cp=("matrix",8,8,p[3],int.from_bytes(bytes.fromhex(key),"little"),"Monotone2")
        if not promise.valid(cp,sol):raise ValueError("canonical witness audit failed")
        if key not in data or len(gates)<len(data[key]["solution"][0]):
            data[key]={"source":"L-meta-"+m[1],"solution":sol}
    return json.dumps({"revision":ref,"classes":data},separators=(",",":"),sort_keys=True)


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("revision")
    a.add_argument("--output",required=True)
    x=a.parse_args()
    data=build(x.revision)
    Path(x.output).write_text(data)
    print(hashlib.sha256(data.encode()).hexdigest())


if __name__=="__main__":main()

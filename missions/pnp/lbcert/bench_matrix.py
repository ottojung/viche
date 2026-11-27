"""Read-only reproducible benchmark on a local public upstream revision."""
import argparse
import json
import re
import subprocess
import time

from missions.pnp import gitctl, validate
from .generators.promise import gen, anneal


def cases(ref):
    git=["git","--git-dir="+gitctl.MIRROR]
    text=subprocess.check_output(git+["grep","-l","RepSizeAtMost",ref,"--",
        "lean/PEqualNP/Outside"],text=True)
    for line in text.splitlines():
        path=line.split(":",1)[1]
        num=re.fullmatch(r"lean/PEqualNP/Outside/L_meta_(\d+)\.lean",path)
        if not num:continue
        src=subprocess.check_output(git+["show",ref+":"+path],text=True)
        mod="PEqualNP.Outside.L_meta_"+num[1]
        m=re.search(r"(?ms)^theorem "+re.escape(mod)+r"\s*:\s*(.*?)\s*:=\s*by\b",src)
        if not m:continue
        stmt=m[1].strip();p=gen.parse(stmt)
        if not p or p[:3]!=("matrix",8,8):continue
        imports=re.findall(r"(?m)^import\s+(\S+)",src)
        yield {"id":"L-meta-"+num[1],"module":mod,"statement":stmt,
               "file":path,"imports":imports},p


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--ref",default="refs/remotes/upstream/main")
    a.add_argument("--limit",type=int,default=0)
    a.add_argument("--anneal",action="store_true")
    args=a.parse_args()
    totals={"cases":0,"heuristic":0,"mixed_extra":0,"anneal":0,"mixed_exclusive":0,
            "static_validated":0}
    start=time.monotonic()
    for q,p in cases(args.ref):
        totals["cases"]+=1
        old=gen.heuristic(p)
        new=None if old else gen.matrix_mixed(p)
        alt=anneal.search(p,gen) if args.anneal and not old else None
        for sol in (old,new,alt):
            if sol and not gen.valid(p,sol):raise ValueError("audit failure")
        totals["heuristic"]+=bool(old)
        totals["mixed_extra"]+=bool(new)
        totals["anneal"]+=bool(alt)
        totals["mixed_exclusive"]+=bool(new and not alt)
        if old or new:
            validate.validate(q,gen.emit(q["id"],q["statement"],p,old or new).encode())
            totals["static_validated"]+=1
        if args.limit and totals["cases"]>=args.limit:break
    print(json.dumps(dict(totals,seconds=round(time.monotonic()-start,3),
                          ref=args.ref,kernel_checked=False)))
    return 0


if __name__=="__main__":raise SystemExit(main())

"""Reproducible remote kernel-check benchmark of the new certificate generator."""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import time

from . import certificate, knowledge, obligations
from .. import config

def rows():
    with closing(sqlite3.connect("file:"+str(Path(config.CACHE_DIR)/"proof-corpus.sqlite")+"?mode=ro",uri=True)) as db:
        revision=db.execute("SELECT value FROM metadata WHERE key='revision'").fetchone()[0]
        result=[]
        for path,stmt,imports in db.execute("SELECT path,statement,imports FROM proof ORDER BY path"):
            if not certificate.parse(stmt):continue
            module=path.removeprefix("lean/").removesuffix(".lean").replace("/",".")
            stem=Path(path).stem
            gid=stem.replace("_","-")
            if not config.GAP_ID_RE.fullmatch(gid):continue
            result.append({"id":gid,"file":path,"module":module,"statement":stmt,"imports":json.loads(imports)})
    return revision,result

def acceptable(log,name):
    if re.search(r"'"+re.escape(name)+r"' does not depend on any axioms",log):return True
    m=re.search(r"'"+re.escape(name)+r"' depends on axioms: \[([^\]]*)\]",log)
    return bool(m and {x.strip() for x in m[1].split(",") if x.strip()}<={"propext","Classical.choice","Quot.sound"})

def run(base,output,limit=None):
    revision,items=rows()
    if limit:items=items[:limit]
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    seen={}
    if output.exists():
        for line in output.read_text().splitlines():
            try:
                row=json.loads(line);seen[row["id"]]=row
            except (ValueError,KeyError):continue
    for meta in items:
        z=certificate.render(meta)
        source=z.get("candidate")
        digest=knowledge.digest(source.encode()) if source else None
        old=seen.get(meta["id"])
        if old and old.get("base")==base and old.get("source_digest")==digest and old.get("status")=="kernel_checked":continue
        start=time.monotonic()
        row={"id":meta["id"],"base":base,"corpus":revision,"source_digest":digest,
             "gates":z.get("gates"),"bound":z.get("bound"),"status":z["status"]}
        if source:
            try:
                proc,r=obligations.method_check(base,"benchmark:"+meta["id"]+":"+digest,
                                             source+"\n#print axioms "+meta["module"]+"\n")
                row["compiler_status"]=r.get("status")
                row["lean_ms"]=r.get("elapsed_ms")
                row["status"]="kernel_checked" if proc.returncode==0 and r.get("status")=="elaborated" and acceptable(r.get("diagnostic",""),meta["module"]) else "not_verified"
                if row["status"]!="kernel_checked":
                    row["diagnostic"]=r.get("diagnostic",proc.stderr)[-1500:]
            except (OSError,ValueError,subprocess.SubprocessError) as exc:
                row.update(status="infrastructure",diagnostic=str(exc)[:1000])
        row["wall_ms"]=round(1000*(time.monotonic()-start))
        with output.open("a") as f:
            f.write(json.dumps(row,ensure_ascii=False)+"\n");f.flush();os.fsync(f.fileno())
        seen[meta["id"]]=row
        print(meta["id"],row["status"],row.get("lean_ms"),row["wall_ms"],flush=True)
    checked=sum(seen.get(m["id"],{}).get("status")=="kernel_checked" for m in items)
    print(json.dumps({"total":len(items),"kernel_checked":checked,"base":base,"corpus":revision,"output":str(output)}),flush=True)
    return int(checked!=len(items))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base",required=True);p.add_argument("--output",required=True);p.add_argument("--limit",type=int)
    a=p.parse_args();return run(a.base,a.output,a.limit)
if __name__=="__main__":raise SystemExit(main())

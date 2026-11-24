"""Composable exact Lean obligations, checked independently in a pinned workspace."""
import argparse
from contextlib import closing
import hashlib
import base64
import json
from pathlib import Path
import re
import subprocess
import tempfile
import time

from .. import assignment, state, support
from . import knowledge as k

def binding():
    cwd=Path.cwd()
    b=assignment.binding(cwd)
    w=assignment.workspace(cwd)
    if not b or not w:raise ValueError("run from your bound research workspace")
    rec=state.load(b[0])
    if not support.active(rec) or rec["lease"]!=b[1]:raise ValueError("obsolete assignment")
    work=w[1].resolve()
    base=subprocess.check_output(["git","-C",str(work),"rev-parse","HEAD"],text=True,timeout=5).strip()
    return rec,work,base

def public_toolchain(base):
    """Method research uses an exact public upstream commit, not a desk lease."""
    from .. import gitctl
    if not re.fullmatch(r"[0-9a-f]{40}",base or ""):raise ValueError("invalid base")
    prefix=["git","--git-dir="+gitctl.MIRROR]
    subprocess.run(prefix+["merge-base","--is-ancestor",base,"refs/remotes/upstream/main"],
                   check=True,timeout=10,capture_output=True)
    return subprocess.check_output(prefix+["show",base+":lean/lean-toolchain"],text=True,timeout=5).strip()

def method_check(base,oid,source):
    toolchain=public_toolchain(base)
    relay=str(Path.home()/".local/bin/marceline-request")
    status=json.loads(subprocess.check_output([relay,"status",base],text=True,timeout=15))
    if not status.get("base_available"):raise ValueError("remote pinned base unavailable")
    raw=source.encode("utf-8")
    if len(raw)>512*1024:raise ValueError("method source exceeds 512 KiB")
    identity=k.digest(("method:"+oid).encode())
    job={"version":1,"mode":"scratch","base":base,"toolchain":toolchain,
         "attempt":identity[:24]+"-"+identity[24:40],"wall_seconds":600,"rss_mib":8192,
         "source_sha256":k.digest(raw),"source_b64":base64.b64encode(raw).decode("ascii")}
    job["job"]=k.digest(k.canon(job).encode())
    with tempfile.NamedTemporaryFile(mode="w",suffix=".json") as f:
        f.write(k.canon(job));f.flush()
        proc=subprocess.run([relay,"lean-check",f.name],capture_output=True,text=True,timeout=1200)
    try:
        result=json.loads(proc.stdout)["result"]
        if any(result.get(x)!=job[x] for x in ("job","base","source_sha256","toolchain","attempt")):result={}
    except (ValueError,KeyError,TypeError):result={}
    return proc,result


def symbol(oid):
    return "viche_o_"+oid

def plan(c, oid):
    seen=set(); result=[]
    def visit(i):
        if i in seen:return
        obj=k.get(c,i)
        if obj["kind"]!="obligation":raise ValueError("not an obligation")
        seen.add(i)
        for dep in obj["dependencies"]:visit(dep)
        result.append(obj)
    visit(oid)
    return result

def checked_body(c,node,base):
    for row in c.execute("SELECT artifact,result FROM proof WHERE node=? AND base=? ORDER BY checked DESC",(node,base)):
        d=json.loads(row["result"])
        if d.get("status")=="kernel_checked":return k.artifact(row["artifact"]).read_text()
    raise ValueError("unresolved dependency "+node)

def build(c,oid,body=None):
    nodes=plan(c,oid); base=nodes[-1]["base"]
    imports=set(); lines=[]
    for o in nodes:
        meta=json.loads(o["detail"])
        imports.update(meta["imports"])
        text=body if o["id"]==oid and body is not None else checked_body(c,o["id"],base)
        lines.append(f"theorem {symbol(o['id'])} : {o['statement']} :=\n{text}\n")
    src="\n".join("import "+x for x in sorted(imports))+"\n\n"+"\n".join(lines)
    return src+"\n#print axioms "+symbol(oid)+"\n"

def candidate(c,oid,rec,base):
    from .. import validate
    nodes=plan(c,oid)
    if nodes[-1]["base"]!=base:raise ValueError("candidate base mismatch")
    imports={"Mathlib"};lines=[]
    module=rec["module"];namespace=module+"_aux"
    for node in nodes:
        imports.update(json.loads(node["detail"])["imports"])
        lines.append(f"lemma {symbol(node['id'])} : {node['statement']} :=\n{checked_body(c,node['id'],base)}\n")
    src="\n".join("import "+x for x in sorted(imports,key=lambda x:(x!="Mathlib",x)))
    src+="\n\nnamespace "+namespace+"\n"+"\n".join(lines)+"\nend "+namespace+"\n\n"
    src+=f"theorem {module} : {rec['statement']} := by\n  exact {namespace}.{symbol(oid)}\n"
    validate.validate({"id":rec["gap_id"],"file":rec["path"],"module":module,
                       "statement":rec["statement"],"imports":rec["imports"]},src.encode())
    return src


def clean_body(text):
    if not text.strip() or re.search(r"\b(sorry|admit|sorryAx|axiom|unsafe|run_tac|run_cmd)\b",text):
        raise ValueError("proof body must be complete, without new axioms or placeholders")

def verify_output(output,oid):
    # Lean emits either no axioms or an explicit list. Missing/truncated output
    # is not verification. Do not equate arbitrary scratch elaboration with proof.
    name=symbol(oid)
    if re.search(r"'"+name+r"' does not depend on any axioms",output):
        return True
    m=re.search(r"'"+name+r"' depends on axioms: \[([^\]]*)\]",output)
    if not m:return False
    return {x.strip() for x in m[1].split(",") if x.strip()} <= {"propext","Classical.choice","Quot.sound"}

def solve(c,oid,path,local=False,method=False):
    obj=k.get(c,oid)
    if obj["kind"]!="obligation":raise ValueError("not an obligation")
    if method:
        if local:raise ValueError("method check uses the pinned remote compiler")
        rec=None;work=None;base=obj["base"]
    else:rec,work,base=binding()
    if obj["base"]!=base:raise ValueError("obligation requires another exact base")
    bodyhash=k.store_artifact(path)
    raw=k.artifact(bodyhash).read_text();clean_body(raw)
    src=build(c,oid,raw);sourcehash=hashlib.sha256(src.encode()).hexdigest()
    if method:
        proc,result=method_check(base,oid,src)
    else:
        with tempfile.NamedTemporaryFile(mode="w",suffix=".lean",prefix=".obligation-",dir=work) as f:
            f.write(src);f.flush()
            if local:
                import os
                env=dict(os.environ,PYTHONPATH="/var/lib/lubko/wd/viche")
                proc=subprocess.run([str(Path.home()/".local/bin/python3"),"-m","missions.pnp.compile",
                                     "--light","--","lake","env","lean",f.name],cwd=work/"lean",
                                    env=env,capture_output=True,text=True,timeout=1200)
                result={"status":"elaborated" if proc.returncode==0 else "not_elaborated",
                        "exit_code":proc.returncode,"base":base,"source_sha256":sourcehash,
                        "diagnostic":(proc.stdout+"\n"+proc.stderr)[-16000:],"mode":"local-managed"}
            else:
                proc=subprocess.run([str(Path.home()/".local/bin/pnp-remote-check"),"--scratch",f.name],
                                    capture_output=True,text=True,timeout=1200)
                try:
                    receipt=json.loads(proc.stdout);result=receipt.get("result",receipt)
                except (ValueError,AttributeError):result={}
    ok=(proc.returncode==0 and result.get("status")=="elaborated" and result.get("exit_code")==0
        and result.get("base")==base and result.get("source_sha256")==sourcehash
        and verify_output(result.get("diagnostic",""),oid))
    result={"status":"kernel_checked" if ok else "not_verified","compiler":result,
            "stderr":proc.stderr[-1000:],"gap":rec["gap_id"] if rec else None,
            "attempt":support.attempt(rec) if rec else "method-research"}
    with c:
        c.execute("INSERT OR REPLACE INTO proof VALUES(?,?,?,?,?,?)",
                  (oid,base,bodyhash,sourcehash,k.canon(result),time.time()))
    return result

def ready(c,base=None,family=None):
    rows=[]
    for row in c.execute("SELECT id FROM object WHERE kind='obligation' ORDER BY created"):
        obj=k.get(c,row["id"])
        if base and obj["base"]!=base or family and obj["family"]!=family:continue
        try:
            checked_body(c,obj["id"],obj["base"]); status="checked"
        except ValueError:
            try:
                for dep in obj["dependencies"]:checked_body(c,dep,obj["base"])
                status="ready"
            except ValueError:status="blocked"
        rows.append({"id":obj["id"],"symbol":symbol(obj["id"]),"statement":obj["statement"],
                     "family":obj["family"],"base":obj["base"],"status":status,
                     "dependencies":obj["dependencies"],"assignments":obj["assignments"]})
    return rows

def fork(c, oid, base):
    mapping={}
    for old in plan(c,oid):
        deps=[mapping[d] for d in old["dependencies"]]
        stmt=old["statement"]
        for a,b in mapping.items():stmt=stmt.replace(symbol(a),symbol(b))
        new=k.add(c,"obligation",old["family"],stmt,old["detail"],old["provenance"]+" / rebased from "+old["id"],
                  base=base,deps=deps)
        k.link(c,new,old["id"],"instantiates")
        mapping[old["id"]]=new
    return mapping

def migrate_body(c,old,new,mapping,output):
    obj=k.get(c,old)
    text=checked_body(c,old,obj["base"])
    for a,b in mapping.items():text=text.replace(symbol(a),symbol(b))
    with Path(output).open("x") as f:f.write(text)
    return {"new":new,"body":output,"note":"Recheck this body on the new base; no verification transferred."}


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("request");a.add_argument("--statement",required=True);a.add_argument("--family")
    a.add_argument("--requires",action="append",default=[]);a.add_argument("--import",dest="imports",action="append",default=[])
    a.add_argument("--base",help="independent method research on an exact public upstream revision");a.add_argument("--provenance")
    a=sub.add_parser("ready");a.add_argument("--family");a.add_argument("--base")
    a=sub.add_parser("fork");a.add_argument("id")
    a=sub.add_parser("body");a.add_argument("id");a.add_argument("--output",required=True)
    a=sub.add_parser("assign");a.add_argument("id");a.add_argument("worker")
    a=sub.add_parser("solve");a.add_argument("id");a.add_argument("body");a.add_argument("--local",action="store_true");a.add_argument("--method",action="store_true")
    a=sub.add_parser("assemble");a.add_argument("id");a.add_argument("--output",required=True);a.add_argument("--candidate",action="store_true")
    a=sub.add_parser("show");a.add_argument("id")
    a=p.parse_args()
    with closing(k.db()) as c:
        if a.cmd=="request":
            imports=a.imports or ["PEqualNP.Defs"]
            if a.base:
                public_toolchain(a.base)
                if not a.family or not a.provenance:raise ValueError("method request requires --family and --provenance")
                r=None;b=a.base
            else:r,w,b=binding()
            if any(not re.fullmatch(r"[A-Za-z0-9_.]+",i) for i in imports):raise ValueError("invalid import")
            fam=a.family or k.family((r.get("gap_title") or "")+" "+r["statement"])
            prov=a.provenance if r is None else f"{r['gap_id']} / {support.attempt(r)}"
            oid=k.add(c,"obligation",fam,a.statement,k.canon({"imports":sorted(set(imports))}),
                      prov,base=b,deps=a.requires)
            out={"id":oid,"symbol":symbol(oid),"statement":a.statement}
        elif a.cmd=="ready":out=ready(c,a.base,a.family)
        elif a.cmd=="show":out=k.get(c,a.id)
        elif a.cmd=="fork":
            r,w,b=binding();out=fork(c,a.id,b)
        elif a.cmd=="body":
            obj=k.get(c,a.id)
            text=checked_body(c,a.id,obj["base"])
            with Path(a.output).open("x") as f:f.write(text)
            out={"path":a.output,"base":obj["base"]}
        elif a.cmd=="assign":
            r,w,b=binding();o=k.get(c,a.id)
            if o["base"]!=b:raise ValueError("base mismatch")
            with c:
                c.execute("INSERT OR IGNORE INTO assignment VALUES(?,?,?,?)",(a.id,support.attempt(r),a.worker,time.time()))
                owner=c.execute("SELECT worker FROM assignment WHERE node=? AND attempt=?",(a.id,support.attempt(r))).fetchone()[0]
                if owner!=a.worker:raise ValueError("already assigned to "+owner+"; coordinate with Executive")
            out={"assigned":a.id,"worker":a.worker}
        elif a.cmd=="solve":out=solve(c,a.id,a.body,a.local,a.method)
        else:
            if a.candidate:
                r,w,b=binding();text=candidate(c,a.id,r,b)
            else:text=build(c,a.id)
            p=Path(a.output)
            with p.open("x") as f:f.write(text)
            out={"path":str(p),"sha256":k.digest(text.encode()),"note":"Final candidate needs the normal submit/check pipeline; graph verification is not upstream acceptance."}
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 1 if a.cmd=="solve" and out["status"]!="kernel_checked" else 0

if __name__=="__main__":raise SystemExit(main())

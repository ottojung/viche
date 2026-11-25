"""Composable exact Lean obligations, checked independently in a pinned workspace."""
import argparse
from contextlib import closing
import hashlib
import os
import base64
import json
from pathlib import Path
import re
import subprocess
import tempfile
import time
import unicodedata

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
    for row in c.execute("SELECT node,base,artifact,source_digest,result FROM proof WHERE node=? AND base=? ORDER BY checked DESC",(node,base)):
        if verified_record(row):return k.artifact(row["artifact"]).read_text()
    raise ValueError("unresolved dependency "+node+"; inspect obligations show "+node+" and solve/check it before assembly")

def declaration_options(meta):
    opts=meta.get("options",{})
    if not isinstance(opts,dict) or set(opts)-{"maxHeartbeats","maxRecDepth","synthInstance.maxSize","synthInstance.maxHeartbeats"}:
        raise ValueError("invalid Lean options")
    if any(type(v) is not int or v<0 or v>10_000_000 for v in opts.values()):
        raise ValueError("invalid Lean option value")
    return "".join(f"set_option {k} {v} in\n" for k,v in sorted(opts.items()))


def proof_parts(node,text):
    from . import dnf_reflection
    if text.startswith(dnf_reflection.MARKER):
        return dnf_reflection.unpack(text,node["statement"],"viche_r_"+node["id"])
    clean_body(text)
    return "",text

def build(c,oid,body=None):
    nodes=plan(c,oid); base=nodes[-1]["base"]
    imports={"Lean"}; lines=[]
    for o in nodes:
        meta=json.loads(o["detail"])
        imports.update(meta["imports"])
        clean_term(o["statement"])
        if any(not re.fullmatch(r"[A-Za-z0-9_.]+",i) for i in imports):raise ValueError("invalid import")
        text=body if o["id"]==oid and body is not None else checked_body(c,o["id"],base)
        helpers,text=proof_parts(o,text)
        clean_term(text)
        lines.append(helpers+declaration_options(meta)+f"theorem {symbol(o['id'])} : {o['statement']} :=\n{text}\n")
    src="\n".join("import "+x for x in sorted(imports))+"\n\n"+"\n".join(lines)
    clean_source(src)
    return src+axiom_guard(symbol(oid))

def candidate(c,oid,rec,base):
    from .. import validate
    nodes=plan(c,oid)
    if nodes[-1]["base"]!=base:raise ValueError("candidate base mismatch")
    imports={"Mathlib"};lines=[]
    module=rec["module"];namespace=module+"_aux"
    for node in nodes:
        imports.update(json.loads(node["detail"])["imports"])
        helpers,text=proof_parts(node,checked_body(c,node["id"],base))
        lines.append(helpers+declaration_options(json.loads(node["detail"]))+f"lemma {symbol(node['id'])} : {node['statement']} :=\n{text}\n")
    src="\n".join("import "+x for x in sorted(imports,key=lambda x:(x!="Mathlib",x)))
    src+="\n\nnamespace "+namespace+"\n"+"\n".join(lines)+"\nend "+namespace+"\n\n"
    src+=f"theorem {module} : {rec['statement']} := by\n  exact {namespace}.{symbol(oid)}\n"
    validate.validate({"id":rec["gap_id"],"file":rec["path"],"module":module,
                       "statement":rec["statement"],"imports":rec["imports"]},src.encode())
    return src


# Proof terms are data. The only executable verification command in a
# generated source is the fixed, trusted axiom guard below.
FORBIDDEN = re.compile(r"(?<![\w.])(?:sorry|admit|sorryAx|axiom|unsafe|native_decide|run_tac|run_cmd|initialize|macro|syntax|notation|elab|trace|dbg_trace|logInfo|logWarning|logError)\b")
DECLARATIONS = re.compile(r"(?<![\w.])(?:import|theorem|lemma|def|abbrev|namespace|section|end|mutual|attribute|instance|open|export|variable|universe)\b")
OPTIONS = {"maxHeartbeats","maxRecDepth","synthInstance.maxSize","synthInstance.maxHeartbeats"}

def uncomment(text):
    # Lean has nested block comments. Preserve newlines and reject an open
    # comment rather than allowing it to swallow the verifier's suffix.
    out=[];i=0;depth=0
    while i<len(text):
        if text.startswith("/-",i):depth+=1;i+=2;continue
        if text.startswith("-/",i):
            if not depth:raise ValueError("unbalanced Lean comment")
            depth-=1;i+=2;continue
        if not depth and text.startswith("--",i):
            j=text.find("\n",i);i=len(text) if j<0 else j;continue
        if not depth or text[i]=="\n":out.append(text[i])
        i+=1
    if depth:raise ValueError("unterminated Lean comment")
    return "".join(out)

def clean_source(text):
    code=unicodedata.normalize("NFKC",uncomment(text))
    if any(unicodedata.category(x) in ("Cf","Cc") and x not in "\n\r\t" for x in code):
        raise ValueError("control character in Lean input")
    if any(x in code for x in ('"', '#', '«', '»')) or FORBIDDEN.search(code):
        raise ValueError("untrusted Lean command, trace, string or non-kernel proof")
    options=list(re.finditer(r"(?m)^\s*set_option\s+([A-Za-z.]+)\s+(\d+)\s+in\s*$",code))
    if len(options)!=len(re.findall(r"(?<![\w.])set_option\b",code)) or any(
        m[1] not in OPTIONS or int(m[2])>10_000_000 for m in options):
        raise ValueError("only scoped, approved resource options are permitted")
    return code

def clean_term(text):
    code=clean_source(text)
    if not code.strip() or DECLARATIONS.search(code):
        raise ValueError("expected a complete Lean term, not declarations")

def clean_body(text):
    from . import dnf_reflection
    if text.startswith(dnf_reflection.MARKER):
        # Parsed and verified against the exact statement by proof_parts.
        if not isinstance(json.loads(text[len(dnf_reflection.MARKER):]),dict):
            raise ValueError("invalid reflected proof artifact")
        return
    clean_term(text)

def axiom_guard(name):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*",name):raise ValueError("invalid theorem name")
    return ("\nopen Lean in\nrun_cmd do\n"
            f"  let axs ← Lean.collectAxioms `{name}\n"
            "  for ax in axs do\n"
            "    unless #[`propext, `Classical.choice, `Quot.sound].contains ax do\n"
            '      throwError "forbidden axiom {ax}"\n'
            f"#print axioms {name}\n")

def verify_report(output,name):
    # Require exactly one report, as a complete final nonblank line.
    # A trace with a favorable substring cannot hide a later bad report.
    if not isinstance(output,str):return False
    prefix="'"+name+"'"
    lines=[x.strip() for x in output.splitlines() if x.strip()]
    if not lines or sum(prefix in x and ("depends on axioms" in x or "does not depend on any axioms" in x) for x in lines)!=1:return False
    if lines[-1]==prefix+" does not depend on any axioms":return True
    m=re.fullmatch(re.escape(prefix)+r" depends on axioms: \[([^\]]*)\]",lines[-1])
    if not m:return False
    return {x.strip() for x in m[1].split(",") if x.strip()} <= {"propext","Classical.choice","Quot.sound"}

def verify_output(output,oid):
    return verify_report(output,symbol(oid))

def source_verified(source,oid,legacy=False):
    suffix=axiom_guard(symbol(oid))
    if not source.endswith(suffix):
        if not legacy:return False
        suffix="\n#print axioms "+symbol(oid)+"\n"
        if not source.endswith(suffix):return False
    try:
        clean_source(source[:-len(suffix)])
    except ValueError:return False
    return True

def verified_record(row):
    """Read only intact evidence. Legacy receipts need the same strict audit;
    new receipts additionally have a compiler-enforced axiom guard."""
    try:
        d=json.loads(row["result"]);r=d["compiler"]
        if not (d["status"]=="kernel_checked" and r["status"]=="elaborated" and r["exit_code"]==0
                and r["base"]==row["base"] and r["source_sha256"]==row["source_digest"]
                and verify_output(r["diagnostic"],row["node"])):return False
        clean_body(k.artifact(row["artifact"]).read_text())
        return source_verified(k.artifact(row["source_digest"]).read_text(),row["node"],legacy=True)
    except (OSError,ValueError,KeyError,TypeError):return False

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
    src=build(c,oid,raw);sourcehash=k.store_bytes(src.encode())
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
        and source_verified(src,oid) and verify_output(result.get("diagnostic",""),oid))
    result={"status":"kernel_checked" if ok else "not_verified","compiler":result,
            "stderr":proc.stderr[-1000:],"gap":rec["gap_id"] if rec else None,
            "attempt":support.attempt(rec) if rec else "method-research",
            "submit_agent":os.environ.get("ANTONINA_AGENT_ID"),"collect_agent":os.environ.get("ANTONINA_AGENT_ID")}
    with c:
        prev=c.execute("SELECT node,base,artifact,source_digest,result FROM proof WHERE node=? AND base=? AND artifact=?",(oid,base,bodyhash)).fetchone()
        if ok or not prev or not verified_record(prev):
            c.execute("INSERT OR REPLACE INTO proof VALUES(?,?,?,?,?,?)",
                      (oid,base,bodyhash,sourcehash,k.canon(result),time.time()))
    return result

def ready(c,base=None,family=None):
    rows=[];checked=set()
    try:
        verified=c.execute("SELECT node,base,artifact,source_digest,result FROM proof WHERE json_extract(result,'$.status')='kernel_checked'").fetchall()
    except Exception:
        verified=[row for row in c.execute("SELECT node,base,artifact,source_digest,result FROM proof")
                  if json.loads(row["result"]).get("status")=="kernel_checked"]
    for row in verified:
        if verified_record(row):checked.add((row["node"],row["base"]))
    for row in c.execute("SELECT id,statement,family,base FROM object WHERE kind='obligation' ORDER BY created"):
        obj=dict(row)
        if base and obj["base"]!=base:continue
        if family and not c.execute("SELECT 1 FROM origin WHERE node=? AND family=?",(obj["id"],family)).fetchone():continue
        deps=[r[0] for r in c.execute("SELECT target FROM edge WHERE source=? AND relation='requires' ORDER BY target",(obj["id"],))]
        status="checked" if (obj["id"],obj["base"]) in checked else "ready" if all((d,obj["base"]) in checked for d in deps) else "blocked"
        rows.append({**obj,"symbol":symbol(obj["id"]),"status":status,"dependencies":deps,
                     "assignments":[dict(r) for r in c.execute("SELECT attempt,worker,at FROM assignment WHERE node=?",(obj["id"],))]})
    return rows


def fork(c, oid, base):
    mapping={}
    for old in plan(c,oid):
        deps=[mapping[d] for d in old["dependencies"]]
        stmt=old["statement"]
        for a,b in mapping.items():stmt=stmt.replace(symbol(a),symbol(b))
        new=k.add(c,"obligation",old["family"],stmt,old["detail"],old["provenance"]+" / rebased from "+old["id"],
                  base=base,deps=deps)
        if new!=old["id"]:k.link(c,new,old["id"],"instantiates")
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
    a=sub.add_parser("ready");a.add_argument("--family");a.add_argument("--base");a.add_argument("--current",action="store_true");a.add_argument("--full",action="store_true")
    a=sub.add_parser("fork");a.add_argument("id")
    a=sub.add_parser("body");a.add_argument("id");a.add_argument("--output",required=True);a.add_argument("--for-node")
    a=sub.add_parser("assign");a.add_argument("id");a.add_argument("worker")
    a=sub.add_parser("solve");a.add_argument("id");a.add_argument("body");a.add_argument("--local",action="store_true");a.add_argument("--method",action="store_true")
    a.add_argument("--async",dest="asynchronous",action="store_true");a.add_argument("--wall",type=int,default=600);a.add_argument("--rss-mib",type=int,default=8192);a.add_argument("--retry",action="store_true",help="retry a terminal unsuccessful async check")
    a=sub.add_parser("collect");a.add_argument("id");a.add_argument("--poll",action="store_true");a.add_argument("--timeout",type=int,default=1100)
    a=sub.add_parser("pending",help="list in-flight checks, or all with --all");a.add_argument("--all",action="store_true");sub.add_parser("reconcile")
    a=sub.add_parser("reuse");a.add_argument("old");a.add_argument("new");a.add_argument("--method",action="store_true");a.add_argument("--async",dest="asynchronous",action="store_true")
    a=sub.add_parser("assemble");a.add_argument("id");a.add_argument("--output",required=True);a.add_argument("--candidate",action="store_true")
    a=sub.add_parser("show");a.add_argument("id");a.add_argument("--full",action="store_true")
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
            clean_term(a.statement)
            fam=a.family or k.family((r.get("gap_title") or "")+" "+r["statement"])
            prov=a.provenance if r is None else f"{r['gap_id']} / {support.attempt(r)}"
            oid=k.add(c,"obligation",fam,a.statement,k.canon({"imports":sorted(set(imports))}),
                      prov,base=b,deps=a.requires)
            out={"id":oid,"symbol":symbol(oid),"statement":a.statement}
        elif a.cmd=="ready":
            out=ready(c,a.base,a.family)
            if a.current:
                r,w,b=binding();out=[dict(x,same_base=x["base"]==b) for x in out if k.belongs(c,x["id"],r["gap_id"]+" / ")]
            if not a.full:out=[dict(x,statement=x["statement"][:450]) for x in out]
        elif a.cmd=="show":
            out=k.get(c,a.id)
            if not a.full:
                for check in out["checks"]:
                    r=json.loads(check["result"]);compiler=r.get("compiler") or {}
                    check["result"]={"status":r.get("status"),"compiler_status":compiler.get("status"),
                        "elapsed_ms":compiler.get("elapsed_ms"),"diagnostic":compiler.get("diagnostic","")[-1500:],
                        "submit_agent":r.get("submit_agent")}

        elif a.cmd=="fork":
            r,w,b=binding();out=fork(c,a.id,b)
        elif a.cmd=="body":
            obj=k.get(c,a.id)
            text=checked_body(c,a.id,obj["base"])
            if a.for_node:
                mapping={}
                for new in plan(c,a.for_node):
                    for link in new["links"]:
                        if link["source"]==new["id"] and link["relation"]=="instantiates":
                            mapping[link["target"]]=new["id"]
                if mapping.get(a.id)!=a.for_node:raise ValueError("target is not a fork of this node")
                for old,new in mapping.items():text=text.replace(symbol(old),symbol(new))
            with Path(a.output).open("x") as f:f.write(text)
            out={"path":a.output,"base":obj["base"],"recheck":bool(a.for_node)}
        elif a.cmd=="assign":
            r,w,b=binding();o=k.get(c,a.id)
            if o["base"]!=b:raise ValueError("base mismatch")
            with c:
                c.execute("INSERT OR IGNORE INTO assignment VALUES(?,?,?,?)",(a.id,support.attempt(r),a.worker,time.time()))
                owner=c.execute("SELECT worker FROM assignment WHERE node=? AND attempt=?",(a.id,support.attempt(r))).fetchone()[0]
                if owner!=a.worker:raise ValueError("already assigned to "+owner+"; coordinate with Executive")
            out={"assigned":a.id,"worker":a.worker}
        elif a.cmd=="solve":
            if a.asynchronous:
                from . import async_check
                if a.local:raise ValueError("async uses remote Lean")
                out=async_check.submit(c,a.id,a.body,a.method,a.wall,a.rss_mib,a.retry)
            else:
                if a.retry or a.wall!=600 or a.rss_mib!=8192:raise ValueError("retry and resource overrides require --async")
                out=solve(c,a.id,a.body,a.local,a.method)
        elif a.cmd=="collect":
            from . import async_check
            out=async_check.collect(c,a.id,1 if a.poll else a.timeout)
        elif a.cmd=="pending":
            from . import async_check
            out=async_check.pending(c)
            if not a.all:out=[x for x in out if x["state"] in ("queued","submitting")]
        elif a.cmd=="reconcile":
            from . import async_check
            out=async_check.reconcile(c)
        elif a.cmd=="reuse":
            old=k.get(c,a.old);text=checked_body(c,a.old,old["base"])
            mapping={}
            for new in plan(c,a.new):
                for link in new["links"]:
                    if link["source"]==new["id"] and link["relation"]=="instantiates":mapping[link["target"]]=new["id"]
            if a.old!=a.new and mapping.get(a.old)!=a.new:raise ValueError("new node is not a fork of old")
            for src,dst in mapping.items():text=text.replace(symbol(src),symbol(dst))
            with tempfile.NamedTemporaryFile(mode="w",suffix=".body") as f:
                f.write(text);f.flush()
                if a.asynchronous:
                    from . import async_check
                    out=async_check.submit(c,a.new,f.name,a.method)
                else:out=solve(c,a.new,f.name,method=a.method)
        else:
            if a.candidate:
                r,w,b=binding();text=candidate(c,a.id,r,b)
            else:text=build(c,a.id)
            p=Path(a.output)
            with p.open("x") as f:f.write(text)
            out={"path":str(p),"sha256":k.digest(text.encode()),"note":"Final candidate needs the normal submit/check pipeline; graph verification is not upstream acceptance."}
    print(json.dumps(out,ensure_ascii=False,indent=2))
    if a.cmd=="collect":return 0 if out["status"]=="kernel_checked" else 75 if out["status"] in ("pending","submitting") else 1
    if a.cmd in ("solve","reuse") and not a.asynchronous:return 0 if out["status"]=="kernel_checked" else 1
    return 0

if __name__=="__main__":raise SystemExit(main())

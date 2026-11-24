"""Durable, asynchronous exact-graph Lean checks; collect without rebuilding."""
from contextlib import closing
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time

from . import knowledge as k
from .. import support

RELAY = str(Path.home()/".local/bin/marceline-request")
ID = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}")

def table(c):
    c.execute("""CREATE TABLE IF NOT EXISTS pending_check(
        id TEXT PRIMARY KEY, node TEXT REFERENCES object(id), base TEXT,
        body TEXT, source TEXT, identity TEXT, request TEXT, at REAL,
        state TEXT, result TEXT
    )""")
    c.commit()

def identity(base,toolchain,attempt,source,wall=600,rss=8192):
    raw=source.encode("utf-8")
    if not raw or len(raw)>512*1024:
        raise ValueError("proof closure empty or exceeds 512 KiB")
    if not 1<=wall<=1200 or not 256<=rss<=16384:
        raise ValueError("remote resource bounds invalid")
    job={"version":1,"mode":"scratch","base":base,"toolchain":toolchain,
         "attempt":attempt,"wall_seconds":wall,"rss_mib":rss,
         "source_sha256":k.digest(raw),"source_b64":base64.b64encode(raw).decode("ascii")}
    job["job"]=k.digest(k.canon(job).encode())
    return job

def make(c,oid,path,method,wall,rss):
    from . import obligations as o
    obj=k.get(c,oid)
    if obj["kind"]!="obligation":raise ValueError("not an obligation")
    if method:
        base=obj["base"];toolchain=o.public_toolchain(base)
        h=k.digest(("method:"+oid).encode());attempt=h[:24]+"-"+h[24:40]
        origin={"gap":None,"attempt":"method-research"}
    else:
        rec,work,base=o.binding()
        toolchain=(work/"lean/lean-toolchain").read_text().strip()
        attempt=support.attempt(rec)
        origin={"gap":rec["gap_id"],"attempt":attempt}
    if obj["base"]!=base:raise ValueError("obligation requires another exact base")
    body=k.store_artifact(path)
    text=k.artifact(body).read_text();o.clean_body(text)
    src=o.build(c,oid,text)
    k.store_bytes(src.encode())
    origin["submit_agent"]=os.environ.get("ANTONINA_AGENT_ID")
    job=identity(base,toolchain,attempt,src,wall,rss)
    ident={x:job[x] for x in ("job","base","toolchain","attempt","source_sha256")}
    ident["origin"]=origin
    return body,job,ident

def snapshot(c,check):
    table(c)
    row=c.execute("SELECT * FROM pending_check WHERE id=? OR request=?",(check,check)).fetchone()
    if not row:raise ValueError("unknown check ID "+check)
    return dict(row)

def recover_request(job):
    # The transport durably writes its request before enqueue, so a client
    # interrupted between enqueue and receipt can resume rather than repeat.
    root=Path.home()/".local/state/marceline-relay/requests"
    for p in root.glob("*.json"):
        try:
            if p.stat().st_size>4*1024*1024:continue
            d=json.loads(p.read_text())
            if d.get("payload",{}).get("job")==job and ID.fullmatch(d.get("id","")):
                return d["id"]
        except (OSError,ValueError,AttributeError):continue
    return None

def submit(c,oid,path,method=False,wall=600,rss=8192):
    table(c)
    body,job,ident=make(c,oid,path,method,wall,rss)
    cid=job["job"]
    # Return an existing identical in-flight/completed check, not a duplicate.
    with c:
        cursor=c.execute("INSERT OR IGNORE INTO pending_check VALUES(?,?,?,?,?,?,NULL,?,'submitting',NULL)",
                        (cid,oid,job["base"],body,job["source_sha256"],k.canon(ident),time.time()))
        new=cursor.rowcount==1
    if not new:
        old=snapshot(c,cid)
        if old["state"]=="submitting" and not old["request"]:
            request=recover_request(cid)
            if request:
                with c:c.execute("UPDATE pending_check SET request=?,state='queued' WHERE id=?",(request,cid))
                old=snapshot(c,cid)
        return {"check":cid,"node":oid,"state":old["state"],"request":old["request"],"reused":True,"collect":"pnp-research obligations collect "+cid}
    try:
        with tempfile.NamedTemporaryFile(mode="w",suffix=".json") as f:
            f.write(k.canon(job));f.flush()
            proc=subprocess.run([RELAY,"submit","lean-check",f.name],capture_output=True,text=True,timeout=30)
        request=proc.stdout.strip()
        if not ID.fullmatch(request):
            m=re.search(r"request ("+ID.pattern+r")",proc.stderr)
            request=m[1] if m else recover_request(cid)
        if not request:
            with c:c.execute("UPDATE pending_check SET state='transport_failed',result=? WHERE id=?",
                             (k.canon({"error":proc.stderr[-1000:]}),cid))
            raise ValueError("relay did not create a request; use a new resource budget or local check")
    except (OSError,subprocess.SubprocessError) as exc:
        request=recover_request(cid)
        if not request:
            with c:c.execute("UPDATE pending_check SET state='transport_failed',result=? WHERE id=?",
                             (k.canon({"error":str(exc)}),cid))
            raise ValueError("relay submission failed") from exc
    with c:c.execute("UPDATE pending_check SET request=?,state='queued' WHERE id=?",(request,cid))
    return {"check":cid,"node":oid,"state":"queued","request":request,
            "collect":"pnp-research obligations collect "+cid}

def proof_result(c,row,result,stderr=""):
    from . import obligations as o
    ident=json.loads(row["identity"])
    expected={x:ident[x] for x in ("job","base","toolchain","attempt","source_sha256")}
    valid=all(result.get(x)==v for x,v in expected.items())
    ok=(valid and result.get("status")=="elaborated" and result.get("exit_code")==0
        and o.verify_output(result.get("diagnostic",""),row["node"]))
    out={"status":"kernel_checked" if ok else "not_verified","compiler":result if valid else {},
         "stderr":stderr[-1000:],**ident["origin"],"collect_agent":os.environ.get("ANTONINA_AGENT_ID")}
    # A later failed retry must not erase a valid proof of identical body/base.
    with c:
        prev=c.execute("SELECT result FROM proof WHERE node=? AND base=? AND artifact=?",
                       (row["node"],row["base"],row["body"])).fetchone()
        if ok or not prev or json.loads(prev[0]).get("status")!="kernel_checked":
            c.execute("INSERT OR REPLACE INTO proof VALUES(?,?,?,?,?,?)",
                      (row["node"],row["base"],row["body"],row["source"],k.canon(out),time.time()))
        c.execute("UPDATE pending_check SET state='done',result=? WHERE id=?",(k.canon(out),row["id"]))
    return out

def collect(c,check,seconds=1100):
    row=snapshot(c,check)
    if row["state"]=="done":return json.loads(row["result"])
    if row["state"]=="transport_failed":
        return {"status":"transport_failed","check":row["id"],"detail":json.loads(row["result"] or "{}")}
    request=row["request"] or recover_request(row["id"])
    if not request:return {"status":"submitting","check":row["id"]}
    if not 1<=seconds<=1800:raise ValueError("wait must be 1–1800 seconds")
    proc=subprocess.run([RELAY,"wait",request,str(seconds)],capture_output=True,text=True,timeout=seconds+30)
    try:
        receipt=json.loads(proc.stdout);result=receipt["result"]
        if not isinstance(result,dict):raise ValueError("invalid compiler result")
    except (ValueError,KeyError,TypeError):
        # A short poll is not a failed proof. Leave the check recoverable.
        if time.time()-row["at"]>24*3600:
            with c:c.execute("UPDATE pending_check SET state='transport_failed',result=? WHERE id=?",
                             (k.canon({"error":"remote receipt expired"}),row["id"]))
            return {"status":"transport_failed","check":row["id"]}
        return {"status":"pending","check":row["id"],"request":request,"detail":proc.stderr[-500:]}
    return proof_result(c,row,result,proc.stderr)

def pending(c):
    table(c)
    return [dict(r) for r in c.execute("SELECT id,node,base,request,at,state FROM pending_check ORDER BY at DESC LIMIT 100")]


def reconcile(c):
    """One status fetch, then collect at most four completed checks.

    The original agent can die or lose its lease; exact mathematical results
    still become durable. This never starts an agent or acquires a lease.
    """
    table(c)
    rows=[dict(x) for x in c.execute("SELECT * FROM pending_check WHERE state IN ('submitting','queued') ORDER BY at")]
    if not rows:return {"pending":0,"collected":[]}
    try:
        status=json.loads(subprocess.check_output([RELAY,"status"],text=True,timeout=10))
        finished={x["id"] for x in status.get("entries",[]) if x.get("state") in ("done","error")}
    except (OSError,ValueError,subprocess.SubprocessError):return {"pending":len(rows),"collected":[],"status":"relay unavailable"}
    out=[]
    for row in rows:
        if len(out)>=4:break
        request=row["request"] or recover_request(row["id"])
        local=Path.home()/".local/state/marceline-relay/receipts"/((request or "")+".json")
        if request in finished or local.is_file():
            r=collect(c,row["id"],3)
            out.append({"id":row["id"],"node":row["node"],"status":r["status"]})
        elif time.time()-row["at"]>24*3600:
            with c:c.execute("UPDATE pending_check SET state='transport_failed',result=? WHERE id=?",
                             (k.canon({"error":"remote receipt expired"}),row["id"]))
    return {"pending":len(rows),"collected":out}

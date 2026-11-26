"""Durable, asynchronous exact-graph Lean checks; collect without rebuilding."""
from contextlib import closing
import json
import os
import time

from . import knowledge as k
from .. import support

DISABLED = "asynchronous proof transport disabled; use obligations solve NODE BODY --local from its exact bound workspace"

def table(c):
    c.execute("""CREATE TABLE IF NOT EXISTS pending_check(
        id TEXT PRIMARY KEY, node TEXT REFERENCES object(id), base TEXT,
        body TEXT, source TEXT, identity TEXT, request TEXT, at REAL,
        state TEXT, result TEXT
    )""")
    c.commit()

def identity(base,toolchain,attempt,source,wall=600,rss=8192):
    raise ValueError(DISABLED)

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
    return None

def submit(c,oid,path,method=False,wall=600,rss=8192,retry=False):
    raise ValueError(DISABLED)

def proof_result(c,row,result,stderr=""):
    from . import obligations as o
    ident=json.loads(row["identity"])
    expected={x:ident[x] for x in ("job","base","toolchain","attempt","source_sha256")}
    valid=all(result.get(x)==v for x,v in expected.items())
    try:source_ok=o.source_verified(k.artifact(row["source"]).read_text(),row["node"])
    except (OSError,ValueError):source_ok=False
    ok=(valid and source_ok and result.get("status")=="elaborated" and result.get("exit_code")==0
        and o.verify_output(result.get("diagnostic",""),row["node"]))
    out={"status":"kernel_checked" if ok else "not_verified","compiler":result if valid else {},
         "stderr":stderr[-1000:],**ident["origin"],"collect_agent":os.environ.get("ANTONINA_AGENT_ID")}
    # A later failed retry must not erase a valid proof of identical body/base.
    with c:
        prev=c.execute("SELECT node,base,artifact,source_digest,result FROM proof WHERE node=? AND base=? AND artifact=?",
                       (row["node"],row["base"],row["body"])).fetchone()
        if ok or not prev or not o.verified_record(prev):
            c.execute("INSERT OR REPLACE INTO proof VALUES(?,?,?,?,?,?)",
                      (row["node"],row["base"],row["body"],row["source"],k.canon(out),time.time()))
        c.execute("UPDATE pending_check SET state='done',result=? WHERE id=? AND at=?",(k.canon(out),row["id"],row["at"]))
    return out

def collect(c,check,seconds=1100):
    row=snapshot(c,check)
    if row["state"]=="done":
        from . import obligations as o
        out=json.loads(row["result"])
        if out.get("status")=="kernel_checked" and not o.verified_record(
                {"node":row["node"],"base":row["base"],"artifact":row["body"],
                 "source_digest":row["source"],"result":row["result"]}):
            return {**out,"status":"not_verified","reason":"historical receipt needs exact-source audit or recheck"}
        return out
    if row["state"]=="transport_failed":
        return {"status":"transport_failed","check":row["id"],"detail":json.loads(row["result"] or "{}")}
    return {"status":"transport_disabled","check":row["id"],"detail":DISABLED}

def pending(c):
    table(c)
    return [dict(r) for r in c.execute("SELECT id,node,base,request,at,state FROM pending_check ORDER BY at DESC LIMIT 100")]


def reconcile(c):
    """Preserve pending historical work without querying a retired transport."""
    table(c)
    rows=[dict(x) for x in c.execute("SELECT * FROM pending_check WHERE state IN ('submitting','queued') ORDER BY at")]
    return {"pending":len(rows),"collected":[],"status":"transport_disabled",
            "detail":DISABLED}

"""Shared-table two-lit proof stock. No desk claims or direct PR operations.

One bounded generator shares semantic formula tables between masks. A
separate pair of workers verifies exact standalone Lean files. SQLite keeps
staged bytes and negative attempts across restarts, keyed by exact statement
and solver version. Only an exact compiler receipt enters ready stock.
"""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from pathlib import Path
import fcntl
import hashlib
import json
import os
import resource
import sqlite3
import tempfile
import time

from . import gen
from ... import checkremote, live, ready
from .... import config, state, support, validate, ledger, fastlane

STOCK_TARGET = 32
VERIFY_WORKERS = 2
MAX_STAGE = 256
SCHEMA = """
CREATE TABLE IF NOT EXISTS attempt (
  gap TEXT NOT NULL, statement TEXT NOT NULL, version TEXT NOT NULL,
  status TEXT NOT NULL, source TEXT, gates INTEGER, observed REAL NOT NULL,
  retry REAL NOT NULL DEFAULT 0, failures INTEGER NOT NULL DEFAULT 0,
  detail TEXT, PRIMARY KEY(gap,statement,version)
);
CREATE INDEX IF NOT EXISTS attempt_status ON attempt(status,observed);
"""


def root():
    return Path(config.STATE_ROOT)/"lbcert"


def version():
    return hashlib.sha256(Path(__file__).read_bytes()+Path(gen.__file__).read_bytes()).hexdigest()[:20]


def heartbeat_path():
    return root()/"promise-batch.heartbeat"


def owns(statement):
    p=gen.parse(statement or "")
    return bool(p and p[0]=="two" and 5<=p[1]<=6 and p[3]<=12)


def alive(now=None):
    try:
        obj=json.loads(heartbeat_path().read_text())
        return obj["version"]==version() and 0<=(time.time() if now is None else now)-obj["at"]<120
    except (OSError,ValueError,KeyError,TypeError):
        return False


def fallback_keys():
    """A failed bounded formula search still gets the ordinary plugin/SAT path."""
    try:
        with closing(sqlite3.connect(f"file:{root()}/promise-batch.sqlite?mode=ro",uri=True,timeout=2)) as db:
            return {(gid,digest) for gid,digest in db.execute(
                "SELECT gap,statement FROM attempt WHERE version=? AND status IN ('refused','invalid')",
                (version(),))}
    except sqlite3.Error:
        return set()


def claimed(q,fallback):
    return owns(q.get("statement")) and (q.get("id"),hashlib.sha256(q["statement"].encode()).hexdigest()) not in fallback


def key(q,v):
    return (q["id"],hashlib.sha256(q["statement"].encode()).hexdigest(),v)


def database(path):
    db=sqlite3.connect(path,timeout=10)
    db.row_factory=sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript(SCHEMA)
    return db


def get(db,k):
    return db.execute("SELECT * FROM attempt WHERE gap=? AND statement=? AND version=?",k).fetchone()


def put(db,k,status,source=None,gates=None,detail=None,retry=0,failures=0):
    with db:
        db.execute("""INSERT INTO attempt(gap,statement,version,status,source,gates,observed,retry,failures,detail)
          VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(gap,statement,version) DO UPDATE SET
          status=excluded.status,source=excluded.source,gates=excluded.gates,observed=excluded.observed,
          retry=excluded.retry,failures=excluded.failures,detail=excluded.detail""",
          (*k,status,source,gates,time.time(),retry,failures,detail))


def eligible(q,row,rec):
    if rec and (rec.get("pr_number") or rec.get("candidate_digest") or rec.get("queued_lease")):
        return False
    if support.active(rec):
        return rec.get("statement")==q.get("statement")
    return not q.get("pr_open") and (row.get("held") or 0)<(row.get("parallel") or 1)


def priority(q,p,row,rec):
    return (not support.active(rec),row.get("level") not in ("solid","warmup"),
            -p[3],-(row.get("points") or 0),row.get("held") or 0,-int(q["id"].split("-")[-1]))


def candidate(q,p):
    start=time.monotonic()
    n,rows,target=gen.domain(p)
    allow=p[-1]=="FanInTwo";full=(1<<len(rows))-1
    sol=gen.sketch_witness(p,q.get("sketch"),.03)
    if not sol:
        depth=7 if n==5 else 6
        table,cost,levels=gen.formula_library(n,tuple(rows),allow,depth)
        for budget in range(p[3],p[3]+3):
            e=gen.formula_pair(target,budget,table,cost,levels,full,allow)
            if e is None and allow and budget:
                e=gen.formula_pair(full^target,budget-1,table,cost,levels,full,False)
                if e is not None:e=("not",e)
            if e is not None:
                sol=gen.compact(p,*gen.compile_expr(n,e))
                if sol and gen.valid(p,sol):break
                sol=None
    if not sol:return None,None,time.monotonic()-start
    if not gen.valid(p,sol):raise ValueError("independent semantic audit failed")
    source=gen.emit(q["id"],q["statement"],p,sol)
    validate.validate(q,source.encode())
    return source,len(sol[0]),time.monotonic()-start


def verify(q,source):
    gid=q["id"];data=source.encode()
    validate.validate(q,data)
    with tempfile.TemporaryDirectory(prefix="promise-check-",dir=root()) as d:
        p=Path(d)/"candidate.lean";p.write_bytes(data)
        rc,r=checkremote.check(str(p),q["module"],timeout=120)
    if rc!=0:return ("transient" if rc==2 else "invalid"),str(r.get("status"))+": "+str(r.get("log") or "")[-300:]
    receipt=dict(r,compiled=True)
    if not ready.exact_receipt(receipt,data):return "transient","receipt mismatch"
    if ready.verified(gid):return "checked","existing exact receipt"
    rec=state.load(gid)
    if rec and (rec.get("pr_number") or rec.get("candidate_digest") or rec.get("queued_lease")):
        return "obsolete","publication already owns unit"
    dst=ready.directory()/(gid+".lean")
    state.atomic_write(str(dst),source)
    if not ready.record(gid,receipt,data):
        return "transient","receipt mismatch"
    state.atomic_write(str(dst.with_suffix(".status")),"ok plugin promise batch standalone compiled\n")
    if support.active(state.load(gid)):
        try:fastlane.submit_ready(gid)
        except Exception as e:print("held submission deferred",gid,type(e).__name__,flush=True)
    return "checked",r.get("id") or "exact receipt"


def current(v):
    snap=live.snapshot(max_age=45)
    if not snap or time.time()-snap["at"]>=120:return []
    gaps=json.loads(live.gaps_bytes(timeout=30))["gaps"]
    out=[]
    for q in gaps:
        gid=q.get("id");row=snap["gaps"].get(gid)
        if not row or not isinstance(gid,str) or not config.GAP_ID_RE.fullmatch(gid):continue
        p=gen.parse(q.get("statement") or "")
        if not p or not owns(q["statement"]):continue
        rec=state.load(gid)
        if not eligible(q,row,rec) or ready.verified(gid):continue
        out.append((priority(q,p,row,rec),q,p,row,key(q,v)))
    return sorted(out,key=lambda x:x[0])


def batch_status():
    info={"version":version(),"alive":alive(),"attempts":{}}
    try:info["heartbeat"]=json.loads(heartbeat_path().read_text())
    except (OSError,ValueError):pass
    try:
        with closing(sqlite3.connect(f"file:{root()}/promise-batch.sqlite?mode=ro",uri=True,timeout=2)) as db:
            info["attempts"]=dict(db.execute("SELECT status,COUNT(*) FROM attempt WHERE version=? GROUP BY status",(info["version"],)))
    except sqlite3.Error:pass
    return info


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status",action="store_true",help="read-only batch status")
    if parser.parse_args().status:
        print(json.dumps(batch_status(),sort_keys=True));return 0
    root().mkdir(parents=True,exist_ok=True)
    lock=(root()/"promise-batch.lock").open("a+")
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:return 0
    # Only one batch process, with one CPU-bound generator, and bounded cache.
    resource.setrlimit(resource.RLIMIT_AS,(1024*1024**2,1024*1024**2))
    v=version();db=database(root()/"promise-batch.sqlite")
    with db:db.execute("DELETE FROM attempt WHERE observed<?",(time.time()-7*86400,))
    deadline=time.monotonic()+300;next_refresh=0;items=[];running={};stock=0;attempts={}
    with ThreadPoolExecutor(max_workers=1) as generation, ThreadPoolExecutor(max_workers=VERIFY_WORKERS) as verification:
        while True:
            now=time.time()
            scheduling=time.monotonic()<deadline and version()==v and not (root()/"STOP").exists()
            if not scheduling and not running:break
            if scheduling and time.monotonic()>=next_refresh:
                try:
                    items=current(v)
                    attempts={tuple(r[k] for k in ("gap","statement","version")):r
                              for r in db.execute("SELECT * FROM attempt WHERE version=?",(v,))}
                    stock=len(ready.offers({}, {},now))
                    state.atomic_write(str(heartbeat_path()),json.dumps({"at":now,"version":v,"stock":stock,"eligible":len(items)}))
                    next_refresh=time.monotonic()+45
                except Exception as e:
                    items=[];next_refresh=time.monotonic()+15
                    print("frontier unavailable",type(e).__name__,str(e)[:140],flush=True)
            if scheduling:
                keys={x[2] for x in running.values()}
                gen_busy=any(x[0]=="generate" for x in running.values())
                ver_busy=sum(x[0]=="verify" for x in running.values())
                staged=sum(1 for _,q,p,row,k in items if (r:=attempts.get(k)) and r["status"]=="staged")
                for pr,q,p,row,k in items:
                    if k in keys:continue
                    r=attempts.get(k)
                    if r and r["status"] in ("staged","checked") and r["source"] and r["retry"]<=now and ver_busy<VERIFY_WORKERS and (stock+ver_busy<STOCK_TARGET or not pr[0]):
                        if ready.verified(q["id"]):continue
                        running[verification.submit(verify,q,r["source"])]=("verify",q,k,r)
                        keys.add(k);ver_busy+=1
                    elif not r and not gen_busy and (staged<MAX_STAGE or not pr[0]):
                        if ready.verified(q["id"]):continue
                        running[generation.submit(candidate,q,p)]=("generate",q,k,None)
                        keys.add(k);gen_busy=True
                    if gen_busy and ver_busy>=VERIFY_WORKERS:break
            if not running:
                time.sleep(3);continue
            done,_=wait(running,timeout=1,return_when=FIRST_COMPLETED)
            for f in done:
                mode,q,k,r=running.pop(f)
                try:
                    result=f.result()
                    if mode=="generate":
                        source,gates,secs=result
                        put(db,k,"staged" if source else "refused",source,gates)
                        ledger.mark("generated",q["id"],engine="promise-batch",status="ok" if source else "refused",secs=round(secs,3))
                        if source:print("staged",q["id"],gates,flush=True)
                    else:
                        status,detail=result
                        failures=r["failures"]+1
                        put(db,k,"staged" if status=="transient" else status,
                            r["source"] if status in ("transient","checked") else None,r["gates"],detail,
                            now+min(900,60*2**min(failures,4)) if status=="transient" else 0,failures)
                        if status=="checked":stock+=1
                        print(status,q["id"],detail,flush=True)
                    attempts[k]=get(db,k)
                except Exception as e:
                    # Infrastructure exceptions are not negative mathematical results.
                    if mode=="verify":
                        put(db,k,"staged",r["source"],r["gates"],type(e).__name__,now+120,r["failures"]+1)
                        attempts[k]=get(db,k)
                    else:
                        # A short in-memory defer avoids a failing generator busy-loop.
                        items=[x for x in items if x[-1]!=k]
                    print(mode,"deferred",q["id"],type(e).__name__,str(e)[:140],flush=True)
    db.close()
    return 0


if __name__=="__main__":
    raise SystemExit(main())

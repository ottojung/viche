"""Executive-gated, offline broker admission of private exact proof receipts.

No network, desk acquisition, publication, checker invocation or flag mutation.
The separate allocator observer may obtain competition evidence for this path.
"""
import json
import os
import stat
import subprocess
import time
from pathlib import Path

from .. import cli, config, desk, frontier, ledger, state
from ..research.obligations import verify_report
from . import prelease, ready

DECISION="records/investigations/executive-conditional-authorization-broker-receipt-promotion-20261126T2249Z.md"
MAX_OBSERVATION_AGE=30
MAX_RECEIPTS=64

def enabled():
    cfg=prelease.enablement()
    if not cfg or not (prelease.TOWN/DECISION).is_file():
        return None
    try:
        flag=prelease.private_json("promote.json")
        if (set(flag)!={"enabled","base","checker_authorization","authorization"}
                or flag["enabled"] is not True or flag["base"]!=cfg["base"]
                or flag["checker_authorization"]!=cfg["authorization"]
                or not isinstance(flag["authorization"],str) or not flag["authorization"].strip()):
            return None
        return cfg,flag
    except (OSError,ValueError,TypeError,KeyError):
        return None

def receipt_dir(cfg):
    root=prelease.private_dir()
    p=root/"receipts"/cfg["base"]
    for d in (p.parent,p):
        st=d.lstat()
        if (not stat.S_ISDIR(st.st_mode) or st.st_uid!=os.getuid()
                or st.st_mode & 0o077 or d.resolve()!=d):
            raise ValueError("unsafe private receipt directory")
    return p

def private_bytes(path,limit):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        st=os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_uid!=os.getuid() or st.st_mode & 0o077:
            raise ValueError("unsafe private receipt file")
        with os.fdopen(fd,"rb",closefd=False) as f:
            data=f.read(limit+1)
        if len(data)>limit:raise ValueError("private receipt size limit")
        return data
    finally:os.close(fd)

def pending(auth=None):
    auth=enabled() if auth is None else auth
    if not auth:return []
    try:
        p=receipt_dir(auth[0])
        rows=[]
        for f in p.glob("*.json"):
            gid,sep,digest=f.stem.rpartition("-")
            if not sep or not config.GAP_ID_RE.fullmatch(gid) or not prelease.DIGEST.fullmatch(digest):
                continue
            if os.path.lexists(ready.marker(gid)):continue
            try:
                st=f.lstat()
                if not stat.S_ISREG(st.st_mode) or st.st_uid!=os.getuid() or st.st_mode&0o077:
                    continue
                rows.append((st.st_mtime,gid,digest))
            except OSError:continue
        return [(g,d) for _,g,d in sorted(rows,reverse=True)[:MAX_RECEIPTS]]
    except (OSError,ValueError,TypeError):
        return []

def observation_path():
    return Path(config.STATE_ROOT)/"cache/promotion-competition.json"

def observations(now):
    try:
        data=json.loads(observation_path().read_text())
        if type(data["at"]) not in (int,float) or not 0<=now-data["at"]<=MAX_OBSERVATION_AGE:return {}
        if not isinstance(data["counts"],dict):return {}
        return {g:v for g,v in data["counts"].items() if type(v) is int and v>=0}
    except (OSError,ValueError,TypeError,KeyError):return {}

def availability(gid,q,snap,now):
    if (not snap.get("complete") or type(snap.get("observed")) not in (int,float)
            or not 0<=now-snap["observed"]<=45):
        return "frontier stale or incomplete"
    row=snap.get("gaps",{}).get(gid)
    if (not row or type(row.get("held")) is not int or row["held"]!=0
            or type(row.get("parallel")) is not int or row["parallel"]<=0):
        return "unit not confirmed unheld/open"
    if (q.get("offerable_now") is not True or q.get("held_now") is not False
            or type(q.get("pr_open")) is not int or q["pr_open"]!=0):
        return "catalog not confirmed offerable/uncontested"
    if observations(now).get(gid)!=0:return "direct competition unknown or contested"
    rec=state.load(gid)
    if rec and (rec.get("pr_number") or rec["state"] not in ("RELEASED","STALE")
                or rec.get("intent") or rec.get("queued_lease")):
        return "already assigned or published"
    if os.path.lexists(ready.marker(gid)):return "existing receipt"
    if desk.retry_until(gid)>now:return "desk cooldown"
    if len(cli.held_records())>=desk.lease_limit():return "capacity"
    return None

def admit(gid,digest,auth):
    """Caller owns the existing acquisition lock; private checker lock is nonblocking."""
    checks=[]
    r={}
    def result(status,reason):
        ledger.mark("private_promotion",gid,status=status,reason=reason,
                    digest=digest,guarded_digest=r.get("guarded_sha256"),
                    base=auth[0]["base"],authorization=auth[1]["authorization"],checks=checks)
        return {"gap":gid,"status":status,"reason":reason}
    fd=None
    try:
        if enabled()!=auth:return result("deferred","authorization changed")
        if not config.GAP_ID_RE.fullmatch(gid) or not prelease.DIGEST.fullmatch(digest):
            return result("rejected","invalid identity")
        fd=prelease.lock()
        cfg,flag=auth
        path=receipt_dir(cfg)/(gid+"-"+digest)
        raw=private_bytes(path.with_suffix(".lean"),config.MAX_FILE_BYTES)
        r=json.loads(private_bytes(path.with_suffix(".json"),131072))
        if not isinstance(r,dict):raise ValueError("receipt not an object")
        if (not ready.exact_receipt(r,raw) or r.get("sha256")!=digest
                or r.get("gap")!=gid):return result("rejected","exact receipt identity")
        checks.append("bytes")
        q=prelease.metadata(gid)
        guarded=prelease.audited(q,raw)
        if (r.get("guarded_sha256")!=prelease.sha(guarded)
                or r.get("statement_sha256")!=prelease.sha(q["statement"].encode())
                or r.get("module")!=q["module"]):
            return result("rejected","statement or guarded digest changed")
        checks.append("canonical")
        log=r.get("compiler_log")
        if (not isinstance(log,str) or r.get("compiler_log_sha256")!=prelease.sha(log.encode())
                or not verify_report(log,q["module"])
                or r.get("axiom_report")!=log.strip().splitlines()[-1].strip()):
            return result("rejected","missing exact trusted final report")
        checks.append("axioms")
        if (r.get("checked_base")!=cfg["base"] or r.get("toolchain")!=config.LEAN_TOOLCHAIN
                or type(r.get("at")) not in (int,float) or not 0<r["at"]<=time.time()):
            return result("rejected","pin, toolchain or check time mismatch")
        prelease.public_base(cfg["base"])
        # The enablement check validates the workspace pin file. Verify the actual HEAD too.
        w=prelease.private_dir()/"worktree"
        if w.resolve()!=w or prelease.git("rev-parse","HEAD",cwd=w)!=cfg["base"]:
            return result("rejected","private checkout pin changed")
        checks.append("base")
        if r.get("authorization")!=cfg["authorization"] or enabled()!=auth:
            return result("deferred","authorization changed")
        checks.append("authorization")
        now=time.time()
        q2=prelease.metadata(gid)
        if q2!=q:return result("deferred","catalog changed during admission")
        reason=availability(gid,q2,frontier.load(now),now)
        if reason:return result("deferred",reason)
        checks.append("availability")
        if enabled()!=auth:return result("deferred","authorization changed before record")
        if not ready.record(gid,r,raw,private=True):return result("deferred","record conflict")
        return result("promoted","exact private proof admitted")
    except BlockingIOError:return result("deferred","checker busy")
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as exc:
        return result("deferred",str(exc)[:180])
    finally:
        if fd is not None:os.close(fd)

def promote_once():
    auth=enabled()
    if not auth:return []
    now=time.time()
    if desk.retry_until()>now:return []
    counts=observations(now)
    # A malformed/deferred item cannot monopolize every cheap allocator pass.
    attempts={(e.get("gid"),e.get("digest")):e for e in ledger.read(hours=1)
              if e.get("stage")=="private_promotion" and e.get("authorization")==auth[1]["authorization"]}
    candidates=[(g,d) for g,d in pending(auth) if counts.get(g)==0
                and now-attempts.get((g,d),{}).get("t",0)>=60]
    if not candidates:return []
    with cli.acquisition_lock():
        # At most one per cheap allocator pass; no direct claims from here.
        g,d=candidates[0]
        return [admit(g,d,auth)]

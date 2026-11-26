"""Exact evidence for documented --proof-of targeted acquisition.

A generated proof is not a checked proof. Only a compiler result identifying
the same bytes and public base allows the broker to say have=proof.
"""
import hashlib
import json
from pathlib import Path
import re
import time

from .. import config, state


def directory():
    return Path(config.STATE_ROOT, "lbcert", "cands")


def marker(gid):
    if not config.GAP_ID_RE.fullmatch(gid):
        raise ValueError("invalid gap")
    return directory()/(gid+".checked.json")


def record(gid, result, data):
    digest=hashlib.sha256(data).hexdigest()
    if not (result.get("status")=="ok" and result.get("compiled") is True
            and result.get("sha256")==digest
            and re.fullmatch(r"[0-9a-f]{40}",result.get("checked_base") or "")):
        return False
    path=directory()/(gid+".lean")
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
        return False
    state.atomic_write(str(marker(gid)),json.dumps({
        "gap":gid,"digest":digest,"base":result["checked_base"],
        "request":result.get("id"),"at":time.time()},sort_keys=True))
    from .. import ledger
    ledger.mark("checked",gid,base=result["checked_base"])
    return True


def verified(gid):
    try:
        m=json.loads(marker(gid).read_text())
        data=(directory()/(gid+".lean")).read_bytes()
        if (m["gap"]==gid and re.fullmatch(r"[0-9a-f]{40}",m["base"])
                and hashlib.sha256(data).hexdigest()==m["digest"]):
            return m
    except (OSError,ValueError,KeyError,TypeError):
        pass
    return None


def offers(snapshot, mem, now):
    attempts=mem.setdefault("proof_of_attempts",{})
    mem["proof_of_attempts"]=attempts={k:v for k,v in attempts.items()
                                       if now-v<600}
    out=[]
    open_now=None
    if not snapshot.get("complete"):
        # The allocator's desk/status snapshot often times out (8 s curl); without it, use the
        # cached live frontier: gaps.json also lists closed/unofferable steps (2026-11-26).
        from . import live
        open_now=live.open_ids()
    for path in directory().glob("*.checked.json"):
        gid=path.name[:-13]
        if now-attempts.get(gid,0)<120:
            continue
        if open_now is not None and gid not in open_now:
            continue
        rec=state.load(gid)
        if rec and (rec.get("pr_number") or rec["state"] not in ("RELEASED","STALE")):
            continue
        if snapshot.get("complete") and gid not in snapshot.get("gaps",{}):
            continue
        m=verified(gid)
        if m:
            out.append((m["at"],gid))
    return [gid for _,gid in sorted(out,reverse=True)]

"""Exact evidence for documented --proof-of targeted acquisition.

A generated proof is not a checked proof. Only a compiler result identifying
the same bytes and public base allows the broker to say have=proof.
"""
import hashlib
import json
from pathlib import Path
import re
import time

from .. import config, state, desk


def directory():
    return Path(config.STATE_ROOT, "lbcert", "cands")


def marker(gid):
    if not config.GAP_ID_RE.fullmatch(gid):
        raise ValueError("invalid gap")
    return directory()/(gid+".checked.json")


def exact_receipt(result, data):
    return (result.get("status")=="ok" and result.get("compiled") is True
            and result.get("sha256")==hashlib.sha256(data).hexdigest()
            and isinstance(result.get("checked_base"),str)
            and re.fullmatch(r"[0-9a-f]{40}",result["checked_base"]) is not None)


def record(gid, result, data):
    if not exact_receipt(result,data):return False
    digest=hashlib.sha256(data).hexdigest()
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
    paths=list(directory().glob("*.checked.json"))
    if not paths:return []
    out=[]
    open_now=None
    rows=snapshot.get("gaps",{})
    if not snapshot.get("complete"):
        # The allocator's desk/status snapshot often times out (8 s curl); without it, use the
        # cached live frontier: gaps.json also lists closed/unofferable steps (2026-11-26).
        from . import live
        current=live.snapshot()
        if current is None:return []
        rows=current["gaps"]
        open_now=set(rows)
    competing=competition(now)
    for path in paths:
        gid=path.name[:-13]
        if now-attempts.get(gid,0)<120 or desk.retry_until(gid)>now:
            continue
        if open_now is not None and gid not in open_now:
            continue
        rec=state.load(gid)
        if rec and (rec.get("pr_number") or rec["state"] not in ("RELEASED","STALE")):
            continue
        if snapshot.get("complete") and gid not in snapshot.get("gaps",{}):
            continue
        row=rows.get(gid,{})
        if (row.get("held") or 0) >= (row.get("parallel") or 1):
            continue
        m=verified(gid)
        if m:
            out.append((competing.get(gid,1),row.get("held") or 0, -(row.get("points") or 0), -m["at"], gid))
    return [gid for _,_,_,_,gid in sorted(out)]



def competition(now):
    """Recent public PR counts, no extra network request; unknown is unknown."""
    try:
        cache=Path(config.STATE_ROOT)/"lbcert"/"gaps-cache.json"
        meta=json.loads(Path(str(cache)+".meta").read_text())
        if 0<=now-meta["at"]<120:
            return {q["id"]:q["pr_open"] for q in json.loads(cache.read_text())["gaps"]
                    if type(q.get("pr_open")) is int and q["pr_open"]>=0}
    except (OSError,ValueError,KeyError,TypeError):
        pass
    return {}

def inventory(snapshot,now=None):
    """A read-only opportunity estimate; no desk request or credit assertion."""
    now=time.time() if now is None else now
    if not snapshot.get("complete") or not isinstance(snapshot.get("gaps"),dict):
        return {"available":False,"reason":"complete fresh frontier unavailable"}
    ids=offers(snapshot,{},now)
    rows=snapshot["gaps"]
    competitors=competition(now)
    uncontested=[g for g in ids if competitors.get(g)==0]
    contested=[g for g in ids if competitors.get(g,0)>0]
    values=[rows[g].get("points") for g in ids]
    known=[p for p in values if type(p) is int and p>=0]
    return {"available":True,"eligible_checked":len(ids),
            "advertised_points_known":sum(known),"priced_candidates":len(known),
            "uncontested_checked":len(uncontested),"contested_checked":len(contested),
            "competition_unknown":len(ids)-len(uncontested)-len(contested),
            "top":[{"gap":g,"advertised_points":rows[g].get("points"),
                    "held":rows[g].get("held"),"competing_prs":competitors.get(g)} for g in ids[:5]],
            "note":"Advertised prices, not guaranteed leases or credited points."}

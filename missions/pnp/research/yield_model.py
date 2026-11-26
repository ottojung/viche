"""Small-sample empirical portfolio signals, never an automatic release gate."""
import argparse
from contextlib import closing
import collections
from datetime import datetime
import json
import math
from pathlib import Path
import time

from .. import state, support, frontier
from . import knowledge

def epoch(s):
    return datetime.fromisoformat(s.replace("Z","+00:00")).timestamp()

def observations():
    all_rows={}
    for r,folder in knowledge.histories():
        g=r["gap_id"];rows=[]
        fam=knowledge.family((r.get("gap_title") or "")+" "+(r.get("statement") or ""))
        attempt=None
        try:
            for line in (folder/"events.jsonl").read_text().splitlines():
                e=json.loads(line);d=e.get("detail",{});t=epoch(e["at"])
                if e["kind"]=="acquired":
                    if attempt:
                        attempt["end"]=t;attempt["outcome"]="superseded";rows.append(attempt)
                    attempt={"gap":g,"family":fam,"start":t,"end":None,"outcome":"censored","submitted":None,"pr":None}
                elif attempt and e["kind"]=="published" and attempt["submitted"] is None:
                    attempt["submitted"]=t;attempt["pr"]=d.get("pr")
                elif attempt and (e["kind"] in ("fastlane_release","portfolio_release","operator_release") or
                                  e["kind"]=="state" and d.get("to") in ("RELEASED","STALE","ACCEPTED")):
                    attempt["end"]=t;attempt["outcome"]=d.get("to","RELEASED").lower()
                    attempt["merge_observed"]=bool(d.get("sha"))
                    rows.append(attempt);attempt=None
            if attempt:
                if folder.parent.name=="quarantine":
                    try:
                        cut=datetime.strptime(folder.name.rsplit("-",1)[1],"%Y%m%d%H%M%S").replace(tzinfo=datetime.fromisoformat("2000-01-01T00:00:00+00:00").tzinfo).timestamp()
                        attempt["end"]=max(attempt["start"],cut)
                    except ValueError:pass
                if r.get("external_verdict")=="ACCEPTED" and attempt["submitted"] and attempt["pr"]==r.get("pr_number"):
                    attempt["outcome"]="checker_accepted";attempt["end"]=time.time()
                rows.append(attempt)
            # Checker acceptance can precede a later stale/merged record. Credit
            # only the most recent published attempt, never every historical lease.
            if r.get("external_verdict")=="ACCEPTED":
                published=[x for x in rows if x["gap"]==g and x["submitted"] and x["pr"]==r.get("pr_number")]
                if published:published[-1]["outcome"]="checker_accepted"
            for row in rows:
                key=(row["gap"],row["start"])
                prev=all_rows.get(key)
                score=lambda x:(x["outcome"]=="checker_accepted",x["outcome"]!="censored",x["submitted"] is not None,x["end"] or 0)
                if prev is None or score(row)>score(prev):all_rows[key]=row
        except (OSError,ValueError,KeyError,TypeError):continue
    return list(all_rows.values())

def estimate(rows,fam,now=None):
    # Cause-specific rates per observed research-hour until first submission
    # or terminal failure. Live attempts contribute exposure, not failures.
    # Weak shrinkage to pooled data avoids 0/1 probabilities from tiny strata.
    now=time.time() if now is None else now
    def rates(xs):
        hours=sum(max(0,((x["submitted"] or x["end"] or now)-x["start"])/3600) for x in xs)
        subs=sum(x["submitted"] is not None for x in xs)
        losses=sum(x["submitted"] is None and x["outcome"]!="censored" for x in xs)
        resolved=[x for x in xs if x["submitted"] and x["outcome"]!="censored"]
        ok=sum(x["outcome"]=="checker_accepted" for x in resolved)
        return hours,subs,losses,len(resolved),ok
    H,S,L,R,A=rates(rows); h,s,l,r,a=rates([x for x in rows if x["family"]==fam])
    prior_hours=2.0
    submit=(s+prior_hours*(S+1)/(H+2))/(h+prior_hours)
    loss=(l+prior_hours*(L+1)/(H+2))/(h+prior_hours)
    accept=(a+4*(A+1)/(R+2))/(r+4)
    return {"family":fam,"observed_hours":round(h,3),"submissions":s,"pre_submission_losses":l,
            "resolved_submissions":r,"checker_acceptances":a,"submit_hazard_per_hour":submit,
            "loss_hazard_per_hour":loss,"accept_given_submission":accept,
            "note":"Heuristic shrinkage; incomplete historical ledger, selection bias, constant hazards; not a calibrated prediction."}

def generator_signal(rec):
    """Concrete candidate availability is stronger than a broad family prior."""
    from .. import config
    from ..lbcert import lbparse
    root=Path(config.STATE_ROOT)/"lbcert"
    gid=rec["gap_id"]
    p=root/"cands"/(gid+".status")
    row={"generator_family":lbparse.family(rec["statement"]),"candidate_status":None}
    try:
        marker=p.read_text().split()
        row["candidate_status"]=marker[0] if marker else None
        row["candidate_exists"]=(root/"cands"/(gid+".lean")).is_file()
        row["candidate_age_seconds"]=round(max(0,time.time()-p.stat().st_mtime),1)
        for item in marker:
            if item.startswith("secs="):row["generation_seconds"]=float(item[5:])
    except (OSError,ValueError):pass
    try:
        from ..lbcert import ready
        row["exact_checked_candidate"]=bool(ready.verified(gid))
    except ImportError:
        row["exact_checked_candidate"]=False
    try:
        f=root/"desk.json"
        if time.time()-f.stat().st_mtime<=120:
            row["competitor_open_prs"]=json.loads(f.read_text()).get(gid)
    except (OSError,ValueError,TypeError):pass
    return row


def view():
    history=observations();out=[];front=frontier.load().get("gaps",{});now=time.time()
    for g in state.all_gaps():
        r=state.load(g)
        if not support.active(r):continue
        fam=knowledge.family((r.get("gap_title") or "")+" "+r["statement"])
        e=estimate(history,fam,now);s=e["submit_hazard_per_hour"];l=e["loss_hazard_per_hour"]
        # Competing acceptance is not separately identified by old events.
        # Expose competition, rather than inventing a quantitative adjustment.
        e.update(gap=g,competition=front.get(g),production=generator_signal(r),
                 probability_proxy_within_30min=round((1-math.exp(-(s+l)*0.5))*s/(s+l)*e["accept_given_submission"],4),
                 probability_proxy_within_60min=round((1-math.exp(-(s+l)))*s/(s+l)*e["accept_given_submission"],4),
                 age_minutes=round((time.time()-r["lease_obtained_at"])/60,1),
                 remaining_hours_proxy=round(1/(s+l),3),
                 probability_proxy=round(s/(s+l)*e["accept_given_submission"],4),
                 expected_yield_proxy_per_hour=round(s*e["accept_given_submission"],4))
        try:
            with closing(knowledge.db()) as c:
                from . import obligations
                ns=[o for o in obligations.ready(c,family=fam) if knowledge.belongs(c,o["id"],r["gap_id"]+" / ")]
                e["proof_graph"]={v:sum(o["status"]==v for o in ns) for v in ("checked","ready","blocked","refuted")}
                e["unresolved_obligations"]=sum(e["proof_graph"][v] for v in ("ready","blocked"))
                e["techniques"]=[{"id":x["id"],"statement":x["statement"][:250]} for x in
                    knowledge.search(c,"",fam,("technique","lemma","certificate"),limit=6)]
        except (OSError,ValueError,TypeError,KeyError):pass
        out.append(e)
    return {"history_attempts":len(history),"active_censored":sum(x["outcome"]=="censored" for x in history),
            "rows":sorted(out,key=lambda x:x["expected_yield_proxy_per_hour"],reverse=True),
            "interpretation":"Family-level baseline only. Evaluators must incorporate actual proof obligations, reusable techniques and current competition; no automated release."}

if __name__=="__main__":print(json.dumps(view(),indent=2))

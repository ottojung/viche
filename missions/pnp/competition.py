"""Direct indexed upstream PR observations for targeted fallback acquisition.

The desk's pr_open count is a useful positive signal, not sufficient negative
evidence. A GitHub search can also lag; never treat incomplete results as clear.
No GitHub writes, and no direct probe on the posting-time fresh lease path.
"""
import json
import subprocess
from . import config, github

MAX_BATCH = 5


def _gh(*args):
    p = subprocess.run([config.GH_CLI,*args],capture_output=True,text=True,timeout=8,check=True)
    return json.loads(p.stdout)


def observe(gids, request=None):
    gids = list(dict.fromkeys(g for g in gids if config.GAP_ID_RE.fullmatch(g)))[:MAX_BATCH]
    if not gids:
        return {}
    req = request or _gh
    try:
        repo = req("api","repositories/"+str(config.UPSTREAM_ID),"--jq","{id,full_name}")
        if repo.get("id") != config.UPSTREAM_ID or not github.REPO_NAME.fullmatch(repo.get("full_name","")):
            return {}
        clauses = []
        for i,g in enumerate(gids):
            q = 'repo:'+repo["full_name"]+' is:pr is:open in:title "'+g+'"'
            clauses.append(f'a{i}:search(type:ISSUE,query:{json.dumps(q)},first:100){{issueCount nodes{{... on PullRequest{{number title state}}}}}}')
        doc = req("api","graphql","-f","query=query { "+" ".join(clauses)+" }")
        if doc.get("errors"):
            return {}
        out = {}
        for i,g in enumerate(gids):
            row = doc.get("data",{}).get(f"a{i}")
            if not isinstance(row,dict):
                continue
            n = row.get("nodes")
            if not isinstance(n,list) or type(row.get("issueCount")) is not int or len(n)!=row["issueCount"]:
                continue
            if any(not isinstance(r,dict) or type(r.get("number")) is not int or not isinstance(r.get("title"),str) or r.get("state")!="OPEN" for r in n):
                continue
            out[g] = sum(r["title"]==g for r in n)
        return out
    except (OSError,subprocess.SubprocessError,ValueError,TypeError,AttributeError,KeyError):
        return {}


def fallback_target(ids,mem,now):
    """At most one bounded observation per 30s; exact zero only, no unknown."""
    cache = mem.setdefault("target_competition",{})
    cache = {g:v for g,v in cache.items()
             if isinstance(v,dict) and 0<=now-v.get("at",0)<30}
    mem["target_competition"] = cache
    selected = list(ids)[:MAX_BATCH]
    pending = [g for g in selected if g not in cache]
    if pending and now-mem.get("last_competition_probe",0)>=30:
        mem["last_competition_probe"] = now
        for g,count in observe(pending).items():
            cache[g] = {"at":now,"open":count}
    return next((g for g in selected if cache.get(g,{}).get("open")==0),None)

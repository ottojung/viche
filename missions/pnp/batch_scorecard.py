"""Post-batch outcome measurement. Read-only with respect to the desk and proofs."""
import json
from pathlib import Path
import statistics
import sys
import time

from . import competition, config, github, leaderboard, ledger, state


def last_closed_window(events):
    start = None
    result = None
    for e in sorted(events, key=lambda x:x["t"]):
        if e.get("stage") == "surge_enter":
            start = e["t"]
        elif e.get("stage") == "surge_exit" and start is not None:
            result = (start-300, e["t"])
            start = None
    return result


def summarize(events, window, first):
    start, end = window
    cohort = [e for e in events if start <= e["t"] <= end]
    seen = {e["gid"] for e in cohort if e.get("stage") == "seen"}
    leased = {e["gid"] for e in cohort if e.get("stage") == "leased"}
    prs = {e["gid"]:e["pr"] for e in cohort if e.get("stage") == "pr_opened"
           and type(e.get("pr")) is int}
    accepted = {e["gid"] for e in events if e["t"] >= start and e.get("stage") == "verdict"
                and e.get("verdict") == "ACCEPTED" and e["gid"] in prs}
    first_count = sum(first.get(str(p)) is True for p in prs.values())
    later_count = sum(first.get(str(p)) is False for p in prs.values())
    known = first_count+later_count
    starts = {}
    delays = []
    for e in sorted(cohort,key=lambda x:x["t"]):
        gid=e["gid"]
        if e.get("stage") == "leased":
            starts[gid]=e["t"]
        elif e.get("stage") == "pr_opened" and gid in starts:
            delays.append(e["t"]-starts.pop(gid))
    return {"start":start,"end":end,"seen":len(seen),"leased":len(leased),
            "prs":prs,"accepted":len(accepted),
            "first":first_count,"later":later_count,"first_unknown":len(prs)-known,
            "first_share_known":first_count/known if known else None,
            "median_lease_to_pr_s":statistics.median(delays) if delays else None}


def observe_first(prs, request=None):
    """Indexed GitHub evidence, including closed rivals; unknown stays unknown."""
    req = request or competition._gh
    try:
        repo = req("api","repositories/"+str(config.UPSTREAM_ID),"--jq","{id,full_name}")
        if repo.get("id") != config.UPSTREAM_ID or not github.REPO_NAME.fullmatch(repo.get("full_name","")):
            return {}
        pairs = [(g,p) for g,p in prs.items() if config.GAP_ID_RE.fullmatch(g)
                 and type(p) is int][:5]
        if not pairs:
            return {}
        clauses = []
        for i,(g,_) in enumerate(pairs):
            q = f'repo:{repo["full_name"]} is:pr in:title "{g}"'
            clauses.append(f'a{i}:search(type:ISSUE,query:{json.dumps(q)},first:100)'
                           '{issueCount nodes{... on PullRequest{number title createdAt}}}')
        doc = req("api","graphql","-f","query=query { "+" ".join(clauses)+" }")
        if doc.get("errors"):
            return {}
        out = {}
        for i,(g,p) in enumerate(pairs):
            row = doc.get("data",{}).get(f"a{i}",{})
            nodes = row.get("nodes",[])
            if len(nodes) != row.get("issueCount"):
                continue
            exact = [n for n in nodes if n.get("title") == g]
            if not exact or not any(n.get("number")==p for n in exact):
                continue
            if any(type(n.get("number")) is not int or not isinstance(n.get("createdAt"),str)
                   for n in exact):
                continue
            earliest = min(exact,key=lambda n:(n["createdAt"],n["number"]))
            out[str(p)] = earliest["number"] == p
        return out
    except Exception:
        return {}


def main():
    events=ledger.read(72)
    window=last_closed_window(events)
    if not window:
        print("no observed closed surge window")
        return 0
    folder=Path(config.STATE_ROOT)/"cache"/"batch-scorecards"
    folder.mkdir(parents=True,exist_ok=True)
    path=folder/(str(int(window[1]))+".json")
    try:
        old=json.loads(path.read_text())
    except (OSError,ValueError):
        old={}
    first=old.get("first_evidence",{})
    data=summarize(events,window,first)
    if "--refresh" in sys.argv[1:]:
        # Wait for search indexing, query at most five unresolved PRs per pass.
        if time.time()-window[1]>=1800:
            pending={g:p for g,p in data["prs"].items() if str(p) not in first}
            first.update(observe_first(pending))
        data=summarize(events,window,first)
        try:
            leaderboard.update()
        except Exception:
            pass
    score=leaderboard.load()
    data.update(first_evidence=first, observed_at=time.time(),
                official_points_total=score.get("our_points") if score.get("available") else None,
                official_score_checked_at=score.get("source_checked_at"),
                note="First status uses complete indexed exact-title search; unknown is explicit. "
                     "Official points are the all-time total, not an attribution to this batch.")
    state.atomic_write(str(path),json.dumps(data,sort_keys=True)+"\n")
    print(json.dumps(data,sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

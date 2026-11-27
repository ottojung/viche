"""Post-batch outcome measurement. Read-only with respect to the desk and proofs."""
import json
from pathlib import Path
import statistics
import subprocess
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


def cohort_credit(events, data, score):
    """Credit for cohort units, only from the official contributor export.

    Local verdicts and PR creation never award points. Earlier credits and
    credits after a later, different PR for the same unit are not attributed.
    The export identifies units, not GitHub PR numbers.
    """
    credits = score.get("our_credit_details") if score.get("available") else None
    if not isinstance(credits, dict):
        return {"official_credited_units": None, "official_cohort_points": None,
                "official_estimated_points": None, "official_ambiguous_units": None}
    opened = {}
    later = {}
    for e in events:
        gid = e.get("gid")
        if e.get("stage") != "pr_opened" or gid not in data["prs"]:
            continue
        t, pr = e["t"], e.get("pr")
        if data["start"] <= t <= data["end"] and pr == data["prs"][gid]:
            opened[gid] = min(opened.get(gid, t), t)
        elif t > data["end"] and pr != data["prs"][gid]:
            later[gid] = min(later.get(gid, t), t)
    matched, ambiguous = [], 0
    for gid, t in opened.items():
        c = credits.get(gid)
        if not isinstance(c, dict) or c["at"] < t:
            continue
        if gid in later and later[gid] <= c["at"]:
            ambiguous += 1
        else:
            matched.append(c)
    return {"official_credited_units": len(matched),
            "official_cohort_points": sum(c["points"] for c in matched),
            "official_estimated_points": sum(c["points"] for c in matched if c["estimated"]),
            "official_ambiguous_units": ambiguous}


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


def board_report(data):
    from .readiness import MANDATE
    count = len(data["prs"])
    text = (f"PnP batch scorecard: {data['seen']} observed units, "
            f"{data['leased']} leased, {count} PRs, "
            f"{data['first']} indexed first / {data['later']} later / "
            f"{data['first_unknown']} unknown; {data['accepted']} accepted verdicts. "
            f"Median lease-to-PR: {data['median_lease_to_pr_s']} s. "
            f"Official cohort-unit credit: {data['official_credited_units']} units, "
            f"{data['official_cohort_points']} points (estimated subset "
            f"{data['official_estimated_points']}; ambiguous units {data['official_ambiguous_units']}). "
            f"Official all-time points: {data['official_points_total']} "
            f"(source checked {data['official_score_checked_at']}). "
            "Credit is matched by official unit ID, not by GitHub PR number.")
    try:
        p=subprocess.run(["antonina","board","comment","--id",MANDATE,
                          "--author","Viche PnP scorecard","--body",text],
                         capture_output=True,timeout=15)
        return p.returncode==0
    except (OSError,subprocess.SubprocessError):
        return False


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
    data.update(cohort_credit(events,data,score))
    data.update(first_evidence=first, observed_at=time.time(),
                official_points_total=score.get("our_points") if score.get("available") else None,
                official_score_checked_at=score.get("source_checked_at"),
                note="First status uses complete indexed exact-title search; unknown is explicit. "
                     "Cohort credit joins official unit IDs and timestamps; exact PR attribution is unavailable.")
    data["board_report_at"]=old.get("board_report_at")
    # First report after every observed window; later reports at most hourly
    # when accepted, race or points evidence actually changes.
    fields=("accepted","first","later","first_unknown","official_points_total",
            "official_credited_units","official_cohort_points","official_estimated_points","official_ambiguous_units")
    changed=any(data.get(k)!=old.get("board_report_values",{}).get(k) for k in fields)
    data["board_report_values"]=old.get("board_report_values",{})
    state.atomic_write(str(path),json.dumps(data,sort_keys=True)+"\n")
    if "--report" in sys.argv[1:] and changed and time.time()-(data["board_report_at"] or 0)>=3600:
        if board_report(data):
            data["board_report_at"]=time.time()
            data["board_report_values"]={k:data[k] for k in fields}
            state.atomic_write(str(path),json.dumps(data,sort_keys=True)+"\n")
    print(json.dumps(data,sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

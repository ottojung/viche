"""Bounded read-only race audit. Missing evidence is unknown, not a win."""
import argparse
from datetime import datetime, timezone
import json
import math
import statistics
import time

from . import config, github, leaderboard, ledger


def epoch(s):
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d.timestamp() if d.tzinfo else None
    except (AttributeError, ValueError, TypeError, OverflowError):
        return None


def audit_events(events, since):
    seen, leased, prs = {}, {}, {}
    for e in sorted((e for e in events if isinstance(e,dict) and type(e.get("t")) in (int,float) and math.isfinite(e["t"])), key=lambda x: x["t"]):
        gid, t, stage = e.get("gid"), e.get("t"), e.get("stage")
        if not isinstance(gid, str) or not config.GAP_ID_RE.fullmatch(gid) or type(t) not in (int, float):
            continue
        if stage == "seen":
            seen.setdefault(gid, t)
        elif stage == "leased":
            leased[gid] = e
        elif stage == "pr_opened" and t >= since and type(e.get("pr")) is int:
            if e["pr"] in prs:
                continue
            lease = leased.get(gid, {})
            prs[e["pr"]] = dict(gid=gid, pr=e["pr"], t=t,
                                 seen=seen.get(gid), leased=lease.get("t"),
                                 proof_of=lease.get("proof_of"), lane=lease.get("lane"))
    return sorted(prs.values(), key=lambda x: x["t"], reverse=True)


def classify(row, search):
    if not isinstance(search, dict):
        return "unknown"
    nodes, total = search.get("nodes"), search.get("issueCount")
    if not isinstance(nodes, list) or type(total) is not int or total != len(nodes):
        return "unknown"
    exact = [n for n in nodes if isinstance(n, dict) and n.get("title") == row["gid"]]
    ours = [n for n in exact if n.get("number") == row["pr"]]
    if len(ours) != 1 or (ours[0].get("author") or {}).get("login", "").lower() != config.DESK_HANDLE.lower():
        return "unknown"
    when = epoch(ours[0].get("createdAt"))
    if when is None or any(epoch(n.get("createdAt")) is None or type(n.get("number")) is not int for n in exact):
        return "unknown"
    # PR numbers strictly order creation within one repository, including equal timestamps.
    earlier = [n for n in exact if n["number"] < row["pr"] and epoch(n["createdAt"]) <= when]
    if earlier:
        if any((n.get("author") or {}).get("login", "").lower() not in ("",config.DESK_HANDLE.lower()) for n in earlier):
            return "rival_first"
        if all((n.get("author") or {}).get("login", "").lower() == config.DESK_HANDLE.lower() for n in earlier):
            return "own_earlier"
        return "unknown"
    if any(n["number"] < row["pr"] or epoch(n["createdAt"]) < when for n in exact):
        return "unknown"
    return "first_observed"


def sample_races(rows, query=None):
    if not rows:
        return []
    repo = github.repository_name(config.UPSTREAM_ID) if query is None else "test/repo"
    # Aliased search calls, exact title filter on return. Search is indexed and
    # can be delayed; first_observed means no earlier indexed exact-title PR.
    clauses = []
    for i, r in enumerate(rows):
        q = f'repo:{repo} is:pr in:title "{r["gid"]}"'
        clauses.append(f'a{i}:search(type:ISSUE,query:{json.dumps(q)},first:100){{issueCount nodes{{... on PullRequest{{number title createdAt author{{login}}}}}}}}')
    raw = (query or (lambda q: github.gh("api", "graphql", "-f", "query="+q)))("query { "+" ".join(clauses)+" }")
    doc = json.loads(raw) if isinstance(raw, str) else raw
    data = doc.get("data", {}) if not doc.get("errors") else {}
    return [dict(gid=r["gid"], pr=r["pr"], result=classify(r, data.get(f"a{i}"))) for i, r in enumerate(rows)]


def duration_summary(rows, name):
    values = sorted(r["t"] - r[name] for r in rows if r[name] is not None and r["t"] >= r[name])
    return {"n": len(values), "median_s": round(statistics.median(values), 1) if values else None,
            "p90_s": round(values[math.ceil(.9*len(values))-1], 1) if values else None}


def points_rate(samples, since):
    good = {}
    for s in samples:
        t = epoch(s.get("source_checked_at"))
        if s.get("score_metric") == "points" and s.get("available") is True and t is not None and type(s.get("our_points")) is int:
            good[t] = s["our_points"]
    inside = sorted((t,p) for t,p in good.items() if t >= since)
    if len(inside) < 2:
        return None
    a,b = inside[0],inside[-1]
    h = (b[0]-a[0])/3600
    return {"hours": round(h, 3), "points_delta": b[1]-a[1], "points_per_hour": round((b[1]-a[1])/h,2)}


def read_history():
    path = leaderboard.record_path() / "history.jsonl"
    try:
        with path.open() as f:
            out = []
            for l in f:
                try:
                    d = json.loads(l)
                    if isinstance(d,dict):out.append(d)
                except ValueError:pass
            return out
    except (OSError, ValueError):
        return []


def report(hours, sample, now=None):
    now = time.time() if now is None else now
    since = now - hours*3600
    rows = audit_events(ledger.read(hours=24*30), since)
    results = []
    error = None
    try:
        results = sample_races(rows[:sample])
    except Exception as e:
        error = type(e).__name__
        results = [dict(gid=r["gid"],pr=r["pr"],result="unknown") for r in rows[:sample]]
    first = sum(r["result"]=="first_observed" for r in results)
    own = sum(r["result"]=="own_earlier" for r in results)
    late = sum(r["result"]=="rival_first" for r in results)
    current = None
    try:
        head = leaderboard.fetch_json(leaderboard.BASE+"head.json")
        rel = head["files"]["contributors"]
        if not leaderboard.PATH_RE.fullmatch(rel):
            raise ValueError("unexpected path")
        source = leaderboard.fetch_json(leaderboard.BASE+rel)
        current = leaderboard.scoreboard(source.get("contributors",source.get("entries")))
        if current.get("score_metric") != "points":
            raise ValueError("legacy scoreboard")
        current.update(available=True, source_checked_at=head.get("checked_at") or head.get("generated_at"))
    except Exception:
        current = None
    return dict(window_hours=hours, prs=len(rows), sighting_to_pr=duration_summary(rows,"seen"),
                lease_to_pr=duration_summary(rows,"leased"),
                posting_prs=sum(r["lane"]=="posting" for r in rows),
                sampled=len(results), first_observed=first, rival_first=late,
                own_earlier=own, unknown=len(results)-first-late-own,
                first_share_known=round(first/(first+late+own),3) if first+late+own else None,
                sample_error=error, sample=results, leaderboard=current,
                credited_rate=points_rate(read_history()+([current] if current else []),since),
                caveat="First observed is indexed exact-title GitHub search; sample is most recent, not random. Sighting is local ledger, not desk creation.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--hours", type=float, default=6)
    p.add_argument("--sample", type=int, default=12)
    a = p.parse_args()
    if not 0 < a.hours <= 720 or not 0 <= a.sample <= 20:
        p.error("hours must be in (0,720], sample in [0,20]")
    print(json.dumps(report(a.hours,a.sample), indent=2, sort_keys=True))

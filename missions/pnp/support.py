"""Parallel research evidence, scoped to an immutable lease; never a gate."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import time

from . import assignment, config, focus, gitctl, github, state
from .proofs import corpus

ROLES = ("knowledge", "methods", "flow")
DECISION_ROLES = ("portfolio", "lease-evaluation")
PREFIX = "Viche P vs NP support:"
KINDS = (*ROLES, "checked")
LIVE = ("LEASED", "RESEARCHING")


def active(rec, now=None):
    return bool(isinstance(rec, dict) and rec.get("state") in LIVE
                and isinstance(rec.get("lease"), str) and rec["lease"]
                and isinstance(rec.get("statement"), str)
                and isinstance(rec.get("lease_expires_at"), (float, int))
                and rec["lease_expires_at"] > (time.time() if now is None else now))


def attempt(rec):
    # Bind evidence to both lease and exact statement, never expose the lease.
    return assignment.attempt_id(rec["lease"]) + "-" + hashlib.sha256(
        rec["statement"].encode()).hexdigest()[:16]


def directory(rec):
    return Path(state.gap_dir(rec["gap_id"]), "support", attempt(rec))


def read(rec):
    if not active(rec):
        return []
    result = []
    for kind in KINDS:
        try:
            path = directory(rec) / (kind + ".json")
            if path.stat().st_size > 8192:
                continue
            obj = json.loads(path.read_text())
            if (obj.get("attempt") == attempt(rec) and obj.get("kind") == kind
                    and isinstance(obj.get("message"), str)
                    and isinstance(obj.get("evidence"), str)
                    and isinstance(obj.get("id"), str)
                    and type(obj.get("coordinate")) is bool):
                result.append(obj)
        except (OSError, ValueError, TypeError, AttributeError):
            continue
    return result


def advise(gap, expected, kind, evidence, message, coordinate=False):
    if kind not in KINDS or not evidence.strip() or not message.strip():
        raise ValueError("kind, evidence and actionable finding required")
    if len(evidence) > 1200 or len(message) > 1600:
        raise ValueError("put long evidence in a file and link it")
    with state.lock(gap):
        rec = state.load(gap)
        if not active(rec) or expected != attempt(rec):
            raise ValueError("assignment ended or changed; preserve finding separately")
        obj = {"gap": gap, "attempt": expected, "kind": kind,
               "evidence": evidence, "message": message, "coordinate": bool(coordinate)}
        obj["id"] = hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:24]
        path = directory(rec) / (kind + ".json")
        text = json.dumps(obj, sort_keys=True, ensure_ascii=False) + "\n"
        if not path.exists() or path.read_text() != text:
            state.atomic_write(str(path), text)
        return obj


def findings(rec):
    """Latest substantive result per worker on this exact attempt."""
    if not active(rec):
        return []
    out = []
    for path in sorted((directory(rec) / "findings").glob("*.json")):
        try:
            if path.stat().st_size > 10000:
                continue
            obj = json.loads(path.read_text())
            if (obj.get("attempt") == attempt(rec) and obj.get("worker") == path.stem
                    and all(isinstance(obj.get(k), str) for k in ("message","evidence","id"))):
                out.append(obj)
        except (OSError, ValueError, TypeError, AttributeError):
            continue
    return out


def finding(evidence, message, cwd=None):
    """Bound researchers publish findings directly, no intermediary."""
    bound = assignment.binding(cwd)
    label = assignment.worker_label(cwd)
    if not bound or not label:
        raise ValueError("run from your immutable assigned workspace")
    if not evidence.strip() or not message.strip() or len(evidence)>1200 or len(message)>4000:
        raise ValueError("substantive evidence and result required; link long artifacts")
    gap, lease = bound
    with state.lock(gap):
        rec = state.load(gap)
        if not active(rec) or rec["lease"] != lease:
            raise ValueError("lease ended; preserve findings in your workspace")
        obj = {"gap":gap,"attempt":attempt(rec),"worker":label,
               "evidence":evidence,"message":message}
        obj["id"] = hashlib.sha256(json.dumps(obj,sort_keys=True).encode()).hexdigest()[:24]
        path = directory(rec) / "findings" / (label+".json")
        try:
            if json.loads(path.read_text()).get("id") == obj["id"]:
                return obj
        except (OSError, ValueError, AttributeError):
            pass
        obj["at"] = time.time()
        state.atomic_write(str(path),json.dumps(obj,ensure_ascii=False,sort_keys=True)+"\n")
        state.event(gap,"research_finding",obj)
        return obj


def targets(all_held=False):
    out = []
    selected = focus.current()
    gaps = state.all_gaps() if all_held else ([selected["gap_id"]] if selected else [])
    for gap in gaps:
        try:
            rec = state.load(gap)
            if active(rec):
                out.append({"gap": gap, "attempt": attempt(rec),
                            "statement": rec["statement"], "imports": rec.get("imports", []),
                            "context": (rec.get("context") or "")[:3000],
                            "advice": read(rec), "findings": findings(rec)})
        except (OSError, ValueError, TypeError, KeyError):
            continue
    return out


def tokens(s):
    # Advisory syntactic match only: preserve identifiers and punctuation.
    # Do not infer semantic equivalence or invalidate leases from this.
    return tuple(re.findall(r"[\w'.]+|[^\s\w'.]", s, re.UNICODE))


def unnegate(ts):
    """Recognize a negated final parenthesized conclusion, not nested subterms."""
    for i in range(len(ts)-2):
        if ts[i:i+2] != ("¬", "(") or (i and ts[i-1] != "→"):
            continue
        depth = 0
        for j in range(i+1, len(ts)):
            if ts[j] == "(":
                depth += 1
            elif ts[j] == ")":
                depth -= 1
                if depth == 0:
                    if j == len(ts)-1:
                        yield ts[:i] + ts[i+2:j]
                    break


def matches(db, statement):
    goal = tokens(statement)
    neg = set(unnegate(goal))
    hits = []
    for path, blob, stmt in db.execute("select path,blob,statement from proof"):
        t = tokens(stmt)
        if t == goal:
            relation = "exact statement"
        elif goal in unnegate(t) or t in neg:
            relation = "opposite conclusion"
        else:
            continue
        hits.append({"path": path, "blob": blob, "relation": relation})
    return hits


def scan(refresh=False):
    # The scanner is independent of the Executive and publication. No
    # cancellation, desk release, agent commands, or publication mutation.
    work = targets(all_held=True)
    if not work:
        return {"active": 0, "matches": 0}
    if refresh:
        gitctl.ensure_mirror()
    count = 0
    with corpus.open_index() as db:
        revision = corpus.update(db)
        for item in work:
            hits = matches(db, item["statement"])
            if not hits:
                # Only a successful fresh corpus scan may withdraw old advice.
                with state.lock(item["gap"]):
                    rec = state.load(item["gap"])
                    if active(rec) and attempt(rec) == item["attempt"]:
                        (directory(rec) / "checked.json").unlink(missing_ok=True)
                continue
            hit = hits[0]
            evidence = "https://github.com/" + github.repository_name(config.UPSTREAM_ID) + "/blob/" + revision + "/" + hit["path"]
            # Keep evidence IDs stable as upstream adds unrelated commits.
            old = next((a for a in item["advice"] if a["kind"] == "checked"), None)
            marker = "Proof blob " + hit["blob"] + "."
            if old and marker in old["message"] and hit["relation"] in old["message"]:
                count += 1
                continue
            message = ("Checked upstream corpus has a syntactic " + hit["relation"]
                       + " match. Read the exact theorem and verify the conclusion, hypotheses, "
                       "and checked status immediately; if confirmed, stop obsolete research "
                       "cooperatively and notify Executive. This is advisory, not a proof verdict. " + marker)
            try:
                advise(item["gap"], item["attempt"], "checked", evidence, message, True)
                count += 1
            except ValueError:
                continue
    return {"active": len(work), "matches": count, "revision": revision}


def roles(agent):
    title = agent.get("title") or ""
    if not isinstance(title, str) or not title.startswith(PREFIX):
        return []
    return sorted({part.strip() for part in title[len(PREFIX):].split(",")} & set(ROLES + DECISION_ROLES))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("targets")
    f = sub.add_parser("finding")
    f.add_argument("--evidence",required=True)
    f.add_argument("--message",required=True)
    check = sub.add_parser("scan")
    check.add_argument("--refresh", action="store_true")
    a = sub.add_parser("advise")
    a.add_argument("gap")
    a.add_argument("attempt")
    a.add_argument("kind", choices=ROLES)
    a.add_argument("evidence")
    a.add_argument("message")
    a.add_argument("--coordinate", action="store_true")
    args = p.parse_args()
    try:
        result = (targets() if args.command == "targets" else
                  scan(args.refresh) if args.command == "scan" else
                  finding(args.evidence,args.message) if args.command == "finding" else
                  advise(args.gap, args.attempt, args.kind, args.evidence,
                         args.message, args.coordinate))
    except (OSError, ValueError, gitctl.GitError) as exc:
        p.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

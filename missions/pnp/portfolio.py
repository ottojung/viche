"""Researcher decisions, consumed by the single deterministic lease allocator.

No model or human approval gate: the two evaluators own their decisions.
Evidence, exact attempt identities and safe state transitions are mandatory.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time

from . import config, focus, frontier, jobs, state, support

ROLES = ("portfolio", "lease-evaluation")
MAX_AGE = 15 * 60
MIN_HARD_AGE = 20 * 60


def path(kind):
    return Path(config.STATE_ROOT, "portfolio-" + kind + ".json")


def record(gap, attempt, allow_correction=False):
    if not config.GAP_ID_RE.fullmatch(gap):
        raise ValueError("invalid gap")
    rec = state.load(gap)
    eligible = support.active(rec) or (allow_correction and focus.correction(rec)
        and isinstance(rec.get("lease"), str) and isinstance(rec.get("statement"), str))
    if not eligible or rec.get("queued_lease") or support.attempt(rec) != attempt:
        raise ValueError("no matching live research lease")
    return rec


def view():
    chosen = focus.current()
    observed = frontier.load()
    rows = []
    from . import status
    roster = status.workers()
    for item in support.targets(all_held=True):
        rec = state.load(item["gap"])
        if not support.active(rec) or support.attempt(rec) != item["attempt"]:
            continue
        workers = [{"id": a["id"], "title": a.get("title"), "cwd": a["cwd"],
                    "role": "general" if support.assignment.general(Path(a["cwd"])) else "specialist",
                    "log_command": "antonina agent log --id " + a["id"] + " --lines 50"}
                   for a in roster["agents"] if a.get("id") and a.get("cwd")
                   and support.assignment.binding(Path(a["cwd"])) == focus.key(rec)]
        # Exited workers' actual findings/logs remain useful to the evaluator.
        # Staffing receipts are attempt-scoped; never relabel an old lease.
        prior = {}
        try:
            for line in Path(state.events_path(item["gap"])).read_text().splitlines():
                event = json.loads(line)
                detail = event.get("detail", {})
                if event.get("kind") != "staffing" or detail.get("attempt") != item["attempt"]:
                    continue
                for worker in detail.get("workers", []):
                    aid = worker.get("agent")
                    if isinstance(aid,str):
                        prior[aid] = {**worker, "at":event.get("at"),
                                      "log_command":"antonina agent log --id "+aid+" --lines 50"}
        except (OSError,ValueError,TypeError,AttributeError):
            pass
        rows.append({**item, "workers":workers, "staffing_history":list(prior.values()),"title": rec.get("gap_title"),
                     "hard": rec.get("acquisition_hard"),
                     "candidate_queued": bool(rec.get("queued_lease")),
                     "remaining_seconds": max(0, round(rec["lease_expires_at"]-time.time())),
                     "age_seconds": round(time.time()-(rec.get("lease_obtained_at") or time.time())),
                     "competition": observed.get("gaps", {}).get(item["gap"]),
                     "artifacts": state.gap_dir(item["gap"]),
                     "focus": bool(chosen and focus.key(chosen) == focus.key(rec))})
    corrections = []
    for gap in state.all_gaps():
        rec = state.load(gap)
        if not focus.correction(rec) or not rec.get("lease") or not isinstance(rec.get("statement"), str):
            continue
        corrections.append({"gap": gap, "attempt": support.attempt(rec),
                            "title": rec.get("gap_title"), "statement": rec["statement"],
                            "pr_url": rec.get("pr_url"), "revision": rec.get("commit_sha"),
                            "local_check_status": rec.get("local_check_status"),
                            "external_verdict": rec.get("external_verdict"),
                            "artifacts": state.gap_dir(gap),
                            "worktree": rec.get("worktree"),
                            "focus": bool(chosen and focus.key(chosen) == focus.key(rec))})
    return {"focus": chosen["gap_id"] if chosen else None,
            "leases": rows, "corrections": corrections, "worker_roster_coverage":roster["coverage"]}


def text_field(value, name):
    if not isinstance(value, str) or not value.strip() or len(value) > 4000:
        raise ValueError(name + " must be substantive text (link longer artifacts)")
    return value.strip()


def submit(kind, gap, attempt, evidence, reason, current=None, current_attempt=None):
    rec = record(gap, attempt, allow_correction=(kind == "switch"))
    evidence, reason = text_field(evidence, "evidence"), text_field(reason, "reason")
    if kind == "switch":
        old = record(current, current_attempt, allow_correction=True)
        selected = focus.current()
        if not selected or focus.key(selected) != focus.key(old) or current == gap:
            raise ValueError("focus changed; reassess the actual portfolio")
    elif kind == "release":
        acquired = rec.get("lease_obtained_at")
        if rec.get("acquisition_hard") is not False and (
                not isinstance(acquired, (int, float)) or time.time()-acquired < MIN_HARD_AGE):
            raise ValueError("hard lease must be held at least twenty minutes before release")
    else:
        raise ValueError("unknown decision")
    obj = {"kind": kind, "gap": gap, "attempt": attempt, "evidence": evidence,
           "reason": reason, "from": current, "from_attempt": current_attempt,
           "at": time.time()}
    if kind == "switch":
        # A correction is tied to the precise published revision, not merely
        # a still-identical statement and old lease.
        obj["to_revision"] = rec.get("commit_sha") if focus.correction(rec) else None
        obj["from_revision"] = old.get("commit_sha") if focus.correction(old) else None
    obj["id"] = hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:24]
    # One pending decision per independent evaluator. Atomic latest decision;
    # the allocator consumes it once and records the result.
    state.atomic_write(str(path(kind)), json.dumps(obj, sort_keys=True)+"\n")
    return {"queued": kind, "gap": gap, "id": obj["id"]}


def pending(kind, mem, now):
    try:
        obj = json.loads(path(kind).read_text())
        if (not isinstance(obj, dict) or obj.get("kind") != kind or
                not isinstance(obj.get("id"), str) or obj["id"] == mem.get("decision_"+kind)):
            return None
        if not 0 <= now-obj["at"] <= MAX_AGE:
            return None
        text_field(obj.get("reason"), "reason")
        text_field(obj.get("evidence"), "evidence")
        return obj
    except (OSError, ValueError, TypeError, KeyError):
        return None


def finish(mem, obj, outcome):
    mem["decision_"+obj["kind"]] = obj["id"]
    mem["last_"+obj["kind"]] = {
        k: obj.get(k) for k in ("id", "gap", "from", "reason", "evidence", "at")}
    mem["last_"+obj["kind"]]["outcome"] = outcome
    print("portfolio decision", obj["kind"], obj["gap"], outcome, flush=True)


def apply_switch(mem, now):
    obj = pending("switch", mem, now)
    if not obj:
        return
    try:
        old = record(obj["from"], obj["from_attempt"], allow_correction=True)
        new = record(obj["gap"], obj["attempt"], allow_correction=True)
        for rec, field in ((old,"from_revision"),(new,"to_revision")):
            revision = rec.get("commit_sha") if focus.correction(rec) else None
            if revision != obj.get(field):
                raise ValueError("correction revision changed")
        chosen = focus.current()
        if not chosen or focus.key(chosen) != focus.key(old):
            raise ValueError("source focus changed")
        if focus.key(old) == focus.key(new):
            raise ValueError("already focused")
    except (ValueError, TypeError, KeyError) as exc:
        finish(mem, obj, "obsolete: " + str(exc))
        return
    # Preserve both live leases and the baseline researchers. Executive
    # moves only extra specialists; completed candidates remain protected.
    mem["focus"] = list(focus.key(new))
    state.event(new["gap_id"], "portfolio_focus", {k:obj[k] for k in ("id","from","reason","evidence")})
    finish(mem, obj, "applied")


def apply_release(d, mem, now):
    obj = pending("release", mem, now)
    if not obj:
        return []
    gap = obj.get("gap")
    try:
        rec = record(gap, obj["attempt"])
        if rec.get("acquisition_hard") is not False and (
                not isinstance(rec.get("lease_obtained_at"), (int, float))
                or now-rec["lease_obtained_at"] < MIN_HARD_AGE):
            raise ValueError("hard minimum holding time not reached")
    except (ValueError, TypeError, KeyError) as exc:
        finish(mem, obj, "obsolete: " + str(exc))
        return []
    fd = jobs.claim(gap)
    if fd is None:
        return []
    try:
        with state.lock(gap):
            try:
                latest = record(gap, obj["attempt"])
            except (ValueError, TypeError, KeyError) as exc:
                finish(mem, obj, "obsolete: " + str(exc))
                return []
            if latest.get("intent") and latest["intent"].get("what") != "portfolio_release":
                return []
            latest["intent"] = {"what":"portfolio_release", "payload":{"decision":obj["id"],"reason":"other"}}
            state.save(latest)
            try:
                d.release(latest["lease"], "other")
            except Exception as exc:
                # No state transition on uncertain remote result; retry
                # this exact decision, or reconcile a confirmed 410.
                print("portfolio release deferred:", gap, str(exc)[:300], flush=True)
                return []
            latest.update(state="RELEASED", failure_reason="other", intent=None)
            state.save(latest)
            state.event(gap, "portfolio_release", {k:obj[k] for k in ("id","reason","evidence")})
        # Newly vacant capacity should be filled immediately.
        mem.pop("last_null_ordinary", None)
        mem.pop("last_null_hard", None)
        finish(mem, obj, "applied")
        return [gap]
    finally:
        os.close(fd)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    subs = p.add_subparsers(dest="kind", required=True)
    subs.add_parser("inspect")
    for kind in ("switch","release"):
        sub = subs.add_parser(kind)
        sub.add_argument("gap")
        sub.add_argument("attempt")
        sub.add_argument("--reason", required=True)
        sub.add_argument("--evidence", required=True)
        if kind == "switch":
            sub.add_argument("--from-gap", required=True)
            sub.add_argument("--from-attempt", required=True)
    a = p.parse_args()
    try:
        result = view() if a.kind == "inspect" else submit(
            a.kind,a.gap,a.attempt,a.evidence,a.reason,
            getattr(a,"from_gap",None),getattr(a,"from_attempt",None))
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (OSError,ValueError,TypeError,KeyError) as exc:
        p.error(str(exc))


if __name__ == "__main__":
    main()

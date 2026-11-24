#!/usr/bin/env python3
"""Read-only P vs NP mission state and independent, Executive-owned worker signal."""
import collections
import datetime
import json
import os
import re
import time
from pathlib import Path
import subprocess
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from missions.pnp import leaderboard, frontier, assignment, support, focus
else:
    from . import leaderboard, frontier, assignment, support, focus

STATE = Path(os.environ.get("VICHE_STATE_ROOT",
                            "/var/lib/lubko/wd/viche-state"))


def workers():
    """Unknown must never be reported as zero; the Executive must investigate."""
    try:
        p = subprocess.run(["antonina", "agent", "list", "--running",
                            "--page", "1", "--limit", "100", "--json"],
                           capture_output=True, text=True, timeout=8, check=True)
        data = json.loads(p.stdout)
        agents = data.get("agents")
        if not isinstance(agents, list):
            raise ValueError("unreadable agent roster")
        filtered = [a for a in agents if
                    (a.get("title") or "").startswith("Viche P vs NP:") or
                    (a.get("cwd") and assignment.workspace(Path(a["cwd"])))]
        coverage = ("partial" if len(agents) >= 100 or data.get("unreadable")
                    else "complete")
        scouts = [{"id": a.get("id"), "title": a.get("title"), "roles": support.roles(a),
                   "state": a.get("state"), "cwd": a.get("cwd")}
                  for a in agents if support.roles(a)]
        return {"support": scouts, "count": len(filtered), "coverage": coverage,
                "agents": [{"id": a.get("id"), "title": a.get("title"),
                            "state": a.get("state"), "cwd": a.get("cwd")}
                           for a in filtered]}
    except (OSError, ValueError, subprocess.SubprocessError):
        return {"support": [], "count": None, "coverage": "unavailable", "agents": []}


def snapshot():
    rows = []
    for path in sorted((STATE / "pnp/gaps").glob("*/state.json")):
        try:
            item = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        rows.append({"gap": item.get("gap_id"),
                     "state": item.get("state"),
                     "pr_url": item.get("pr_url"),
                     "lease_expires_at": item.get("lease_expires_at"),
                     "lease_obtained_at": item.get("lease_obtained_at"),
                     "resource_deferred": bool(item.get("publisher_memory_required") and not frontier.build_control.resource_ready(item)) if item.get("state") in ("CANDIDATE_READY", "LOCAL_CHECKED") else False,
                     "local_check_status": item.get("local_check_status"),
                     "correction_queued": bool(item.get("queued_lease")),
                     "external_verdict": item.get("external_verdict"),
                     "failure_reason": item.get("failure_reason")})
    lb = leaderboard.load()
    stale = True
    if lb.get("available"):
        try:
            age = (datetime.datetime.now(datetime.timezone.utc) -
                   datetime.datetime.fromisoformat(
                       lb["observed_at"].replace("Z", "+00:00"))).total_seconds()
            stale = age > 1800
        except (KeyError, ValueError):
            stale = True
    w = workers()
    observed = frontier.load()
    by_gap = {r["gap"]: r for r in rows}
    for worker in w["agents"]:
        match = re.search(r"\bL-[a-z0-9]+(?:-[a-z0-9]+)+\b", worker.get("title") or "")
        bound = assignment.binding(Path(worker["cwd"])) if worker.get("cwd") else None
        gid = bound[0] if bound else match.group(0) if match else None
        worker["gap"] = gid
        worker["bound"] = bool(bound)
        worker["lease_current"] = None
        if bound:
            try:
                rec = frontier.state.load(gid)
                if isinstance(rec, dict) and rec.get("lease"):
                    worker["lease_current"] = rec["lease"] == bound[1]
            except (OSError, ValueError):
                pass
        worker["gap_state"] = by_gap.get(gid, {}).get("state")
        worker["competition"] = observed.get("gaps", {}).get(gid)
    corrections = sorted(r["gap"] for r in rows if (r["state"] == "REJECTED" and not r["correction_queued"]) or (r["state"] == "PR_OPEN" and r["local_check_status"] == "failed" and r["external_verdict"] != "ACCEPTED"))
    stale_workers = [a["id"] for a in w["agents"]
                     if (a["gap_state"] in frontier.STOPPED and a["gap"] not in corrections) or a["lease_current"] is False]
    active = [r["gap"] for r in rows if r["state"] in frontier.ACTIVE
              and type(r["lease_expires_at"]) in (int, float)
              and r["lease_expires_at"] > time.time() and isinstance(r["gap"], str)]
    selected = focus.current()
    focus_gap = selected["gap_id"] if selected else None
    staffed = {a["gap"] for a in w["agents"] if a["lease_current"] is True}
    reserves = sorted(r["gap"] for r in rows if r["gap"] in active and r["gap"] != focus_gap
                      and r["state"] in ("LEASED", "RESEARCHING"))
    focus_workers = [a["id"] for a in w["agents"] if focus_gap and a["gap"] == focus_gap
                     and a["lease_current"] is True]
    unstaffed = [focus_gap] if focus_gap and focus_gap not in staffed and w["coverage"] == "complete" else []
    off_focus = sorted(a["id"] for a in w["agents"] if focus_gap and a["gap"] and a["gap"] != focus_gap and (a["gap_state"] in ("LEASED", "RESEARCHING") or a["gap"] in corrections))
    ordinary = observed.get("ordinary")
    # These are useful opportunities, not automatic staffing instructions.
    # Desk status only exposes title/competition, not individually offerable IDs.
    related = []
    for gid, item in observed.get("gaps", {}).items():
        held, parallel = item.get("held"), item.get("parallel")
        if type(held) is int and type(parallel) is int and held < parallel:
            related.append({"gap": gid, "title": item.get("title"), "held": held, "parallel": parallel})
    related.sort(key=lambda x: (x["held"], x["gap"]))
    coordination_due = bool(w["coverage"] == "complete" and (
        stale_workers or unstaffed or off_focus or
        (focus_gap and len(focus_workers) < 2)))
    # Support agents are never counted as leased researchers. Coverage is
    # a coordination signal, not an agent-number quota or a proof gate.
    scouts = w.pop("support", [])
    covered = {role for agent in scouts for role in agent["roles"]}
    useful = bool(active or corrections or w["count"] or ordinary or observed.get("offerable"))
    needed = set(support.ROLES) if useful else set()
    if active:
        needed.add("lease-evaluation")
    if len(active) > 1:
        needed.add("portfolio")
    missing_support = sorted(needed - covered) if w["coverage"] == "complete" else []
    try:
        memory = json.loads((STATE / "pnp/allocator.json").read_text())
        decisions = {k: memory.get("last_"+k) for k in ("switch","release")}
    except (OSError, ValueError, AttributeError):
        decisions = {}
    findings = []
    for target in support.targets():
        findings.extend(a for a in target["advice"] if a.get("coordinate"))
    coordination_due = coordination_due or bool(missing_support)
    age = {r["gap"]: max(0, round((time.time()-r["lease_obtained_at"])/60))
           for r in rows if r["gap"] in active and type(r["lease_obtained_at"]) in (int,float)}
    score = {k: lb.get(k) for k in ("rank", "our_steps", "leader",
                                   "runner_up", "lead_over_second",
                                   "our_margin_vs_best_competitor",
                                   "additional_steps_to_clear_first",
                                   "source_checked_at", "observed_at",
                                   "margin_change_since_previous_snapshot")}
    score["available"] = lb.get("available", False)
    score["stale"] = stale
    by_state = dict(collections.Counter(r["state"] for r in rows))
    return {
        "observed": len(rows), "by_state": by_state, "recent": rows[-12:],
        "leaderboard": score, "workers": w,
        "research_support": {"agents": scouts, "coverage_missing": missing_support,
                             "coordination_findings": findings,
                             "portfolio_decisions": decisions,
                             "action": "Executive owns staffing and material steering; support findings are advisory and arrive directly in worker guards."},
        "frontier": {k: observed.get(k) for k in ("offerable", "ordinary", "open_gaps", "held")},
        "frontier_fresh": bool(observed), "active_lease_gaps": active,
        "research_focus": focus_gap, "focus_workers": focus_workers, "reserve_gaps": reserves,
        "focus_details": ({k: selected.get(k) for k in ("gap_title", "statement", "imports", "context")}
                          if selected else None),
        "staff_command": ("python3 -m missions.pnp.staff " + focus_gap + " --worker LABEL=APPROACH"
                          if focus_gap else None),
        "off_focus_workers": off_focus,
        "unstaffed_active_gaps": unstaffed, "active_lease_age_minutes": age,
        "potential_fronts": related[:12],
        "coordination_due": coordination_due, "correction_needed": corrections,
        "publisher_build_busy": frontier.build_control.busy(),
        "legacy_lean_compiler_pids": frontier.build_control.legacy_compilers(),
        "lean_headroom_bytes": frontier.build_control.headroom(),
        "resource_deferred_gaps": [r["gap"] for r in rows if r.get("resource_deferred")],
        "workers_on_terminal_gaps": stale_workers,
        "owned_by": "Viche Executive; other operators do not launch agents",
        "action": (
            "Executive: retire obsolete workers cooperatively and concentrate useful research on research_focus. Preserve artifacts; reserve gaps need no workers."
            if stale_workers else
            "Executive must concentrate independent P vs NP researchers on research_focus "
            "and coordinate submissions; reserve gaps intentionally have no workers."
            if not focus_workers else
            "Executive must parallelize distinct proof approaches on research_focus, "
            "not distribute researchers across reserve gaps."
            if len(focus_workers) == 1 else
            "Executive must restore visibility of the actual worker roster."
            if w["count"] is None else
            "Executive must increase the verified checked-step lead over #2 "
            "and protect the lead trajectory."
            if score.get("rank") == 1 else
            "Executive must increase checked-step throughput to gain #1; "
            "evaluate research yield, resources and worker replenishment."),
        # No timestamps here: the general government dispatch gate changes
        # only when mission facts or staffing change, not every refresh.
        "dispatch_signal": {
            "leaderboard": [score.get("rank"), score.get("our_steps"),
                            (score.get("leader") or {}).get("steps"),
                            (score.get("runner_up") or {}).get("steps")],
            "workers": w["count"], "coverage": w["coverage"],
            "gaps": by_state, "active": sorted(active), "focus": focus_gap,
            "off_focus": off_focus,
            "assignments": sorted((str(a["id"]), a["gap"] or "", a["gap_state"] or "") for a in w["agents"]),
            "ordinary_available": (observed.get("ordinary") or 0) > 0 if observed else None,
            "hard_available": (observed.get("offerable") or 0) > (observed.get("ordinary") or 0) if observed else None,
            "corrections": corrections, "unstaffed": unstaffed,
            "support": sorted((str(a["id"]), ",".join(a["roles"])) for a in scouts),
            "missing_support": missing_support,
            "support_findings": sorted(a["id"] for a in findings),
            "portfolio_decisions": {k: v.get("id") for k,v in decisions.items() if isinstance(v,dict)}, "obsolete_workers": sorted(stale_workers),
            "unbound": sorted(str(a["id"]) for a in w["agents"] if not a["bound"])},
        "caveat": "Only public checked steps count; local activity is not proof."}


if __name__ == "__main__":
    print(json.dumps(snapshot(), sort_keys=True))

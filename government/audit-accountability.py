#!/usr/bin/env python3
"""Deterministic oversight of randomized audit coverage and recorded findings.

Auditor submissions are claims with evidence references, not independently verified
facts. The controller never declares an issue solved from agent completion alone.
"""
import argparse
import re
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def json_file(path, fallback=None):
    return json.loads(path.read_text()) if path.exists() else fallback


def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")
    os.replace(temp, path)


def base():
    return Path(os.environ.get("VICHE_STATE_ROOT", "/var/lib/lubko/wd/viche-state")) / "oversight" / "random"


def records_dir():
    # Authoritative, Git-anchored append-only trail (Act 17 §2.2). Lives in the
    # town repository, which the audit office does not solely control.
    return Path(os.environ.get("VICHE_TOWN_ROOT", "/var/lib/lubko/wd/viche")) / "records" / "oversight" / "corrections"


def append_correction(case_id, record):
    # Append-only: never overwrite or rewrite a committed entry (Act 17 §2.2, §2.7).
    d = records_dir()
    d.mkdir(parents=True, exist_ok=True)
    with open(d / f"{case_id}.jsonl", "a") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")
    return d / f"{case_id}.jsonl"


def report(args):
    root = base()
    if not re.fullmatch(r"[0-9a-f]{18}", args.case):
        raise ValueError("invalid audit case identifier")
    case = json_file(root / "cases" / f"{args.case}.json")
    if case is None:
        raise ValueError("unknown audit case")
    if not args.evidence or not args.evidence.strip():
        raise ValueError("durable evidence reference is required")
    path = root / "outcomes" / f"{args.case}.json"
    prior = json_file(path)
    now = int(os.environ.get("VICHE_OVERSIGHT_NOW", time.time()))

    if args.confirm:
        # Second procedural pass (Act 17 §2.4): same office, same pinned model.
        # Explicitly NOT independent verification (Constitution X single substrate).
        if prior is None:
            raise ValueError("no prior outcome to confirm against")
        if not prior.get("correction_pending"):
            raise ValueError("no pending correction to confirm")
        pending = None
        for h in prior.get("history", []):
            if h.get("correction") and not h.get("confirmed"):
                pending = h
        if pending is None:
            raise ValueError("no pending correction to confirm")
        pending["confirmed"] = True
        pending["confirmed_at"] = now
        pending["confirm_evidence_ref"] = args.evidence
        append_correction(args.case, {
            "at": now, "case_id": args.case, "verdict": pending["verdict"],
            "evidence_ref": args.evidence, "auditor": pending.get("auditor", ""),
            "correction": True, "supersedes": pending["supersedes"],
            "reason_code": pending.get("reason_code", ""),
            "why_stronger": pending.get("why_stronger", ""),
            "confirmed": True, "phase": "second_procedural_pass_not_independent",
        })
        prior["verdict"] = pending["verdict"]
        prior["at"] = now
        prior["evidence_ref"] = pending["evidence_ref"]
        prior["details"] = pending.get("details", prior.get("details", ""))
        prior["correction_pending"] = False
        if pending["supersedes"] == "finding" and pending["verdict"] != "finding":
            prior["corrected_from_finding"] = True
        atomic(path, prior)
        print(json.dumps(prior))
        return

    if args.correction:
        # File a superseding verdict (Act 17 §2.1-2.2, §2.5-2.6).
        if prior is None:
            raise ValueError("no prior verdict; file an ordinary verdict first")
        if not args.supersedes or args.supersedes != prior["verdict"]:
            raise ValueError("correction must state the verdict it supersedes")
        if prior.get("correction_pending"):
            raise ValueError("one correction per case per cycle (finality)")
        if args.evidence == prior.get("evidence_ref"):
            raise ValueError("correction evidence must be distinct from the original reference")
        if not args.why_stronger or not args.why_stronger.strip():
            raise ValueError("correction must state why the new evidence is stronger")
        if not args.reason_code or not args.reason_code.strip():
            raise ValueError("correction requires a reason_code")
        if not args.auditor or not args.auditor.strip():
            raise ValueError("correction requires auditor identity")
        if args.verdict == "verified_fixed" and prior["verdict"] != "finding":
            raise ValueError("verified_fixed requires a previous finding")
        held = [h.get("verdict") for h in prior.get("history", [])]
        if args.verdict in held:
            raise ValueError("bare re-flip: target verdict already held by this case")
        rec = {
            "at": now, "case_id": args.case, "verdict": args.verdict,
            "evidence_ref": args.evidence, "auditor": args.auditor,
            "correction": True, "supersedes": args.supersedes,
            "reason_code": args.reason_code, "why_stronger": args.why_stronger[:1000],
            "details": args.details[:1000], "confirmed": False,
            "phase": "correction_filed",
        }
        append_correction(args.case, rec)
        hist = prior.get("history", [])
        hist.append(rec)
        prior["history"] = hist
        prior["correction_pending"] = True
        atomic(path, prior)
        print(json.dumps(prior))
        return

    if prior and prior["verdict"] != "finding":
        raise ValueError("case already has a final verdict")
    if args.verdict == "verified_fixed" and (not prior or prior["verdict"] != "finding"):
        raise ValueError("verified_fixed requires a previous finding")
    result = {"case_id": args.case, "population": case["population"],
              "subject": case["id"], "verdict": args.verdict, "at": now,
              "evidence_ref": args.evidence, "details": args.details[:1000],
              "caveat": "auditor_report_not_independent_proof"}
    atomic(path, result)
    print(json.dumps(result))


def listed_agents():
    all_agents = []
    for page in range(1, 101):
        p = subprocess.run(["antonina", "agent", "list", "--running",
                            "--page", str(page), "--json"], capture_output=True,
                           text=True, timeout=30)
        if p.returncode:
            raise RuntimeError(f"agent list failed: {p.stderr[-160:]}")
        data = json.loads(p.stdout)
        if isinstance(data, dict):
            if data.get("unreadable", 0):
                raise RuntimeError("unreadable agent inventory entries")
            items = data.get("agents")
        else:
            items = data
        if not isinstance(items, list):
            raise RuntimeError("invalid agent list response")
        all_agents.extend(items)
        if len(items) < 50:
            return all_agents
    raise RuntimeError("incomplete agent list")


def check(args):
    root = base()
    now = int(os.environ.get("VICHE_OVERSIGHT_NOW", time.time()))
    deadline = int(os.environ.get("VICHE_AUDIT_EVIDENCE_DEADLINE", "21600"))
    if deadline <= 0:
        raise ValueError("invalid deadline")
    signals = []
    cases = list((root / "cases").glob("*.json")) if (root / "cases").exists() else []
    findings = {}
    overdue = 0
    for path in cases:
        case = json_file(path)
        verdict = json_file(root / "outcomes" / path.name)
        if verdict is None and now - int(case["at"]) > deadline:
            overdue += 1
            signals.append({"type": "unreported_sample", "case_id": case["case_id"]})
        if verdict is not None:
            if verdict.get("correction_pending"):
                signals.append({"type": "correction_pending", "case_id": case["case_id"]})
            if verdict["verdict"] == "finding":
                subject = f"{case['population']}:{case['id']}"
                findings[subject] = findings.get(subject, 0) + 1
                signals.append({"type": "unresolved_finding", "case_id": case["case_id"],
                                "evidence_ref": verdict["evidence_ref"]})
            elif verdict.get("corrected_from_finding"):
                signals.append({"type": "corrected_finding", "case_id": case["case_id"],
                                "evidence_ref": verdict["evidence_ref"]})
            if verdict["verdict"] == "inconclusive" and now - verdict["at"] > deadline:
                signals.append({"type": "unresolved_inconclusive", "case_id": case["case_id"]})
    for subject, count in findings.items():
        if count >= 2:
            signals.append({"type": "repeated_finding", "subject": subject,
                            "count": count})
    agents = 0
    try:
        inventory = listed_agents()
        agents = len(inventory)
        for agent in inventory:
            agent_id = str(agent.get("id", ""))
            p = subprocess.run(["antonina", "agent", "status", "--id", agent_id, "--json"],
                               capture_output=True, text=True, timeout=25)
            if p.returncode:
                signals.append({"type": "agent_status_unavailable", "agent_id": agent_id})
                continue
            metadata = json.loads(p.stdout)
            # Model choice belongs to Antonina. An idle agent with no model
            # history is normal; avoid inventing a compliance incident.
            if metadata.get("state") not in ("idle", "running", "succeeded", "failed", "stopped", "killed"):
                signals.append({"type": "agent_state_unrecognized", "agent_id": agent_id})
    except Exception as e:
        signals.append({"type": "agent_inventory_unavailable", "detail": str(e)[:180]})
    evidence = {"at": now, "cases_total": len(cases), "cases_unreported_overdue": overdue,
                "running_agents_checked": agents, "signals": signals,
                "finding_count": sum(findings.values()),
                "assessment": "requires_investigation_not_a_guilt_verdict"}
    atomic(root / "health.json", evidence)
    incident = root / "incident.json"
    if signals:
        atomic(incident, evidence)
    elif incident.exists():
        os.replace(incident, root / f"cleared-{now}.json")
    print(json.dumps(evidence))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["check", "report"])
    p.add_argument("--case", default="")
    p.add_argument("--verdict", choices=["verified", "not_assigned",
                                           "finding", "inconclusive", "verified_fixed"])
    p.add_argument("--evidence", default="")
    p.add_argument("--details", default="")
    p.add_argument("--correction", action="store_true",
                   help="file a superseding verdict (Act 17); requires --supersedes, "
                        "--why_stronger, --reason_code, --auditor")
    p.add_argument("--confirm", action="store_true",
                   help="second procedural pass confirming a pending correction (Act 17 §2.4)")
    p.add_argument("--supersedes", default="")
    p.add_argument("--why_stronger", default="")
    p.add_argument("--reason_code", default="")
    p.add_argument("--auditor", default="")
    args = p.parse_args()
    if args.action == "report":
        if args.correction and args.confirm:
            raise ValueError("--correction and --confirm are mutually exclusive")
        if args.confirm:
            if not args.case:
                raise ValueError("case is required")
        elif not args.case or not args.verdict:
            raise ValueError("case and verdict are required")
        report(args)
    else:
        check(args)


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Audit accountability failed: {err}", file=sys.stderr)
        sys.exit(1)

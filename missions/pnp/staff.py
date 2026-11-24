"""Executive-invoked baseline staffing of every lease and focused specialists.

Not an autonomous agent scheduler. The Executive supplies the mathematical
approaches and invokes this helper. Existing workers are adopted by exact
workspace, not mutable titles; uncertainty never authorizes duplicate starts.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from . import assignment, config, focus, gitctl, state, support


def antonina(*args):
    result = subprocess.run(["antonina", "agent", *args], capture_output=True,
                            text=True, timeout=30, check=True)
    return result.stdout.strip()


def roster():
    rows = {}
    page = 1
    while True:
        data = json.loads(antonina("list", "--page", str(page), "--limit", "100", "--json"))
        agents = data.get("agents")
        if not isinstance(agents, list) or data.get("unreadable"):
            raise ValueError("agent roster unavailable")
        for agent in agents:
            if not isinstance(agent.get("id"), str) or agent["id"] in rows:
                raise ValueError("inconsistent agent roster")
            rows[agent["id"]] = agent
        if len(agents) < 100:
            return list(rows.values())
        page += 1


def prompt(rec, approach, general=False):
    return (
        "Work on the exact current P vs NP assignment below, using the independent "
        "workspace already prepared for you. Pursue this distinct mathematical "
        "approach; communicate useful sublemmas and artifacts to the other researchers "
        "on this same gap. No unrelated gap acquisition, no direct desk or GitHub "
        "mutation, no agent launches. Use the local managed compiler and guard from "
        "your bound cwd. Use the checked proof corpus where applicable. Preserve "
        "work when the lease ends. When a complete exact proof exists, immediately "
        "invoke python3 /var/lib/lubko/wd/viche/missions/pnp/cli.py submit GAP FILE "
        "with actual gap and file; never wait for an extra review. If the guard "
        "says publication owns the candidate or stop, do not compete with it.\n"
        f"Gap: {rec['gap_id']}\nStatement: {rec['statement']}\n"
        f"Imports: {json.dumps(rec.get('imports', []))}\n"
        f"Context: {rec.get('context') or ''}\n"
        "Share substantial findings immediately from your bound cwd using "
        "PYTHONPATH=/var/lib/lubko/wd/viche python3 -m missions.pnp.support finding "
        "--evidence 'artifact or checked lemma' --message 'specific result, blocker or next route'. "
        "Read research_findings in the guard output; use peer insights rather than duplicate work. "
        "Evaluators rely on your actual findings and logs. "
        + ("You are the persistent general researcher for this lease, whether focused or not. "
           "Understand the exact statement, study existing proofs, pursue promising routes, "
           "test assumptions and share concrete results. Continue productive mathematical work "
           "and submit a complete proof directly. A focus change does not end your assignment. "
           if general else "You are a focused specialist. If focus moves, preserve your findings "
           "and finish cooperatively; the general researcher remains. ")
        + f"Assigned approach: {approach}"
    )


def current_matches(rec, general=False):
    latest = state.load(rec["gap_id"])
    if not support.active(latest) or latest.get("queued_lease") or focus.key(latest) != focus.key(rec):
        return False
    if general:
        return True
    selected = focus.current()
    return selected is not None and focus.key(selected) == focus.key(rec)


def dispatch(gap, plans):
    rec = state.load(gap)
    if not support.active(rec) or rec.get("queued_lease"):
        raise ValueError("not a live research lease")
    if not all(label == "general" or current_matches(rec) for label, _ in plans):
        raise ValueError("only the general researcher may be dispatched on a nonfocused lease")
    if not plans or len({label for label, _ in plans}) != len(plans):
        raise ValueError("distinct nonempty approach labels required")
    for label, approach in plans:
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,48}", label) or not approach.strip():
            raise ValueError("invalid worker label or empty approach")
    os.makedirs(config.STATE_ROOT, exist_ok=True)
    fd = os.open(os.path.join(config.STATE_ROOT, "staff.lock"), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        agents = roster()
        base = None
        results = []
        for label, approach in plans:
            if not current_matches(rec, label == "general"):
                break
            try:
                # A single upstream fetch per batch, rather than per worker.
                path = Path(assignment.prepare(gap, checkout=False, worker=label)["cwd"])
                existing = [a for a in agents if a.get("cwd") and
                            Path(a["cwd"]).resolve() == path.resolve()]
                running = [a for a in existing if a.get("state") == "running"]
                if running:
                    results.append({"worker": label, "status": "already running", "id": running[0]["id"]})
                    continue
                if existing and any(a.get("state") not in ("idle", "clearexit", "stopped", "killed", "failed") for a in existing):
                    raise ValueError("uncertain worker state")
                if not (path / ".git").exists() and base is None:
                    base = gitctl.ensure_mirror()
                assignment.prepare(gap, worker=label, base=base)
                if not current_matches(rec, label == "general"):
                    break
                reusable = next((a for a in existing if a.get("state") in ("idle", "clearexit")), None)
                if reusable:
                    agent_id = reusable["id"]
                else:
                    agent_id = antonina("new", "--cwd", str(path), "--title",
                                        f"Viche P vs NP research: {gap} {label}")
                    if not re.fullmatch(r"[a-zA-Z0-9_-]+", agent_id):
                        raise ValueError("unreadable new agent id")
                if not current_matches(rec, label == "general"):
                    break
                answer = json.loads(antonina("run", "--id", agent_id, "--cwd", str(path),
                                            "--prompt", prompt(rec, approach, label == "general"), "--detach", "--json"))
                if answer.get("state") != "running":
                    raise ValueError("agent launch not confirmed")
                results.append({"worker": label, "status": "started", "id": agent_id})
            except (OSError, ValueError, subprocess.SubprocessError, gitctl.GitError) as exc:
                results.append({"worker": label, "status": "deferred", "detail": str(exc)[:300]})
        return results
    finally:
        os.close(fd)


GENERAL_APPROACH = ("Develop a broad mathematical understanding of the exact problem. "
                    "Inspect previous artifacts, checked lemmas and nearby reductions; "
                    "derive or test promising proof routes, including constructive witnesses "
                    "or counterexamples when appropriate. Share specific progress, remaining "
                    "obstacles and viable next steps with all researchers and evaluators.")


def baseline():
    out = []
    for gap in state.all_gaps():
        rec = state.load(gap)
        if not support.active(rec) or rec.get("queued_lease"):
            continue
        try:
            out.extend({"gap": gap, **row} for row in dispatch(gap, [("general", GENERAL_APPROACH)]))
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            out.append({"gap":gap,"status":"deferred","detail":str(exc)[:300]})
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("gap", nargs="?")
    p.add_argument("--baseline", action="store_true", help="staff one general researcher on every live lease")
    p.add_argument("--worker", action="append", metavar="LABEL=APPROACH")
    args = p.parse_args()
    try:
        if args.baseline:
            if args.gap or args.worker:
                raise ValueError("use --baseline alone")
            print(json.dumps(baseline(), indent=2))
            return
        if not args.gap or not args.worker:
            raise ValueError("specify GAP and --worker, or --baseline")
        plans = [tuple(item.split("=", 1)) for item in args.worker]
        if any(len(plan) != 2 for plan in plans):
            raise ValueError("use LABEL=APPROACH")
        print(json.dumps(dispatch(args.gap, plans), indent=2))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        p.error(str(exc))


if __name__ == "__main__":
    main()

"""Execute the Executive's standing staffing orders, not new allocation choices."""
import hashlib
import json
from pathlib import Path
import subprocess
import time

from . import assignment, config, focus, staff, state, status, support

SUPPORT = {
    "knowledge": "Find checked equivalents, opposite conclusions, stronger reusable proofs and admissible imports. Send verified applicability and concrete proof fragments, not just scores.",
    "methods": "Independently attack the focused claim. Derive a concrete sublemma, construction, refutation or identify a precise false premise. Use full-function checks; never duplicate an existing search.",
    "flow": "Investigate actual idle time, duplicated computation, correction and publication delay. Deliver concrete improvements that increase checked contributions; do not monitor tool calls.",
    "portfolio": "Use portfolio inspect and compare all live leases and eligible published-proof corrections using their researchers' findings and actual artifacts. Make the evidence-based switch decision directly with portfolio switch if justified.",
    "lease-evaluation": "Use portfolio inspect. Investigate actual mathematical blockers and alternatives. Decide justified releases through portfolio release; never release because of vacancies, age alone or temporary compiler contention.",
}
FRONTS = (
    ("integrator", "Identify the precise missing inference, split the Lean proof into independent lemmas, reuse peer sources and checked upstream proofs, assemble and submit the exact theorem as soon as complete."),
    ("alternative", "Pursue a genuinely independent construction or refutation using the exact statement. First inspect existing peer findings and checked sources; use reusable finite search when applicable."),
)


def live():
    return [r for g in state.all_gaps() if (r := state.load(g)) and
            support.active(r) and not r.get("queued_lease")]


def signature(role, records, selected):
    scope = records if role in support.DECISION_ROLES else (
        [selected] if selected and support.active(selected) else records)
    # Only changes in assignments or primary mathematical evidence warrant a
    # completed support pass. Its own advice does not trigger itself.
    data = [(support.attempt(r), sorted([f["id"] for f in support.findings(r)] + [a["id"] for a in support.read(r) if a["kind"] == "checked"]))
            for r in scope]
    if role == "portfolio":
        for gap in state.all_gaps():
            rec = state.load(gap)
            if focus.correction(rec) and rec.get("lease") and isinstance(rec.get("statement"), str):
                data.append((support.attempt(rec), ["correction", rec.get("commit_sha") or "", rec.get("local_check_status") or "", rec.get("external_verdict") or ""]))
    return hashlib.sha256(json.dumps(sorted(data)).encode()).hexdigest()


def support_pass(role, records, selected, agents):
    path = Path(config.STATE_ROOT, "swarm", "standing-support", role)
    path.mkdir(parents=True, exist_ok=True)
    receipt = path / "dispatch.json"
    sig = signature(role, records, selected)
    existing = [a for a in agents if role in support.roles(a)]
    if any(a.get("state") == "running" for a in existing):
        return {"role": role, "status": "already running"}
    if any(a.get("state") not in staff._REUSABLE for a in existing):
        return {"role": role, "status": "uncertain"}
    try:
        old = json.loads(receipt.read_text())
    except (OSError, ValueError):
        old = {}
    owner = next((a for a in existing if a.get("id") == old.get("agent")), None)
    if old.get("signature") == sig and old.get("launched") and owner and owner.get("state") in ("clearexit", "idle"):
        if not old.get("completed"):
            old["completed"] = True
            state.atomic_write(str(receipt), json.dumps(old) + "\n")
        return {"role": role, "status": "completed same evidence"}
    if old.get("signature") == sig and time.time() - old.get("at", 0) < 120:
        return {"role": role, "status": "retry deferred"}
    reusable = next((a for a in existing if a.get("state") in ("idle", "clearexit")
                     and a.get("cwd") == str(path)), None)
    aid = reusable["id"] if reusable else staff.antonina(
        "new", "--cwd", str(path), "--title", support.PREFIX + " " + role)
    # Save before launch; a timeout is not permission to create a duplicate.
    state.atomic_write(str(receipt), json.dumps(
        {"signature": sig, "agent": aid, "at": time.time()}) + "\n")
    prompt = (
        "You are performing a bounded Executive-delegated research support pass. "
        "Read /var/lib/lubko/wd/viche/missions/pnp/mandate.md. "
        "Use PYTHONPATH=/var/lib/lubko/wd/viche python3 -m missions.pnp.support targets "
        "and python3 -m missions.pnp.portfolio inspect. "
        "Deliver substantive evidence directly via support advise (or portfolio decisions). "
        "Do not launch/steer agents, acquire leases, edit other workspaces, or open PRs. "
        "Finish when no further useful distinct work remains. "
        "Do not repeat the previous pass without a material reason.\n" + SUPPORT[role])
    answer = json.loads(staff.antonina("run", "--id", aid, "--cwd", str(path),
                                     "--prompt", prompt, "--detach", "--json"))
    if answer.get("state") != "running":
        raise ValueError("support launch not confirmed")
    state.atomic_write(str(receipt), json.dumps(
        {"signature": sig, "agent": aid, "at": time.time(), "launched": True}) + "\n")
    return {"role": role, "status": "started", "id": aid}


def required_support(records):
    return (list(support.ROLES) + ["lease-evaluation"] +
            (["portfolio"] if len(records) > 1 else [])) if records else []


def completed_roles(records, selected):
    done = set()
    for role in required_support(records):
        try:
            receipt = json.loads(Path(config.STATE_ROOT, "swarm", "standing-support",
                                      role, "dispatch.json").read_text())
            if receipt.get("completed") and receipt.get("signature") == signature(role, records, selected):
                done.add(role)
        except (OSError, ValueError, AttributeError):
            pass
    return done


def focus_plans(selected, agents):
    if not selected or not focus.eligible(selected):
        return []
    labels = []
    for a in agents:
        if a.get("state") != "running" or not a.get("cwd"):
            continue
        cwd = Path(a["cwd"])
        if assignment.binding(cwd) == focus.key(selected) and not assignment.general(cwd):
            labels.append(assignment.worker_label(cwd) or "")
    if focus.correction(selected):
        return [] if labels else [("correction", "Repair exact published source using checker diagnostics.")]
    has_integrator = any("integrat" in label.lower() for label in labels)
    has_alternative = any("integrat" not in label.lower() for label in labels)
    return [p for p in FRONTS if not (has_integrator if p[0]=="integrator" else has_alternative)]


def already_covered(records, selected, observed):
    # The cheap running-only snapshot is sufficient to prove coverage.
    # Historical registry pagination is necessary only when there is a vacancy.
    general = set()
    for a in observed["agents"]:
        if not a.get("cwd"):
            continue
        cwd = Path(a["cwd"])
        bound = assignment.binding(cwd)
        if assignment.general(cwd):
            general.add(bound)
    if any(focus.key(r) not in general for r in records):
        return False
    if focus_plans(selected, observed["agents"]):
        return False
    roles = {role for a in observed["support"] for role in a["roles"]}
    return set(required_support(records)) <= roles | completed_roles(records, selected)


def execute():
    records = live()
    selected = focus.current()
    if not records and not selected:
        return {"status": "no research"}
    observed = status.workers()
    if observed["coverage"] != "complete":
        return {"status": "worker coverage unknown"}
    if already_covered(records, selected, observed):
        return {"status": "covered"}
    with staff.staffing_lock():
        # One registry snapshot, while the same lock excludes model-invoked
        # staff batches. Baseline is prescribed for every live lease.
        agents = staff.roster()
        result = {"baseline": staff.baseline(agents, locked=True), "focus": [], "support": []}
        selected = focus.current()
        plans = focus_plans(selected, agents)
        if plans:
            try:
                result["focus"] = staff.dispatch(selected["gap_id"], plans, agents, locked=True)
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                result["focus"] = [{"status": "deferred", "detail": str(exc)[:300]}]
        records = live()
        for role in required_support(records):
            try:
                result["support"].append(support_pass(role, records, selected, agents))
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                result["support"].append({"role": role, "status": "deferred", "detail": str(exc)[:300]})
        return result


if __name__ == "__main__":
    try:
        print(json.dumps(execute(), ensure_ascii=False))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "deferred", "detail": str(exc)[:300]}))

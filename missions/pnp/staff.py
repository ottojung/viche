"""Executive-invoked baseline staffing of every lease and focused specialists.

Not an autonomous agent scheduler. The Executive supplies the mathematical
approaches and invokes this helper. Existing workers are adopted by exact
workspace, not mutable titles; uncertainty never authorizes duplicate starts.
"""
import argparse
import concurrent.futures
import contextlib
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from . import assignment, brief, config, focus, gitctl, state, support

# A full baseline used to paginate the whole (>2600 agent) registry once per
# live gap. Fetch pages in bounded concurrent waves and let baseline reuse a
# single snapshot. These are performance bounds, not policy limits: a page
# shape we cannot validate still fails closed.
_ROSTER_PAGE_SIZE = 100
_ROSTER_WAVE = 8
_MAX_ROSTER_PAGES = 4096                       # guard against a corrupt cursor
_REUSABLE = frozenset(("idle", "clearexit", "stopped", "killed", "failed"))


def antonina(*args):
    # All deterministic Executive dispatch paths use this wire. Inject exactly
    # one short role playbook at the actual invocation, including restarts.
    args=list(args);did=None
    if args[:1]==["run"] and all(x in args for x in ("--id","--cwd","--prompt")):
        from .research import playbook, adoption
        path=Path(args[args.index("--cwd")+1])
        label=assignment.worker_label(path)
        role=playbook.role_for(label,label=="general") if label else None
        if path.parent.name in ("standing-support","independent") and path.name in playbook.ROLES:
            role=path.name
        if role:
            i=args.index("--prompt")+1
            if not args[i].startswith("YOUR ROLE:"):
                args[i]=playbook.guide(role)+"\n\n"+args[i]
            did=adoption.planned(args[args.index("--id")+1],path,role,args[i])
    result = subprocess.run(["antonina", "agent", *args], capture_output=True,
                            text=True, timeout=30, check=True)
    if did:
        try:
            if json.loads(result.stdout).get("state")=="running":adoption.confirmed(did)
        except (ValueError,AttributeError):pass
    return result.stdout.strip()


def _roster_page(page):
    data = json.loads(antonina("list", "--page", str(page),
                               "--limit", str(_ROSTER_PAGE_SIZE), "--json"))
    agents = data.get("agents")
    if not isinstance(agents, list) or data.get("unreadable"):
        raise ValueError("agent roster unavailable")
    return agents


def roster():
    """Read every agent once, tolerating insertions during pagination.

    Antonina's --page/--limit windows are taken against a live registry. The
    Town adds agents while we page, so the same id can reappear on the next
    page when a new agent shifts the offset window. Only additions happen on
    these workspaces (agents are retired by state change, never deleted), so
    a repeated id is a harmless duplicate, never a *skipped* agent: adoption
    is by exact cwd and a duplicated row still yields one candidate for that
    workspace. We therefore dedupe across pages instead of raising a spurious
    "inconsistent agent roster", while a duplicate *within one page* remains
    corruption and fails closed. Unreadable pages and an unbounded cursor also
    fail closed rather than being mistaken for an empty registry.
    """
    rows = {}
    page = 1
    while page <= _MAX_ROSTER_PAGES:
        wanted = list(range(page, min(page + _ROSTER_WAVE, _MAX_ROSTER_PAGES + 1)))
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(wanted)) as pool:
            pages = dict(zip(wanted, pool.map(_roster_page, wanted)))
        # A short page is the end of the registry. Pages beyond it were part
        # of the same concurrent wave and are ignored (they can only contain
        # agents added after the snapshot boundary).
        short = next((p for p in wanted if len(pages[p]) < _ROSTER_PAGE_SIZE), None)
        for p in wanted:
            if short is not None and p > short:
                break
            seen = set()
            for agent in pages[p]:
                aid = agent.get("id")
                if not isinstance(aid, str) or aid in seen:
                    raise ValueError("inconsistent agent roster")
                seen.add(aid)
                rows.setdefault(aid, agent)  # cross-page repeat = insertion race
        if short is not None:
            return list(rows.values())
        page += len(wanted)
    raise ValueError("agent roster unavailable")


def prompt(rec, approach, general=False, label=None):
    return (
        "Use the injected role playbook and exact assignment below. Work from your bound cwd. "
        "No direct desk/GitHub mutation, unrelated claims or agent launches. "
        "Read guard's preflight candidate and peer findings; use an applicable generator, "
        "checked proof or adapter before reinventing it. The full tool inventory is available "
        "through python3 -m missions.pnp.tools when needed, not mandatory at entry. "
        "For finite search use durable CEGIS checkpoints and independently verify witnesses; "
        "UNSAT alone is not a Lean proof. Preserve checked helpers and exact failed inferences. "
        "When an exact proof exists, immediately invoke python3 /var/lib/lubko/wd/viche/missions/pnp/cli.py "
        "submit GAP FILE with the actual gap and file. No extra approval. If guard says "
        "publication owns the candidate or stop, preserve your work and do not compete.\n"
        f"Gap: {rec['gap_id']}\nStatement: {rec['statement']}\n"
        f"Imports: {json.dumps(rec.get('imports', []))}\n"
        f"Context: {rec.get('context') or ''}\n"
        f"Desk proof sketch / cut ancestry / failed approaches (advisory): {json.dumps(brief.read(rec),ensure_ascii=False)[:6000]}\n"
        "Start by reading the exact supplied sketch, checked reduction sources, and solved siblings "
        "with the current pinned upstream checkout. Do not redo known mathematics. "
        "For shard assignments work only on the assigned range; do not infer a global refutation. "
        "Use python3 -m missions.pnp.brief from the bound workspace for the full packet.\n"
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
        + (f"CORRECTION: existing PR {rec.get('pr_url')}; inspect the exact published proof "
           f"and local diagnostic {rec.get('local_check_log', '')[-2000:]}. Correct the same "
           "PR through submit; no new PR. Use the saved candidate in the gap state directory. "
           if focus.correction(rec) else "")
        + f"Assigned approach: {approach}"
    )


def current_matches(rec, general=False):
    latest = state.load(rec["gap_id"])
    if not focus.eligible(latest) or latest.get("queued_lease") or focus.key(latest) != focus.key(rec):
        return False
    if general:
        return support.active(latest)
    selected = focus.current()
    return selected is not None and focus.key(selected) == focus.key(rec)


@contextlib.contextmanager
def staffing_lock():
    os.makedirs(config.STATE_ROOT, exist_ok=True)
    fd = os.open(os.path.join(config.STATE_ROOT, "staff.lock"), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)


def dispatch(gap, plans, agents=None, locked=False):
    """adopt by exact cwd; ``agents`` may be a baseline's single snapshot."""
    if Path(config.STATE_ROOT).resolve() == Path("/var/lib/lubko/wd/viche-state/pnp"):
        raise RuntimeError("standing controller owns live dispatch")
    rec = state.load(gap)
    if not focus.eligible(rec) or rec.get("queued_lease"):
        raise ValueError("not a live research or correction assignment")
    if not all(current_matches(rec, label == "general") for label, _ in plans):
        raise ValueError("only the general researcher may be dispatched on a nonfocused lease")
    if not plans or len({label for label, _ in plans}) != len(plans):
        raise ValueError("distinct nonempty approach labels required")
    for label, approach in plans:
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,48}", label) or not approach.strip():
            raise ValueError("invalid worker label or empty approach")
    with (contextlib.nullcontext() if locked else staffing_lock()):
        # A direct dispatch still reads the roster itself; baseline passes a
        # snapshot it already fetched so N live gaps cost one pagination, not N.
        if agents is None:
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
                if len(running) > 1:
                    # Two live workers on one bound workspace are already a
                    # duplicate: refuse rather than pick one blindly or add a
                    # third. This is the fail-closed side of "never duplicate".
                    raise ValueError("duplicate worker on workspace")
                if running:
                    results.append({"worker": label, "status": "already running", "id": running[0]["id"]})
                    continue
                if existing and any(a.get("state") not in _REUSABLE for a in existing):
                    raise ValueError("uncertain worker state")
                if not (path / ".git").exists() and base is None:
                    # Compositional workers must be able to assemble checked
                    # lemmas on the same base. Do not reset existing worktrees.
                    general_path = (Path(state.gap_dir(gap)) / "attempts" /
                                    assignment.attempt_id(rec["lease"]) / "workers/general/path")
                    if label.startswith("ob-"):
                        from .research import knowledge
                        from contextlib import closing
                        with closing(knowledge.db()) as c:
                            base=knowledge.get(c,label[3:])["base"]
                    elif label != "general" and (general_path / ".git").exists():
                        base = subprocess.check_output(["git","-C",str(general_path),"rev-parse","HEAD"],
                                                       text=True,timeout=5).strip()
                    else:
                        base = gitctl.ensure_mirror()
                chosen_base=base
                if label.startswith("ob-"):
                    from .research import knowledge
                    from contextlib import closing
                    with closing(knowledge.db()) as c:
                        chosen_base=knowledge.get(c,label[3:])["base"]
                assignment.prepare(gap, worker=label, base=chosen_base)
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
                                            "--prompt", prompt(rec, approach, label == "general", label), "--detach", "--json"))
                if answer.get("state") != "running":
                    raise ValueError("agent launch not confirmed")
                results.append({"worker": label, "status": "started", "id": agent_id})
                if label.startswith("ob-"):
                    try:
                        from .research import knowledge
                        from contextlib import closing
                        import time
                        with closing(knowledge.db()) as c,c:
                            c.execute("INSERT OR REPLACE INTO assignment VALUES(?,?,?,?)",
                                      (label[3:],support.attempt(rec),label,time.time()))
                    except Exception:pass

            except (OSError, ValueError, subprocess.SubprocessError, gitctl.GitError) as exc:
                results.append({"worker": label, "status": "deferred", "detail": str(exc)[:300]})
        # A staffing/replenishment decision is routine, not a Git delivery.
        # The existing per-gap append-only event log is the durable record:
        # timestamped, with the agent id receipt and the reason/approach.
        # Adoptions of an already-running worker are not new decisions and add
        # no entry, so idle passes do not amplify the trail.
        started = {row["worker"]: row["id"] for row in results
                   if row.get("status") == "started"}
        if started:
            workers = []
            for label, approach in plans:
                if label in started:
                    workers.append({"label": label, "agent": started[label],
                                    "approach": approach})
            # Best effort: the worker is already dispatched. An audit append
            # that fails must not surface as a failed dispatch (which could be
            # replayed into a duplicate worker) or gate liveness.
            try:
                state.event(gap, "staffing", {"workers": workers, "attempt": support.attempt(rec)})
            except Exception as exc:
                print("staffing event log unavailable: %s" % exc, file=sys.stderr)
        return results


GENERAL_APPROACH = ("Develop a broad mathematical understanding of the exact problem. "
                    "Inspect previous artifacts, checked lemmas and nearby reductions; "
                    "derive or test promising proof routes, including constructive witnesses "
                    "or counterexamples when appropriate. Share specific progress, remaining "
                    "obstacles and viable next steps with all researchers and evaluators.")


def baseline(agents=None, locked=False):
    if Path(config.STATE_ROOT).resolve() == Path("/var/lib/lubko/wd/viche-state/pnp"):
        raise RuntimeError("standing controller owns live dispatch")
    if not locked:
        with staffing_lock():
            return baseline(agents, locked=True)
    live = []
    for gap in state.all_gaps():
        rec = state.load(gap)
        if support.active(rec) and not rec.get("queued_lease"):
            live.append(gap)
    if not live:
        return []
    # One bounded, race-tolerant pagination for the whole pass. A direct
    # dispatch() still fetches its own roster, so its contract is unchanged;
    # reusing the snapshot here is safe because each live gap has a distinct
    # bound workspace and cannot collide with another gap's dispatch.
    try:
        if agents is None:
            agents = roster()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return [{"gap": g, "status": "deferred", "detail": str(exc)[:300]} for g in live]
    out = []
    for gap in live:
        try:
            out.extend({"gap": gap, **row} for row in
                       dispatch(gap, [("general", GENERAL_APPROACH)], agents=agents, locked=True))
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            out.append({"gap": gap, "status": "deferred", "detail": str(exc)[:300]})
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("gap", nargs="?")
    p.add_argument("--baseline", action="store_true", help="staff one general researcher on every live lease")
    p.add_argument("--worker", action="append", metavar="LABEL=APPROACH")
    args = p.parse_args()
    # Interactive legacy entry points must not race the standing controller.
    # Hermetic callers of the old helpers remain supported for regression tests.
    if Path(config.STATE_ROOT).resolve() == Path("/var/lib/lubko/wd/viche-state/pnp"):
        from .staffing import store
        if args.worker:
            p.error("declare exact-attempt extras in staffing/policy.json; controller owns launches")
        print(json.dumps(store.read_health(),indent=2))
        return
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

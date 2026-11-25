"""Live research capability discovery. Advisory, never an admission gate."""
import argparse
import hashlib
import importlib.util
import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PREFIX = "PYTHONPATH=/var/lib/lubko/wd/viche python3 -m missions.pnp."


def present(path):
    return (ROOT / path).is_file()


def inventory():
    # Only advertise capabilities whose implementation exists at this revision.
    rows = []
    def add(path, use, purpose, when):
        if present(path):
            rows.append({"command": PREFIX + use, "purpose": purpose, "when": when})
    add("lbcert/lbremote.py", "lbcert.lbremote STATEMENT.txt PEqualNP.Outside.L_meta_N OUT.lean",
        "lb_cert lower-bound certificate built on marceline-dev (~20 s); exit 0 written, 3 bound false, 4 too big",
        "Statement `∀ t, HasCircuitSize n f t → K ≤ t`, `¬HasCircuitSize n f S` or its `¬ (...)` twin. "
        "Usually already done: see PNP_STATE_ROOT/lbcert/cands/GAP.status; the allocator fast lane submits it.")
    add("lbcert/sibremote.py", "lbcert.sibremote STATEMENT.txt PEqualNP.Outside.L_meta_N OUT.lean --imports PEqualNP.Defs",
        "Prove the step with a merged same-shape sibling's proof, compiled on marceline-dev; exit 0 written, 5 none",
        "Any step. Retried automatically every 5 min while held; run it after a new sibling merges.")
    add("brief.py", "brief", "Exact leased statement, original sketch, parent cuts and siblings",
        "At entry; before independent mathematics.")
    add("proofs/__main__.py", "proofs find [QUERY]", "Retrieve checked analogous proofs and structural hints",
        "Before proving a lemma from scratch; inspect source, not just scores.")
    add("proofs/__main__.py", "proofs source MODULE", "Retrieve checked source text",
        "For a plausible related proof; verify hypotheses and permitted imports.")
    add("proofs/circuit.py", "proofs circuit --output NEW.lean", "Validate prescribed finite circuit and emit candidate",
        "Explicit circuit or finite truth-table claim.")
    add("proofs/synthesis.py", "proofs synthesize --output NEW.lean", "Generate small graph-edge monotone circuits",
        "Existential circuit construction; exact star cover when integrated.")
    add("proofs/search.py", "proofs search SPEC.json --seconds 60 --checkpoint ROWS.json",
        "Bounded SAT/CEGIS with full independent witness checks",
        "Finite gate-budget or truth-table problem; UNSAT is not a Lean refutation.")
    add("proofs/rows.py", "proofs rows SPEC.json WITNESS.json",
        "Independent bitset verification of multi-output specified rows and disjunctive constraints",
        "Large-input finite witness with prescribed rows; full correctness requires a proved row reduction.")
    add("proofs/rows.py", "proofs row-search SPEC.json --seconds 60 --checkpoint ROWS.json",
        "Bounded SAT/CEGIS for 64 inputs, 96 gates, multiple outputs and existential row groups",
        "Specified finite positive/negative rows; UNSAT is encoding evidence, not a Lean verdict.")
    add("proofs/bank.py", "proofs bank GRAPH.json --output SPEC.json",
        "Exact monotone bipartite bank constraints using maximal independent sets",
        "Neighborhood bank on incident pairs and independent sets, optional OR output and masked edge.")
    add("adapter/__main__.py", "adapter detect --limit 8 --emit-candidates",
        "Detect candidate adaptations from checked corpus",
        "Related theorem or stronger bound; verify and compile resulting candidates.")
    add("adapter/__main__.py", "adapter closure SOURCE.lean --target DECL --emit",
        "Extract candidate declaration dependency closure",
        "Large reusable mathematical proof core; inspect scope and dependencies.")
    add("adapter/__main__.py", "adapter adapt SOURCE.lean --output NEW.lean",
        "Adapt a related checked proof to the bound statement",
        "Proof family with small changes; exact statement and Lean verification required.")
    add("metrics.py", "metrics", "Observed acquisition, submission and acceptance funnel",
        "Measure bottlenecks and credited outcomes; lease-slot hours are not compute hours.")
    add("bench/__main__.py", "bench --json --no-results", "Retrospective generator benchmark",
        "Engineering improvement to reusable proof production, not proof of a live claim.")
    add("proofs/fragments.py", "proofs fragments --all-attempts", "List durable checked/unverified source fragments",
        "Before rebuilding a helper; read status, check in the pinned context.")
    add("proofs/fragments.py", "proofs share FILE --message RESULT", "Snapshot reusable helper for peers",
        "When a useful intermediate Lean result exists; don't wait for full proof.")
    add("preflight.py", "preflight", "Read automatic cheap generator results for this attempt",
        "At entry or when guard reports a candidate; review and submit exact proof.")
    add("compile.py", "compile --light -- lake env lean Scratch.lean",
        "Managed scratch validation; use narrow imports if possible",
        "Small proof iteration, explicit local file.")
    add("compile.py", "compile -- lake build +MODULE", "Managed full build",
        "Check exact completed candidate; avoid duplicate work.")
    add("support.py", "support finding --evidence ARTIFACT --message RESULT",
        "Deliver substantive evidence directly to peers",
        "When a result, false premise or useful reusable route is found.")
    add("cli.py", "cli guard", "Assignment validity, new tool revision and peer evidence",
        "At natural checkpoints, especially after expensive work.")
    add("cli.py", "cli submit GAP FILE", "Queue exact completed proof for publication",
        "Immediately when complete; never wait for an extra review.")
    if present("research/entry.py") and (Path.home()/".local/bin/pnp-research").is_file():
        rows += [
            {"command":"pnp-research start","purpose":"Short role-specific work packet with exact pinned revision, prior findings and open obligations","when":"First command after dispatch; no need to read every tool manual."},
            {"command":"pnp-research guide ROLE","purpose":"Executable detailed examples for your role","when":"Only when you need the next unfamiliar operation."},
            {"command":"pnp-research knowledge find QUERY","purpose":"Cumulative mathematical objects from current and archived leases","when":"Before rediscovering a lemma or failed approach."},
            {"command":"pnp-research obligations ready --current","purpose":"Exact proof dependency graph for your current gap","when":"At decomposition and natural proof checkpoints."},
            {"command":"pnp-research obligations solve NODE BODY --async","purpose":"Durable kernel check of a complete body and checked dependencies","when":"Parallel Lean iteration; collect CHECK_ID later."},
            {"command":"pnp-research certificate --check --output Candidate.lean","purpose":"Generate and asynchronously check exact star-cover Lean certificate using reflection or list permutation","when":"Compatible graph-circuit construction; normal publication checks still apply."},
            {"command":"pnp-research yield","purpose":"Empirical family-level allocation baseline, current graph progress and competition","when":"Portfolio and lease evaluators."},
            {"command":"pnp-research adoption","purpose":"Observed role-prompt delivery and actual agent tool calls","when":"Flow and Executive evaluation; not mathematical success."},
        ]
    if (Path.home()/".local/bin/pnp-remote-check").is_file():
        rows.append({"command":"pnp-remote-check --scratch --async FILE.lean","purpose":"Remote Lean on exact pinned revision","when":"Heavy intermediate checks; use --availability once per checkout and --wait ID for result."})
    return rows


def snapshot():
    rows = inventory()
    # Hash actual relevant source bytes so that updates to existing tools are
    # visible, not just new filenames. Do not hash the whole repository.
    h = hashlib.sha256(json.dumps(rows,sort_keys=True).encode())
    files = [ROOT / "tools.py", ROOT / "compile.py", ROOT / "brief.py",
             ROOT / "preflight.py"]
    for package in ("proofs", "adapter", "bench", "remote", "research"):
        files += sorted((ROOT/package).glob("*.py"))
    for p in files:
        try:
            h.update(str(p.relative_to(ROOT)).encode())
            h.update(p.read_bytes())
        except OSError:
            continue
    return {"revision":h.hexdigest()[:16],"command":PREFIX+"tools",
            "capabilities":rows,
            "sat_dependency_available":importlib.util.find_spec("pysat") is not None,
            "remote_client_installed":(Path.home()/".local/bin/pnp-remote-check").is_file(),
            "remote_build_available":None,
            "note":"Only implemented tools are listed. Heuristic candidates and SAT results are not kernel verdicts. Use --help for exact syntax. Do not delay publication to run irrelevant tools."}


def record(name, cwd=None):
    """Best-effort, idempotent evidence of actual invocation, not a report/gate."""
    from . import assignment, state, support
    if not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", name):
        return
    try:
        bound = assignment.binding(cwd)
        label = assignment.worker_label(cwd)
        if not bound or not label:
            return
        rec = state.load(bound[0])
        if not support.active(rec) or rec["lease"] != bound[1]:
            return
        path = support.directory(rec)/"tool-use"/label/(name+".json")
        # Record the most recent invocation only. No arguments, source,
        # credentials, or unbounded logs.
        state.atomic_write(str(path),json.dumps(
            {"tool":name,"at":time.time(),"attempt":support.attempt(rec)})+"\n")
    except (OSError,ValueError,TypeError,KeyError,AttributeError):
        pass


def usage(rec):
    from . import support
    if not support.active(rec):
        return {}
    result = {}
    try:
        for path in (support.directory(rec)/"tool-use").glob("*/*.json"):
            try:
                obj=json.loads(path.read_text())
                if obj.get("attempt")==support.attempt(rec) and obj.get("tool")==path.stem:
                    result.setdefault(path.parent.name,{})[path.stem]=obj["at"]
            except (OSError,ValueError,TypeError,KeyError,AttributeError):
                continue
    except OSError:
        pass
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--usage",action="store_true",help="Observed invocations on current live assignments")
    args=p.parse_args()
    if args.usage:
        from . import state, support
        rows={}
        for gap in state.all_gaps():
            rec=state.load(gap)
            if support.active(rec):
                rows[gap]=usage(rec)
        print(json.dumps(rows,ensure_ascii=False,indent=2))
    else:
        record("inventory")
        print(json.dumps(snapshot(),ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()

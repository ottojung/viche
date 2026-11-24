"""One source of truth for short, executable role onboarding."""
from pathlib import Path
import json
import os
import subprocess

from .. import assignment, config, state, support
from . import knowledge

P = "PYTHONPATH=/var/lib/lubko/wd/viche python3 -m missions.pnp."
CLI = "pnp-research"
ROLES = {
    "general": ("Own the exact leased theorem; explore promising routes, reuse knowledge and share concrete results.",
        "Use the existing checked corpus before inventing a proof. For compatible graph constructions run pnp-research certificate --output Candidate.lean from the bound workspace. Verify generated candidates through the normal pipeline. Preserve your results when focus changes."),
    "integrator": ("Own the proof dependency graph and eventual exact submission, not another independent full-theorem search.",
        "Request exact missing types, assign through Executive, reuse checked bodies. When the root is complete, assemble --candidate and submit immediately."),
    "specialist": ("Solve the assigned distinct approach or exact obligation, not every part of the theorem.",
        "Publish a checked helper or a precise counterexample; do not duplicate another worker's assigned node."),
    "knowledge": ("Make mathematical results cumulative across attempts.",
        "Search exact sources; promote findings into typed knowledge objects and link their dependencies. A worker report is not a kernel receipt."),
    "methods": ("Find new reusable mathematical arguments applicable to the focus.",
        "Look for reductions, transferable techniques, finite witnesses and false premises. Deliver concrete evidence to the focus workers."),
    "method": ("Prove a reusable theorem for a family, independently of any desk lease.",
        "Use a cached public revision and exact mathematical hypotheses; test multiple applications. Record checked lemmas and failed generalizations."),
    "tool": ("Turn mathematical techniques into reusable proof-generating software.",
        "Use the existing star/circuit search and corpus tools. Benchmark holdout families, independently verify certificates, and check Lean proof output. Work in your own workspace."),
    "flow": ("Eliminate measurable bottlenecks in actual proof production.",
        "Use adoption evidence, queue latency and outcomes; propose concrete corrections rather than reports or extra gates."),
    "portfolio": ("Choose the best focus using actual remaining mathematical work and expected yield.",
        "Compare worker evidence, checked/ready/blocked obligations, compatible techniques and current competition. Use the existing portfolio switch if justified."),
    "lease-evaluation": ("Evaluate whether to continue or release a live lease.",
        "Use concrete remaining dependencies and competing opportunities, not age, temporary compile contention or raw family scores. Preserve reusable knowledge."),
    "transport": ("Keep remote compilation fast, reliable and cache-compatible.",
        "Inspect relay status and real check times; improve throughput without duplicating caches."),
    "adapter": ("Automate application of checked proof families to new statements.",
        "Prefer exact source transformations, validate final statements, and test independent holdouts."),
    "benchmark": ("Measure mathematical throughput, verified outputs and resource use.",
        "Do not substitute invocation counts for checked proof output or credited results."),
}
BOUND = {"general", "integrator", "specialist"}
DECISIONS = {"portfolio", "lease-evaluation"}
METHOD = {"method", "tool", "adapter", "benchmark"}

def role_for(label, general=False):
    return "general" if general else "integrator" if label and "integrat" in label.lower() else "specialist"

def guide(role):
    if role not in ROLES:
        raise ValueError("unknown role")
    purpose, guidance = ROLES[role]
    lines = [f"YOUR ROLE: {role}. {purpose}",
             "FIRST: run ~/.local/bin/pnp-research start --role " + role +
             " (a small current work packet, not a documentation reading task).",
             guidance]
    if role in BOUND:
        lines += [
          "In your workspace, pnp-research obligations ready --current shows open dependencies; obligations show ID gives the exact type. Request with obligations request --statement TYPE --requires ID; solve with obligations solve ID BODY --async, collect with obligations collect ID. BODY is a Lean term beginning with by.",
          "Use pnp-remote-check --scratch --async FILE.lean for experimental Lean; pnp-remote-check --wait ID retrieves the result. Use managed local Lean if remote unavailable. Do not build the same file twice.",
          "Use pnp-research knowledge find QUERY; knowledge show ID retrieves artifacts. Share findings through the existing support channel. Complete exact proof: use the normal submit command immediately."
        ]
    elif role in METHOD:
        lines += [
          "Use pnp-research obligations request --base SHA --family FAMILY --provenance SOURCE --statement TYPE; obligations solve ID BODY --method --async; obligations collect ID. The work packet supplies an exact public base. No desk lease is needed.",
          "Run pnp-research knowledge find QUERY; store exact reusable objects with knowledge add. Use pnp-research certificate GRAPH.json --output Candidate.lean for a Lean-rendered graph-circuit certificate; star GRAPH.json returns its computational witness."
        ]
    elif role in DECISIONS:
        lines += ["Use pnp-research yield (empirical baseline; not calibrated) and " + P + "portfolio inspect. Read current proof artifacts before deciding."]
    elif role in {"knowledge","methods"}:
        lines += ["Use pnp-research knowledge find QUERY and knowledge show ID; knowledge add KIND --family FAMILY --statement TEXT --provenance SOURCE --file FILE. Deliver actionable evidence via support advise."]
    elif role in {"flow","transport"}:
        lines += ["Use pnp-research adoption; marceline-request status; inspect actual outcomes and timings, not merely reports."]
    lines += ["Detailed examples on demand: pnp-research guide " + role + ". No separate onboarding gate."]
    return "\n".join(lines)

def pinned_base(cwd):
    w = assignment.workspace(cwd)
    if w:
        path = w[1]
        try:
            return subprocess.check_output(["git","-C",str(path),"rev-parse","HEAD"],text=True,timeout=3).strip()
        except (OSError,subprocess.SubprocessError):return None
    from .. import gitctl
    try:
        return subprocess.check_output(["git","--git-dir="+gitctl.MIRROR,"rev-parse","refs/remotes/upstream/main"],text=True,timeout=3).strip()
    except (OSError,subprocess.SubprocessError):return None

def compatible_public_base(latest):
    from .. import gitctl
    try:
        raw=subprocess.check_output([str(Path.home()/".local/bin/marceline-request"),"status"],text=True,timeout=10)
        status=json.loads(raw)
        if status.get("age_seconds") is None or status["age_seconds"]>180:return latest
        cached=set((status.get("capabilities") or {}).get("lean_bases",[]))
        recent=subprocess.check_output(["git","--git-dir="+gitctl.MIRROR,"rev-list","--first-parent","--max-count=220","refs/remotes/upstream/main"],
                                       text=True,timeout=5).splitlines()
        return next((b for b in recent if b in cached),latest)
    except (OSError,ValueError,subprocess.SubprocessError):return latest

def details(role):
    text=guide(role)
    if role in BOUND:
        return text+"""
EXACT WORKFLOW (run from the bound workspace):
  PYTHONPATH=/var/lib/lubko/wd/viche python3 -m missions.pnp.cli guard
  pnp-research start
  pnp-research knowledge find 'specific mathematical terms'
  pnp-research obligations ready --current
  pnp-research obligations show NODE_ID
  pnp-research obligations request --statement '∀ n : Nat, n + 0 = n' --import Mathlib
  # write a file proof.body containing: by intro n; exact Nat.add_zero n
  pnp-research obligations solve NODE_ID proof.body --async
  # output contains CHECK_ID; keep working, then:
  pnp-research obligations collect CHECK_ID --poll
  # exit 75 means pending, not failure; later collect CHECK_ID (blocking).
  pnp-research obligations assemble ROOT_ID --candidate --output Candidate.lean
  # submit through the ordinary exact-lease command; no extra approval gate.
For a different exact base: obligations fork NODE_ID; use obligations body OLD_ID
--for-node NEW_ID --output proof.body, then recheck each dependency in order.
A ready node is mathematically OPEN; a checked node has an exact kernel receipt.
"""
    if role in METHOD:
        return text+"""
INDEPENDENT METHOD WORKFLOW:
  pnp-research start --role """+role+"""
  pnp-research knowledge find --kind technique
  # BASE is the exact public revision printed in the work packet.
  pnp-research obligations request --base BASE --family graph-circuit \
    --provenance 'exact general Boolean identity' --import Mathlib \
    --statement '∀ a b : Bool, a && b = b && a'
  # proof.body: by intro a b; exact Bool.and_comm a b
  pnp-research obligations solve NODE_ID proof.body --method --async
  pnp-research obligations collect CHECK_ID
  pnp-research certificate GRAPH.json --output Candidate.lean
Keep reusable lemmas and counterexamples in the graph, not only in your transcript.
"""
    if role in {"knowledge","methods"}:
        return text+"""
  pnp-research knowledge find 'obstruction cross tree'
  pnp-research knowledge show OBJECT_ID
  pnp-research knowledge add counterexample --family graph-circuit \
    --statement 'exact failed inference' --detail 'why it fails' \
    --provenance 'source and revision' --file witness.json
  pnp-research knowledge link COUNTEREXAMPLE_ID OBSTRUCTION_ID counterexample_to
Use actual precise evidence, not generic summaries. Link typed objects to the
proof graph; only kernel receipts justify checked status.
"""
    if role in DECISIONS:
        return text+"""
  pnp-research yield
  PYTHONPATH=/var/lib/lubko/wd/viche python3 -m missions.pnp.portfolio inspect
Compare family-level empirical baseline with the actual proof graph and current
competition. A submitted PR is not a credited step. An unresolved obligation
is not proof that the whole theorem is false. Use only the existing allocator
decision mechanism; record your concrete rationale.
"""
    return text+"\nInspect pnp-research adoption and the actual mathematical artifacts.\n"

def guide_main():
    import argparse
    p=argparse.ArgumentParser(description="Detailed role-specific commands")
    p.add_argument("role",choices=sorted(ROLES))
    a=p.parse_args();print(details(a.role));return 0


def packet(role, cwd=None):
    cwd=Path(cwd or Path.cwd()).resolve()
    b=assignment.binding(cwd)
    rec=state.load(b[0]) if b else None
    if not rec or rec.get("lease")!=b[1]:rec=None
    base=pinned_base(cwd)
    latest=base
    if not rec and role in METHOD:base=compatible_public_base(latest)
    out={"role":role,"base":base,"instructions":guide(role)}
    if latest!=base:out["latest_public_base"]=latest
    if rec:
        out["gap"]=rec["gap_id"]
        out["assignment_current"]=support.active(rec)
        out["attempt"]=support.attempt(rec)
        out["family"]=knowledge.family((rec.get("gap_title") or "")+" "+rec.get("statement",""))
        out["cumulative_research"]=knowledge.relevant(rec)
        try:
            from .. import preflight
            report=preflight.read(rec)
            if report and report.get("result")=="candidate":
                out["preflight_candidate"]={"path":report["candidate"],"generator":report.get("generator"),
                                            "sha256":report["sha256"],"kernel_checked":False}
        except (OSError,ValueError,ImportError,KeyError):pass
        label=assignment.worker_label(cwd)
        if label and label.startswith("ob-"):
            out["assigned_obligation"]=label[3:]
        out["next_commands"]=[
            "pnp-research obligations ready --current",
            "pnp-research knowledge find --family "+out["family"],
            "pnp-remote-check --availability",
        ]
    elif role in METHOD:
        out["next_commands"]=["pnp-research knowledge find --kind technique",
            "pnp-research obligations ready --base "+base if base else "pnp-research obligations ready",
            "marceline-request status "+base if base else "marceline-request status"]
        if role=="tool":
            out["next_commands"].insert(0,"pnp-research certificate GRAPH.json --output Candidate.lean")
            out["source_locations"]=["missions/pnp/research/certificate.py","missions/pnp/research/star.py",
                                     "missions/pnp/research/certificate_bench.py","missions/pnp/proofs/"]
        with knowledge.db() as c:
            from . import obligations
            out["open_method_nodes"]=[{"id":x["id"],"family":x["family"],"base":x["base"],"statement":x["statement"][:250]}
                for x in obligations.ready(c) if x["status"]=="ready" and not x["assignments"]][:6]
        c.close()
    elif role in DECISIONS:
        out["next_commands"]=["pnp-research yield",P+"portfolio inspect"]
    else:
        out["next_commands"]=["pnp-research knowledge stats",P+"support targets"]
    return out

def main():
    import argparse
    from . import adoption
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--role",choices=sorted(ROLES))
    p.add_argument("--json",action="store_true")
    a=p.parse_args()
    role=a.role or adoption.current_role() or role_for(assignment.worker_label(),assignment.general())
    data=packet(role)
    if a.json:
        print(json.dumps(data,ensure_ascii=False,indent=2))
    else:
        print("CURRENT WORK PACKET — "+role)
        print("Purpose:",ROLES[role][0])
        for key in ("gap","family","base","latest_public_base","assignment_current","assigned_obligation"):
            if key in data:print(key+":",data[key])
        context=data.get("cumulative_research") or {}
        if context.get("obligations"):
            print("\nExact-gap obligations (show ID for full statement; fork/recheck if base differs):")
            for o in context["obligations"]:
                print(o["id"],"CHECKED" if o.get("verified") else o.get("status","OPEN"),("same-base" if o.get("base")==data.get("base") else "other-base"),o["statement"][:220].replace("\n"," "))
        if context.get("knowledge"):
            print("\nRelevant knowledge:")
            for x in context["knowledge"]:
                print(x["id"],x["kind"],x["statement"][:200].replace("\n"," "))
        if data.get("preflight_candidate"):
            print("\nGenerated candidate (not yet kernel-checked):",data["preflight_candidate"]["path"])
        if data.get("open_method_nodes"):
            print("\nOpen mathematical methods (coordinate ownership before reuse):")
            for x in data["open_method_nodes"]:print(x["id"],x["family"],x["statement"].replace("\n"," "))
        if data.get("source_locations"):print("Sources:",", ".join(data["source_locations"]))
        print("\nUseful next commands:")
        if data.get("assigned_obligation"):print("pnp-research obligations show "+data["assigned_obligation"])
        print("\n".join(data["next_commands"]))
        print("Detailed examples: pnp-research guide "+role)
    return 0

if __name__=="__main__":raise SystemExit(main())

"""Executive's short, executable tool instructions, injected at dispatch."""
import argparse
import subprocess
from pathlib import Path

P = "PYTHONPATH=/var/lib/lubko/wd/viche python3 -m missions.pnp."
RELAY = "~/.local/bin/pnp-remote-check"

def instructions(role):
    roles = {
        "general": (
            "Understand the exact claim and its negation; search checked analogues, then choose a mathematical route. "
            "Share concrete results via support finding. Continue if focus changes."
        ),
        "integrator": (
            "Decompose into precise Lean obligations; incorporate peer fragments and assemble the candidate. "
            "Use remote elaboration in parallel with local iteration; submit immediately when complete."
        ),
        "specialist": (
            "Solve your assigned subproblem or distinct approach, not the whole swarm's work. "
            "Share usable proof fragments and counterexamples immediately."
        ),
        "knowledge": (
            f"Run {P}support targets; find checked analogues/opposite conclusions with proofs find/source. "
            "Read exact sources and verify applicable hypotheses. Deliver evidence with support advise GAP ATTEMPT knowledge EVIDENCE MESSAGE."
        ),
        "methods": (
            f"Run {P}support targets; derive reductions, witnesses or counterexamples. "
            "Use proofs search/row-search for bounded finite synthesis and proofs rows for independent verification when available. "
            "Deliver reusable artifacts with support advise GAP ATTEMPT methods EVIDENCE MESSAGE."
        ),
        "flow": (
            f"Run {P}support targets and {P}metrics if present. Compare actual worker activity, duplicate builds and elapsed time. "
            "Use ~/.local/bin/marceline-request status to assess remote queue/health. Recommend concrete allocation changes, not generic reports."
        ),
        "portfolio": (
            f"Run {P}portfolio inspect. Compare actual mathematical progress and remaining work across all leases. "
            "Use portfolio switch only for a materially better route; factor in local and remote compiler availability."
        ),
        "lease-evaluation": (
            f"Run {P}portfolio inspect; read workers' evidence and checked reductions. "
            "Use portfolio release only with concrete mathematical/economic evidence, never just because a compile is slow."
        ),
        "transport": (
            "Maintain the deployed relay, cache coverage and latency. Use ~/.local/bin/marceline-request status; "
            "measure successful remote builds and queue times, prioritize current base coverage, avoid duplicating dependency caches."
        ),
        "adapter": (
            f"Use {P}tools if available; develop reusable checked-proof adaptations and benchmark against held-out problems. "
            "Prefer actual validated candidates over reports."
        ),
        "benchmark": (
            f"Use {P}tools and {P}metrics if available. Measure accepted proofs, wall time and resource use; "
            "compare remote versus local builds, not just invocation counts."
        ),
    }
    if role not in roles:
        raise ValueError("unknown research role")
    text = roles[role]
    if role in ("general", "integrator", "specialist"):
        text += (
            f" From your bound cwd, run {P}cli guard; if available, {P}tools lists commands. "
            f"Remote Lean: run {RELAY} --availability once for this checkout. "
            f"If available, use {RELAY} --async FILE.lean for a complete candidate or "
            f"{RELAY} --scratch --async FILE.lean for an intermediate Lean check; "
            "continue mathematics while it runs, then ~/.local/bin/marceline-request wait ID 1100. "
            "Read nested result.status and diagnostics. Use local managed Lean for small checks or unavailable/busy remote; "
            "do not run the same build twice. Remote elaboration is not upstream acceptance and never delays submit."
        )
    return text

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("role")
    p.add_argument("--task", default="")
    p.add_argument("--agent", help="Executive: dispatch this role to the named existing/newly created idle agent")
    p.add_argument("--cwd", type=Path)
    p.add_argument("--steer", action="store_true", help="Executive: replace current instructions at a justified checkpoint")
    a = p.parse_args()
    try:
        text = instructions(a.role) + ("\n\nAssigned task: " + a.task if a.task else "")
        if a.agent:
            if not a.cwd or not a.cwd.is_dir() or not a.task:
                p.error("--agent requires existing --cwd and explicit --task")
            argv = ["antonina", "agent", "run", "--id", a.agent, "--cwd", str(a.cwd.resolve()),
                    "--prompt", text, "--detach", "--json"]
            if a.steer:
                argv.append("--steer")
            return subprocess.call(argv)
        print(text)
    except ValueError as exc:
        p.error(str(exc))

if __name__ == "__main__":
    raise SystemExit(main())

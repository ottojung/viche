"""Executive-only dispatch helper for independent research workstreams."""
import argparse
import subprocess
from pathlib import Path

ROLES = {
 "method": "Develop a mathematical technique that solves a FAMILY of problems; not a single lease. Search pnp-research knowledge find and checked upstream proofs; formulate exact general lemmas. Use pnp-research obligations request --base SHA --family FAMILY --provenance SOURCE --statement TYPE; solve ID BODY --method independently of desk leases. Preserve exact hypotheses, failed generalizations and counterexamples. Demonstrate transfer to multiple distinct instances. No desk acquisition or direct PRs.",
 "tool": "Turn a validated mathematical method into a deterministic reusable tool with independent verification. Run pnp-research star GRAPH.json for monotone graph circuits; output a certificate and benchmark distinct held-out families. Use pnp-research obligations for the Lean semantics. Measure actual kernel checks and accepted contributions, not just tool invocations. Integrate with existing proof tools; no duplicate tool stack.",
 "knowledge": "Index durable evidence using pnp-research knowledge ingest; query by family and exact terms; promote important results into lemma, technique, obstruction, counterexample, reduction and certificate objects with exact evidence and dependency IDs. Do not label reported proofs kernel-checked.",
 "portfolio": "Run pnp-research yield. Combine observed family baseline, exact open/checked obligations, applicable techniques and current competition with first-hand worker evidence. Small samples and censored history limit calibration. Do not release solely on numerical score.",
 "lease-evaluation": "Run pnp-research yield; compare realistic remaining obligations and evidence of feasibility. Preserve reusable knowledge before release. Do not release due to age, a single failed tactic, or raw family rate.",
 "integrator": "Use pnp-research obligations ready and show ID to turn the current proof outline into exact dependencies. Request exact types, assign complementary tasks via Executive, reuse checked bodies and assemble --candidate only when the root is checked. If base differs, fork and independently recheck. Submit the exact complete candidate immediately."
}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("role",choices=sorted(ROLES));p.add_argument("--task",default="")
    p.add_argument("--agent");p.add_argument("--cwd",type=Path)
    a=p.parse_args();text=ROLES[a.role]+("\nAssigned task: "+a.task if a.task else "")
    if not a.agent:
        print(text);return 0
    if not a.cwd or not a.cwd.is_dir() or not a.task:p.error("explicit task and existing cwd required")
    # Existing agents are created and selected only by Executive.
    return subprocess.call(["antonina","agent","run","--id",a.agent,"--cwd",str(a.cwd.resolve()),
                            "--prompt",text,"--detach","--json"])
if __name__=="__main__":raise SystemExit(main())

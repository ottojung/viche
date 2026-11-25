#!/usr/bin/env python3
"""Graph-edge monotone circuit-witness generator.

Statement shapes (desk corpus):
  * edge-list: `C.eval (List.ofFn x) = true ↔ ∃ u v, (u.val,v.val) ∈ [(pairs)] ∧ ...`
  * explicit DNF: `C.eval (List.ofFn x) = (x a && x b) || ...`
Method: greedily cover the graph by stars (one OR over the neighbours of a centre plus one
AND with the centre), then OR the stars; emit merged L-meta-929-style witness proof
(helper namespace, simp/decide for gate kinds and size, `decide +kernel` for evaluation).
Exit 3 when the cover exceeds the bound or the shape is not recognised.
"""
import re
import sys

MATCH = (r"∃ C : PEqualNP\.CircuitLowerBounds\.Circuit, "
         r"PEqualNP\.MetaComplexity\.Monotone2 C ∧ C\.size ≤ \d+ ∧ .*C\.eval \(List\.ofFn x\)")


def parse(stmt):
    n = int(re.search(r"∀ x : Fin (\d+) → Bool", stmt).group(1))
    bound = int(re.search(r"C\.size ≤ (\d+)", stmt).group(1))
    lm = re.search(r"\(\[([0-9, ()]+)\] : List \(ℕ × ℕ\)\)", stmt)
    if lm:
        edges = [(int(a), int(b)) for a, b in re.findall(r'\((\d+),\s*(\d+)\)', lm.group(1))]
    else:
        expr = stmt.split("C.eval (List.ofFn x) = ", 1)[1].strip()
        m = re.match(r"\(fun x : Fin \d+ → Bool => (.*)\) x$", expr)
        if m:
            expr = m.group(1)
        edges = []
        for t in re.split(r'\|\|', expr):
            lits = [int(z) for z in re.findall(r'x\s*(\d+)', t)]
            if len(lits) != 2:
                return None
            edges.append(tuple(sorted(lits)))
    if not edges or any(a >= n or b >= n for a, b in edges):
        return None
    return n, bound, sorted(set(tuple(sorted(e)) for e in edges))


def star_cover(n, edges, bound):
    remaining = set(edges)
    stars = []
    while remaining:
        best, bestgain = None, 0
        for u in range(n):
            gain = sum(1 for a, b in remaining if a == u or b == u)
            if gain > bestgain:
                bestgain, best = gain, u
        if best is None:
            break
        u = best
        nb = sorted({b if a == u else a for a, b in remaining if a == u or b == u})
        stars.append((u, nb))
        remaining = {(a, b) for a, b in remaining if a != u and b != u}
    gates, wires = [], []
    for u, nb in stars:
        w = nb[0]
        for v in nb[1:]:
            gates.append(('or', w, v)); w = n + len(gates) - 1
        gates.append(('and', u, w)); wires.append(n + len(gates) - 1)
    w = wires[0]
    for v in wires[1:]:
        gates.append(('or', w, v)); w = n + len(gates) - 1
    return gates if len(gates) <= bound else None


def emit(statement, gates, outwire):
    num_m = re.search(r"(\d+)$", sys.argv[1]) if len(sys.argv) > 1 else None
    num = num_m.group(1) if num_m else "0"
    mod = "PEqualNP.Outside.L_meta_" + num
    gs = ", ".join("⟨GateOp.%s, [%d, %d]⟩" % (op, a, b) for op, a, b in gates)
    return """import Mathlib
import PEqualNP.Defs

namespace %s_aux

open PEqualNP.CircuitLowerBounds

-- Witness circuit from a greedy star cover; proof shape follows merged L_meta_929 (Apache-2.0).
def c : Circuit := ⟨[%s], %d⟩

end %s_aux

open %s_aux

set_option maxRecDepth 100000 in
set_option maxHeartbeats 20000000 in
theorem %s : %s := by
  refine ⟨c, ?_, ?_, ?_⟩
  · simp [PEqualNP.MetaComplexity.Monotone2, c]
  · decide
  · decide +kernel
""" % (mod, gs, outwire, mod, mod, mod, statement)


def main():
    if len(sys.argv) != 4:
        sys.exit(2)
    gid, sf, out = sys.argv[1:4]
    statement = open(sf).read().strip()
    parsed = parse(statement)
    if parsed is None:
        print("unrecognised edge-cover statement", file=sys.stderr); sys.exit(3)
    n, bound, edges = parsed
    gates = star_cover(n, edges, bound)
    if gates is None:
        print("star cover exceeds bound %d" % bound, file=sys.stderr); sys.exit(3)
    open(out, "w").write(emit(statement, gates, n + len(gates) - 1))
    sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generator for the two-lit graph-function HasCircuitSize family (BACKLOG family 2).

Statement shape (merged L_meta_21896 / desk rows):
  ∃ C : Circuit, FanInTwo C ∧ C.size ≤ K ∧
    ∀ i j : Fin n, C.eval (List.ofFn fun k : Fin n => decide (k = i ∨ k = j))
      = (M : ℕ).testBit (n * min i.val j.val + max i.val j.val)

Method: the two-hot input has bits {i,j}; the function is the edge indicator of
the graph whose mask bits are M at n*i+j for i<j.  Build one AND per edge and OR
the AND outputs (2|E|-1 gates).  Every circuit is audited on all n^2 (i,j) rows.
Emits the merged L_meta_21896 proof shape.  Exit 3 on any other shape or when
the construction exceeds K (no speculative below-optimum proof).
"""
import re
import sys

MATCH = (r"∃ C : PEqualNP\.CircuitLowerBounds\.Circuit, PEqualNP\.MetaComplexity\.(?:FanInTwo|Monotone2) C ∧ "
         r"C\.size ≤ \d+ ∧ ∀ i j : Fin (\d+), C\.eval \(List\.ofFn fun k : Fin \d+ => decide \(k = i ∨ k = j\)\) = "
         r"(?:\((\d+) : ℕ\)|(\d+))\.testBit \(\d+ \* min i\.val j\.val \+ max i\.val j\.val\)")


def parse(stmt):
    s = " ".join(stmt.split())
    m = re.search(MATCH, s)
    if not m:
        return None
    n = int(m.group(1))
    mask = int(m.group(2) if m.group(2) is not None else m.group(3))
    k = int(re.search(r"C\.size ≤ (\d+)", s).group(1))
    return n, mask, k


def build(n, mask):
    """Minimum star cover: cost |E| + tau - 1 (tau = min vertex cover size).

    Self-loop mask bits are unsupported (they require a NOT gate and a different
    promise shape); audit rejects them, so such rows refuse honestly.
    """
    if any((mask >> (n * i + i)) & 1 for i in range(n)):
        return [], None
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)
             if (mask >> (n * i + j)) & 1]
    if not edges:  # constant false: x0 AND NOT x0
        return [("not", 0, None), ("and", 0, n)], n + 1
    adj = [set() for _ in range(n)]
    for u, v in edges:
        adj[u].add(v); adj[v].add(u)
    best = None
    for bits in range(1 << n):
        S = {i for i in range(n) if (bits >> i) & 1}
        if not all(u in S or v in S for u, v in edges):
            continue
        if best is None or len(S) < len(best):
            best = S
    gates = []
    star_out = []
    for v in sorted(best):
        # assign each incident edge to v when the other endpoint is not a chosen
        # centre, and to the smaller centre when both ends are centres
        nb = sorted(u for u in adj[v] if u not in best or v < u)
        if not nb:
            continue
        w = nb[0]
        for u in nb[1:]:
            gates.append(("or", w, u))
            w = n + len(gates) - 1
        gates.append(("and", v, w))
        star_out.append(n + len(gates) - 1)
    if not star_out:
        return [], None
    w = star_out[0]
    for x in star_out[1:]:
        gates.append(("or", w, x))
        w = n + len(gates) - 1
    return gates, w


def audit(n, mask, gates, out):
    for i in range(n):
        for j in range(n):
            w = [False] * n
            w[i] = True
            w[j] = True
            for op, a, b in gates:
                w.append(1 - w[a] if op == "not" else
                         (w[a] & w[b] if op == "and" else w[a] | w[b]))
            want = bool((mask >> (n * min(i, j) + max(i, j))) & 1)
            if bool(w[out]) != want:
                return False
    return True


def emit_lean(n, mask, k, gates, out, gid, stmt):
    name = gid.replace("-", "_")
    mod = "PEqualNP.Outside." + name
    glist = ", ".join("⟨GateOp.%s, [%d%s]⟩" % (op, a, "" if op == "not" else ", %d" % b)
                      for op, a, b in gates)
    return """import Mathlib
import PEqualNP.Defs

namespace %s

open PEqualNP.CircuitLowerBounds PEqualNP.MetaComplexity

def C0 : Circuit := ⟨[%s], %d⟩

theorem ok0 : FanInTwo C0 := by
  intro g hg
  simp only [C0, List.mem_cons, List.not_mem_nil, or_false] at hg
  rcases hg with %s <;> simp

theorem %s : %s := by
  refine ⟨C0, ok0, by decide, ?_⟩
  intro i j
  decide +kernel

end %s
""" % (name, glist, out, " | ".join(["rfl"] * len(gates)),
       mod, stmt.strip(), name)


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: gen.py GID STATEMENT_FILE OUT.lean")
    gid = sys.argv[1]
    stmt = open(sys.argv[2]).read()
    p = parse(stmt)
    if p is None:
        sys.exit(3)
    n, mask, k = p
    gates, out = build(n, mask)
    if out is None or len(gates) > k or not audit(n, mask, gates, out):
        sys.exit(3)
    open(sys.argv[3], "w").write(emit_lean(n, mask, k, gates, out, gid, stmt))
    return 0


if __name__ == "__main__":
    sys.exit(main())

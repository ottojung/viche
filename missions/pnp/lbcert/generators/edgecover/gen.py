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

# Narrow match: only monotone edge-function witnesses (edge-list or pure 2-literal DNF).
# Excludes table-indexed, 3+ literal DNF, and non-graph monotone statements.
MATCH = (
    r"^∃ C : PEqualNP\.CircuitLowerBounds\.Circuit, "
    r"PEqualNP\.MetaComplexity\.Monotone2 C ∧ C\.size ≤ \d+ ∧ "
    r"(?:"
    r"\(∀ x : Fin \d+ → Bool, \(C\.eval \(List\.ofFn x\) = true ↔ "
    r"∃ u v : Fin \d+, \(u\.val, v\.val\) ∈ \(\[.*"
    r"|"
    r"∀ x : Fin \d+ → Bool, C\.eval \(List\.ofFn x\) = "
    r"(?:\(fun x : Fin \d+ → Bool => )?\(?x \d+ && x \d+\)?(?: \|\| \(?x \d+ && x \d+\)?)*\)?(?: x)?$"
    r")"
)


def parse(stmt):
    mn = re.search(r"∀ x : Fin (\d+) → Bool", stmt)
    mb = re.search(r"C\.size ≤ (\d+)", stmt)
    if not mn or not mb:
        return None
    n, bound = int(mn.group(1)), int(mb.group(1))
    lm = re.search(r"\(\[([0-9, ()]+)\] : List \(ℕ × ℕ\)\)", stmt)
    if lm:
        edges = [(int(a), int(b)) for a, b in re.findall(r'\((\d+),\s*(\d+)\)', lm.group(1))]
    else:
        parts = stmt.split("C.eval (List.ofFn x) = ", 1)
        if len(parts) != 2:
            return None
        expr = parts[1].strip()
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


def exact_bipartite_star_cover(n, edges, bound):
    """Exact minimum star cover for bipartite graphs (enumerate smaller side).

    Cost of a centre set S is sum_deg(S) + |S| - 1.  Returns None when the graph
    is not bipartite, the smaller side is too large to enumerate, or the optimum
    exceeds the bound (then the greedy fallback cannot do better anyway).
    """
    adj = [set() for _ in range(n)]
    for a, b in edges:
        adj[a].add(b); adj[b].add(a)
    color = [-1] * n
    bip = True
    for s in range(n):
        if color[s] != -1:
            continue
        color[s] = 0; stack = [s]
        while stack:
            u = stack.pop()
            for v in adj[u]:
                if color[v] == -1:
                    color[v] = 1 - color[u]; stack.append(v)
                elif color[v] == color[u]:
                    bip = False
    if not bip:
        return None
    sides = [[v for v in range(n) if color[v] == c] for c in (0, 1)]
    small = sides[0] if len(sides[0]) <= len(sides[1]) else sides[1]
    if len(small) > 16:
        return None
    best = None
    for mask in range(1 << len(small)):
        full = {small[i] for i in range(len(small)) if (mask >> i) & 1}
        for u in small:
            if u not in full:
                for v in adj[u]:
                    if color[v] != color[u]:
                        full.add(v)
        if not all(a in full or b in full for a, b in edges):
            continue
        cost = sum(len(adj[v]) + 1 for v in full) - 1
        if best is None or cost < best[0]:
            best = (cost, full)
    if best is None or best[0] > bound:
        return None
    gates, wires = [], []
    for u in sorted(best[1]):
        nb = sorted(adj[u])
        w = nb[0]
        for v in nb[1:]:
            gates.append(('or', w, v)); w = n + len(gates) - 1
        gates.append(('and', u, w)); wires.append(n + len(gates) - 1)
    w = wires[0]
    for v in wires[1:]:
        gates.append(('or', w, v)); w = n + len(gates) - 1
    return gates if len(gates) <= bound else None


def star_cover(n, edges, bound):
    exact = exact_bipartite_star_cover(n, edges, bound)
    if exact is not None:
        return exact
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


def simulate(n, gates):
    """Symbolic Bool expression computed by the gate list (compound AND operand first).

    Matches the normal form produced by
      simp [c, Circuit.eval, GateOp.eval, Bool.and_comm]
    on the concrete circuit fold: a compound (OR-derived) operand of an AND gate is
    placed before the plain input variable, while plain/plain conjunctions keep order.
    """
    w = ["b%d" % i for i in range(n)]
    orflag = [False] * n
    for op, a, b in gates:
        x, y = w[a], w[b]
        xo, yo = orflag[a], orflag[b]
        xs = "(%s)" % x if xo else x
        ys = "(%s)" % y if yo else y
        if op == 'and':
            expr = "(%s && %s)" % (ys, xs) if (yo and not xo) else "(%s && %s)" % (xs, ys)
            flag = False
        else:
            expr = "%s || %s" % (x, y)
            flag = True
        w.append(expr)
        orflag.append(flag)
    return w[n + len(gates) - 1]

def _bool_rhs(statement, n, edges):
    """Return a Bool-arg RHS expression for the helper lemma."""
    if '↔ ∃ u v' in statement.split('C.eval (List.ofFn x) = ', 1)[1]:
        # edge-list form: translate to disjunction of edge conjunctions
        return " || ".join("(%s && %s)" % ("b%d" % u, "b%d" % v)
                           for u, v in edges)
    rhs = statement.split("C.eval (List.ofFn x) = ", 1)[1].strip()
    m = re.match(r"\(fun x : Fin \d+ → Bool => (.*)\) x$", rhs)
    if m:
        rhs = m.group(1)
    return re.sub(r'x\s*(\d+)', lambda z: "b%d" % int(z.group(1)), rhs)


def emit(statement, n, edges, gates, outwire):
    """Emit a witness with a small, kernel-check-friendly eval proof.

    `eval_bool` is closed by `simp` over the concrete circuit fold; the residual
    star-form/DNF equivalence is closed by `decide` over Bool variables.  Both proof
    terms are small, so applying them in the final theorem stays fast.
    """
    num_m = re.search(r"(\d+)$", sys.argv[1]) if len(sys.argv) > 1 else None
    num = num_m.group(1) if num_m else "0"
    mod = "PEqualNP.Outside.L_meta_" + num
    ns = mod + "_aux"
    gs = ", ".join("⟨GateOp.%s, [%d, %d]⟩" % (op, a, b) for op, a, b in gates)
    names = ["b%d" % i for i in range(n)]
    star = "(" + simulate(n, gates) + ")"
    dnf = _bool_rhs(statement, n, edges)
    args = " ".join(names)
    call = " ".join("(x %d)" % i for i in range(n))
    xlist = ", ".join("x %d" % i for i in range(n))
    wf_alts = " | ".join(["rfl"] * len(gates))
    return """import Mathlib
import PEqualNP.Defs

namespace %s

open PEqualNP.CircuitLowerBounds

-- Witness circuit from a greedy star cover; proof shape follows merged L_meta_929 (Apache-2.0).
def c : Circuit := ⟨[%s], %d⟩

lemma eval_bool (%s : Bool) : c.eval [%s] = %s := by
  simp [c, Circuit.eval, GateOp.eval, Bool.and_comm]

lemma star_eq_dnf : ∀ %s : Bool, %s = (%s) := by
  decide

lemma wf : PEqualNP.MetaComplexity.Monotone2 c := by
  intro g hg
  simp only [c, List.mem_cons, List.not_mem_nil, or_false] at hg
  rcases hg with %s <;> simp

end %s

open %s

set_option maxRecDepth 100000 in
set_option maxHeartbeats 4000000 in
theorem %s : %s := by
  refine ⟨c, wf, by decide, ?_⟩
  intro x
  have h : List.ofFn x = [%s] := by simp [List.ofFn_succ]
  rw [h]
  exact (eval_bool %s).trans (star_eq_dnf %s)
""" % (ns, gs, outwire, args, ", ".join(names), star, args, star, dnf, wf_alts,
       ns, ns, mod, statement, xlist, call, call)

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
    open(out, "w").write(emit(statement, n, edges, gates, n + len(gates) - 1))
    sys.exit(0)


if __name__ == "__main__":
    main()

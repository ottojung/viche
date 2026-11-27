#!/usr/bin/env python3
"""Explicit-DNF edge-function HasCircuitSize generator.

Statement shape:
  PEqualNP.MetaComplexity.HasCircuitSize n
    (fun x : Fin n → Bool => (x a && x b) || ...) K

Method: greedy star cover of the edge graph (OR neighbours + AND centre, OR tree),
verified on all 2^n rows in Python; emits the merged L_meta_18229 proof shape
(unfold HasCircuitSize, refine witness, simp FanInTwo, decide, decide +kernel).
Exit 3 when the cover exceeds the bound or the shape is not recognised.
"""
import re
import sys

MATCH = (r"PEqualNP\.MetaComplexity\.HasCircuitSize \d+ \(fun x : Fin \d+ → Bool => "
         r"\(?x \d+ && x \d+\)?(?: \|\| \(?x \d+ && x \d+\)?)*\) \d+")


def parse(stmt):
    m = re.match(r"PEqualNP\.MetaComplexity\.HasCircuitSize (\d+) \(fun x : Fin (\d+) → Bool => "
                 r"(.+)\) (\d+)$", stmt.strip())
    if not m:
        return None
    n, bound = int(m.group(1)), int(m.group(4))
    if n != int(m.group(2)):
        return None
    edges = []
    for t in m.group(3).split('||'):
        lits = [int(z) for z in re.findall(r'x\s*(\d+)', t)]
        if len(lits) != 2:
            return None
        edges.append(tuple(sorted(lits)))
    if not edges or any(a >= n or b >= n for a, b in edges):
        return None
    return n, bound, sorted(set(edges))


def optimal_bipartite_star_cover(n, edges, bound):
    """Minimum-cost star cover when the graph is bipartite (exact on the smaller side).

    For a vertex cover S the star circuit costs sum_{v in S} deg(v) + |S| - 1
    (deg(v)-1 OR gates plus one AND per centre, then a final OR tree).
    Enumerating subsets of the smaller bipartition finds the optimum when that
    side is small; otherwise return None and let the greedy fallback run.
    """
    from itertools import combinations
    adj = [set() for _ in range(n)]
    for a, b in edges:
        adj[a].add(b); adj[b].add(a)
    color = [-1] * n
    bip = True
    for s in range(n):
        if color[s] != -1:
            continue
        color[s] = 0
        stack = [s]
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
    small, other = (sides[0], sides[1]) if len(sides[0]) <= len(sides[1]) else (sides[1], sides[0])
    if len(small) > 16:
        return None
    best = None
    for mask in range(1 << len(small)):
        chosen = {small[i] for i in range(len(small)) if (mask >> i) & 1}
        # any edge not touched by a chosen small-side vertex needs its other end
        full = set(chosen)
        for u in small:
            if u not in chosen:
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
    exact = optimal_bipartite_star_cover(n, edges, bound)
    if exact is not None:
        return exact
    remaining = set(edges)
    stars = []
    while remaining:
        best, gain = None, 0
        for u in range(n):
            g = sum(1 for a, b in remaining if a == u or b == u)
            if g > gain:
                gain, best = g, u
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


def verify(n, edges, gates, out):
    for mask in range(1 << n):
        w = [(mask >> i) & 1 for i in range(n)]
        for op, a, b in gates:
            w.append(w[a] | w[b] if op == 'or' else w[a] & w[b])
        if w[out] != int(any((mask >> a) & 1 and (mask >> b) & 1 for a, b in edges)):
            return False
    return True


def emit(statement, gates, out):
    gs = ", ".join("⟨.%s, [%d, %d]⟩" % g for g in gates)
    return """import Mathlib
import PEqualNP.Defs

-- Witness circuit from a greedy star cover; proof shape follows merged L_meta_18229 (Apache-2.0).
theorem PEqualNP.Outside.%s : %s := by
  unfold PEqualNP.MetaComplexity.HasCircuitSize
  refine ⟨⟨[%s], %d⟩, ?_, ?_, ?_⟩
  · simp [PEqualNP.MetaComplexity.FanInTwo]
  · decide
  · decide +kernel
""" % (sys.argv[1].replace('L-meta-', 'L_meta_'), statement, gs, out)


def main():
    if len(sys.argv) != 4:
        sys.exit(2)
    gid, sf, outfile = sys.argv[1:4]
    statement = open(sf).read().strip()
    p = parse(statement)
    if p is None:
        print("unrecognised edge HasCircuitSize statement", file=sys.stderr)
        sys.exit(3)
    n, bound, edges = p
    gates = star_cover(n, edges, bound)
    if gates is None:
        print("star cover exceeds bound %d" % bound, file=sys.stderr)
        sys.exit(3)
    out = n + len(gates) - 1
    if not verify(n, edges, gates, out):
        print("witness verification failed", file=sys.stderr)
        sys.exit(3)
    open(outfile, "w").write(emit(statement, gates, out))
    sys.exit(0)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Cost-aware symbolic biclique cover for graph edge functions.

A biclique (A,B) of the graph is implemented by fan-in-two gates as
  OR(A) then OR(B) then AND   -- |A|+|B|-1 gates (a star is the case |A|=1).
The cover is enumerated by closing row/column subsets under the adjacency relation
(symbolic closure, no truth table over 2^n inputs) and selected greedily by
new-edges-per-gate.  Works for graphs far beyond brute-force input sizes.
"""
import itertools
import random


def bicliques(n, edges, max_sub=3, random_tries=200, seed=0):
    adj = [set() for _ in range(n)]
    for a, b in edges:
        if a == b or a >= n or b >= n:
            continue
        adj[a].add(b)
        adj[b].add(a)

    def close(R, C):
        if not R or not C:
            return None
        R2 = frozenset(i for i in range(n) if C <= adj[i])
        C2 = frozenset(c for c in range(n) if all(c in adj[i] for i in R2))
        if not R2 or not C2:
            return None
        return R2, C2

    seen = set()
    for r in range(1, min(max_sub, n) + 1):
        for S in itertools.combinations(range(n), r):
            C = set(adj[S[0]])
            for i in S[1:]:
                C &= adj[i]
            if C:
                c = close(frozenset(S), frozenset(C))
                if c:
                    seen.add(c)
    rng = random.Random(seed)
    for _ in range(random_tries):
        S = rng.sample(range(n), rng.randint(2, min(max_sub, n)))
        C = set(adj[S[0]])
        for i in S[1:]:
            C &= adj[i]
        if C:
            c = close(frozenset(S), frozenset(C))
            if c:
                seen.add(c)
    out = []
    for R, C in seen:
        cov = frozenset((a, b) for a in R for b in C if b in adj[a])
        cost = len(R) + len(C) - 1
        if cov:
            out.append((R, C, cov, cost))
    return out


def greedy_cover(n, edges, cands=None, max_sub=3, tries=200, seed=0):
    remaining = frozenset(tuple(sorted(e)) for e in edges)
    if cands is None:
        cands = bicliques(n, edges, max_sub=max_sub, random_tries=tries, seed=seed)
    chosen = []
    while remaining:
        best = None
        ratio = -1.0
        for R, C, cov, cost in cands:
            gain = len(cov & remaining)
            if gain and gain / cost > ratio:
                ratio, best = gain / cost, (R, C, cov, cost)
        if best is None:
            break
        remaining = remaining - best[2]
        chosen.append(best)
    gates = sum(x[3] for x in chosen) + max(0, len(chosen) - 1)
    return gates, chosen


def to_gates(n, chosen):
    """Translate covered bicliques into interleaved OR/AND gate triples."""
    gates, wires = [], []
    for R, C, _, _ in chosen:
        A, B = sorted(R), sorted(C)
        w = A[0]
        for v in A[1:]:
            gates.append(('or', w, v))
            w = n + len(gates) - 1
        z = B[0]
        for v in B[1:]:
            gates.append(('or', z, v))
            z = n + len(gates) - 1
        gates.append(('and', w, z))
        wires.append(n + len(gates) - 1)
    w = wires[0]
    for v in wires[1:]:
        gates.append(('or', w, v))
        w = n + len(gates) - 1
    return gates

"""Graph-circuit generators for the retrospective PnP benchmark.

Generators take (n, edges) where edges are sorted unique (u,v), u<v, and return
(gates, output). Gates are (op, a, b) with op in {"and","or"} and wire indices
referring to inputs [0,n) or previous gates [n, n+len(gates)).
"""
from __future__ import annotations

import itertools


def _disjoin(gates, memo, n, xs):
    xs = list(xs)
    result = xs[0]
    for x in xs[1:]:
        key = ("or", *sorted((result, x)))
        if key not in memo:
            memo[key] = n + len(gates)
            gates.append(key)
        result = memo[key]
    return result


def legacy_greedy(n, edges):
    """Legacy greedy block-cover generator (pre-star-cover synthesis).

    Covers edges by stars or complete bipartite blocks, sharing OR
    subexpressions. Tries three ranking strategies and returns the smallest
    circuit found. This is the historical generator compared in the
    2026-11-24 founder proof-production study.
    """
    edges = set(tuple(sorted(e)) for e in edges)
    neighbors = {
        i: {b if a == i else a for a, b in edges if i in (a, b)}
        for i in range(n)
    }
    blocks = set()
    for i in range(n):
        if neighbors[i]:
            blocks.add(((i,), tuple(sorted(neighbors[i]))))
    for k in range(2, min(4, n) + 1):
        for left in itertools.combinations(range(n), k):
            right = set.intersection(*(neighbors[i] for i in left))
            if right:
                blocks.add((left, tuple(sorted(right))))
    blocks = sorted(blocks)

    best = None
    for strategy in range(3):
        gates, memo, remaining, outputs = [], {}, set(edges), []

        def gate(op, a, b):
            key = (op, *sorted((a, b)))
            if key not in memo:
                memo[key] = n + len(gates)
                gates.append(key)
            return memo[key]

        def disjoin(xs):
            return _disjoin(gates, memo, n, xs)

        while remaining:
            choices = []
            for a, b in blocks:
                covered = {tuple(sorted((u, v))) for u in a for v in b} & remaining
                if not covered:
                    continue
                cost = len(a) + len(b)
                if strategy == 0:
                    rank = (len(covered) / cost, len(covered))
                elif strategy == 1:
                    rank = (len(covered), -cost)
                else:
                    rank = (len(covered) - cost, -cost)
                choices.append((rank, a, b, covered))
            _, a, b, covered = max(choices, key=lambda t: (t[0], t[1], t[2]))
            outputs.append(gate("and", disjoin(a), disjoin(b)))
            remaining -= covered
        output = disjoin(outputs)
        if best is None or len(gates) < len(best[0]):
            best = (gates, output)
    return best


def exact_star_cover(n, edges):
    """Exact minimum vertex cover with single ownership of each edge.

    Finds a minimum vertex cover and assigns every edge to exactly one cover
    endpoint, forming a star. This avoids paying for an edge twice. It is an
    upper bound on optimal circuit size, not a claim of globally optimal
    circuits. This is the generator reported by the 2026-11-24 founder
    proof-production study as meeting all 42 recognized accepted constructions.
    """
    edges = set(tuple(sorted(e)) for e in edges)
    vertices = sorted(set(itertools.chain.from_iterable(edges)))
    centers = None
    for k in range(0, len(vertices) + 1):
        for s in itertools.combinations(vertices, k):
            if all(a in s or b in s for a, b in edges):
                centers = s
                break
        if centers is not None:
            break
    stars = {v: [] for v in centers}
    for a, b in sorted(edges):
        owner = a if a in stars else b
        other = b if owner == a else a
        stars[owner].append(other)

    gates = []

    def gate(op, a, b):
        gates.append((op, a, b))
        return n + len(gates) - 1

    def disjoin(xs):
        r = xs[0]
        for x in xs[1:]:
            r = gate("or", r, x)
        return r

    outputs = [gate("and", v, disjoin(ns)) for v, ns in sorted(stars.items()) if ns]
    if not outputs:
        # Empty edge set is outside the normal benchmark shape, but keep the
        # generator total.
        return [], 0
    return gates, disjoin(outputs)


GENERATORS = {
    "legacy_greedy": legacy_greedy,
    "exact_star_cover": exact_star_cover,
}


def get(name):
    if name not in GENERATORS:
        raise KeyError(f"unknown generator {name!r}; known: {sorted(GENERATORS)}")
    return GENERATORS[name]

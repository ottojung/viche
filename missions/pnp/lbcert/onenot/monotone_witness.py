"""Fast constructive search for small monotone circuits.

The recursive decompositions are valid for monotone truth tables. Ranking
uses the number of distinct gates (DAG sharing), not the formula tree size.
This produces an independently audited upper-bound witness only: it never
claims minimum size or a formal lower bound.
"""
from functools import lru_cache
from itertools import product
import time

def synthesize(n, f, width=3, budget=None):
    deadline = None if budget is None else time.monotonic() + max(0, budget)

    def check_budget():
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError
    if not 1 <= n <= 6 or len(f) != 1 << n or any(v not in (0, 1) for v in f):
        return None
    if any(f[r] and not f[r | (1 << i)] for r in range(1 << n) for i in range(n)):
        return None
    full = (1 << (1 << n)) - 1
    target = sum(int(v) << r for r, v in enumerate(f))
    one, zero = ("c", 1), ("c", 0)
    variables = [("x", i) for i in range(n)]
    low = [sum(1 << r for r in range(1 << n) if not r & (1 << i)) for i in range(n)]
    high = [full ^ m for m in low]
    inputs = {m: variables[i] for i, m in enumerate(high)}
    if target in (0, full) or target in inputs:
        return None  # current Lean emitter expects an internal output gate

    def combine(op, a, b):
        if a == b:
            return a
        absorb, neutral = (zero, one) if op == "and" else (one, zero)
        if a == absorb or b == absorb:
            return absorb
        if a == neutral:
            return b
        if b == neutral:
            return a
        other = "or" if op == "and" else "and"
        if a[0] == other and b in a[1:]:
            return b
        if b[0] == other and a in b[1:]:
            return a
        return (op, *sorted((a, b)))

    @lru_cache(None)
    def gates(expr):
        if expr[0] in ("x", "c"):
            return frozenset()
        return gates(expr[1]) | gates(expr[2]) | {expr}

    def cofactor(t, i, val):
        if val:
            b = t & high[i]
            return b | (b >> (1 << i))
        b = t & low[i]
        return b | (b << (1 << i))

    def upward(t):
        for i in range(n):
            t |= (t & low[i]) << (1 << i)
        return t

    def downward(t):
        for i in range(n):
            t |= (t & high[i]) >> (1 << i)
        return t

    @lru_cache(None)
    def solve(t):
        check_budget()
        if t == 0:
            return (zero,)
        if t == full:
            return (one,)
        if t in inputs:
            return (inputs[t],)
        candidates = set()
        for i, x in enumerate(variables):
            check_budget()
            a, b = cofactor(t, i, 0), cofactor(t, i, 1)
            if a == b:
                continue
            diff = b & (full ^ a)
            # f = f0 OR (x AND f1), or f1 AND (x OR f0).
            # In the first expression f1 can be replaced by the upward
            # closure of f1\f0; dually f0 by complement(downward(diff)).
            # Both reduce support and preserve the exact truth table.
            for r in {b, upward(diff)}:
                for l, rr in product(solve(a), solve(r)):
                    candidates.add(combine("or", l, combine("and", x, rr)))
            for r in {a, full ^ downward(diff)}:
                for l, rr in product(solve(b), solve(r)):
                    candidates.add(combine("and", l, combine("or", x, rr)))
        return tuple(sorted(candidates, key=lambda e: (len(gates(e)), e))[:width])

    try:
        exprs = solve(target)
    except TimeoutError:
        return None
    for expr in exprs:
        code = []
        wires = {v: i for i, v in enumerate(variables)}
        masks = [m for m in high]

        def emit(e):
            if e in wires:
                return wires[e]
            if e[0] not in ("and", "or"):
                raise ValueError("unexpected constant in witness")
            a, b = emit(e[1]), emit(e[2])
            tt = ({0:0, 1:0, 2:0, 3:1} if e[0] == "and" else
                  {0:0, 1:1, 2:1, 3:1})
            wire = n + len(code)
            code.append((a, b, tt))
            masks.append(masks[a] & masks[b] if e[0] == "and" else masks[a] | masks[b])
            wires[e] = wire
            return wire

        out = emit(expr)
        if code and out == n + len(code) - 1 and masks[out] == target:
            return code
    return None

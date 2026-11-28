"""Fast constructive search for small monotone circuits.

The recursive decompositions are valid for monotone truth tables. Ranking
uses the number of distinct gates (DAG sharing), not the formula tree size.
This produces an independently audited upper-bound witness only: it never
claims minimum size or a formal lower bound.
"""
from functools import lru_cache
from itertools import product,combinations
import time

def synthesize(n, f, width=3, budget=None, decompose=False):
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
        if decompose:
            cof = [(cofactor(t,i,0),cofactor(t,i,1)) for i in range(n)]
            support = [i for i,(a,b) in enumerate(cof) if a != b]
            # Bi-decomposition: disjoint exclusive supports, common variables
            # permitted. Removing one essential variable from each side gives
            # the exact factors when the two restricted tables OR/AND to t.
            for i,j in combinations(support,2):
                for val,op in ((0,"or"),(1,"and")):
                    a,b=cof[i][val],cof[j][val]
                    if (a|b if val==0 else a&b)==t:
                        for l,r in product(solve(a),solve(b)):
                            candidates.add(combine(op,l,r))
            # Detect a monotone functional divisor g(A) which can replace A
            # by one variable in the remaining h. All nonconstant outer
            # slices must be the same g. Neither subproblem has full support.
            def restrict(tab,group,assignment):
                for pos,i in enumerate(group):
                    tab=cofactor(tab,i,(assignment>>pos)&1)
                return tab
            def substitute(e,var,rep):
                if e==var:return rep
                if e[0] in ("x","c"):return e
                return combine(e[0],substitute(e[1],var,rep),substitute(e[2],var,rep))
            for k in range(2,len(support)):
                for A in combinations(support,k):
                    check_budget()
                    B=[i for i in support if i not in A]
                    g=None; valid=True
                    for assignment in range(1<<len(B)):
                        part=restrict(t,B,assignment)
                        if part in (0,full):continue
                        if g is None:g=part
                        elif g!=part:
                            valid=False;break
                    if not valid or g is None:continue
                    rep=A[0]
                    a,b=restrict(t,A,0),restrict(t,A,(1<<len(A))-1)
                    h=(a&low[rep])|(b&high[rep])
                    if h==t or g==t:continue
                    for he,ge in product(solve(h),solve(g)):
                        candidates.add(substitute(he,variables[rep],ge))
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

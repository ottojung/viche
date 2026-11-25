"""Monotone witnesses for graph edge functions: OR of terms OR(A) AND OR(B), A x B complete in G.
Exact minimum of sum(|A| + |B|) over biclique covers (branch and bound), then identical OR sets are
built once.  Cost of the circuit = sum(|A| + |B|) - 1 - sharing savings.
"""
import itertools


def bicliques(n, edges):
    adj = [[False] * n for _ in range(n)]
    for u, v in edges:
        adj[u][v] = adj[v][u] = True
    eidx = {}
    for t, (u, v) in enumerate(edges):
        eidx[(min(u, v), max(u, v))] = t
    verts = sorted({u for e in edges for u in e})
    out = {}
    for assign in itertools.product((0, 1, 2), repeat=len(verts)):
        A = [v for v, s in zip(verts, assign) if s == 1]
        B = [v for v, s in zip(verts, assign) if s == 2]
        if not A or not B or min(A) > min(B):
            continue
        if all(adj[a][b] for a in A for b in B):
            mask = 0
            for a in A:
                for b in B:
                    mask |= 1 << eidx[(min(a, b), max(a, b))]
            out[(tuple(A), tuple(B))] = mask
    return [(A, B, m, len(A) + len(B)) for (A, B), m in out.items()]


def _by_edge(cands, E):
    by_edge = [[] for _ in range(E)]
    for c in cands:
        for t in range(E):
            if (c[2] >> t) & 1:
                by_edge[t].append(c)
    return by_edge


def best_cover(n, edges):
    cands = bicliques(n, edges)
    E = len(edges)
    allm = (1 << E) - 1
    by_edge = _by_edge(cands, E)
    for t in range(E):
        by_edge[t].sort(key=lambda c: (c[3] / bin(c[2]).count('1'), c[3]))
    best = [10 ** 9, None]
    maxcov = max(bin(c[2]).count('1') for c in cands)

    def rec(cov, cost, chosen):
        if cov == allm:
            if cost < best[0]:
                best[0], best[1] = cost, list(chosen)
            return
        rem = E - bin(cov).count('1')
        if cost + 2 * ((rem + maxcov - 1) // maxcov) >= best[0]:
            return
        t = (~cov & allm & -(~cov & allm)).bit_length() - 1
        for c in by_edge[t]:
            chosen.append(c)
            rec(cov | c[2], cost + c[3], chosen)
            chosen.pop()

    rec(0, 0, [])
    return best[1]


def all_covers(n, edges, slack=2, cap=2000):
    """Covers with cost <= best + slack (for sharing-aware selection)."""
    cands = bicliques(n, edges)
    E = len(edges)
    allm = (1 << E) - 1
    by_edge = _by_edge(cands, E)
    bound = sum(c[3] for c in best_cover(n, edges)) + slack
    res = []

    def rec(cov, cost, chosen):
        if len(res) >= cap:
            return
        if cov == allm:
            res.append(list(chosen))
            return
        if cost + 2 > bound:
            return
        t = (~cov & allm & -(~cov & allm)).bit_length() - 1
        for c in by_edge[t]:
            if cost + c[3] > bound:
                continue
            chosen.append(c)
            rec(cov | c[2], cost + c[3], chosen)
            chosen.pop()

    rec(0, 0, [])
    return res


def build(n, cover):
    """Gates (a, b, tt) for the cover, OR sets shared; tt as in onenot (mono: and / or)."""
    gates = []
    AND = {0: 0, 1: 0, 2: 0, 3: 1}
    OR = {0: 0, 1: 1, 2: 1, 3: 1}
    memo = {}

    def orset(S):
        S = tuple(sorted(S))
        if len(S) == 1:
            return S[0]
        if S in memo:
            return memo[S]
        sub = max((T for T in memo if set(T) < set(S)), key=len, default=None)
        if sub is not None:
            cur = memo[sub]
            rest = [v for v in S if v not in sub]
        else:
            cur = S[0]
            rest = list(S[1:])
        for v in rest:
            gates.append((cur, v, OR) if cur < v else (v, cur, OR))
            cur = n + len(gates) - 1
        memo[S] = cur
        return cur

    terms = []
    for A, B, m, c in cover:
        a = orset(A)
        b = orset(B)
        gates.append((min(a, b), max(a, b), AND))
        terms.append(n + len(gates) - 1)
    cur = terms[0]
    for t in terms[1:]:
        gates.append((cur, t, OR))
        cur = n + len(gates) - 1
    return gates


def witness(n, edges, f, evaluate):
    best = None
    for cover in all_covers(n, edges):
        g = build(n, cover)
        if best is None or len(g) < len(best):
            if all(evaluate(n, g, r) == f[r] for r in range(1 << n)):
                best = g
    return best

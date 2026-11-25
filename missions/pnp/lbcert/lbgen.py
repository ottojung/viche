#!/usr/bin/env python3
"""Certificate generator for the public `lb_cert` frontier-search engine (open-goat/pequalnp-proofs,
Apache-2.0; engine as in L_meta_7281). Mirrors `next`, `via`, `stepOK`, `rootOK` exactly.

Proves  ∀ s, HasCircuitSize n f s → lb ≤ s   (AND/OR/NOT fan-in-two circuits)
by exhaustively refuting every NatRun with cap = lb - 1 gates, up to the automorphisms of f.
"""
import itertools, sys, time

sys.setrecursionlimit(100000)


class Feasible(Exception):
    pass


class TooBig(Exception):
    pass


def isort(l):
    return sorted(l)


def tagU(ws, a, neg, ka):
    return 4 * ws.index(a) + 2 * int(neg) + int(ka)


def tagB(ws, a, b, conj, ka, kb):
    j = ws.index(b)
    return 48 + 8 * (j * (j + 1) // 2 + ws.index(a)) + 4 * int(conj) + 2 * int(ka) + int(kb)


def erase(l, x):
    l = list(l)
    l.remove(x)
    return l


def successors(m, slack, ws):
    for a in ws:
        ra = erase(ws, a)
        if slack >= 1:
            for neg in (False, True):
                w = a ^ m if neg else a
                yield tagU(ws, a, neg, False), [w] + ra
                if slack >= 2:
                    yield tagU(ws, a, neg, True), [w, a] + ra
        for b in ra:
            if a <= b:
                r = erase(ra, b)
                for conj in (False, True):
                    w = (a & b) if conj else (a | b)
                    yield tagB(ws, a, b, conj, False, False), [w] + r
                    if slack >= 1:
                        yield tagB(ws, a, b, conj, True, False), [w, a] + r
                        yield tagB(ws, a, b, conj, False, True), [w, b] + r
                    if slack >= 2:
                        yield tagB(ws, a, b, conj, True, True), [w, a, b] + r


class Engine:
    def __init__(self, n, y, pD, pM, G, maxstates=4000):
        self.n = n
        self.N = 1 << n
        self.m = (1 << self.N) - 1
        self.y = y
        self.pD = pD
        self.pM = pM
        self.G = G
        self.T = {}
        self.maxstates = maxstates

    def accD(self, d, ws):
        acc = 0
        for w in ws:
            acc |= w ^ (w >> d)
        return acc

    def accM(self, q, ws):
        acc = 0
        for w in ws:
            if not (w >> q) & 1:
                acc |= w
        return acc

    def via(self, t, ws):
        if len(ws) > t + 1:
            return False
        if t == 0 and sorted(ws) != [self.y]:
            return False
        for d, R in self.pD:
            if R & self.accD(d, ws) != R:
                return False
        if len(ws) == t + 1:
            for q, P in self.pM:
                if P & self.accM(q, ws) != P:
                    return False
        return True

    def act(self, pi, w):
        r = 0
        for k, p in enumerate(pi):
            if (w >> p) & 1:
                r |= 1 << k
        return r

    def canon(self, ws):
        best = isort(ws)
        bj = None
        for j, pi in enumerate(self.G):
            c = isort([self.act(pi, w) for w in ws])
            if c < best:
                best, bj = c, j
        return best, bj

    def explore(self, t, es):
        key = (t,) + tuple(es)
        if key in self.T:
            return
        if len(self.T) >= self.maxstates:
            raise TooBig(len(self.T))
        self.T[key] = None
        hints = []
        seen = {}
        slack = t + 1 - len(es)
        for tag, ys in successors(self.m, slack, es):
            tt = t - 1
            if not self.via(tt, ys):
                continue
            if tt == 0:
                raise Feasible()
            sy = isort(ys)
            k2 = (tt,) + tuple(sy)
            if k2 in seen:
                cj = seen[k2]
            else:
                c, j = self.canon(ys)
                self.explore(tt, c)
                cj = j
                seen[k2] = j
            if cj is not None:
                hints.append((tag, cj))
        hh, st = [], set()
        for tag, j in hints:
            if tag not in st:
                st.add(tag)
                hh.append((tag, j))
        self.T[key] = hh


def automorphisms(n, y):
    N = 1 << n
    G = []
    for sigma in itertools.permutations(range(n)):
        if list(sigma) == list(range(n)):
            continue
        pi = []
        for k in range(N):
            v = 0
            for i in range(n):
                if (k >> i) & 1:
                    v |= 1 << sigma[i]
            pi.append(v)
        e = Engine(n, y, [], [], [])
        if e.act(pi, y) == y:
            G.append(pi)
    return G


def make_pD(n, y, m):
    out = []
    for i in range(n):
        d = 1 << i
        R = (y ^ (y >> d)) & ~(m ^ (m >> d)) & m
        if R:
            out.append((d, R))
    return out


def make_pM(n, y, limit=8):
    N = 1 << n
    false_pts = [q for q in range(N) if not (y >> q) & 1]
    false_pts.sort(key=lambda q: -bin(q).count('1'))
    return [(q, y) for q in false_pts[:limit]]


def prsOK(m, y, pD, pM):
    for d, R in pD:
        if R & (y ^ (y >> d)) != R or R & (m ^ (m >> d)) != 0:
            return False
    for q, P in pM:
        if P & y != P or (y >> q) & 1:
            return False
    return True


def gen_y(n, y, lb, maxstates=4000, pm_limit=8, verbose=True):
    t0 = time.time()
    N = 1 << n
    m = (1 << N) - 1
    xs = [sum(1 << v for v in range(N) if (v >> i) & 1) for i in range(n)]
    pD = make_pD(n, y, m)
    pM = make_pM(n, y, pm_limit)
    assert prsOK(m, y, pD, pM)
    G = automorphisms(n, y)
    E = Engine(n, y, pD, pM, G, maxstates)
    cap = lb - 1
    roots = 0
    for r in range(len(xs) + 1):
        for zs in itertools.combinations(xs, r):
            zs = list(zs)
            if not zs or not E.via(cap, zs):
                continue
            roots += 1
            c, j = E.canon(zs)
            E.explore(cap, c)
    if verbose:
        print('n=%d lb=%d |G|=%d roots=%d states=%d time=%.1fs' % (n, lb, len(G), roots, len(E.T), time.time() - t0),
              file=sys.stderr)
    return dict(n=n, m=m, y=y, xs=xs, pD=pD, pM=pM, G=G, T=E.T, cap=cap, lb=lb)


def build_bt(items):
    if not items:
        return 'BT.lf'
    mid = len(items) // 2
    return '(BT.nd %s [%s] %s)' % (build_bt(items[:mid]), ','.join(map(str, items[mid])), build_bt(items[mid + 1:]))


def emit_data(d, chunks=6):
    keys = sorted([list(k) for k in d['T'].keys()])
    lines = []
    lines.append('def L_ : List ℕ := [%s]' % ','.join(map(str, range(1 << d['n']))))
    lines.append('def M_ : ℕ := %d' % d['m'])
    lines.append('def Y_ : ℕ := %d' % d['y'])
    lines.append('def XS_ : List ℕ := [%s]' % ','.join(map(str, d['xs'])))
    lines.append('def PD_ : List (ℕ × ℕ) := [%s]' % ','.join('(%d,%d)' % p for p in d['pD']))
    lines.append('def PM_ : List (ℕ × ℕ) := [%s]' % ','.join('(%d,%d)' % p for p in d['pM']))
    lines.append('')
    lines.append('def G_ : List (List ℕ) := [%s]' % ','.join('[%s]' % ','.join(map(str, pi)) for pi in d['G']))
    lines.append('')
    lines.append('-- the closed set of failing search states (%d states, up to %d symmetries)' % (len(keys), len(d['G'])))
    lines.append('noncomputable def T_cert : BT := %s' % build_bt(keys))
    lines.append('')
    k = max(1, min(chunks, len(keys)))
    size = (len(keys) + k - 1) // k
    parts = [keys[i * size:(i + 1) * size] for i in range(k)]
    parts = [p for p in parts if p]
    for i, p in enumerate(parts):
        ent = []
        for key in p:
            h = d['T'][tuple(key)]
            ent.append('([%s],[%s])' % (','.join(map(str, key)), ','.join('(%d,%d)' % th for th in h)))
        lines.append('noncomputable def K_%d : List (List ℕ × List (ℕ × ℕ)) := [%s]' % (i, ','.join(ent)))
    return lines, len(parts)


def balanced_append(names):
    if len(names) == 1:
        return names[0]
    mid = len(names) // 2
    return '(%s ++ %s)' % (balanced_append(names[:mid]), balanced_append(names[mid:]))


def balanced_all(names):
    if len(names) == 1:
        return names[0]
    mid = len(names) // 2
    return '(all_app %s %s)' % (balanced_all(names[:mid]), balanced_all(names[mid:]))


def emit_proof(d, nparts, module, statement, aux):
    lines = []
    for i in range(nparts):
        lines.append('lemma c_%d : K_%d.all (fun kh => stepOK M_ Y_ PD_ PM_ G_ T_cert kh.1 kh.2) = true := by decide +kernel' % (i, i))
    ks = ['K_%d' % i for i in range(nparts)]
    cs = ['c_%d' % i for i in range(nparts)]
    lines.append('set_option maxRecDepth 100000 in')
    lines.append('lemma hK_cert : T_cert.toList = %s.map Prod.fst := by decide +kernel' % balanced_append(ks))
    lines.append('set_option maxRecDepth 100000 in')
    lines.append('lemma hT_cert : ∀ x, T_cert.mem x = true → ∃ h, (stepOK M_ Y_ PD_ PM_ G_ T_cert) x h = true :=')
    lines.append('  cover (p := stepOK M_ Y_ PD_ PM_ G_ T_cert) T_cert _ hK_cert (%s)' % balanced_all(cs))
    lines.append('')
    lines.append('end %s' % aux)
    lines.append('')
    lines.append('open %s in' % aux)
    lines.append('theorem %s : %s := by' % (module, statement))
    lines.append('  exact lb_cert _ L_ M_ Y_ XS_ PD_ PM_ G_ T_cert %d %d rfl (by decide +kernel) (by decide +kernel) '
                 '(by decide +kernel) ⟨fun _ => false, fun _ => true, by decide⟩ (by decide +kernel) '
                 '(by decide +kernel) hT_cert (by decide +kernel)' % (d['cap'], d['lb']))
    return lines


def emit_data_compact(d, chunks=6, prefix='Z'):
    keys = sorted([list(k) for k in d['T'].keys()])
    wires = sorted({w for k in keys for w in k[1:]})
    B62 = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

    def b62(i):
        r = B62[i % 62]
        i //= 62
        while i:
            r = B62[i % 62] + r
            i //= 62
        return r
    name = {w: prefix + b62(i) for i, w in enumerate(wires)}
    lines = []
    lines.append('def L_ : List ℕ := [%s]' % ','.join(map(str, range(1 << d['n']))))
    lines.append('def M_ : ℕ := %d' % d['m'])
    lines.append('def Y_ : ℕ := %d' % d['y'])
    lines.append('def XS_ : List ℕ := [%s]' % ','.join(map(str, d['xs'])))
    lines.append('def PD_ : List (ℕ × ℕ) := [%s]' % ','.join('(%d,%d)' % p for p in d['pD']))
    lines.append('def PM_ : List (ℕ × ℕ) := [%s]' % ','.join('(%d,%d)' % p for p in d['pM']))
    lines.append('')
    lines.append('def G_ : List (List ℕ) := [%s]' % ','.join('[%s]' % ','.join(map(str, pi)) for pi in d['G']))
    lines.append('')
    for w in wires:
        lines.append('def %s : ℕ := 0x%x' % (name[w], w))
    lines.append('')

    def kstr(k):
        return '[%d%s]' % (k[0], ''.join(',' + name[w] for w in k[1:]))

    def bt(items):
        if not items:
            return 'Z_e'
        mid = len(items) // 2
        return '(Z_n %s %s %s)' % (bt(items[:mid]), kstr(items[mid]), bt(items[mid + 1:]))

    lines.append('def Z_n : BT → List ℕ → BT → BT := BT.nd')
    lines.append('def Z_e : BT := BT.lf')
    lines.append('-- the closed set of failing search states (%d states, up to %d symmetries)' % (len(keys), len(d['G'])))
    lines.append('noncomputable def T_cert : BT := %s' % bt(keys))
    lines.append('')
    k = max(1, min(chunks, len(keys)))
    size = (len(keys) + k - 1) // k
    nparts = 0
    for i in range(k):
        part = keys[i * size:(i + 1) * size]
        if not part:
            continue
        hs = ['[%s]' % ','.join('(%d,%d)' % th for th in d['T'][tuple(key)]) for key in part]
        lines.append('def H_%d : List (List (ℕ × ℕ)) := [%s]' % (i, ','.join(hs)))
        lines.append('noncomputable def K_%d : List (List ℕ × List (ℕ × ℕ)) := '
                     'List.zip ((T_cert.toList.drop %d).take %d) H_%d' % (i, i * size, len(part), i))
        nparts += 1
    return lines, nparts

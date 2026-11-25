#!/usr/bin/env python3
"""One-NOT family generator ("At fan-in two, one NOT gate saves nothing on edges ...").

Statement: every AND/OR/NOT fan-in-2 circuit with at most one NOT computing the edge function of a
graph can be replaced by an AND/OR circuit that is no longer.

Proof shape: that of the merged L-meta-14150 (Apache-2.0; it follows L-meta-8463 / L-meta-1449),
instantiated per graph:
  * a monotone witness circuit with M gates (biclique cover, else SAT with cadical);
  * no circuit with M-2 binary gates (NOTs free) separates the sampled row pairs, checked in the
    kernel by the template's live-set search;
  so a circuit with a NOT has >= M-1 binary gates + 1 NOT >= M gates; a NOT-free one is monotone.

Pairs: the critical pairs (x, x - e_i), f(x) = 1, f(x - e_i) = 0, at most 128 of them (wider words
trip Lean's `exponentiation.threshold`, and a global set_option is not allowed by the validators).
Kernel budget: the C search (lsearch.c) with the kernel's own pruning counts states; the kernel
manages ~2k states/s, so instances over STATE_CAP are refused (rc 3) instead of being compiled.
Files pass missions.pnp.validate: helpers are `lemma`, one `theorem`, no `noncomputable section`.

Deployed on marceline-dev at /home/lubko/pnp-infra/onenot (with lsearch built there and the
template ref_14150.lean = upstream lean/PEqualNP/Outside/L_meta_14150.lean); the relay handler
lb-handler.py routes one-NOT statements here and compiles the result before returning it.

usage: onenot.py <gid> <statement-file> <out.lean>      exit 0 ok, 3 approach fails, 2 error
"""
import os, re, sys, subprocess, tempfile, random, json, time, itertools

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
TEMPLATE = os.environ.get('ONENOT_TEMPLATE', os.path.join(HERE, 'ref_14150.lean'))
CADICAL = os.path.expanduser('~/.elan/toolchains/leanprover--lean4---v4.36.0/bin/cadical')
SAT_TIMEOUT = int(os.environ.get('ONENOT_SAT_TIMEOUT', '240'))
LIVE_TIMEOUT = int(os.environ.get('ONENOT_LIVE_TIMEOUT', '60'))
PAIR_TARGET = int(os.environ.get('ONENOT_PAIRS', '128'))
STATE_CAP = int(os.environ.get('ONENOT_STATE_CAP', '400000'))
MONO_STEP_TIMEOUT = int(os.environ.get('ONENOT_MONO_TIMEOUT', '20'))


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, file=sys.stderr, flush=True)


# ----------------------------------------------------------------------------- parsing
def parse(stmt):
    n = int(re.search(r'∀ x : Fin (\d+) → Bool', stmt).group(1))
    lst = re.search(r'\(\[([0-9, ]*)\] : List ℕ\)', stmt).group(1)
    nums = [int(t) for t in lst.split(',') if t.strip()]
    edges = [(nums[2 * i], nums[2 * i + 1]) for i in range(len(nums) // 2)]
    return n, edges


def truth(n, edges):
    return [int(any((r >> u) & 1 and (r >> v) & 1 for u, v in edges)) for r in range(1 << n)]


# ----------------------------------------------------------------------------- SAT (fallback witness)
class CNF:
    def __init__(self):
        self.nv = 0
        self.cl = []

    def var(self):
        self.nv += 1
        return self.nv

    def add(self, c):
        self.cl.append(c)

    def solve(self, timeout):
        with tempfile.NamedTemporaryFile('w', suffix='.cnf', delete=False) as fh:
            fh.write('p cnf %d %d\n' % (self.nv, len(self.cl)))
            fh.write(''.join(' '.join(map(str, c)) + ' 0\n' for c in self.cl))
            path = fh.name
        try:
            p = subprocess.run([CADICAL, '-q', path], capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return None, None
        finally:
            os.unlink(path)
        if p.returncode == 20:
            return False, None
        if p.returncode != 10:
            raise RuntimeError('cadical rc %d %s' % (p.returncode, p.stderr[-300:]))
        val = set()
        for line in p.stdout.splitlines():
            if line.startswith('v'):
                for t in line.split()[1:]:
                    x = int(t)
                    if x > 0:
                        val.add(x)
        return True, val


def circuit_sat(n, k, rows, f, mono, timeout=SAT_TIMEOUT):
    """Is there a circuit of k fan-in-2 gates (mono: AND/OR; else AND-type with free negations)
    whose last gate equals f (general: up to polarity) on rows?  Returns (status, gates)."""
    S = CNF()
    sel, T, V = [], [], []
    for i in range(k):
        m = n + i
        d = {}
        for a in range(m):
            for b in range(a + 1, m):
                d[(a, b)] = S.var()
        sel.append(d)
        vs = list(d.values())
        S.add(vs)
        for x, y in itertools.combinations(vs, 2):
            S.add([-x, -y])
        t = {pq: S.var() for pq in (1, 2, 3)}   # pq = 2*p + q, t00 = 0
        T.append(t)
        if mono:
            S.add([t[3]])
            S.add([-t[1], t[2]]); S.add([t[1], -t[2]])
        else:
            a1, a2, a3 = t[1], t[2], t[3]
            for s1, s2, s3 in ((0, 0, 0), (1, 1, 0), (1, 0, 1), (0, 1, 1)):
                S.add([a1 if s1 == 0 else -a1, a2 if s2 == 0 else -a2, a3 if s3 == 0 else -a3])
        V.append({r: S.var() for r in rows})
    for i in range(k):
        for (a, b), s in sel[i].items():
            for r in rows:
                for p in (0, 1):
                    la = []
                    if a < n:
                        if ((r >> a) & 1) != p:
                            continue
                    else:
                        la.append(-V[a - n][r] if p else V[a - n][r])
                    for q in (0, 1):
                        lb = list(la)
                        if b < n:
                            if ((r >> b) & 1) != q:
                                continue
                        else:
                            lb.append(-V[b - n][r] if q else V[b - n][r])
                        v = V[i][r]
                        if p == 0 and q == 0:
                            S.add([-s] + lb + [-v])
                        else:
                            tv = T[i][2 * p + q]
                            S.add([-s] + lb + [-tv, v])
                            S.add([-s] + lb + [tv, -v])
    for i in range(k - 1):
        S.add([s for j in range(i + 1, k) for (a, b), s in sel[j].items() if a == n + i or b == n + i])
    if mono:
        for r in rows:
            S.add([V[k - 1][r] if f[r] else -V[k - 1][r]])
    else:
        pol = S.var()
        for r in rows:
            v = V[k - 1][r]
            if f[r]:
                S.add([v, pol]); S.add([-v, -pol])
            else:
                S.add([-v, pol]); S.add([v, -pol])
    ok, val = S.solve(timeout)
    if not ok:
        return ok, None
    gates = []
    for i in range(k):
        (a, b), = [ab for ab, s in sel[i].items() if s in val]
        tt = {0: 0}
        for pq in (1, 2, 3):
            tt[pq] = int(T[i][pq] in val)
        gates.append((a, b, tt))
    return True, gates


def evaluate(n, gates, r):
    w = [(r >> j) & 1 for j in range(n)]
    for a, b, tt in gates:
        w.append(tt[2 * w[a] + w[b]])
    return w[-1]


def cegar(n, k, f, mono, seed_rows, rng, timeout=SAT_TIMEOUT):
    rows = sorted(set(seed_rows))
    while True:
        st, gates = circuit_sat(n, k, rows, f, mono, timeout)
        if st is None:
            return None, rows, None
        if not st:
            return False, rows, None
        flip = 0
        if not mono:
            r0 = rows[0]
            flip = evaluate(n, gates, r0) ^ f[r0]
        bad = [r for r in range(1 << n) if (evaluate(n, gates, r) ^ flip) != f[r]]
        if not bad:
            return True, rows, gates
        bad0 = [r for r in bad if not f[r]]
        bad1 = [r for r in bad if f[r]]
        add = ([rng.choice(bad0)] if bad0 else []) + ([rng.choice(bad1)] if bad1 else [])
        rows = sorted(set(rows) | set(add))


def seeds(n, edges, f):
    rows = {(1 << u) | (1 << v) for u, v in edges}
    for r in range(1 << n):      # maximal independent sets
        if not f[r] and all(f[r | (1 << j)] for j in range(n) if not (r >> j) & 1):
            rows.add(r)
    return rows


# ----------------------------------------------------------------------------- kernel search
def critical_pairs(n, f):
    """(x, x - e_i) with f(x) = 1, f(x - e_i) = 0 (Hamming 1, as in the merged files)."""
    return [(x, x ^ (1 << i)) for x in range(1 << n) if f[x]
            for i in range(n) if (x >> i) & 1 and not f[x ^ (1 << i)]]


def general_none(n, f, pairs, k, limit, timeout=None, pairs_only=True):
    """True: no circuit of k binary gates (NOTs free) separates the aligned pairs, decided by the C
    search with the kernel search's own pruning (pairs_only), so `limit` also caps the kernel work;
    False: such a circuit exists; None: over the limit / timeout."""
    P = len(pairs)
    rows = [a for a, b in pairs] + [b for a, b in pairs]
    full = (1 << (2 * P)) - 1
    words = [full ^ sum(((r >> i) & 1) << j for j, r in enumerate(rows)) for i in range(n)]
    inp = '%d %d %d %d\n%s\n' % (n, P, k, limit, '\n'.join('%x' % w for w in words))
    env = dict(os.environ)
    if pairs_only:
        env['LSEARCH_PAIRS_ONLY'] = '1'
    try:
        r = subprocess.run([os.path.join(HERE, 'lsearch')], input=inp, capture_output=True, text=True,
                           timeout=timeout or LIVE_TIMEOUT, env=env)
    except subprocess.TimeoutExpired:
        return None
    return {'none': True, 'found': False}.get(r.stdout.strip())


def count_kids(inputs, P, m):
    """len (allKids m inputs) of the template (mirrors rootsN / kidsL / kids0 / kidsG)."""
    full = (1 << P) - 1
    M120 = (1 << (2 * P)) - 1
    nsep = lambda x: ((x >> P) ^ x) & full
    total = 0
    n = len(inputs)
    for mask in range(1 << n):
        ws = [inputs[i] for i in range(n) if (mask >> i) & 1]
        L = len(ws)
        if L > m + 2:
            continue
        c = 0
        for w in ws:
            c |= nsep(w)
        if c != full:
            continue
        extra = m + 2 - L
        for i in range(L):
            for j in range(i + 1, L):
                a, b = ws[i], ws[j]
                base = 0
                for t, w in enumerate(ws):
                    if t != i and t != j:
                        base |= nsep(w)
                for z in (a & b, a | b, a & (M120 - b), b & (M120 - a)):
                    v = nsep(z) | base
                    if L == m + 2:
                        total += (v == full)
                    else:
                        total += (v == full) + ((v | nsep(a)) == full) + ((v | nsep(b)) == full) + (extra >= 2)
    return total


# ----------------------------------------------------------------------------- Lean
def lean_file(gid, stmt, n, pairs, M, wit, parts=24):
    P = len(pairs)
    W2 = 2 * P
    k = M - 2          # refuted binary gate count
    m = k - 1
    name = 'L_meta_' + gid.split('-')[-1]
    src = open(TEMPLATE, encoding='utf-8').read().split('\n')
    cut = next(i for i, l in enumerate(src) if l.startswith('def inputs : List W'))
    out = []
    for l in src[:cut]:
        if l.startswith('namespace PEqualNP.Outside.L_meta_'):
            l = 'namespace PEqualNP.Outside.' + name
        elif l.startswith('def M120'):
            l = 'def M120 : ℕ := 0x%x' % ((1 << W2) - 1)
        elif l.startswith('def M60'):
            l = 'def M60 : ℕ := 0x%x' % ((1 << P) - 1)
        elif l.startswith('def P60'):
            l = 'def P60 : ℕ := 0x%x' % (1 << P)
        elif l.startswith('def gN'):
            l = 'def gN : ℕ := 0x%x' % (((1 << P) - 1) << P)
        else:
            l = re.sub(r'\b112\b', str(W2), l)
            l = re.sub(r'\b56\b', str(P), l)
        out.append(l)
    for i, l in enumerate(out):
        if l.startswith('-- L-meta-1449), Apache-2.0'):
            out.insert(i + 1, '-- This file instantiates the merged L-meta-14150 (Apache-2.0) for another graph: new sampled')
            out.insert(i + 2, '-- rows, function, bound and monotone witness.')
            break
    # sampled rows: row j < P has f = 1, row P + j has f = 0 (pair j)
    rows = [a for a, b in pairs] + [b for a, b in pairs]
    comp = [sum(((r >> i) & 1) << j for j, r in enumerate(rows)) for i in range(n)]
    inputs = [((1 << W2) - 1) ^ w for w in comp]
    assert len(set(inputs)) == n, 'columns not distinct'
    lhs = stmt[:stmt.index("→ ∃ (gates' : List")]
    j = lhs.index('(List.ofFn x) = decide (')
    dec = lhs[j + len('(List.ofFn x) = '):].rstrip()
    assert dec.endswith(')')
    dec = dec[:-1]      # the closing paren of the hypothesis
    T = ['def inputs : List W := [%s]' % ', '.join('0x%x' % w for w in inputs), '',
         'def complementInputs : List W := inputs.map (fun w => ~~~w)', '',
         'def targetFun (x : Fin %d → Bool) : Bool :=' % n, '  ' + dec, '']
    rest = src[cut:]
    s0 = next(i for i, l in enumerate(rest) if l.startswith('set_option maxRecDepth 100000 in'))
    s1 = next(i for i, l in enumerate(rest) if l.startswith('theorem roots_ok'))
    for l in rest[s0:s1 - 2]:   # sample_rows .. bound_from_impossible
        l = re.sub(r'\b112\b', str(W2), l)
        l = l.replace('Fin 8 → Bool', 'Fin %d → Bool' % n).replace('(i : Fin 8)', '(i : Fin %d)' % n)
        l = l.replace('complementInputs.length = 8', 'complementInputs.length = %d' % n)
        T.append(l)
    T += ['set_option maxRecDepth 32000 in', 'set_option maxHeartbeats 0 in', 'theorem roots_ok :',
          '    (rootsN (%d + 1) (inputs.map BitVec.toNat)).all (fun ws => !nisGoal ws) = true := by' % m,
          '  decide +kernel', '']
    nk = count_kids(inputs, P, m)
    chunk = max(1, -(-nk // parts))
    np_ = max(1, -(-nk // chunk))
    log(gid, 'allKids', nk, 'parts', np_, 'chunk', chunk)
    for p in range(np_):
        T += ['set_option maxRecDepth 32000 in', 'set_option maxHeartbeats 0 in', 'theorem part_%d :' % p]
        if p < np_ - 1:
            T.append('    (((allKids %d (inputs.map BitVec.toNat)).drop %d).take %d).all (dead %d) = true := by'
                     % (m, p * chunk, chunk, m))
        else:
            T.append('    ((allKids %d (inputs.map BitVec.toNat)).drop %d).all (dead %d) = true := by'
                     % (m, p * chunk, m))
        T.append('  decide +kernel')
    T.append('')
    chain = 'part_%d' % (np_ - 1)
    for p in range(np_ - 2, -1, -1):
        chain = 'all_chunk _ _ %d %d part_%d (%s)' % (p * chunk, chunk, p, chain)
    T += ['theorem kids_ok : (allKids %d (inputs.map BitVec.toNat)).all (dead %d) = true :=' % (m, m),
          '  ' + chain, '',
          'theorem no_d_binary (t : W) (ht : t = goal ∨ t = ~~~goal)',
          '    (run : build basicOps t %d inputs.toFinset) : False :=' % k,
          '  refute %d inputs (by decide) roots_ok kids_ok t ht run' % m, '',
          'def wgates : List Gate :=',
          '  [%s]' % ', '.join('⟨.%s, [%d, %d]⟩' % ('or' if tt[1] else 'and', a, b) for a, b, tt in wit), '',
          'def wout : ℕ := %d' % (n + len(wit) - 1), '',
          'theorem witness_fits : ∀ g ∈ wgates, (g.op = GateOp.and ∨ g.op = GateOp.or) ∧ g.inputs.length ≤ 2 := by',
          '  simp [wgates]', '',
          'set_option maxRecDepth 32000 in', 'set_option maxHeartbeats 0 in',
          'theorem witness_eval : ∀ x : Fin %d → Bool, Circuit.eval ⟨wgates, wout⟩ (List.ofFn x) = targetFun x := by' % n,
          '  decide +kernel', '',
          'end PEqualNP.Outside.' + name, '']
    Q = 'PEqualNP.Outside.' + name
    T.append('theorem %s : %s := by' % (Q, stmt))
    T.append('''  intro gates o fits _ computes
  by_cases hasNot : ∃ g ∈ gates, g.op = PEqualNP.CircuitLowerBounds.GateOp.not
  · obtain ⟨g, mem, op⟩ := hasNot
    have short : Q.binaryCost gates < gates.length :=
      (List.length_filter_lt_length_iff_exists
        (p := Q.isBinary)).mpr
        ⟨g, mem, by simp [Q.isBinary, op]⟩
    have bound := Q.bound_from_impossible
      KK Q.no_d_binary gates o fits computes
    refine ⟨Q.wgates, Q.wout, Q.witness_fits, ?_, Q.witness_eval⟩
    change MM ≤ gates.length
    omega
  · refine ⟨gates, o, ?_, Nat.le_refl _, computes⟩
    intro g mem
    obtain ⟨op, cap⟩ := fits g mem
    exact ⟨op.elim Or.inl (fun h => h.elim Or.inr (fun eq => (hasNot ⟨g, mem, eq⟩).elim)), cap⟩'''
             .replace('Q.', Q + '.').replace('KK', str(k)).replace('MM', str(M)))
    T.append('')
    lines = '\n'.join(out + T).split('\n')
    # the validators want exactly one `theorem`: helpers become Mathlib `lemma`s
    last = max(i for i, l in enumerate(lines) if l.startswith('theorem PEqualNP.Outside.'))
    for i in range(last):
        lines[i] = re.sub(r'^(\s*)(private |protected )?theorem\b', r'\1\2lemma', lines[i])
    # `noncomputable section X` is not a scope line the town validator understands: plain section,
    # its definitions marked noncomputable one by one (same elaboration)
    inside = False
    for i in range(last):
        l = lines[i]
        mm = re.match(r'^noncomputable section (\w+)\s*$', l)
        if mm:
            lines[i] = 'section ' + mm.group(1)
            inside = mm.group(1)
            continue
        if inside and l.strip() == 'end ' + inside:
            inside = False
            continue
        if inside:
            l = re.sub(r'^(private |protected )?def\b', lambda x: 'noncomputable ' + (x.group(1) or '') + 'def', l)
            lines[i] = re.sub(r'^(private |protected )?abbrev\b', lambda x: 'noncomputable ' + (x.group(1) or '') + 'abbrev', l)
    if lines[0].strip() != 'import Mathlib':
        lines.insert(0, 'import Mathlib')
    return '\n'.join(lines)


# ----------------------------------------------------------------------------- driver
def solve(gid, stmt, seed=1):
    """Monotone witness of M gates (biclique cover, then SAT for M-1) and no circuit of M-2 binary
    gates on the critical pairs, within the kernel budget."""
    rng = random.Random(seed)
    n, edges = parse(stmt)
    f = truth(n, edges)
    sd = seeds(n, edges, f)
    t0 = time.time()
    pairs = critical_pairs(n, f)
    import biclique
    wit = biclique.witness(n, edges, f, evaluate)
    if not wit:
        return None, 'no biclique witness'
    M = len(wit)
    tried_smaller = False
    while True:
        r = general_none(n, f, pairs, M - 2, STATE_CAP)
        log(gid, 'witness', M, 'general', M - 2, {True: 'none', False: 'found', None: 'over budget'}[r],
            '%.0fs' % (time.time() - t0))
        if r:
            return finish(gid, n, f, pairs, M, wit, rng, t0)
        if tried_smaller and r is False:
            return None, 'a general circuit with %d binary gates exists; witness %d' % (M - 2, M)
        st, rows, w2 = cegar(n, M - 1, f, True, sd, rng, timeout=MONO_STEP_TIMEOUT)
        log(gid, 'mono', M - 1, st, '%.0fs' % (time.time() - t0))
        if not st:
            return None, ('kernel search over budget at %d gates' % (M - 2) if r is None else
                          'a general circuit with %d binary gates exists; no monotone %d found' % (M - 2, M - 1))
        M, wit, tried_smaller = M - 1, w2, True


def finish(gid, n, f, pairs, M, wit, rng, t0):
    keep = pairs
    if len(pairs) > PAIR_TARGET:
        # keep the edge rows with their one-vertex partners, then random pairs, within the budget
        keep = None
        base = [p for p in pairs if bin(p[0]).count('1') == 2]
        rest = [p for p in pairs if p not in set(base)]
        for _ in range(8):
            trial = (base + rng.sample(rest, max(0, PAIR_TARGET - len(base))))[:PAIR_TARGET]
            if general_none(n, f, trial, M - 2, STATE_CAP):
                keep = trial
                break
        if keep is None:
            return None, 'no %d-pair sample within the kernel budget' % PAIR_TARGET
    log(gid, 'ok M', M, 'pairs', len(keep), 'of', len(pairs), '%.0fs' % (time.time() - t0))
    return dict(n=n, M=M, k=M - 2, wit=wit, pairs=keep), None


def main():
    gid, sf, out = sys.argv[1:4]
    stmt = open(sf, encoding='utf-8').read().strip()
    try:
        res, why = solve(gid, stmt)
    except Exception as e:
        log('error', repr(e))
        sys.exit(2)
    if res is None:
        log(gid, 'skip:', why)
        print(json.dumps({'status': 'fail', 'why': why}))
        sys.exit(3)
    text = lean_file(gid, stmt, res['n'], res['pairs'], res['M'], res['wit'],
                     parts=int(os.environ.get('ONENOT_PARTS', '24')))
    open(out, 'w', encoding='utf-8').write(text)
    print(json.dumps({'status': 'ok', 'M': res['M'], 'P': len(res['pairs'])}))


if __name__ == '__main__':
    main()

"""Reusable engine for the six-input monotone-vs-general family, using the
merged L-meta-40311 core-search shape (Apache-2.0; see UPSTREAM-LICENSE.txt).

Public entry points:
  parse(statement) -> (n, f, T) or None
  solve(gid, statement) -> (lean_text, None) or (None, reason)
"""
import os, re, sys, time, random

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    import monotone_witness as _mw  # noqa: E402
except Exception:
    _mw = None
sys.path.insert(0, os.path.join(HERE, '..', '..', 'onenot'))
try:
    import onenot as _onenot  # noqa: E402
except Exception:
    _onenot = None

# strict bounded table literal (mirrors missions.pnp.lbcert.lbparse.table_literal)
def _table_literal(n, body, var='x'):
    if not 1 <= n <= 8:
        return None
    b = re.sub(r'\s+', ' ', body.strip())
    suffix = r'\(∑ i : Fin %d, if %s i then 2 \^ \(i : ℕ\) else 0\)' % (n, re.escape(var))
    m = re.fullmatch(r'Nat\.testBit\s+\((\d{1,20})\s*\*\s*2\s*\^\s*32\s*\+\s*(\d{1,10})\)\s+' + suffix, b)
    if m:
        hi, lo = int(m.group(1)), int(m.group(2))
        if lo >= 2**32:
            return None
        val = hi * 2**32 + lo
    else:
        m = re.fullmatch(r'Nat\.testBit\s+\(?(\d{1,20})\)?\s+' + suffix, b)
        if not m:
            return None
        val = int(m.group(1))
    return val if val.bit_length() <= (1 << n) else None

TEMPLATE = os.path.join(HERE, 'ref_40311.lean')
STATE_CAP = int(os.environ.get('SIXCORE_STATE_CAP', '400000'))
SAT_TIMEOUT = int(os.environ.get('SIXCORE_SAT_TIMEOUT', '120'))
MONO_TIMEOUT = int(os.environ.get('SIXCORE_MONO_TIMEOUT', '30'))
PAIR_TARGET = 128

# ---- search port (faithful to L-meta-40311) ----
M256 = (1 << 256) - 1
M128 = (1 << 128) - 1
GOAL = M128 << 128

def _sep(w): return ((w >> 128) ^ w) & M128
def _cuts(ws):
    c = 0
    for w in ws: c |= _sep(w)
    return c
def _ops(a, b):
    return [a & b, a | b, a & (~b & M256), b & (~a & M256)]
def _canon(ws):
    out = []
    for x in ws:
        i = 0
        while i < len(out) and out[i] <= x: i += 1
        out.insert(i, x)
    return out


def _search_with_cap(k, rows, cap):
    """Return (result_bool, states_used). Raises BudgetExceeded if cap hit."""
    states = [0]
    class Budget(Exception):
        pass
    def opt(kk, extra, ws):
        states[0] += 1
        if states[0] > cap:
            raise Budget()
        t = tuple(ws)
        if t == (GOAL,) or t == (M128,):  # GOAL or ~GOAL
            return True
        if kk == 0:
            return False
        L = len(ws)
        for i in range(L):
            for j in range(i + 1, L):
                a, b = ws[i], ws[j]
                r = [ws[t] for t in range(L) if t != i and t != j]
                base = 0
                for w in r: base |= _sep(w)
                sa, sb = _sep(a), _sep(b)
                for z in _ops(a, b):
                    v = _sep(z) | base
                    if v == M128 and opt(kk - 1, extra, _canon([z] + r)):
                        return True
                    if extra and ((v | sa) == M128) and opt(kk - 1, extra - 1, _canon([z, a] + r)):
                        return True
                    if extra and ((v | sb) == M128) and opt(kk - 1, extra - 1, _canon([z, b] + r)):
                        return True
                    if extra >= 2 and ((v | sa | sb) == M128) and opt(kk - 1, extra - 2, _canon([z, a, b] + r)):
                        return True
        return False
    def search(n, inputs):
        for mask in range(1 << len(inputs)):
            ws = [inputs[i] for i in range(len(inputs)) if (mask >> i) & 1]
            if len(ws) <= n + 1 and _cuts(ws) == M128 and opt(n, n + 1 - len(ws), _canon(ws)):
                return True, states[0]
        return False, states[0]
    try:
        r, st = search(k, rows)
        return r, st
    except Budget:
        return None, states[0]


# ---- parsing ----
HEAD_RE = re.compile(r'^∀ s : ℕ, PEqualNP\.MetaComplexity\.HasCircuitSize (\d+) \(fun x : Fin (\d+) → Bool => (.*?)\) s → ∃ C : PEqualNP\.CircuitLowerBounds\.Circuit, PEqualNP\.MetaComplexity\.Monotone2 C ∧ C\.size ≤ s ∧ ∀ x : Fin \d+ → Bool, C\.eval \(List\.ofFn x\) = (.*)$', re.S)

def parse(stmt):
    text = re.sub(r'\s+', ' ', stmt.strip())
    if text.startswith('(') and text.endswith(')'):
        text = text[1:-1].strip()
    m = HEAD_RE.match(text)
    if not m or m.group(1) != m.group(2) or m.group(3).strip() != m.group(4).strip():
        return None
    n = int(m.group(1))
    if n != 6:
        return None
    body = m.group(3).strip()
    # prefer canonical lbparse.table_literal if available
    try:
        import lbparse as _lp
        tl = getattr(_lp, 'table_literal', None)
    except Exception:
        tl = None
    if tl is None:
        tl = _table_literal
    T = tl(n, body, 'x')
    if T is None:
        return None
    f = [(T >> r) & 1 for r in range(1 << n)]
    return n, body, f, T


def matches(statement):
    return parse(statement) is not None


def solve(gid, stmt, budget=600):
    p = parse(stmt)
    if p is None:
        return None, 'statement shape not recognised'
    n, body, f, T = p
    if any(f[r] and not f[r | (1 << i)] for r in range(1 << n) for i in range(n)):
        return None, 'function not monotone'
    t0 = time.monotonic()
    deadline = t0 + budget
    # fast constructive witness
    wit = None
    if _mw is not None:
        wit = _mw.synthesize(n, f, width=3)
    if wit is None and _onenot is not None:
        rng = random.Random(1)
        rows0 = list(range(1 << n))
        for size in range(2, 4 * n + 4):
            if time.monotonic() >= deadline - 5:
                break
            st, _, cand = _onenot.cegar(n, size, f, True, rows0, rng,
                                        timeout=min(30, deadline - time.monotonic() - 4))
            if st is True:
                wit = cand
                break
            if st is None:
                break
    if not wit:
        return None, 'no monotone witness found'
    if not all(_onenot.evaluate(n, wit, r) == f[r] for r in range(1 << n)) if _onenot else True:
        return None, 'monotone witness audit failed'
    M = len(wit)
    # critical pairs -> 128 columns
    if _onenot is None:
        return None, 'onenot helper unavailable'
    pairs = _onenot.critical_pairs(n, f)
    if not pairs:
        return None, 'no critical pairs'
    P = PAIR_TARGET
    seq = (pairs + [pairs[i % len(pairs)] for i in range(P - len(pairs))])[:P]
    assignments = [a for a, b in seq] + [b for a, b in seq]
    rows = [sum(((assignments[k] >> i) & 1) << k for k in range(2 * P)) for i in range(n)]
    for k in range(2 * P):
        x = assignments[k]
        if f[x] != (1 if k < P else 0):
            return None, 'sample polarity mismatch at column %d' % k
    k_refute = M - 2
    if k_refute < 1:
        k_refute = 1
    # honor budget for search
    if time.monotonic() >= deadline - 2:
        return None, 'budget exhausted before search'
    res, states = _search_with_cap(k_refute, rows, STATE_CAP)
    if res is None:
        return None, 'kernel search over budget (%d states)' % states
    if res is True:
        return None, 'a circuit with %d binary gates separates the sample' % k_refute
    name = 'L_meta_' + gid.split('-')[-1]
    text = _emit(gid, stmt, n, body, f, T, rows, M, wit, k_refute, name)
    return text, None


def _emit(gid, stmt, n, body, f, T, rows, M, wit, k_refute, name):
    src = open(TEMPLATE, encoding='utf-8').read().split('\n')
    out = []
    for l in src:
        if l.startswith('namespace PEqualNP.Outside.L_meta_'):
            l = 'namespace PEqualNP.Outside.' + name
        out.append(l)
    # instance-specific part
    W2 = 2 * PAIR_TARGET
    gates = ', '.join('⟨.%s, [%d, %d]⟩' % ('or' if tt[1] else 'and', a, b) for a, b, tt in wit)
    row_words = ',\n  '.join('0x%016x#64 ++ 0x%016x#64 ++ 0x%016x#64 ++ 0x%016x#64' % (
        (rows[i] >> 192) & ((1 << 64) - 1),
        (rows[i] >> 128) & ((1 << 64) - 1),
        (rows[i] >> 64) & ((1 << 64) - 1),
        rows[i] & ((1 << 64) - 1)) for i in range(n))
    Texpr = body.split('Nat.testBit ')[1].split(' ')[0] if 'Nat.testBit ' in body else str(T)
    # Actually body is "Nat.testBit (expr) (sum...)"; reconstruct target as given
    target_expr = body
    MM = M
    K = k_refute
    inst = r'''
def target (x : Fin N → Bool) : Bool :=
  BODY

def rows : List W :=
  [ROWS]

def witness : Circuit :=
  ⟨[GATES], OUT⟩

set_option maxRecDepth 1000000 in
set_option maxHeartbeats 0 in
theorem reject : search K rows = false := by
  decide +kernel

set_option maxRecDepth 1000000 in
set_option maxHeartbeats 0 in
theorem witness_ok : ∀ x : Fin N → Bool, Circuit.eval witness (List.ofFn x) = target x := by
  decide +kernel

set_option maxRecDepth 1000000 in
set_option maxHeartbeats 0 in
theorem sample_ok : ∀ k : Fin W2, target (fun i => (rows.getD i.val 0)[k.val]) = (~~~goal)[k.val] := by
  decide +kernel

theorem solve (s : ℕ) (hs : HasCircuitSize N target s) :
    ∃ C : Circuit, Monotone2 C ∧ C.size ≤ s ∧ ∀ x : Fin N → Bool, C.eval (List.ofFn x) = target x := by
  obtain ⟨C, fits, size, computes⟩ := hs
  by_cases hasNot : ∃ g ∈ C.gates, g.op = GateOp.not
  · obtain ⟨g, mem, op⟩ := hasNot
    have short : binaryCost C.gates < C.size :=
      (List.length_filter_lt_length_iff_exists (p := isBinary)).mpr
        ⟨g, mem, by simp [isBinary, op]⟩
    have bound := bound_from_search rows rfl (by decide) reject sample_ok C.gates C.output fits computes
    refine ⟨witness, by simp [Monotone2, witness], ?_, witness_ok⟩
    change MM ≤ s
    omega
  · refine ⟨C, ?_, size, computes⟩
    intro g mem
    obtain ⟨op, cap⟩ := fits g mem
    change g.op = .and ∨ g.op = .or ∨ g.op = .not at op
    exact ⟨op.elim Or.inl (fun h => h.elim Or.inr (fun eq => (hasNot ⟨g, mem, eq⟩).elim)), cap⟩

end PEqualNP.Outside.NAME

theorem PEqualNP.Outside.NAME :
    STMT := by
  exact PEqualNP.Outside.NAME.solve
'''
    inst = (inst.replace('BODY', target_expr)
             .replace('ROWS', row_words)
             .replace('GATES', gates)
             .replace('OUT', str(n + len(wit) - 1))
             .replace('W2', str(W2))
             .replace('MM', str(MM))
             .replace('NAME', name)
             .replace('STMT', stmt.strip()))
    inst = re.sub(r'\\bK\\b', str(K), inst)
    inst = re.sub(r'\\bN\\b', str(n), inst)
    # fix namespace in prefix? already handled; also replace remaining L_meta_40311 refs in prefix already none
    lines = '\n'.join(out).split('\n') + inst.split('\n')
    idxs = [i for i, l in enumerate(lines) if 'theorem PEqualNP.Outside.' in l]
    last = idxs[-1] if idxs else len(lines) - 1
    for i in range(last):
        lines[i] = re.sub(r'^(\s*)(private |protected )?theorem\b', r'\1\2lemma', lines[i])
    if lines[0].strip() != 'import Mathlib':
        # ensure import Mathlib present (prefix imports PEqualNP.Defs only)
        lines.insert(0, 'import Mathlib')
    if 'import PEqualNP.Defs' not in lines[:5]:
        lines.insert(1, 'import PEqualNP.Defs')
    return '\n'.join(lines)


def main():
    import argparse
    # engine module also usable as library; CLI for debugging
    pass
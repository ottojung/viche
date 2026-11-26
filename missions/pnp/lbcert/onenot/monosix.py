#!/usr/bin/env python3
"""Monotone-equals-general family ("Table N: six-input monotone f ... every fan-in-two AND/OR/NOT circuit"):
  ∀ s, HasCircuitSize n f s → ∃ C, Monotone2 C ∧ C.size ≤ s ∧ ∀ x, C.eval … = f x.

Proof shape: that of the merged L-meta-13175 (Apache-2.0; live-set search of L-meta-8463/1449):
a monotone circuit of M gates (SAT/cadical, exact minimum), and no circuit with M-2 binary gates
(NOTs free) separating sampled row pairs (kernel `search`), so a circuit with a NOT has >= M gates and
a NOT-free one is already monotone.  Runs locally beside onenot.py (template
ref_13175.lean = upstream lean/PEqualNP/Outside/L_meta_13175.lean); the retired relay handler is
no longer used and exact checks go through the managed local compiler.
Typical: generation ~5 s, compile ~5 s.

usage: monosix.py GID STATEMENT_FILE OUT.lean      exit 0 ok, 3 beyond the method, 2 error
"""
import json, os, random, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import onenot  # noqa: E402  (SAT witness search, critical pairs, C live search)

TEMPLATE = os.environ.get('MONOSIX_TEMPLATE', os.path.join(HERE, 'ref_13175.lean'))
STATE_CAP = int(os.environ.get('MONOSIX_STATE_CAP', '400000'))
PAIR_MAX = 120
log = onenot.log

HEAD_RE = re.compile(r'^∀ s : ℕ, PEqualNP\.MetaComplexity\.HasCircuitSize (\d+) \(fun x : Fin (\d+) → Bool => (.*?)\) s → ∃ C : PEqualNP\.CircuitLowerBounds\.Circuit, PEqualNP\.MetaComplexity\.Monotone2 C ∧ C\.size ≤ s ∧ ∀ x : Fin \d+ → Bool, C\.eval \(List\.ofFn x\) = (.*)$', re.S)


def parse(stmt):
    m = HEAD_RE.match(re.sub(r'\s+', ' ', stmt.strip()))
    if not m or m.group(1) != m.group(2) or m.group(3).strip() != m.group(4).strip():
        return None
    n, body = int(m.group(1)), m.group(3).strip()
    t = re.fullmatch(r'Nat\.testBit \((.*?)\) \(∑ i : Fin %d, if x i then 2 \^ \(i : ℕ\) else 0\)' % n, body)
    if not t:
        return None
    expr = t.group(1).replace(' ', '')
    if not re.fullmatch(r'[0-9*+^()]+', expr):
        return None
    T = eval(expr.replace('^', '**'), {'__builtins__': {}})
    f = [(T >> r) & 1 for r in range(1 << n)]
    return n, body, f


def lean(gid, stmt, n, body, f, pairs, M, wit):
    P = len(pairs)
    W2 = 2 * P
    k = M - 2
    name = 'L_meta_' + gid.split('-')[-1]
    src = open(TEMPLATE, encoding='utf-8').read().split('\n')
    cut = next(i for i, l in enumerate(src) if l.startswith('def target'))
    out = []
    for l in src[:cut]:
        if l.startswith('namespace PEqualNP.Outside.L_meta_'):
            l = 'namespace PEqualNP.Outside.' + name
        else:
            l = re.sub(r'\b64\b', str(W2), l)
            l = re.sub(r'\b32\b', str(P), l)
        out.append(l)
    out.insert(next(i for i, l in enumerate(out) if l.startswith('namespace ')) + 1,
               '\n-- Instantiates the merged L-meta-13175 (Apache-2.0) for this function: sampled rows, bound and witness.')
    rows = [a for a, b in pairs] + [b for a, b in pairs]
    words = [sum(((r >> i) & 1) << j for j, r in enumerate(rows)) for i in range(n)]
    assert len(set(words)) == n
    gates = ', '.join('⟨.%s, [%d, %d]⟩' % ('or' if tt[1] else 'and', a, b) for a, b, tt in wit)
    T = '''def target (x : Fin N → Bool) : Bool :=
  BODY

theorem bound_from_search (inputs : List W) (width : inputs.length = N)
    (nd : inputs.Nodup) (reject : search K inputs = false)
    (sample : ∀ k : Fin W2,
      target (fun i => (inputs.getD i.val 0)[k.val]) = (~~~goal)[k.val])
    (gs : List Gate) (o : ℕ) (hg : ∀ g ∈ gs, legal g)
    (he : ∀ x : Fin N → Bool, Circuit.eval ⟨gs,o⟩ (List.ofFn x) = target x) :
    K < binaryCost gs := by
  by_contra! low
  have init : ∀ u ∈ inputs, holds inputs.toFinset u := by
    intro u hu
    exact .inr (.inr ⟨u, List.mem_toFinset.mpr hu, .inl rfl⟩)
  have evaluate (k : Fin W2) :
      (gs.foldl step (inputs.map (bit k))).getD o false = bit k (~~~goal) := by
    let x (i : Fin N) : Bool := bit k (inputs.getD i.val 0)
    have same : List.ofFn x = inputs.map (bit k) := by
      apply List.ext_getElem
      · simp [width]
      · intro i hi hj
        have hlt : i < inputs.length := by simpa using hj
        simp only [List.getElem_ofFn, List.getElem_map, x, List.getD_eq_getElem?_getD,
          List.getElem?_eq_getElem hlt, Option.getD_some]
    change Circuit.eval ⟨gs,o⟩ (inputs.map (bit k)) = bit k (~~~goal)
    rw [← same, he]
    exact sample k
  obtain ⟨t, ht, run⟩ := compile gs o hg inputs inputs.toFinset init evaluate
  have lift {a b : ℕ} (h : a ≤ b) (hr : build basicOps t a inputs.toFinset) :
      build basicOps t b inputs.toFinset := by
    induction h with
    | refl => exact hr
    | step _ ih => exact Or.inl ih
  exact Bool.noConfusion (reject.symm.trans (search_complete ht K inputs nd (lift low run)))

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
    T = (T.replace('BODY', body).replace('ROWS', ', '.join('0x%x' % w for w in words))
          .replace('GATES', gates).replace('OUT', str(n + len(wit) - 1))
          .replace('W2', str(W2)).replace('MM', str(M)).replace('NAME', name)
          .replace('STMT', stmt.strip()))
    T = re.sub(r'\bK\b', str(k), T)
    T = re.sub(r'\bN\b', str(n), T)
    lines = '\n'.join(out).split('\n') + T.split('\n')
    last = max(i for i, l in enumerate(lines) if l.startswith('theorem PEqualNP.Outside.'))
    for i in range(last):
        lines[i] = re.sub(r'^(\s*)(private |protected )?theorem\b', r'\1\2lemma', lines[i])
    if lines[0].strip() != 'import Mathlib':
        lines.insert(0, 'import Mathlib')
    return '\n'.join(lines)


def solve(gid, stmt):
    p = parse(stmt)
    if not p:
        return None, 'statement shape not recognised'
    n, body, f = p
    if any(f[r] and not f[r | (1 << i)] for r in range(1 << n) for i in range(n)):
        return None, 'function not monotone'
    t0 = time.time()
    rng = random.Random(1)
    rows = [r for r in range(1 << n)]
    M = wit = None
    for s in range(1, 4 * n + 4):
        st, _, g = onenot.cegar(n, s, f, True, rows, rng, timeout=120)
        if st is None:
            return None, 'monotone witness search timed out at %d' % s
        if st:
            M, wit = s, g
            break
    log(gid, 'monotone size', M, '%.0fs' % (time.time() - t0))
    pairs = onenot.critical_pairs(n, f)
    if len(pairs) > PAIR_MAX:
        pairs = pairs[:PAIR_MAX]
    r = onenot.general_none(n, f, pairs, M - 2, STATE_CAP)
    log(gid, 'general', M - 2, {True: 'none', False: 'found', None: 'over budget'}[r], 'pairs', len(pairs))
    if not r:
        return None, ('a circuit with %d binary gates exists on the sample: one NOT may save a gate' % (M - 2)
                      if r is False else 'kernel search over budget')
    return lean(gid, stmt, n, body, f, pairs, M, wit), None


def main():
    gid, sf, out = sys.argv[1:4]
    stmt = open(sf, encoding='utf-8').read().strip()
    try:
        text, why = solve(gid, stmt)
    except Exception as e:
        log('error', repr(e))
        sys.exit(2)
    if text is None:
        log(gid, 'skip:', why)
        print(json.dumps({'status': 'fail', 'why': why}))
        sys.exit(3)
    open(out, 'w', encoding='utf-8').write(text)
    print(json.dumps({'status': 'ok'}))


if __name__ == '__main__':
    main()

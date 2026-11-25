#!/usr/bin/env python3
"""Constructive circuit-witness generator for six-input one-NOT statements.

Statement shape (from radar BACKLOG family 1):
  ∃ C : Circuit, FanInTwo C ∧ (∃ g ∈ C.gates, g.op = .not ∧ g.inputs.length = 1)
    ∧ C.size ≤ K ∧ ∀ x : Fin n → Bool, C.eval (List.ofFn x) = Nat.testBit T (∑ i, ...)

Method: beam search over wires (64-bit truth-table masks) building fan-in-two gates
AND/OR/NOT up to K gates, keeping the most target-correlated states; emit the merged
proof shape (concrete witness + gate-kind/size/eval `decide +kernel` closure).
Exit 3 (refuse) when no circuit within bound is found.  Pure Python, <=600 s.
"""
import itertools
import random
import re
import sys

MATCH = (r"∃ C : PEqualNP\.CircuitLowerBounds\.Circuit, "
         r"PEqualNP\.MetaComplexity\.FanInTwo C ∧ "
         r"\(∃ g ∈ C\.gates, g\.op = PEqualNP\.CircuitLowerBounds\.GateOp\.not ∧ "
         r"g\.inputs\.length = 1\) ∧ C\.size ≤ \d+ ∧")


def parse(stmt):
    n = int(re.search(r"∀ x : Fin (\d+) → Bool", stmt).group(1))
    bound = int(re.search(r"C\.size ≤ (\d+)", stmt).group(1))
    m = re.search(r"Nat\.testBit \((\d+) \* 2 \^ 32 \+ (\d+)\)", stmt)
    if not m:
        return None
    hi, lo = int(m.group(1)), int(m.group(2))
    target = [(hi << 32 | lo) >> r & 1 for r in range(1 << n)]
    return n, bound, target


def input_masks(n):
    return [sum(1 << r for r in range(1 << n) if (r >> i) & 1) for i in range(n)]


def evaluate(gates, n):
    full = (1 << (1 << n)) - 1
    w = input_masks(n)
    for op, a, b in gates:
        va, vb = w[a], w[b]
        w.append(va & vb if op == 'and' else va | vb if op == 'or' else full ^ va)
    return w[n + len(gates) - 1], w


def beam_search(n, target, bound, width=1500, seed=0):
    tmask = sum(v << r for r, v in enumerate(target))
    full = (1 << (1 << n)) - 1
    base = input_masks(n)
    states = [(base, ())]
    rng = random.Random(seed)
    for depth in range(bound):
        nxt = {}
        for w, hist in states:
            cands = []
            for a in range(len(w)):
                v = full ^ w[a]
                if v not in w:
                    cands.append((v, ('not', a, None)))
            for a, b in itertools.combinations(range(len(w)), 2):
                for op, v in (('and', w[a] & w[b]), ('or', w[a] | w[b])):
                    if v not in w:
                        cands.append((v, (op, a, b)))
            for v, op in cands:
                sc = (1 << n) - ((v ^ tmask).bit_count())
                key = tuple(w + [v])
                if key not in nxt or sc > nxt[key][0]:
                    nxt[key] = (sc, w + [v], hist + (op,))
        items = sorted(nxt.values(), key=lambda x: -x[0])
        for sc, w, hist in items:
            if tmask in w and any(o[0] == 'not' for o in hist):
                out = w.index(tmask)
                return list(hist), out
        states = [(w, h) for _, w, h in items[:width]]
        if not states:
            break
    return None


def emit(n, bound, statement, gates, outwire):
    num = re.search(r"L_meta_(\d+)$", __import__('sys').argv[1] if len(__import__('sys').argv) > 1 else "")
    num = num.group(1) if num else "0"
    mod = "PEqualNP.Outside.L_meta_" + num
    opname = {'and': 'and', 'or': 'or', 'not': 'not'}
    gs = ", ".join(
        "⟨PEqualNP.CircuitLowerBounds.GateOp.%s, [%s]⟩" %
        (opname[op], ", ".join(str(x) for x in ([a] if op == 'not' else [a, b])))
        for op, a, b in gates)
    notpos = next(j for j, g in enumerate(gates) if g[0] == 'not')
    notwire = gates[notpos][1]
    alts = " | ".join("h%d" % j for j in range(len(gates)))
    rcases = "rcases hg with " + alts + " <;> subst g <;> simp"
    code = """import Mathlib
import PEqualNP.Defs

namespace %s_aux

-- Witness circuit found by the circwit generator (beam search over 64-bit wire masks).
-- Proof pattern follows constructed circuit witnesses in the merged corpus (Apache-2.0).

def witness : PEqualNP.CircuitLowerBounds.Circuit :=
  ⟨[%s], %d⟩

end %s_aux

open %s_aux

set_option maxRecDepth 100000 in
set_option maxHeartbeats 20000000 in
theorem %s : %s := by
  refine ⟨%s_aux.witness, ?_, ?_, ?_, ?_⟩
  · intro g hg
    simp only [%s_aux.witness, List.mem_cons, List.not_mem_nil, or_false] at hg
    %s
  · refine ⟨⟨PEqualNP.CircuitLowerBounds.GateOp.not, [%d]⟩, ?_, by simp⟩
    simp [%s_aux.witness]
  · decide +kernel
  · decide +kernel
""" % (mod, gs, n + len(gates) - 1 if False else n + len(gates) - 1, mod, mod, mod,
       statement, mod, mod, rcases, notwire, mod)
    return code


def main():
    if len(sys.argv) != 4:
        sys.exit(2)
    gid, sf, out = sys.argv[1:4]
    statement = open(sf).read().strip()
    parsed = parse(statement)
    if parsed is None:
        print("unrecognised circuit-witness statement", file=sys.stderr)
        sys.exit(3)
    n, bound, target = parsed
    found = beam_search(n, target, bound, seed=sum(ord(c) for c in gid) % 1000)
    if found is None:
        print("no circuit within bound %d" % bound, file=sys.stderr)
        sys.exit(3)
    gates, outwire = found
    open(out, "w").write(emit(n, bound, statement, gates, outwire))
    sys.exit(0)


if __name__ == "__main__":
    main()

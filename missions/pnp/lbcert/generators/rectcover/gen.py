#!/usr/bin/env python3
"""Rectangle-cover generator for matrix colouring statements.

Learn from merged PEqualNP.Outside.L_meta_10011 / 10013 / 10015 (Apache-2.0):
a witness is a list of all-zero (or all-one) rectangles given as Finsets, and
both soundness and completeness are checked by kernel decide. The search below
builds maximal bicliques of the target-colour bipartite graph and runs a
greedy set cover; instances whose cover exceeds the stated bound are refused.
"""
import random
import re
import sys

MATCH = r"∃ L : List \(Finset \(Fin \d+\) × Finset \(Fin \d+\)\), L.length ≤ \d+"


def parse(text):
    m = re.search(r"Finset \(Fin (\d+)\) × Finset \(Fin (\d+)\)", text)
    if not m:
        return None
    nr, nc = int(m.group(1)), int(m.group(2))
    bound = int(re.search(r"L\.length ≤ (\d+)", text).group(1))
    lists = [list(map(int, re.findall(r"\d+", m.group(1))))
             for m in re.finditer(r"\(\[([0-9, ]+)\] : List ℕ\)", text)]
    rows = max(lists, key=len)
    if len(rows) != nr:
        return None
    want_false = "testBit j.val = false" in text
    return nr, nc, bound, rows, want_false


def cover_rectangles(rows, nc, want_false, seed=0, tries=3):
    n = len(rows)
    Zi = [frozenset(j for j in range(nc)
                    if bool((rows[i] >> j) & 1) != want_false)
          for i in range(n)]
    concepts = set()

    def close(R, C):
        if not R or not C:
            return None
        R2 = frozenset(i for i in range(n) if C <= Zi[i])
        C2 = frozenset(c for c in range(nc) if all(c in Zi[i] for i in R2))
        return (R2, C2) if R2 and C2 else None

    Zjt = [frozenset(i for i in range(n) if j in Zi[i]) for j in range(nc)]
    for j in range(nc):
        concepts.add(close(Zjt[j], frozenset({j})))
    for i in range(n):
        concepts.add(close(frozenset({i}), Zi[i]))
    # exhaustive small subsets / full enumeration when feasible
    import itertools
    full_enum = False
    if n <= 18:
        full_enum = True
        allC = (1 << nc) - 1
        Zib = [0] * n
        for i in range(n):
            for j in Zi[i]:
                Zib[i] |= 1 << j
        for mask in range(1, 1 << n):
            Cb = allC
            mm = mask
            while mm:
                b = mm & -mm; i = b.bit_length() - 1; Cb &= Zib[i]; mm ^= b
                if not Cb: break
            if not Cb: continue
            Rb = 0
            for i in range(n):
                if (Zib[i] & Cb) == Cb: Rb |= 1 << i
            R = frozenset(i for i in range(n) if Rb >> i & 1)
            C = frozenset(j for j in range(nc) if Cb >> j & 1)
            concepts.add((R, C))
    elif nc <= 18:
        full_enum = True
        allR = (1 << n) - 1
        Zjb = [0] * nc
        for j in range(nc):
            for i in Zjt[j]: Zjb[j] |= 1 << i
        for mask in range(1, 1 << nc):
            Rb = allR
            mm = mask
            while mm:
                b = mm & -mm; j = b.bit_length() - 1; Rb &= Zjb[j]; mm ^= b
                if not Rb: break
            if not Rb: continue
            Cb = 0
            for j in range(nc):
                if (Zjb[j] & Rb) == Rb: Cb |= 1 << j
            R = frozenset(i for i in range(n) if Rb >> i & 1)
            C = frozenset(j for j in range(nc) if Cb >> j & 1)
            concepts.add((R, C))
    else:
        if n <= 22:
            for r in range(2, min(6, n + 1)):
                for S in itertools.combinations(range(n), r):
                    C = set(Zi[S[0]])
                    for i in S[1:]: C &= Zi[i]
                    if C: concepts.add(close(frozenset(S), frozenset(C)))
        if nc <= 22:
            for r in range(2, min(6, nc + 1)):
                for S in itertools.combinations(range(nc), r):
                    R = set(Zjt[S[0]])
                    for j in S[1:]: R &= Zjt[j]
                    if R: concepts.add(close(frozenset(R), frozenset(S)))
    if not full_enum:
        # pairwise closures always
        for j in range(nc):
            for k in range(j + 1, nc):
                R = frozenset(i for i in range(n) if j in Zi[i] and k in Zi[i])
                c = close(R, frozenset({j, k}))
                if c:
                    concepts.add(c)
        for i in range(n):
            for k in range(i + 1, n):
                C = Zi[i] & Zi[k]
                c = close(frozenset({i, k}), C)
                if c:
                    concepts.add(c)
        rng = random.Random(seed)
        for _ in range(40000):
            S = rng.sample(range(n), rng.randint(2, min(10, n)))
            C = set(Zi[S[0]])
            for i in S[1:]:
                C &= Zi[i]
            if C:
                c = close(frozenset(S), frozenset(C))
                if c:
                    concepts.add(c)
    concepts.discard(None)
    cands = sorted(concepts, key=lambda p: len(p[0]) * len(p[1]), reverse=True)
    if len(cands) > 4000:
        cands = cands[:4000]
    Z = {(i, j) for i in range(n) for j in Zi[i]}
    best = None
    for t in range(tries):
        remaining = set(Z)
        cover = []
        while remaining:
            pick, gain = None, 0
            for R, C in cands:
                g = sum(1 for i in R for j in C if (i, j) in remaining)
                if g > gain:
                    gain, pick = g, (R, C)
            if pick is None:
                break
            remaining -= {(i, j) for i in pick[0] for j in pick[1]}
            cover.append(pick)
        if not remaining and (best is None or len(cover) < len(best)):
            best = cover

    # Exact minimum set cover via SAT for small/medium instances.
    return best
    try:
        from pysat.solvers import Minisat22
        from pysat.card import CardEnc, EncType
    except Exception:
        return best
    if len(Z) > 1500:
        return best
    if len(cands) > 2500:
        cands = cands[:2500]
    idx = {(i, j): k for k, (i, j) in enumerate(sorted(Z))}
    masks = []
    for R, C in cands:
        m = 0
        for i in R:
            for j in C:
                m |= 1 << idx[(i, j)]
        masks.append(m)
    full = (1 << len(idx)) - 1
    by_edge = [[] for _ in range(len(idx))]
    for ci, m in enumerate(masks):
        mm = m
        while mm:
            b = mm & -mm
            by_edge[b.bit_length() - 1].append(ci + 1)
            mm ^= b
    upper = len(best) if best else len(cands)
    lo, hi = 1, upper
    opt = None
    while lo <= hi:
        mid = (lo + hi) // 2
        cnf = []
        for lits in by_edge:
            if lits:
                cnf.append(lits)
        if mid < len(cands):
            enc = CardEnc.atmost(lits=list(range(1, len(cands) + 1)), bound=mid,
                                 encoding=EncType.seqcounter, top_id=len(cands))
            cnf.extend(enc.clauses)
        with Minisat22(bootstrap_with=cnf) as s:
            sat = s.solve()
            model = s.get_model() if sat else None
        if sat and model:
            chosen = [cands[v - 1] for v in model if 1 <= v <= len(cands)]
            cov = 0
            for R, C in chosen:
                for i in R:
                    for j in C:
                        cov |= 1 << idx[(i, j)]
            if cov == full:
                opt = chosen
                hi = mid - 1
            else:
                lo = mid + 1
        else:
            lo = mid + 1
    if opt is not None and (best is None or len(opt) < len(best)):
        best = opt
    return best


def emit(gid_mod, statement, nr, nc, cover):
    mnum = re.search(r"(\d+)$", gid_mod)
    num = mnum.group(1) if mnum else gid_mod.rsplit("_", 1)[-1]
    aux = "PEqualNP.Outside.L_meta_" + num + "_aux"
    boxes = ", ".join(
        "({" + ",".join(str(i) for i in sorted(R)) + "},{" +
        ",".join(str(j) for j in sorted(C)) + "})" for R, C in cover)
    code = """import Mathlib
import PEqualNP.Defs

-- Rectangle witness computed by the rectcover generator; method learned from
-- merged PEqualNP.Outside.L_meta_10011 / L_meta_10013 / L_meta_10015.

namespace %s

def cover : List (Finset (Fin %d) × Finset (Fin %d)) := [%s]

end %s

set_option maxRecDepth 100000 in
set_option maxHeartbeats 20000000 in
theorem PEqualNP.Outside.L_meta_%s : %s := by
  refine ⟨%s.cover, by decide, ?_, ?_⟩
  · decide +kernel
  · decide +kernel
""" % (aux, nr, nc, boxes, aux, num, statement, aux)
    return code


def main():
    if len(sys.argv) != 4:
        sys.exit(2)
    gid, stmt_file, out = sys.argv[1:4]
    statement = open(stmt_file).read().strip()
    parsed = parse(statement)
    if parsed is None:
        print("unrecognised rectangle statement", file=sys.stderr)
        sys.exit(3)
    nr, nc, bound, rows, want_false = parsed
    cover = cover_rectangles(rows, nc, want_false, seed=sum(ord(c) for c in gid))
    if cover is None or len(cover) > bound:
        print("cover %s exceeds bound %d" %
              (len(cover) if cover is not None else "not found", bound), file=sys.stderr)
        sys.exit(3)
    open(out, "w").write(emit(gid, statement, nr, nc, cover))
    sys.exit(0)


if __name__ == "__main__":
    main()

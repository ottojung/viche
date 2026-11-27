#!/usr/bin/env python3
"""Generator for fixed-graph-table `Represents` witnesses (BACKLOG family 1).

Statement shape (desk / merged L-meta-20578, L-meta-19035, Apache-2.0):
  (∃ C : Circuit, FanInTwo C ∧ C.size ≤ K ∧
     Represents (fun u v : Fin n => (([0x.., ..] : List ℕ).getD u.val 0).testBit v.val) C)

Method: build a monotone fan-in-two circuit for the adjacency function on the
one-a-side promise by a cost-aware bipartite biclique cover (OR of rows, OR of
columns, AND; OR the rectangles).  Every wire column is verified in Python on
all n*n promise rows before emission.  The emitted proof uses the reusable
library lemma `PromiseColTree.represents_of_tcols` (learned from the merged
L-meta-20578 / L-meta-19035 files): the whole promise table is checked by one
`decide +kernel` over big-integer wire columns, not by enumerating 2^(2n) rows.

Exit 3 (refuse) when the cover exceeds the bound, the table is unsupported, or
the circuit fails its independent semantic audit.  Pure Python, <= 600 s.
"""
import itertools
import random
import re
import sys

PREFIX = r"\(?∃ C : PEqualNP\.CircuitLowerBounds\.Circuit, PEqualNP\.MetaComplexity\.FanInTwo C ∧ C\.size ≤ (\d+) ∧ "
TABLE = r"PEqualNP\.Represents\.Represents \(fun u v : Fin (\d+) => \(\(\[([0-9a-fA-Fx, ]+)\] : List ℕ\)\.getD u\.val 0\)\.testBit v\.val\) C\)?$"
MATCH = PREFIX + TABLE


def parse(stmt):
    s = " ".join(stmt.split())
    m = re.search(r"C\.size ≤ (\d+) ∧\s*PEqualNP\.Represents\.Represents \(fun u v : Fin (\d+) => \(\(\[([0-9a-fA-Fx, ]+)\] : List ℕ\)\.getD u\.val 0\)\.testBit v\.val\) C\)?\s*$", s)
    if not m:
        return None
    k = int(m.group(1))
    n = int(m.group(2))
    rows = [int(x, 16) for x in re.findall(r"0x[0-9a-fA-F]+", m.group(3))]
    if len(rows) != n or any(r >> n for r in rows):
        return None
    return n, k, rows


def candidates(n, rows, max_sub=4, tries=300, seed=0):
    """Closed bipartite bicliques (row subset R, column subset C)."""
    adjR = [frozenset(v for v in range(n) if (rows[u] >> v) & 1) for u in range(n)]
    seen = set()
    rng = random.Random(seed)
    max_comb = min(max_sub, 3) if n <= 40 else 1
    seeds = [tuple(c) for r in range(1, max_comb + 1)
             for c in itertools.combinations(range(n), r)]
    if n >= 2:  # clamp sample size to population (small-n safety)
        hi = min(max_sub, n)
        seeds += [tuple(rng.sample(range(n), rng.randint(2, hi)))
                  for _ in range(tries)]
    for S in seeds:
        C = set(adjR[S[0]])
        for u in S[1:]:
            C &= adjR[u]
        if not C:
            continue
        R2 = frozenset(u for u in range(n) if C <= adjR[u])
        C2 = frozenset(C)
        if R2 and C2:
            cov = frozenset((u, v) for u in R2 for v in C2)
            cost = len(R2) + len(C2) - 1
            seen.add((R2, C2, cov, cost))
    return list(seen)


def cover(n, rows, bound):
    ones = frozenset((u, v) for u in range(n) for v in range(n)
                     if (rows[u] >> v) & 1)
    if not ones:
        return []
    cands = candidates(n, rows)
    remaining = set(ones)
    chosen = []
    ngates = 0
    while remaining:
        best, ratio = None, -1.0
        for R, C, cov, cost in cands:
            gain = len(cov & remaining)
            if gain and gain / cost > ratio:
                ratio, best = gain / cost, (R, C, cov, cost)
        if best is None:
            return None
        R, C, cov, cost = best
        remaining -= cov
        chosen.append((sorted(R), sorted(C)))
        ngates += cost
        if ngates > bound:
            return None
    ngates += len(chosen) - 1
    if ngates > bound:
        return None
    return chosen


def mixed_pairs(n, rows, max_sub=5):
    """Admissible disjoint biclique pairs (no selector sharing assumed).

    A pair (R1,C1),(R2,C2) is realised by two mixed selectors
    (R1 OR C2) AND (R2 OR C1), requiring R1/R2 disjoint and C1/C2 disjoint.
    Its AND covers R1*C1 union R2*C2 (two rectangles per gate).  Unshared
    cost is |R1|+|R2|+|C1|+|C2|-1 (two OR trees plus one AND).
    """
    adjR = [frozenset(v for v in range(n) if (rows[u] >> v) & 1) for u in range(n)]
    bics = set()
    for r in range(1, min(max_sub, n) + 1):
        for S in itertools.combinations(range(n), r):
            C = set(adjR[S[0]])
            for u in S[1:]:
                C &= adjR[u]
            if len(C) < 2:
                continue
            R2 = frozenset(u for u in range(n) if C <= adjR[u])
            C2 = frozenset(C)
            if len(R2) >= 2:
                bics.add((R2, C2))
    bics = list(bics)
    out = []
    for i, (R1, C1) in enumerate(bics):
        for R2, C2 in bics[i + 1:]:
            if R1 & R2 or C1 & C2:
                continue
            cov = frozenset((u, v) for u in R1 for v in C1)
            cov |= frozenset((u, v) for u in R2 for v in C2)
            cost = len(R1) + len(R2) + len(C1) + len(C2) - 1
            out.append((cov, cost, (R1, C1), (R2, C2)))
    return out


def mixed_cover(n, rows, bound, max_sub=5):
    """Multi-start greedy cover by mixed-selector AND pairs (fast frozenset scans).

    A few deterministic (noise, seed) starts are tried; the cover with the
    smallest actual shared-OR-DAG gate count is returned, or None if none fits.
    """
    ones = frozenset((u, v) for u in range(n) for v in range(n)
                     if (rows[u] >> v) & 1)
    if not ones:
        return []
    if n > 40:  # candidate enumeration too expensive; plain cover path handles large graphs
        return None
    cands = mixed_pairs(n, rows, max_sub=max_sub)
    if not cands:
        return None
    best_chosen, best_gates = None, None
    for noise, seed in ((0.15, 2),):
        rng = random.Random(seed)
        rem, chosen, est = set(ones), [], 0
        while rem:
            score, pick = -1.0, None
            for cov, cost, b1, b2 in cands:
                gain = len(cov & rem)
                if gain:
                    sc = (gain / cost) * rng.uniform(1 - noise, 1 + noise)
                    if sc > score:
                        score, pick = sc, (cov, cost, b1, b2)
            if pick is None:
                break
            cov, cost, b1, b2 = pick
            rem -= cov
            chosen.append((b1, b2))
            est += cost
            if est > bound + 2 * n:
                break
        if not chosen or (est + max(0, len(chosen) - 1)) > bound + 2 * n:
            continue
        gates, out = build_gates_mixed(n, chosen)
        if out is None or not audit(n, rows, gates, out):
            continue
        if best_gates is None or len(gates) < best_gates:
            best_chosen, best_gates = chosen, len(gates)
    if best_chosen is None or best_gates > bound:
        return None
    return best_chosen


def build_gates_mixed(n, chosen):
    """Build mixed-selector pairs using a shared, greedily reused OR-DAG.

    OR wires are memoised by the frozenset of input wires they cover.  Each new
    selector is assembled by repeatedly OR-ing in the cached subset that covers
    the most still-missing inputs, so intermediate OR gates are shared across
    selectors (mirroring the merged L_meta_20578 witness's 164 shared OR gates
    for 32 selectors).
    """
    gates = []  # (op 0=and / 1=or, a, b)
    or_cache = {}

    def or_wire(ws):
        S = frozenset(ws)
        if len(S) == 1:
            return next(iter(S))
        if S in or_cache:
            return or_cache[S]
        cur, curw = frozenset(), None
        while cur != S:
            best, best_gain = None, 0
            for ss, ww in or_cache.items():
                if ss <= S and not ss <= cur:
                    gain = len(ss - cur)
                    if gain > best_gain:
                        best_gain, best = gain, (ss, ww)
            if best is None:
                ss = frozenset([min(S - cur)])
                ww = next(iter(ss))
            else:
                ss, ww = best
            if curw is None:
                curw = ww
            else:
                gates.append((1, curw, ww))
                curw = 2 * n + len(gates) - 1
                or_cache[cur | ss] = curw
            cur = cur | ss
        return curw

    def selector(R, C):
        rw = or_wire(R) if R else None
        cw = or_wire([n + v for v in C]) if C else None
        if rw is None:
            return cw
        if cw is None:
            return rw
        gates.append((1, rw, cw))
        return 2 * n + len(gates) - 1

    and_wires = []
    for (R1, C1), (R2, C2) in chosen:
        a = selector(R1, C2)
        b = selector(R2, C1)
        gates.append((0, a, b))
        and_wires.append(2 * n + len(gates) - 1)
    if not and_wires:
        return gates, None
    return gates, or_wire(and_wires)


def build_gates(n, chosen):
    """Interleaved OR-row, OR-col, AND, final OR tree. Wires: 0..2n-1 inputs."""
    gates = []  # (op 0=and / 1=or, a, b)

    def or_tree(wires):
        w = wires[0]
        for v in wires[1:]:
            gates.append((1, w, v))
            w = 2 * n + len(gates) - 1
        return w

    and_wires = []
    for R, C in chosen:
        rw = or_tree(R)
        cw = or_tree([n + v for v in C])
        gates.append((0, rw, cw))
        and_wires.append(2 * n + len(gates) - 1)
    out = or_tree(and_wires)
    return gates, out


def audit(n, rows, gates, out):
    """Independent per-row evaluation of every gate on all n*n promise rows."""
    total = 2 * n + len(gates)
    for u in range(n):
        for v in range(n):
            w = [False] * total
            w[u] = True
            w[n + v] = True
            for i, (op, a, b) in enumerate(gates):
                w[2 * n + i] = (w[a] & w[b]) if op == 0 else (w[a] | w[b])
            if w[out] != bool((rows[u] >> v) & 1):
                return False
    return True


def emit(n, k, rows, gates, out, gid, stmt):
    name = gid.replace("-", "_")
    mod = "PEqualNP.Outside." + name
    ns = mod + "_aux"
    codes = ", ".join("(%d,%d,%d)" % (op, a, b) for op, a, b in gates)
    N = 1
    while (1 << N) < n * n:
        N += 1
    D = 1
    while (1 << D) < 2 * n + len(gates):
        D += 1
    return """import Mathlib
import PEqualNP.Defs
import PEqualNP.Library.Helpers.PromiseColTree

-- Witness from a cost-aware bipartite biclique cover; proof shape learned from
-- merged PEqualNP.Outside.L_meta_20578 / L_meta_19035 (Apache-2.0).

namespace %s

def codes : List (ℕ × ℕ × ℕ) := [%s]

def circ : PEqualNP.CircuitLowerBounds.Circuit :=
  ⟨codes.map (fun (o, a, b) =>
     ⟨if o = 0 then PEqualNP.CircuitLowerBounds.GateOp.and
      else PEqualNP.CircuitLowerBounds.GateOp.or, [a, b]⟩), %d⟩

end %s

set_option maxRecDepth 200000 in
set_option maxHeartbeats 20000000 in
theorem %s : %s := by
  refine ⟨%s.circ,
    PEqualNP.Library.Helpers.Replay.fanInTwoB_sound ?_, ?_, ?_⟩
  · decide +kernel
  · decide +kernel
  · apply PEqualNP.Library.Helpers.PromiseColTree.represents_of_tcols
      (N := %d) (D := %d) (by decide) %s.circ
    · intro r hr
      simp only [List.mem_cons, List.not_mem_nil, or_false] at hr
      omega
    · decide +kernel
    · decide +kernel
    · decide +kernel
""" % (ns, codes, out, ns, mod, stmt.strip(), ns, N, D, ns)


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: gen.py GID STATEMENT_FILE OUT.lean")
    gid = sys.argv[1]
    stmt = open(sys.argv[2]).read()
    p = parse(stmt)
    if p is None:
        sys.exit(3)
    n, k, rows = p
    chosen = cover(n, rows, k)
    gates, out = None, None
    if chosen:  # empty table has no output wire; fall through to refusal
        gates, out = build_gates(n, chosen)
    if gates is None or len(gates) > k or not audit(n, rows, gates, out):
        # plain biclique cover failed or over bound: try mixed selectors
        chosen = mixed_cover(n, rows, k)
        gates, out = None, None
        if chosen:
            gates, out = build_gates_mixed(n, chosen)
        if gates is None or out is None or len(gates) > k or not audit(n, rows, gates, out):
            sys.exit(3)
    open(sys.argv[3], "w").write(emit(n, k, rows, gates, out, gid, stmt))
    return 0


if __name__ == "__main__":
    sys.exit(main())

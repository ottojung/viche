#!/usr/bin/env python3
"""Bounded rectangle-cover witness search, followed by independent Lean verification.

Enumerate maximal rectangles by row intersections (capped on dense matrices),
retain row/column covers, use fast bitset greedy search, then one bounded SAT
query at the requested bound. Refusal is never a lower-bound proof.
"""
import random
import re
import sys
import threading

MAX_INTERSECTIONS = 12000
MAX_CANDIDATES = 6000
PATTERN = re.compile(
    r"∃ L : List \(Finset \(Fin (\d+)\) × Finset \(Fin (\d+)\)\), L.length ≤ (\d+) ∧ "
    r"\(∀ r ∈ L, ∀ i ∈ r\.1, ∀ j ∈ r\.2, \(\(\[([0-9, ]*)\] : List ℕ\)\.getD i\.val 0\)\.testBit j\.val = (true|false)\) ∧ "
    r"∀ \(i : Fin \1\) \(j : Fin \2\), \(\(\[\4\] : List ℕ\)\.getD i\.val 0\)\.testBit j\.val = \5 → ∃ r ∈ L, i ∈ r\.1 ∧ j ∈ r\.2"
)


def parse(text):
    m = PATTERN.fullmatch(" ".join(text.split()))
    if not m:
        return None
    nr, nc, bound = map(int, m.group(1, 2, 3))
    rows = [int(x) for x in m[4].split(",") if x.strip()]
    if not (0 < nr <= 64 and 0 < nc <= 64 and len(rows) == nr):
        return None
    return nr, nc, bound, rows, m[5] == "false"


def matches(text):
    return parse(text) is not None


def bits(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


def rectangle_mask(r, c, nc):
    return sum(c << (i * nc) for i in bits(r))


def matrix(rows, nc, want_false):
    full = (1 << nc) - 1
    return [(x ^ full if want_false else x) & full for x in rows]


def candidates(rows, nc):
    """Every generated rectangle is a maximal all-target submatrix."""
    nr = len(rows)
    full = (1 << nc) - 1
    def close(c):
        r = sum(1 << i for i, x in enumerate(rows) if c & x == c)
        if not r or not c:
            return None
        for i in bits(r):
            c &= rows[i]
        return r, c
    mandatory = {close(c) for c in rows if c}
    mandatory.update(close(1 << j) for j in range(nc))
    mandatory.discard(None)
    # Distinct intersections, not all subsets; capped deterministically.
    inter = {full}
    for c in rows:
        inter |= {x & c for x in inter}
        inter.discard(0)
        if len(inter) > MAX_INTERSECTIONS:
            inter = set(sorted(inter, key=lambda x: (-x.bit_count(), x))[:MAX_INTERSECTIONS])
    boxes = {close(c) for c in inter}
    boxes.discard(None)
    extras = sorted(boxes - mandatory, key=lambda p: (-p[0].bit_count()*p[1].bit_count(), p))
    return sorted(mandatory | set(extras[:max(0, MAX_CANDIDATES-len(mandatory))]))


def prune(chosen, masks, target):
    for i in reversed(range(len(chosen))):
        other = 0
        for j, c in enumerate(chosen):
            if j != i:
                other |= masks[c]
        if other == target:
            chosen.pop(i)
    return chosen


def greedy(masks, target, seed=0, tries=12):
    rng = random.Random(seed)
    best = None
    for t in range(tries):
        left = target
        out = []
        order = list(range(len(masks)))
        if t:
            rng.shuffle(order)
        while left:
            if best is not None and len(out) >= len(best):
                break
            index = max(order, key=lambda i: (masks[i] & left).bit_count())
            gain = masks[index] & left
            if not gain:
                break
            left ^= gain
            out.append(index)
        if not left:
            out = prune(out, masks, target)
            if best is None or len(out) < len(best):
                best = out
    return best


def bounded_sat(masks, target, bound, seconds=30):
    """One decision problem at the desk bound, never an unbounded optimum loop."""
    try:
        from pysat.solvers import Minisat22
        from pysat.card import CardEnc, EncType
    except ImportError:
        return None
    if bound < 0 or not masks or len(masks)*max(1,bound) > 220000:
        return None
    cells = list(bits(target))
    by_cell = {i: [] for i in cells}
    for ci, m in enumerate(masks, 1):
        for i in bits(m):
            by_cell[i].append(ci)
    if any(not x for x in by_cell.values()):
        return None
    clauses = list(by_cell.values())
    if bound < len(masks):
        clauses += CardEnc.atmost(lits=list(range(1, len(masks)+1)), bound=bound,
                                  encoding=EncType.seqcounter, top_id=len(masks)).clauses
    with Minisat22(bootstrap_with=clauses) as solver:
        solver.conf_budget(200000)
        timer = threading.Timer(seconds, solver.interrupt)
        timer.start()
        try:
            ok = solver.solve_limited(expect_interrupt=True)
            if ok is True:
                model = solver.get_model()
                return [v-1 for v in model if 1 <= v <= len(masks)]
        finally:
            timer.cancel()
            timer.join()
    return None


def audit(boxes, rows, nc, bound):
    if len(boxes) > bound:
        return False
    target = sum(x << (i*nc) for i,x in enumerate(rows))
    union = 0
    for r, c in boxes:
        if not (0 < r < (1 << len(rows)) and 0 < c < (1 << nc)):
            return False
        m = rectangle_mask(r, c, nc)
        if m & ~target:
            return False
        union |= m
    return union == target


def cover_rectangles(rows, nc, want_false, bound, seed=0, seconds=30):
    zi = matrix(rows, nc, want_false)
    target = sum(x << (i*nc) for i,x in enumerate(zi))
    if not target:
        return []
    if bound <= 0:
        return None
    boxes = candidates(zi, nc)
    masks = [rectangle_mask(r,c,nc) for r,c in boxes]
    # The singleton row and column covers give an unconditional upper bound.
    # Prefer the smallest of those and the maximal-rectangle greedy cover.
    row_cover = [(1 << i, c) for i, c in enumerate(zi) if c]
    col_cover = [(sum(1 << i for i, c in enumerate(zi) if c & (1 << j)), 1 << j)
                 for j in range(nc) if any(c & (1 << j) for c in zi)]
    baseline = min(row_cover, col_cover, key=len)
    if len(baseline) <= bound:
        return baseline if audit(baseline, zi, nc, bound) else None
    best = greedy(masks, target, seed)
    if best is None or len(best) > bound:
        best = bounded_sat(masks, target, bound, seconds)
    if best is None:
        return None
    chosen = [boxes[i] for i in best]
    return chosen if audit(chosen, zi, nc, bound) else None


def emit(gid, statement, nr, nc, rows, want_false, cover):
    num = re.fullmatch(r"L-meta-(\d+)", gid).group(1)
    aux = "PEqualNP.Outside.L_meta_" + num + "_aux"
    color = "false" if want_false else "true"
    # Mask verifier follows the independently merged L-meta-10011 proof pattern.
    return f"""import PEqualNP.Defs

namespace {aux}

def boxes : List (ℕ × ℕ) := {str(cover)}
def rows : List ℕ := {rows}
def members {{n : ℕ}} (mask : ℕ) : Finset (Fin n) := Finset.univ.filter fun i => mask.testBit i.val

set_option maxRecDepth 100000 in
set_option maxHeartbeats 20000000 in
lemma sound : ∀ p ∈ boxes, ∀ i : Fin {nr}, ∀ j : Fin {nc}, p.1.testBit i.val = true → p.2.testBit j.val = true → (rows.getD i.val 0).testBit j.val = {color} := by decide +kernel

set_option maxRecDepth 100000 in
set_option maxHeartbeats 20000000 in
lemma complete : ∀ i : Fin {nr}, ∀ j : Fin {nc}, (rows.getD i.val 0).testBit j.val = {color} → ∃ p ∈ boxes, p.1.testBit i.val = true ∧ p.2.testBit j.val = true := by decide +kernel

end {aux}

open {aux}

theorem PEqualNP.Outside.L_meta_{num} : {statement} := by
  refine ⟨boxes.map (fun p => (members p.1, members p.2)), by decide, ?_, ?_⟩
  · intro r hr i hi j hj
    obtain ⟨p, hp, rfl⟩ := List.mem_map.mp hr
    exact sound p hp i j (by simpa [members] using hi) (by simpa [members] using hj)
  · intro i j h
    obtain ⟨p, hp, hi, hj⟩ := complete i j h
    exact ⟨_, List.mem_map.mpr ⟨p, hp, rfl⟩, by simpa [members] using hi, by simpa [members] using hj⟩
"""


def main():
    if len(sys.argv) != 4:
        return 2
    gid, sf, out = sys.argv[1:4]
    statement = open(sf).read().strip()
    parsed = parse(statement)
    if not parsed:
        print("unrecognised rectangle statement", file=sys.stderr)
        return 3
    nr, nc, bound, rows, want_false = parsed
    cover = cover_rectangles(rows, nc, want_false, bound, seed=sum(map(ord,gid)))
    if cover is None:
        print("no verified rectangle cover within bound and search budget", file=sys.stderr)
        return 3
    open(out, "w").write(emit(gid, statement, nr, nc, rows, want_false, cover))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Majority/threshold circuit-witness generator (HasCircuitSize family).

Statement shape:
  PEqualNP.MetaComplexity.HasCircuitSize n
    (fun x : Fin n → Bool => decide (k ≤ (List.ofFn x).count true)) K

Known median/majority circuits are kept as data; the proof shape follows the
merged PEqualNP.Outside.L_meta_18229 / L_meta_18232 files (Apache-2.0):
unfold HasCircuitSize, `refine ⟨⟨gates, out⟩, ?_, ?_, ?_⟩`, `simp [FanInTwo]`,
`decide`, `decide +kernel`. The gate list is verified against all 2^n rows in
Python before emission. Exit 3 for unsupported parameters or over-bound circuits.
"""
import re
import sys

MATCH = (r"PEqualNP\.MetaComplexity\.HasCircuitSize \d+ "
         r"\(fun x : Fin \d+ → Bool => decide \(\d+ ≤ \(List\.ofFn x\)\.count true\)\) \d+")

# (n, k): (gates, output wire) from merged L_meta_18229 / L_meta_18232.
CIRCUITS = {
    (8, 4): (
        [('and', [0, 1]), ('or', [0, 1]), ('and', [3, 4]), ('or', [3, 4]),
         ('and', [6, 7]), ('or', [6, 7]), ('and', [2, 10]), ('or', [2, 10]),
         ('and', [5, 12]), ('or', [5, 12]), ('and', [15, 11]), ('or', [15, 11]),
         ('and', [17, 13]), ('or', [17, 13]), ('or', [8, 14]),
         ('and', [19, 21]), ('and', [18, 20]), ('or', [18, 20]),
         ('or', [22, 16]), ('or', [9, 24]), ('and', [27, 25]),
         ('and', [28, 23]), ('or', [28, 23]), ('or', [26, 29]), ('and', [31, 30])], 32),
    (9, 5): (
        [('and', [1, 2]), ('or', [1, 2]), ('and', [4, 5]), ('or', [4, 5]),
         ('and', [7, 8]), ('or', [7, 8]), ('and', [0, 9]), ('or', [0, 9]),
         ('and', [3, 11]), ('or', [3, 11]), ('and', [6, 13]), ('or', [6, 13]),
         ('and', [16, 10]), ('or', [16, 10]), ('and', [18, 12]), ('or', [18, 12]),
         ('and', [20, 14]), ('or', [20, 14]), ('or', [15, 17]),
         ('and', [24, 26]), ('and', [23, 25]), ('or', [23, 25]),
         ('or', [27, 19]), ('or', [21, 29]), ('and', [22, 28]),
         ('and', [32, 30]), ('and', [34, 33]), ('or', [34, 33]),
         ('or', [31, 35]), ('and', [37, 36])], 38),
}


def parse(stmt):
    m = re.match(r"PEqualNP\.MetaComplexity\.HasCircuitSize (\d+) \(fun x : Fin \d+ → Bool => "
                 r"decide \((\d+) ≤ \(List\.ofFn x\)\.count true\)\) (\d+)$", stmt.strip())
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def verify(n, k, gates, out):
    for mask in range(1 << n):
        w = [(mask >> i) & 1 for i in range(n)]
        for op, ins in gates:
            v = [w[z] for z in ins]
            w.append(v[0] & v[1] if op == 'and' else v[0] | v[1])
        if w[out] != int(sum(w[:n]) >= k):
            return False
    return True


def emit(statement, n, k, bound, gates, out):
    gs = ", ".join("⟨.%s, [%s]⟩" % (op, ", ".join(str(z) for z in ins))
                   for op, ins in gates)
    return """import Mathlib
import PEqualNP.Defs

-- Witness circuit follows merged PEqualNP.Outside.L_meta_18229 / L_meta_18232 (Apache-2.0).
theorem PEqualNP.Outside.%s : %s := by
  unfold PEqualNP.MetaComplexity.HasCircuitSize
  refine ⟨⟨[%s], %d⟩, ?_, ?_, ?_⟩
  · simp [PEqualNP.MetaComplexity.FanInTwo]
  · decide
  · decide +kernel
""" % (sys.argv[1].replace('L-meta-', 'L_meta_'), statement, gs, out)


def main():
    if len(sys.argv) != 4:
        sys.exit(2)
    gid, sf, outfile = sys.argv[1:4]
    statement = open(sf).read().strip()
    p = parse(statement)
    if p is None:
        print("unrecognised majority HasCircuitSize statement", file=sys.stderr)
        sys.exit(3)
    n, k, bound = p
    if (n, k) not in CIRCUITS:
        print("no known circuit for n=%d k=%d" % (n, k), file=sys.stderr)
        sys.exit(3)
    gates, out = CIRCUITS[(n, k)]
    # Empirically the town compile lane OOMs on the 35-gate n=9 witness
    # (plugtest L-meta-18232: "kernel excessive memory consumption"), while the
    # 25-gate n=8 witness compiles in ~50 s. Refuse larger circuits honestly.
    if len(gates) > 25:
        print("circuit of %d gates exceeds compiled-witness limit 25" % len(gates), file=sys.stderr)
        sys.exit(3)
    if len(gates) > bound or not verify(n, k, gates, out):
        print("circuit over bound %d or verification failed" % bound, file=sys.stderr)
        sys.exit(3)
    open(outfile, "w").write(emit(statement, n, k, bound, gates, out))
    sys.exit(0)


if __name__ == '__main__':
    main()

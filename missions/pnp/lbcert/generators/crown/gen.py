#!/usr/bin/env python3
"""Generator for crown (u != v) RepSizeAtMost witnesses.

Statement shape (BACKLOG family 4; merged PEqualNP.Outside.L_meta_19546):
  PEqualNP.Represents.RepSizeAtMost (fun u v : Fin n => decide (u ≠ v)) K

Method (decoded from the merged 7x7 witness, Apache-2.0): on the one-a-side
promise let s_i = u_i ∨ v_i; then u ≠ v iff e_2(s_0..s_{n-1}), the second
elementary symmetric polynomial.  Maintain A = e_2 of the prefix, B = OR of
the prefix; for each new i add AND(s_i, B) into A and OR s_i into B.  Cost
4n-5 gates (the last B update is omitted), exactly the merged witness's size.
Every gate list is audited on all n^2 promise rows in Python before emission.
Exit 3 for unsupported shapes or when 4n-5 exceeds the bound.  Pure Python.
"""
import re
import sys

MATCH = (r"PEqualNP\.Represents\.RepSizeAtMost \(fun u v : Fin \d+ => decide \(u ≠ v\)\) \d+")


def parse(stmt):
    s = " ".join(stmt.split())
    m = re.fullmatch(r"PEqualNP\.Represents\.RepSizeAtMost \(fun u v : Fin (\d+) => decide \(u ≠ v\)\) (\d+)", s)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def build(n):
    """Return (gates, output wire); wires 0..n-1 = u, n..2n-1 = v."""
    if n < 2:
        return None
    gates = []  # ('and'|'or', a, b)

    def emit(op, a, b):
        gates.append((op, a, b))
        return 2 * n + len(gates) - 1

    s = [emit("or", i, n + i) for i in range(n)]
    if n == 2:
        return gates, emit("and", s[0], s[1])
    A = emit("and", s[0], s[1])
    B = emit("or", s[0], s[1])
    for i in range(2, n):
        A = emit("or", A, emit("and", s[i], B))
        if i < n - 1:
            B = emit("or", B, s[i])
    return gates, A


def audit(n, gates, out):
    total = 2 * n + len(gates)
    for u in range(n):
        for v in range(n):
            w = [False] * total
            w[u] = True
            w[n + v] = True
            for i, (op, a, b) in enumerate(gates):
                w[2 * n + i] = (w[a] & w[b]) if op == "and" else (w[a] | w[b])
            if w[out] != (u != v):
                return False
    return True


def emit_lean(n, k, gates, out, gid, stmt):
    name = gid.replace("-", "_")
    mod = "PEqualNP.Outside." + name
    glist = ", ".join("⟨GateOp.%s, [%d, %d]⟩" % (op, a, b) for op, a, b in gates)
    return """import Mathlib
import PEqualNP.Defs

open PEqualNP.CircuitLowerBounds

set_option maxRecDepth 200000 in
set_option maxHeartbeats 20000000 in
theorem %s : %s := by
  refine ⟨({ gates := [%s], output := %d } : Circuit), ?_, ?_, ?_⟩
  · simp [PEqualNP.MetaComplexity.Monotone2]
  · decide
  · decide +kernel
""" % (mod, stmt.strip(), glist, out)


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: gen.py GID STATEMENT_FILE OUT.lean")
    gid = sys.argv[1]
    stmt = open(sys.argv[2]).read()
    p = parse(stmt)
    if p is None:
        sys.exit(3)
    n, k = p
    built = build(n)
    if built is None:
        sys.exit(3)
    gates, out = built
    if len(gates) > k or not audit(n, gates, out):
        sys.exit(3)
    open(sys.argv[3], "w").write(emit_lean(n, k, gates, out, gid, stmt))
    return 0


if __name__ == "__main__":
    sys.exit(main())

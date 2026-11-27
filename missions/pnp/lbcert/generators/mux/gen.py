#!/usr/bin/env python3
"""Generator for 3-address / 8-data multiplexer HasCircuitSize witnesses.

Statement shape (BACKLOG family 5; desk L-meta-9939):
  PEqualNP.MetaComplexity.HasCircuitSize 11
    (fun x : Fin 11 => (List.ofFn x).getD
       (3 + (1*(x 0).toNat + 2*(x 1).toNat + 4*(x 2).toNat)) false) K

Method: balanced fan-in-two mux tree.  c_i = NOT a_i (3 gates); four 2:1 muxes
on the data bits with a0 (12 gates), two with a1 (6 gates), one with a2 (3 gates):
24 gates total.  Emits the merged L-meta-1001-style proof shape (namespace with
circuit def, FanInTwo by simp, eval by `decide +kernel`, final tuple).

Every gate list is audited on all 2^11 inputs before emission.  Exit 3 for any
other shape or when 24 exceeds the posted bound (no speculative 23-gate proof).
"""
import re
import sys

MATCH = r"PEqualNP\.MetaComplexity\.HasCircuitSize 11 \(fun x : Fin 11 → Bool => \(List\.ofFn x\)\.getD \(3 \+ \(1 \* \(x 0\)\.toNat \+ 2 \* \(x 1\)\.toNat \+ 4 \* \(x 2\)\.toNat\)\) false\) \d+"


def parse(stmt):
    s = " ".join(stmt.split())
    if not re.fullmatch(MATCH, s):
        return None
    return int(re.search(r"\) (\d+)$", s).group(1))


def build():
    """Return (gates, output wire); wires 0..10 inputs (a0,a1,a2,d0..d7)."""
    gates = []  # ('not'|'and'|'or', a, b)

    def emit(op, a, b=None):
        gates.append((op, a, b))
        return 11 + len(gates) - 1

    c0, c1, c2 = emit("not", 0), emit("not", 1), emit("not", 2)

    def mux(sel, nsel, lo, hi):
        a = emit("and", nsel, lo)
        b = emit("and", sel, hi)
        return emit("or", a, b)

    p = [mux(0, c0, 3 + 2 * i, 4 + 2 * i) for i in range(4)]
    t = [mux(1, c1, p[2 * i], p[2 * i + 1]) for i in range(2)]
    out = mux(2, c2, t[0], t[1])
    return gates, out


def audit(gates, out):
    for pat in range(1 << 11):
        w = [(pat >> i) & 1 for i in range(11)]
        for op, a, b in gates:
            w.append(1 - w[a] if op == "not" else
                     (w[a] & w[b] if op == "and" else w[a] | w[b]))
        want = ((pat >> (3 + ((pat & 1) + 2 * ((pat >> 1) & 1) + 4 * ((pat >> 2) & 1)))) & 1)
        if w[out] != want:
            return False
    return True


def emit_lean(gates, out, gid, stmt):
    name = gid.replace("-", "_")
    mod = "PEqualNP.Outside." + name
    glist = ", ".join(
        "⟨GateOp.%s, [%d%s]⟩" % (op, a, "" if op == "not" else ", %d" % b)
        for op, a, b in gates)
    args = " ".join("b%d" % i for i in range(11))
    args_list = ", ".join("b%d" % i for i in range(11))
    rhs = ("(List.ofFn (fun i : Fin 11 => match i with "
           "| 0 => b0 | 1 => b1 | 2 => b2 | 3 => b3 | 4 => b4 | 5 => b5 "
           "| 6 => b6 | 7 => b7 | 8 => b8 | 9 => b9 | 10 => b10)).getD "
           "(3 + (1 * b0.toNat + 2 * b1.toNat + 4 * b2.toNat)) false")
    return """import Mathlib
import PEqualNP.Defs

namespace %s

open PEqualNP.CircuitLowerBounds PEqualNP.MetaComplexity

def C0 : Circuit := ⟨[%s], %d⟩

theorem ok0 : FanInTwo C0 := by
  intro g hg
  simp only [C0, List.mem_cons, List.not_mem_nil, or_false] at hg
  rcases hg with %s <;> simp

theorem ev0 : ∀ %s : Bool, C0.eval [%s] = (%s) := by
  decide +kernel

theorem ofFn11 (x : Fin 11 → Bool) : List.ofFn x = [%s] := by
  simp [List.ofFn_succ]

end %s

theorem %s : %s :=
  ⟨%s.C0, %s.ok0, by decide, fun x => by
      rw [%s.ofFn11]
      exact %s.ev0 %s⟩
""" % (name, glist, out, " | ".join(["rfl"] * len(gates)),
       args, args_list, rhs,
       ", ".join("x %d" % i for i in range(11)), name, mod, stmt.strip(),
       name, name, name, name, args)


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: gen.py GID STATEMENT_FILE OUT.lean")
    gid = sys.argv[1]
    stmt = open(sys.argv[2]).read()
    bound = parse(stmt)
    if bound is None:
        sys.exit(3)
    gates, out = build()
    if len(gates) > bound or not audit(gates, out):
        sys.exit(3)
    open(sys.argv[3], "w").write(emit_lean(gates, out, gid, stmt))
    return 0


if __name__ == "__main__":
    sys.exit(main())

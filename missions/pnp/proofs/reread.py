"""Recognize the explicit IsAO2/size/edge-function/ReadTwiceAt data family.

Strict full-statement recognition; never treat title or partial match as proof.
The independent verification uses joint read-once trees, not scalar minima.
"""
import re

CIRCUIT = r"PEqualNP\.CircuitLowerBounds\.Circuit"
OP = r"PEqualNP\.CircuitLowerBounds\.GateOp\.(and|or)"
GATE = re.compile(r"\{ op := " + OP + r", inputs := \[(\d+), (\d+)\] \}")
PAIR = re.compile(r"\((\d+), (\d+)\)")


def _pairs(text, n):
    pairs = [(int(a), int(b)) for a, b in PAIR.findall(text)]
    if PAIR.sub("", text).replace(",", "").strip():
        raise ValueError("unexpected edge list")
    if any(not (0 <= a < n and 0 <= b < n and a != b) for a, b in pairs):
        raise ValueError("invalid edge")
    if len(pairs) != len(set(pairs)):
        raise ValueError("duplicate edge")
    return pairs


def parse(statement):
    s = " ".join(statement.split())
    # Exact grammar of the published family. If the desk changes its printer
    # or adds another condition, leave it for the researcher instead.
    header = re.match(r"∀ (\w+) : " + CIRCUIT + r", \1 = \(\{ gates := \[(.*?)\], output := (\d+) \} : " + CIRCUIT + r"\) → ", s)
    if not header:
        return None
    c, gate_text, out = header.groups()
    tail = s[header.end():]
    p = (r"PEqualNP\.TopForm\.IsAO2 (\d+) " + c + r" ∧ " + c + r"\.size = (\d+) ∧ "
         r"\(∀ (\w+) : Fin \1 → Bool, PEqualNP\.MetaComplexity\.circuitFun \1 " + c +
         r" \3 = decide \(∃ (\w+) ∈ \(\[(.*?)\] : List \(Fin \1 × Fin \1\)\), "
         r"\3 \4\.1 = true ∧ \3 \4\.2 = true\)\) ∧ "
         r"\(∀ (\w+) ∈ \(\[(.*?)\] : List \(Fin \1 × Fin \1\)\), "
         r"PEqualNP\.Core\.ReadTwiceAt \1 " + c + r" \(" + c + r"\.output - \1\) \6\.1 \6\.2 ↔ "
         r"\6 ∈ \(\[(.*?)\] : List \(Fin \1 × Fin \1\)\)\)")
    m = re.fullmatch(p, tail)
    if not m:
        return None
    n, size, _, _, edges, _, edges2, reread = m.groups()
    n, size, out = int(n), int(size), int(out)
    if not 2 <= n <= 16 or not 1 <= size <= 96 or not n <= out < n + size:
        return None
    gates = [(op, int(a), int(b)) for op, a, b in GATE.findall(gate_text)]
    if len(gates) != size or GATE.sub("", gate_text).replace(",", "").strip():
        return None
    if any(a >= n+i or b >= n+i for i, (_, a, b) in enumerate(gates)):
        return None
    try:
        e, e2, rr = _pairs(edges, n), _pairs(edges2, n), _pairs(reread, n)
    except ValueError:
        return None
    if not e or e != e2 or not set(rr) <= set(e):
        return None
    return n, gates, out, e, rr


def read_once(n, gates, output, u, v):
    # A proof tree with each leaf used at most once is represented by its
    # support mask. OR chooses one subtree; AND combines disjoint supports.
    wires = [{1} if i == u else {2} if i == v else set() for i in range(n)]
    for op, a, b in gates:
        x, y = wires[a], wires[b]
        wires.append(x | y if op == "or" else {i | j for i in x for j in y if not i & j})
    return bool(wires[output])


def verify(statement):
    parsed = parse(statement)
    if parsed is None:
        return None
    n, gates, out, edges, reread = parsed
    cases = 1 << n
    # Bitset evaluation of all assignments.
    wires = [sum(1 << row for row in range(cases) if row >> i & 1)
             for i in range(n)]
    expected = 0
    for a, b in edges:
        expected |= wires[a] & wires[b]
    for op, a, b in gates:
        wires.append(wires[a] | wires[b] if op == "or" else wires[a] & wires[b])
    mismatch = wires[out] ^ expected
    actual = [e for e in edges if not read_once(n, gates, out, *e)]
    return {"family":"explicit_reread", "verified":not mismatch and set(actual)==set(reread),
            "inputs":n, "gates":len(gates), "output":out, "cases":cases,
            "edges":edges, "expected_reread":reread, "actual_reread":actual,
            "first_counterexample":(mismatch & -mismatch).bit_length()-1 if mismatch else None,
            "local_lean_checked":False, "auto_render":n<=8}


PROOF = """intro C hC
  subst C
  refine ⟨by decide +kernel, rfl, ?_, ?_⟩
  · intro x
    revert x
    decide +kernel
  · decide +kernel"""

def main():
    """Independently inspect an explicitly supplied public or bound statement."""
    import argparse
    import json
    from pathlib import Path
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("statement",type=Path)
    a=p.parse_args()
    print(json.dumps(verify(a.statement.read_text()),ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()

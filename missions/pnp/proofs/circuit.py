"""Exact finite witness validation and Lean proof rendering."""
import re

from .. import validate
from . import reread

GATE = re.compile(r"⟨PEqualNP\.CircuitLowerBounds\.GateOp\.(and|or|not),\s*\[([0-9, ]*)\]⟩")
EDGE = re.compile(r"\(x (\d+) && x (\d+)\)")
INPUT = re.compile(r"∀ x : Fin (\d+) → Bool, C\.eval \(List\.ofFn x\) =")


def explicit_circuit(meta):
    """Recognize only explicit circuit equality rows; reject ambiguous shapes."""
    s = meta["statement"]
    r = reread.verify(s)
    if r is not None:
        # Large certificates have independent semantic checks, but the
        # small direct Lean renderer is not yet validated for that budget.
        return r if r["auto_render"] else None
    head = re.match(r"let C : PEqualNP\.CircuitLowerBounds\.Circuit := \(⟨\[(.*?)\],\s*(\d+)⟩ : PEqualNP\.CircuitLowerBounds\.Circuit\);", s, re.S)
    if not head:
        return None
    body = head.group(1)
    gates = [(m[1], [int(x.strip()) for x in m[2].split(",") if x.strip()])
             for m in GATE.finditer(body)]
    if not gates or GATE.sub("", body).replace(",", "").strip():
        return None
    m = INPUT.search(s)
    if not m:
        return None
    n, out = int(m[1]), int(head[2])
    prefix = s[head.end():m.start()].strip()
    basic = f"C.gates.length = {len(gates)} ∧ C.output = {out} ∧"
    if not prefix.startswith(basic):
        return None
    extra = prefix[len(basic):].strip()
    gate_shape = ("(∀ p ∈ C.gates.zipIdx, ((p.1.op.eval [] = true ∧ ∀ a b : Bool, "
                  "p.1.op.eval [a, b] = (a && b)) ∨ (p.1.op.eval [] = false ∧ "
                  "∀ a b : Bool, p.1.op.eval [a, b] = (a || b))) ∧ "
                  "p.1.inputs.length = 2 ∧ ∀ i ∈ p.1.inputs, i < " + str(n) + " + p.2) ∧")
    if extra not in ("", gate_shape):
        return None
    if extra and any(op not in ("and", "or") for op, _ in gates):
        return None
    if n > 12 or len(gates) > 64 or not 0 <= out < n+len(gates):
        return None
    rhs = s[m.end():].strip()
    # Accept only a disjunction of parenthesized edge conjunctions.
    if not re.fullmatch(r"[()\s]*" + EDGE.pattern + r"(?:[()\s]*\|\|[()\s]*" + EDGE.pattern + r")*[()\s]*", rhs):
        return None
    edges = [(int(a), int(b)) for a,b in EDGE.findall(rhs)]
    if not edges or any(a >= n or b >= n for a,b in edges):
        return None
    if any(len(ins) != (1 if op == "not" else 2) or any(i >= n+j for i in ins)
           for j,(op,ins) in enumerate(gates)):
        return None
    for mask in range(1 << n):
        wires = [bool(mask & (1 << i)) for i in range(n)]
        for op, ins in gates:
            xs = [wires[i] for i in ins]
            wires.append(all(xs) if op == "and" else any(xs) if op == "or" else not xs[0])
        expected = any(wires[a] and wires[b] for a,b in edges)
        if wires[out] != expected:
            return {"verified": False, "counterexample": mask, "inputs": n}
    return {"verified": True, "inputs": n, "cases": 1 << n,
            "gates": len(gates), "output": out, "edges": edges}


def render(meta, proof):
    if proof == "decide" and reread.parse(meta["statement"]) is not None:
        r = reread.verify(meta["statement"])
        if not r or not r["verified"] or not r["auto_render"]:
            raise ValueError("explicit re-read certificate does not satisfy the statement")
        proof = reread.PROOF
    imports = ["Mathlib"] + [m for m in meta["imports"] if m != "Mathlib"]
    text = "\n".join("import "+m for m in imports) + "\n\n"
    text += "set_option maxRecDepth 100000 in\nset_option maxHeartbeats 0 in\n"
    text += "theorem " + meta["module"] + " : " + meta["statement"] + " := by\n  " + proof + "\n"
    validate.validate(meta, text.encode())
    return text

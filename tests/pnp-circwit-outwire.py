"""Regression: circwit must emit the wire beam_search verified as the target.

beam_search can find the target on an earlier wire (for example a bare input
projection). Emitting the last gate wire then produces a false theorem that
fails to compile while structure-only validation still says 'generated'.
"""
import importlib.util
import re
import unittest
from pathlib import Path

GEN = (Path(__file__).resolve().parents[1] /
       "missions/pnp/lbcert/generators/circwit/gen.py")
_spec = importlib.util.spec_from_file_location("circwit_gen", GEN)
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)


def statement(mask, bound=3):
    return ("∃ C : PEqualNP.CircuitLowerBounds.Circuit, "
            "PEqualNP.MetaComplexity.FanInTwo C ∧ "
            "(∃ g ∈ C.gates, g.op = PEqualNP.CircuitLowerBounds.GateOp.not ∧ "
            "g.inputs.length = 1) ∧ C.size ≤ %d ∧ "
            "∀ x : Fin 2 → Bool, "
            "Nat.testBit (0 * 2 ^ 32 + %d) (∑ i, x i)" % (bound, mask))


def emitted_output(code):
    # The last "], N⟩" is the circuit output index; gate inputs are "[i]" and
    # do not contain a comma-separated numeric index before the bracket.
    m = re.search(r"\], (\d+)⟩", code)
    assert m is not None, "no witness circuit output in emitted candidate"
    return int(m.group(1))


class CircwitOutwire(unittest.TestCase):
    def test_input_projection_is_not_emitted_as_last_wire(self):
        # n=2, target = x0 -> rows 0,1,0,1 (mask 10). beam_search returns the
        # bare input wire 0, while the last gate wire is n + len(gates) - 1.
        stmt = statement(10)
        parsed = gen.parse(stmt)
        self.assertIsNotNone(parsed)
        n, bound, target = parsed
        self.assertEqual((n, target), (2, [0, 1, 0, 1]))
        found = gen.beam_search(n, target, bound, seed=0)
        self.assertIsNotNone(found)
        gates, outwire = found
        self.assertEqual(outwire, 0)
        self.assertNotEqual(outwire, n + len(gates) - 1)
        code = gen.emit(n, bound, stmt, gates, outwire)
        self.assertEqual(emitted_output(code), outwire)

    def test_emitted_output_equals_verified_wire(self):
        # Covers an input projection (mask 10) and a NOT-gate wire (mask 5).
        for mask in (10, 5):
            stmt = statement(mask)
            n, bound, target = gen.parse(stmt)
            gates, outwire = gen.beam_search(n, target, bound, seed=0)
            code = gen.emit(n, bound, stmt, gates, outwire)
            self.assertEqual(emitted_output(code), outwire, "mask %d" % mask)


if __name__ == "__main__":
    unittest.main()

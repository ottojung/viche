"""Rectangle witness search: exact target audit and bounded fallback."""
import importlib.util
import sys
from pathlib import Path
import unittest

p=Path(__file__).resolve().parents[1]/"missions/pnp/lbcert/generators/rectcover/gen.py"
spec=importlib.util.spec_from_file_location("rectcover",p)
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

class TestRectangles(unittest.TestCase):
    def test_sat_improves_greedy(self):
        try:import pysat
        except ImportError:self.skipTest("optional PySAT not installed")
        rows=[0,6,5,12];n=4;boxes=r.candidates(rows,n)
        masks=[r.rectangle_mask(a,b,n) for a,b in boxes]
        target=sum(x<<(i*n) for i,x in enumerate(rows))
        self.assertEqual(len(r.greedy(masks,target,tries=1)),4)
        selected=r.bounded_sat(masks,target,3,seconds=5)
        self.assertIsNotNone(selected)
        self.assertTrue(r.audit([boxes[i] for i in selected],rows,n,3))
        self.assertIsNone(r.bounded_sat(masks,target,2,seconds=5))
    def test_audit_and_negative_color(self):
        rows=[0b001,0b010,0b100]
        cover=r.cover_rectangles(rows,3,False,3)
        self.assertTrue(r.audit(cover,rows,3,3))
        self.assertFalse(r.audit([(7,7)],rows,3,3))
        self.assertIsNone(r.cover_rectangles(rows,3,False,2,seconds=1))
        self.assertEqual(r.cover_rectangles([7,7],3,True,0),[])
    def test_exact_statement(self):
        s="∃ L : List (Finset (Fin 2) × Finset (Fin 2)), L.length ≤ 2 ∧ (∀ r ∈ L, ∀ i ∈ r.1, ∀ j ∈ r.2, (([1, 2] : List ℕ).getD i.val 0).testBit j.val = true) ∧ ∀ (i : Fin 2) (j : Fin 2), (([1, 2] : List ℕ).getD i.val 0).testBit j.val = true → ∃ r ∈ L, i ∈ r.1 ∧ j ∈ r.2"
        self.assertEqual(r.parse(s),(2,2,2,[1,2],False))
        self.assertFalse(r.matches(s.replace("true →","false →")))
        self.assertFalse(r.matches(s.replace("([1, 2] : List ℕ).getD", "([2, 1] : List ℕ).getD",1)))
        code=r.emit("L-meta-99",s,2,2,[1,2],False,[(1,1),(2,2)])
        self.assertIn("theorem PEqualNP.Outside.L_meta_99 :",code)
if __name__=="__main__":unittest.main()

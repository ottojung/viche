import importlib.util
import itertools
import unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"missions/pnp/lbcert/generators/edgecover/gen.py"
s=importlib.util.spec_from_file_location("edge",p);e=importlib.util.module_from_spec(s);s.loader.exec_module(e)
class EdgeCover(unittest.TestCase):
    def test_exact_dnf(self):
        s="∃ C : PEqualNP.CircuitLowerBounds.Circuit, PEqualNP.MetaComplexity.Monotone2 C ∧ C.size ≤ 3 ∧ ∀ x : Fin 3 → Bool, C.eval (List.ofFn x) = (fun x : Fin 3 → Bool => (x 0 && x 1) || (x 0 && x 2)) x"
        n,k,edges,rhs=e.parse(s)
        self.assertEqual((n,k,edges),(3,3,[(0,1),(0,2)]))
        self.assertFalse(e.matches(s.replace("x 0 && x 1","x 0 && x 1 && x 2")))
        self.assertFalse(e.matches(s.replace("x 0 && x 1","!x 0 && x 1")))
        self.assertFalse(e.matches(s.replace("x 0 && x 1","x 0 && x 7")))
        code=e.emit("L-meta-99",s,n,e.star_cover(n,edges,k),rhs)
        self.assertEqual(code.count("theorem "),1)
        self.assertIn("= ((b0 && b1) || (b0 && b2)) :=",code)
    def test_exact_budget_and_truth_table(self):
        edges=[(0,1),(0,2),(1,3),(2,4),(3,5),(4,5),(6,7)]
        self.assertIsNone(e.star_cover(8,edges,9))
        gates=e.star_cover(8,edges,10)
        self.assertEqual(len(gates),10)
        for row in itertools.product((False,True),repeat=8):
            w=list(row)
            for op,a,b in gates:w.append(w[a] and w[b] if op=="and" else w[a] or w[b])
            self.assertEqual(w[-1],any(row[a] and row[b] for a,b in edges))
if __name__=="__main__":unittest.main()

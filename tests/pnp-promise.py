import unittest,sys,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp.lbcert.generators.promise import gen as g

class Promise(unittest.TestCase):
    def test_parse_matrix_two(self):
        p=g.parse("PEqualNP.Represents.RepSizeAtMost (fun (u : Fin 2) (v : Fin 3) => (19 : ℕ).testBit (3 * u.val + v.val)) 5")
        self.assertEqual(p,("matrix",2,3,5,19,"Monotone2"))
        self.assertFalse(g.parse("PEqualNP.Represents.RepSizeAtMost (fun (u : Fin 2) (v : Fin 3) => (19 : ℕ).testBit (2 * u.val + v.val)) 5"))
        p=("two",3,3,4,1<<1,"FanInTwo")
        self.assertTrue(g.valid(p,([("and",[0,1])],3)))
        self.assertFalse(g.valid(p,([("or",[0,1])],3)))
    def test_parenthesized_matrix_statement(self):
        statement = "PEqualNP.Represents.RepSizeAtMost (fun u v : Fin 8 => (4081470838034108865 : ℕ).testBit (8 * u.val + v.val)) 28"
        self.assertEqual(g.parse(statement),g.parse("(("+statement+"))"))
        self.assertIsNone(g.parse("("+statement+") ∧ True"))
    def test_mixed_rectangle_fallback(self):
        from unittest.mock import patch
        p=("matrix",8,8,31,5582313321192137625,"Monotone2")
        # Fixed iteration bound, independent of CI host performance.
        with patch.object(g.time,"monotonic",return_value=0):
            s=g.matrix_mixed(p)
        self.assertIsNotNone(s)
        self.assertTrue(g.valid(p,s))
        self.assertLessEqual(len(s[0]),31)
        self.assertIsNone(g.matrix_mixed(("matrix",8,8,0,p[4],"Monotone2")))
        self.assertIsNone(g.matrix_mixed(("two",5,5,8,23,"Monotone2")))
    def test_mixed_rectangle_exact_semantics(self):
        from unittest.mock import patch
        with patch.object(g.time,"monotonic",return_value=0):
            for mask in range(1,15):
                p=("matrix",2,2,8,mask,"Monotone2")
                sol=g.matrix_mixed(p)
                self.assertIsNotNone(sol)
                self.assertTrue(g.valid(p,sol))
    def test_generated_witnesses_audited(self):
        for kind,n,m in (("matrix",2,3),("two",3,3)):
            for mask in (0,1,3,7,19,63):
                p=(kind,n,m,12,mask,"FanInTwo")
                s=g.heuristic(p,.05) or g.small_formula(p) or g.synth_sat(p,.1)
                if s is not None:self.assertTrue(g.valid(p,s))
    def test_sketch_and_semantics(self):
        p=("two",3,3,1,1<<1,"FanInTwo")
        self.assertTrue(g.valid(p,g.sketch_witness(p,"A held answer: AND(0,1)")))
        self.assertIsNone(g.sketch_witness(p,"AND(0,7)"))
        self.assertIsNone(g.sketch_witness(p,"OR(0,1)"))
    def test_relabel(self):
        a=("matrix",2,2,3,1,"Monotone2")
        b=("matrix",2,2,3,8,"Monotone2")
        v=([("and",[0,2])],4)
        self.assertTrue(g.valid(b,g.transport(a,b,v)))
    def test_sat_audit(self):
        p=("matrix",2,2,1,1,"Monotone2")
        try:import pysat
        except ImportError:self.skipTest("pysat unavailable")
        self.assertTrue(g.valid(p,g.synth_sat(p,.5)))
    def test_compiled_anneal_semantics(self):
        from missions.pnp.lbcert.generators.promise import anneal
        from unittest.mock import patch
        p=("matrix",2,2,1,1,"Monotone2")
        if anneal.executable() is not None:
            self.assertTrue(g.valid(p,anneal.search(p,g,.5)))
        with patch.object(anneal,"executable",return_value=None):
            self.assertIsNone(anneal.search(p,g))
        self.assertIsNone(anneal.search(("matrix",10,10,2,1,"FanInTwo"),g))
    def test_corpus_literal(self):
        p=("matrix",2,2,1,1,"Monotone2")
        self.assertEqual(g.lean_witness(p,"def w := ⟨[⟨.and, [0, 2]⟩], 4⟩"),([("and",[0,2])],4))
if __name__=="__main__":unittest.main()

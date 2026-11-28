#!/usr/bin/env python3
"""Check transported leaf samples and candidate shape, not kernel validity."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp.lbcert.generators.core_reuse import gen
from missions.pnp import validate

def statement(mask):
    body=f"Nat.testBit ({mask>>32} * 2 ^ 32 + {mask&gen.FULL32}) (∑ i : Fin 6, if x i then 2 ^ (i : ℕ) else 0)"
    st=("∀ s : ℕ, PEqualNP.MetaComplexity.HasCircuitSize 6 (fun x : Fin 6 → Bool => "+body+
        ") s → ∃ C : PEqualNP.CircuitLowerBounds.Circuit, PEqualNP.MetaComplexity.Monotone2 C ∧ C.size ≤ s ∧ "+
        "∀ x : Fin 6 → Bool, C.eval (List.ofFn x) = "+body)
    return st,body

class Tests(unittest.TestCase):
    def test_all_index_samples(self):
        idx=gen.index()
        self.assertEqual(len(idx),690)
        for mask,(floor,cols,roots,source) in idx.items():
            self.assertTrue(gen.sample_ok(mask,cols))
            self.assertTrue(all(w in roots or w in (0,gen.FULL64) for w in cols))
            self.assertGreater(floor,0)
            self.assertTrue(source.startswith("L-meta-"))
    def test_two_cofactor_proof_shape(self):
        mask=0xfeeaeee8feeaeae8 # L-meta-37045, excluded from certificate sources
        st,body=statement(mask)
        plan=gen.route(mask)
        self.assertEqual(plan[0],10)
        self.assertEqual(len(plan[2]),2)
        f=[mask>>r&1 for r in range(64)]
        w=gen.monotone_witness.synthesize(6,f,width=8)
        self.assertLessEqual(len(w),11)
        self.assertTrue(all(gen.onenot.evaluate(6,w,r)==f[r] for r in range(64)))
        out=gen.emit("L-meta-999997",st,body,mask,plan,w)
        meta={"id":"L-meta-999997","file":"lean/PEqualNP/Outside/L_meta_999997.lean","module":"PEqualNP.Outside.L_meta_999997","statement":st,"imports":["PEqualNP.Defs"]}
        self.assertEqual(len(validate.validate(meta,out.encode())),64)
        self.assertIn("lemma sixLower : Low 10 sixTarget := two",out)
        self.assertIn("lemma leaf_0",out)
        self.assertIn("lemma leaf_1",out)
    def test_reject_nonmatching(self):
        self.assertFalse(gen.matches("True"))
        self.assertIsNone(gen.route(0))
        st,_=statement(0xffffffffffffffff)
        self.assertFalse(gen.matches(st))

if __name__=="__main__":unittest.main()

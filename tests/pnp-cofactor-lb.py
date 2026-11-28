#!/usr/bin/env python3
"""Offline exact row-transport and candidate-shape tests; no Lean execution."""
import hashlib
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp.lbcert.generators.cofactor_lb import gen
from missions.pnp import validate
from missions.pnp.lbcert import plugins

GID="L-meta-999997"
MODULE="PEqualNP.Outside.L_meta_999997"
AND={0:0,1:0,2:0,3:1}
OR={0:0,1:1,2:1,3:1}

def statement(mask):
    body=f"Nat.testBit ({mask>>32} * 2 ^ 32 + {mask&gen.FULL32}) (∑ i : Fin 6, if x i then 2 ^ (i : ℕ) else 0)"
    st=("∀ s : ℕ, PEqualNP.MetaComplexity.HasCircuitSize 6 (fun x : Fin 6 → Bool => "+body+
        ") s → ∃ C : PEqualNP.CircuitLowerBounds.Circuit, PEqualNP.MetaComplexity.Monotone2 C ∧ C.size ≤ s ∧ "+
        "∀ x : Fin 6 → Bool, C.eval (List.ofFn x) = "+body)
    return st,body

def source_mask(i,val,order,dual):
    mask=0
    for row in range(64):
        p=sum(((row>>order[j])&1)<<j for j in range(5))
        if dual:p^=31
        g=((gen.BASE>>p)&1)^dual
        # f = g OR x_i for a low slice; f = g AND x_i for high.
        bit=(g or (row>>i&1)) if val==0 else (g and (row>>i&1))
        mask|=int(bit)<<row
    return mask

class Tests(unittest.TestCase):
    def test_all_certified_orbits_on_every_slice(self):
        self.assertEqual(len(gen.orbit()),40)
        for _,(perm,dual) in gen.orbit().items():
            for i in range(6):
                remaining=[j for j in range(6) if i!=j]
                order=tuple(remaining[j] for j in perm)+(i,)
                for val in (0,1):
                    mask=source_mask(i,val,order,dual)
                    e=next(r for r in range(64) if not r&(1<<i) and
                           ((mask>>r)^(mask>>(r|(1<<i))))&1)
                    match=(i,val,order,dual,e)
                    dom,raw,sub,moves,root,r0,r1=gen.transfer(mask,match)
                    self.assertEqual(sub&dom,mask&dom)
                    self.assertIsNotNone(gen.route(mask))
                    # Independently check every source row's destination.
                    for r in range(64):
                        p=sum(((r>>order[j])&1)<<j for j in range(6))
                        p^=31 if dual else 0
                        p^=32 if val else 0
                        self.assertEqual(gen.apply_moves(1<<r,moves),1<<p)
                    self.assertEqual(r0^r1,1<<i)

    def test_template_digest_and_static_direct_and_dual_emission(self):
        self.assertEqual(hashlib.sha256((gen.HERE/"template.lean").read_bytes()).hexdigest(),gen.TEMPLATE_SHA)
        original=0xeeeaeae8eeeaeaa8
        # Explicit 11-gate witness from the merged source, independently replayed.
        witness=[(2,3,OR),(4,6,OR),(3,5,OR),(0,1,OR),(1,7,OR),
                 (2,8,AND),(0,11,OR),(4,6,AND),(12,13,OR),(9,14,AND),(10,15,AND)]
        for dual in (False,True):
            mask=original
            w=witness
            if dual:
                mask=gen.FULL64^int(f"{original:064b}"[::-1],2)
                w=[(a,b,AND if tt==OR else OR) for a,b,tt in witness]
            f=[mask>>r&1 for r in range(64)]
            self.assertTrue(all(gen.onenot.evaluate(6,w,r)==f[r] for r in range(64)))
            # Force the known restriction, including the dual proof route.
            val=int(dual)
            match=(5,val,tuple(range(6)),dual,
                   next(r for r in range(32) if ((mask>>r)^(mask>>(r+32)))&1))
            st,body=statement(mask)
            out=gen.emit(GID,st,body,mask,match,w)
            meta={"id":GID,"file":"lean/PEqualNP/Outside/L_meta_999997.lean","module":MODULE,
                  "statement":st,"imports":["PEqualNP.Defs"]}
            self.assertEqual(len(validate.validate(meta,out.encode())),64)
            self.assertIn("lower_slice",out)
            self.assertEqual("lemma lowerNegTransfer" in out,dual)

    def test_invalid_or_unsupported_input_refused(self):
        self.assertIsNone(gen.route(0))
        self.assertFalse(gen.matches("True"))
        st,_=statement(0xffffffffffffffff)
        self.assertFalse(gen.matches(st))
        st,_=statement(0xeeeaeae8eeeaeaa8)
        self.assertTrue(gen.matches(st))
        self.assertFalse(gen.matches("¬ ("+st+")"))
        self.assertIn("cofactor_lb",plugins.discover())

if __name__=="__main__":
    unittest.main()

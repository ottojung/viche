#!/usr/bin/env python3
"""Exact truth-table tests for constructive witness improvements."""
from pathlib import Path
import random
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"missions/pnp/lbcert/onenot"))
import dontcare, monotone_witness, onenot

class Tests(unittest.TestCase):
    def test_redundant_cone(self):
        A,O=dontcare.AND,dontcare.OR
        w=[(0,1,A),(0,3,O),(2,4,A)]
        f=[int(bool(r&1 and r&4)) for r in range(8)]
        result=dontcare.compress(3,w,f,budget=0)
        self.assertEqual(len(result),1)
        self.assertEqual([onenot.evaluate(3,result,r) for r in range(8)],f)
        with self.assertRaises(ValueError):
            dontcare.compress(3,w,[0]*8,budget=0)

    def test_small_monotone_tables(self):
        # Exhaust every nonconstant, nonprojection monotone 3-input table.
        for mask in range(256):
            f=[mask>>r&1 for r in range(8)]
            if any(f[a]>f[b] for a in range(8) for b in range(8) if a&b==a):
                continue
            if mask in (0,255,0xaa,0xcc,0xf0):continue
            w=monotone_witness.synthesize(3,f,decompose=True)
            self.assertTrue(w,hex(mask))
            self.assertEqual([onenot.evaluate(3,w,r) for r in range(8)],f)
            v=dontcare.compress(3,w,f,budget=.1)
            self.assertLessEqual(len(v),len(w))
            self.assertEqual([onenot.evaluate(3,v,r) for r in range(8)],f)

    def test_random_four_input_tables(self):
        rng=random.Random(20261128)
        for _ in range(20):
            terms=rng.sample(range(1,16),5)
            f=[int(any(r&t==t for t in terms)) for r in range(16)]
            if sum(f) in (0,16) or any(f==[r>>i&1 for r in range(16)] for i in range(4)):continue
            w=monotone_witness.synthesize(4,f,decompose=True)
            self.assertTrue(w)
            v=dontcare.compress(4,w,f,budget=.1)
            self.assertLessEqual(len(v),len(w))
            self.assertEqual([onenot.evaluate(4,v,r) for r in range(16)],f)

if __name__=="__main__":unittest.main()

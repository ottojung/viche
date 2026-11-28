import json
import random
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp.lbcert.generators.hcsreuse import gen as g
from missions.pnp import validate

def stmt(n,rhs,b):
    return f"(PEqualNP.MetaComplexity.HasCircuitSize {n} (fun x : Fin {n} → Bool => {rhs}) {b})"

def scalar(n,r,sol):
    w=[bool(r>>i&1) for i in range(n)]
    gates,out=sol
    for op,inds in gates:
        vals=[w[i] for i in inds]
        w.append(all(vals) if op=="and" else any(vals) if op=="or" else not (vals[0] if vals else False))
    return out<len(w) and w[out]

class HCSReuse(unittest.TestCase):
    def test_all_data(self):
        lib=g.library()
        self.assertEqual(len(lib),1458)
        rng=random.Random(42)
        for k,v in lib.items():
            n,mask=map(int,k.split(":"))
            sol=v["solution"]
            self.assertTrue(g.valid((n,mask,len(sol[0])),sol),k)
            self.assertIsNotNone(g.lookup((n,mask,len(sol[0]))))
            if sol[0] and len(sol[0])>1:
                self.assertIsNone(g.lookup((n,mask,len(sol[0])-1)))
        for k in rng.sample(sorted(lib),30):
            n,mask=map(int,k.split(":"))
            sol=lib[k]["solution"]
            for row in range(1<<n):
                self.assertEqual(scalar(n,row,sol),bool(mask>>row&1),k)
    def test_arithmetic(self):
        terms="(1 * (x 0).toNat + 2 * (x 1).toNat + 4 * (x 2).toNat)"
        terms2="(1 * (x 3).toNat + 2 * (x 4).toNat + 4 * (x 5).toNat)"
        for bit in (2,3,4):
            p=g.parse(stmt(6,f"Nat.testBit ({terms} * {terms2}) {bit}",37))
            self.assertEqual(p[1],sum(1<<r for r in range(64) if (((r&7)*(r>>3))>>bit)&1))
            self.assertIsNotNone(g.lookup(p))
        p=g.parse(stmt(6,f"decide ({terms2} < {terms})",11))
        self.assertEqual(p[1],sum(1<<r for r in range(64) if (r&7)>r>>3))
        self.assertIsNone(g.lookup(p))
        for rhs,pred in [
            ("decide (3 ≤ ((List.ofFn x).count true))",lambda r:r.bit_count()>=3),
            ("decide (((List.ofFn x).count true) % 3 = 0)",lambda r:r.bit_count()%3==0),
            ("decide (((List.ofFn x).count true) = 2)",lambda r:r.bit_count()==2),
            ("!((x 0) && x 1) || x 2",lambda r:not(r&1 and r&2) or r&4)]:
            self.assertEqual(g.parse(stmt(6,rhs,60))[1],sum(1<<r for r in range(64) if pred(r)))
    def test_exact_shape(self):
        s=stmt(5,"decide (3 ≤ ((List.ofFn x).count true))",10)
        self.assertTrue(g.matches(s))
        for bad in ["¬ "+s,s+" ∧ True",s[1:],stmt(5,"x 5",10),stmt(5,"x 1 || junk",10)]:
            self.assertFalse(g.matches(bad))
        sol=g.lookup(g.parse(s))
        q={"id":"L-meta-11099","module":"PEqualNP.Outside.L_meta_11099","statement":s,
           "file":"lean/PEqualNP/Outside/L_meta_11099.lean","imports":["PEqualNP.Defs"]}
        validate.validate(q,g.emit(q["id"],s,sol).encode())
        self.assertFalse(g.valid((2,0,1),([("or",[0,5])],2)))
    def test_constant_and_transport(self):
        for n,mask,b in [(3,0,0),(3,255,1),(3,170,0),(3,85,1)]:
            self.assertTrue(g.valid((n,mask,b),g.lookup((n,mask,b))))
        sol=([("and",[0,1])],3)
        self.assertEqual(g.evaluate(3,g.transport(3,sol,(2,0,1))),160)
        self.assertEqual(g.evaluate(3,g.complement(3,sol)),119)

if __name__=="__main__":unittest.main()

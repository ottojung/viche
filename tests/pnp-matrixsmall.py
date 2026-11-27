import random
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp.lbcert.generators.matrixsmall import gen as m
from missions.pnp.lbcert.generators.promise import gen as g
from missions.pnp.lbcert import plugins

class SmallMatrix(unittest.TestCase):
    def test_all_entries_and_permutations(self):
        rng=random.Random(1)
        lib=m.library()
        self.assertEqual(len(lib),458)
        for key,e in lib.items():
            n,c,mask,pred=key.split(":")
            n,c,mask=int(n),int(c),int(mask)
            gates,out=e["solution"]
            q=("matrix",n,c,len(gates),mask,pred)
            self.assertTrue(g.valid(q,(gates,out)),key)
            self.assertIsNotNone(m.lookup(q),key)
            r=list(range(n));s=list(range(c));rng.shuffle(r);rng.shuffle(s)
            z=sum((mask>>(r[i]*c+s[j])&1)<<(i*c+j) for i in range(n) for j in range(c))
            q=("matrix",n,c,len(gates),z,pred)
            self.assertTrue(g.valid(q,m.lookup(q)),key)
            t=m.transpose(q)
            self.assertTrue(g.valid(t,m.lookup(t)),key)
    def test_exact_family_and_emit(self):
        from missions.pnp import validate
        s="∃ C : PEqualNP.CircuitLowerBounds.Circuit, PEqualNP.MetaComplexity.FanInTwo C ∧ C.size ≤ 6 ∧ PEqualNP.Represents.Represents (fun (u : Fin 4) (v : Fin 4) => (([13, 13, 2, 1] : List ℕ).getD u.val 0).testBit v.val) C"
        p=m.parse(s)
        self.assertTrue(m.matches(s))
        q={"id":"L-meta-26307","module":"PEqualNP.Outside.L_meta_26307","statement":s,
           "file":"lean/PEqualNP/Outside/L_meta_26307.lean","imports":["PEqualNP.Defs"]}
        validate.validate(q,g.emit(q["id"],s,p,m.lookup(p)).encode())
        self.assertFalse(m.matches("¬ ("+s+")"))
        self.assertFalse(m.matches(s+" ∧ True"))
        self.assertFalse(m.matches(s.replace("≤ 6","≤ 0")))
    def test_data_version_is_included(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"gen.py";p.write_text("pass")
            h=plugins.fingerprint(p)
            d=p.with_name("witnesses.json");d.write_text("{}")
            h2=plugins.fingerprint(p)
            self.assertNotEqual(h,h2)
            d.write_text("[]")
            self.assertNotEqual(h2,plugins.fingerprint(p))

if __name__=="__main__":unittest.main()

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from missions.pnp.lbcert.generators.gateelim import gen
from missions.pnp.validate import validate

def meta(gid,s):
    n=gid.replace("-","_")
    return dict(id=gid,module="PEqualNP.Outside."+n,file="lean/PEqualNP/Outside/"+n+".lean",imports=["PEqualNP.Defs"],statement=s)

class GateElimination(unittest.TestCase):
    def test_basic_bounds(self):
        b=gen.bounds
        self.assertEqual(b.lower((1,))[0],0)
        self.assertEqual(b.lower((3,))[0],1)
        self.assertEqual(b.lower(b.normalize([3,6,12]))[0],4)
        self.assertEqual(b.lower(b.normalize([273,161,266,98,140,84]))[0],13)

    def test_seeded_exact_emit(self):
        s=json.loads(gen.checked("shape.json",gen.SHAPE_SHA))
        e=gen.parse(s)
        self.assertIsNotNone(e)
        self.assertTrue(gen.matches(s))
        text=gen.generate("L-meta-27817",s)
        self.assertEqual(len(validate(meta("L-meta-27817",s),text.encode())),64)
        self.assertIn("rule3B",text)
        self.assertFalse(gen.matches("¬ ("+s+")"))
        self.assertFalse(gen.matches(s.replace("Fin 8","Fin 9",1)))
        self.assertIsNone(gen.generate("L-pcx-1",s))

    def test_seed_witnesses(self):
        for k,r in gen.seeds().items():
            e=tuple(tuple(map(int,p.split(","))) for p in k.split(";"))
            f=gen.bounds.normalize((1<<i)|(1<<j) for i,j in e)
            b,_=gen.bounds.lower(f)
            w=gen.feasible(e)
            self.assertEqual(b,r["bound"],k)
            self.assertLessEqual(len(w),b+1,k)
            for x in range(256):
                v=[bool(x>>i&1) for i in range(8)]
                for i,j,tt in w:
                    self.assertTrue(0<=i<len(v) and 0<=j<len(v) and i!=j)
                    v.append(bool(tt[int(v[i])+2*int(v[j])]))
                self.assertEqual(v[-1],gen.truth(f,x),k)

    def test_refusal_falls_through(self):
        s=json.loads(gen.checked("shape.json",gen.SHAPE_SHA))
        with patch.object(gen,"feasible",return_value=None):
            self.assertFalse(gen.matches(s))
            self.assertIsNone(gen.generate("L-meta-27817",s))

if __name__=="__main__":unittest.main()

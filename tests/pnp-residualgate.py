import json,re,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from missions.pnp.lbcert.generators.gateelim_residual import gen
from missions.pnp.validate import validate

def statement(key):
    g=gen.shape()
    s=json.loads(g.checked("shape.json",g.SHAPE_SHA))
    old=re.search(r"\[[0-9, ]+\](?= : List ℕ)",s).group()
    edges=[int(n) for pair in key.split(";") for n in pair.split(",")]
    return s.replace(old,str(edges))

class Residual(unittest.TestCase):
    def test_seeded_sources_exact_and_bounded(self):
        self.assertEqual(len(gen.seeds()),16)
        for key,row in gen.seeds().items():
            s=statement(key)
            gid="L-meta-999999"
            meta=dict(id=gid,module="PEqualNP.Outside.L_meta_999999",
                      file="lean/PEqualNP/Outside/L_meta_999999.lean",
                      imports=["PEqualNP.Defs"],statement=s)
            self.assertTrue(gen.matches(s),key)
            self.assertLessEqual(len(row["witness"]),row["bound"]+1)
            text=gen.generate(gid,s)
            self.assertIn("base v",text)
            self.assertEqual(len(validate(meta,text.encode())),64,key)
            self.assertFalse(gen.matches("¬ ("+s+")"))
            self.assertFalse(gen.matches(s.replace("Fin 8","Fin 9",1)))
            self.assertIsNone(gen.generate("L-pcx-1",s))
    def test_library_samples(self):
        data=json.loads(gen.read(gen.HERE/"bases.json",gen.BASE_SHA))
        self.assertEqual(len(data),6)
        for key,row in data.items():
            f=tuple(map(int,key.split(";")))
            truth=lambda x:any(x&t==t for t in f)
            self.assertTrue(all(truth(a) and not truth(z) and (a^z).bit_count()==1
                                for a,z in row["pairs"]))
            self.assertGreater(row["bound"],0)

if __name__=="__main__":unittest.main()

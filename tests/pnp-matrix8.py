import random,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp.lbcert.generators.matrix8 import gen as m
from missions.pnp.lbcert.generators.promise import gen as g

class Matrix8(unittest.TestCase):
    def test_all_public_entries(self):
        lib=m.library()
        self.assertEqual(len(lib),62)
        for key,item in lib.items():
            p=("matrix",8,8,len(item["solution"][0]),int.from_bytes(bytes.fromhex(key),"little"),"Monotone2")
            self.assertTrue(g.valid(p,item["solution"]))
            self.assertEqual(m.canon(p[4])[0],key)
            self.assertTrue(g.valid(p,m.lookup(p)))
            if p[3]:self.assertIsNone(m.direct_lookup(p[:3]+(p[3]-1,)+p[4:]))
    def test_permuted_witnesses(self):
        rng=random.Random(4)
        for key,item in sorted(m.library().items()):
            mask=int.from_bytes(bytes.fromhex(key),"little")
            r=list(range(8));c=list(range(8));rng.shuffle(r);rng.shuffle(c)
            z=sum((mask>>(8*r[i]+c[j])&1)<<(8*i+j) for i in range(8) for j in range(8))
            self.assertEqual(m.canon(z)[0],key)
            p=("matrix",8,8,len(item["solution"][0]),z,"Monotone2")
            self.assertTrue(g.valid(p,m.lookup(p)))
    def test_transpose_witness_reuse(self):
        # Independent historical holdout for which row/column relabeling alone failed.
        p=("matrix",8,8,32,0,"Monotone2")
        # Every stored circuit must also work after swapping the two blocks.
        for key,item in m.library().items():
            mask=int.from_bytes(bytes.fromhex(key),"little")
            q=p[:3]+(len(item["solution"][0]),m.transpose(mask),p[-1])
            sol=m.lookup(q)
            self.assertIsNotNone(sol)
            self.assertTrue(g.valid(q,sol))
        # Confirm that the fallback, not merely direct matching, is exercised.
        self.assertTrue(any(m.direct_lookup(p[:3]+(len(v["solution"][0]),m.transpose(int.from_bytes(bytes.fromhex(k),"little")),p[-1])) is None
                            for k,v in m.library().items()))
    def test_exact_statement_and_fallback(self):
        from missions.pnp import validate
        stmt="(PEqualNP.Represents.RepSizeAtMost (fun u v : Fin 8 => (4081470838034108865 : ℕ).testBit (8 * u.val + v.val)) 28)"
        p=m.parse(stmt);self.assertTrue(m.matches(stmt))
        sol=m.lookup(p)
        self.assertTrue(g.valid(p,sol))
        q={"id":"L-meta-19710","module":"PEqualNP.Outside.L_meta_19710","statement":stmt,
           "file":"lean/PEqualNP/Outside/L_meta_19710.lean","imports":["PEqualNP.Defs"]}
        validate.validate(q,g.emit(q["id"],stmt,p,sol).encode())
        self.assertFalse(m.matches(stmt.replace("28)","1)")))
        self.assertFalse(m.matches("True"))
if __name__=="__main__":unittest.main()

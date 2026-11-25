"""Independent checks of explicit-row multi-output search and monotone bank coverage."""
import itertools
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp.proofs import bank, rows

class Test(unittest.TestCase):
    def test_multi_output_and_disjunction(self):
        raw={"n":2,"gates":2,"ops":["and","or"],
             "outputs":[{"name":"a","ones":[3],"zeros":[0,1,2]},
                        {"name":"b","ones":[1,2,3],"zeros":[0]}],
             "groups":[[[0,1,0],[1,2,0]]]}
        w={"gates":[["and",0,1],["or",0,1]],"outputs":[2,3]}
        self.assertTrue(rows.verify(raw,w)["verified"])
        self.assertFalse(rows.verify(raw,{**w,"outputs":[3,2]})["verified"])
        result=rows.solve(raw,5)
        if result["result"]=="unavailable":self.skipTest("optional solver unavailable")
        self.assertEqual(result["result"],"verified_rows")
        self.assertTrue(rows.verify(raw,result)["verified"])
        raw["gates"]=1
        self.assertEqual(rows.solve(raw,5)["result"],"unsat_encoding")

    def test_group_is_not_all_literals(self):
        raw={"n":2,"gates":0,"outputs":[{"name":"a","wire":0}],
             "groups":[[[0,1,0],[0,2,0]]]}
        self.assertTrue(rows.verify(raw,{"gates":[],"outputs":[0]})["verified"])
        raw["groups"]=[[[0,1,0]]]
        self.assertFalse(rows.verify(raw,{"gates":[],"outputs":[0]})["verified"])
        r=rows.solve(raw,5)
        if r["result"]=="unavailable":self.skipTest("optional solver unavailable")
        self.assertEqual(r["result"],"unsat_encoding")

    def test_bank_rows_exact_for_monotone_circuits(self):
        raw={"n":4,"left":[0,1],"edges":[[0,2],[0,3],[1,3]],"gates":2,
             "or_output":[2,3],"require_masked_edge":True}
        s=bank.generate(raw)
        E=raw["edges"]
        def check_full(gates,outs):
            for r in range(16):
                w=[(r>>i)&1 for i in range(4)]
                for k,a,b in gates:w.append(w[a]&w[b] if k=="and" else w[a]|w[b])
                no=not any(w[p] and w[l] for p,l in E)
                for p,l in E:
                    if w[p] and w[l] and not w[outs[p]]:return False
                    if no and w[p] and w[outs[p]]:return False
                if w[outs[2]] != (w[2] or w[3]):return False
            # Check existential condition by direct per-singleton evaluation.
            for p,l in E:
                w=[int(i==l) for i in range(4)]
                for k,a,b in gates:w.append(w[a]&w[b] if k=="and" else w[a]|w[b])
                if not w[outs[p]]:return True
            return False
        # All 0/1-gate circuits and all output choices; compare against
        # independent full-domain semantics, not the row construction.
        circuits=[[]]+[[[k,a,b]] for k in ("and","or") for a in range(4) for b in range(a,4)]
        for gates in circuits:
            for outs in itertools.product(range(4+len(gates)),repeat=3):
                self.assertEqual(rows.verify(s,{"gates":gates,"outputs":list(outs)})["verified"],check_full(gates,outs))
        witness={"gates":[["or",2,3],["and",0,4]],"outputs":[5,3,4]}
        self.assertTrue(check_full(witness["gates"],witness["outputs"]))
        self.assertTrue(rows.verify(s,witness)["verified"])
        result=rows.solve(s,5)
        if result["result"]=="unavailable":self.skipTest("optional solver unavailable")
        self.assertEqual(result["result"],"verified_rows")
        self.assertTrue(check_full(result["gates"],result["outputs"]))

    def test_checkpoint_and_validation(self):
        s={"n":25,"gates":1,"outputs":[{"name":"wide","ones":[1<<24],"zeros":[0]}]}
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp,"cp.json")
            r=rows.solve(s,5,path)
            if r["result"]=="unavailable":self.skipTest("optional solver unavailable")
            self.assertEqual(r["result"],"verified_rows")
            self.assertTrue(path.exists())
            with self.assertRaises(ValueError):rows.solve(dict(s,gates=2),5,path)
        for invalid in (
            {"gates":[["and",-1,0]],"outputs":[0]},
            {"gates":[],"outputs":[25]},
            {"gates":[["not",0]],"outputs":[25]},
        ):
            with self.assertRaises(ValueError):rows.verify(s,invalid)

if __name__=="__main__":
    unittest.main(verbosity=2)

"""Offline tests for version-bound staging and exact receipt admission."""
import sys,tempfile,time,hashlib,unittest,io,contextlib,json
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp.lbcert.generators.promise import batch as b
from missions.pnp import config, allocator
from missions.pnp.lbcert import ready

GID="L-meta-24806"
MODULE="PEqualNP.Outside.L_meta_24806"
STATEMENT=("∃ C : PEqualNP.CircuitLowerBounds.Circuit, PEqualNP.MetaComplexity.FanInTwo C ∧ C.size ≤ 9 ∧ "
           "∀ i j : Fin 6, C.eval (List.ofFn fun k : Fin 6 => decide (k = i ∨ k = j)) = "
           "(2 : ℕ).testBit (6 * min i.val j.val + max i.val j.val)")
Q={"id":GID,"module":MODULE,"statement":STATEMENT,"file":"lean/PEqualNP/Outside/L_meta_24806.lean","imports":["PEqualNP.Defs"],"pr_open":0}

class Tests(unittest.TestCase):
    def test_versioned_attempts_and_fallback(self):
        with tempfile.TemporaryDirectory() as d,patch.object(config,"STATE_ROOT",d),patch.object(config,"GAPS_DIR",d+"/gaps"):
            b.root().mkdir()
            db=b.database(b.root()/"promise-batch.sqlite")
            v=b.version();k=b.key(Q,v)
            self.assertTrue(b.claimed(Q,set()))
            b.put(db,k,"refused")
            self.assertFalse(b.claimed(Q,b.fallback_keys()))
            self.assertIsNone(b.get(db,b.key(Q,v+"changed")))
            b.put(db,k,"staged","candidate",4)
            self.assertEqual(b.get(db,k)["source"],"candidate")
            self.assertTrue(b.claimed(Q,b.fallback_keys()))
            self.assertEqual(b.batch_status()["attempts"],{"staged":1})
            with patch.object(sys,"argv",["batch","--status"]),contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(b.main(),0)
                self.assertEqual(json.loads(output.getvalue())["attempts"],{"staged":1})
            db.close()
    def test_current_competition_and_exact_lease(self):
        row={"held":1,"parallel":1}
        self.assertFalse(b.eligible(Q,row,None))
        self.assertTrue(b.eligible(Q,{"held":0,"parallel":1},None))
        self.assertFalse(b.eligible({**Q,"pr_open":1},{"held":0,"parallel":1},None))
        rec={"state":"LEASED","statement":STATEMENT,"lease":"fixture","lease_expires_at":time.time()+1000}
        self.assertTrue(b.eligible(Q,row,rec))
        self.assertFalse(b.eligible(Q,row,{**rec,"statement":"changed"}))
        self.assertFalse(b.eligible(Q,row,{**rec,"candidate_digest":"busy"}))
    def test_candidate_semantics_and_receipt(self):
        p=b.gen.parse(STATEMENT);source,gates,_=b.candidate(Q,p)
        self.assertTrue(source);self.assertLessEqual(gates,9)
        with tempfile.TemporaryDirectory() as d,patch.object(config,"STATE_ROOT",d),patch.object(config,"GAPS_DIR",d+"/gaps"):
            b.root().mkdir()
            with patch.object(b.checkremote,"check",return_value=(0,{"status":"ok","sha256":"bad","checked_base":"a"*40})):
                self.assertEqual(b.verify(Q,source)[0],"transient")
                self.assertIsNone(ready.verified(GID))
                self.assertFalse((ready.directory()/(GID+".lean")).exists())
            receipt={"status":"ok","sha256":hashlib.sha256(source.encode()).hexdigest(),"checked_base":"a"*40,"id":"fixture"}
            with patch.object(b.checkremote,"check",return_value=(0,receipt)),patch.object(allocator,"proof_of_now",return_value="acquired") as claim:
                self.assertEqual(b.verify(Q,source)[0],"checked")
                claim.assert_called_once_with(GID)
                self.assertEqual(ready.verified(GID)["digest"],receipt["sha256"])
    def test_shared_dag_reduces_formula_cost(self):
        from missions.pnp.lbcert.generators.promise import dag
        p=("two",6,6,9,4362044,"FanInTwo")
        witness=dag.search(p,3)
        self.assertTrue(witness)
        self.assertTrue(b.gen.valid(p,witness))
        self.assertLessEqual(len(witness[0]),9)
    def test_transient_does_not_become_checked(self):
        with tempfile.TemporaryDirectory() as d,patch.object(config,"STATE_ROOT",d),patch.object(config,"GAPS_DIR",d+"/gaps"):
            b.root().mkdir()
            source,_,_=b.candidate(Q,b.gen.parse(STATEMENT))
            with patch.object(b.checkremote,"check",return_value=(2,{"status":"busy"})):
                self.assertEqual(b.verify(Q,source)[0],"transient")
                self.assertIsNone(ready.verified(GID))
if __name__=="__main__":unittest.main()

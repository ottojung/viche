"""Offline tests for version-bound staging and exact receipt admission."""
import sys,tempfile,time,hashlib,unittest,io,contextlib,json
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp.lbcert.generators.promise import batch as b
from missions.pnp import config, jobs, state
from missions.pnp.lbcert import ready

GID="L-meta-24806"
MODULE="PEqualNP.Outside.L_meta_24806"
STATEMENT=("∃ C : PEqualNP.CircuitLowerBounds.Circuit, PEqualNP.MetaComplexity.FanInTwo C ∧ C.size ≤ 9 ∧ "
           "∀ i j : Fin 6, C.eval (List.ofFn fun k : Fin 6 => decide (k = i ∨ k = j)) = "
           "(2 : ℕ).testBit (6 * min i.val j.val + max i.val j.val)")
Q={"id":GID,"module":MODULE,"statement":STATEMENT,"file":"lean/PEqualNP/Outside/L_meta_24806.lean","imports":["PEqualNP.Defs"],"pr_open":0,"offerable_now":True}

class Tests(unittest.TestCase):
    def test_stop_blocks_publication(self):
        with tempfile.TemporaryDirectory() as d,patch.object(config,"STATE_ROOT",d):
            b.root().mkdir();(b.root()/"STOP").touch()
            with patch.object(jobs,"submit") as submit:
                self.assertEqual(b.publish_staged(Q,"fixture","lease"),("transient","generator paused"))
                submit.assert_not_called()

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
    def test_held_staging_and_lease_fence(self):
        p=b.gen.parse(STATEMENT);source,gates,_=b.candidate(Q,p)
        self.assertTrue(source);self.assertLessEqual(gates,9)
        digest=hashlib.sha256(source.encode()).hexdigest()
        rec={"state":"LEASED","statement":STATEMENT,"lease":"fixture","lease_expires_at":time.time()+1000}
        with tempfile.TemporaryDirectory() as d,patch.object(config,"STATE_ROOT",d),patch.object(config,"GAPS_DIR",d+"/gaps"):
            b.root().mkdir()
            with patch.object(state,"load",return_value=None),patch.object(jobs,"submit") as submit:
                self.assertEqual(b.publish_staged(Q,source,"fixture")[0],"transient")
                submit.assert_not_called()
                self.assertIsNone(ready.verified(GID))
            with patch.object(state,"load",return_value=rec),patch.object(jobs,"submit") as submit:
                self.assertEqual(b.publish_staged(Q,source,"old")[0],"transient")
                submit.assert_not_called()
            def publish(gid,path,*,expected_lease,only_unclaimed):
                self.assertEqual(gid,GID);self.assertEqual(Path(path).read_text(),source)
                self.assertEqual(expected_lease,"fixture");self.assertTrue(only_unclaimed)
                return {"status":"publishing"}
            latest={**rec,"state":"CANDIDATE_READY","candidate_digest":digest,"queued_lease":"fixture"}
            with patch.object(state,"load",side_effect=[rec,latest]),patch.object(jobs,"submit",side_effect=publish):
                self.assertEqual(b.publish_staged(Q,source,"fixture")[0],"delegated")
                self.assertIsNone(ready.verified(GID))
            with patch.object(state,"load",return_value=rec),patch.object(jobs,"submit",return_value={"status":"publishing"}):
                self.assertEqual(b.publish_staged(Q,source,"fixture")[0],"transient")
    def test_automatic_publisher_cannot_overwrite_another_candidate(self):
        from missions.pnp import publish
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as d,patch.object(config,"STATE_ROOT",d),patch.object(config,"GAPS_DIR",d+"/gaps"):
            root=Path(d);src=root/"proof.lean";src.write_text("candidate")
            rec={"state":"LEASED","lease":"lease"}
            raced={**rec,"state":"CANDIDATE_READY","candidate_digest":"other","queued_lease":"lease"}
            import os
            fd=os.open(root/"publisher.lock",os.O_CREAT|os.O_RDWR,0o600)
            with patch.object(state,"load",side_effect=[rec,raced]),patch.object(jobs,"claim",return_value=fd),patch.object(state,"lock",side_effect=lambda g:contextlib.nullcontext()),patch.object(state,"atomic_write") as write:
                with self.assertRaisesRegex(publish.StopPublish,"another publication"):
                    jobs.submit(GID,str(src),expected_lease="lease",only_unclaimed=True)
                write.assert_not_called()

    def test_shared_dag_reduces_formula_cost(self):
        from missions.pnp.lbcert.generators.promise import dag
        p=("two",6,6,9,4362044,"FanInTwo")
        witness=dag.search(p,3)
        self.assertTrue(witness)
        self.assertTrue(b.gen.valid(p,witness))
        self.assertLessEqual(len(witness[0]),9)
    def test_unheld_catalog_must_explicitly_be_offerable(self):
        for value in (False,None):
            self.assertFalse(b.eligible({**Q,"offerable_now":value},{"held":0,"parallel":1},None))

if __name__=="__main__":unittest.main()

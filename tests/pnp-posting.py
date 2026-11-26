"""Offline posting lane tests: no live desk, compiler or GitHub mutation."""
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp import config, posting, state, support, focus, fastlane
from missions.pnp.lbcert import ready
from missions.pnp.staffing import plan

GID="L-meta-24806"
MODULE="PEqualNP.Outside.L_meta_24806"
STATEMENT=("∃ C : PEqualNP.CircuitLowerBounds.Circuit, PEqualNP.MetaComplexity.FanInTwo C ∧ C.size ≤ 9 ∧ "
           "∀ i j : Fin 6, C.eval (List.ofFn fun k : Fin 6 => decide (k = i ∨ k = j)) = "
           "(2 : ℕ).testBit (6 * min i.val j.val + max i.val j.val)")


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        p=patch.multiple(config,STATE_ROOT=self.tmp.name,GAPS_DIR=self.tmp.name+"/gaps",
                         CACHE_DIR=self.tmp.name+"/cache")
        p.start();self.addCleanup(p.stop)

    def rec(self, **fields):
        now=time.time()
        r=dict(state="LEASED",lease="test-lease",lease_obtained_at=now-1,
               lease_expires_at=now+600,statement=STATEMENT,module=MODULE,
               path="lean/PEqualNP/Outside/L_meta_24806.lean",imports=["PEqualNP.Defs"],
               work_lane="posting",acquisition_hard=False,acquisition_prs=0,
               lease_terms={"points":30,"level":"solid"})
        return state.create(GID,**{**r,**fields})

    def test_stop_preserves_held_work_and_blocks_new_lane(self):
        from missions.pnp import allocator
        r=self.rec()
        stop=Path(config.STATE_ROOT)/"lbcert"/"STOP"
        stop.parent.mkdir();stop.touch()
        with patch.object(posting,"generate") as gen,patch.object(posting.jobs,"submit") as send:
            self.assertFalse(posting.launch(GID))
            posting.run(GID,support.attempt(r))
            self.assertEqual(allocator.fill(None,{},time.time(),{}),[])
            self.assertEqual(allocator.proof_of_now(GID),"paused")
            self.assertEqual(posting.maintain(None,{},time.time(),{},[r]),[])
            gen.assert_not_called();send.assert_not_called()
        self.assertEqual(state.load(GID)["work_lane"],"research")

    def test_actual_promise_generation_and_exact_submission(self):
        r=self.rec()
        def submit(gid,path,expected_lease):
            self.assertEqual((gid,expected_lease),(GID,r["lease"]))
            self.assertIn(STATEMENT,Path(path).read_text())
            state.update(gid,queued_lease=expected_lease,candidate_digest="fixture")
            return {"status":"publishing"}
        with patch.object(ready,"competition",return_value={}),patch.object(ready,"verified",return_value=None),patch.object(posting.jobs,"submit",side_effect=submit) as send:
            posting.run(GID,support.attempt(r))
        send.assert_called_once()
        self.assertEqual(state.load(GID)["posting"]["result"],"submitted")

    def test_contested_offer_not_generated(self):
        r=self.rec(acquisition_prs=1)
        with patch.object(ready,"competition",return_value={}),patch.object(posting,"generate") as gen:
            posting.run(GID,support.attempt(r))
        gen.assert_not_called()
        self.assertEqual(state.load(GID)["posting"]["result"],"contested")

    def test_stale_attempt_does_not_submit(self):
        old=self.rec()
        state.transition(GID,"STALE")
        state.reacquire(GID,lease="new-lease",lease_expires_at=time.time()+600,
                        work_lane="posting")
        with patch.object(posting,"generate") as gen,patch.object(posting.jobs,"submit") as send:
            posting.run(GID,support.attempt(old))
        gen.assert_not_called();send.assert_not_called()

    def test_release_requires_exact_live_lease(self):
        r=self.rec()
        class Desk:
            def release(self,*a):raise AssertionError("not our lease")
        self.assertFalse(fastlane.release(Desk(),{},GID,"out_of_time","test",expected_lease="old"))

    def test_high_value_unknown_becomes_research_not_release(self):
        r=self.rec(lease_terms={"points":350,"level":"solid"})
        posting.status(GID,support.attempt(r),"unknown")
        with patch.object(fastlane,"release") as release:
            self.assertEqual(posting.maintain(None,{},time.time(),{},[state.load(GID)]),[])
        self.assertEqual(state.load(GID)["work_lane"],"research")
        release.assert_not_called()

    def test_hard_minimum_age_and_solid_release(self):
        r=self.rec(acquisition_hard=True,lease_terms={"level":"hard","points":30})
        posting.status(GID,support.attempt(r),"unknown")
        with patch.object(fastlane,"release",return_value=True) as release:
            posting.maintain(None,{},time.time(),{},[state.load(GID)])
            release.assert_not_called()
            state.update(GID,acquisition_hard=False,lease_terms={"level":"solid","points":30})
            self.assertEqual(posting.maintain(None,{},time.time(),{},[state.load(GID)]),[GID])
            self.assertEqual(release.call_args.kwargs["expected_lease"],r["lease"])

    def test_posting_not_model_focus(self):
        r=self.rec()
        self.assertFalse(focus.eligible(r))
        self.assertIsNone(focus.choose([r]))
        self.assertFalse(plan.current(plan.bound(r,"general","task",0)))

    def test_reacquisition_resets_posting_status(self):
        r=self.rec()
        posting.status(GID,support.attempt(r),"unknown")
        state.transition(GID,"STALE")
        rec=state.reacquire(GID,lease="new",lease_expires_at=time.time()+600,work_lane="posting")
        self.assertIsNone(rec["posting"])
        self.assertNotEqual(support.attempt(rec),support.attempt(r))

    def test_interrupted_worker_restarts_bounded(self):
        r=self.rec(posting={"attempt":"old","result":"unknown","starts":2})
        with patch.object(posting.subprocess,"Popen") as spawn:
            self.assertTrue(posting.launch(GID))
            self.assertTrue(posting.launch(GID))
            self.assertFalse(posting.launch(GID))
        self.assertEqual(spawn.call_count,2)
        self.assertEqual(state.load(GID)["posting"]["result"],"unknown")


if __name__=="__main__":unittest.main()

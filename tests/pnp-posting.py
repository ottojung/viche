"""Offline posting lane tests: no live desk, compiler or GitHub mutation."""
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp import config, posting, state, support, focus, fastlane, surge
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

    def test_refusal_falls_through_within_original_budget(self):
        r=self.rec()
        from missions.pnp.lbcert.generators.promise import batch
        def fake(name,gid,sf,out,timeout):
            self.assertGreater(timeout,0)
            self.assertLessEqual(timeout,posting.BUDGET)
            if name=="first":
                Path(out).write_text("discard")
                return 3,"not supported"
            self.assertFalse(Path(out).exists())
            Path(out).write_text("second candidate")
            return 0,""
        with tempfile.TemporaryDirectory() as d, \
             patch.object(batch,"staged_candidate",return_value=None), \
             patch.object(posting.plugins,"families_of",return_value=iter([("first","x"),("second","y")])), \
             patch.object(posting.plugins,"run",side_effect=fake) as run, \
             patch.object(posting.validate,"validate") as validate:
            status,out=posting.generate(r,Path(d))
            self.assertEqual(status,"generated")
            self.assertEqual(out.read_text(),"second candidate")
            self.assertEqual(run.call_count,2)
            validate.assert_called_once()
            self.assertLessEqual(run.call_args_list[1].kwargs["timeout"],run.call_args_list[0].kwargs["timeout"])

    def test_plugin_failure_does_not_fall_through(self):
        r=self.rec()
        from missions.pnp.lbcert.generators.promise import batch
        with tempfile.TemporaryDirectory() as d, \
             patch.object(batch,"staged_candidate",return_value=None), \
             patch.object(posting.plugins,"families_of",return_value=iter([("first","x"),("second","y")])), \
             patch.object(posting.plugins,"run",return_value=(124,"timeout")) as run:
            self.assertEqual(posting.generate(r,Path(d)),("unknown",None))
            run.assert_called_once()

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

    def test_quiet_hard_research_not_discarded_for_low_price(self):
        now=time.time()
        r=self.rec(work_lane="research",acquisition_hard=True,acquisition_level="hard",
                   lease_obtained_at=now-1201,lease_terms={"level":"hard","points":105})
        with patch.object(surge,"active",return_value=False),patch.object(fastlane,"release") as release,patch.object(posting,"launch") as launch:
            self.assertEqual(posting.maintain(None,{},now,{"complete":True,"observed":now,"ordinary":0},[r]),[])
            self.assertEqual(state.load(GID)["work_lane"],"research")
            release.assert_not_called();launch.assert_not_called()

    def test_stale_complete_observation_cannot_discard_hard_research(self):
        now=time.time()
        r=self.rec(work_lane="research",acquisition_hard=True,acquisition_level="hard",
                   lease_obtained_at=now-1201,lease_terms={"level":"hard","points":105})
        with patch.object(surge,"active",return_value=False),patch.object(fastlane,"release") as release,patch.object(posting,"launch") as launch:
            for obs in ({"complete":True,"observed":now-61,"ordinary":0},
                        {"complete":True,"observed":now-61,"ordinary":50},
                        {"complete":True,"observed":now,"ordinary":None}):
                self.assertEqual(posting.maintain(None,{},now,obs,[r]),[])
                self.assertEqual(state.load(GID)["work_lane"],"research")
            release.assert_not_called();launch.assert_not_called()
            posting.maintain(None,{},now,{"complete":True,"observed":now,"ordinary":1},[r])
            self.assertEqual(state.load(GID)["work_lane"],"posting")
            launch.assert_called_once_with(GID)

    def test_surge_preserves_young_hard_and_cached_candidates(self):
        r=self.rec(work_lane="research",acquisition_hard=True,
                   lease_terms={"level":"hard","points":600})
        now=time.time()
        with patch.object(surge,"active",return_value=True), \
             patch.object(fastlane,"release",return_value=True) as release, \
             patch.object(fastlane,"cand_ready",return_value="complete.lean"):
            self.assertEqual(posting.maintain(None,{},now,{},[r]),[])
            release.assert_not_called()
            state.update(GID,lease_obtained_at=now-1201)
            self.assertEqual(posting.maintain(None,{},now,{},[state.load(GID)]),[])
            release.assert_not_called()

    def test_surge_yields_mature_research_with_no_candidate(self):
        r=self.rec(work_lane="research",acquisition_hard=True,
                   lease_obtained_at=time.time()-1201,lease_terms={"level":"hard","points":600})
        with patch.object(surge,"active",return_value=True), \
             patch.object(fastlane,"release",return_value=True) as release, \
             patch.object(fastlane,"cand_ready",return_value=None):
            self.assertEqual(posting.maintain(None,{},time.time(),{},[r]),[GID])
            self.assertEqual(release.call_args.kwargs["expected_lease"],r["lease"])

    def test_stalled_surge_keeps_only_one_failed_assignment(self):
        r=self.rec()
        posting.status(GID,support.attempt(r),"unsupported")
        with patch.object(surge,"active",return_value=True), \
             patch.object(surge,"recovery",return_value=True), \
             patch.object(ready,"competition",return_value={}), \
             patch.object(fastlane,"release") as release:
            self.assertEqual(posting.maintain(None,{},time.time(),{},[state.load(GID)]),[])
            self.assertEqual(state.load(GID)["work_lane"],"research")
            other="L-meta-24807"
            rr=dict(r)
            rr.pop("gap_id",None)
            rr.update(lease="test-other",work_lane="posting",posting={"result":"unknown"})
            state.create(other,**rr)
            release.return_value=True
            self.assertEqual(posting.maintain(None,{},time.time(),{},[state.load(GID),state.load(other)]),[other])
            self.assertEqual(state.load(GID)["work_lane"],"research")
            self.assertEqual(release.call_count,1)

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


class SurgeDecideTests(unittest.TestCase):
    """Hermetic burst-detection tests: no desk, ledger or state mutation."""

    @staticmethod
    def _snapshot(now, count):
        rows={f"g{i}":{"title":"a fan-in-two representation"} for i in range(count)}
        seen={f"g{i}":now-10 for i in range(count)}
        return {"observed":now,"ordinary":1000,"gaps":rows},seen

    def test_sporadic_arrivals_do_not_sustain_surge(self):
        now=time.time()
        snap,seen=self._snapshot(now,3)
        previous={"active":True,"last_busy":now-1000,"observed":now-5,"ordinary":1000}
        out=surge.decide(previous,snap,seen,now)
        self.assertEqual(out["last_busy"],previous["last_busy"])
        self.assertTrue(out["active"])  # still inside the old quiet window
        later=now+300  # 1300s since the last genuine burst
        snap2,seen2=self._snapshot(later,3)
        out2=surge.decide(out,snap2,seen2,later)
        self.assertFalse(out2["active"])

    def test_genuine_burst_activates_and_refreshes(self):
        now=time.time()
        count=surge.BURST_MIN_GAPS+5
        snap,seen=self._snapshot(now,count)
        out=surge.decide({},snap,seen,now)
        self.assertTrue(out["active"])
        self.assertEqual(out["last_busy"],now)
        self.assertEqual(out["new_witnesses"],count)


if __name__=="__main__":unittest.main()

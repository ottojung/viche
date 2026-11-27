"""Focused offline regression tests for surge, pause and readiness policy."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from missions.pnp import batch_scorecard, config, leaderboard, pause, readiness, surge


class Batch(unittest.TestCase):
    def test_offers_trigger_and_quiet_hysteresis(self):
        # Surge throttles only on an actual burst of new witness-hint arrivals;
        # a large claimable frontier alone must never suppress staffing.
        gaps = {"L-meta-0": {"title": "two-lit row"}}
        seen = {"L-meta-0": 1000}
        busy = surge.decide({}, {"observed":1000,"ordinary":100,"gaps":gaps}, seen, 1000)
        self.assertTrue(busy["active"])
        quiet = surge.decide(busy, {"observed":2199,"ordinary":0}, {}, 2199)
        self.assertTrue(quiet["active"])
        self.assertFalse(surge.decide(quiet, {"observed":2200,"ordinary":0}, {}, 2200)["active"])

    def test_large_frontier_alone_does_not_trigger_surge(self):
        # A plentiful claimable frontier with no new witness-hint arrivals must
        # not by itself keep surge permanently active and block staffing.
        self.assertFalse(surge.decide({}, {"observed":1000,"ordinary":1000}, {}, 1000)["active"])

    def test_fifty_fresh_witnesses(self):
        gaps = {f"L-meta-{i}":{"title":"two-lit row"} for i in range(50)}
        seen = {g:999 for g in gaps}
        doc = {"observed":1000,"ordinary":0,"gaps":gaps}
        self.assertTrue(surge.decide({},doc,seen,1000)["active"])
        self.assertFalse(surge.decide({},doc,dict(list(seen.items())[:49]),1000)["active"])
        self.assertFalse(surge.decide({},doc,seen,1061).get("active",False))

    def test_stale_observation_neither_refreshes_nor_holds_forever(self):
        gaps = {"L-meta-0": {"title": "two-lit row"}}
        seen = {"L-meta-0": 1000}
        old = surge.decide({}, {"observed":1000,"ordinary":100,"gaps":gaps}, seen, 1000)
        self.assertEqual(surge.decide(old,{"observed":1000,"ordinary":0},{},1200),old)
        self.assertTrue(surge.active(2199,old))
        self.assertFalse(surge.active(2201,old))


    def test_stalled_batch_requires_distinct_failures_span_and_no_success(self):
        events=[{"t":1000+i*12,"stage":"posting_generated","gid":f"L-meta-{i}",
                 "result":"unsupported"} for i in range(45)]
        self.assertTrue(surge.yield_evidence(events,1750)["stalled"])
        self.assertFalse(surge.yield_evidence(events[:39],1750)["stalled"])
        self.assertFalse(surge.yield_evidence([{**e,"gid":"same"} for e in events],1750)["stalled"])
        self.assertFalse(surge.yield_evidence(events,1600-1)["stalled"])
        self.assertFalse(surge.yield_evidence(events+[{"t":1700,"stage":"pr_opened"}],1750)["stalled"])
        self.assertFalse(surge.yield_evidence(events+[{"t":1700,"stage":"posting_generated","result":"generated"}],1750)["stalled"])

    def test_recovery_revoked_when_observation_stale(self):
        row={"active":True,"recovery":True,"observed":1000}
        self.assertTrue(surge.recovery(1060,row))
        self.assertFalse(surge.recovery(1061,row))


class Offerability(unittest.TestCase):
    def test_actual_catalog_count_not_nominal_capacity(self):
        from missions.pnp import frontier
        snap={"complete":True,"offerable":2,"gaps":{
            "L-meta-1":{"level":"open","held":0,"parallel":1},
            "L-meta-2":{"level":"hard","held":3,"parallel":3},
            "L-meta-3":{"level":"hard","held":0,"parallel":1}}}
        rows=[{"id":"L-meta-1","offerable_now":False},
              {"id":"L-meta-2","offerable_now":True},{"id":"L-meta-3","offerable_now":True}]
        self.assertEqual(frontier.offer_levels(snap,rows),{"hard":2})
        self.assertIsNone(frontier.offer_levels(snap,rows[:2]))
        self.assertIsNone(frontier.offer_levels(snap,rows+[rows[1]]))

    def test_stale_catalog_cannot_narrow_probe(self):
        from missions.pnp import frontier
        with tempfile.TemporaryDirectory() as d,patch.object(config,"STATE_ROOT",d):
            root=Path(d)/"lbcert";root.mkdir()
            p=root/"gaps-cache.json"
            p.write_text('{"gaps":[]}')
            (root/"gaps-cache.json.meta").write_text('{"at":100}')
            self.assertIsNone(frontier.cached_offer_levels({"observed":200},200))


class Pause(unittest.TestCase):
    def test_expiry_and_emergency_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/"lbcert"
            root.mkdir()
            self.assertFalse(pause.paused(tmp,100))
            (root/"MAINTENANCE.json").write_text(json.dumps(
                {"at":100,"expires":3700,"author":"operator","reason":"deploy"}))
            self.assertTrue(pause.paused(tmp,3699))
            self.assertFalse(pause.paused(tmp,3700))
            (root/"STOP").touch()
            self.assertTrue(pause.paused(tmp,9999))
            self.assertEqual(pause.status(tmp,9999)["kind"],"emergency")

    def test_invalid_maintenance_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"lbcert"
            root.mkdir()
            p=root/"MAINTENANCE.json"
            for data in ("not JSON", "[]", '{"at":0,"expires":3601,"author":"x","reason":"y"}',
                         '{"at":0,"expires":20,"author":"","reason":"y"}'):
                p.write_text(data)
                self.assertTrue(pause.paused(tmp,100))


class Readiness(unittest.TestCase):
    def test_lease_age_and_invalid_expiry(self):
        now=1000
        for expiry in (float("nan"), None, 1299, 1631):
            self.assertEqual(readiness.lease_errors([{"gap_id":"x","lease_expires_at":expiry}],now),["x"])
        self.assertEqual(readiness.lease_errors([{"gap_id":"x","lease_expires_at":1300}],now),[])

    def test_no_pass_on_unknown_capacity_or_refused_generator(self):
        with patch.object(readiness.posting,"paused",return_value=False), \
             patch.object(readiness.desk,"capacity",return_value=None), \
             patch.object(readiness.frontier,"load",return_value={"observed":1000}), \
             patch.object(readiness.cli,"held_records",return_value=[]), \
             patch.object(readiness.github,"identity",return_value="test"), \
             patch.object(readiness.github,"repository_name",return_value="test/repo"), \
             patch.object(readiness,"promise_probe",side_effect=RuntimeError("refused")):
            result=readiness.check(1000)
        self.assertFalse(result["ready"])
        self.assertEqual(set(result["errors"]),{"capacity","promise"})


class Scorecard(unittest.TestCase):
    def test_cohort_and_unknown_first(self):
        events=[
            {"t":900,"stage":"seen","gid":"L-meta-1"},
            {"t":1000,"stage":"surge_enter","gid":"desk"},
            {"t":1010,"stage":"leased","gid":"L-meta-1"},
            {"t":1030,"stage":"pr_opened","gid":"L-meta-1","pr":7},
            {"t":1040,"stage":"pr_opened","gid":"L-meta-2","pr":8},
            {"t":2300,"stage":"surge_exit","gid":"desk"},
            {"t":2400,"stage":"verdict","gid":"L-meta-1","verdict":"ACCEPTED"},
            {"t":2500,"stage":"pr_opened","gid":"L-meta-3","pr":9},
        ]
        w=batch_scorecard.last_closed_window(events)
        r=batch_scorecard.summarize(events,w,{"7":True})
        self.assertEqual(w,(700,2300))
        self.assertEqual((r["seen"],r["leased"],len(r["prs"]),r["accepted"]),(1,1,2,1))
        self.assertEqual((r["first"],r["first_unknown"],r["median_lease_to_pr_s"]),(1,1,20))

    def test_credit_is_from_complete_official_export_and_never_local_verdict(self):
        row = {"github":"ottojung", "steps":2, "points":40, "lemmas":[
            {"id":"L-meta-1","points":10,"at":"1970-01-01T00:20:00Z","points_estimated":True},
            {"id":"L-meta-2","points":30,"at":"1970-01-01T00:30:00Z"}]}
        credits=leaderboard.credit_details([row])
        self.assertIsNotNone(credits)
        self.assertIsNone(leaderboard.credit_details([{**row,"points":41}]))
        self.assertIsNone(leaderboard.credit_details([{**row,"lemmas":row["lemmas"][:1]}]))
        self.assertIsNone(leaderboard.credit_details([{**row,"lemmas":[row["lemmas"][0]]*2}]))
        events=[{"stage":"pr_opened","gid":"L-meta-1","pr":1,"t":1100},
                {"stage":"pr_opened","gid":"L-meta-2","pr":2,"t":1101},
                {"stage":"pr_opened","gid":"L-meta-2","pr":3,"t":1500},
                {"stage":"verdict","gid":"L-meta-3","verdict":"ACCEPTED","t":1300}]
        data={"start":1000,"end":1400,"prs":{"L-meta-1":1,"L-meta-2":2,"L-meta-3":4}}
        out=batch_scorecard.cohort_credit(events,data,{"available":True,"our_credit_details":credits})
        self.assertEqual(out,{"official_credited_units":1,"official_cohort_points":10,
                              "official_estimated_points":10,"official_ambiguous_units":1})
        self.assertIsNone(batch_scorecard.cohort_credit(events,data,{"available":True})["official_cohort_points"])
        self.assertEqual(batch_scorecard.cohort_credit(events,data,{"available":True,"our_credit_details":{}})["official_cohort_points"],0)

    def test_unindexed_first_five_do_not_starve_other_races(self):
        prs={f"L-meta-{i}":i for i in range(1,13)}
        first={}
        attempted={}
        for now,expected in ((100,list(range(1,6))),(101,list(range(6,11))),
                             (102,[11,12,1,2,3])):
            batch=batch_scorecard.first_query_batch(prs,first,attempted)
            self.assertEqual(list(batch.values()),expected)
            attempted.update({str(p):now for p in batch.values()})
        first["4"]=True
        self.assertNotIn(4,batch_scorecard.first_query_batch(prs,first,attempted).values())
        self.assertEqual(len(batch_scorecard.first_query_batch(prs,first,attempted)),5)

    def test_first_query_includes_closed_rivals_and_refuses_partial_index(self):
        def req(*args):
            if args[1].startswith("repositories/"):
                return {"id":config.UPSTREAM_ID,"full_name":"owner/repo"}
            return {"data":{"a0":{"issueCount":2,"nodes":[
                {"number":4,"title":"L-meta-1","createdAt":"2026-11-26T00:00:00Z"},
                {"number":7,"title":"L-meta-1","createdAt":"2026-11-26T00:01:00Z"}]},
                "a1":{"issueCount":2,"nodes":[
                {"number":8,"title":"L-meta-2","createdAt":"2026-11-26T00:01:00Z"}]}}}
        self.assertEqual(batch_scorecard.observe_first({"L-meta-1":7,"L-meta-2":8},req),{"7":False})


if __name__ == "__main__":
    unittest.main()

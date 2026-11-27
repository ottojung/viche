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
        busy = surge.decide({}, {"observed":1000,"ordinary":100}, {}, 1000)
        self.assertTrue(busy["active"])
        quiet = surge.decide(busy, {"observed":2199,"ordinary":0}, {}, 2199)
        self.assertTrue(quiet["active"])
        self.assertFalse(surge.decide(quiet, {"observed":2200,"ordinary":0}, {}, 2200)["active"])

    def test_fifty_fresh_witnesses(self):
        gaps = {f"L-meta-{i}":{"title":"two-lit row"} for i in range(50)}
        seen = {g:999 for g in gaps}
        doc = {"observed":1000,"ordinary":0,"gaps":gaps}
        self.assertTrue(surge.decide({},doc,seen,1000)["active"])
        self.assertFalse(surge.decide({},doc,dict(list(seen.items())[:49]),1000)["active"])
        self.assertFalse(surge.decide({},doc,seen,1061).get("active",False))

    def test_stale_observation_neither_refreshes_nor_holds_forever(self):
        old = surge.decide({}, {"observed":1000,"ordinary":100}, {}, 1000)
        self.assertEqual(surge.decide(old,{"observed":1000,"ordinary":0},{},1200),old)
        self.assertTrue(surge.active(2199,old))
        self.assertFalse(surge.active(2201,old))


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

"""Focused offline regression tests for surge, pause and readiness policy."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from missions.pnp import config, pause, readiness, surge


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


if __name__ == "__main__":
    unittest.main()

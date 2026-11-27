import fcntl
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp import config, observation, freshness
from missions.pnp.lbcert import live, catalog_observer


class Observer(unittest.TestCase):
    def test_baseline_fresh_and_outage(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(config, "STATE_ROOT", tmp), patch.object(observation.ledger, "mark") as mark:
            def observe(at, ids, complete=True):
                observation.record({"observed": at, "complete": complete, "gaps": dict.fromkeys(ids)}, now=at)
            observe(100, ["a"])
            mark.assert_not_called()
            observe(110, ["a", "b"])
            mark.assert_called_once_with("seen", "b")
            mark.reset_mock()
            observe(115, ["c"], False)
            observe(400, ["a", "d"])
            mark.assert_not_called()
            observe(410, ["a", "d", "e"])
            mark.assert_called_once_with("seen", "e")
            observe(405, ["f"])
            mark.assert_called_once_with("seen", "e")

    def test_recent_index_survives_restart_without_ledger_scan(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(config,"STATE_ROOT",tmp), \
             patch.object(observation.ledger,"read",side_effect=AssertionError("hot path must not read ledger")), \
             patch.object(observation.ledger,"mark"):
            def observe(at, ids, complete=True):
                observation.record({"observed":at,"complete":complete,"gaps":dict.fromkeys(ids)},now=at)
            observe(100,["a"])
            self.assertEqual(freshness.recent(100),{})
            observe(110,["a","b"])
            self.assertEqual(freshness.recent(110),{"b":110})
            observe(120,["a","b","c"])
            self.assertEqual(freshness.recent(120),{"b":110,"c":120})
            observe(125,["d"],False)
            self.assertEqual(freshness.recent(125),{"b":110,"c":120})
            self.assertEqual(freshness.recent(241),{})  # observation outage
            observe(250,["a","b","c","d"])
            self.assertEqual(freshness.recent(250),{})  # rebaseline, no fake arrival
            observe(260,["a","b","c","d","e"])
            self.assertEqual(freshness.recent(260),{"e":260})
            for t in (350,440,530,570):
                observe(t,["a","b","c","d","e"])
            self.assertEqual(freshness.recent(570),{})  # first sighting aged out
            observe(575,["a","b","c","d"])  # e disappears and returns
            observe(580,["a","b","c","d","e"])
            self.assertEqual(freshness.recent(580),{})
            Path(freshness.observation_path()).write_text("[]")
            self.assertEqual(freshness.recent(580),{})

    def test_legacy_observation_does_not_make_old_ids_fresh(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(config,"STATE_ROOT",tmp), \
             patch.object(observation.ledger,"mark") as mark:
            p=Path(freshness.observation_path())
            p.parent.mkdir()
            p.write_text(json.dumps({"ids":["old"],"at":100}))
            self.assertEqual(freshness.recent(105),{})
            observation.record({"observed":110,"complete":True,"gaps":{"old":{},"new":{}}},now=110)
            self.assertEqual(freshness.recent(110),{"new":110})
            mark.assert_called_once_with("seen","new")

    def test_malformed_history_cannot_create_fresh_arrivals(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(config,"STATE_ROOT",tmp), \
             patch.object(observation.ledger,"mark") as mark:
            p=Path(freshness.observation_path())
            p.parent.mkdir()
            p.write_text(json.dumps({"ids":"old","at":100,"recent":{"injected":100}}))
            self.assertEqual(freshness.recent(105),{})
            observation.record({"observed":110,"complete":True,"gaps":{"old":{},"new":{}}},now=110)
            self.assertEqual(freshness.recent(110),{})
            mark.assert_not_called()
            p.write_text(json.dumps({"ids":["old"],"at":110,"recent":{"injected":110}}))
            self.assertEqual(freshness.recent(110),{})

    def test_shared_fresh_cache(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(live, "GAPS_CACHE", os.path.join(tmp, "catalog.json")), patch.object(live.time, "time", return_value=100), patch.object(live, "_fetch_gaps") as fetch:
            with open(live.GAPS_CACHE, "wb") as f:
                f.write(b'{"gaps":[]}')
            with open(live.GAPS_CACHE + ".meta", "w") as f:
                json.dump({"at": 95}, f)
            self.assertEqual(live.gaps_bytes(), b'{"gaps":[]}')
            fetch.assert_not_called()

    def test_contention_uses_old_cache_without_refresh(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(live, "GAPS_CACHE", os.path.join(tmp, "catalog.json")), patch.object(live.time, "time", return_value=100), patch.object(live, "_fetch_gaps") as fetch:
            with open(live.GAPS_CACHE, "wb") as f:
                f.write(b'{"gaps":[]}')
            with open(live.GAPS_CACHE + ".meta", "w") as f:
                json.dump({"at": 50}, f)
            with open(live.GAPS_CACHE + ".lock", "a") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.assertEqual(live.gaps_bytes(), b'{"gaps":[]}')
                fetch.assert_not_called()
                with open(live.GAPS_CACHE + ".meta") as f:
                    self.assertEqual(json.load(f)["at"], 50)

    def test_catalog_independent_of_status_error(self):
        with patch.object(catalog_observer.frontier, "refresh", side_effect=OSError), patch.object(live, "gaps_bytes") as gaps:
            with self.assertRaises(OSError):
                catalog_observer.refresh()
            gaps.assert_called_once_with(timeout=20)


if __name__ == "__main__":
    unittest.main()

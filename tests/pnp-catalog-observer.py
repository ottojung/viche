import fcntl
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from missions.pnp import config, observation
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

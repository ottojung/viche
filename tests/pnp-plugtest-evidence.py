"""Offline generator evidence regressions."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp.lbcert import plugtest, plugins

class Evidence(unittest.TestCase):
    def test_historical_imports_never_take_candidate_metadata(self):
        text="-- old proof\nimport PEqualNP.Defs\nimport PEqualNP.Library.Helpers.PromiseColTree\n\nopen X\n"
        self.assertEqual(plugtest.historical_imports(text),["PEqualNP.Defs","PEqualNP.Library.Helpers.PromiseColTree"])
    def test_refusal_only_not_a_pass(self):
        r=[{"result":"refused"}]*2
        self.assertFalse(plugtest.summary("x",r)["ok"])
        self.assertTrue(plugtest.summary("x",r,True)["ok"])
        self.assertTrue(plugtest.summary("x",r+[{"result":"candidate_only"}])["ok"])
        self.assertFalse(plugtest.summary("x",r+[{"result":"invalid"}],True)["ok"])
        self.assertFalse(plugtest.summary("x",[],True)["ok"])
    def test_open_cases_require_real_open_frontier_and_exact_desk_imports(self):
        import json
        rows=[{"id":"L-meta-3","statement":"x","imports":["Allowed"]},
              {"id":"L-meta-4","statement":"x","imports":["Closed"]}]
        with patch.object(plugtest.live,"gaps_bytes",return_value=json.dumps({"gaps":rows}).encode()),patch.object(plugtest.live,"open_ids",return_value={"L-meta-3"}):
            got=plugtest.desk_open(lambda x:True,2)
            self.assertEqual(got,[{**rows[0],"source":"desk"}])
        with patch.object(plugtest.live,"gaps_bytes",return_value=b'{"gaps":[]}'),patch.object(plugtest.live,"open_ids",return_value=None):
            with self.assertRaises(RuntimeError):plugtest.desk_open(lambda x:True,2)
    def test_helper_version_changes_retry_key(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"gen.py";p.write_text("MATCH='x'")
            before=plugins.fingerprint(p)
            q=Path(d)/"helper.py";q.write_text("x=1")
            after=plugins.fingerprint(p)
            self.assertNotEqual(before,after)
            q.write_text("x=2")
            self.assertNotEqual(after,plugins.fingerprint(p))
    def test_empty_registry_no_rescan(self):
        with patch.object(plugins,"discover",side_effect=AssertionError):
            self.assertIsNone(plugins.family_of("x",{}))
    def test_exit_zero_without_candidate_reports_generator_error(self):
        with patch.object(plugins,"run",return_value=(0,"")):
            self.assertEqual(plugtest.one("x",{"id":"L-meta-1","statement":"True"})["result"],"generator_error")

if __name__=="__main__":
    unittest.main()

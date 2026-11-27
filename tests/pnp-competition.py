from pathlib import Path
import sys,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp import competition as c, config

class Tests(unittest.TestCase):
    def req(self,rows):
        def call(*a):
            if a[1].startswith("repositories/"):
                return {"id":config.UPSTREAM_ID,"full_name":"test/repo"}
            self.assertIn("is:open",a[-1])
            return {"data":rows}
        return call
    def test_batch_exact_and_incomplete(self):
        rival={"number":11,"title":"L-meta-1","state":"OPEN"}
        result=c.observe(["L-meta-1","L-meta-2","L-meta-3"],self.req({
            "a0":{"issueCount":1,"nodes":[rival]},
            "a1":{"issueCount":1,"nodes":[rival]},
            "a2":{"issueCount":101,"nodes":[rival]}}))
        self.assertEqual(result,{"L-meta-1":1,"L-meta-2":0})
    def test_decorated_title_and_id_boundary(self):
        def pr(n,title):return {"number":n,"title":title,"state":"OPEN"}
        rows=[pr(1,"Prove L-meta-1 (edge_detect_prove)"),
              pr(2,"L-meta-10"),pr(3,"L-meta-1-2"),pr(4,"L-meta-1")]
        self.assertEqual(c.observe(["L-meta-1"],self.req({"a0":{"issueCount":4,"nodes":rows}})),{"L-meta-1":2})
    def test_wrong_identity(self):
        self.assertEqual(c.observe(["L-meta-1"],lambda *a:{"id":1,"full_name":"test/repo"}),{})
    def test_unknown_never_acquire_and_paced(self):
        mem={}
        with patch.object(c,"observe",return_value={"L-meta-1":1}) as obs:
            self.assertIsNone(c.fallback_target(["L-meta-1","L-meta-2"],mem,100))
            self.assertIsNone(c.fallback_target(["L-meta-2"],mem,105))
            self.assertEqual(obs.call_count,1)
        with patch.object(c,"observe",return_value={"L-meta-2":0}):
            self.assertEqual(c.fallback_target(["L-meta-2"],mem,131),"L-meta-2")
    def test_api_error(self):
        self.assertEqual(c.observe(["L-meta-1"],lambda *a:{"errors":[{"message":"bad"}]}),{})
if __name__=="__main__":unittest.main()

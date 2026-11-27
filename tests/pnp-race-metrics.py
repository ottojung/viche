from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp import race_metrics as r, config

GID="L-meta-123"
OUR=dict(title=GID,number=12,createdAt="2026-11-26T20:00:00Z",author={"login":config.DESK_HANDLE})
RIVAL=dict(title=GID,number=11,createdAt="2026-11-26T20:00:00Z",author={"login":"another-contributor"})
ROW=dict(gid=GID,pr=12)

def search(*rows, count=None):
    return dict(nodes=list(rows),issueCount=len(rows) if count is None else count)

class TestRaceMetrics(unittest.TestCase):
    def test_first_and_late(self):
        self.assertEqual(r.classify(ROW,search(OUR)),"first_observed")
        self.assertEqual(r.classify(ROW,search(OUR,RIVAL)),"rival_first")
        self.assertEqual(r.classify(ROW,search(OUR,{**RIVAL,"author":OUR["author"]})),"own_earlier")
    def test_exact_title(self):
        self.assertEqual(r.classify(ROW,search(OUR,{**RIVAL,"title":GID+"0"})),"first_observed")
    def test_missing_and_truncated(self):
        self.assertEqual(r.classify(ROW,search(OUR,count=101)),"unknown")
        self.assertEqual(r.classify(ROW,search(RIVAL)),"unknown")
        self.assertEqual(r.classify(ROW,search({**OUR,"author":None})),"unknown")
        self.assertEqual(r.classify(ROW,search(OUR,{**RIVAL,"createdAt":"bad"})),"unknown")
    def test_query_exact_alias(self):
        def fake(q):
            self.assertIn("repo:test/repo",q)
            self.assertIn("is:pr",q)
            return {"data":{"a0":search(OUR,RIVAL)}}
        self.assertEqual(r.sample_races([ROW],fake)[0]["result"],"rival_first")
    def test_attempts_and_window(self):
        events=[dict(gid=GID,t=t,stage=s,**fields) for t,s,fields in [
            (1,"seen",{}),(2,"leased",{"proof_of":True}),
            (4,"leased",{"lane":"posting"}),(7,"pr_opened",{"pr":12}),
            (8,"pr_opened",{"pr":12}),(9,"seen",{})]]
        rows=r.audit_events(events+[None,{"t":"bad"}],5)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["leased"],4)
        self.assertEqual(rows[0]["lane"],"posting")
        self.assertEqual(r.duration_summary(rows,"seen")["median_s"],6)
        self.assertEqual(r.duration_summary(rows,"leased")["median_s"],3)
    def test_rates_only_credited_points(self):
        a=dict(score_metric="points",available=True,source_checked_at="2026-11-26T20:00:00Z",our_points=40)
        b={**a,"source_checked_at":"2026-11-26T20:30:00Z","our_points":70}
        self.assertEqual(r.points_rate([a,b],0)["points_per_hour"],60)
        self.assertIsNone(r.points_rate([a,{**b,"score_metric":"steps"}],0))
        self.assertIsNone(r.points_rate([a,{**a,"our_points":70}],0))

if __name__=="__main__":
    unittest.main()

import json,sys,unittest,time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp import radar,frontier
from missions.pnp.lbcert import live
class Tests(unittest.TestCase):
    def test_fast_history_exact_subjects_and_dedup(self):
        from types import SimpleNamespace
        rows = ["20\0A\0L-meta-12 (#100)", "19\0B\0Prove L-meta-13 (edge_detect_prove) (#101)",
                "18\0C\0L-meta-12 (#99)", "17\0D\0Discuss L-meta-14 (#102)",
                "16\0E\0L-meta-15", "15\0F\0L-pcx-15 (#103)", "broken"]
        with patch.object(radar.subprocess, "run", return_value=SimpleNamespace(stdout="\n".join(rows))) as run:
            self.assertEqual(radar.recent_merges(ref="pinned-head"), [
                ("PEqualNP.Outside.L_meta_12", "A", 20),
                ("PEqualNP.Outside.L_meta_13", "B", 19)])
            args = run.call_args.args[0]
            self.assertIn("--first-parent", args)
            self.assertEqual(args[-1], "pinned-head")
            self.assertNotIn("--name-only", args)
    def test_radar_scores_actual_offers_only(self):
        rows=[{"id":"L-meta-1","title":"Unclaimable","statement":"True","offerable_now":False},
              {"id":"L-meta-2","title":"Actual shard","statement":"False","offerable_now":True}]
        snap={"observed":time.time(),"complete":True,"offerable":1,"gaps":{
           "L-meta-1":{"level":"open","points":900,"held":0,"parallel":1},
           "L-meta-2":{"level":"hard","points":120,"held":3,"parallel":3}}}
        with patch.object(live,"gaps_bytes",return_value=json.dumps({"gaps":rows}).encode()), \
             patch.object(frontier,"load",return_value=snap),patch.object(frontier,"cached_offer_levels",return_value={"hard":1}), \
             patch.object(radar.sibling,"index",return_value=("head",{})),patch.object(radar.sibling,"skeleton",side_effect=lambda x:x), \
             patch.object(radar.plugins,"discover",return_value={}),patch.object(radar.plugins,"family_of",return_value=None), \
             patch.object(radar.lbparse,"family",return_value=None),patch.object(radar,"recent_merges",return_value=[]),patch.object(radar,"status",return_value=None):
            r=radar.build()
            self.assertTrue(r["offers_known"])
            self.assertEqual(r["families"][0]["label"],"Actual shard")
            self.assertEqual(r["families"][0]["free_points"],120)
            self.assertEqual(r["families"][0]["uncovered_points"],120)
            self.assertEqual(r["families"][0]["uncovered_offerable"],1)
            self.assertEqual(r["families"][1]["uncovered_offerable"],0)
            self.assertEqual(r["families"][1]["free_points"],0)
            self.assertTrue(r["families"][0]["examples"][0]["offered"])
    def test_live_priority_over_merges_and_closed_refusals(self):
        def f(name, **kw):
            return dict(label=name, coverage='', coverage_counts={}, merged_6h=0,
                        uncovered_offerable=0, uncovered_points=0,
                        refused_offerable=0, refused_points=0) | kw
        old=f("closed",merged_6h=200)
        live=f("live",uncovered_offerable=1,uncovered_points=30)
        partial=f("partial",coverage="partial: plugin:x",coverage_counts={"":1,"plugin:x":8},
                  uncovered_offerable=1,uncovered_points=150)
        refused=f("refused",coverage="plugin:x",refused_offerable=2,refused_points=60)
        rows=[old,live,partial,refused]
        todo,hard,history=radar.backlog_priorities({"families":rows,"offers_known":True})
        self.assertEqual([x["label"] for x in todo],["partial","live"])
        self.assertEqual(hard,[refused])
        self.assertEqual(history,[old])
        self.assertEqual(radar.backlog_priorities({"families":rows,"offers_known":False}),([],[],[old]))
    def test_posting_evidence_uses_latest_and_counts_attempts(self):
        ev=[{"stage":"posting_generated","gid":"L-meta-1","result":"unsupported","t":1},
            {"stage":"posting_generated","gid":"L-meta-1","result":"generated","t":3},
            {"stage":"posting_generated","gid":"L-meta-1","result":"unknown","t":2},
            {"stage":"verdict","gid":"L-meta-1","result":"accepted","t":4}]
        counts, latest = radar.posting_evidence(ev)
        self.assertEqual(counts["L-meta-1"], {"unsupported":1,"unknown":1,"generated":1})
        self.assertEqual(latest, {"L-meta-1":"generated"})
        old={"label":"old","merged_6h":100,"posting_attempts":{}}
        failed={"label":"failing","merged_6h":0,"posting_attempts":{"unknown":7}}
        self.assertEqual(radar.yield_leads({"families":[old,failed],"offers_known":False}),[failed])
    def test_stale_observation_is_not_ranked(self):
        with patch.object(live,"gaps_bytes",return_value=b'{"gaps":[]}'),patch.object(frontier,"load",return_value={}), \
             patch.object(radar.sibling,"index",return_value=("head",{})),patch.object(radar.plugins,"discover",return_value={}):
            with self.assertRaises(RuntimeError):radar.build()
if __name__=="__main__":unittest.main()

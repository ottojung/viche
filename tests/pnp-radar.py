import json,sys,unittest,time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp import radar,frontier
from missions.pnp.lbcert import live
class Tests(unittest.TestCase):
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
            self.assertEqual(r["families"][1]["free_points"],0)
            self.assertTrue(r["families"][0]["examples"][0]["offered"])
    def test_stale_observation_is_not_ranked(self):
        with patch.object(live,"gaps_bytes",return_value=b'{"gaps":[]}'),patch.object(frontier,"load",return_value={}), \
             patch.object(radar.sibling,"index",return_value=("head",{})),patch.object(radar.plugins,"discover",return_value={}):
            with self.assertRaises(RuntimeError):radar.build()
if __name__=="__main__":unittest.main()

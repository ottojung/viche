#!/usr/bin/env python3
"""Check that upstream hints never replace the leased statement or scope."""
import json
import tempfile
import sys
from pathlib import Path
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp import brief, config, desk, state, staff
ROW={"id":"L-meta-7","statement":"True","module":"PEqualNP.Outside.L_meta_7",
     "file":"lean/PEqualNP/Outside/L_meta_7.lean","imports":["PEqualNP.Defs"],
     "sketch":"Step 2 of 2 of a checked cut of L-meta-6. Its sibling steps: L-meta-5.",
     "reductions":True}
CUT={"parent":"L-meta-6","state":"open",
     "artifact":{"lean_file":"lean/PEqualNP/Outside/R_meta_6_1.lean","content_hash":"sha256:123"}}
REC={"gap_id":ROW["id"],"statement":ROW["statement"],"module":ROW["module"],
     "path":ROW["file"],"imports":ROW["imports"],"dead":["failed route"]}
class Test(unittest.TestCase):
    def test_cut_and_siblings(self):
        notes=brief.read(REC,{"gaps":[ROW],"reductions":[CUT]})
        self.assertEqual(notes["parents"],["L-meta-6"])
        self.assertEqual(notes["siblings"],["L-meta-5"])
        self.assertEqual(notes["reduction_sources"][0]["path"],CUT["artifact"]["lean_file"])
        self.assertEqual(notes["dead"],["failed route"])
        self.assertNotIn("statement",notes)
    def test_mismatch_never_changes_scope(self):
        notes=brief.read(REC,{"gaps":[dict(ROW,statement="False")],"reductions":[CUT]})
        self.assertNotIn("sketch",notes)
        notes=brief.read(dict(REC,desk_notes={"sketch":"leased sketch"}),{"gaps":[ROW],"reductions":[CUT]})
        self.assertEqual(notes["sketch"],"leased sketch")
    def test_shard_preserved_at_wire_boundary(self):
        payload={"gap":ROW,"lease":"lease","shard":2,"shards":8}
        d=desk.Desk(request=lambda *a:(200,json.dumps(payload)),min_interval=0)
        answer=d._next_gap()
        self.assertEqual(brief.acquisition(answer["gap"],answer)["shard"],2)
        self.assertEqual(brief.acquisition(answer["gap"],answer)["shards"],8)
    def test_reacquisition_replaces_previous_hints(self):
        with tempfile.TemporaryDirectory() as tmp, patch.multiple(config,GAPS_DIR=tmp+"/gaps",CACHE_DIR=tmp+"/cache"):
            state.create(REC["gap_id"],state="RELEASED",desk_notes={"sketch":"old","shard":3})
            rec=state.reacquire(REC["gap_id"],desk_notes={"sketch":"new"})
            self.assertEqual(rec["desk_notes"],{"sketch":"new"})
    def test_prompt_includes_the_actual_sketch(self):
        with patch.object(brief,"read",return_value={"sketch":"known argument"}):
            self.assertIn("known argument",staff.prompt(dict(REC,state="LEASED"),"proof"))
if __name__=="__main__":
    unittest.main(verbosity=2)

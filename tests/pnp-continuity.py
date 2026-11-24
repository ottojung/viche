#!/usr/bin/env python3
"""Hermetic tests of standing Executive orders and correction liveness."""
import contextlib
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp import assignment, build_control, config, continuity, focus, staff, state, support
from missions.pnp.proofs import fragments

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root=self.tmp.name
        p=patch.multiple(config,STATE_ROOT=root,GAPS_DIR=root+"/gaps",CACHE_DIR=root+"/cache")
        p.start();self.addCleanup(p.stop)
        self.a=state.create("L-meta-1",state="LEASED",lease="a",statement="True",lease_expires_at=time.time()+600)
        self.b=state.create("L-meta-2",state="LEASED",lease="b",statement="True",lease_expires_at=time.time()+600)
    def test_baseline_and_focus_are_not_model_turns(self):
        observed={"coverage":"complete","agents":[],"support":[]}
        with patch.object(continuity.status,"workers",return_value=observed), \
             patch.object(staff,"roster",return_value=[]), \
             patch.object(staff,"baseline",return_value=[]) as baseline, \
             patch.object(staff,"dispatch",return_value=[]) as dispatch, \
             patch.object(continuity,"support_pass",return_value={}) as scout:
            continuity.execute()
        baseline.assert_called_once_with([],locked=True)
        self.assertEqual(dispatch.call_count,1)
        self.assertEqual([p[0] for p in dispatch.call_args.args[1]],["integrator","alternative"])
        self.assertEqual(scout.call_count,5)
    def test_unknown_roster_does_not_dispatch(self):
        with patch.object(continuity.status,"workers",return_value={"coverage":"partial"}),patch.object(staff,"roster") as roster:
            self.assertEqual(continuity.execute()["status"],"worker coverage unknown")
            roster.assert_not_called()
    def test_focus_integrator_replenished_independently(self):
        path=assignment.prepare(self.a["gap_id"],checkout=False,worker="construction")["cwd"]
        agents=[{"cwd":path,"state":"running"}]
        self.assertEqual([p[0] for p in continuity.focus_plans(self.a,agents)],["integrator"])
        self.assertEqual([p[0] for p in continuity.focus_plans(self.b,agents)],["integrator","alternative"])
    def test_support_receipt_no_repeat_without_changed_evidence(self):
        role="knowledge"
        path=str(Path(config.STATE_ROOT,"swarm","standing-support",role))
        records=[self.a,self.b]
        with patch.object(staff,"antonina",side_effect=["agent-id",json.dumps({"state":"running"})]) as wire:
            self.assertEqual(continuity.support_pass(role,records,self.a,[])["status"],"started")
            self.assertEqual(wire.call_count,2)
        done=[{"id":"agent-id","title":support.PREFIX+" "+role,"state":"clearexit","cwd":path}]
        with patch.object(staff,"antonina") as wire:
            self.assertEqual(continuity.support_pass(role,records,self.a,done)["status"],"completed same evidence")
            wire.assert_not_called()
        self.assertEqual(continuity.completed_roles(records,self.a),{role})
        support.advise(self.a["gap_id"],support.attempt(self.a),"checked","proof","new exact match")
        self.assertFalse(continuity.completed_roles(records,self.a))
    def test_correction_workspace_and_compilation(self):
        rec=state.create("L-meta-3",state="PR_OPEN",lease="old",statement="True",pr_number=42,
                         local_check_status="failed",external_verdict="pending",lease_expires_at=0)
        with patch.object(focus,"current",return_value=rec):
            self.assertTrue(staff.current_matches(rec))
            self.assertFalse(staff.current_matches(rec,general=True))
            a=assignment.prepare(rec["gap_id"],checkout=False,worker="correction")
            self.assertEqual(assignment.binding(Path(a["cwd"])),(rec["gap_id"],"old"))
        self.assertFalse(build_control.obsolete(rec["gap_id"],"old"))
        self.assertTrue(build_control.obsolete(rec["gap_id"],"superseded"))
        state.update(rec["gap_id"],queued_lease="old")
        self.assertTrue(build_control.obsolete(rec["gap_id"],"old"))
    def test_fragment_survives_source_edit_and_reacquisition(self):
        path=Path(assignment.prepare(self.a["gap_id"],checkout=False,worker="general")["cwd"])
        path.mkdir(parents=True)
        source=path/"Helper.lean";source.write_text("lemma helper : True := by trivial\n")
        with patch.object(fragments.subprocess,"check_output",return_value="base\n"):
            fragment=fragments.share(source,"helper, not checked",path)
        source.write_text("different")
        self.assertIn("lemma helper",Path(fragment["path"]).read_text())
        self.assertEqual(len(fragments.inventory(cwd=path)),1)
        state.update(self.a["gap_id"],lease="new")
        new=Path(assignment.prepare(self.a["gap_id"],checkout=False,worker="general")["cwd"])
        self.assertEqual(fragments.inventory(cwd=new),[])
        old,=fragments.inventory(True,cwd=new)
        self.assertFalse(old["current_attempt"])
        self.assertFalse(old["verified_by_tool"])

if __name__=="__main__":
    unittest.main(verbosity=2)

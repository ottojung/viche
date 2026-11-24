#!/usr/bin/env python3
"""Offline lease allocation policy, no external mutations."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from missions.pnp import allocator, assignment, cli, config, focus, state

NOW = 10000


class Desk:
    def __init__(self, offers=()):
        self.offers = list(offers)
        self.calls = []
        self.releases = []

    def docs(self):
        return "fixture"

    def next_gap(self, hard=False, another=False):
        self.calls.append((hard, another))
        if not self.offers:
            return None
        expected, result = self.offers.pop(0)
        assert expected == hard, (expected, hard)
        if result is None:
            return None
        return {"gap":{"id":result, "statement":"True", "module":"PEqualNP.Outside."+result.replace("-","_"),
                       "file":"lean/PEqualNP/Outside/"+result.replace("-","_")+".lean"},
                "lease":"lease-"+result}

    def release(self, lease, reason):
        self.releases.append((lease,reason))
        return {}


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = self.tmp.name
        self.patch = patch.multiple(config, STATE_ROOT=root, GAPS_DIR=root+"/gaps", CACHE_DIR=root+"/cache")
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.addCleanup(self.tmp.cleanup)

    def add(self, gap="L-meta-1", **extra):
        fields = dict(state="LEASED", lease="lease-"+gap, lease_obtained_at=NOW-1800,
                      lease_expires_at=NOW+1200, statement="True")
        fields.update(extra)
        return state.create(gap, **fields)

    def test_prefer_ordinary_fill_hard_cap(self):
        d = Desk([(False,"L-meta-1"),(False,None)]+[(True,"L-meta-"+str(i)) for i in range(2,6)])
        mem = {}
        self.assertEqual(len(allocator.fill(d,mem,NOW,{"ordinary":1,"offerable":3})),5)
        self.assertEqual(len(cli.held_records()),5)
        self.assertEqual(d.calls[:3],[(False,False),(False,True),(True,True)])
        self.assertEqual(len(d.calls),6)
        self.assertEqual(allocator.fill(d,mem,NOW+30,{}),[])
        self.assertEqual(len(d.calls),6)

    def test_null_backoff_and_new_ordinary_signal(self):
        d = Desk()
        mem = {}
        allocator.fill(d,mem,NOW,{"ordinary":0})
        self.assertEqual(d.calls,[(False,False),(True,False)])
        allocator.fill(d,mem,NOW+30,{"ordinary":0})
        self.assertEqual(len(d.calls),2)
        allocator.fill(d,mem,NOW+60,{"ordinary":1})
        self.assertEqual(d.calls[-1],(False,False))
        self.assertEqual(len(d.calls),3)
        allocator.fill(d,mem,NOW+121,{})
        self.assertEqual(d.calls[-1],(True,False))

    def test_publication_does_not_occupy_slots(self):
        self.add(state="PR_OPEN",pr_number=42)
        self.add("L-meta-2",state="REJECTED",pr_number=43)
        self.add("L-meta-3",state="SIGNED")
        self.assertEqual([r["gap_id"] for r in cli.held_records()],["L-meta-3"])

    def test_release_only_after_confirmed_absence(self):
        rec=self.add()
        d=Desk()
        mem={}
        live={(rec["gap_id"],rec["lease"])}
        allocator.retire(d,mem,NOW,(live,set()))
        allocator.retire(d,mem,NOW+30,(set(),set()))
        self.assertEqual(allocator.retire(d,mem,NOW+200,(set(),set())),[])
        with patch.object(allocator,"bound_roster",return_value=(set(),set())):
            self.assertEqual(allocator.retire(d,mem,NOW+331,(set(),set())),["L-meta-1"])
        self.assertEqual(d.releases,[(rec["lease"],"other")])
        self.assertEqual(state.load(rec["gap_id"])["state"],"RELEASED")

    def test_unknown_roster_resets_absence(self):
        self.add()
        d=Desk()
        mem={}
        allocator.retire(d,mem,NOW,(set(),set()))
        allocator.retire(d,mem,NOW+100,None)
        allocator.retire(d,mem,NOW+1300,(set(),set()))
        self.assertFalse(d.releases)

    def test_new_or_queued_not_released(self):
        self.add(lease_obtained_at=NOW)
        self.add("L-meta-2",state="CANDIDATE_READY",queued_lease="lease-L-meta-2")
        self.add("L-meta-3",state="RESEARCHING",queued_lease="lease-L-meta-3")
        mem={}
        d=Desk()
        allocator.retire(d,mem,NOW,(set(),set()))
        allocator.retire(d,mem,NOW+600,(set(),set()))
        self.assertFalse(d.releases)

    def test_roster_rechecked_before_release(self):
        rec=self.add()
        d=Desk()
        with patch.object(allocator,"bound_roster",return_value=({(rec["gap_id"],rec["lease"])},set())):
            self.assertFalse(allocator.release_abandoned(rec,d,NOW,NOW-1500,True))
        self.assertFalse(d.releases)

    def test_reserves_never_released_for_idle_roster(self):
        for i in range(1,6):
            self.add("L-meta-"+str(i))
        d = Desk()
        mem = {}
        allocator.retire(d,mem,NOW,(set(),set()))
        allocator.retire(d,mem,NOW+7200,(set(),set()))
        self.assertEqual(d.releases,[])
        self.assertEqual(len(cli.held_records()),5)

    def test_single_stable_focus_and_rotation(self):
        hard = self.add(acquisition_hard=True)
        ordinary = self.add("L-meta-2",acquisition_hard=False)
        self.assertEqual(focus.choose([hard,ordinary],now=NOW),ordinary)
        self.assertEqual(focus.choose([hard,ordinary],focus.key(hard),now=NOW),hard)
        hard["queued_lease"]=hard["lease"]
        self.assertEqual(focus.choose([hard,ordinary],focus.key(hard),now=NOW),ordinary)
        correction = self.add("L-meta-3",state="PR_OPEN",pr_number=42,local_check_status="failed")
        self.assertEqual(focus.choose([hard,ordinary,correction],now=NOW),correction)
        self.assertEqual(focus.choose([hard,ordinary,correction],focus.key(ordinary),now=NOW),ordinary)

    def test_independent_parallel_workspaces_same_exact_lease(self):
        rec = self.add()
        a = Path(assignment.prepare(rec["gap_id"],checkout=False,worker="construction")["cwd"])
        b = Path(assignment.prepare(rec["gap_id"],checkout=False,worker="formalization")["cwd"])
        self.assertNotEqual(a,b)
        self.assertEqual(assignment.binding(a/"lean"),focus.key(rec))
        self.assertEqual(assignment.binding(b),focus.key(rec))
        state.transition(rec["gap_id"],"STALE")
        state.reacquire(rec["gap_id"],lease="fresh")
        c = Path(assignment.prepare(rec["gap_id"],checkout=False,worker="construction")["cwd"])
        self.assertNotEqual(a,c)
        self.assertEqual(assignment.binding(c),(rec["gap_id"],"fresh"))
        self.assertEqual(assignment.binding(a),focus.key(rec))
        with self.assertRaises(ValueError):
            assignment.prepare(rec["gap_id"],checkout=False,worker="../other")

    def test_new_positive_frontier_revision_wakes_acquisition(self):
        d=Desk()
        mem={}
        allocator.fill(d,mem,NOW,{"ordinary":1,"offerable":1,"source_updated_at":"a"})
        allocator.fill(d,mem,NOW+30,{"ordinary":1,"offerable":1,"source_updated_at":"a"})
        self.assertEqual(len(d.calls),2)
        allocator.fill(d,mem,NOW+60,{"ordinary":1,"offerable":1,"source_updated_at":"b"})
        self.assertEqual(d.calls[-1],(False,False))
        self.assertEqual(len(d.calls),3)

    def test_duplicate_never_churns(self):
        self.add()
        d=Desk([(False,"L-meta-1"),(True,None)])
        self.assertEqual(allocator.fill(d,{},NOW,{}),[])
        self.assertFalse(d.releases)
        self.assertEqual(len(cli.held_records()),1)


if __name__=="__main__":
    unittest.main(verbosity=2)

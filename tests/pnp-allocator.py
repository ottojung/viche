#!/usr/bin/env python3
"""Offline lease allocation policy, no external mutations."""
import os
import fcntl
import json
import time
from types import SimpleNamespace
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from missions.pnp import allocator, assignment, cli, config, desk, focus, portfolio, staff, state, support

NOW = 10000


class Desk:
    def __init__(self, offers=()):
        self.offers = list(offers)
        self.calls = []
        self.releases = []

    def docs(self):
        return "fixture"

    def _next_gap(self, hard=False, another=False):
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

    def test_missing_workers_do_not_release_leases(self):
        now=time.time()
        for i in range(1,6):
            self.add("L-meta-"+str(i),lease_expires_at=now+1200)
        d=Desk()
        with patch.object(allocator,"bound_roster",return_value=(set(),set())), \
             patch.object(allocator.frontier,"refresh",return_value={}):
            result=allocator.tick(d,now=now)
        self.assertEqual(result["held"],5)
        self.assertEqual(result["released"],[])
        self.assertFalse(d.releases)

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

    def test_raw_next_is_not_a_diagnostic(self):
        d = desk.Desk()
        with patch.object(d, "_call") as wire:
            with self.assertRaises(desk.DeskError):
                d.next_gap()
            wire.assert_not_called()

    def test_manual_acquisition_excluded_by_live_allocator(self):
        fd = os.open(os.path.join(config.STATE_ROOT, "allocator-loop.lock"),
                     os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            with patch.object(cli.desk_mod, "Desk") as factory:
                self.assertEqual(cli.cmd_acquire(SimpleNamespace(hard=False, another=True)),2)
                factory.assert_not_called()
        finally:
            os.close(fd)

    def test_staff_batch_adopts_running_and_starts_new_once(self):
        rec = self.add(lease_expires_at=time.time()+1200)
        a = Path(assignment.prepare(rec["gap_id"],checkout=False,worker="existing")["cwd"])
        calls = []
        def fake_antonina(*args):
            calls.append(args)
            if args[0] == "new":
                return "new-agent-id"
            if args[0] == "run":
                return json.dumps({"state":"running"})
            raise AssertionError(args)
        with patch.object(staff,"roster",return_value=[{"id":"running-id","cwd":str(a),"state":"running"}]), \
             patch.object(staff,"antonina",side_effect=fake_antonina), \
             patch.object(staff.gitctl,"ensure_mirror",return_value="base") as fetch, \
             patch.object(staff.assignment,"prepare",wraps=assignment.prepare) as original:
            def prepare(gap, checkout=True, worker=None, base=None):
                return original._mock_wraps(gap,checkout=False,worker=worker)
            original.side_effect=prepare
            result=staff.dispatch(rec["gap_id"],[("existing","reuse"),("fresh","new proof")])
        self.assertEqual([r["status"] for r in result],["already running","started"])
        self.assertEqual([c[0] for c in calls],["new","run"])
        fetch.assert_called_once()
        self.assertIn(rec["statement"], calls[1][calls[1].index("--prompt")+1])

    def test_staff_rejects_reserve_and_unknown_roster(self):
        a=self.add(acquisition_hard=False,lease_expires_at=time.time()+1200)
        b=self.add("L-meta-2",acquisition_hard=True,lease_expires_at=time.time()+1200)
        with patch.object(staff,"antonina") as run:
            with self.assertRaises(ValueError):
                staff.dispatch(b["gap_id"],[("x","prove")])
            with patch.object(staff,"roster",side_effect=ValueError("unknown")):
                with self.assertRaises(ValueError):
                    staff.dispatch(a["gap_id"],[("x","prove")])
            run.assert_not_called()

    def portfolio_fixture(self, **fields):
        now = time.time()
        a = self.add(acquisition_hard=True,lease_obtained_at=now-1500,
                     lease_expires_at=now+1200)
        b = self.add("L-meta-2",acquisition_hard=False,lease_obtained_at=now-1500,
                     lease_expires_at=now+1200, **fields)
        mem = {"focus":list(focus.key(a))}
        state.atomic_write(allocator.memory_path(), json.dumps(mem))
        return a,b,mem

    def test_portfolio_switch_parks_previous_focus_and_keeps_lease(self):
        a,b,mem = self.portfolio_fixture()
        with patch.object(allocator.status,"workers",return_value={"agents":[],"coverage":"complete"}):
            self.assertEqual(len(portfolio.view()["leases"]),2)
        decision=portfolio.submit("switch",b["gap_id"],support.attempt(b),
                                  "checked lemma and witness","a requires new theorem; b has explicit witness",
                                  a["gap_id"],support.attempt(a))
        portfolio.apply_switch(mem,time.time())
        self.assertEqual(mem["focus"],list(focus.key(b)))
        self.assertEqual(state.load(b["gap_id"])["state"],"LEASED")
        self.assertEqual(mem["last_switch"]["id"],decision["id"])
        self.assertEqual(state.load(a["gap_id"])["state"],"LEASED")
        portfolio.apply_switch(mem,time.time())
        self.assertEqual(mem["focus"],list(focus.key(b)))

    def test_portfolio_rejects_switch_after_source_reacquired(self):
        a,b,mem=self.portfolio_fixture()
        portfolio.submit("switch",b["gap_id"],support.attempt(b),"lemma","b substantially easier",
                         a["gap_id"],support.attempt(a))
        state.transition(a["gap_id"],"STALE")
        state.reacquire(a["gap_id"],lease="replacement",lease_expires_at=time.time()+1200)
        portfolio.apply_switch(mem,time.time())
        self.assertTrue(mem["last_switch"]["outcome"].startswith("obsolete"))
        self.assertEqual(mem["focus"],list(focus.key(a)))

    def test_evaluator_releases_with_other_and_refills(self):
        a,b,mem=self.portfolio_fixture()
        mem.update(last_null_hard=time.time(),last_null_ordinary=time.time())
        portfolio.submit("release",b["gap_id"],support.attempt(b),"failed proof routes","requires independent major lower bound")
        d=Desk()
        self.assertEqual(portfolio.apply_release(d,mem,time.time()),[b["gap_id"]])
        self.assertEqual(d.releases,[(b["lease"],"other")])
        self.assertEqual(state.load(b["gap_id"])["state"],"RELEASED")
        self.assertNotIn("last_null_ordinary",mem)
        self.assertEqual(portfolio.apply_release(d,mem,time.time()),[])
        self.assertEqual(len(d.releases),1)

    def test_evaluator_protects_queued_candidate_and_hard_minimum(self):
        a,b,mem=self.portfolio_fixture()
        state.update(a["gap_id"],lease_obtained_at=time.time())
        with self.assertRaises(ValueError):
            portfolio.submit("release",a["gap_id"],support.attempt(a),"evidence","reason")
        portfolio.submit("release",b["gap_id"],support.attempt(b),"evidence","reason")
        state.update(b["gap_id"],state="CANDIDATE_READY",queued_lease=b["lease"])
        d=Desk()
        self.assertEqual(portfolio.apply_release(d,mem,time.time()),[])
        self.assertFalse(d.releases)
        self.assertTrue(mem["last_release"]["outcome"].startswith("obsolete"))

    def test_evaluator_does_not_release_reacquired_lease(self):
        a,b,mem=self.portfolio_fixture()
        portfolio.submit("release",b["gap_id"],support.attempt(b),"evidence","reason")
        state.transition(b["gap_id"],"STALE")
        state.reacquire(b["gap_id"],lease="fresh",lease_expires_at=time.time()+1200)
        d=Desk()
        self.assertEqual(portfolio.apply_release(d,mem,time.time()),[])
        self.assertFalse(d.releases)
        self.assertEqual(state.load(b["gap_id"])["lease"],"fresh")

    def test_baseline_staffs_every_live_gap(self):
        a,b,mem=self.portfolio_fixture()
        self.add("L-meta-3",state="CANDIDATE_READY",queued_lease="q")
        with patch.object(staff,"dispatch",return_value=[{"status":"started"}]) as dispatch:
            result=staff.baseline()
        self.assertEqual({r["gap"] for r in result},{a["gap_id"],b["gap_id"]})
        self.assertTrue(all(c.args[1][0][0]=="general" for c in dispatch.call_args_list))
        self.assertTrue(staff.current_matches(b,general=True))
        self.assertFalse(staff.current_matches(b))

    def test_general_findings_available_to_peers_and_evaluators(self):
        a,b,mem=self.portfolio_fixture()
        general=Path(assignment.prepare(b["gap_id"],checkout=False,worker="general")["cwd"])
        specialist=Path(assignment.prepare(b["gap_id"],checkout=False,worker="search")["cwd"])
        self.assertTrue(assignment.general(general))
        self.assertFalse(assignment.general(specialist))
        note=support.finding("artifact.md","Specific checked proof route.",cwd=general)
        other=support.finding("search.py","A distinct search result.",cwd=specialist)
        self.assertEqual({x["id"] for x in support.findings(b)},{note["id"],other["id"]})
        with patch.object(allocator.status,"workers",return_value={"agents":[{"id":"gen","title":"general","cwd":str(general)}],"coverage":"complete"}):
            row=next(r for r in portfolio.view()["leases"] if r["gap"]==b["gap_id"])
        self.assertEqual(row["workers"][0]["role"],"general")
        self.assertIn("antonina agent log --id gen",row["workers"][0]["log_command"])
        self.assertEqual(len(row["findings"]),2)
        state.transition(b["gap_id"],"STALE")
        state.reacquire(b["gap_id"],lease="fresh",lease_expires_at=time.time()+1200)
        self.assertEqual(support.findings(state.load(b["gap_id"])),[])
        with self.assertRaises(ValueError):
            support.finding("x","old attempt",cwd=general)

    def test_duplicate_never_churns(self):
        self.add()
        d=Desk([(False,"L-meta-1"),(True,None)])
        self.assertEqual(allocator.fill(d,{},NOW,{}),[])
        self.assertFalse(d.releases)
        self.assertEqual(len(cli.held_records()),1)


if __name__=="__main__":
    unittest.main(verbosity=2)

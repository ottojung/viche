#!/usr/bin/env python3
"""Hermetic failure-injection tests of the standing staffing controller."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp import assignment, config, focus, state, support, staff
from missions.pnp.staffing import backend, controller, plan, policy, reconcile, store


class Fake:
    def __init__(self):
        self.agents={}
        self.created=0
        self.runs=[]
        self.stops=[]
        self.mode=""
        self.clock=time.time()

    def status(self,aid):
        if self.mode=="unknown":
            raise subprocess.TimeoutExpired("status",1)
        if aid not in self.agents:
            raise backend.MissingAgent("deleted")
        return dict(self.agents[aid])

    def new(self,slot):
        self.created+=1
        aid="agent-"+str(self.created)
        self.agents[aid]={"id":aid,"cwd":slot.path,"state":"idle","alive":False,
                          "created_at":time.time()}
        if self.mode=="create-timeout":
            raise subprocess.TimeoutExpired("new",1)
        return aid

    def run(self,slot,aid):
        self.runs.append(aid)
        self.agents[aid].update(state="running",alive=True,started_at=time.time())
        if self.mode=="run-timeout":
            raise subprocess.TimeoutExpired("run",1)
        if self.mode=="crash":
            raise KeyboardInterrupt()

    def stop(self,aid):
        self.stops.append(aid)
        self.agents[aid].update(state="stopped",alive=False,finished_at=time.time())

    def running(self):
        return [dict(x) for x in self.agents.values() if x["state"]=="running"]

    def history(self):
        return [dict(x) for x in self.agents.values()]

    def finish(self,aid,seconds=100,failed=False):
        self.agents[aid].update(state="failed" if failed else "clearexit",alive=False,
                                started_at=time.time()-seconds,finished_at=time.time())


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root=self.tmp.name
        q=patch.multiple(config,STATE_ROOT=root,GAPS_DIR=root+"/gaps",CACHE_DIR=root+"/cache")
        q.start();self.addCleanup(q.stop)
        self.fake=Fake()
        q=patch.multiple(backend,status=self.fake.status,new=self.fake.new,run=self.fake.run,
                         stop=self.fake.stop,running=self.fake.running,prepare=lambda s:None,
                         resource_ready=lambda:True)
        q.start();self.addCleanup(q.stop)
        self.p=dict(policy.DEFAULT)
        self.rec=state.create("L-meta-1",state="LEASED",lease="fixture",statement="True",
                              lease_expires_at=time.time()+3600)
        self.slot=plan.bound(self.rec,"general","fixture",0)

    def step(self,slot=None,now=None,history=True):
        return reconcile.reconcile(slot or self.slot,self.p,self.fake.running(),
                                   self.fake.history() if history else None,now)

    def launch(self):
        r=self.step()
        self.assertEqual(r["phase"],"starting")
        self.assertEqual(self.step()["phase"],"running")
        return r["agent"]

    def age_intent(self,slot=None):
        s=slot or self.slot
        r=store.get(s.key)
        r["intent"]["at"]-=120
        r["next_at"]=0
        store.put(s.key,r)

    def test_ack_is_not_coverage_and_restarts_same_workspace(self):
        aid=self.launch()
        self.fake.finish(aid)
        r=self.step()
        self.assertEqual(r["phase"],"vacant")
        self.assertEqual(self.step()["phase"],"vacant")
        self.assertEqual(self.step(now=r["next_at"]+1)["phase"],"starting")
        self.assertEqual(self.fake.runs,[aid,aid])
        self.assertEqual(self.fake.created,1)

    def test_run_timeout_recovers_observed_effect(self):
        self.fake.mode="run-timeout"
        r=self.step()
        self.assertEqual(r["phase"],"unknown")
        self.assertEqual(store.get(self.slot.key)["intent"]["op"],"run")
        self.fake.mode=""
        self.assertEqual(self.step()["phase"],"running")
        self.assertEqual(len(self.fake.runs),1)

    def test_process_crash_after_run_before_ack(self):
        self.fake.mode="crash"
        with self.assertRaises(KeyboardInterrupt):
            self.step()
        self.assertEqual(store.get(self.slot.key)["intent"]["op"],"run")
        self.fake.mode=""
        self.assertEqual(self.step()["phase"],"running")
        self.assertEqual(len(self.fake.runs),1)

    def test_new_timeout_adopts_idle_orphan(self):
        self.fake.mode="create-timeout"
        r=self.step()
        self.assertEqual(r["phase"],"unknown")
        self.assertEqual(store.get(self.slot.key)["intent"]["op"],"new")
        self.fake.mode=""
        self.assertEqual(self.step()["phase"],"unknown")
        self.age_intent()
        self.assertEqual(self.step()["phase"],"starting")
        self.assertEqual(self.fake.created,1)

    def test_ambiguous_launch_without_effect_is_retried_only_after_grace(self):
        aid=self.fake.new(self.slot)
        with patch.object(backend,"run",side_effect=subprocess.TimeoutExpired("run",1)):
            self.assertEqual(self.step()["phase"],"unknown")
        self.assertEqual(self.step()["phase"],"unknown")
        self.age_intent()
        self.assertEqual(self.step()["phase"],"starting")
        self.assertEqual(self.fake.runs,[aid])

    def test_unknown_backend_never_authorizes_replacement(self):
        aid=self.launch()
        self.fake.mode="unknown"
        self.assertEqual(self.step()["phase"],"unknown")
        self.assertEqual(self.fake.runs,[aid])
        self.fake.mode=""
        self.assertEqual(self.step()["phase"],"running")

    def test_no_history_no_create(self):
        self.assertEqual(self.step(history=False)["phase"],"unknown")
        self.assertEqual(self.fake.created,0)

    def test_deleted_identity_recovers(self):
        aid=self.launch()
        self.fake.finish(aid)
        del self.fake.agents[aid]
        r=self.step()
        self.assertIsNone(r["agent"])
        self.assertEqual(self.step(now=r["next_at"]+1)["phase"],"starting")
        self.assertEqual(self.fake.created,2)

    def test_duplicate_retirement_keeps_previous_owner(self):
        aid=self.launch()
        other=self.fake.new(self.slot)
        self.fake.run(self.slot,other)
        self.assertEqual(self.step()["phase"],"unknown")
        self.assertEqual(self.fake.stops,[other])
        self.assertEqual(self.step()["agent"],aid)
        self.assertEqual(self.step()["phase"],"running")

    def test_duplicate_pause_does_not_stop(self):
        self.launch()
        self.fake.run(self.slot,self.fake.new(self.slot))
        self.p["paused"]=True
        self.assertEqual(self.step()["phase"],"unknown")
        self.assertFalse(self.fake.stops)

    def test_orphaned_running_identity_reconciled(self):
        aid=self.launch()
        self.fake.agents[aid]["alive"]=False
        now=time.time()
        self.assertEqual(self.step(now=now)["phase"],"unknown")
        self.assertFalse(self.fake.stops)
        self.step(now=now+self.p["ambiguity_grace"]+1)
        self.assertEqual(self.fake.stops,[aid])

    def test_rotate_after_repeated_short_exit_preserves_workspace(self):
        aid=self.launch()
        self.p["rotate_after"]=2
        for i in range(2):
            self.fake.finish(aid,seconds=1)
            r=self.step()
            r=self.step(now=r["next_at"]+1)
            if i==0:
                self.assertEqual(r["agent"],aid)
                self.step()
        # Second failed context gets a different identity, same exact slot.
        self.assertEqual(self.fake.created,2)
        self.assertNotEqual(r["agent"],aid)
        self.assertEqual(self.fake.agents[r["agent"]]["cwd"],self.slot.path)

    def test_lease_change_during_prepare_no_launch(self):
        def swap(s):
            state.update(self.rec["gap_id"],lease="replacement")
        with patch.object(backend,"prepare",side_effect=swap):
            r=self.step()
        self.assertEqual(r["phase"],"obsolete")
        self.assertFalse(self.fake.runs)
        self.assertEqual(self.fake.created,0)
        with self.assertRaises(ValueError):
            assignment.prepare(self.rec["gap_id"],checkout=False,worker="general",expected="fixture")

    def test_resource_deferral_no_launch(self):
        with patch.object(backend,"resource_ready",return_value=False):
            r=self.step()
        self.assertEqual(r["phase"],"deferred")
        self.assertFalse(self.fake.runs)

    def test_support_same_evidence_completes_then_refreshes(self):
        s=plan.Slot(str(Path(config.STATE_ROOT,"swarm","standing-support","knowledge")),
                    "knowledge","task",signature="v1")
        aid=self.step(s)["agent"]
        self.step(s)
        self.fake.finish(aid)
        r=self.step(s)
        r=self.step(s,now=r["next_at"]+1)
        self.assertEqual(r["phase"],"completed")
        self.assertEqual(len(self.fake.runs),1)
        self.assertEqual(self.step(s,now=r["last_finish"]+601)["phase"],"starting")

    def test_focus_switch_keeps_general_and_retires_exact_specialist(self):
        b=state.create("L-meta-2",state="LEASED",lease="second",statement="True",
                       lease_expires_at=time.time()+3600)
        path=assignment.prepare(self.rec["gap_id"],checkout=False,worker="integrator")["cwd"]
        a={"cwd":path,"id":"old"}
        gen={"cwd":assignment.prepare(self.rec["gap_id"],checkout=False,worker="general")["cwd"]}
        with patch.object(focus,"current",return_value=b):
            self.assertTrue(plan.obsolete(a,[]))
            self.assertFalse(plan.obsolete(gen,[]))
            slots=plan.desired(self.p,[])
        self.assertEqual(sum(s.label=="general" for s in slots),2)
        self.assertEqual({s.gap for s in slots if s.label=="integrator"},{b["gap_id"]})

    def test_refuted_obligation_is_not_dispatched_and_exact_worker_retires(self):
        from missions.pnp.research import knowledge as k, obligations as o
        c=k.db();self.addCleanup(c.close)
        target=k.add(c,"obligation","test","True",k.canon({"imports":["Mathlib"]}),
                     "L-meta-1 / fixture",base="a"*40)
        negation=k.add(c,"obligation","test","¬ True",k.canon({"imports":["Mathlib"]}),
                       "L-meta-1 / fixture",base="a"*40)
        body=k.store_bytes(b"by simp")
        source=k.store_bytes(o.build(c,negation,"by simp").encode())
        result={"status":"kernel_checked","compiler":{"status":"elaborated","exit_code":0,
            "base":"a"*40,"source_sha256":source,
            "diagnostic":f"'{o.symbol(negation)}' does not depend on any axioms"}}
        with c:c.execute("INSERT INTO proof VALUES(?,?,?,?,?,?)",
                         (negation,"a"*40,body,source,k.canon(result),1))
        k.link(c,negation,target,"counterexample_to")
        path=assignment.prepare(self.rec["gap_id"],checkout=False,worker="ob-"+target)["cwd"]
        ready=k.add(c,"obligation","test","True ∧ True",k.canon({"imports":["Mathlib"]}),
                    "L-meta-1 / fixture",base="a"*40)
        ready_path=assignment.prepare(self.rec["gap_id"],checkout=False,worker="ob-"+ready)["cwd"]
        self.p["focus_obligations"]=0
        with patch.object(focus,"current",return_value=self.rec):
            slots=plan.desired(self.p,[])
            self.assertNotIn("ob-"+target,[s.label for s in slots])
            self.assertTrue(plan.obsolete({"cwd":path},slots))
            self.assertFalse(plan.obsolete({"cwd":ready_path},slots))

    def test_obligation_dispatch_respects_ownership_and_critical_path(self):
        from missions.pnp.research import knowledge as k, async_check
        c=k.db(); self.addCleanup(c.close)
        attempt=support.attempt(self.rec)
        origin=self.rec["gap_id"]+" / "+attempt
        def node(stmt):
            return k.add(c,"obligation","test",stmt,k.canon({"imports":["Mathlib"]}),origin,base="a"*40)
        first,second,third,demo=map(node,("1=1","2=2","3=3","4=4"))
        root=k.add(c,"obligation","test","True",k.canon({"imports":["Mathlib"]}),origin,base="a"*40,deps=(first,second,third))
        async_check.table(c)
        with c:
            c.execute("INSERT INTO assignment VALUES(?,?,?,?)",(first,attempt,"general",time.time()))
            c.execute("INSERT INTO pending_check(id,node,state) VALUES(?,?,?)",("job",second,"queued"))
        slots=plan.obligation_slots(self.rec,[],2)
        self.assertEqual([s.label for s in slots],["ob-"+third])
        backend.reserve_obligation(slots[0])
        backend.reserve_obligation(slots[0])
        with self.assertRaises(backend.Uncertain):
            backend.reserve_obligation(plan.bound(self.rec,"ob-"+first,"task",2))
        self.assertEqual(c.execute("SELECT worker FROM assignment WHERE node=? AND attempt=?",(first,attempt)).fetchone()[0],"general")

    def test_bad_policy_fails_closed(self):
        policy.root().mkdir(parents=True)
        (policy.root()/"policy.json").write_text('{"parallel":100000}')
        with self.assertRaises(ValueError):policy.load()
        (policy.root()/"policy.json").write_text('{"paused":true,"interval":3}')
        self.assertTrue(policy.load()["paused"])

    def test_tick_runs_known_slots_despite_history_error(self):
        aid=self.launch()
        other=state.create("L-meta-2",state="LEASED",lease="b",statement="True",
                           lease_expires_at=time.time()+3600)
        with patch.object(staff,"roster",side_effect=ValueError("history unavailable")):
            out=controller.tick()
        r=next(x for x in out["slots"] if x["key"]==self.slot.key)
        self.assertEqual(r["phase"],"running")
        self.assertEqual(r["agent"],aid)
        cold=next(x for x in out["slots"] if x["gap"]==other["gap_id"] and x["label"]=="general")
        self.assertEqual(cold["phase"],"unknown")

    def test_partial_running_snapshot_never_starts(self):
        with patch.object(backend,"running",side_effect=backend.Uncertain("partial")):
            with self.assertRaises(backend.Uncertain):controller.tick()
        self.assertFalse(self.fake.runs)

    def test_persistent_vacancy_alert_not_transient(self):
        aid=self.launch()
        self.fake.finish(aid)
        self.step()
        row=store.get(self.slot.key)
        row["uncovered_since"]=time.time()-200
        row["next_at"]=time.time()+120
        store.put(self.slot.key,row)
        with patch.object(staff,"roster",return_value=self.fake.history()):
            out=controller.tick()
        self.assertIn(self.rec["gap_id"]+":general",out["alerts"])
        self.assertNotIn(self.rec["gap_id"]+":integrator",out["alerts"])

    def test_metrics_no_imputation_across_outage(self):
        t=time.time()-300
        a=[{"label":"general","phase":"running"}]
        store.sample(a,t)
        store.sample(a,t+200)
        m=store.metrics()
        self.assertEqual(m["general_covered_seconds"],60)
        self.assertEqual(m["unobserved_seconds"],140)

if __name__=="__main__":
    unittest.main(verbosity=2)

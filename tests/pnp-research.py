#!/usr/bin/env python3
"""Offline regression tests for the research substrate."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tempfile
import unittest
from unittest.mock import patch
import itertools
import json
from missions.pnp import config,state
from missions.pnp.research import knowledge as k,obligations as o,star,yield_model as y,adoption,async_check,certificate,playbook
from missions.pnp import assignment,staff,continuity,support
import os

class Research(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        root=Path(t.name)/"pnp"
        for key,value in [("STATE_ROOT",str(root)),("GAPS_DIR",str(root/"gaps"))]:
            p=patch.object(config,key,value);p.start();self.addCleanup(p.stop)
        self.c=k.db();self.addCleanup(self.c.close)
        self.base="a"*40
    def obligation(self,stmt,deps=()):
        return k.add(self.c,"obligation","test",stmt,k.canon({"imports":["Mathlib"]}),"test fixture",base=self.base,deps=deps)
    def fixture_receipt(self,a,body):
        h=k.store_bytes(body.encode())
        source=k.store_bytes(o.build(self.c,a,body).encode())
        r={"status":"kernel_checked","compiler":{"status":"elaborated","exit_code":0,
            "base":self.base,"source_sha256":source,"diagnostic":f"'{o.symbol(a)}' does not depend on any axioms"}}
        with self.c:self.c.execute("INSERT INTO proof VALUES(?,?,?,?,?,?)",(a,self.base,h,source,k.canon(r),1))
        return h
    def test_graph(self):
        a=self.obligation("True")
        self.assertEqual(a,self.obligation("True"))
        b=self.obligation("True ∧ True",[a])
        self.assertEqual([x["id"] for x in o.plan(self.c,b)],[a,b])
        self.assertEqual({x["id"]:x["status"] for x in o.ready(self.c)},{a:"ready",b:"blocked"})
        with self.assertRaises(ValueError):o.build(self.c,b,"by trivial")
        with self.assertRaises(ValueError):self.obligation("False",["missing"])
        m=o.fork(self.c,b,"b"*40)
        self.assertEqual(k.get(self.c,m[b])["dependencies"],[m[a]])
        self.assertFalse(k.get(self.c,m[a])["checks"])
    def test_checked_negation_marks_target_refuted(self):
        target=self.obligation("True")
        negation=self.obligation("¬ True")
        self.fixture_receipt(negation,"by simp")
        k.link(self.c,negation,target,"counterexample_to")
        statuses={x["id"]:x for x in o.ready(self.c)}
        self.assertEqual(statuses[target]["status"],"refuted")
        self.assertEqual(statuses[target]["refuted_by"],[negation])
        self.assertEqual(statuses[negation]["status"],"checked")

        unverified=self.obligation("¬ True ∧ True")
        other=self.obligation("True ∧ True")
        k.link(self.c,unverified,other,"counterexample_to")
        statuses={x["id"]:x for x in o.ready(self.c)}
        self.assertEqual(statuses[other]["status"],"ready")
        self.assertEqual(statuses[other]["refuted_by"],[])

    def test_axioms(self):
        a=self.obligation("True");name=o.symbol(a)
        self.assertTrue(o.verify_output(f"'{name}' depends on axioms: [propext, Classical.choice, Quot.sound]",a))
        self.assertTrue(o.verify_output(f"'{name}' does not depend on any axioms",a))
        self.assertFalse(o.verify_output(f"'{name}' depends on axioms: [sorryAx]",a))
        self.assertFalse(o.verify_output("",a))
        valid=f"'{name}' does not depend on any axioms"
        self.assertFalse(o.verify_output("trace: "+valid,a))
        self.assertFalse(o.verify_output(valid+"\n"+f"'{name}' depends on axioms: [sorryAx]",a))
        self.assertFalse(o.verify_output(valid+"\ntrailing message",a))
        for body in ("by sorry","by native_decide","by trace \"fake\"","by trivial\n#print axioms x",
                     "by trivial /- unclosed","set_option pp.universes 1 in\nby trivial",
                     "by trivial\nlemma fake : False := by trivial"):
            with self.subTest(body=body),self.assertRaises(ValueError):o.clean_body(body)
        o.clean_body("set_option maxHeartbeats 4000000 in\nby /- nested /- comment -/ -/ trivial")
        source=o.build(self.c,a,"by trivial")
        self.assertTrue(o.source_verified(source,a))
        self.assertFalse(o.source_verified(source+"\n",a))
        self.assertFalse(o.source_verified(source,"another"))
        self.assertFalse(o.source_verified(source.replace("by trivial","by native_decide"),a))
        self.assertFalse(o.source_verified(source.replace("by trivial","by trivial\n#exit"),a))
        injected=self.obligation("True\naxiom bogus : False")
        with self.assertRaises(ValueError):o.build(self.c,injected,"by trivial")

    def test_sync_receipt(self):
        from types import SimpleNamespace
        a=self.obligation("True")
        def method(base,oid,source):
            return SimpleNamespace(returncode=0,stderr=""),{"status":"elaborated","exit_code":0,
                "base":base,"source_sha256":k.digest(source.encode()),
                "diagnostic":f"'{o.symbol(oid)}' does not depend on any axioms"}
        with tempfile.NamedTemporaryFile(mode="w") as f:
            f.write("by trivial");f.flush()
            with patch.object(o,"method_check",side_effect=method):
                result=o.solve(self.c,a,f.name,method=True)
        self.assertEqual(result["status"],"kernel_checked")
        self.assertEqual(o.checked_body(self.c,a,self.base),"by trivial")
    def test_candidate(self):
        a=self.obligation("True")
        self.fixture_receipt(a,"by trivial")
        rec={"gap_id":"L-meta-1","module":"PEqualNP.Outside.L_meta_1","path":"lean/PEqualNP/Outside/L_meta_1.lean","statement":"True","imports":[]}
        code=o.candidate(self.c,a,rec,self.base)
        self.assertIn("namespace PEqualNP.Outside.L_meta_1_aux",code)
        self.assertIn("theorem PEqualNP.Outside.L_meta_1 : True",code)
        self.assertNotIn("#print",code)
    def test_symbolic_exhaustive(self):
        # All nonempty graphs on four vertices.
        edges=list(itertools.combinations(range(4),2))
        for mask in range(1,1<<len(edges)):
            E=[e for i,e in enumerate(edges) if mask>>i&1]
            z=star.synthesize(4,E)
            self.assertEqual(star.verify(4,E,z["gates"],z["output"])["status"],"verified")
            size=min(len(C) for k in range(1,5) for C in itertools.combinations(range(4),k) if all(a in C or b in C for a,b in E))
            self.assertEqual(len(z["cover"]),size)
            self.assertLessEqual(len(z["gates"]),len(E)+size-1)
        self.assertEqual(star.verify(2,[(0,1)],[("or",0,1)],2)["status"],"counterexample")
    def test_exact_cross_origin_dedup(self):
        a=self.obligation("True")
        b=k.add(self.c,"obligation","another-family","True",k.canon({"imports":["Mathlib"]}),
                "L-meta-19 / another attempt",base=self.base)
        self.assertEqual(a,b)
        self.assertEqual(len(k.get(self.c,a)["origins"]),2)
        self.assertTrue(k.belongs(self.c,a,"L-meta-19 / "))
        self.assertEqual(o.fork(self.c,a,self.base),{a:a})
        self.assertEqual(len(k.search(self.c,"True",fam="another-family")),1)
    def test_role_delivery_and_adoption(self):
        rec=state.create("L-meta-5",state="LEASED",lease="fixture",statement="True",
                         lease_expires_at=__import__("time").time()+600)
        p=Path(assignment.prepare(rec["gap_id"],checkout=False,worker="general")["cwd"])
        p.mkdir(parents=True)
        class Result:
            stdout='{"state":"running"}'
        with patch.object(staff.subprocess,"run",return_value=Result()) as wire:
            staff.antonina("run","--id","agent-fixture","--cwd",str(p),"--prompt","Exact task","--detach","--json")
            prompt=wire.call_args.args[0]
            self.assertIn("YOUR ROLE: general",prompt[prompt.index("--prompt")+1])
            self.assertIn("pnp-research start",prompt[prompt.index("--prompt")+1])
        with patch.dict(os.environ,{"ANTONINA_AGENT_ID":"agent-fixture","ANTONINA_INVOCATION_ID":"turn"}):
            oldcwd=Path.cwd()
            try:
                os.chdir(p)
                self.assertEqual(adoption.current_role(),"general")
                adoption.record("start",__import__("time").time(),0)
                adoption.record("knowledge find",__import__("time").time(),0)
            finally:os.chdir(oldcwd)
        result=adoption.report()
        self.assertEqual(result["roles"]["general"]["discovered"],1)
        self.assertEqual(result["roles"]["general"]["successful_use"],1)
    def test_expired_packet_and_workspace_attribution(self):
        rec=state.create("L-meta-8",state="LEASED",lease="fixture",statement="True",
                         lease_expires_at=__import__("time").time()+600)
        p=Path(assignment.prepare(rec["gap_id"],checkout=False,worker="general")["cwd"])
        p.mkdir(parents=True)
        with patch.object(playbook,"pinned_base",return_value=self.base):
            data=playbook.packet("general",p)
            self.assertTrue(data["assignment_current"])
            state.transition(rec["gap_id"],"RELEASED",failure_reason="fixture")
            data=playbook.packet("general",p)
            self.assertFalse(data["assignment_current"])
            self.assertNotIn("pnp-research obligations ready --current",data["next_commands"])
        did=adoption.planned("agent-fixture",p,"general","fixture")
        with __import__("contextlib").closing(adoption.db()) as c:
            self.assertIsNotNone(adoption.lookup(c,"agent-fixture",p,__import__("time").time()))
            self.assertIsNone(adoption.lookup(c,"agent-fixture",Path(config.STATE_ROOT),__import__("time").time()))
        with patch.dict(os.environ,{"ANTONINA_AGENT_ID":"agent-fixture"}):
            old=Path.cwd()
            try:
                os.chdir(p)
                adoption.record("start",__import__("time").time(),0)
            finally:os.chdir(old)
        report=adoption.report()
        self.assertNotIn("general",report["roles"])
        self.assertEqual(report["observed_usage"]["general"]["opened_packet"],1)
        self.assertEqual(report["observed_usage"]["general"]["unconfirmed_dispatches"],1)
    def test_operator_release_is_exact_and_explicit(self):
        from missions.pnp import cli
        from argparse import Namespace
        gap="L-meta-7"
        r=state.create(gap,state="LEASED",lease="fixture",statement="True",
                       lease_expires_at=__import__("time").time()+600)
        a=Namespace(gap=gap,reason="missing_lemma",operator_override=False,attempt=None,evidence=None)
        with patch.object(cli.desk_mod,"Desk") as desk:
            self.assertEqual(cli.cmd_release(a),2)
            desk.assert_not_called()
            a.operator_override=True;a.attempt="stale";a.evidence="concrete repair"
            self.assertEqual(cli.cmd_release(a),2)
            desk.assert_not_called()
            a.attempt=support.attempt(r)
            state.update(gap,queued_lease="fixture")
            self.assertEqual(cli.cmd_release(a),2)
            desk.assert_not_called()
            state.update(gap,queued_lease=None)
            self.assertEqual(cli.cmd_release(a),0)
            desk.return_value.release.assert_called_once_with("fixture","missing_lemma")
        self.assertEqual(state.load(gap)["state"],"RELEASED")
        events=[json.loads(l) for l in Path(state.events_path(gap)).read_text().splitlines()]
        self.assertTrue(any(e["kind"]=="operator_release" and e["detail"]["attempt"]==a.attempt for e in events))
    def test_independent_roles_and_obligation_fronts(self):
        rec=state.create("L-meta-9",state="LEASED",lease="fixture",statement="True",
                         lease_expires_at=__import__("time").time()+600)
        oid=k.add(self.c,"obligation","test","True",k.canon({"imports":["Mathlib"]}),
                  "L-meta-9 / prior attempt",base=self.base)
        self.assertIn("ob-"+oid,[x[0] for x in continuity.focus_plans(rec,[])])
        self.assertEqual(set(continuity.required_support([])),{"method","tool"})
        self.assertEqual(support.roles({"cwd":str(Path(config.STATE_ROOT)/"swarm/independent/method"),"title":"independent worker"}),["method"])
    def test_async_receipt_identity(self):
        oid=self.obligation("True")
        body=k.store_bytes(b"by trivial")
        source=o.build(self.c,oid,"by trivial")
        k.store_bytes(source.encode())
        job=async_check.identity(self.base,"toolchain","a"*24+"-"+"b"*16,source)
        ident={x:job[x] for x in ("job","base","toolchain","attempt","source_sha256")}
        ident["origin"]={"gap":None,"attempt":"method-research"}
        async_check.table(self.c)
        with self.c:self.c.execute("INSERT INTO pending_check VALUES(?,?,?,?,?,?,NULL,0,'queued',NULL)",
             (job["job"],oid,self.base,body,job["source_sha256"],k.canon(ident)))
        row=async_check.snapshot(self.c,job["job"])
        result={**job,"status":"elaborated","exit_code":0,
                "diagnostic":"'"+o.symbol(oid)+"' does not depend on any axioms"}
        self.assertEqual(async_check.proof_result(self.c,row,result)["status"],"kernel_checked")
        bad={**result,"base":"b"*40}
        self.assertEqual(async_check.proof_result(self.c,row,bad)["status"],"not_verified")
        self.assertEqual(o.checked_body(self.c,oid,self.base),"by trivial")
    def test_large_certificate(self):
        edges=[(p,13+l) for p in range(13) for l in range(13) if (p-l)%13 in (0,1,3,9)]
        meta=certificate.graph_meta({"n":26,"edges":edges,"bound":64})
        r=certificate.render(meta)
        self.assertEqual(r["status"],"generated")
        self.assertEqual(r["gates"],64)
        self.assertIn("L.Perm R := by decide",r["candidate"])
        self.assertNotIn("∀ b0 b1",r["candidate"])
        # No generated proof is claimed kernel-checked before verification.
        self.assertEqual(r["verification"]["status"],"verified")
    def test_reflected_artifact_assembly(self):
        from missions.pnp.research import dnf_reflection as d
        meta=certificate.graph_meta({"n":20,"edges":[(u,v) for u in range(10) for v in range(10,20)],"bound":109})
        r=certificate.render(meta)
        self.assertEqual(r["proof_strategy"],"reflection")
        self.assertIn("lemma sound",r["candidate"])
        self.assertIn("foldl dstep",r["candidate"])
        body=certificate.obligation_body(meta,r["certificate"])
        self.assertTrue(body.startswith(d.MARKER))
        a=self.obligation(meta["statement"])
        src=o.build(self.c,a,body)
        self.assertIn("namespace viche_r_"+a,src)
        self.assertIn("#print axioms "+o.symbol(a),src)
        self.assertNotIn(d.MARKER,src)
        bad=json.loads(body[len(d.MARKER):]);bad["output"]=0
        with self.assertRaises(ValueError):o.build(self.c,a,d.artifact(bad))
        self.fixture_receipt(a,body)
        b=self.obligation("True",[a])
        self.fixture_receipt(b,"by trivial")
        rec={"gap_id":"L-meta-1","module":"PEqualNP.Outside.L_meta_1","path":"lean/PEqualNP/Outside/L_meta_1.lean","statement":"True","imports":["Mathlib"]}
        result=o.candidate(self.c,b,rec,self.base)
        self.assertIn("namespace viche_r_"+a,result)
        self.assertEqual(result.count("theorem "),1)
        self.assertNotIn("#print",result)
    def test_archive_ingest(self):
        archive=Path(config.STATE_ROOT).parent/"quarantine"/"L-meta-2-20261124100000"
        archive.mkdir(parents=True)
        (archive/"state.json").write_text(json.dumps({"gap_id":"L-meta-2","statement":"Petersen circuit","state":"RELEASED"}))
        e={"at":"2026-11-24T09:00:00Z","kind":"acquired","detail":{}}
        f={"at":"2026-11-24T09:05:00Z","kind":"research_finding","detail":{"id":"f","attempt":"a","worker":"general","message":"reuse lemma","evidence":"note"}}
        end={"at":"2026-11-24T09:20:00Z","kind":"state","detail":{"to":"RELEASED"}}
        (archive/"events.jsonl").write_text("\n".join(json.dumps(x) for x in (e,f,end))+"\n")
        k.ingest(self.c);k.ingest(self.c)
        self.assertEqual(len(k.search(self.c,"reuse lemma")),1)
        history=y.observations();self.assertEqual(len(history),1)
        self.assertEqual(history[0]["outcome"],"released")
        self.assertGreater(y.estimate(history,"petersen")["loss_hazard_per_hour"],0)
if __name__=="__main__":unittest.main()

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
    def test_axioms(self):
        a=self.obligation("True");name=o.symbol(a)
        self.assertTrue(o.verify_output(f"'{name}' depends on axioms: [propext, Classical.choice, Quot.sound]",a))
        self.assertTrue(o.verify_output(f"'{name}' does not depend on any axioms",a))
        self.assertFalse(o.verify_output(f"'{name}' depends on axioms: [sorryAx]",a))
        self.assertFalse(o.verify_output("",a))
        with self.assertRaises(ValueError):o.clean_body("by sorry")
    def test_candidate(self):
        a=self.obligation("True")
        with tempfile.NamedTemporaryFile(mode="w") as f:
            f.write("by trivial");f.flush();h=k.store_artifact(f.name)
        with self.c:self.c.execute("INSERT INTO proof VALUES(?,?,?,?,?,?)",(a,self.base,h,"fixture",k.canon({"status":"kernel_checked"}),1))
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
            self.assertEqual(adoption.current_role(),"general")
            adoption.record("start",__import__("time").time(),0)
            adoption.record("knowledge find",__import__("time").time(),0)
        result=adoption.report()
        self.assertEqual(result["roles"]["general"]["discovered"],1)
        self.assertEqual(result["roles"]["general"]["successful_use"],1)
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
        job=async_check.identity(self.base,"toolchain","a"*24+"-"+"b"*16,"source")
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

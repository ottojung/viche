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
from missions.pnp.research import knowledge as k,obligations as o,star,yield_model as y

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

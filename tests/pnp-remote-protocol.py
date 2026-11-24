#!/usr/bin/env python3
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from missions.pnp import config
from missions.pnp.remote import protocol as p
from missions.pnp.remote.spool import Spool

GAP = {"id":"L-meta-1", "file":"lean/PEqualNP/Meta/T.lean",
       "module":"PEqualNP.Meta.T","statement":"True","imports":[]}
SOURCE = b"import Mathlib\n\ntheorem PEqualNP.Meta.T : True := by trivial\n"
ATTEMPT = "a"*24+"-"+"b"*16

def job():
    return p.make(GAP,SOURCE,"c"*40,config.LEAN_TOOLCHAIN,ATTEMPT)

def rehash(obj):
    obj["job"]=p.digest(p.canonical({k:v for k,v in obj.items() if k!="job"}))
    return p.canonical(obj)

class Tests(unittest.TestCase):
    def test_determinism_and_binding(self):
        j=job()
        self.assertEqual(j,job())
        self.assertEqual(p.request(p.canonical(j))[1],SOURCE)
        with self.assertRaises(ValueError):
            p.request(p.canonical(j),{"attempt":"other"})
        for key,value in [("base","HEAD"),("wall_seconds",0),("rss_mib",999999),
                          ("mode","shell"),("attempt","secret"),("toolchain","nightly"),
                          ("source_sha256","f"*64)]:
            bad=dict(j,**{key:value})
            with self.assertRaises(ValueError):
                p.request(rehash(bad))
        bad=copy.deepcopy(j);bad["gap"]["file"]="../../bad.lean"
        with self.assertRaises(ValueError):
            p.request(rehash(bad))
        with self.assertRaises(ValueError):
            p.request(b'{"a":1,"a":2}')
    def test_result_binding(self):
        j=job()
        r=p.make_result(j,"elaborated",10,5000,exit_code=0)
        self.assertEqual(p.result(p.canonical(r),j),r)
        with self.assertRaises(ValueError):
            p.result(p.canonical(dict(r,source_sha256="e"*64)),j)
        with self.assertRaises(ValueError):
            p.make_result(j,"elaborated",10,None,exit_code=1)
    def test_spool_admission_cache_cancellation(self):
        with tempfile.TemporaryDirectory() as d:
            s=Spool(Path(d)/"private");j=job();ident=s.submit(p.canonical(j))
            called=[]
            def runner(req,source,cancelled):
                called.append(req["job"])
                self.assertEqual(source,SOURCE)
                return p.make_result(req,"elaborated",5,5000,exit_code=0)
            self.assertEqual(s.run_one(ident,runner,lambda:0),"deferred")
            self.assertEqual(s.run_one(ident,runner,lambda:16*1024**3),"elaborated")
            self.assertEqual(s.submit(p.canonical(j)),ident)
            self.assertEqual(s.run_one(ident,runner,lambda:16*1024**3),"cached")
            self.assertEqual(len(called),1)
            self.assertEqual(s.poll(ident)["status"],"elaborated")
            s.cancel(ident)
            self.assertEqual(s.run_one(ident,runner,lambda:0),"obsolete")
            self.assertEqual(s.poll(ident)["status"],"obsolete")
    def test_retryable_and_private(self):
        with tempfile.TemporaryDirectory() as d:
            s=Spool(Path(d)/"private");j=job();ident=s.submit(p.canonical(j))
            def runner(req,source,cancelled):
                return p.make_result(req,"resource",50,1000,exit_code=137)
            for i in range(2):
                self.assertEqual(s.run_one(ident,runner,lambda:16*1024**3),"resource")
            (Path(d)/"private").chmod(0o755)
            with self.assertRaises(ValueError):
                Spool(Path(d)/"private")
if __name__=="__main__":
    unittest.main()

"""Proof-of readiness requires checked exact bytes; memory admission uses clean cache."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp import config, desk
from missions.pnp.lbcert import ready
from missions.relay import compile_admission

class TestReady(unittest.TestCase):
    def test_exact_receipt_and_targeted_offer(self):
        with tempfile.TemporaryDirectory() as d, patch.object(config,"STATE_ROOT",d), patch.object(config,"GAPS_DIR",d+"/gaps"):
            gid="L-meta-123"
            root=ready.directory();root.mkdir(parents=True)
            p=root/(gid+".lean");p.write_bytes(b"candidate")
            r={"status":"ok","compiled":True,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"checked_base":"a"*40}
            self.assertFalse(ready.record(gid,{**r,"compiled":False},p.read_bytes()))
            self.assertTrue(ready.record(gid,r,p.read_bytes()))
            self.assertEqual(ready.offers({"complete":True,"gaps":{gid:{}}},{},time.time()),[gid])
            p.write_bytes(b"changed")
            self.assertIsNone(ready.verified(gid))
    def test_memory_with_active_cache_and_tmpfs(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);M=1024*1024
            (root/"memory.max").write_text(str(30*1024*M))
            (root/"memory.current").write_text(str(29*1024*M))
            (root/"memory.stat").write_text(f"file {25*1024*M}\nshmem {2*1024*M}\nfile_dirty {1024*M}\ninactive_file 0\n")
            (root/"meminfo").write_text("MemAvailable: 30000000 kB\n")
            self.assertEqual(compile_admission.headroom(root,root/"meminfo"),23*1024)
    def test_targeted_wire_parameters(self):
        d=desk.Desk()
        with patch.object(d,"_call",return_value=(200,{"gap":None})) as call:
            self.assertIsNone(d._next_gap(another=True,proof_of="L-meta-123"))
            self.assertEqual(call.call_args.args[2]["gap"],"L-meta-123")
            self.assertEqual(call.call_args.args[2]["have"],"proof")

if __name__=="__main__":unittest.main()

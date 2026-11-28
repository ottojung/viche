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
            inv=ready.inventory({"complete":True,"gaps":{gid:{"points":37,"held":0,"parallel":2}}})
            self.assertEqual((inv["eligible_checked"],inv["advertised_points_known"]),(1,37))
            self.assertFalse(ready.inventory({})["available"])
            p.write_bytes(b"changed")
            self.assertIsNone(ready.verified(gid))
    def test_uncontested_first_but_contested_not_discarded(self):
        with tempfile.TemporaryDirectory() as d,patch.object(config,"STATE_ROOT",d),patch.object(config,"GAPS_DIR",d+"/gaps"):
            root=ready.directory();root.mkdir(parents=True)
            rows={}
            for gid,points in (("L-meta-123",100),("L-meta-124",20)):
                data=gid.encode()
                (root/(gid+".lean")).write_bytes(data)
                self.assertTrue(ready.record(gid,{"status":"ok","compiled":True,"sha256":hashlib.sha256(data).hexdigest(),"checked_base":"a"*40},data))
                rows[gid]={"points":points,"held":0,"parallel":2}
            cache=root.parent/"gaps-cache.json"
            cache.write_text(json.dumps({"gaps":[{"id":"L-meta-123","pr_open":2},{"id":"L-meta-124","pr_open":0}]}))
            Path(str(cache)+".meta").write_text(json.dumps({"at":time.time()}))
            snap={"complete":True,"gaps":rows}
            self.assertEqual(ready.offers(snap,{},time.time()),["L-meta-124","L-meta-123"])
            self.assertEqual(ready.offers(snap,{},time.time(),uncontested=True),["L-meta-124"])
            cache.with_name(cache.name+".meta").write_text(json.dumps({"at":time.time()-300}))
            self.assertEqual(ready.offers(snap,{},time.time(),uncontested=True),[])
            Path(str(cache)+".meta").write_text(json.dumps({"at":time.time()}))
            inv=ready.inventory(snap)
            self.assertEqual((inv["uncontested_checked"],inv["contested_checked"]),(1,1))
    def test_memory_with_active_cache_and_tmpfs(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);M=1024*1024
            (root/"memory.max").write_text(str(30*1024*M))
            (root/"memory.current").write_text(str(29*1024*M))
            (root/"memory.stat").write_text(f"file {25*1024*M}\nshmem {2*1024*M}\nfile_dirty {1024*M}\ninactive_file 0\n")
            (root/"meminfo").write_text("MemAvailable: 30000000 kB\n")
            self.assertEqual(compile_admission.headroom(root,root/"meminfo"),23*1024)
    def test_targeted_retry_does_not_block_unrelated_stock(self):
        with tempfile.TemporaryDirectory() as root, patch.object(config,"STATE_ROOT",root):
            desk.record_retry({"retry_after_s":1800},"L-meta-123")
            self.assertGreater(desk.retry_until("L-meta-123"),time.time()+1700)
            self.assertEqual(desk.retry_until("L-meta-124"),0)
            desk.record_retry({"retry_after_s":60})
            self.assertGreater(desk.retry_until("L-meta-124"),time.time()+50)
    def test_rate_limit_is_global_even_for_target(self):
        with tempfile.TemporaryDirectory() as root, patch.object(config,"STATE_ROOT",root):
            desk.record_retry({"retry_after_s":60,"note":"step rate limit"},"L-meta-123")
            self.assertGreater(desk.retry_until("L-meta-124"),time.time()+50)
            calls=[]
            def rate_limited(*a):
                calls.append(a)
                return 429,json.dumps({"retry_after_s":90})
            d=desk.Desk(request=rate_limited,min_interval=0)
            # A recorded cooldown must prevent a new request even if it
            # was entered between allocation and the paced wire operation.
            with self.assertRaises(desk.DeskError):d._call("GET","/next",{})
            self.assertEqual(calls,[])
            # Expire only this synthetic fixture's prior retry, then
            # independently verify global recording of the next HTTP 429.
            with patch.object(desk.time,"time",return_value=time.time()+61):
                with self.assertRaises(desk.DeskError):d._call("GET","/next",{})
                self.assertEqual(len(calls),1)
                self.assertGreater(desk.retry_until(),time.time()+80)
    def test_ledger_respects_dynamic_state_root(self):
        from missions.pnp import ledger
        with tempfile.TemporaryDirectory() as root, patch.object(config,"STATE_ROOT",root):
            ledger.mark("fixture","L-meta-123")
            self.assertTrue(Path(root,"ledger.jsonl").is_file())
    def test_capacity_retained_until_observed_update(self):
        with tempfile.TemporaryDirectory() as root, patch.object(config,"STATE_ROOT",root):
            Path(root,"desk-capacity.json").write_text(json.dumps({"capacity":3,"at":0}))
            self.assertEqual(desk.lease_limit(),3)
            desk.record_capacity({"capacity":4,"holding":2})
            self.assertEqual(desk.lease_limit(),4)
    def test_level_wire_parameters(self):
        d=desk.Desk()
        with patch.object(d,"_call",return_value=(200,{"gap":None})) as call:
            self.assertIsNone(d._next_gap(another=True,level="solid"))
            self.assertEqual(call.call_args.args[2]["level"],"solid")
            self.assertEqual(call.call_args.args[2]["model"],"unknown")
            with self.assertRaises(desk.DeskError):d._next_gap(level="invalid")

    def test_kind_wire_parameters(self):
        d=desk.Desk()
        with patch.object(d,"_call",return_value=(200,{"gap":None})) as call:
            self.assertIsNone(d._next_gap(level="solid",kind="prove"))
            self.assertEqual(call.call_args.args[2]["kind"],"prove")
            with self.assertRaises(desk.DeskError): d._next_gap(kind="invalid")
            with self.assertRaises(desk.DeskError): d._next_gap(kind="prove",proof_of="L-meta-123")

    def test_targeted_wire_parameters(self):
        d=desk.Desk()
        with patch.object(d,"_call",return_value=(200,{"gap":None})) as call:
            self.assertIsNone(d._next_gap(another=True,proof_of="L-meta-123"))
            self.assertEqual(call.call_args.args[2]["gap"],"L-meta-123")
            self.assertEqual(call.call_args.args[2]["have"],"proof")

if __name__=="__main__":unittest.main()

"""Offline regression for shared status observations and accurate cooldowns."""
import contextlib
import fcntl
import io
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
import urllib.error
from unittest.mock import patch
from missions.pnp import config, desk, frontier
from missions.pnp.lbcert import live

class Tests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        stack=contextlib.ExitStack();self.addCleanup(stack.close)
        stack.enter_context(patch.object(config,"STATE_ROOT",str(self.root)))
        stack.enter_context(patch.object(live,"STATUS_CACHE",str(self.root/"status.json")))
        stack.enter_context(patch.object(live,"CACHE",str(self.root/"live.json")))
        self.pace=stack.enter_context(patch.object(desk,"pace"))
        self.net=stack.enter_context(patch.object(live.urllib.request,"urlopen"))
        self.raw={"open_gaps":1,"gaps":[{"id":"L-meta-1","held":0,"parallel":1}]}
    def cache(self,age):
        p=Path(live.STATUS_CACHE);p.write_text(json.dumps(self.raw))
        at=time.time()-age;os.utime(p,(at,at));return at
    def test_reuse_preserves_age(self):
        at=self.cache(5)
        d,seen=live.status_doc(with_time=True)
        self.assertAlmostEqual(seen,at,places=3);self.assertEqual(d,self.raw)
        s=frontier.refresh();self.assertAlmostEqual(s["observed"],at,places=3)
        snap=live.snapshot();self.assertAlmostEqual(snap["at"],at,places=3)
        self.net.assert_not_called();self.pace.assert_not_called()
    def test_out_of_order_status_cannot_overwrite_newer_frontier(self):
        at=self.cache(5)
        fresh=frontier.normalize(self.raw,at+2)
        Path(frontier.cache_path()).write_text(json.dumps(fresh))
        self.assertAlmostEqual(frontier.refresh()["observed"],at+2,places=3)
        self.assertAlmostEqual(frontier.load()["observed"],at+2,places=3)
    def test_status_cooldown_rechecked_after_pacing(self):
        self.pace.side_effect=lambda *a:desk.record_status_retry({"retry_after_s":100})
        with self.assertRaises(OSError):live.status_doc()
        self.net.assert_not_called()
    def test_contention_does_not_request_or_rejuvenate(self):
        at=self.cache(40)
        with open(live.STATUS_CACHE+".lock","a") as lk:
            fcntl.flock(lk,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaises(OSError):frontier.refresh()
            self.assertEqual(frontier.load(),{})
        self.net.assert_not_called()
        self.assertAlmostEqual(Path(live.STATUS_CACHE).stat().st_mtime,at,places=3)
    def test_429_status_header_and_cooldown(self):
        e=urllib.error.HTTPError(live.URL,429,"limited",{"Retry-After":"180"},io.BytesIO(b'{"retry_after_s":60}'))
        self.net.side_effect=e
        with self.assertRaises(urllib.error.HTTPError):live.status_doc()
        self.assertGreater(desk.status_retry_until(),time.time()+170)
        self.assertEqual(desk.retry_until(),0)
        with self.assertRaises(OSError):live.status_doc()
        self.assertEqual(self.net.call_count,1)
    def test_next_rechecks_after_pacing(self):
        d=desk.Desk(request=lambda *a: self.fail("network forbidden"),min_interval=0)
        d.shared_pace=True
        self.pace.side_effect=lambda *a:desk.record_retry({"retry_after_s":100})
        with self.assertRaises(desk.DeskError):d._call("GET","/next",{})
    def test_retry_parser(self):
        self.assertEqual(desk.retry_response('{"retry_after_s":-2}')["retry_after_s"],60)
        self.assertEqual(desk.retry_response('{"retry_after_s":500}',{"Retry-After":"30"})["retry_after_s"],500)
        self.assertEqual(desk.retry_response('not json',{"Retry-After":"90000"})["retry_after_s"],90000)
    def test_429_next_records_endpoint(self):
        d=desk.Desk(request=lambda *a:(429,'{"retry_after_s":120}'),min_interval=0)
        with self.assertRaisesRegex(desk.DeskError,"/next"):d._call("GET","/next",{})
        self.assertGreater(desk.retry_until(),time.time()+100)
        row=json.loads((self.root/"ledger.jsonl").read_text().splitlines()[-1])
        self.assertEqual(row["endpoint"],"/next");self.assertEqual(row["retry_after_s"],120)
        self.assertNotIn("lease",row)

if __name__=="__main__":unittest.main()

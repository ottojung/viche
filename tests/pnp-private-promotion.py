"""No live desk or production state; exact gated receipt promotion regression."""
import contextlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp import config, fastlane, ledger, promotion_observer
from missions.pnp.lbcert import prelease as p, promotion as m, ready
from missions.pnp.lbcert.generators.promise import gen

GID="L-meta-24806"
BASE="a"*40
MOD="PEqualNP.Outside.L_meta_24806"
S=("∃ C : PEqualNP.CircuitLowerBounds.Circuit, PEqualNP.MetaComplexity.FanInTwo C ∧ C.size ≤ 9 ∧ "
   "∀ i j : Fin 6, C.eval (List.ofFn fun k : Fin 6 => decide (k = i ∨ k = j)) = "
   "(2 : ℕ).testBit (6 * min i.val j.val + max i.val j.val)")
Q={"id":GID,"module":MOD,"file":"lean/PEqualNP/Outside/L_meta_24806.lean","statement":S,
   "imports":["PEqualNP.Defs"],"offerable_now":True,"held_now":False,"pr_open":0}
RAW=gen.emit(GID,S,gen.parse(S),([("and",[0,1])],6)).encode()
DIGEST=p.sha(RAW)
CFG={"base":BASE,"authorization":"checker-test"}
FLAG={"base":BASE,"checker_authorization":"checker-test","authorization":"promotion-test","enabled":True}
LOG="'"+MOD+"' depends on axioms: [propext, Quot.sound]"

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name);self.private=root/"private";self.private.mkdir(mode=0o700)
        self.prod=root/"prod";self.prod.mkdir()
        self.town=root/"town";(self.town/Path(m.DECISION).parent).mkdir(parents=True)
        (self.town/m.DECISION).touch()
        (self.private/"worktree").mkdir()
        self.stack=contextlib.ExitStack();self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.multiple(p,PRIVATE=self.private,PRODUCTION=self.prod,TOWN=self.town))
        self.stack.enter_context(patch.object(config,"STATE_ROOT",str(self.prod)))
        self.stack.enter_context(patch.object(p,"deployment",return_value=True))
        self.stack.enter_context(patch.object(p,"public_base"))
        self.stack.enter_context(patch.object(p,"git",return_value=BASE))
        self.stack.enter_context(patch.object(m.cli,"held_records",return_value=[]))
        self.stack.enter_context(patch.object(m.desk,"lease_limit",return_value=4))
        self.stack.enter_context(patch.object(m.desk,"retry_until",return_value=0))
        self.stack.enter_context(patch.object(m.frontier,"load",side_effect=lambda now:{"complete":True,"observed":now,"gaps":{GID:{"held":0,"parallel":1}}}))
        self.stack.enter_context(patch.object(p,"metadata",return_value=dict(Q)))
        self.stack.enter_context(patch.object(m,"observations",return_value={GID:0}))
        self.stack.enter_context(patch.object(m.state,"load",return_value=None))
        self.stack.enter_context(patch.object(m.cli,"acquisition_lock",side_effect=contextlib.nullcontext))
        self.stack.enter_context(patch.object(m.desk,"http_request",side_effect=AssertionError("network forbidden")))
        self.write(self.private/"enable.json",CFG)
        self.write(self.private/"workspace.json",{"base":BASE,"toolchain":config.LEAN_TOOLCHAIN})
        self.receipt={"status":"ok","compiled":True,"sha256":DIGEST,"checked_base":BASE,
            "gap":GID,"module":MOD,"statement_sha256":p.sha(S.encode()),
            "guarded_sha256":p.sha(p.audited(Q,RAW)),"toolchain":config.LEAN_TOOLCHAIN,
            "axiom_report":LOG,"compiler_log":LOG+"\n","compiler_log_sha256":p.sha((LOG+"\n").encode()),
            "authorization":CFG["authorization"],"at":time.time()-600}
        self.folder=self.private/"receipts"/BASE
        self.folder.parent.mkdir(mode=0o700);self.folder.mkdir(mode=0o700)
        self.path=self.folder/(GID+"-"+DIGEST)
        self.path.with_suffix(".lean").write_bytes(RAW);self.path.with_suffix(".lean").chmod(0o600)
        self.write(self.path.with_suffix(".json"),self.receipt)
    def write(self,path,data):
        path.write_text(json.dumps(data));path.chmod(0o600)
    def enable(self):
        self.write(self.private/"promote.json",FLAG)
    def admit(self):
        self.enable()
        return m.admit(GID,DIGEST,(CFG,FLAG))
    def assertNotPromoted(self):
        self.assertFalse(ready.marker(GID).exists())
    def test_disabled_and_wrong_authorization(self):
        self.assertEqual(m.promote_once(),[])
        self.assertEqual(list(self.prod.iterdir()),[])
        self.write(self.private/"promote.json",{**FLAG,"checker_authorization":"wrong"})
        self.assertIsNone(m.enabled())
        self.assertNotPromoted()
    def test_private_stage_and_original_check_time(self):
        self.assertEqual(self.admit()["status"],"promoted")
        marker=ready.verified(GID)
        self.assertEqual(marker["at"],self.receipt["at"])
        self.assertEqual(marker["origin"],"private-prelease")
        self.assertEqual(Path(fastlane.cand_ready(GID)).read_bytes(),RAW)
        self.assertEqual(self.path.with_suffix(".lean").read_bytes(),RAW)
        self.assertEqual(m.pending((CFG,FLAG)),[])
    def test_legacy_receipt_does_not_block_new_local_receipt(self):
        ready.directory().mkdir(parents=True)
        src=ready.directory()/(GID+".lean");src.write_bytes(RAW)
        legacy=ready.directory()/(GID+".checked.json");legacy.write_text("historical evidence")
        self.assertIsNone(ready.verified(GID))
        self.assertEqual(self.admit()["status"],"promoted")
        self.assertEqual(legacy.read_text(),"historical evidence")
        self.assertEqual(ready.verified(GID)["origin"],"private-prelease")

    def test_different_existing_source_untouched(self):
        ready.directory().mkdir(parents=True)
        src=ready.directory()/(GID+".lean");src.write_bytes(b"other")
        self.assertNotEqual(self.admit()["status"],"promoted")
        self.assertEqual(src.read_bytes(),b"other");self.assertNotPromoted()
    def test_inexact_receipt(self):
        for key,value in (("sha256","0"*64),("guarded_sha256","0"*64),
                          ("statement_sha256","0"*64),("checked_base","b"*40),("authorization","other")):
            with self.subTest(key=key):
                self.write(self.path.with_suffix(".json"),{**self.receipt,key:value})
                self.assertNotEqual(self.admit()["status"],"promoted")
                self.assertNotPromoted()
    def test_bad_axiom_log_not_hidden(self):
        log=LOG+"\n"+LOG+"\n"
        self.write(self.path.with_suffix(".json"),{**self.receipt,"compiler_log":log,
                   "compiler_log_sha256":p.sha(log.encode())})
        self.assertEqual(self.admit()["status"],"rejected");self.assertNotPromoted()
    def test_stop_and_permissions(self):
        self.enable();(self.prod/"lbcert").mkdir();(self.prod/"lbcert/STOP").touch()
        self.assertIsNone(m.enabled())
        (self.prod/"lbcert/STOP").unlink();(self.private/"promote.json").chmod(0o644)
        self.assertIsNone(m.enabled())
    def test_unknown_or_contested(self):
        for counts in ({},{GID:1}):
            with patch.object(m,"observations",return_value=counts):
                self.assertEqual(self.admit()["status"],"deferred")
                self.assertNotPromoted()
    def test_catalog_offerable_not_just_unheld(self):
        with patch.object(p,"metadata",return_value={**Q,"offerable_now":False}):
            self.assertEqual(self.admit()["status"],"deferred")
            self.assertNotPromoted()
    def test_backoff_and_capacity(self):
        with patch.object(m.desk,"retry_until",return_value=time.time()+100):
            self.assertEqual(self.admit()["status"],"deferred")
            self.assertEqual(m.promote_once(),[])
        with patch.object(m.cli,"held_records",return_value=[{}]*4):
            self.assertEqual(self.admit()["status"],"deferred")
        self.assertNotPromoted()
    def test_symlink_receipt_refused(self):
        src=self.path.with_suffix(".lean");src.unlink()
        outside=src.parent/"other";outside.write_bytes(RAW)
        src.symlink_to(outside)
        self.assertNotEqual(self.admit()["status"],"promoted")
        self.assertNotPromoted()
    def test_observer_disabled_no_network(self):
        with patch.object(promotion_observer.competition,"observe") as net:
            promotion_observer.observe();net.assert_not_called()
    def test_observer_no_claim(self):
        self.enable()
        with patch.object(promotion_observer.competition,"observe",return_value={GID:0}) as net:
            promotion_observer.observe()
            net.assert_called_once_with([GID])
        self.assertNotPromoted()
        self.assertEqual(json.loads(m.observation_path().read_text())["counts"],{GID:0})

if __name__=="__main__":unittest.main()

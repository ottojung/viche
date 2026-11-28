"""Offline controls for the disabled private pre-lease verifier."""
import contextlib
import json
import os
from pathlib import Path
import subprocess
import sqlite3
import time
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp import config, compile as compiler, build_control
from missions.pnp.lbcert import prelease as p
from missions.pnp.lbcert.generators.promise import gen

BASE="a"*40
CFG={"base":BASE,"authorization":"executive-test-only"}
GID="L-meta-24806"
MOD="PEqualNP.Outside.L_meta_24806"
S=("∃ C : PEqualNP.CircuitLowerBounds.Circuit, PEqualNP.MetaComplexity.FanInTwo C ∧ C.size ≤ 9 ∧ "
   "∀ i j : Fin 6, C.eval (List.ofFn fun k : Fin 6 => decide (k = i ∨ k = j)) = "
   "(2 : ℕ).testBit (6 * min i.val j.val + max i.val j.val)")
Q={"id":GID,"module":MOD,"file":"lean/PEqualNP/Outside/L_meta_24806.lean","statement":S,"imports":["PEqualNP.Defs"]}
RAW=gen.emit(GID,S,gen.parse(S),([("and",[0,1])],6)).encode()

class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.private=self.root/"private"; self.private.mkdir(mode=0o700)
        self.prod=self.root/"production"; self.prod.mkdir()
        self.lean=self.private/"worktree/lean";self.lean.mkdir(parents=True)
        self.stack=contextlib.ExitStack();self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.multiple(p,PRIVATE=self.private,PRODUCTION=self.prod))
        self.stack.enter_context(patch.object(p,"deployment",return_value=True))
        self.candidate=self.root/"source.lean";self.candidate.write_bytes(RAW)
    def write(self,name,doc):
        f=self.private/name;f.write_text(json.dumps(doc));f.chmod(0o600)
    def enable(self):
        self.write("enable.json",CFG)
        self.write("workspace.json",{"base":BASE,"toolchain":config.LEAN_TOOLCHAIN})
    def test_disabled_no_effects(self):
        with patch.object(p.subprocess,"run") as run:
            self.assertEqual(p.check(GID,self.candidate),{"status":"disabled"})
            self.assertEqual(p.initialize(),"disabled")
            run.assert_not_called()
        self.assertEqual(list(self.prod.iterdir()),[])
        self.assertFalse((self.private/"checker.lock").exists())
    def test_stop_and_wrong_pin(self):
        self.enable(); self.assertEqual(p.enablement(),CFG)
        (self.prod/"lbcert").mkdir();(self.prod/"lbcert/STOP").touch()
        self.assertIsNone(p.enablement())
        (self.prod/"lbcert/STOP").unlink()
        self.write("workspace.json",{"base":"b"*40,"toolchain":config.LEAN_TOOLCHAIN})
        self.assertIsNone(p.enablement())
    def test_insecure_flag(self):
        self.enable();(self.private/"enable.json").chmod(0o644)
        self.assertIsNone(p.enablement())
    def test_exact_emitter_only(self):
        guarded=p.audited(Q,RAW)
        self.assertTrue(guarded.startswith(RAW))
        self.assertIn(b"#print axioms",guarded[len(RAW):])
        with self.assertRaises(ValueError):p.audited(Q,RAW+b"\n")
        with self.assertRaises(ValueError):p.audited(Q,RAW.replace(b".and",b".or"))
    def test_receipt_private_not_production(self):
        self.enable()
        def compiled(args,lean,cfg,job,budget):
            self.assertEqual(lean,self.lean)
            self.assertEqual((cfg,job["sha256"],budget),(CFG,p.sha(RAW),p.CHECK_BUDGET))
            self.assertEqual((lean/job["file"]).read_bytes(),p.audited(Q,RAW))
            return 0,"'"+MOD+"' depends on axioms: [propext, Quot.sound]\n"
        with patch.object(p,"build_ready",return_value=True),patch.object(p,"metadata",return_value=Q),patch.object(p,"workspace",return_value=self.lean),patch.object(p,"managed",side_effect=compiled):
            r=p.check(GID,self.candidate)
        self.assertEqual(r["status"],"ok")
        self.assertTrue(p.ready.exact_receipt(r,RAW))
        self.assertEqual(list(self.prod.iterdir()),[])
        out=self.private/"receipts"/BASE/(GID+"-"+p.sha(RAW))
        self.assertEqual(out.with_suffix(".lean").read_bytes(),RAW)
        self.assertEqual(json.loads(out.with_suffix(".json").read_text()),r)
        self.assertEqual(list(self.lean.iterdir()),[])
    def test_failed_report_or_cancel_never_receipted(self):
        self.enable()
        with patch.object(p,"build_ready",return_value=True),patch.object(p,"metadata",return_value=Q),patch.object(p,"workspace",return_value=self.lean):
            for rc,log in [(0,"ok"),(0,"'"+MOD+"' depends on axioms: [sorryAx]"),(75,"timeout")]:
                with patch.object(p,"managed",return_value=(rc,log)):
                    self.assertNotEqual(p.check(GID,self.candidate)["status"],"ok")
        self.assertFalse((self.private/"receipts").exists())
        self.assertEqual(list(self.lean.iterdir()),[])
    def test_network_namespace_and_exact_job(self):
        self.enable()
        self.write("job.json",{**CFG,"kind":"build","host_net":"net:[fixture]"})
        with patch.object(p,"workspace",return_value=self.lean),patch.object(os,"readlink",return_value="net:[fixture]"):
            with self.assertRaises(ValueError):p.compiler_context(["lake","build","+PEqualNP.Defs"],self.lean)
        with patch.object(p,"workspace",return_value=self.lean),patch.object(os,"readlink",return_value="net:[other]"):
            self.assertEqual(p.compiler_context(["lake","build","+PEqualNP.Defs"],self.lean),(CFG,p.BUILD_BUDGET))
            with self.assertRaises(ValueError):p.compiler_context(["lean","other.lean"],self.lean)
    def test_namespace_wrapper_bounded_and_cleans_job(self):
        self.enable()
        def run(cmd,**kw):
            self.assertEqual(cmd[:10],["/run/current-system/profile/bin/unshare","--user","--map-root-user","--net","--pid","--mount","--mount-proc","--fork","--kill-child=SIGKILL","--"])
            self.assertEqual(cmd[10:],["python3","-m","missions.pnp.compile","--prelease","--","lake","build","+PEqualNP.Defs"])
            self.assertEqual(kw["timeout"],p.BUILD_BUDGET+40)
            self.assertEqual(kw["env"]["PYTHONPATH"],p.host_boundary.PYTHONPATH)
            raise subprocess.TimeoutExpired(cmd,kw["timeout"])
        with patch.object(p.subprocess,"run",side_effect=run):
            self.assertEqual(p.managed(["lake","build","+PEqualNP.Defs"],self.lean,CFG,{"kind":"build"},p.BUILD_BUDGET)[0],75)
        self.assertFalse((self.private/"job.json").exists())
    def test_read_only_staged_intake(self):
        self.enable();now=time.time()
        lb=self.prod/"lbcert";lb.mkdir()
        (lb/"gaps-cache.json").write_text(json.dumps({"gaps":[{**Q,"pr_open":0,"offerable_now":True,"held_now":False}]}))
        (lb/"gaps-cache.json.meta").write_text(json.dumps({"at":now}))
        db=lb/"promise-batch.sqlite"
        with contextlib.closing(sqlite3.connect(db)) as c:
            c.execute("CREATE TABLE attempt(gap,source,observed,status)")
            c.execute("INSERT INTO attempt VALUES(?,?,?,?)",(GID,RAW.decode(),now,"staged"))
            c.commit()
        initial={str(f.relative_to(self.prod)):f.read_bytes() for f in self.prod.rglob("*") if f.is_file()}
        snap={"complete":True,"gaps":{GID:{"held":0,"parallel":1,"points":50}}}
        with patch.object(p.frontier,"load",return_value=snap),patch.object(p.freshness,"recent",return_value={GID:now}),patch.object(p.state,"load",return_value=None),patch.object(p.ready,"verified",return_value=None):
            result=p.staged_candidates(CFG,now)
            self.assertEqual([(gid,raw) for _,gid,raw in result],[(GID,RAW)])
            for overrides in ({"offerable_now":False},{"held_now":True},{"offerable_now":None},{"pr_open":False}):
                original=(lb/"gaps-cache.json").read_text()
                (lb/"gaps-cache.json").write_text(json.dumps({"gaps":[{**Q,"pr_open":0,"offerable_now":True,"held_now":False,**overrides}]}))
                self.assertEqual(p.staged_candidates(CFG,now),[])
                (lb/"gaps-cache.json").write_text(original)
            snap["gaps"][GID]["held"]=1
            self.assertEqual(p.staged_candidates(CFG,now),[])
        self.assertEqual({str(f.relative_to(self.prod)):f.read_bytes() for f in self.prod.rglob("*") if f.is_file()},initial)
    def test_symlinked_receipt_directory_refused(self):
        self.enable()
        (self.private/"receipts").symlink_to(self.prod,target_is_directory=True)
        with patch.object(p,"build_ready",return_value=True),patch.object(p,"metadata",return_value=Q),patch.object(p,"workspace",return_value=self.lean),patch.object(p,"managed",return_value=(0,"'"+MOD+"' does not depend on any axioms")):
            with self.assertRaises(ValueError):p.check(GID,self.candidate)
        self.assertEqual(list(self.prod.iterdir()),[])
    def test_compiler_disabled_does_not_spawn(self):
        with patch.object(compiler,"run") as run,patch.object(compiler.assignment,"workspace") as workspace:
            with self.assertRaises(SystemExit):
                compiler.main(["--prelease","--","lake","build","+PEqualNP.Defs"])
            run.assert_not_called();workspace.assert_not_called()
    def test_compiler_deadline_before_spawn(self):
        self.enable()
        @contextlib.contextmanager
        def slot(**kw):
            yield ()
        with patch.object(build_control,"slot",slot),patch.object(compiler.subprocess,"Popen") as spawn:
            with self.assertRaises(build_control.BuildDeferred):
                compiler.run(["lake","build","+PEqualNP.Defs"],prelease=(CFG,0))
            spawn.assert_not_called()

    def test_compiler_cancellation_reaps_child_group(self):
        self.enable()
        @contextlib.contextmanager
        def slot(**kw):
            self.assertFalse(kw["publication"]);self.assertTrue(kw["heavy"])
            yield ()
        with patch.object(build_control,"slot",slot),patch.object(build_control,"headroom",return_value=10**10),patch.object(build_control,"oom_count",return_value=0),patch.object(p,"enablement",side_effect=[CFG,None]),patch.object(compiler.subprocess,"Popen") as spawn,patch.object(os,"killpg") as kill:
            proc=spawn.return_value;proc.pid=321
            with self.assertRaises(build_control.BuildDeferred):
                compiler.run(["lake","build","+PEqualNP.Defs"],prelease=(CFG,120))
            kill.assert_called_once_with(321,compiler.signal.SIGKILL)
            proc.wait.assert_called_once_with()

if __name__=="__main__":unittest.main()

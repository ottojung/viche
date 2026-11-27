"""Exercise a real scheduling tick with all lower-bound slots occupied."""
import json
import os
import sys
import tempfile
import time
import types
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

class Fairness(unittest.TestCase):
    def test_transient_retry_only_after_backoff(self):
        from missions.pnp.lbcert import autosolve as a
        with tempfile.TemporaryDirectory() as d, patch.object(a, "CANDS", d):
            gid="L-meta-42"
            self.assertTrue(a.retryable(gid))
            path=Path(d)/(gid+".status")
            for st in ("relay_error", "error", "deferred"):
                path.write_text(st+" test")
                self.assertFalse(a.retryable(gid))
                t=time.time()-a.RETRY_DELAY-1
                os.utime(path,(t,t))
                self.assertTrue(a.retryable(gid))
            for st in ("false", "unsupported", "toobig", "ok", "generated", "failed"):
                path.write_text(st+" test")
                os.utime(path,(t,t))
                self.assertFalse(a.retryable(gid))

    def test_unavailable_plugin_check_preserves_candidate(self):
        from missions.pnp.lbcert import autosolve as a
        from missions.pnp import state, support, validate, fastlane
        import plugins
        from missions.pnp.lbcert import checklocal
        g=dict(id="L-meta-42",statement="True",module="M",file="M.lean",imports=[])
        def generate(name,gid,sf,out):
            Path(out).write_text("candidate")
            return 0,""
        with tempfile.TemporaryDirectory() as d, patch.object(a,"CANDS",d), \
             patch.object(plugins,"run",side_effect=generate), \
             patch.object(validate,"validate"), patch.object(state,"load",return_value=None), \
             patch.object(support,"active",return_value=False), \
             patch.object(checklocal,"check",side_effect=AssertionError("unbound check forbidden")), \
             patch.object(fastlane,"submit_ready"):
            a.gen_plugin(g,"test","123")
            self.assertEqual((Path(d)/"L-meta-42.lean").read_text(),"candidate")
            self.assertTrue(a.status(g["id"]).startswith("generated plugin"))
            self.assertFalse(a.fresh(g["id"],"123"))

    def test_staging_preserves_existing_bytes(self):
        from missions.pnp.lbcert import autosolve as a
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);old=p/"proof.lean";new=p/"alternate.lean"
            old.write_text("original");new.write_text("replacement")
            self.assertFalse(a.stage_bytes(str(new),str(old)))
            self.assertEqual(old.read_text(),"original")
            self.assertEqual(new.read_text(),"replacement")
            new.write_text("original")
            self.assertTrue(a.stage_bytes(str(new),str(old)))
            self.assertFalse(new.exists())

    def test_independent_lanes(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ,{"PNP_STATE_ROOT":d}):
            from missions.pnp.lbcert import autosolve as a
            from missions.pnp import cli, fastlane
            from missions.pnp.lbcert import ready
            import plugins
            import live
            live.open_ids=lambda: None    # offline: no live desk frontier
            work=Path(d)/"lbcert";cands=work/"cands";cands.mkdir(parents=True,exist_ok=True)
            gaps=[dict(id="L-meta-"+str(i),statement="lower",module="M") for i in range(1,9)]
            gaps+= [dict(id="L-meta-100",statement="constructive",module="M"),
                     dict(id="L-meta-101",statement="prepared",module="M")]
            (cands/"L-meta-101.lean").write_text("dummy")
            pools=[]
            class Pool:
                def __init__(self,n):
                    self.limit=n;self.jobs=[];pools.append(self)
                def submit(self,fn,*args):
                    self.jobs.append((fn.__name__,args[0]["id"]))
                    f=Mock();f.done.return_value=False
                    return f
                def shutdown(self,**kwargs):pass
            def stop(_): (work/"STOP").touch()
            with patch.multiple(a, WORK=str(work), CANDS=str(cands), QUEUED=set(),
                               ThreadPoolExecutor=Pool), \
                 patch.object(a,"ensure_engines",return_value=[]), \
                 patch.object(a.threading,"Thread"), \
                 patch.object(a,"source_changed",return_value=False), \
                 patch.object(a,"get",return_value=json.dumps({"gaps":gaps}).encode()), \
                 patch.object(a.lbparse,"family",side_effect=lambda s:"lb" if s=="lower" else None), \
                 patch.object(a,"status",side_effect=lambda g:"generated test" if g=="L-meta-101" else None), \
                 patch.object(cli,"held_records",return_value=[]), \
                 patch.object(ready,"verified",return_value=None), \
                 patch.object(plugins,"discover",return_value={"x":1}), \
                 patch.object(plugins,"family_of",side_effect=lambda s,_:("x","v1") if s=="constructive" else None), \
                 patch.object(a.time,"sleep",side_effect=stop), \
                 patch.object(a.managed_process,"stop_all"):
                self.assertEqual(a.main(),0)
            self.assertEqual([p.limit for p in pools],[1,2])
            self.assertEqual(len(pools[0].jobs),1)
            self.assertEqual(pools[1].jobs,[("gen_plugin","L-meta-100")])


    def test_generation_timeout_frees_worker_with_retryable_status(self):
        from missions.pnp.lbcert import autosolve as a
        from missions.pnp import state, support, ledger
        import subprocess
        g = dict(id="L-meta-43", statement="HasCircuitSize 3 (fun x : Fin 3 => True) 4",
                 module="M", file="M.lean", imports=[])
        def hang(*args, **kwargs):
            raise subprocess.TimeoutExpired(args[0] if args else "lbremote", a.GEN_TIMEOUT)
        with tempfile.TemporaryDirectory() as d, patch.object(a, "CANDS", d), \
             patch.object(a, "WORK", d), \
             patch.object(a.managed_process, "run", side_effect=hang), \
             patch.object(state, "load", return_value=None), \
             patch.object(support, "active", return_value=False), \
             patch.object(ledger, "mark") as mark:
            a.generate(g, ["engine.lean"])
            path = Path(d) / "L-meta-43.status"
            self.assertTrue(path.read_text().startswith("deferred generation timeout"))
            self.assertIn(str(a.GEN_TIMEOUT), path.read_text())
            mark.assert_called_once()
            old = time.time() - a.RETRY_DELAY - 1
            os.utime(path, (old, old))
            self.assertTrue(a.retryable("L-meta-43"))

    def test_sibling_index_does_not_start_remote_adaptation(self):
        from missions.pnp.lbcert import autosolve as a
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            work, cands = root / "work", root / "work" / "cands"
            gaps = root / "state" / "gaps"
            gid = "L-meta-44"
            (gaps / gid).mkdir(parents=True)
            (gaps / gid / "state.json").write_text(json.dumps(
                {"state": "LEASED", "statement": "s", "module": "M", "imports": []}))
            cands.mkdir(parents=True)
            calls = []
            def fake_run(cmd, **kwargs):
                calls.append(cmd)
                raise AssertionError("sibling indexing must not launch a transport")
            fake_sibling = types.SimpleNamespace(index=lambda *args: ("head1", {}))
            with patch.dict(sys.modules, {"sibling": fake_sibling}), \
                 patch.object(a, "STATE", str(root / "state")), \
                 patch.object(a, "WORK", str(work)), \
                 patch.object(a, "CANDS", str(cands)), \
                 patch.object(a.managed_process, "run", side_effect=fake_run), \
                 patch.object(a, "write_status"):
                 a.sibling_pass()
                 self.assertEqual(calls, [])

if __name__=="__main__":unittest.main()

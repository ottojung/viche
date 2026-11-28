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
    def test_runtime_fingerprint_tracks_helper_and_data_not_docs(self):
        from missions.pnp.lbcert import autosolve as a
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"gen.py").write_text("x=1")
            h=a.runtime_hash(root)
            (root/"README.md").write_text("docs")
            self.assertEqual(a.runtime_hash(root),h)
            (root/"helper.py").write_text("x=2")
            h2=a.runtime_hash(root);self.assertNotEqual(h,h2)
            (root/"helper.py").write_text("x=3")
            self.assertNotEqual(a.runtime_hash(root),h2)
            (root/"witnesses.json").write_text("{}")
            self.assertNotEqual(a.runtime_hash(root),h2)
            h3=a.runtime_hash(root)
            (root/"template.lean").write_text("def a := 1")
            self.assertNotEqual(a.runtime_hash(root),h3)
            with patch.object(a,"START_HASH",h),patch.object(a,"runtime_hash",return_value=h2):
                self.assertTrue(a.source_changed())

    def test_reload_drains_mutations_before_releasing_owner(self):
        from missions.pnp.lbcert import autosolve as a
        order=[]
        class Pool:
            def shutdown(self,**kw):
                self.kw=kw
                order.append("drain")
        pools=[Pool(),Pool(),Pool()]
        with patch.object(a.managed_process,"stop_all",side_effect=lambda:order.append("stop")):
            a.drain_workers(pools)
        self.assertEqual(order,["stop","drain","drain","drain"])
        self.assertTrue(all(p.kw=={"wait":True,"cancel_futures":True} for p in pools))

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
        def generate(name,gid,sf,out,timeout=None):
            Path(out).write_text("candidate")
            return 0,""
        from missions.pnp import ledger
        with tempfile.TemporaryDirectory() as d, patch.object(a,"CANDS",d), \
             patch.object(plugins,"run",side_effect=generate), \
             patch.object(validate,"validate"), patch.object(state,"load",return_value=None), \
             patch.object(support,"active",return_value=False), \
             patch.object(checklocal,"check",return_value=(2,{"status":"bound_workspace_required"})), \
             patch.object(fastlane,"submit_ready"), \
             patch.object(ledger,"mark"):
            a.gen_plugin(g,"test","123")
            self.assertEqual((Path(d)/"L-meta-42.lean").read_text(),"candidate")
            self.assertTrue(a.status(g["id"]).startswith("generated plugin"))
            self.assertFalse(a.fresh(g["id"],"123"))

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
                     dict(id="L-meta-101",statement="prepared",module="M"),
                     dict(id="L-meta-102",statement="mono",module="M")]
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
                 patch.object(a.lbparse,"family",side_effect=lambda s:{"lower":"lb","mono":"mono"}.get(s)), \
                 patch.object(a,"status",side_effect=lambda g:{"L-meta-101":"generated test","L-meta-102":"unsupported old-assembler"}.get(g)), \
                 patch.object(cli,"held_records",return_value=[]), \
                 patch.object(ready,"verified",return_value=None), \
                 patch.object(plugins,"discover",return_value={"x":1}), \
                 patch.object(plugins,"family_of",side_effect=lambda s,_:("x","v1") if s in ("constructive","mono") else None), \
                 patch.object(a.time,"sleep",side_effect=stop), \
                 patch.object(a.managed_process,"stop_all"):
                self.assertEqual(a.main(),0)
            self.assertEqual([p.limit for p in pools],[1,2,1])
            self.assertEqual(len(pools[0].jobs),1)
            self.assertEqual(pools[1].jobs,[("gen_plugin","L-meta-102"),("gen_plugin","L-meta-100")])
            self.assertEqual(pools[2].jobs,[("check_prepared","L-meta-101")])

    def test_real_registry_recognizes_the_orphaned_families(self):
        from missions.pnp.lbcert import plugins, lbparse
        n=6
        body="Nat.testBit (4278124266 * 2 ^ 32 + 4277075624) (∑ i : Fin 6, if x i then 2 ^ (i : ℕ) else 0)"
        s=("∀ s : ℕ, PEqualNP.MetaComplexity.HasCircuitSize 6 (fun x : Fin 6 → Bool => "+body+
           ") s → ∃ C : PEqualNP.CircuitLowerBounds.Circuit, PEqualNP.MetaComplexity.Monotone2 C ∧ C.size ≤ s ∧ "
           "∀ x : Fin 6 → Bool, C.eval (List.ofFn x) = "+body)
        found=plugins.discover()
        self.assertIn("monosix",[name for name,_ in plugins.families_of(s,found)])
        self.assertIn("monosix",[name for name,_ in plugins.families_of("("+s+")",found)])
        lb="¬PEqualNP.MetaComplexity.HasCircuitSize 6 (fun x : Fin 6 → Bool => "+body+") 3"
        self.assertIn("zz_lbcert",[name for name,_ in plugins.families_of(lb,found)])
        self.assertEqual(lbparse.table_literal(n,body),0xfefefeeafeeefea8)
        self.assertEqual(lbparse.truth_table(n,"fun x : Fin 6 → Bool => "+body)[0],0xfefefeeafeeefea8)
        self.assertIsNone(lbparse.table_literal(10000,body))
        self.assertIsNone(lbparse.table_literal(n,body.replace("2 ^ 32","2 ^ 99999999")))
        self.assertIsNone(lbparse.table_literal(n,body.replace("4277075624","4294967296")))
        self.assertIsNone(lbparse.table_literal(n,body.replace("4278124266","4294967296")))

    def test_constructive_witnesses_are_independently_truth_table_audited(self):
        import random
        from missions.pnp.lbcert.onenot import monotone_witness
        rng=random.Random(3)
        masks=[0xfefefeeafeeefea8,0xfefefee8feeefea0,0x8000000000000000]
        for _ in range(12):
            terms=rng.sample(range(1,64),rng.randint(3,8))
            masks.append(sum(int(any(row&t==t for t in terms))<<row for row in range(64)))
        for t in masks:
            f=[(t>>r)&1 for r in range(64)]
            w=monotone_witness.synthesize(6,f)
            self.assertIsNotNone(w,hex(t))
            for row in range(64):
                values=[(row>>i)&1 for i in range(6)]
                for a,b,tt in w:
                    self.assertLess(max(a,b),len(values))
                    values.append(tt[2*values[a]+values[b]])
                self.assertEqual(values[-1],f[row],(hex(t),row))
        self.assertEqual(len(monotone_witness.synthesize(6,[int(r==63) for r in range(64)])),5)
        self.assertIsNone(monotone_witness.synthesize(6,[int(r==0) for r in range(64)]))

    def test_six_input_emitter_static_validation_not_kernel_receipt(self):
        from missions.pnp.lbcert import plugins
        from missions.pnp import validate
        import importlib
        found=plugins.discover()
        mod=importlib.import_module("monosix")
        from missions.pnp.lbcert.onenot import monotone_witness
        gid="L-meta-999999"
        name="PEqualNP.Outside.L_meta_999999"
        body="Nat.testBit (2147483648 * 2 ^ 32 + 0) (∑ i : Fin 6, if x i then 2 ^ (i : ℕ) else 0)"
        st=("∀ s : ℕ, PEqualNP.MetaComplexity.HasCircuitSize 6 (fun x : Fin 6 → Bool => "+body+
           ") s → ∃ C : PEqualNP.CircuitLowerBounds.Circuit, PEqualNP.MetaComplexity.Monotone2 C ∧ C.size ≤ s ∧ "
           "∀ x : Fin 6 → Bool, C.eval (List.ofFn x) = "+body)
        f=[int(r==63) for r in range(64)]
        w=monotone_witness.synthesize(6,f)
        template=Path(found["monosix"][0]).with_name("template.lean")
        with patch.object(mod,"TEMPLATE",str(template)):
            out=mod.lean(gid,st,6,body,f,mod.onenot.critical_pairs(6,f),len(w),w)
        self.assertEqual(len(validate.validate(dict(id=gid,module=name,statement=st,
           file="lean/PEqualNP/Outside/L_meta_999999.lean",imports=["PEqualNP.Defs"]),out.encode())),64)

    def test_route_fingerprint_changes_when_fallback_changes(self):
        from missions.pnp.lbcert import plugins
        a={"first":("a","v1",lambda _:True),"second":("b","v2",lambda _:True)}
        b={**a,"second":("b","v3",lambda _:True)}
        self.assertEqual(plugins.family_of("test",a)[0],"first")
        self.assertNotEqual(plugins.family_of("test",a)[1],plugins.family_of("test",b)[1])

    def test_wider_monotone_beam_improves_historical_witness(self):
        from missions.pnp.lbcert.onenot import monotone_witness
        mask=0xfeeaece8fee0ecc0
        f=[(mask>>r)&1 for r in range(64)]
        self.assertEqual(len(monotone_witness.synthesize(6,f,3)),11)
        self.assertEqual(len(monotone_witness.synthesize(6,f,8)),10)
        self.assertIsNone(monotone_witness.synthesize(6,f,16,budget=0))

    def test_screen_binary_is_cached_by_source_and_compiler_identity(self):
        from missions.pnp.lbcert.onenot import screen_binary as screen
        import tempfile,sys
        from unittest.mock import patch
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            source=root/"source.c"
            source.write_text("first")
            builds=[]
            def build(argv, **kwargs):
                builds.append(argv)
                Path(argv[argv.index("-o")+1]).write_bytes(b"screen")
            with patch.object(screen.shutil,"which",return_value=sys.executable), \
                 patch.object(screen.subprocess,"run",side_effect=build):
                first=screen.cached_screen(source,root=root/"cache")
                self.assertIsNotNone(first)
                self.assertEqual(first,screen.cached_screen(source,root=root/"cache"))
                self.assertEqual(len(builds),1)
                source.write_text("second")
                second=screen.cached_screen(source,root=root/"cache")
                self.assertNotEqual(first,second)
                self.assertEqual(len(builds),2)
                Path(second).chmod(0o777)
                self.assertEqual(second,screen.cached_screen(source,root=root/"cache"))
                self.assertEqual(len(builds),3)
                link=root/"link"
                link.symlink_to(root/"cache",target_is_directory=True)
                self.assertIsNone(screen.cached_screen(source,root=link))

    def test_screen_binary_failed_build_is_not_cached(self):
        from missions.pnp.lbcert.onenot import screen_binary as screen
        import tempfile,sys,subprocess
        from unittest.mock import patch
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            source=root/"source.c";source.write_text("test")
            with patch.object(screen.shutil,"which",return_value=sys.executable), \
                 patch.object(screen.subprocess,"run",side_effect=subprocess.TimeoutExpired("cc",1)):
                self.assertIsNone(screen.cached_screen(source,root=root/"cache"))
                self.assertEqual(list((root/"cache").glob("*.bin")),[])
                self.assertIsNone(screen.cached_screen(source,budget=0,root=root/"cache"))

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

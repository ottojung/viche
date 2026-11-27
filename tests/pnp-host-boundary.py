#!/usr/bin/env python3
"""Focused fail-closed regression tests for the PnP host boundary."""
import ast
import atexit
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_isolated_state = tempfile.mkdtemp(prefix="pnp-host-boundary-")
os.environ["PNP_STATE_ROOT"] = _isolated_state
atexit.register(__import__("shutil").rmtree, _isolated_state, ignore_errors=True)


class HostBoundary(unittest.TestCase):
    def deny_process(self, *args, **kwargs):
        raise AssertionError("a process/network transport was spawned")

    def test_legacy_relay_clients_fail_closed_without_subprocesses(self):
        from missions.pnp.lbcert import lbremote, sibremote, checkremote
        from missions.pnp import host_boundary
        for fn in (lbremote.main, sibremote.main, checkremote.main):
            out = io.StringIO()
            with patch("subprocess.run", self.deny_process), \
                 patch("subprocess.Popen", self.deny_process), \
                 patch("subprocess.check_output", self.deny_process), \
                 patch("sys.stdout", out):
                self.assertEqual(fn(), host_boundary.EXIT)
            self.assertEqual(json.loads(out.getvalue())["status"], host_boundary.STATUS)
        code, result = checkremote.check("unused.lean", "M")
        self.assertEqual(code, host_boundary.EXIT)
        self.assertEqual(result["status"], host_boundary.STATUS)

    def test_earlycheck_never_starts_remote_worker(self):
        from missions.pnp import earlycheck
        rec = {"gap_id":"L-meta-99", "state":"SIGNED", "local_check_status":"pending",
               "base_sha":"a"*40,"candidate_digest":"b"*64,"commit_sha":"c"*40,"lease":"lease"}
        with patch("subprocess.Popen", self.deny_process):
            self.assertFalse(earlycheck.start(rec, b"candidate"))

    def test_async_lane_refuses_submission_and_preserves_pending_receipt(self):
        from missions.pnp.research import async_check
        from missions.pnp.research import knowledge as k
        from missions.pnp import config
        with tempfile.TemporaryDirectory() as td:
            with patch.object(config, "STATE_ROOT", td):
                db = k.db()
                self.addCleanup(db.close)
                async_check.table(db)
                db.execute("PRAGMA foreign_keys=OFF")
                with patch("subprocess.run", self.deny_process), \
                     patch("subprocess.check_output", self.deny_process):
                    with self.assertRaisesRegex(ValueError, "transport disabled"):
                        async_check.submit(db, "node", "body")
                    db.execute("INSERT INTO pending_check VALUES(?,?,?,?,?,?,?,?,?,?)",
                               ("check", "node", "a"*40, "body", "d"*64, "{}", "legacy-id", 1,
                                "queued", None))
                    db.commit()
                    self.assertEqual(async_check.collect(db, "check")["status"], "transport_disabled")
                    report = async_check.reconcile(db)
                    self.assertEqual(report["pending"], 1)
                    self.assertEqual(tuple(db.execute("SELECT state,request FROM pending_check").fetchone()),
                                     ("queued", "legacy-id"))

    def test_autosolve_uses_local_generator_not_relay_and_preserves_generated_status(self):
        from missions.pnp.lbcert import autosolve as auto
        from missions.pnp import state, support, ledger, fastlane
        with tempfile.TemporaryDirectory() as td:
            gid = "L-meta-314"
            g = {"id":gid,"statement":"True","module":"M"}
            def generator(argv, **kwargs):
                self.assertIn("lbassemble.py", argv)
                self.assertNotIn("lbremote.py", argv)
                Path(argv[5]).write_text("generated candidate")
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            with patch.object(auto, "CANDS", td), patch.object(auto, "WORK", td), \
                 patch.object(auto.managed_process, "run", side_effect=generator), \
                 patch.object(state, "load", return_value=None), patch.object(support, "active", return_value=False), \
                patch.object(ledger, "mark"), patch.object(fastlane, "submit_ready"):
                auto.generate(g, ["engine.lean"])
                self.assertEqual((Path(td)/(gid+".lean")).read_text(), "generated candidate")
                self.assertTrue(auto.status(gid).startswith("generated"))

    def test_stop_short_circuits_before_starting_any_worker(self):
        from missions.pnp.lbcert import autosolve as auto
        with tempfile.TemporaryDirectory() as td:
            stop = Path(td)/"STOP"
            stop.touch()
            with patch.object(auto, "WORK", td), patch.object(auto, "ensure_engines",
                    side_effect=AssertionError("STOP must prevent initialization")), \
                 patch.object(auto.threading, "Thread", side_effect=AssertionError("STOP must prevent workers")):
                self.assertEqual(auto.main(), 0)

    def test_permitted_local_check_uses_exact_bound_managed_compiler(self):
        from missions.pnp.lbcert import checklocal
        from missions.pnp import assignment, state, support, focus, host_boundary
        with tempfile.TemporaryDirectory() as td:
            work = Path(td); (work/"lean").mkdir(); (work/"lean"/"lean-toolchain").write_text("toolchain\n")
            rec = {"gap_id":"L-meta-314","lease":"lease","base_sha":"a"*40,"state":"RESEARCHING",
                   "module":"PEqualNP.Outside.L_meta_314","path":"lean/PEqualNP/Outside/L_meta_314.lean",
                   "statement":"True","imports":["PEqualNP.Defs"]}
            def run(argv, **kwargs):
                self.assertTrue(host_boundary.is_managed_compile(argv))
                self.assertEqual(kwargs["env"]["PYTHONPATH"], host_boundary.PYTHONPATH)
                self.assertEqual(Path(kwargs["cwd"]).resolve(), (work/"lean").resolve())
                guarded=(work/"lean"/argv[-1]).read_text()
                self.assertIn("Lean.collectAxioms",guarded)
                return SimpleNamespace(returncode=0, stdout="'PEqualNP.Outside.L_meta_314' does not depend on any axioms", stderr="")
            with patch.object(assignment, "binding", return_value=(rec["gap_id"],"lease")), \
                 patch.object(assignment, "workspace", return_value=(rec["gap_id"],work,Path(td)/"binding.json")), \
                 patch.object(state, "load", return_value=rec), patch.object(support, "active", return_value=True), \
                 patch.object(focus, "eligible", return_value=True), \
                 patch("subprocess.check_output", return_value="a"*40), \
                 patch("subprocess.run", side_effect=run) as spawned:
                candidate=work/"candidate.lean"; candidate.write_text("import PEqualNP.Defs\ntheorem PEqualNP.Outside.L_meta_314 : True := by trivial\n")
                code,result=checklocal.check(str(candidate),rec["module"])
                self.assertEqual(code,0)
                spawned.reset_mock()
                spawned.side_effect=None
                spawned.return_value=SimpleNamespace(returncode=0,stdout="'PEqualNP.Outside.L_meta_314' depends on axioms: [sorryAx]",stderr="")
                bad,receipt=checklocal.check(str(candidate),rec["module"])
                self.assertNotEqual(bad,0)
                self.assertFalse(receipt["compiled"])
                candidate.write_text("import PEqualNP.Defs\ntheorem PEqualNP.Outside.L_meta_314 : True := by admit\n")
                self.assertNotEqual(checklocal.check(str(candidate),rec["module"])[0],0)
            self.assertEqual(code,0)
            self.assertTrue(result["compiled"])
            self.assertEqual(result["checked_base"],"a"*40)
            spawned.assert_called_once()

    def test_executable_tree_has_no_relay_spawn_or_ci_disablement(self):
        sources=list((ROOT/"missions/pnp").rglob("*.py"))
        prohibited=("~/.local/bin/marceline-request", "~/.local/bin/pnp-remote-check")
        for path in sources:
            text=path.read_text(errors="replace")
            for phrase in prohibited:
                self.assertNotIn(phrase, text, str(path))
            tree=ast.parse(text, filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if node.func.attr in ("run", "Popen", "check_output", "call"):
                        rendered=ast.get_source_segment(text,node) or ""
                        self.assertNotRegex(rendered, r"marceline-request|pnp-remote-check|sibremote\.py|lbremote\.py")
        docs=(ROOT/"missions/pnp/README.md").read_text()
        self.assertIn("GitHub-hosted", docs)
        self.assertIn("missions.pnp.compile", docs)
        relay=(ROOT/"missions/relay/marceline-request").read_text()
        self.assertNotIn("exec ", relay)
        self.assertIn("exit 9", relay)


if __name__ == "__main__":
    unittest.main()

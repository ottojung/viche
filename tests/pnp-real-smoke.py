#!/usr/bin/env python3
"""Real local integration smoke: CLI process, lease decoding, GPG Git, PR URLs.

No network mutation. Never opens a real pull request or claims a real desk task.
"""
import os
import pathlib
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
TMP = tempfile.TemporaryDirectory(prefix="pnp-real-smoke-")
os.environ["PNP_STATE_ROOT"] = str(pathlib.Path(TMP.name) / "state")

from missions.pnp import cli, config, github, state, gitctl, jobs, build_control  # noqa: E402


class FullPathSmoke(unittest.TestCase):
    def test_documented_cli_is_executable(self):
        result = subprocess.run([sys.executable,
                                 str(ROOT / "missions/pnp/cli.py"), "--help"],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("submit", result.stdout)

    def test_generated_branch_accepted(self):
        for gap in ("L-meta-1393", "L-gct-086", "L-meta-582"):
            b = config.branch_for(gap)
            self.assertTrue(config.BRANCH_RE.fullmatch(b), b)
            self.assertEqual(subprocess.run(["git", "check-ref-format",
                                             "--branch", b],
                                            capture_output=True).returncode, 0)

    def test_desk_lease_object_decoded(self):
        gap = "L-meta-93285"
        fake = SimpleNamespace(
            docs=lambda refresh=False: "current",
            next_gap=lambda hard=False, another=False: {
                "gap": {"id": gap, "statement": "True",
                        "module": "PEqualNP.Outside.L_meta_93285",
                        "file": "lean/PEqualNP/Outside/L_meta_93285.lean",
                        "imports": []},
                "lease": {"id": "lease-sample", "expires_at": "future"}
            })
        with patch.object(cli.desk_mod, "Desk", return_value=fake):
            self.assertEqual(cli.cmd_acquire(SimpleNamespace(
                hard=False, another=False)), 0)
        self.assertEqual(state.load(gap)["lease"], "lease-sample")

    def test_pr_create_url_and_target(self):
        calls = []
        def fake_gh(*args):
            calls.append(args)
            return "https://github.com/brilliant-hq/pequalnp-proofs/pull/10023\n"
        with patch.object(github, "gh", fake_gh):
            self.assertEqual(github.create_pr("pnp/l_meta_582", "L-meta-582"),
                             10023)
        self.assertEqual(calls[0][2:4], ("--repo", config.UPSTREAM))
        self.assertIn("ottojung:pnp/l_meta_582", calls[0])

    def test_publisher_lock_survives_parent_and_recovers_after_exit(self):
        gap = "L-meta-93286"
        state.create(gap, state="LEASED", lease="test-lease")
        fd = jobs.claim(gap)
        self.assertIsNotNone(fd)
        p = subprocess.Popen([sys.executable, "-c",
                              "import sys; sys.stdin.read()"],
                             pass_fds=(fd,), stdin=subprocess.PIPE)
        os.close(fd)
        try:
            self.assertIsNone(jobs.claim(gap))
        finally:
            p.kill()
            p.wait(timeout=5)
            p.stdin.close()
        again = jobs.claim(gap)
        self.assertIsNotNone(again)
        os.close(again)

    def test_dependency_cache_does_not_inherit_checker_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            seed = root / "seed/lean/.lake"
            seed.mkdir(parents=True)
            (seed / "packages").mkdir()
            (seed / "check.lock").mkdir()
            work = root / "work/lean"
            work.mkdir(parents=True)
            for name in ("lean-toolchain", "lake-manifest.json"):
                (seed.parent / name).write_text("pinned")
                (work / name).write_text("pinned")
            with patch.dict(os.environ, {"PNP_SHARED_LAKE": str(seed)}):
                gitctl.prepare_build_cache(str(work.parent))
            self.assertFalse((work / ".lake").is_symlink())
            self.assertTrue((work / ".lake/packages").is_symlink())
            self.assertFalse((work / ".lake/check.lock").exists())

    def test_publication_slot_and_confirmed_obsolescence(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(config, "CACHE_DIR", tmp), patch.object(build_control, "headroom", return_value=16 * build_control.GIB), patch.object(build_control, "legacy_compilers", return_value=[]):
                self.assertFalse(build_control.busy())
                with build_control.slot(timeout=0):
                    self.assertTrue(build_control.busy())
                    with self.assertRaises(build_control.BuildDeferred):
                        with build_control.slot(timeout=0):
                            self.fail("duplicate full publication build")
                self.assertFalse(build_control.busy())
        with patch.object(state, "load", return_value={"state": "STALE", "lease": "old"}):
            self.assertTrue(build_control.obsolete("L-meta-1", "old"))
        with patch.object(state, "load", side_effect=OSError("temporarily unavailable")):
            self.assertFalse(build_control.obsolete("L-meta-1", "old"))
        with patch.object(state, "load", return_value={"state": "LEASED", "lease": "new"}):
            self.assertTrue(build_control.obsolete("L-meta-1", "old"))

    def test_memory_reserve_and_process_group_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "memory.max").write_text(str(14 * build_control.GIB))
            (root / "memory.current").write_text(str(13 * build_control.GIB))
            (root / "memory.stat").write_text("inactive_file 1073741824\n")
            (root / "meminfo").write_text("MemAvailable: 12582912 kB\n")
            self.assertEqual(build_control.headroom(root, root / "meminfo"), 2 * build_control.GIB)
            (root / "memory.max").write_text("max")
            self.assertIsNone(build_control.headroom(root))
        with patch.object(build_control, "headroom", return_value=build_control.GIB):
            self.assertIn("reserve", build_control.memory_reason(1))
        with patch.object(build_control, "headroom", return_value=None), patch.object(
                build_control, "group_rss", return_value=7 * build_control.GIB):
            self.assertIsNone(build_control.memory_reason(1))
            self.assertIn("light", build_control.memory_reason(1, heavy=False))
        with patch.object(build_control, "headroom", return_value=None), patch.object(
                build_control, "group_rss", return_value=0):
            self.assertIsNone(build_control.memory_reason(1))

    def test_clean_cache_budget_and_physical_cap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            gib = build_control.GIB
            (root / "memory.max").write_text(str(14 * gib))
            (root / "memory.current").write_text(str(14 * gib))
            (root / "memory.stat").write_text(
                "file %d\nshmem %d\nfile_dirty %d\nfile_writeback %d\nslab_reclaimable %d\ninactive_file %d\n" %
                (10*gib, gib, gib, 0, 2*gib, gib))
            (root / "meminfo").write_text("MemAvailable: 12582912 kB\n")
            self.assertEqual(build_control.headroom(root, root / "meminfo"), 8*gib*9//10+gib)
            (root / "meminfo").write_text("MemAvailable: 4194304 kB\n")
            self.assertEqual(build_control.headroom(root, root / "meminfo"), 4*gib)

    def test_light_shared_heavy_exclusive(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(config, "CACHE_DIR", tmp), patch.object(build_control, "headroom", return_value=12 * build_control.GIB), patch.object(build_control, "legacy_compilers", return_value=[]):
            with build_control.slot(timeout=0, heavy=False, publication=False):
                with build_control.slot(timeout=0, heavy=False, publication=False):
                    with self.assertRaises(build_control.BuildDeferred):
                        with build_control.slot(timeout=0, heavy=False, publication=False):
                            self.fail("third light build exceeds reserved capacity")
                    with self.assertRaises(build_control.BuildDeferred):
                        with build_control.slot(timeout=0, heavy=True):
                            self.fail("heavy overlaps light")
            with build_control.slot(timeout=0, heavy=True):
                with self.assertRaises(build_control.BuildDeferred):
                    with build_control.slot(timeout=0, heavy=False, publication=False):
                        self.fail("light overlaps heavy")

    def test_waiting_publisher_has_admission_priority(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(config, "CACHE_DIR", tmp), patch.object(build_control, "headroom", return_value=12 * build_control.GIB), patch.object(build_control, "legacy_compilers", return_value=[]):
            entered = threading.Event()
            release = threading.Event()
            errors = []
            def publisher():
                try:
                    with build_control.slot(timeout=5):
                        entered.set()
                        release.wait(5)
                except Exception as exc:
                    errors.append(exc)
                    entered.set()
            with build_control.slot(timeout=0, heavy=True, publication=False):
                thread = threading.Thread(target=publisher)
                thread.start()
                try:
                    deadline = time.monotonic() + 3
                    while time.monotonic() < deadline:
                        fd = os.open(build_control.priority_path(), os.O_CREAT | os.O_RDWR, 0o600)
                        try:
                            import fcntl
                            if not build_control.try_lock(fd, fcntl.LOCK_EX):
                                break
                        finally:
                            os.close(fd)
                        time.sleep(0.025)
                    else:
                        self.fail("publisher never took priority gate")
                    self.assertFalse(entered.is_set())
                    with self.assertRaises(build_control.BuildDeferred):
                        with build_control.slot(timeout=0, heavy=False, publication=False):
                            self.fail("new light build overtook publisher")
                except BaseException:
                    release.set()
                    raise
            try:
                self.assertTrue(entered.wait(3))
                self.assertFalse(errors)
            finally:
                release.set()
                thread.join(5)

    def test_legacy_compiler_and_unknown_memory_defer_admission(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(config, "CACHE_DIR", tmp):
            with patch.object(build_control, "headroom", return_value=12 * build_control.GIB), patch.object(build_control, "legacy_compilers", return_value=[123]):
                with self.assertRaises(build_control.BuildDeferred):
                    with build_control.slot(timeout=0):
                        self.fail("legacy compiler overlaps managed build")
            with patch.object(build_control, "headroom", return_value=None), patch.object(build_control, "legacy_compilers", return_value=[]):
                with self.assertRaises(build_control.BuildDeferred):
                    with build_control.slot(timeout=0):
                        self.fail("unknown headroom allowed a heavy build")

    def test_supervisor_reaps_its_own_memory_deferred_child(self):
        from missions.pnp import compile as compiler
        children = []
        popen = subprocess.Popen
        def spawn(*args, **kwargs):
            proc = popen(*args, **kwargs)
            children.append(proc)
            return proc
        with tempfile.TemporaryDirectory() as tmp, patch.object(config, "CACHE_DIR", tmp), patch.object(build_control, "headroom", return_value=10 * build_control.GIB), patch.object(build_control, "legacy_compilers", return_value=[]), patch.object(build_control, "memory_reason", return_value="simulated pressure"), patch.object(compiler, "command", return_value=[sys.executable, "-c", "import time; time.sleep(30)"]), patch.object(compiler.subprocess, "Popen", side_effect=spawn):
            with self.assertRaises(build_control.MemoryDeferred):
                compiler.run(["lean", "scratch.lean"])
            self.assertEqual(len(children), 1)
            self.assertIsNotNone(children[0].poll())
            self.assertFalse(build_control.busy())

    def test_compiler_supervisor_success(self):
        from missions.pnp import compile as compiler
        with tempfile.TemporaryDirectory() as tmp, patch.object(config, "CACHE_DIR", tmp), patch.object(build_control, "headroom", return_value=10 * build_control.GIB), patch.object(build_control, "legacy_compilers", return_value=[]), patch.object(compiler, "command", return_value=[sys.executable, "-c", "pass"]):
            self.assertEqual(compiler.run(["lean", "scratch.lean"]), 0)
            self.assertFalse(build_control.busy())

    def test_compilation_has_no_elapsed_time_limit(self):
        from missions.pnp import compile as compiler
        from unittest.mock import MagicMock
        proc = MagicMock()
        proc.pid = 123456
        proc.wait.side_effect = [subprocess.TimeoutExpired("lean", 0.25)] * 2500 + [0]
        with tempfile.TemporaryDirectory() as tmp, patch.object(config, "CACHE_DIR", tmp), patch.object(build_control, "headroom", return_value=10 * build_control.GIB), patch.object(build_control, "legacy_compilers", return_value=[]), patch.object(build_control, "memory_reason", return_value=None), patch.object(compiler.subprocess, "Popen", return_value=proc):
            self.assertEqual(compiler.run(["lean", "scratch.lean"]), 0)
            self.assertEqual(proc.wait.call_count, 2501)
            self.assertTrue(all(call.kwargs == {"timeout": 0.25} for call in proc.wait.call_args_list))
            self.assertFalse(build_control.busy())

    def test_resource_blocked_waits_for_more_headroom(self):
        rec = {"publisher_memory_required": 10 * build_control.GIB}
        with patch.object(build_control, "headroom", return_value=9 * build_control.GIB):
            self.assertFalse(build_control.resource_ready(rec))
        with patch.object(build_control, "headroom", return_value=11 * build_control.GIB):
            self.assertTrue(build_control.resource_ready(rec))
        with patch.object(build_control, "headroom", return_value=None):
            self.assertFalse(build_control.resource_ready(rec))
        self.assertTrue(build_control.resource_ready({}))

    def test_reuse_requires_exact_publisher_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            def git(*args):
                return subprocess.run(["git", "-C", tmp, *args], check=True,
                                      capture_output=True, text=True).stdout.strip()
            git("init", "-q")
            pathlib.Path(tmp, "seed").write_text("base")
            git("add", "seed")
            git("-c", "user.name=Seed", "-c", "user.email=seed@example.org",
                "-c", "commit.gpgsign=false", "commit", "-qm", "base")
            base = git("rev-parse", "HEAD")
            path = "lean/PEqualNP/Outside/L_meta_582.lean"
            gitctl.pin_candidate(tmp, path, b"proof")
            self.assertTrue(gitctl.reusable_checked_tree(tmp, base, path, b"proof"))
            self.assertFalse(gitctl.reusable_checked_tree(tmp, base, path, b"other"))
            pathlib.Path(tmp, "seed").write_text("different dependency")
            self.assertFalse(gitctl.reusable_checked_tree(tmp, base, path, b"proof"))

    def test_real_signed_git_commit(self):
        # CI environments intentionally lack Otto Jung's private signing key.
        key = config.SIGNING_KEY.rstrip("!")
        r = subprocess.run(["gpg", "--batch", "--list-secret-keys", key],
                           capture_output=True, timeout=10)
        if r.returncode != 0:
            self.skipTest("Otto Jung signing key unavailable in this environment")
        work = pathlib.Path(TMP.name) / "signed"
        work.mkdir()
        def git(*args):
            r = subprocess.run(["git", "-C", str(work), *args],
                               capture_output=True, text=True, timeout=15)
            self.assertEqual(r.returncode, 0, r.stderr)
            return r.stdout.strip()
        git("init", "-q")
        (work / "seed").write_text("base\n")
        git("add", "seed")
        # Seed locally, without signing; the *new* contribution must be signed.
        git("-c", "user.name=Seed", "-c", "user.email=seed@example.org",
            "-c", "commit.gpgsign=false", "commit", "-qm", "seed")
        base = git("rev-parse", "HEAD")
        (work / "proof").write_text("proof\n")
        git("add", "proof")
        sha = gitctl.signed_commit(str(work), base, "L-meta-582")
        self.assertEqual(sha, git("rev-parse", "HEAD"))
        self.assertTrue(gitctl.all_new_commits_signed(str(work), base))
        self.assertEqual(git("log", "-1", "--format=%ae"), config.AUTHOR_EMAIL)


    def test_real_rejected_pr_correction_commit(self):
        key = config.SIGNING_KEY.rstrip("!")
        r = subprocess.run(["gpg", "--batch", "--list-secret-keys", key],
                           capture_output=True, timeout=10)
        if r.returncode != 0:
            self.skipTest("Otto Jung signing key unavailable")
        work = pathlib.Path(TMP.name) / "correction"
        work.mkdir()
        def git(*args):
            r = subprocess.run(["git", "-C", str(work), *args],
                               capture_output=True, text=True, timeout=15)
            self.assertEqual(r.returncode, 0, r.stderr)
            return r.stdout.strip()
        git("init", "-q")
        (work / "seed").write_text("base\n")
        git("add", "seed")
        git("-c", "user.name=Seed", "-c", "user.email=seed@example.org",
            "-c", "commit.gpgsign=false", "commit", "-qm", "seed")
        base = git("rev-parse", "HEAD")
        proof = "lean/PEqualNP/Outside/L_meta_582.lean"
        gitctl.pin_candidate(str(work), proof, b"proof version one\n")
        first = gitctl.signed_commit(str(work), base, "L-meta-582")
        gitctl.pin_candidate(str(work), proof, b"proof version two\n",
                             correction=True)
        second = gitctl.signed_commit(str(work), base, "L-meta-582",
                                      correction=True)
        self.assertNotEqual(first, second)
        self.assertEqual(gitctl.new_commits(str(work), base), [first, second])
        self.assertTrue(gitctl.all_new_commits_signed(str(work), base))


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
"""Hermetic tests for exact, lease-scoped compiler reclamation."""
import fcntl
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from missions.pnp import config, state, watchdog, compile as compiler

GAP = "L-meta-1662"
LIVE = "L-meta-1665"


class WatchdogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.patches = patch.multiple(config, GAPS_DIR=str(self.root / "gaps"),
                                      WORKTREES_DIR=str(self.root / "worktrees"),
                                      CACHE_DIR=str(self.root / "cache"))
        self.patches.start()
        self.addCleanup(self.patches.stop)
        self.stale = self.worktree(GAP, "STALE")
        self.live = self.worktree(LIVE, "RESEARCHING")
        self.unrelated = self.root / "unrelated"
        self.unrelated.mkdir()
        self.binary = self.root / "checklemma"
        shutil.copyfile(shutil.which("sleep"), self.binary)
        self.binary.chmod(0o700)

    def worktree(self, gap, status):
        state.create(gap, state=status, lease="lease-" + gap)
        cwd = Path(state.gap_dir(gap), "path", "lean")
        cwd.mkdir(parents=True)
        return cwd

    def spawn(self, cwd, executable=None, env=None):
        p = subprocess.Popen([str(executable or self.binary), "90"], cwd=cwd, env=env)
        def cleanup():
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.wait()
        self.addCleanup(cleanup)
        end = time.monotonic() + 3
        while time.monotonic() < end:
            try:
                if Path("/proc", str(p.pid), "exe").resolve(strict=True) == (executable or self.binary):
                    break
            except OSError:
                pass
            time.sleep(.02)
        return p

    def test_exact_stale_compiler_only(self):
        stale = self.spawn(self.stale)
        live = self.spawn(self.live)
        unrelated = self.spawn(self.unrelated)
        ordinary = self.spawn(self.stale, Path(shutil.which("sleep")).resolve())
        watchdog.scan()
        self.assertEqual(stale.wait(timeout=3), -signal.SIGTERM)
        for child in (live, unrelated, ordinary):
            self.assertIsNone(child.poll())

    def test_reacquisition_before_signal(self):
        p = self.spawn(self.stale)
        entry = Path("/proc", str(p.pid))
        ident = watchdog.identity(entry)
        self.assertEqual(ident[0], GAP)
        state.reacquire(GAP, lease="new-lease")
        with patch.object(watchdog, "send") as send:
            self.assertIsNone(watchdog.stop_if_terminal(entry, ident, {}, 0))
            send.assert_not_called()
        self.assertIsNone(p.poll())

    def test_orphaned_managed_compiler_on_superseded_lease(self):
        env = dict(os.environ, PNP_MANAGED_COMPILER="1",
                   PNP_PUBLISH_GAP=GAP, PNP_PUBLISH_LEASE="lease-" + GAP)
        old = self.spawn(self.stale, env=env)
        state.reacquire(GAP, lease="new-lease")
        current = self.spawn(self.stale, env=dict(env, PNP_PUBLISH_LEASE="new-lease"))
        watchdog.scan()
        self.assertEqual(old.wait(timeout=3), -signal.SIGTERM)
        self.assertIsNone(current.poll())

    def test_unreadable_state_and_busy_lock(self):
        p = self.spawn(self.stale)
        lock = os.open(Path(state.gap_dir(GAP), ".lock"), os.O_RDWR)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(watchdog.scan(), {})
            self.assertIsNone(p.poll())
        finally:
            os.close(lock)
        Path(state.state_path(GAP)).write_text("{broken")
        self.assertEqual(watchdog.scan(), {})
        self.assertIsNone(p.poll())

    def test_term_grace_and_kill_only_if_still_obsolete(self):
        p = self.spawn(self.stale)
        entry = Path("/proc", str(p.pid))
        ident = watchdog.identity(entry)
        with patch.object(watchdog, "send") as send:
            first = watchdog.stop_if_terminal(entry, ident, {}, 10)
            self.assertEqual(send.call_args.args[1], signal.SIGTERM)
            send.reset_mock()
            watchdog.stop_if_terminal(entry, ident, dict([first]), 11)
            send.assert_not_called()
            watchdog.stop_if_terminal(entry, ident, dict([first]), 14)
            self.assertEqual(send.call_args.args[1], signal.SIGKILL)
            send.reset_mock()
            state.reacquire(GAP, lease="new-lease")
            watchdog.stop_if_terminal(entry, ident, dict([first]), 15)
            send.assert_not_called()

    def test_mismatched_identity_never_signalled(self):
        p = self.spawn(self.stale)
        entry = Path("/proc", str(p.pid))
        gap, start = watchdog.identity(entry)
        with patch.object(watchdog, "send") as send:
            self.assertIsNone(watchdog.stop_if_terminal(entry, (gap, start + 1), {}, 0))
            send.assert_not_called()

    def test_requires_exact_local_assignment_for_managed_build(self):
        original = Path.cwd()
        try:
            os.chdir(self.live)
            with patch.object(compiler, "run") as run:
                self.assertEqual(compiler.main(["--", "lean", "test.lean"]), 75)
                self.assertEqual(compiler.main(["--gap", GAP, "--lease", "lease-" + GAP,
                                                "--", "lean", "test.lean"]), 75)
                self.assertEqual(compiler.main(["--gap", LIVE, "--lease", "wrong",
                                                "--", "lean", "test.lean"]), 75)
                run.assert_not_called()
        finally:
            os.chdir(original)

    def test_singleton_ensure(self):
        os.makedirs(config.CACHE_DIR, exist_ok=True)
        lock = os.open(watchdog.lock_path(), os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with patch.object(watchdog.subprocess, "Popen") as launch:
                watchdog.ensure()
                launch.assert_not_called()
        finally:
            os.close(lock)


if __name__ == "__main__":
    unittest.main()

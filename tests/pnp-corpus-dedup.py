#!/usr/bin/env python3
"""Pinned-corpus hardlink sharing: dedup, non-mutation, clean git state."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from missions.pnp import config, gitctl


def git(*args, cwd=None):
    p = subprocess.run(["git"] + list(args), cwd=cwd, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, text=True)
    if p.returncode:
        raise AssertionError("git %s failed: %s" % (args[:2], p.stderr))
    return p.stdout.strip()


class CorpusDedup(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="viche-corpus-dedup-")
        src = os.path.join(self.tmp, "src")
        os.makedirs(os.path.join(src, "lean", "PEqualNP", "Outside"))
        git("init", "-q", cwd=src)
        git("config", "user.email", "t@t", cwd=src)
        git("config", "user.name", "t", cwd=src)
        for name in ("a.lean", "b.lean"):
            with open(os.path.join(src, "lean", "PEqualNP", "Outside", name), "w") as f:
                f.write("theorem " + name.replace(".", "_") + " : True := trivial\n")
        # A tracked executable, as in the real pinned tree (tools/bin/lake etc.).
        bindir = os.path.join(src, "tools", "bin")
        os.makedirs(bindir)
        exe = os.path.join(bindir, "lake")
        with open(exe, "w") as f:
            f.write("#!/bin/sh\nexit 0\n")
        os.chmod(exe, 0o755)
        with open(os.path.join(src, "README.md"), "w") as f:
            f.write("pinned\n")
        # A tracked symlink as in the real pinned tree (records/AGENDA*.md).
        os.makedirs(os.path.join(src, "records"), exist_ok=True)
        with open(os.path.join(src, "records", "target.md"), "w") as f:
            f.write("target pinned\n")
        os.symlink("target.md",
                   os.path.join(src, "records", "AGENDA-link.md"))
        git("add", "-A", cwd=src)
        git("commit", "-qm", "base", cwd=src)
        self.sha = git("rev-parse", "HEAD", cwd=src)
        self.mirror = os.path.join(self.tmp, "fork.git")
        git("clone", "--bare", "-q", src, self.mirror)
        self.cache = os.path.join(self.tmp, "cache")
        os.makedirs(self.cache, exist_ok=True)
        self._mirror, self._cache = gitctl.MIRROR, config.CACHE_DIR
        gitctl.MIRROR, config.CACHE_DIR = self.mirror, self.cache
        self.wt = os.path.join(self.tmp, "wt")
        git("--git-dir=" + self.mirror, "worktree", "add", "--detach",
            self.wt, self.sha)

    def tearDown(self):
        gitctl.MIRROR, config.CACHE_DIR = self._mirror, self._cache
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_hardlinks_are_shared_and_git_state_is_clean(self):
        linked = gitctl.share_pinned_corpus(self.wt, self.sha)
        self.assertGreater(linked, 0)
        central = os.path.join(self.cache, "pinned-corpus", self.sha)
        rel = os.path.join("lean", "PEqualNP", "Outside", "a.lean")
        self.assertEqual(os.stat(os.path.join(self.wt, rel)).st_ino,
                         os.stat(os.path.join(central, rel)).st_ino)
        # The shared corpus is immutable so an edit cannot corrupt peers.
        self.assertEqual(os.stat(os.path.join(central, rel)).st_mode & 0o222, 0)
        # Tracked executables keep the exec bit in both the central corpus and
        # the worker worktree, so git still sees a clean pinned revision.
        exerel = os.path.join("tools", "bin", "lake")
        for root in (self.wt, central):
            mode = os.stat(os.path.join(root, exerel)).st_mode
            self.assertTrue(mode & 0o111, "exec bit lost in " + root)
            self.assertEqual(mode & 0o222, 0, "write bit present in " + root)
        # Git still sees the worktree as exactly the pinned revision.
        self.assertEqual(git("status", "--porcelain", cwd=self.wt), "")

    def test_new_worker_file_is_not_a_shared_hardlink(self):
        gitctl.share_pinned_corpus(self.wt, self.sha)
        newfile = os.path.join(self.wt, "lean", "PEqualNP", "Outside", "new.lean")
        with open(newfile, "w") as f:
            f.write("theorem new_thing : True := trivial\n")
        central = os.path.join(self.cache, "pinned-corpus", self.sha)
        self.assertFalse(os.path.exists(os.path.join(central, "lean", "PEqualNP",
                                                     "Outside", "new.lean")))
        self.assertEqual(git("status", "--porcelain", cwd=self.wt),
                         "?? lean/PEqualNP/Outside/new.lean")

    def test_symlinks_are_preserved_and_target_mtime_untouched(self):
        link = os.path.join(self.wt, "records", "AGENDA-link.md")
        target = os.path.join(self.wt, "records", "target.md")
        self.assertTrue(os.path.islink(link))
        # Give the target a distinctive mtime: a dedup that follows the
        # symlink would overwrite it via utime().
        stamp = 1600000000123456789
        os.utime(target, ns=(stamp, stamp))
        before = os.stat(target).st_mtime_ns
        gitctl.share_pinned_corpus(self.wt, self.sha)
        central = os.path.join(self.cache, "pinned-corpus", self.sha)
        # The symlink stays a symlink in both trees; it is never replaced by
        # a regular hardlinked file, and chmod never follows it.
        self.assertTrue(os.path.islink(
            os.path.join(central, "records", "AGENDA-link.md")))
        self.assertTrue(os.path.islink(link))
        self.assertEqual(os.stat(target).st_mtime_ns, before)
        self.assertEqual(git("status", "--porcelain", cwd=self.wt), "")

    def test_second_call_is_idempotent(self):
        first = gitctl.share_pinned_corpus(self.wt, self.sha)
        second = gitctl.share_pinned_corpus(self.wt, self.sha)
        self.assertGreaterEqual(second, 0)
        self.assertEqual(git("status", "--porcelain", cwd=self.wt), "")
        self.assertGreater(first, 0)


if __name__ == "__main__":
    unittest.main()

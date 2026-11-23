#!/usr/bin/env python3
"""Real local integration smoke: CLI process, lease decoding, GPG Git, PR URLs.

No network mutation. Never opens a real pull request or claims a real desk task.
"""
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
TMP = tempfile.TemporaryDirectory(prefix="pnp-real-smoke-")
os.environ["PNP_STATE_ROOT"] = str(pathlib.Path(TMP.name) / "state")

from government.pnp import cli, config, github, state, gitctl  # noqa: E402


class FullPathSmoke(unittest.TestCase):
    def test_documented_cli_is_executable(self):
        result = subprocess.run([sys.executable,
                                 str(ROOT / "government/pnp/cli.py"), "--help"],
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

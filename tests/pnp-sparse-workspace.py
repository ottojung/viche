import pathlib
import subprocess
import tempfile
import unittest

from missions.pnp import research_workspace as w


def git(path, *args):
    return subprocess.check_output(["git", "-C", str(path), *args],
                                   stderr=subprocess.STDOUT).decode().strip()


class SparseWorkspace(unittest.TestCase):
    def test_pinned_outside_and_isolation(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = root / "repo"
            repo.mkdir()
            git(repo, "init", "-q")
            out = repo / w.OUTSIDE
            out.mkdir(parents=True)
            (repo / "lean/lean-toolchain").write_text("test")
            (out / "A.lean").write_text("import PEqualNP.Outside.B\n")
            (out / "B.lean").write_text("def b := 1\n")
            (out / "Huge.lean").write_text("a" * 1000000)
            git(repo, "add", ".")
            git(repo, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                "-c", "commit.gpgsign=false", "commit", "-qm", "fixture")
            head = git(repo, "rev-parse", "HEAD")
            dest = root / "worker"
            w.create(str(repo / ".git"), dest, head, ["PEqualNP.Outside.A"])
            self.assertTrue((dest / w.OUTSIDE / "A.lean").exists())
            self.assertTrue((dest / w.OUTSIDE / "B.lean").exists())
            self.assertFalse((dest / w.OUTSIDE / "Huge.lean").exists())
            self.assertTrue((repo / w.OUTSIDE / "Huge.lean").exists())
            self.assertEqual(git(dest, "status", "--porcelain"), "")
            self.assertEqual(len(git(dest, "show", "HEAD:" + w.OUTSIDE + "Huge.lean")), 1000000)
            (dest / w.OUTSIDE / "New.lean").write_text("unique")
            with self.assertRaises(Exception):
                w.restore_incomplete(str(repo / ".git"), dest, head, [])
            self.assertEqual((dest / w.OUTSIDE / "New.lean").read_text(), "unique")
            second = root / "partial"
            git(repo, "worktree", "add", "--detach", "--no-checkout", str(second), head)
            w.restore_incomplete(str(repo / ".git"), second, head, [])
            self.assertTrue((second / "lean/lean-toolchain").exists())
            self.assertFalse((second / w.OUTSIDE / "A.lean").exists())
            git(second, "sparse-checkout", "add", "/" + w.OUTSIDE + "A.lean")
            self.assertTrue((second / w.OUTSIDE / "A.lean").exists())
            self.assertEqual(git(second, "status", "--porcelain"), "")
            git(dest, "sparse-checkout", "disable")
            self.assertEqual((dest / w.OUTSIDE / "Huge.lean").stat().st_size, 1000000)


if __name__ == "__main__":
    unittest.main()

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from missions.pnp import assignment, config, retention, state


def git(path, *args):
    return subprocess.check_output(["git", "-C", str(path), *args],
                                   stderr=subprocess.STDOUT).decode().strip()


class Retention(unittest.TestCase):
    def test_terminal_only_preserves_unique_and_recovery(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            gaps = root / "gaps"
            with patch.object(config, "STATE_ROOT", str(root)), patch.object(config, "GAPS_DIR", str(gaps)):
                rec = state.create("L-meta-7", state="LEASED", lease="fixture")
                path = Path(assignment.prepare("L-meta-7", checkout=False, worker="general")["cwd"])
                path.mkdir()
                git(path, "init", "-q")
                outside = path / retention.OUT
                outside.mkdir(parents=True)
                (outside / "clean.lean").write_text("a" * 1000000)
                (outside / "changed.lean").write_text("old")
                (path / ".gitignore").write_text("*.ignored\n")
                git(path, "add", ".")
                git(path, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                    "-c", "commit.gpgsign=false", "commit", "-qm", "fixture")
                (outside / "changed.lean").write_text("unique change")
                (outside / "new.lean").write_text("new result")
                (outside / "scratch.ignored").write_text("ignored result")
                with patch.object(retention, "idle", return_value=True):
                    self.assertEqual(retention.compact(path), "active_or_unbound")
                    rec["state"] = "RELEASED"
                    state.save(rec)
                    with patch.object(retention, "idle", return_value=False):
                        self.assertEqual(retention.compact(path), "in_use")
                    self.assertGreater(retention.compact(path), 0)
                    self.assertEqual(retention.compact(path), "already")
                self.assertFalse((outside / "clean.lean").exists())
                self.assertEqual((outside / "changed.lean").read_text(), "unique change")
                self.assertEqual((outside / "new.lean").read_text(), "new result")
                self.assertEqual((outside / "scratch.ignored").read_text(), "ignored result")
                self.assertTrue((path.parent / "storage-delta.tar.gz").is_file())
                info = json.loads((path.parent / "storage-compact.json").read_text())
                self.assertEqual(git(path, "rev-parse", info["ref"]), info["base"])
                git(path, "sparse-checkout", "disable")
                self.assertEqual((outside / "clean.lean").stat().st_size, 1000000)


if __name__ == "__main__":
    unittest.main()

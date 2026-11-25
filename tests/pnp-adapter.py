#!/usr/bin/env python3
"""Tests for family-level proof adaptation and certificate reuse."""
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import time
from argparse import Namespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from missions.pnp import assignment, config, state, validate
from missions.pnp.adapter.__main__ import _load_gap
from missions.pnp.proofs import corpus
from missions.pnp.adapter.closure import parse_source, dependency_closure
from missions.pnp.adapter.adapt import adapt_exact_module, controlled_module_rename
from missions.pnp.adapter.detect import detect_and_adapt

MIRROR = "/var/lib/lubko/wd/viche-state/pnp/cache/fork.git"


def git_cat(path, revision="refs/remotes/upstream/main"):
    return subprocess.check_output(
        ["git", "--git-dir=" + MIRROR, "cat-file", "-p", f"{revision}:{path}"],
        text=True,
    )


def mirror_available():
    return Path(MIRROR).exists()


class AdapterClosureTests(unittest.TestCase):
    def test_controlled_module_rename_not_global(self):
        src = "namespace PEqualNP.Outside.L_meta_1\ndef foo := 1\nend PEqualNP.Outside.L_meta_1\ntheorem PEqualNP.Outside.L_meta_1 : True := by trivial\n"
        out = controlled_module_rename(src, "PEqualNP.Outside.L_meta_1", "PEqualNP.Outside.L_meta_2")
        self.assertIn("PEqualNP.Outside.L_meta_2", out)
        self.assertNotIn("PEqualNP.Outside.L_meta_1", out)
        # Do not touch unrelated names
        src2 = "def L_meta_1_aux := 1\nnamespace Other.L_meta_1\nend Other.L_meta_1\n"
        out2 = controlled_module_rename(src2, "PEqualNP.Outside.L_meta_1", "PEqualNP.Outside.L_meta_2")
        self.assertEqual(out2, src2)

    def test_dependency_closure_extracts_transitive_defs(self):
        src = """import Mathlib
import PEqualNP.Defs

namespace PEqualNP.Outside.L_meta_9

def base : Nat := 1
def helper : Nat := base + 1
def unused : Nat := 999
lemma mid : helper = base + 1 := rfl

end PEqualNP.Outside.L_meta_9

theorem PEqualNP.Outside.L_meta_9 : True := by
  have h := PEqualNP.Outside.L_meta_9.mid
  trivial
"""
        model = parse_source(src)
        decls = dependency_closure(model, "PEqualNP.Outside.L_meta_9")
        names = [d.name for d in decls]
        self.assertIn("mid", names)
        self.assertIn("helper", names)
        self.assertIn("base", names)
        self.assertNotIn("unused", names)

    @unittest.skipUnless(mirror_available(), "upstream mirror unavailable")
    def test_closure_on_l_meta_2455(self):
        src = git_cat("lean/PEqualNP/Outside/L_meta_2455.lean")
        model = parse_source(src)
        decls = dependency_closure(model, "PEqualNP.Outside.L_meta_2455")
        names = {d.name for d in decls}
        self.assertIn("theta_fifteen_gates", names)
        self.assertIn("least_theta_five_branches", names)
        # Should be substantial but a closure (includes the final theorem).
        self.assertGreater(len(decls), 100)


class AdapterAdaptTests(unittest.TestCase):
    def test_nested_relative_namespace_preserved(self):
        src = ("import Mathlib.Tactic.NormNum\n"
               "namespace PEqualNP.Outside.L_meta_1\nnamespace Inner\n"
               "lemma x : True := by trivial\nend Inner\n"
               "end PEqualNP.Outside.L_meta_1\n"
               "theorem PEqualNP.Outside.L_meta_1 : True := by "
               "exact PEqualNP.Outside.L_meta_1.Inner.x\n")
        gap={"id":"L-meta-2","file":"lean/PEqualNP/Outside/L_meta_2.lean",
             "module":"PEqualNP.Outside.L_meta_2","statement":"True","imports":[]}
        r=adapt_exact_module(src,gap)
        self.assertTrue(r.ok,r.details)
        self.assertIn("namespace Inner\n",r.candidate)
        self.assertTrue(r.candidate.startswith("import Mathlib.Tactic.NormNum\n"))
        self.assertNotIn("namespace PEqualNP.Outside.L_meta_2.Inner",r.candidate)
        d=detect_and_adapt(None,gap,source_text=src)
        self.assertTrue(d[0].ok,d[0].error)

    @unittest.skipUnless(mirror_available(), "upstream mirror unavailable")
    def test_adapt_l_meta_1152_to_self(self):
        src = git_cat("lean/PEqualNP/Outside/L_meta_1152.lean")
        gap = {
            "id": "L-meta-1152",
            "file": "lean/PEqualNP/Outside/L_meta_1152.lean",
            "module": "PEqualNP.Outside.L_meta_1152",
            "imports": ["PEqualNP.Defs"],
            "statement": "∃ C : PEqualNP.CircuitLowerBounds.Circuit, PEqualNP.MetaComplexity.Monotone2 C ∧ C.size ≤ 8 ∧ ∀ x : Fin 8 → Bool, C.eval (List.ofFn x) = (fun x : Fin 8 → Bool => (x 0 && x 1) || (x 0 && x 2) || (x 0 && x 3) || (x 1 && x 4) || (x 1 && x 5) || (x 6 && x 7)) x",
        }
        r = adapt_exact_module(src, gap)
        self.assertTrue(r.ok, r.details)
        self.assertEqual(r.details["sha256"], validate.validate(gap, r.candidate.encode("utf-8")))

    @unittest.skipUnless(mirror_available(), "upstream mirror unavailable")
    def test_adapt_l_meta_1152_to_new_module(self):
        src = git_cat("lean/PEqualNP/Outside/L_meta_1152.lean")
        gap = {
            "id": "L-meta-99999",
            "file": "lean/PEqualNP/Outside/L_meta_99999.lean",
            "module": "PEqualNP.Outside.L_meta_99999",
            "imports": ["PEqualNP.Defs"],
            "statement": "∃ C : PEqualNP.CircuitLowerBounds.Circuit, PEqualNP.MetaComplexity.Monotone2 C ∧ C.size ≤ 8 ∧ ∀ x : Fin 8 → Bool, C.eval (List.ofFn x) = (fun x : Fin 8 → Bool => (x 0 && x 1) || (x 0 && x 2) || (x 0 && x 3) || (x 1 && x 4) || (x 1 && x 5) || (x 6 && x 7)) x",
        }
        r = adapt_exact_module(src, gap)
        self.assertTrue(r.ok, r.details)
        self.assertIn("PEqualNP.Outside.L_meta_99999", r.candidate)
        self.assertNotIn("PEqualNP.Outside.L_meta_1152", r.candidate)
        validate.validate(gap, r.candidate.encode("utf-8"))


class AdapterDetectTests(unittest.TestCase):
    @unittest.skipUnless(mirror_available(), "upstream mirror unavailable")
    def test_detect_family_2455_to_2457(self):
        # Index the two family members in a temp corpus DB.
        db = sqlite3.connect(":memory:")
        db.execute("create table proof(path text primary key, blob text, statement text, source text, tactics text, imports text)")
        db.execute("create table metadata(key text primary key, value text)")
        for name in ("L_meta_2455", "L_meta_2457"):
            path = f"lean/PEqualNP/Outside/{name}.lean"
            src = git_cat(path)
            stmt = corpus.statement(src)
            imports = json.dumps(__import__("re").findall(r"(?m)^import ([A-Za-z0-9_.]+)$", src))
            db.execute("insert into proof values(?,?,?,?,?,?)",
                       (path, "blob", stmt, src, "[]", imports))
        db.execute("insert into metadata values('revision','test')")
        db.execute("insert into metadata values('index_version','2')")

        target_src = git_cat("lean/PEqualNP/Outside/L_meta_2457.lean")
        target_stmt = corpus.statement(target_src)
        gap = {
            "id": "L-meta-2457",
            "file": "lean/PEqualNP/Outside/L_meta_2457.lean",
            "module": "PEqualNP.Outside.L_meta_2457",
            "imports": ["PEqualNP.Defs"],
            "statement": target_stmt,
        }
        detections = detect_and_adapt(db, gap, limit=8)
        self.assertTrue(detections, "no detections")
        ok = [d for d in detections if d.ok]
        self.assertTrue(ok, f"no successful adaptation: {[d.error for d in detections]}")
        # The exact 2457 source should be adaptable.
        best = ok[0]
        validate.validate(gap, best.candidate.encode("utf-8"))
        self.assertIn("PEqualNP.Outside.L_meta_2457", best.candidate)


class AdapterCLITests(unittest.TestCase):
    def test_live_assignment_uses_exact_binding(self):
        with tempfile.TemporaryDirectory() as tmp, patch.multiple(
                config, STATE_ROOT=tmp, GAPS_DIR=tmp+"/gaps", CACHE_DIR=tmp+"/cache"):
            rec=state.create("L-meta-7", state="LEASED", lease="one",
                statement="True", module="PEqualNP.Outside.L_meta_7",
                path="lean/PEqualNP/Outside/L_meta_7.lean",
                imports=["PEqualNP.Defs"], lease_expires_at=time.time()+600)
            cwd=Path(assignment.prepare("L-meta-7",checkout=False,worker="general")["cwd"])
            args=Namespace(gap_json=None,module=None,statement=None,file=None,
                           gap_id=None,imports=None)
            with patch.object(Path,"cwd",return_value=cwd):
                self.assertEqual(_load_gap(args)["id"],"L-meta-7")
                self.assertEqual(_load_gap(args)["statement"],rec["statement"])
                with self.assertRaises(SystemExit):
                    _load_gap(Namespace(**{**vars(args),"gap_json":"offline.json"}))
                state.update("L-meta-7",lease="two")
                with self.assertRaises(SystemExit):
                    _load_gap(args)

    def test_cli_closure(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp, "x.lean")
            src.write_text(
                "import Mathlib\n\nnamespace M\n\ndef a : Nat := 1\ndef b : Nat := a\ndef c : Nat := 99\n\nend M\n\n"
                "theorem M.t : True := by\n  have h := M.b\n  trivial\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [sys.executable, "-m", "missions.pnp.adapter", "closure", str(src), "--target", "M.t"],
                cwd=str(Path(__file__).resolve().parents[1]),
                capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            obj = json.loads(proc.stdout)
            names = {d["name"] for d in obj["declarations"]}
            self.assertIn("b", names)
            self.assertIn("a", names)
            self.assertNotIn("c", names)


if __name__ == "__main__":
    unittest.main(verbosity=2)

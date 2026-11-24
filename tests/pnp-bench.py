#!/usr/bin/env python3
"""Offline tests for missions.pnp.bench retrospective generator benchmark."""
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from missions.pnp.bench import corpus, evaluate, generators
from missions.pnp.bench.cli import main as bench_main


def _stmt(edges, n=8, bound=8):
    rhs = " || ".join(f"(x {a} && x {b})" for a, b in edges)
    return (
        "∃ C : PEqualNP.CircuitLowerBounds.Circuit, "
        "PEqualNP.MetaComplexity.Monotone2 C ∧ "
        f"C.size ≤ {bound} ∧ ∀ x : Fin {n} → Bool, "
        f"C.eval (List.ofFn x) = (fun x : Fin {n} → Bool => {rhs}) x"
    )


def _make_db(rows):
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    Path(path).unlink()  # we'll create via sqlite
    db = sqlite3.connect(path)
    db.execute("create table proof(path text primary key, blob text, statement text, source text, tactics text, imports text)")
    db.execute("create table metadata(key text primary key, value text)")
    for i, (module, edges, bound) in enumerate(rows):
        path_lean = "lean/" + module.replace(".", "/") + ".lean"
        stmt = _stmt(edges, bound=bound)
        db.execute("insert into proof values(?,?,?,?,?,?)",
                   (path_lean, f"blob{i}", stmt, "", "[]", json.dumps(["PEqualNP.Defs"])))
    db.execute("insert into metadata values('revision','test')")
    db.execute("insert into metadata values('index_version','2')")
    db.commit()
    db.close()
    return path


class BenchTests(unittest.TestCase):
    def test_generators_satisfy_known_row(self):
        edges = [(0, 2), (0, 3), (1, 2), (1, 3)]
        expected_max = {"legacy_greedy": 3, "exact_star_cover": 5}
        for name, gen in generators.GENERATORS.items():
            gates, out = gen(4, edges)
            ok, detail = evaluate.independent_truth_table(4, edges, gates, out)
            self.assertTrue(ok, (name, detail))
            self.assertLessEqual(len(gates), expected_max[name], name)

    def test_independent_verifier_catches_bad_output(self):
        edges = [(0, 1), (2, 3)]
        gates, out = generators.exact_star_cover(4, edges)
        ok, _ = evaluate.independent_truth_table(4, edges, gates, out)
        self.assertTrue(ok)
        bad_gates = list(gates)
        bad_gates[-1] = ("and", 0, 1)  # corrupt last gate
        ok, detail = evaluate.independent_truth_table(4, edges, bad_gates, out)
        self.assertFalse(ok)
        self.assertIn(detail["error"], {"semantic_mismatch", "wire_out_of_range", "output_out_of_range"})

    def test_corpus_load_and_evaluate(self):
        rows = [
            ("PEqualNP.Outside.L_meta_1", [(0, 1), (2, 3)], 3),
            ("PEqualNP.Outside.L_meta_2", [(0, 1), (0, 2), (1, 3)], 4),
            ("PEqualNP.Outside.L_meta_3", [(0, 1), (0, 2), (0, 3), (1, 4)], 5),
        ]
        db_path = _make_db(rows)
        try:
            loaded = corpus.load_graph_circuits(db_path)
            self.assertEqual(len(loaded), 3)
            for name, gen in generators.GENERATORS.items():
                report = evaluate.evaluate_with_holdouts(loaded, gen, name, test_fraction=0.34)
                s = report["overall"]
                self.assertEqual(s["total"], 3)
                self.assertEqual(s["truth_table_verified"], 3)
                self.assertEqual(s["checked_bound_satisfied"], 3)
                self.assertIn("family_holdout", report)
                self.assertIn("time_holdout", report)
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_cli_json(self):
        import io, contextlib
        rows = [
            ("PEqualNP.Outside.L_meta_10", [(0, 1), (2, 3)], 3),
            ("PEqualNP.Outside.L_meta_11", [(0, 1), (0, 2), (1, 3)], 4),
        ]
        db_path = _make_db(rows)
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = bench_main(["--corpus-db", db_path, "--json", "--no-results"])
            self.assertEqual(rc, 0)
            report = json.loads(buf.getvalue())
            self.assertEqual(report["rows"], 2)
            self.assertEqual(len(report["reports"]), 2)
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_holdout_group_split(self):
        rows = []
        for i in range(8):
            rows.append({"module": f"M{i}", "n": 8, "edge_count": 4, "edges": [[0, 1]], "bound": 1, "path": f"p{i}"})
        for i in range(4):
            rows.append({"module": f"N{i}", "n": 8, "edge_count": 7, "edges": [[0, 1]], "bound": 1, "path": f"q{i}"})
        train, test = evaluate.holdout_split(rows, corpus.family_key, test_fraction=0.25)
        self.assertTrue(train)
        self.assertTrue(test)
        train_fams = {corpus.family_key(r) for r in train}
        test_fams = {corpus.family_key(r) for r in test}
        self.assertFalse(train_fams & test_fams)


if __name__ == "__main__":
    unittest.main(verbosity=2)

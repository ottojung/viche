#!/usr/bin/env python3
"""No network, no lease acquisition, no GitHub mutation."""
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from missions.pnp.proofs import corpus, circuit, synthesis
from missions.pnp import validate

META = {"id": "L-meta-12345",
        "module": "PEqualNP.Outside.L_meta_12345",
        "file": "lean/PEqualNP/Outside/L_meta_12345.lean",
        "imports": ["PEqualNP.Defs"],
        "statement": ("let C : PEqualNP.CircuitLowerBounds.Circuit := "
                      "(⟨[⟨PEqualNP.CircuitLowerBounds.GateOp.and, [0, 1]⟩], 2⟩ : PEqualNP.CircuitLowerBounds.Circuit); "
                      "C.gates.length = 1 ∧ C.output = 2 ∧ ∀ x : Fin 2 → Bool, C.eval (List.ofFn x) = ((x 0 && x 1))")}


class ProofTools(unittest.TestCase):
    def test_finite_circuit(self):
        result = circuit.explicit_circuit(META)
        self.assertTrue(result["verified"])
        self.assertEqual(result["cases"], 4)
        validate.validate(META, circuit.render(META, "decide").encode())

    def test_false_and_malformed_circuit(self):
        bad = dict(META, statement=META["statement"].replace("GateOp.and", "GateOp.or"))
        self.assertFalse(circuit.explicit_circuit(bad)["verified"])
        bad = dict(META, statement=META["statement"].replace("[0, 1]", "[0, 2]"))
        self.assertIsNone(circuit.explicit_circuit(bad))
        bad = dict(META, statement=META["statement"].replace("((x 0 && x 1))", "((x 0 && x 1) && (x 0 && x 1))"))
        self.assertIsNone(circuit.explicit_circuit(bad))

    def test_synthesis_bound_and_truth_table(self):
        meta = dict(META, statement=("∃ C : PEqualNP.CircuitLowerBounds.Circuit, "
          "PEqualNP.MetaComplexity.Monotone2 C ∧ C.size ≤ 3 ∧ ∀ x : Fin 4 → Bool, "
          "C.eval (List.ofFn x) = (fun x : Fin 4 → Bool => "
          "(x 1 && x 3) || (x 0 && x 2) || (x 0 && x 3) || (x 1 && x 2)) x"))
        r = synthesis.candidate(meta)
        self.assertEqual(r["gates"], 3)
        self.assertEqual(r["cases"], 16)
        self.assertIn("(b1 && b3) || (b0 && b2)",r["candidate"])
        validate.validate(meta,r["candidate"].encode())
        bad = dict(meta, statement=meta["statement"].replace("≤ 3","≤ 2"))
        self.assertIsNone(synthesis.candidate(bad)["candidate"])

    def test_corpus_incremental_and_allowed_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = sqlite3.connect(":memory:")
            db.execute("create table proof(path text primary key, blob text, statement text, source text, tactics text, imports text)")
            db.execute("create table metadata(key text primary key, value text)")
            def git(*args):
                return subprocess.check_output(["git","-C",tmp,*args],stderr=subprocess.STDOUT)
            git("init","-q")
            proof = Path(tmp, META["file"])
            proof.parent.mkdir(parents=True)
            proof.write_text(circuit.render(META,"decide"))
            git("add",".")
            git("-c","user.name=Test","-c","user.email=test@example.test","-c","commit.gpgsign=false","commit","-qm","fixture")
            sha = corpus.update(db,mirror=str(Path(tmp,".git")),revision="HEAD")
            hits = corpus.search(db,META["statement"],[META["module"]])
            self.assertEqual(len(hits),1)
            self.assertTrue(hits[0]["direct_import_allowed"])
            self.assertIn("decide",hits[0]["tactics"])
            self.assertEqual(corpus.update(db,mirror=str(Path(tmp,".git")),revision="HEAD"),sha)
            proof.unlink()
            git("add","-A")
            git("-c","user.name=Test","-c","user.email=test@example.test","-c","commit.gpgsign=false","commit","-qm","remove")
            corpus.update(db,mirror=str(Path(tmp,".git")),revision="HEAD")
            self.assertEqual(corpus.search(db,META["statement"]),[])


if __name__ == "__main__":
    unittest.main(verbosity=2)

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
from missions.pnp.proofs import corpus, circuit, synthesis, search
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

    def test_joint_reread_certificate(self):
        # AND(AND(x0,x1),OR(x0,x1)) computes one edge. Each scalar
        # minimum is 1, but no single proof tree is simultaneously read-1.
        from missions.pnp.proofs import reread
        c = "PEqualNP.CircuitLowerBounds."
        gates = ", ".join("{ op := "+c+"GateOp."+op+", inputs := ["+str(a)+", "+str(b)+"] }"
                          for op,a,b in (("and",0,1),("or",0,1),("and",2,3)))
        edge = "([(0, 1)] : List (Fin 2 × Fin 2))"
        statement = (f"∀ C : {c}Circuit, C = ({{ gates := [{gates}], output := 4 }} : {c}Circuit) → "
          f"PEqualNP.TopForm.IsAO2 2 C ∧ C.size = 3 ∧ "
          f"(∀ x : Fin 2 → Bool, PEqualNP.MetaComplexity.circuitFun 2 C x = decide (∃ e ∈ {edge}, x e.1 = true ∧ x e.2 = true)) ∧ "
          f"(∀ e ∈ {edge}, PEqualNP.Core.ReadTwiceAt 2 C (C.output - 2) e.1 e.2 ↔ e ∈ {edge})")
        meta = dict(META,statement=statement)
        r = circuit.explicit_circuit(meta)
        self.assertEqual(r["actual_reread"],[(0,1)])
        self.assertTrue(r["verified"])
        src=circuit.render(meta,"decide")
        self.assertIn("subst C",src)
        validate.validate(meta,src.encode())
        bad = dict(meta,statement=statement.removesuffix(edge+")")+"([] : List (Fin 2 × Fin 2)))")
        self.assertFalse(circuit.explicit_circuit(bad)["verified"])
        with self.assertRaises(ValueError):
            circuit.render(bad,"decide")
        self.assertIsNone(circuit.explicit_circuit(dict(meta,statement=statement+" ∧ False")))
        self.assertFalse(reread.read_once(2,[("and",0,1),("or",0,1),("and",2,3)],4,0,1))
        self.assertTrue(reread.read_once(2,[("and",0,1)],2,0,1))

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

    def test_minimum_star_cover_has_no_duplicate_edges(self):
        # Two intersecting full stars, plus a disconnected edge. Greedy
        # maximal stars can pay for an edge twice; exact assignment cannot.
        edges={(0,1),(0,2),(0,3),(1,4),(1,5),(6,7)}
        gates,out=synthesis.star_cover(8,edges)
        self.assertEqual(len(gates),8)
        self.assertTrue(synthesis.verify(8,edges,gates,out))
        gates,out=synthesis.synthesize(8,edges)
        self.assertLessEqual(len(gates),8)
        self.assertTrue(synthesis.verify(8,edges,gates,out))

    def test_sat_exact_against_independent_two_variable_enumeration(self):
        import itertools
        # Independently enumerate all functions realizable with up to two
        # gates (including repeated inputs, NOT and any output wire).
        functions = {0b1010,0b1100}
        frontier = {(0b1010,0b1100)}
        for budget in range(3):
            if budget:
                new=set()
                for wires in frontier:
                    values={15^a for a in wires}
                    values.update(a&b for a in wires for b in wires)
                    values.update(a|b for a in wires for b in wires)
                    new.update(wires+(v,) for v in values)
                    functions.update(values)
                frontier=new
            for truth in range(16):
                raw={"n":2,"gates":budget,"ones":[r for r in range(4) if truth>>r&1]}
                result=search.solve(raw,5)
                if result["result"]=="unavailable":
                    self.skipTest("optional SAT solver unavailable")
                self.assertEqual(result["result"],"verified_witness" if truth in functions else "unsat_encoding",(raw,result))
    def test_sat_checkpoint_and_fixed_prefix(self):
        raw={"n":3,"gates":2,"edges":[[0,1],[0,2]],"ops":["and","or"],"fixed":[["or",2,1]]}
        with tempfile.TemporaryDirectory() as tmp:
            cp=Path(tmp,"rows.json")
            r=search.solve(raw,5,cp)
            if r["result"]=="unavailable":
                self.skipTest("optional SAT solver unavailable")
            self.assertEqual(r["result"],"verified_witness")
            self.assertEqual(r["gates"][0],["or",2,1])
            self.assertTrue(cp.exists())
            self.assertEqual(search.solve(raw,5,cp)["result"],"verified_witness")
            with self.assertRaises(ValueError):
                search.solve(dict(raw,gates=3),5,cp)
    def test_structural_hints_not_implication_verdicts(self):
        hint=corpus.structural_hint("P → Q → R","Q → R")
        self.assertTrue(hint["same_conclusion_shape"])
        self.assertEqual(hint["hypotheses_matched"],1)

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

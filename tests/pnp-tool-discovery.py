"""Capability advertising and generator preflight remain advisory."""
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp import assignment, config, preflight, state, tools

STMT = ("∃ C : PEqualNP.CircuitLowerBounds.Circuit, "
        "PEqualNP.MetaComplexity.Monotone2 C ∧ C.size ≤ 2 ∧ "
        "∀ x : Fin 3 → Bool, C.eval (List.ofFn x) = "
        "(fun x : Fin 3 → Bool => (x 0 && x 1) || (x 0 && x 2)) x")

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root=self.tmp.name
        p=patch.multiple(config,STATE_ROOT=root,GAPS_DIR=root+"/gaps",CACHE_DIR=root+"/cache")
        p.start()
        self.addCleanup(p.stop)
        self.rec=state.create("L-meta-7",state="LEASED",lease="one",
            statement=STMT,module="PEqualNP.Outside.L_meta_7",
            path="lean/PEqualNP/Outside/L_meta_7.lean",imports=["PEqualNP.Defs"],
            lease_expires_at=time.time()+600)
    def test_generator_is_independent_of_model_and_does_not_publish(self):
        result=preflight.run(self.rec,"v1")
        self.assertEqual(result["result"],"candidate")
        self.assertFalse(result["local_lean_checked"])
        self.assertTrue(Path(result["candidate"]).is_file())
        self.assertEqual(state.load("L-meta-7"),self.rec)
        with patch.object(preflight.synthesis,"candidate") as generate:
            self.assertEqual(preflight.run(self.rec,"v1"),result)
            generate.assert_not_called()
        Path(result["candidate"]).write_text("changed")
        self.assertIsNone(preflight.read(self.rec))
        self.assertEqual(preflight.run(self.rec,"v1")["result"],"candidate")
    def test_old_lease_and_unsupported_problem(self):
        preflight.run(self.rec,"v1")
        newer=state.update("L-meta-7",lease="two")
        self.assertIsNone(preflight.read(newer))
        self.assertIsNone(preflight.run(self.rec,"v2"))
        new=state.update("L-meta-7",statement="True")
        self.assertEqual(preflight.run(new,"v1")["result"],"not_recognized")
        state.update("L-meta-7",state="RELEASED")
        self.assertEqual(preflight.scan(),[])
    def test_tool_invocation_is_bound_to_attempt(self):
        cwd=Path(assignment.prepare("L-meta-7",checkout=False,worker="general")["cwd"])
        tools.record("proofs-synthesize",cwd)
        self.assertIn("proofs-synthesize",tools.usage(self.rec)["general"])
        newer=state.update("L-meta-7",lease="new")
        self.assertEqual(tools.usage(newer),{})
        tools.record("proofs-search",cwd)
        self.assertEqual(tools.usage(newer),{})

    def test_only_installed_capabilities_and_revision_changes(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(tools,"ROOT",Path(tmp)):
            self.assertFalse(any("adapter" in x["command"] for x in tools.inventory()))
            a=tools.snapshot()["revision"]
            path=Path(tmp,"adapter","__main__.py")
            path.parent.mkdir()
            path.write_text("pass")
            self.assertTrue(any("adapter detect" in x["command"] for x in tools.inventory()))
            b=tools.snapshot()["revision"]
            self.assertNotEqual(a,b)
            path.write_text("# changed")
            self.assertNotEqual(b,tools.snapshot()["revision"])

if __name__=="__main__":
    unittest.main(verbosity=2)

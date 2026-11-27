import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missions.pnp.lbcert.generators.onenot_candidates import gen
from missions.pnp.validate import validate

class TestCandidates(unittest.TestCase):
    def test_all_exact_candidates(self):
        rows = gen.records()
        self.assertEqual(len(rows), 5)
        for statement,row in rows.items():
            with self.subTest(gid=row["gid"]):
                self.assertTrue(gen.matches(statement))
                text = gen.generate(row["gid"], statement)
                self.assertIsNotNone(text)
                self.assertEqual(len(validate(dict(row["metadata"],statement=statement),text.encode())),64)

    def test_refuse_changed_statement_or_id(self):
        statement = next(iter(gen.records()))
        self.assertFalse(gen.matches(statement+" True"))
        self.assertIsNone(gen.generate("L-meta-00000",statement))

if __name__ == "__main__":
    unittest.main()

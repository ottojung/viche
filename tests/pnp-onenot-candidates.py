import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missions.pnp.lbcert.generators.onenot_candidates import gen
from missions.pnp.validate import validate

class TestCandidates(unittest.TestCase):
    def test_all_exact_candidates(self):
        rows = gen.records()
        self.assertEqual(len(rows), 12)
        for statement,row in rows.items():
            with self.subTest(gid=row["gid"]):
                self.assertTrue(gen.matches(statement))
                text = gen.generate(row["gid"], statement)
                self.assertIsNotNone(text)
                self.assertEqual(len(validate(dict(row["metadata"],statement=statement),text.encode())),64)

    def test_unseeded_search_and_exact_shape(self):
        import shutil
        import time
        from unittest.mock import patch
        if not shutil.which("cc"):
            self.skipTest("no C compiler")
        allrows=gen.records()
        stmt,row=next((s,r) for s,r in allrows.items() if r["gid"]=="L-meta-27817")
        other={s:r for s,r in allrows.items() if s!=stmt}
        gen.pattern.cache_clear()
        try:
            start=time.monotonic()
            with patch.object(gen,"records",return_value=other):
                result=gen.generate(row["gid"],stmt)
            self.assertIsNotNone(result)
            self.assertLess(time.monotonic()-start,12)
            validate(dict(row["metadata"],statement=stmt),result.encode())
        finally:gen.pattern.cache_clear()
        self.assertFalse(gen.matches("¬ ("+stmt+")"))
        self.assertFalse(gen.matches(stmt.replace("Fin 8","Fin 9",1)))

    def test_refuse_changed_statement_or_id(self):
        statement = next(iter(gen.records()))
        self.assertFalse(gen.matches(statement+" True"))
        self.assertIsNone(gen.generate("L-meta-00000",statement))

if __name__ == "__main__":
    unittest.main()

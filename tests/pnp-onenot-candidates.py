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
        # Deterministic regression of the adaptive path; production wall-clock
        # refusals are allowed and cannot be asserted away on a busy host.
        from unittest.mock import patch
        allrows=gen.records()
        stmt,row=next((s,r) for s,r in allrows.items() if r["gid"]=="L-meta-27817")
        other={s:r for s,r in allrows.items() if s!=stmt}
        load=gen.load_module
        def fixture(name,path):
            m=load(name,path)
            if name=="pnp_onenot_screen":
                m.screen=lambda emitter,n,f,w: [tuple(x) for x in row["pairs"]]
            return m
        gen.pattern.cache_clear()
        try:
            with patch.object(gen,"records",return_value=other), patch.object(gen,"load_module",side_effect=fixture):
                result=gen.generate(row["gid"],stmt)
            self.assertIsNotNone(result)
            validate(dict(row["metadata"],statement=stmt),result.encode())
        finally:gen.pattern.cache_clear()
        self.assertFalse(gen.matches("¬ ("+stmt+")"))
        self.assertFalse(gen.matches(stmt.replace("Fin 8","Fin 9",1)))

    def test_screen_refuses_timeout(self):
        from unittest.mock import patch
        import subprocess
        path=gen.HERE/"search.py"
        search=gen.load_module("screen_test",path)
        emitter=gen.load_module("emitter_test",gen.HERE.parent.parent/"onenot"/"onenot.py")
        from types import SimpleNamespace
        f=[False]*255+[True]
        w=[(0,1,{})]*3
        with patch.dict(sys.modules, {"screen_binary":SimpleNamespace(cached_screen=lambda *a,**kw:None)}):
            self.assertIsNone(search.screen(emitter,8,f,w))
        with patch.dict(sys.modules, {"screen_binary":SimpleNamespace(cached_screen=lambda *a,**kw:"screen")}), \
             patch.object(search.subprocess,"run",side_effect=subprocess.TimeoutExpired("screen",2)):
            self.assertIsNone(search.screen(emitter,8,f,w))

    def test_refuse_changed_statement_or_id(self):
        statement = next(iter(gen.records()))
        self.assertFalse(gen.matches(statement+" True"))
        self.assertIsNone(gen.generate("L-meta-00000",statement))

if __name__ == "__main__":
    unittest.main()

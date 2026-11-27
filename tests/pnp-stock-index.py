"""The optional index is never a proof receipt."""
import os
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp.lbcert.generators.promise import gen,stock_index,batch


class IndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.env=patch.dict(os.environ,{"PNP_STATE_ROOT":self.tmp.name})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.p=("two",2,2,1,2,"FanInTwo")
        self.n,self.rows,self.t=gen.domain(self.p)
        self.path=stock_index.path_for(self.p)
        self.path.parent.mkdir(parents=True)
        # AND of the two distinct variables is true only on the off-diagonal.
        self.sol=([("and",[0,1])],2)
        self.assertTrue(gen.valid(self.p,self.sol))

    def fixture(self,record=b"\x01\x02\x00\x00\x01",offset=None,inputs=None):
        w=len(self.rows)
        header=stock_index.MAGIC+struct.pack("<4I",self.n,w,1,0)
        header+=struct.pack("<2I",*(gen.input_tables(self.n,self.rows) if inputs is None else inputs))
        table=[0]*(1<<w)
        table[self.t]=len(header)+4*len(table) if offset is None else offset
        self.path.write_bytes(header+struct.pack(f"<{len(table)}I",*table)+record)

    def test_valid_and_missing(self):
        self.assertIsNone(stock_index.lookup(self.p,gen))
        self.fixture()
        self.assertEqual(stock_index.lookup(self.p,gen),self.sol)

    def test_wrong_table_signature(self):
        self.fixture(inputs=[0,0])
        self.assertIsNone(stock_index.lookup(self.p,gen))

    def test_wrong_semantics(self):
        self.fixture(record=b"\x01\x02\x01\x00\x01")
        self.assertIsNone(stock_index.lookup(self.p,gen))

    def test_corrupt_offset_or_truncation(self):
        for off in (1,2**32-1):
            self.fixture(offset=off)
            self.assertIsNone(stock_index.lookup(self.p,gen))
        self.fixture(record=b"\x01\x02\x00")
        self.assertIsNone(stock_index.lookup(self.p,gen))

    def test_bad_wires_or_budget(self):
        self.fixture(record=b"\x01\x02\x00\x02\x01")
        self.assertIsNone(stock_index.lookup(self.p,gen))
        self.fixture()
        self.assertIsNone(stock_index.lookup(("two",2,2,0,2,"FanInTwo"),gen))

    def test_monotone_excludes_not(self):
        p=("two",2,2,1,8,"Monotone2")
        self.assertIsNone(stock_index.lookup_file(self.path,p,gen))
        self.fixture(record=b"\x01\x02\x02\x00\x00")
        self.assertIsNone(stock_index.lookup_file(self.path,("two",2,2,1,2,"Monotone2"),gen))

    def test_symlink_not_followed(self):
        self.fixture()
        other=self.path.with_suffix(".data")
        self.path.rename(other)
        self.path.symlink_to(other)
        self.assertIsNone(stock_index.lookup(self.p,gen))

    def test_index_snapshot_ignores_non_regular_and_temporary_files(self):
        matrix = ("matrix", 4, 5, 9, 123, "Monotone2")
        p = stock_index.path_for(matrix)
        before = stock_index.index_versions()
        self.assertEqual(stock_index.version_for(matrix, before), b"missing")
        tmp = p.with_suffix(".idx.tmp")
        tmp.write_bytes(b"candidate")
        self.assertEqual(before, stock_index.index_versions())
        p.symlink_to(tmp)
        self.assertEqual(before, stock_index.index_versions())
        p.unlink()
        tmp.rename(p)
        installed = stock_index.index_versions()
        self.assertNotEqual(stock_index.version_for(matrix, installed), b"missing")
        # A discovery snapshot is immutable even if the live path is replaced.
        self.assertEqual(stock_index.version_for(matrix, before), b"missing")
        tmp.write_bytes(b"candidate")
        tmp.replace(p)
        self.assertNotEqual(stock_index.version_for(matrix, installed),
                            stock_index.version_for(matrix, stock_index.index_versions()))

    def test_only_matching_plugin_domain_is_retried(self):
        from missions.pnp.lbcert import plugins, autosolve
        s45 = ("PEqualNP.Represents.RepSizeAtMost "
               "(fun (u : Fin 4) (v : Fin 5) => (123 : ℕ).testBit (5 * u.val + v.val)) 9")
        s44 = ("PEqualNP.Represents.RepSizeAtMost "
               "(fun u v : Fin 4 => (123 : ℕ).testBit (4 * u.val + v.val)) 9")
        self.assertEqual(gen.parse(s45)[:3], ("matrix",4,5))
        self.assertEqual(gen.parse(s44)[:3], ("matrix",4,4))
        found = plugins.discover()
        name,old45 = plugins.family_of(s45,found)
        self.assertEqual(name,"promise")
        old44 = plugins.family_of(s44,found)[1]
        old_batch = batch.version()
        p = stock_index.path_for(gen.parse(s45))
        p.write_bytes(b"candidate")
        new = plugins.discover()
        new45 = plugins.family_of(s45,new)[1]
        self.assertNotEqual(old45,new45)
        self.assertEqual(old44,plugins.family_of(s44,new)[1])
        self.assertEqual(old_batch,batch.version())
        self.assertEqual(old45,plugins.family_of(s45,found)[1])
        with patch.object(autosolve,"status",return_value="unsupported plugin promise "+old45+" rc=3"):
            self.assertFalse(autosolve.fresh("L-meta-99",old45))
            self.assertTrue(autosolve.fresh("L-meta-99",new45))
        p.unlink()
        self.assertEqual(old45,plugins.family_of(s45,plugins.discover())[1])

    def test_dependency_update_reloads_generator_worker(self):
        from missions.pnp.lbcert import autosolve
        source = Path(self.tmp.name)/"worker.py"
        dependency = Path(self.tmp.name)/"dependency.py"
        source.write_text("old")
        dependency.write_text("old")
        with patch.object(autosolve,"SOURCE_FILES",(source,dependency)):
            initial=autosolve.source_digest()
            with patch.object(autosolve,"START_HASH",initial):
                self.assertFalse(autosolve.source_changed())
                dependency.write_text("new")
                self.assertTrue(autosolve.source_changed())
                dependency.write_text("old")
                self.assertFalse(autosolve.source_changed())

    def test_index_change_invalidates_batch_version(self):
        old=batch.version()
        p=stock_index.path_for(("two",6,6,0,0,"FanInTwo"))
        p.write_bytes(b"new")
        self.assertNotEqual(old,batch.version())


if __name__=="__main__":
    unittest.main()

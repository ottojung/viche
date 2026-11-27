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

    def test_index_change_invalidates_batch_version(self):
        old=batch.version()
        p=stock_index.path_for(("two",6,6,0,0,"FanInTwo"))
        p.write_bytes(b"new")
        self.assertNotEqual(old,batch.version())


if __name__=="__main__":
    unittest.main()

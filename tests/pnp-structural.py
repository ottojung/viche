#!/usr/bin/env python3
"""Offline regression tests for the reusable bit-reflection structural generator."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
import unittest

from missions.pnp import validate
from missions.pnp.structural import bitpack, extract, oracle

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "records/pnp-structural-20261128/extracted/L_meta_17487.lean"

# Instances used while developing the generator.
DEV = [(13, [0, 1, 3, 9]), (7, [0, 1, 3])]
# Held out: different plane orders / difference sets, never used in development.
HELD_OUT = [(21, [0, 1, 4, 14, 16]), (5, [0, 1]),
            (9, [0, 1, 3]), (31, [0, 1, 3, 8, 12, 18]), (3, [0, 1])]


def meta_for(n, diffs, gid="L-meta-17487"):
    module = "PEqualNP.Outside.L_meta_struct_%d" % n
    return {"id": gid, "file": "lean/PEqualNP/Outside/L_meta_struct_%d.lean" % n,
            "module": module, "statement": bitpack.statement_for(n, diffs),
            "imports": ["PEqualNP.Defs"]}


class Structural(unittest.TestCase):
    def test_generic_block_is_exact_upstream_extraction(self):
        src = FIXTURE.read_text(encoding="utf-8")
        upstream = extract.generic_block(src).replace("theorem ", "lemma ").rstrip()
        self.assertEqual(upstream, bitpack.GENERIC_BLOCK.rstrip())
        self.assertEqual(extract.PINNED_BLOB, "1052b76494a2972ca5ee978fd4dfa6e60b9bd302")
        self.assertEqual(extract.LICENSE, "Apache-2.0")

    def test_recognition_is_full_statement(self):
        for n, diffs in DEV + HELD_OUT:
            s = bitpack.statement_for(n, diffs)
            self.assertEqual(bitpack.recognize(s), (n, diffs))
        self.assertIsNone(bitpack.recognize("A step toward: at least 64 gates"))
        self.assertIsNone(bitpack.recognize(bitpack.statement_for(13, [0, 1, 3, 9])[:-20]))

    def _check(self, n, diffs):
        meta = meta_for(n, diffs)
        rep = bitpack.candidate(meta)
        self.assertEqual(rep["result"], "candidate", rep)
        self.assertTrue(rep["oracle_identity"]["verified"])
        self.assertTrue(rep["oracle_lemmas"]["verified"])
        self.assertFalse(rep["local_lean_checked"])
        self.assertFalse(rep["desk_credit_claimed"])
        text = rep["candidate"]
        self.assertEqual(validate.validate(meta, text.encode("utf-8")), rep["sha256"])
        self.assertEqual(text.count("\ntheorem "), 1)
        self.assertTrue(text.count("\nlemma ") >= 5)
        self.assertIn("licensed Apache-2.0", text)
        self.assertIn("import PEqualNP.Defs", text)
        return rep

    def test_development_instances(self):
        for n, diffs in DEV:
            self._check(n, diffs)

    def test_held_out_instances(self):
        for n, diffs in HELD_OUT:
            self._check(n, diffs)

    def test_refuses_the_five_named_deep_targets(self):
        """The named unmatched steps are not this generator's shape: no false proof."""
        cat = ROOT.parent / "wd/viche-state/pnp/cache/proof-catalog.json"
        # Suite env isolates PnP state; the fixture catalogue is optional.
        fixture = ROOT / "records/pnp-structural-20261128/targets.json"
        if not fixture.exists() and cat.exists():
            fixture = cat
        if not fixture.exists():
            self.skipTest("no statement catalogue available in this environment")
        data = json.loads(fixture.read_text(encoding="utf-8"))
        rows = data["gaps"] if isinstance(data, dict) else data
        by_id = {r["id"]: r for r in rows if "id" in r}
        for gid in ("L-meta-6136", "L-meta-6648", "L-meta-8101",
                    "L-meta-7798", "L-meta-8217"):
            r = by_id.get(gid)
            if not r or "statement" not in r:
                continue
            meta = {"id": gid, "file": r["file"], "module": r["module"],
                    "statement": r["statement"], "imports": r.get("imports", [])}
            rep = bitpack.candidate(meta)
            self.assertEqual(rep["result"], "not-recognized", gid)

    def test_invalid_parameters_rejected(self):
        for n, diffs in [(1, [0]), (13, []), (13, [0, 0]), (13, [13]), (13, [-1])]:
            with self.assertRaises(ValueError):
                bitpack.params(n, diffs)
        self.assertFalse(oracle.verify_identity(1, [0], trials=5)["verified"])
        self.assertFalse(bitpack.recognize(""))


if __name__ == "__main__":
    unittest.main()

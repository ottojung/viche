import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from missions.pnp.lbcert.generators.pm3lower import gen
from missions.pnp.validate import validate

class LowerBound(unittest.TestCase):
    def test_prefix_independent(self):
        _,s=gen.template()
        for k in (11,12):
            for op in ("and, [1, 3]","or, [0, 9]","not, [0]"):
                q=s.replace("C.size ≤ 12",f"C.size ≤ {k}").replace("GateOp.or, [2, 9]","GateOp."+op)
                self.assertTrue(gen.matches(q))
                gid="L-meta-27438";module="PEqualNP.Outside.L_meta_27438"
                m=dict(id=gid,module=module,file="lean/PEqualNP/Outside/L_meta_27438.lean",imports=["PEqualNP.Defs"],statement=q)
                self.assertEqual(len(validate(m,gen.generate(gid,q).encode())),64)
    def test_reject_outside_proved_bound_or_shape(self):
        _,s=gen.template()
        self.assertFalse(gen.matches(s.replace("≤ 12","≤ 13")))
        self.assertFalse(gen.matches(s[2:]))
        self.assertFalse(gen.matches(s.replace("x 0 && x 4 && x 8","x 0 && x 4 && x 7")))
        self.assertIsNone(gen.generate("L-pcx-1",s))
    def test_outer_parentheses(self):
        _,s=gen.template()
        self.assertTrue(gen.matches("( ("+s+") )"))

if __name__=="__main__":unittest.main()

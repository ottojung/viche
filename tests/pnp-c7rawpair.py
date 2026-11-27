import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp.lbcert.generators.c7rawpair import gen
from missions.pnp import validate

class TestC7(unittest.TestCase):
    def test_all_raw_cases(self):
        for i in range(9):
            for a in range(2,6):
                s=gen.shape.replace('i.val = 0',f'i.val = {i}',1)
                s=s.replace('2 ∈ (C.gates.get i).inputs ∧ 2 ≠ 0 ∧ 2 < 7 + i.val',f'{a} ∈ (C.gates.get i).inputs ∧ {a} ≠ 0 ∧ {a} < 7 + i.val')
                s=s.replace('getD 2 false = true',f'getD {a} false = true')
                self.assertTrue(gen.matches(s))
                gid='L-meta-29784';mod='PEqualNP.Outside.L_meta_29784'
                validate.validate(dict(id=gid,statement=s,module=mod,file='lean/PEqualNP/Outside/L_meta_29784.lean',imports=['PEqualNP.Defs']),gen.generate(gid,s).encode())
    def test_refusals(self):
        self.assertFalse(gen.matches(gen.shape[2:]))
        self.assertFalse(gen.matches(gen.shape.replace('getD 2 false','getD 3 false')))
        self.assertFalse(gen.matches(gen.shape.replace('GateOp.or','GateOp.and')))
        self.assertIsNone(gen.generate('L-pcx-1',gen.shape))
    def test_pair_truth(self):
        f=lambda r:any(r&(1<<i) and r&(1<<((i+1)%7)) for i in range(7))
        for a in range(2,6):
            b=6 if a==2 else 1
            x=(1<<a)|(1<<b)
            self.assertFalse(f(x));self.assertTrue(f(x|1))
if __name__=='__main__':unittest.main()

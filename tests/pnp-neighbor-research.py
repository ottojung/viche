import importlib.util
import itertools
from pathlib import Path
import random
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
def mod(name,path):
    s=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
N=mod('neighbor',ROOT/'missions/pnp/lbcert/research/neighbor/run.py')
R=mod('repair',ROOT/'missions/pnp/lbcert/research/rectangles/repair.py')
F=mod('floors',ROOT/'missions/pnp/lbcert/research/screen128/floors.py')

class Research(unittest.TestCase):
    def test_remapping(self):
        rng=random.Random(628)
        for _ in range(50):
            g=[(rng.randrange(6+i),rng.randrange(6+i),rng.randrange(2)) for i in range(12)]
            m=N.evaluate(g);p=rng.sample(range(6),6)
            mm=N.move(m,p)
            for dual in (False,True):
                a=N.dual(mm) if dual else mm
                # The native result is in the transformed basis. Convert back.
                inv=[p.index(i) for i in range(6)]
                h=N.remap(g,inv,dual)
                self.assertEqual(N.evaluate(h),a)
                self.assertEqual(N.evaluate(N.remap(h,p,dual)),m)
    def test_repair_oracle(self):
        rng=random.Random(627)
        for _ in range(50):
            target=255
            a=[rng.randrange(1,256) for i in range(9)]
            a.extend([1<<i for i in range(8)])
            r=R.Repair(a,target,10)
            for k in (1,2,3):
                expected=any(not (target&~self.union(a,c)) for c in itertools.combinations(range(len(a)),k))
                result=r.solve(target,k)
                self.assertEqual(result is not None,expected)
                if result is not None:
                    self.assertLessEqual(len(result),k)
                    self.assertEqual(self.union(a,result),target)
    @staticmethod
    def union(a,ids):
        out=0
        for i in ids:out|=a[i]
        return out
    def test_floor_transport(self):
        for m in range(16):
            for p in itertools.permutations(range(2)):
                a=sum(1<<sum(((r>>i)&1)<<p[i] for i in range(2)) for r in range(4) if m>>r&1)
                self.assertEqual(F.canon(m,2),F.canon(a,2))
                self.assertEqual(F.canon(m,2),F.canon(F.dual(m,2),2))
    def test_slice(self):
        m=N.ROOTS[0]&N.ROOTS[2]|N.ROOTS[5]
        for i in range(6):
            for b in (0,1):
                f=F.slice_(m,6,i,b)
                for r in range(32):
                    row=(r&((1<<i)-1))|((r>>i)<<(i+1))|(b<<i)
                    self.assertEqual(f>>r&1,m>>row&1)
if __name__=='__main__':unittest.main()

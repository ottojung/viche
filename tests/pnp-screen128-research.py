"""Untrusted screen parity and independent full truth-table oracle."""
import itertools
import os
from pathlib import Path
import random
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'missions/pnp/lbcert/research/screen128/screen.c'
OLD=ROOT/'missions/pnp/lbcert/onenot/lsearch.c'

def input_for(n, mask, pairs, k, limit=100000):
    p=len(pairs); rows=[a for a,b in pairs]+[b for a,b in pairs]
    full=(1<<(2*p))-1
    words=[full^sum(((r>>i)&1)<<j for j,r in enumerate(rows)) for i in range(n)]
    return f'{n} {p} {k} {limit}\n'+'\n'.join(f'{w:x}' for w in words)+'\n'

def brute(n,k):
    full=(1<<(1<<n))-1
    def can(w):return w^full if w&1 else w
    roots=frozenset(can(sum(((r>>i)&1)<<r for r in range(1<<n))) for i in range(n))
    states={roots};hits=set(roots)
    for _ in range(k):
        ns=set()
        for wires in states:
            for a,b in itertools.combinations(wires,2):
                for w in (a&b,a|b,a&~b,b&~a):
                    c=can(w)
                    if c and c not in wires:
                        ns.add(wires|{c});hits.add(c)
        states=ns
    return hits|{x^full for x in hits}

class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.new=Path(cls.tmp.name)/'new';cls.old=Path(cls.tmp.name)/'old'
        for src,out in ((SRC,cls.new),(OLD,cls.old)):
            subprocess.run(['cc','-O2','-o',str(out),str(src)],check=True,timeout=60)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def run_screen(self,bin,inp):
        return subprocess.run([str(bin)],input=inp,text=True,capture_output=True,check=True,timeout=20,
                env={**os.environ,'LSEARCH_PAIRS_ONLY':'1'}).stdout.strip()
    def test_small_oracle(self):
        # All nonconstant 3-variable complement classes, at budgets 1 and 3.
        # Every assignment of differing polarity is paired: no sampling gap.
        for k in (1,3):
            hits=brute(3,k)
            for mask in range(2,255,2):
                pairs=[(x,y) for x in range(8) if mask>>x&1 for y in range(8) if not mask>>y&1]
                inp=input_for(3,mask,pairs,k)
                self.assertEqual(self.run_screen(self.new,inp),'found' if mask in hits else 'none',(mask,k))
    def test_old_parity(self):
        rng=random.Random(819)
        for _ in range(24):
            mask=rng.randrange(1,65535)
            pairs=[(x,y) for x in range(16) if mask>>x&1 for y in range(16) if not mask>>y&1]
            rng.shuffle(pairs);pairs=pairs[:64]
            inp=input_for(4,mask,pairs,rng.randrange(1,5))
            a=self.run_screen(self.old,inp);b=self.run_screen(self.new,inp)
            self.assertEqual(a,b,(mask,a,b))
    def test_width_guard(self):
        self.assertEqual(self.run_screen(self.new,'6 65 3 100\n'),'toolarge')

if __name__=='__main__':unittest.main()

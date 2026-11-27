"""Small residual lower bounds, used only to construct Lean certificates."""
import itertools
from functools import lru_cache

class Refinement:
    def __init__(self, bounds, data):
        self.b=bounds
        self.data=data
        self.index=None
        self.lower=lru_cache(maxsize=250000)(self._lower)

    def find(self,f):
        n=self.b.active(f).bit_count()
        if n not in (5,6):return None
        if self.index is None:
            index={}
            for key,row in self.data.items():
                masks=tuple(map(int,key.split(';')))
                k=max(t.bit_length() for t in masks)
                for p in itertools.permutations(range(8),k):
                    mapped=tuple(sorted(sum(1<<p[i] for i in range(k) if t>>i&1) for t in masks))
                    if mapped not in index or index[mapped][0]['bound']<row['bound']:
                        index[mapped]=(row,p)
            self.index=index
        return self.index.get(f)

    def _lower(self,f):
        b=self.b;vs=b.indices(b.active(f))
        if len(vs)<=1:return 0,('zero',)
        R={(i,c):b.rest(f,i,c) for i in vs for c in (False,True)}
        B={ic:self.lower(g)[0] for ic,g in R.items()}
        base=self.find(f)
        best=(base[0]['bound'],('base',)) if base else (0,('zero',))
        for i in vs:
            for c in (False,True):
                if b.nonconstant(R[i,c]) and B[i,c]+1>best[0]:
                    best=(B[i,c]+1,('one',i,c))
            if all(b.nonconstant(R[i,c]) for c in (False,True)):
                v=min(B[i,False],B[i,True])+2
                if v>best[0]:best=(v,('two',i))
        def opt(i,j,s,u):
            if not b.active(R[j,not u])>>i&1:return 0
            return max((B[i,c]+delta for c,delta in ((not s,3),(s,2)) if b.nonconstant(R[i,c])),default=0)
        v=min(max(opt(i,j,s,u),opt(j,i,u,s)) for i,j in itertools.combinations(vs,2) for s,u in itertools.product((False,True),repeat=2))
        return (v,('three',)) if v>best[0] else best

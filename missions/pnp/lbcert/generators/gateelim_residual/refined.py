"""Small residual lower bounds, used only to construct Lean certificates."""
import itertools
from functools import lru_cache

def describe(f):
    """Degree/singleton invariants for a normalized OR of variables and edges."""
    vs=tuple(sorted({i for t in f for i in range(t.bit_length()) if t>>i&1}))
    if any(t.bit_count() not in (1,2) for t in f):return None
    singleton={t.bit_length()-1 for t in f if t.bit_count()==1}
    adj={i:set() for i in vs}
    for t in f:
        if t.bit_count()==2:
            i,j=[i for i in vs if t>>i&1]
            adj[i].add(j);adj[j].add(i)
    colors={i:(i in singleton,len(adj[i]),tuple(sorted(len(adj[j]) for j in adj[i]))) for i in vs}
    return vs,adj,colors


def signature(d):
    return tuple(sorted(d[2].values()))


def mapping(source,target):
    """Exact isomorphism, after inexpensive necessary invariants."""
    sv,sa,sc=source;tv,ta,tc=target
    options={i:tuple(j for j in tv if sc[i]==tc[j]) for i in sv}
    order=sorted(sv,key=lambda i:(len(options[i]),-len(sa[i]),i))
    m={}
    def search(k):
        if k==len(order):return tuple(m[i] for i in sv)
        i=order[k]
        for j in options[i]:
            if j in m.values() or any((x in sa[i])!=(y in ta[j]) for x,y in m.items()):continue
            m[i]=j
            hit=search(k+1)
            if hit is not None:return hit
            del m[i]
        return None
    return search(0)


class Refinement:
    def __init__(self, bounds, data):
        self.b=bounds
        self.data=data
        self.index={}
        for key,row in data.items():
            masks=tuple(map(int,key.split(";")))
            desc=describe(masks)
            if desc is None or desc[0]!=tuple(range(len(desc[0]))):
                raise ValueError("noncanonical base variables")
            self.index.setdefault(signature(desc),[]).append((row,desc))
        for group in self.index.values():
            group.sort(key=lambda x:-x[0]["bound"])
        self.lower=lru_cache(maxsize=250000)(self._lower)
        self.find=lru_cache(maxsize=100000)(self._find)

    def _find(self,f):
        if self.b.active(f).bit_count() not in (5,6,7):return None
        d=describe(f)
        if d is None:return None
        for row,desc in self.index.get(signature(d),()):
            p=mapping(desc,d)
            if p is not None:return row,p
        return None

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

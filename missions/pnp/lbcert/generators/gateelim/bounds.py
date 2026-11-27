"""Recursive monotone-function gate elimination, proof plan only."""
from functools import lru_cache
from itertools import combinations,product
from collections import Counter
import json,time

def normalize(terms):
    t=sorted(set(terms),key=lambda t:(t.bit_count(),t));out=[]
    for m in t:
        if not any(x&m==x for x in out):out.append(m)
    return tuple(sorted(out))

@lru_cache(maxsize=250000)
def active(f):
    u=0
    for t in f:u|=t
    return u

@lru_cache(maxsize=500000)
def rest(f,i,c):
    m=1<<i
    return normalize(t&~m for t in f if c or not t&m)

def indices(mask):
    return [i for i in range(mask.bit_length()) if mask>>i&1]

def nonconstant(f):
    return bool(f and f!=(0,))

@lru_cache(maxsize=250000)
def lower(f):
    vs=indices(active(f))
    if len(vs)<=1:return 0,('zero',)
    R={(i,c):rest(f,i,c) for i in vs for c in (False,True)}
    B={ic:lower(g)[0] for ic,g in R.items()}
    best=(0,('zero',))
    for i in vs:
        for c in (False,True):
            if nonconstant(R[i,c]) and B[i,c]+1>best[0]:best=(B[i,c]+1,('one',i,c))
        if all(nonconstant(R[i,c]) for c in (False,True)):
            b=min(B[i,False],B[i,True])+2
            if b>best[0]:best=(b,('two',i))
    def opt(i,j,s,u):
        if not active(R[j,not u])>>i&1:return 0
        return max((B[i,c]+delta for c,delta in ((not s,3),(s,2)) if nonconstant(R[i,c])),default=0)
    opts=[]
    for i,j in combinations(vs,2):
        for s,u in product((False,True),repeat=2):
            opts.append(max(opt(i,j,s,u),opt(j,i,u,s)))
    b=min(opts)
    if b>best[0]:best=(b,('three',))
    return best

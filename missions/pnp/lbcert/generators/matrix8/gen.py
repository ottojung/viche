"""Exact public-witness relabeling for 8x8 one-hot matrices.

Derived gate data from merged upstream, Apache-2.0; see README.md.
Never claims a lease or a compiler receipt.
"""
import itertools
import hashlib
import json
import sys
from pathlib import Path
from functools import lru_cache

# Also runnable directly by the normal plugin process.
sys.path.insert(0,str(Path(__file__).resolve().parents[5]))
from missions.pnp.lbcert.generators.promise import gen as promise

def sigs(rows):
    cols=[sum(1<<i for i,r in enumerate(rows) if r>>j&1) for j in range(8)]
    cs=[(a.bit_count(),tuple(sorted((a&b).bit_count() for b in cols))) for a in cols]
    rs=[(a.bit_count(),tuple(sorted((a&b).bit_count() for b in rows))) for a in rows]
    # Alternating color refinement with incidence and pair-intersection types.
    for _ in range(2):
        cs=[(cs[j],tuple(sorted(rs[i] for i,r in enumerate(rows) if r>>j&1))) for j in range(8)]
        cs=[sorted(set(cs)).index(s) for s in cs]
        rs=[(rs[i],tuple(sorted(cs[j] for j in range(8) if r>>j&1))) for i,r in enumerate(rows)]
        rs=[sorted(set(rs)).index(s) for s in rs]
    return cs

@lru_cache(maxsize=40320)
def translate(perm):
    t=[0]*256
    for x in range(1,256):
        low=x&-x;t[x]=t[x^low]|1<<perm[low.bit_length()-1]
    return bytes(t)

@lru_cache(maxsize=1024)
def canon(mask):
    rows=[mask>>(8*i)&255 for i in range(8)]
    colors=sigs(rows)
    groups=[[j for j,c in enumerate(colors) if c==k] for k in sorted(set(colors))]
    best=None;mapping=None;count=0
    for chunks in itertools.product(*(itertools.permutations(g) for g in groups)):
        cp=sum(chunks,())
        inv=tuple(cp.index(j) for j in range(8))
        table=translate(inv)
        rr=[table[r] for r in rows]
        rp=sorted(range(8),key=lambda i:rr[i])
        z=bytes(rr[i] for i in rp)
        count+=1
        if best is None or z<best:best=z;mapping=tuple(rp)+tuple(8+j for j in cp)
    return best.hex(),mapping


# Pin the reviewed data; changes to it require a new plugin version.
DATA_SHA256 = "b3fcf137821ec9d3305255962ab1f31665330e6a41ade7e2ef1f21fce4006b15"

@lru_cache(maxsize=1)
def library():
    try:
        raw=Path(__file__).with_name("witnesses.json").read_bytes()
        if hashlib.sha256(raw).hexdigest()!=DATA_SHA256:return {}
        return json.loads(raw)["classes"]
    except (OSError,ValueError,KeyError,TypeError):return {}


def parse(statement):
    s=" ".join(statement.split())
    while s.startswith("(") and s.endswith(")"):s=s[1:-1].strip()
    p=promise.parse(s)
    return p if p and p[:3]==("matrix",8,8) else None


@lru_cache(maxsize=512)
def lookup(p):
    if not p:return None
    key,mp=canon(p[4]&((1<<64)-1))
    entry=library().get(key)
    if not entry:return None
    try:
        gates,out=entry["solution"]
        if len(gates)>p[3] or not 0<=out<16+len(gates):return None
        def wire(w):return mp[w] if 0<=w<16 else w
        sol=([(op,[wire(w) for w in args]) for op,args in gates],wire(out))
        return sol if promise.valid(p,sol) else None
    except (AssertionError,IndexError,TypeError,KeyError,ValueError):return None


def matches(statement):
    return lookup(parse(statement)) is not None


def main():
    if len(sys.argv)!=4:return 2
    gid,sf,out=sys.argv[1:]
    statement=Path(sf).read_text().strip()
    p=parse(statement)
    sol=lookup(p)
    if sol is None:return 3
    # Emit exact desk proposition through the existing independent emitter.
    # This is candidate generation, never a kernel receipt.
    Path(out).write_text(promise.emit(gid,statement,p,sol))
    return 0


if __name__=="__main__":raise SystemExit(main())

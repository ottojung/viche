"""Exact public-witness reuse for 2–5 by 2–5 one-hot matrices."""
import hashlib
import json
from functools import lru_cache
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[5]))
from missions.pnp.lbcert.generators.promise import gen as promise

DATA_SHA256 = "5d42872b1f64777e9ff3a57b56c298448cdd245e33b7f20e6f6a6a7d0d135429"


@lru_cache(maxsize=1)
def library():
    try:
        raw=Path(__file__).with_name("witnesses.json").read_bytes()
        if hashlib.sha256(raw).hexdigest()!=DATA_SHA256:return {}
        return json.loads(raw)["classes"]
    except (OSError,ValueError,TypeError,KeyError):return {}


def parse(statement):
    p=promise.parse(statement)
    return p if p and p[0]=="matrix" and all(2<=n<=5 for n in p[1:3]) else None


def direct(p):
    key,mp=promise.iso_key(p)
    entry=library().get(":".join(map(str,key[1:]))+":"+p[-1])
    if not entry:return None
    try:
        gates,out=entry["solution"]
        if len(gates)>p[3] or not 0<=out<len(mp)+len(gates):return None
        def w(i):return mp[i] if 0<=i<len(mp) else i
        sol=([(op,[w(i) for i in args]) for op,args in gates],w(out))
        return sol if promise.valid(p,sol) else None
    except (TypeError,ValueError,AssertionError,IndexError,KeyError):return None


def transpose(p):
    kind,n,m,k,mask,pred=p
    z=sum((mask>>(i*m+j)&1)<<(j*n+i) for i in range(n) for j in range(m))
    return (kind,m,n,k,z,pred)


@lru_cache(maxsize=512)
def lookup(p):
    if not p:return None
    result=direct(p)
    if result is not None:return result
    result=direct(transpose(p))
    if result is None:return None
    n,m=p[1:3]
    def w(i):return i+n if i<m else i-m if i<m+n else i
    gates,out=result
    sol=([(op,[w(i) for i in args]) for op,args in gates],w(out))
    return sol if promise.valid(p,sol) else None


def matches(statement):
    return lookup(parse(statement)) is not None


def main():
    if len(sys.argv)!=4:return 2
    gid,sf,out=sys.argv[1:]
    stmt=Path(sf).read_text().strip()
    p=parse(stmt)
    sol=lookup(p)
    if sol is None:return 3
    Path(out).write_text(promise.emit(gid,stmt,p,sol))
    return 0


if __name__=="__main__":raise SystemExit(main())

"""Generate untrusted lower-floor hints for projected live-set screening.

Each result 'none' on any opposite-label pair sample is a screen hint only.
A hash collision could give a false negative. No formal certificate here.
"""
import itertools,collections,subprocess,json,sys,time
from pathlib import Path
from functools import lru_cache

def slice_(m,n,i,b):
    return sum(((m>>((r&((1<<i)-1))|((r>>i)<<(i+1))|(b<<i)))&1)<<r
               for r in range(1<<(n-1)))

def dual(m,n):
    return ((1<<(1<<n))-1)^int(f'{m:0{1<<n}b}'[::-1],2)

@lru_cache(maxsize=None)
def canon(m,n):
    if n==0:return 0
    best=m
    for order in itertools.permutations(range(n)):
        a=sum(1<<sum(((r>>i)&1)<<order[i] for i in range(n)) for r in range(1<<n) if m>>r&1)
        best=min(best,a,dual(a,n))
    return best

def critical(m,n):
    return [(r,r^(1<<i)) for r in range(1<<n) if m>>r&1
            for i in range(n) if r>>i&1 and not m>>(r^(1<<i))&1]

def input_(m,n,k,cap):
    pairs=critical(m,n);p=len(pairs)
    rows=[a for a,b in pairs]+[b for a,b in pairs]
    words=[sum(((r>>i)&1)<<j for j,r in enumerate(rows)) for i in range(n)]
    return f'{n} {p} {k} {cap}\n'+'\n'.join(f'{w:x}' for w in words)+'\n'

def screen(exe,m,n,k,cap=300000,seconds=3):
    try:
        q=subprocess.run([exe],input=input_(m,n,k,cap),text=True,capture_output=True,timeout=seconds,check=True)
        return q.stdout.strip()
    except (subprocess.SubprocessError,OSError):
        return 'timeout'

def floor(exe,m,n,cache):
    F=(1<<(1<<n))-1
    if m in (0,F):return 0
    key=(n,canon(m,n))
    if key in cache:return cache[key]
    # Remove nonessential variables; a free-negation basis is invariant under dummy inputs.
    pairs=[(slice_(m,n,i,0),slice_(m,n,i,1)) for i in range(n)]
    for a,b in pairs:
        if a==b:
            cache[key]=floor(exe,a,n-1,cache)
            return cache[key]
    # Every essential variable must be connected; n-1 is an unconditional floor.
    lo=max(0,n-1)
    if n>1:
        for a,b in pairs:
            if a not in (0,(1<<(1<<(n-1)))-1) or b not in (0,(1<<(1<<(n-1)))-1):
                lo=max(lo,1+max(floor(exe,a,n-1,cache),floor(exe,b,n-1,cache)))
            if a not in (0,(1<<(1<<(n-1)))-1) and b not in (0,(1<<(1<<(n-1)))-1):
                lo=max(lo,2+min(floor(exe,a,n-1,cache),floor(exe,b,n-1,cache)))
    # The two-gate rule needs both slices nonconstant (true for this monotone family).
    if n<=5:
        for k in range(lo,11):
            z=screen(exe,key[1],n,k)
            if z!='none':break
            lo=k+1
    cache[key]=lo
    return lo

if __name__=='__main__':
    exe,src,dest=sys.argv[1:4]
    cache={};out=[]
    for r in json.load(open(src)):
        m=r['mask'];a=[]
        for i in range(6):
            for b in (0,1):
                s=slice_(m,6,i,b);a.append((i,b,floor(exe,s,5,cache)))
        print(r['id'],len(r['gates']),a,'classes',len(cache),flush=True)
        out.append(dict(id=r['id'],mask=m,gates=r['gates'],floors=a))
        Path(dest).write_text(json.dumps(out))

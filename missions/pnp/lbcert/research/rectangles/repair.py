"""Exact bounded repair of a heuristic cover. Search refusal is not a proof."""
import itertools
import functools
import time

def bits(x):
    while x:
        b=x&-x
        yield b.bit_length()-1
        x-=b

class Repair:
    def __init__(self,masks,target,budget=30):
        self.masks=masks
        self.target=target
        self.deadline=time.monotonic()+budget
        self.n=len(masks)
        idx=[bytearray((self.n+7)//8) for _ in range(target.bit_length())]
        for j,m in enumerate(masks):
            if m&~target:raise ValueError("invalid rectangle")
            for i in bits(m):idx[i][j//8]|=1<<(j%8)
        self.index=[int.from_bytes(x,'little') for x in idx]
        self.order=sorted(bits(target),key=lambda i:self.index[i].bit_count())
        self.all=(1<<self.n)-1

    def one(self,u):
        ix=self.all
        for i in bits(u):
            ix&=self.index[i]
            if not ix:return None
        return (ix&-ix).bit_length()-1 if ix else None

    @functools.lru_cache(maxsize=100000)
    def solve(self,u,k):
        if not u:return ()
        if time.monotonic()>self.deadline:raise TimeoutError
        if k<1:return None
        j=self.one(u)
        if j is not None:return (j,)
        if k==1:return None
        c=next(i for i in self.order if u>>i&1)
        # Deduplicate residual coverage, retain the candidate with largest gain first.
        residual={}
        for j in bits(self.index[c]):
            v=u&~self.masks[j]
            residual.setdefault(v,j)
        for v,j in sorted(residual.items(),key=lambda e:e[0].bit_count()):
            r=self.solve(v,k-1)
            if r is not None:return (j,*r)
        return None

    def repair(self,selected,depth=3):
        for k in range(1,depth+1):
            for drop in itertools.combinations(range(len(selected)),k):
                keep=[j for i,j in enumerate(selected) if i not in drop]
                u=self.target
                for j in keep:u&=~self.masks[j]
                r=self.solve(u,k)
                if r is not None:return keep+list(r)
        return None

if __name__=='__main__':
    import sys,struct,json
    data=open(sys.argv[1],'rb').read()
    n,k=struct.unpack_from('<II',data)
    target=int.from_bytes(data[8:64],'little')
    masks=[int.from_bytes(data[64+i*56:120+i*56],'little') for i in range(n)]
    a=open(sys.argv[2]).read().splitlines()
    best=min((l.split() for l in a if l.startswith('step ') and len(l.split())==4+k),key=lambda a:int(a[3]))
    selected=list(map(int,best[4:]))
    r=Repair(masks,target,float(sys.argv[3]))
    print('repair',best[:4],flush=True)
    try:sol=r.repair(selected,3)
    except TimeoutError:sol=None
    print('result',sol,'cache',r.solve.cache_info(),flush=True)
    if sol is not None:
        u=target
        for j in sol:u&=~masks[j]
        assert not u and len(sol)<=k
        print(json.dumps(sol))

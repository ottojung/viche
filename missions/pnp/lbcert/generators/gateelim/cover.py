import random

def candidates(n,edges):
 adj=[0]*n
 ei={}
 for i,(a,b) in enumerate(edges):adj[a]|=1<<b;adj[b]|=1<<a;ei[a,b]=i;ei[b,a]=i
 vals=[tuple(i for i in range(n) if m>>i&1) for m in range(1<<n)]
 res=[]
 for a in range(1,1<<n):
  bmax=(1<<n)-1
  for v in vals[a]:bmax&=adj[v]
  b=bmax
  while b:
   if a<b:
    e=0
    for x in vals[a]:
     for y in vals[b]:e|=1<<ei[x,y]
    res.append((a,b,e))
   b=(b-1)&bmax
 return res,vals
def greedy(n,edges,build,trials=20):
 cs,vs=candidates(n,edges)
 rng=random.Random(1);best=None
 if not cs:return None
 for t in range(trials):
  avail=set(1<<i for i in range(n));rem=(1<<len(edges))-1;cover=[]
  def extra(a):
   k=max((s.bit_count() for s in avail if a&s==s),default=1)
   return a.bit_count()-k
  while rem:
   def score(c):
    a,b,e=c;hit=(e&rem).bit_count()
    if not hit:return -1
    cost=2+extra(a)+extra(b)
    return hit/cost*(1+(rng.random()-.5)*(.4 if t else 0))
   a,b,e=max(cs,key=score)
   cover.append((vs[a],vs[b],e,len(vs[a])+len(vs[b])))
   avail.update((a,b));rem&=~e
  g=build(n,cover)
  if best is None or len(g)<len(best):best=g
 return best

def build(n, cover):
    """Gates (a, b, tt) for the cover, OR sets shared; tt as in onenot (mono: and / or)."""
    gates = []
    AND = {0: 0, 1: 0, 2: 0, 3: 1}
    OR = {0: 0, 1: 1, 2: 1, 3: 1}
    memo = {}

    def orset(S):
        S = tuple(sorted(S))
        if len(S) == 1:
            return S[0]
        if S in memo:
            return memo[S]
        sub = max((T for T in memo if set(T) < set(S)), key=len, default=None)
        if sub is not None:
            cur = memo[sub]
            rest = [v for v in S if v not in sub]
        else:
            cur = S[0]
            rest = list(S[1:])
        for v in rest:
            gates.append((cur, v, OR) if cur < v else (v, cur, OR))
            cur = n + len(gates) - 1
        memo[S] = cur
        return cur

    terms = []
    for A, B, m, c in cover:
        a = orset(A)
        b = orset(B)
        gates.append((min(a, b), max(a, b), AND))
        terms.append(n + len(gates) - 1)
    cur = terms[0]
    for t in terms[1:]:
        gates.append((cur, t, OR))
        cur = n + len(gates) - 1
    return gates


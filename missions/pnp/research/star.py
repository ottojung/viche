"""Reusable exact star-cover construction and symbolic monotone verification.

Unlike truth-table enumeration, antichains represent the exact upward-closed
set of accepted inputs. Resource exhaustion is unknown, never a verdict.
"""
import argparse
import collections
import json
import time

class Deferred(Exception):pass

def normalize(n,edges):
    E={tuple(sorted(e)) for e in edges}
    if not 2<=n<=256 or not E or any(len(e)!=2 or not all(type(x) is int for x in e)
          or not 0<=e[0]<e[1]<n for e in E):
        raise ValueError("nonempty simple graph with 2–256 vertices required")
    return E

def bipartition(n,E):
    neighbors=[set() for _ in range(n)]
    for a,b in E:neighbors[a].add(b);neighbors[b].add(a)
    colors={}
    for root in range(n):
        if root in colors:continue
        colors[root]=0;queue=[root]
        for v in queue:
            for w in sorted(neighbors[v]):
                if w not in colors:colors[w]=1-colors[v];queue.append(w)
                elif colors[v]==colors[w]:return None
    return colors,neighbors

def bipartite_cover(n,E):
    part=bipartition(n,E)
    if part is None:return None
    colors,neighbors=part;L=sorted(v for v in range(n) if colors[v]==0);match={}
    def augment(v,seen):
        for w in sorted(neighbors[v]):
            if w in seen:continue
            seen.add(w)
            if w not in match or augment(match[w],seen):
                match[w]=v;return True
        return False
    for v in L:augment(v,set())
    reverse={v:w for w,v in match.items()}
    reachedL=set(v for v in L if v not in reverse);reachedR=set()
    queue=sorted(reachedL)
    for v in queue:
        for w in sorted(neighbors[v]):
            if reverse.get(v)==w or w in reachedR:continue
            reachedR.add(w)
            if w in match and match[w] not in reachedL:
                reachedL.add(match[w]);queue.append(match[w])
    cover=(set(L)-reachedL)|reachedR
    if len(cover)!=len(match) or not all(a in cover or b in cover for a,b in E):
        raise AssertionError("matching/cover certificate invalid")
    return cover,sorted((v,w) for w,v in match.items())

def general_cover(E,seconds=5):
    # Branch on an uncovered edge; a maximal disjoint matching supplies a
    # lower bound for each remaining subproblem. Retain an incumbent.
    deadline=time.monotonic()+seconds
    best=set(v for e in E for v in e)
    def greedy(edges):
        chosen=set()
        while edges:
            degrees=collections.Counter(v for e in edges for v in e)
            v=max(degrees,key=lambda x:(degrees[x],-x))
            chosen.add(v);edges={e for e in edges if v not in e}
        return chosen
    best=greedy(E)
    def search(edges,chosen):
        nonlocal best
        if time.monotonic()>deadline:raise Deferred()
        if not edges:
            if len(chosen)<len(best):best=chosen
            return
        if len(chosen)>=len(best):return
        used=set();lb=0
        for a,b in sorted(edges):
            if a not in used and b not in used:used.update((a,b));lb+=1
        if len(chosen)+lb>=len(best):return
        deg=collections.Counter(v for e in edges for v in e)
        a,b=max(edges,key=lambda e:(deg[e[0]]+deg[e[1]],e))
        for v in sorted((a,b),key=lambda x:(-deg[x],x)):
            search({e for e in edges if v not in e},chosen|{v})
    try:search(E,set());return best,True
    except Deferred:return best,False

def synthesize(n,edges,seconds=5):
    E=normalize(n,edges);pair=bipartite_cover(n,E)
    if pair is not None:cover,matching=pair;exact=True
    else:cover,exact=general_cover(E,seconds);matching=None
    stars={v:[] for v in sorted(cover)};owners=[]
    for a,b in sorted(E):
        v,w=(a,b) if a in cover else (b,a)
        stars[v].append(w);owners.append([a,b,v])
    gates=[]
    def gate(op,a,b):
        gates.append([op,a,b]);return n+len(gates)-1
    def disjoin(xs):
        r=xs[0]
        for x in xs[1:]:r=gate("or",r,x)
        return r
    outs=[gate("and",v,disjoin(ns)) for v,ns in stars.items() if ns]
    output=disjoin(outs)
    return {"n":n,"edges":[list(e) for e in sorted(E)],"cover":sorted(cover),"owners":owners,
            "matching":matching,"minimum_cover_proved_by_search":exact,
            "gates":gates,"output":output,"star_bound":len(E)+len(cover)-1}

def minimal(terms,limit):
    out=[]
    for x in sorted(set(terms),key=lambda x:(x.bit_count(),x)):
        if not any((x&y)==y for y in out):
            out.append(x)
            if len(out)>limit:raise Deferred()
    return out

def verify(n,edges,gates,output,limit=20000):
    E=normalize(n,edges);w=[[1<<i] for i in range(n)]
    try:
        for op,a,b in gates:
            if op not in ("or","and") or type(a) is not int or type(b) is not int or not 0<=a<len(w) or not 0<=b<len(w):
                return {"status":"invalid_circuit"}
            if op=="and" and len(w[a])*len(w[b])>limit*4:raise Deferred()
            w.append(minimal(w[a]+w[b] if op=="or" else (x|y for x in w[a] for y in w[b]),limit))
        if type(output) is not int or not 0<=output<len(w):return {"status":"invalid_circuit"}
        actual=set(w[output]);expected={(1<<a)|(1<<b) for a,b in E}
        if actual!=expected:
            candidates=sorted(actual^expected,key=lambda x:(x.bit_count(),x))
            for x in candidates:
                got=any(x&y==y for y in actual);want=any(x&y==y for y in expected)
                if got!=want:return {"status":"counterexample","input":x,"actual":got,"expected":want}
            raise AssertionError("distinct antichains must differ")
        return {"status":"verified","minimal_true_sets":len(actual),"max_wire_antichain":max(map(len,w))}
    except Deferred:return {"status":"unknown","reason":"antichain resource bound"}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("graph");p.add_argument("--seconds",type=float,default=5)
    a=p.parse_args()
    with open(a.graph) as f:d=json.load(f)
    cert=synthesize(d["n"],d["edges"],a.seconds)
    cert["verification"]=verify(cert["n"],cert["edges"],cert["gates"],cert["output"])
    print(json.dumps(cert,indent=2))
    return 0 if cert["verification"]["status"]=="verified" else 1

if __name__=="__main__":raise SystemExit(main())

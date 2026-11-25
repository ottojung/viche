"""Exact monotone bipartite neighborhood-bank row reduction.

For each nonisolated left vertex p, require output true on every incident
pair {p,l}, false on every independent input containing p. Every independent
input extends to a maximal independent set; monotonicity then gives the
negative condition from maximal rows. For an exact OR output, its singleton
positives and maximal false complement suffice. The optional group demands
that at least one incident line singleton is rejected by its point output.
"""
from . import rows

def generate(raw):
    if not isinstance(raw,dict) or set(raw)-{"n","left","edges","gates","or_output","require_masked_edge"}:
        raise ValueError("invalid bank specification")
    n=raw.get("n");left=raw.get("left")
    if type(n) is not int or not 1<=n<=64 or not rows._indices(left,n) or len(set(left))!=len(left) or len(left)>16:
        raise ValueError("left side must have at most 16 distinct vertices")
    right=set(range(n))-set(left); left=sorted(left);L=set(left)
    edges=raw.get("edges")
    if not isinstance(edges,list) or any(not rows._indices(e,n) or len(e)!=2 or e[0] not in L or e[1] not in right for e in edges):
        raise ValueError("edges must be [left,right]")
    N={p:set() for p in left}
    for p,l in edges:N[p].add(l)
    # For every subset S of L, take all R not adjacent to S, then close L.
    # This is a maximal independent set. All maximal independent sets occur.
    maximal=set()
    for m in range(1<<len(left)):
        selected={p for i,p in enumerate(left) if m>>i&1}
        free=right-set().union(*(N[p] for p in selected))
        closed={p for p in left if not (N[p]&free)}
        maximal.add(sum(1<<v for v in closed|free))
    outputs=[];group=[]
    for p in left:
        if not N[p]:continue
        j=len(outputs)
        outputs.append({"name":"point_"+str(p),"ones":[(1<<p)|(1<<l) for l in sorted(N[p])],
                        "zeros":[r for r in sorted(maximal) if r>>p&1]})
        group.extend([j,1<<l,0] for l in sorted(N[p]))
    if "or_output" in raw:
        xs=raw["or_output"]
        if not rows._indices(xs,n) or not xs:raise ValueError("nonempty OR output required")
        xs=set(xs)
        outputs.append({"name":"exact_or","ones":[1<<x for x in sorted(xs)],
                        "zeros":[((1<<n)-1)^sum(1<<x for x in xs)]})
    return rows.spec({"n":n,"gates":raw["gates"],"ops":["and","or"],"outputs":outputs,
                      "groups":[group] if raw.get("require_masked_edge") is True else []})

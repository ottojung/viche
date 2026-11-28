"""Bounded exact truth-table resynthesis of monotone circuit witnesses.

A wire is replaceable if the replacement agrees on the output's care
set: the rows where forcing this wire to 0 vs 1 changes the output.
We search replacements built from independent existing wires, rebuild
the output cone, merge semantically equal wires, and independently
audit the result. No negative result or optimality claim is made.
"""
import itertools
import time

AND = {0:0,1:0,2:0,3:1}
OR = {0:0,1:1,2:1,3:1}

def _inputs(n):
    return [sum(1 << r for r in range(1<<n) if r & (1<<i)) for i in range(n)]

def _decode(n, witness):
    gates=[]
    for i,(a,b,tt) in enumerate(witness):
        if not 0<=a<n+i or not 0<=b<n+i or tt not in (AND, OR):
            raise ValueError("invalid monotone witness")
        gates.append((int(tt==OR),a,b))
    return gates

def _eval(inputs,gates,force=None):
    w=list(inputs)
    for i,(op,a,b) in enumerate(gates,len(inputs)):
        w.append(force[1] if force is not None and force[0]==i
                 else (w[a]|w[b] if op else w[a]&w[b]))
    return w

def _rebuild(inputs,gates,replace=None,expr=None):
    """Keep only output cone, merge equal masks and remove dead branches."""
    n=len(inputs); out=[]; masks=list(inputs)
    by_mask={v:i for i,v in enumerate(masks)}
    memo={i:i for i in range(n)}
    def emit(e):
        if isinstance(e,int):
            if e in memo:return memo[e]
            op,a,b = gates[e-n]
            result=emit(expr) if e==replace else emit((op,a,b))
            memo[e]=result
            return result
        op,a,b=e
        a,b=emit(a),emit(b)
        mask=masks[a]|masks[b] if op else masks[a]&masks[b]
        if mask in by_mask:return by_mask[mask]
        i=n+len(out)
        out.append((op,min(a,b),max(a,b)))
        masks.append(mask);by_mask[mask]=i
        return i
    root=emit(n+len(gates)-1)
    if root<n:return None
    # Semantic merging can discard one of the just-emitted subtrees.
    use=set()
    def visit(i):
        if i<n or i in use:return
        use.add(i)
        _,a,b=out[i-n]
        visit(a);visit(b)
    visit(root)
    remap={i:i for i in range(n)}; clean=[]
    for i in sorted(use):
        op,a,b=out[i-n]
        remap[i]=n+len(clean)
        clean.append((op,remap[a],remap[b]))
    assert remap[root]==n+len(clean)-1
    return clean

def compress(n,witness,f,budget=0.5,depth=2,target_size=None):
    """Return a no-larger audited witness; deadline and input size bounded.

    Search one-/two-gate replacements over existing wires outside the
    replaced node's transitive fanout. Constant forcing is only used
    to compute the care set, not in the returned monotone circuit.
    """
    if not 1<=n<=6 or not witness or len(witness)>30 or len(f)!=1<<n:
        return witness
    deadline=time.monotonic()+max(0,budget)
    inputs=_inputs(n); full=(1<<(1<<n))-1
    target=sum(int(v)<<r for r,v in enumerate(f))
    gates=_decode(n,witness)
    if _eval(inputs,gates)[-1]!=target:
        raise ValueError("incorrect input witness")
    base=_rebuild(inputs,gates)
    if base is not None:gates=base
    while time.monotonic()<deadline and (target_size is None or len(gates)>target_size):
        masks=_eval(inputs,gates); best=gates
        # Descendant closure (including the wire itself).
        fanout=[{i} for i in range(n+len(gates))]
        for i,(_,a,b) in enumerate(gates,n):
            for j in range(i):
                if a in fanout[j] or b in fanout[j]:
                    fanout[j].add(i)
        for i in range(n+len(gates)-1,n-1,-1):
            if time.monotonic()>=deadline:break
            care=_eval(inputs,gates,(i,0))[-1]^_eval(inputs,gates,(i,full))[-1]
            wanted=masks[i]&care
            avail=[j for j in range(len(masks)) if j not in fanout[i]]
            small=[(masks[j],j) for j in avail]
            for a,b in itertools.combinations(avail,2):
                small.extend(((masks[a]&masks[b],(0,a,b)),
                              (masks[a]|masks[b],(1,a,b))))
            def consider(v,e):
                nonlocal best
                if v&care!=wanted:return
                new=_rebuild(inputs,gates,i,e)
                if new is not None and len(new)<len(best):
                    if _eval(inputs,new)[-1]!=target:
                        raise ValueError("invalid replacement")
                    best=new
            for v,e in small:
                consider(v,e)
            if target_size is not None and len(best)<=target_size:break
            if depth>1:
                for v,e in small[len(avail):]:
                    if time.monotonic()>=deadline:break
                    for j in avail:
                        consider(v&masks[j],(0,e,j))
                        consider(v|masks[j],(1,e,j))
                    if target_size is not None and len(best)<=target_size:break
            if target_size is not None and len(best)<=target_size:break
        if len(best)>=len(gates):break
        gates=best
    out=[(a,b,OR if op else AND) for op,a,b in gates]
    if len(out)>len(witness) or _eval(inputs,_decode(n,out))[-1]!=target:
        raise ValueError("resynthesis audit failed")
    return out

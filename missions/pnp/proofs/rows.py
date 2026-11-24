"""Explicit-row, multi-output circuit verification and SAT synthesis.

Only listed rows and disjunctive groups are checked. A caller must prove any
reduction from a quantified statement to those rows. The graph-bank generator
has such a monotonicity argument; arbitrary row specifications do not.
"""
import hashlib
import json
from pathlib import Path
import time

from .. import state

def _indices(xs, n):
    return isinstance(xs,list) and all(type(x) is int and 0<=x<n for x in xs)

def spec(raw):
    if not isinstance(raw,dict) or set(raw)-{"n","gates","ops","extra","fixed","outputs","groups"}:
        raise ValueError("unknown specification field")
    n,budget=raw.get("n"),raw.get("gates")
    if type(n) is not int or not 1<=n<=64 or type(budget) is not int or not 0<=budget<=96:
        raise ValueError("supported bounds: 1..64 inputs, 0..96 gates")
    ops=raw.get("ops",["and","or"])
    if not isinstance(ops,list) or not ops or any(x not in ("and","or","not") for x in ops) or len(ops)!=len(set(ops)):
        raise ValueError("invalid operations")
    extra=raw.get("extra",[])
    if not isinstance(extra,list) or len(extra)>16 or any(not _indices(x,n) for x in extra):
        raise ValueError("extra inputs must be ORs of base inputs")
    ni=n+len(extra)
    fixed=raw.get("fixed",[])
    if not isinstance(fixed,list) or len(fixed)>budget:
        raise ValueError("invalid prefix")
    for i,g in enumerate(fixed):
        if not isinstance(g,list) or not g or g[0] not in ops or len(g)!=(2 if g[0]=="not" else 3) or not _indices(g[1:],ni+i):
            raise ValueError("invalid fixed gate")
    outs=raw.get("outputs")
    if not isinstance(outs,list) or not 1<=len(outs)<=64:
        raise ValueError("1..64 outputs required")
    outputs=[]; names=set(); allrows=set(); count=0
    for o in outs:
        if not isinstance(o,dict) or set(o)-{"name","ones","zeros","wire"}:
            raise ValueError("invalid output")
        name=o.get("name")
        if not isinstance(name,str) or not name or len(name)>80 or name in names:
            raise ValueError("unique output names required")
        names.add(name)
        one,zero=o.get("ones",[]),o.get("zeros",[])
        if not _indices(one,1<<n) or not _indices(zero,1<<n) or set(one)&set(zero):
            raise ValueError("invalid or inconsistent rows")
        wire=o.get("wire")
        if wire is not None and (type(wire) is not int or not 0<=wire<ni+budget):
            raise ValueError("invalid fixed output wire")
        allrows.update(one);allrows.update(zero);count+=len(one)+len(zero)
        outputs.append({"name":name,"ones":sorted(set(one)),"zeros":sorted(set(zero)),"wire":wire})
    groups=raw.get("groups",[])
    if not isinstance(groups,list) or len(groups)>128:
        raise ValueError("invalid groups")
    normalized=[]
    for group in groups:
        if not isinstance(group,list) or not group:
            raise ValueError("nonempty groups required")
        for item in group:
            if not isinstance(item,list) or len(item)!=3 or not _indices(item[:1],len(outputs)) or not _indices(item[1:2],1<<n) or type(item[2]) is not int or item[2] not in (0,1):
                raise ValueError("group literals are [output index,row,value]")
            allrows.add(item[1])
        count+=len(group)
        normalized.append(sorted(set(tuple(x) for x in group)))
    if len(allrows)>8192 or count>131072:
        raise ValueError("row budget exceeded")
    return {"n":n,"gates":budget,"ops":sorted(ops),"extra":[sorted(set(x)) for x in extra],
            "fixed":fixed,"outputs":outputs,"groups":[[list(x) for x in g] for g in normalized]}

def rowset(s):
    return sorted({r for o in s["outputs"] for k in ("ones","zeros") for r in o[k]}
                  | {r for g in s["groups"] for _,r,_ in g})

def signatures(s,gates,outputs,rs):
    ni=s["n"]+len(s["extra"])
    if not isinstance(gates,list) or len(gates)>s["gates"] or gates[:len(s["fixed"])]!=s["fixed"]:
        raise ValueError("invalid witness gate budget or prefix")
    if not _indices(outputs,ni+len(gates)) or len(outputs)!=len(s["outputs"]):
        raise ValueError("invalid output wires")
    if any(o["wire"] is not None and w!=o["wire"] for o,w in zip(s["outputs"],outputs)):
        raise ValueError("fixed output mismatch")
    mask=(1<<len(rs))-1
    wires=[sum(((r>>i)&1)<<j for j,r in enumerate(rs)) for i in range(s["n"])]
    for xs in s["extra"]:
        v=0
        for x in xs:v|=wires[x]
        wires.append(v)
    for g in gates:
        if not isinstance(g,list) or not g or g[0] not in s["ops"] or len(g)!=(2 if g[0]=="not" else 3) or not _indices(g[1:],len(wires)):
            raise ValueError("invalid witness gate")
        a=wires[g[1]]
        wires.append(mask^a if g[0]=="not" else a&wires[g[2]] if g[0]=="and" else a|wires[g[2]])
    return [wires[w] for w in outputs]

def violations(s,gates,outputs):
    rs=rowset(s); index={r:i for i,r in enumerate(rs)}
    sig=signatures(s,gates,outputs,rs)
    def value(j,r):return (sig[j]>>index[r])&1
    bad=[(j,r,v) for j,o in enumerate(s["outputs"]) for k,v in (("ones",1),("zeros",0))
         for r in o[k] if value(j,r)!=v]
    groups=[i for i,g in enumerate(s["groups"]) if not any(value(j,r)==v for j,r,v in g)]
    return bad,groups

def verify(raw,witness):
    s=spec(raw)
    if not isinstance(witness,dict):
        raise ValueError("expected witness object")
    bad,groups=violations(s,witness.get("gates"),witness.get("outputs"))
    return {"verified":not bad and not groups,"rows":len(rowset(s)),"outputs":len(s["outputs"]),
            "failed_rows":len(bad),"examples":[list(b) for b in bad[:20]],
            "failed_groups":groups,"scope":"listed_rows_and_groups_only"}

def solve(raw,seconds=30,checkpoint=None):
    s=spec(raw)
    if not 0<seconds<=3600:raise ValueError("seconds must be in (0,3600]")
    try:
        from pysat.formula import IDPool
        from pysat.card import CardEnc,EncType
        from pysat.solvers import Cadical195
    except ImportError:
        return {"result":"unavailable","reason":"python-sat with CaDiCaL195 required"}
    digest=hashlib.sha256(json.dumps(s,sort_keys=True).encode()).hexdigest()
    checkpoint=Path(checkpoint).resolve() if checkpoint else None
    allrows=set(rowset(s))
    initial={r for o in s["outputs"] for k in ("ones","zeros") for r in o[k][:1]}
    initial.update(r for g in s["groups"] for _,r,_ in g)
    if checkpoint and checkpoint.exists():
        old=json.loads(checkpoint.read_text())
        if old.get("spec")!=digest or not _indices(old.get("rows"),1<<s["n"]) or not set(old["rows"])<=allrows:
            raise ValueError("checkpoint specification mismatch")
        initial.update(old["rows"])
    p=IDPool();V=p.id;cnf=[]
    ni=s["n"]+len(s["extra"]);ng=s["gates"];ops=s["ops"];nw=ni+ng
    def onehot(xs):cnf.extend(CardEnc.equals(xs,1,vpool=p,encoding=EncType.seqcounter).clauses)
    def sel(i,d,w):return V(("selector",i,d,w))
    def op(i,k):return V(("op",i,k))
    def out(j,w):return V(("out",j,w))
    def oval(j,r):return V(("output-value",j,r))
    for i in range(ng):
        onehot([op(i,k) for k in ops])
        for d in (0,1):onehot([sel(i,d,w) for w in range(ni+i)])
        # Only sound commutativity breaking; never require distinct inputs or used gates.
        for a in range(ni+i):
            for b in range(a):
                for k in ("and","or"):
                    if k in ops:cnf.append([-op(i,k),-sel(i,0,a),-sel(i,1,b)])
            if "not" in ops:cnf.append([-op(i,"not"),-sel(i,0,a),sel(i,1,a)])
        if i<len(s["fixed"]):
            k,*args=s["fixed"][i];a,b=(args[0],args[0]) if k=="not" else sorted(args)
            cnf.extend([[op(i,k)],[sel(i,0,a)],[sel(i,1,b)]])
    for j,o in enumerate(s["outputs"]):
        onehot([out(j,w) for w in range(nw)])
        if o["wire"] is not None:cnf.append([out(j,o["wire"])])
    required={}
    for j,o in enumerate(s["outputs"]):
        for k,v in (("ones",1),("zeros",0)):
            for r in o[k]:required.setdefault(r,[]).append((j,v))
    observed={}
    for group in s["groups"]:
        for j,r,_ in group:observed.setdefault(r,set()).add(j)
    rows=set()
    def add_row(r,solver):
        if r in rows:return
        rows.add(r)
        def val(w):return V(("value",r,w))
        def add(c):solver.add_clause(c)
        bits=[(r>>i)&1 for i in range(s["n"])]
        bits += [int(any(bits[i] for i in xs)) for xs in s["extra"]]
        for w,b in enumerate(bits):add([val(w) if b else -val(w)])
        for i in range(ng):
            a,b,g=V(("a",r,i)),V(("b",r,i)),val(ni+i)
            for d,z in ((0,a),(1,b)):
                for w in range(ni+i):
                    q=sel(i,d,w);add([-q,-z,val(w)]);add([-q,z,-val(w)])
            for k,clauses in (("and",[[-g,a],[-g,b],[g,-a,-b]]),
                              ("or",[[g,-a],[g,-b],[-g,a,b]]),("not",[[g,a],[-g,-a]])):
                if k in ops:
                    for c in clauses:add([-op(i,k),*c])
        targets={j for j,_ in required.get(r,[])}|observed.get(r,set())
        for j in targets:
            z=oval(j,r)
            for w in range(nw):
                q=out(j,w);add([-q,-z,val(w)]);add([-q,z,-val(w)])
        for j,v in required.get(r,[]):add([oval(j,r) if v else -oval(j,r)])
    def save():
        if checkpoint:state.atomic_write(str(checkpoint),json.dumps({"spec":digest,"rows":sorted(rows)})+"\n")
    start=time.monotonic()
    with Cadical195(bootstrap_with=cnf) as solver:
        for r in sorted(initial):add_row(r,solver)
        for group in s["groups"]:
            solver.add_clause([oval(j,r) if v else -oval(j,r) for j,r,v in group])
        save();rounds=0
        while time.monotonic()-start<seconds:
            solver.conf_budget(2000);result=solver.solve_limited();rounds+=1
            if result is None:continue
            if result is False:
                return {"result":"unsat_encoding","formal_refutation":False,"spec":digest,"rows":len(rows),"rounds":rounds}
            model=set(solver.get_model());gates=[]
            for i in range(ng):
                k=next(k for k in ops if op(i,k) in model)
                a=next(w for w in range(ni+i) if sel(i,0,w) in model)
                b=next(w for w in range(ni+i) if sel(i,1,w) in model)
                gates.append([k,a] if k=="not" else [k,a,b])
            gates[:len(s["fixed"])]=s["fixed"]
            outputs=[next(w for w in range(nw) if out(j,w) in model) for j in range(len(s["outputs"]))]
            bad,groups=violations(s,gates,outputs)
            if not bad and not groups:
                return {"result":"verified_rows","gates":gates,"outputs":outputs,"rows":len(allrows),
                        "scope":"listed_rows_and_groups_only","spec":digest}
            if groups or any(r in rows for _,r,_ in bad):
                raise RuntimeError("encoding and independent verifier disagree")
            for r in sorted({r for _,r,_ in bad})[:8]:add_row(r,solver)
            save()
        return {"result":"unknown","rows":len(rows),"rounds":rounds,"spec":digest}

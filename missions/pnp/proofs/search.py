"""Bounded exact finite circuit search; SAT witnesses checked on every row.

The gate budget is an upper bound: unused gates and repeated inputs are legal.
No undocumented minimality/essential-wire assumptions. UNSAT is solver evidence,
not a Lean proof. Checkpoints preserve CEGIS rows, not learned SAT clauses.
"""
import hashlib
import json
from pathlib import Path
import time

from .. import state


def spec(raw):
    if not isinstance(raw, dict) or set(raw) - {"n", "gates", "ops", "edges", "ones", "extra", "fixed"}:
        raise ValueError("unknown or malformed specification field")
    n, budget = raw.get("n"), raw.get("gates")
    if type(n) is not int or not 1 <= n <= 12 or type(budget) is not int or not 0 <= budget <= 24:
        raise ValueError("supported bounds: 1..12 variables, 0..24 gates")
    ops = raw.get("ops", ["and", "or", "not"])
    if not isinstance(ops, list) or not ops or any(x not in ("and", "or", "not") for x in ops) or len(set(ops)) != len(ops):
        raise ValueError("ops must be a nonempty subset of and, or, not")
    if ("edges" in raw) == ("ones" in raw):
        raise ValueError("provide exactly one of edges or ones")
    def indices(xs, limit):
        return isinstance(xs, list) and all(type(x) is int and 0 <= x < limit for x in xs)
    if "edges" in raw:
        edges = raw["edges"]
        if not isinstance(edges, list) or any(not indices(e, n) or len(e) != 2 or e[0] == e[1] for e in edges):
            raise ValueError("invalid edge list")
        ones = [r for r in range(1 << n) if any(r >> a & 1 and r >> b & 1 for a,b in edges)]
    else:
        ones = raw["ones"]
        if not indices(ones, 1 << n):
            raise ValueError("invalid truth-table ones")
    extra = raw.get("extra", [])
    if not isinstance(extra, list) or len(extra) > 12 or any(not indices(x, n) for x in extra):
        raise ValueError("extra inputs must be ORs of base inputs; [] means false")
    fixed = raw.get("fixed", [])
    if not isinstance(fixed, list) or len(fixed) > budget:
        raise ValueError("invalid fixed gate prefix")
    prefix = []
    for i, g in enumerate(fixed):
        if not isinstance(g, list) or not g or g[0] not in ops or len(g) != (2 if g[0] == "not" else 3) or not indices(g[1:], n+len(extra)+i):
            raise ValueError("invalid fixed gate")
        prefix.append([g[0], *g[1:]])
    return {"n": n, "gates": budget, "ops": sorted(ops), "ones": sorted(set(ones)),
            "extra": [sorted(set(x)) for x in extra], "fixed": prefix}


def inputs(s, row):
    bits = [(row >> i) & 1 for i in range(s["n"])]
    return bits + [int(any(bits[j] for j in xs)) for xs in s["extra"]]


def evaluate(s, gates, output, row):
    wires = inputs(s, row)
    for op, *args in gates:
        if op not in s["ops"] or len(args) != (1 if op == "not" else 2) or any(type(a) is not int or not 0 <= a < len(wires) for a in args):
            raise ValueError("invalid witness gate")
        a = wires[args[0]]
        wires.append(1-a if op == "not" else a & wires[args[1]] if op == "and" else a | wires[args[1]])
    if type(output) is not int or not 0 <= output < len(wires):
        raise ValueError("invalid output")
    return wires[output]


def counterexamples(s, gates, output):
    if len(gates) > s["gates"] or gates[:len(s["fixed"])] != s["fixed"]:
        raise ValueError("witness violates gate budget or fixed prefix")
    ones = set(s["ones"])
    return [r for r in range(1 << s["n"])
            if evaluate(s,gates,output,r) != int(r in ones)]


def solve(raw, seconds=30, checkpoint=None):
    s = spec(raw)
    checkpoint = Path(checkpoint).resolve() if checkpoint else None
    if not 0 < seconds <= 3600:
        raise ValueError("seconds must be in (0,3600]")
    # Optional dependency, never needed to use or publish other proofs.
    try:
        from pysat.formula import IDPool
        from pysat.card import CardEnc, EncType
        from pysat.solvers import Cadical195
    except ImportError:
        return {"result": "unavailable", "reason": "python-sat with CaDiCaL195 is required"}
    digest = hashlib.sha256(json.dumps(s,sort_keys=True).encode()).hexdigest()
    initial = {0, (1 << s["n"])-1, *s["ones"][:16]}
    initial.update(1 << i for i in range(s["n"]))
    if checkpoint and Path(checkpoint).exists():
        data = json.loads(Path(checkpoint).read_text())
        if data.get("spec") != digest:
            raise ValueError("checkpoint belongs to another specification")
        rows = data.get("rows")
        if not isinstance(rows,list) or any(type(x) is not int or not 0 <= x < 1 << s["n"] for x in rows):
            raise ValueError("invalid checkpoint rows")
        initial.update(rows)
    p = IDPool(); V = p.id
    ni = s["n"] + len(s["extra"]); ng = s["gates"]; ops = s["ops"]
    cnf = []
    def onehot(xs):
        cnf.extend(CardEnc.equals(xs, 1, vpool=p, encoding=EncType.seqcounter).clauses)
    def sel(i,d,w): return V(("selector",i,d,w))
    def op(i,k): return V(("op",i,k))
    def out(w): return V(("out",w))
    for i in range(ng):
        onehot([op(i,k) for k in ops])
        for d in (0,1):
            onehot([sel(i,d,w) for w in range(ni+i)])
        # Commutativity only; equal binary operands and unused wires are valid.
        for k in ("and","or"):
            if k in ops:
                for a in range(ni+i):
                    for b in range(a):
                        cnf.append([-op(i,k),-sel(i,0,a),-sel(i,1,b)])
        if "not" in ops:
            for a in range(ni+i):
                cnf.append([-op(i,"not"),-sel(i,0,a),sel(i,1,a)])
        if i < len(s["fixed"]):
            k,*args = s["fixed"][i]
            # For fixed binary prefixes preserve the exact given ordering
            # in the decoded witness; internal selectors are canonical.
            a,b = (args[0],args[0]) if k == "not" else sorted(args)
            cnf.extend([[op(i,k)],[sel(i,0,a)],[sel(i,1,b)]])
    onehot([out(w) for w in range(ni+ng)])
    rows=set(); ones=set(s["ones"])
    def add_row(r, solver):
        if r in rows:
            return
        rows.add(r)
        def val(w): return V(("value",r,w))
        def add(c): solver.add_clause(c)
        for w,b in enumerate(inputs(s,r)):
            add([val(w) if b else -val(w)])
        for i in range(ng):
            a,b,g = V(("a",r,i)),V(("b",r,i)),val(ni+i)
            for d,z in ((0,a),(1,b)):
                for w in range(ni+i):
                    q=sel(i,d,w)
                    add([-q,-z,val(w)]);add([-q,z,-val(w)])
            for k,clauses in (
                ("and",[[-g,a],[-g,b],[g,-a,-b]]),
                ("or",[[g,-a],[g,-b],[-g,a,b]]),
                ("not",[[g,a],[-g,-a]])):
                if k in ops:
                    for c in clauses:
                        add([-op(i,k),*c])
        for w in range(ni+ng):
            add([-out(w),val(w) if r in ones else -val(w)])
    def save():
        if checkpoint:
            state.atomic_write(str(checkpoint),json.dumps({"spec":digest,"rows":sorted(rows)})+"\n")
    start=time.monotonic()
    with Cadical195(bootstrap_with=cnf) as solver:
        for r in sorted(initial):
            add_row(r,solver)
        save()
        rounds=0
        while time.monotonic()-start < seconds:
            # Bounded conflict slices retain learning inside this invocation.
            solver.conf_budget(2000)
            result=solver.solve_limited()
            rounds+=1
            if result is None:
                continue
            if result is False:
                return {"result":"unsat_encoding","rows":len(rows),"rounds":rounds,
                        "formal_refutation":False,"spec":digest}
            m=set(solver.get_model())
            gates=[]
            for i in range(ng):
                k=next(k for k in ops if op(i,k) in m)
                a=next(w for w in range(ni+i) if sel(i,0,w) in m)
                b=next(w for w in range(ni+i) if sel(i,1,w) in m)
                gates.append([k,a] if k=="not" else [k,a,b])
            gates[:len(s["fixed"])]=s["fixed"]
            output=next(w for w in range(ni+ng) if out(w) in m)
            bad=counterexamples(s,gates,output)
            if not bad:
                return {"result":"verified_witness","gates":gates,"output":output,
                        "cases":1<<s["n"],"rows":len(rows),"spec":digest}
            if any(r in rows for r in bad):
                raise RuntimeError("SAT encoding disagrees with independent evaluator")
            for r in bad[:8]:
                add_row(r,solver)
            save()
        return {"result":"unknown","rows":len(rows),"rounds":rounds,"spec":digest}

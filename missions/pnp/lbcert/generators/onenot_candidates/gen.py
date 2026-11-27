"""Precomputed one-NOT candidates, never a kernel receipt."""
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import sys
from functools import lru_cache

HERE = Path(__file__).resolve().parent
DATA_SHA = "65f4f26a41b112c14124fac05b7a2ba892040532ae3ed7fe4fb7fae3814a9126"
TEMPLATE_SHA = "6e2471678d274f6a13144e0746c23dd0809c12b89acf446063877822267f18de"


def pinned(path, expected):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("candidate data changed without review")
    return raw


@lru_cache(maxsize=1)
def records():
    data = json.loads(pinned(HERE / "candidates.json", DATA_SHA))
    return {row["statement"].strip(): row for row in data}


def normalized(statement):
    return " ".join(statement.split())


@lru_cache(maxsize=1)
def pattern():
    sample=normalized(next(iter(records())))
    graph=re.search(r"\[[0-9, ]+\](?= : List ℕ)",sample).group(0)
    parts=sample.split(graph)
    expr=re.escape(parts[0])+r"(?P<graph>\[[0-9, ]+\])"+re.escape(parts[1])
    for part in parts[2:]:
        expr+=r"(?P=graph)"+re.escape(part)
    return re.compile(expr)


def edges_of(statement):
    m=pattern().fullmatch(normalized(statement))
    if not m:return None
    try:
        nums=[int(x) for x in m.group("graph")[1:-1].split(",")]
    except ValueError:return None
    if not nums or len(nums)%2:return None
    edges=list(zip(nums[::2],nums[1::2]))
    if any(not 0<=a<b<8 for a,b in edges) or len(set(edges))!=len(edges):
        return None
    return edges


def matches(statement):
    return edges_of(statement) is not None


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def generate(gid, statement):
    if not re.fullmatch(r"L-meta-[0-9]+",gid):
        return None
    edges=edges_of(statement)
    if edges is None:
        return None
    row = records().get(statement.strip())
    if row is not None and row["gid"] != gid:
        return None
    pinned(HERE / "template.lean", TEMPLATE_SHA)
    path = HERE.parent.parent / "onenot" / "onenot.py"
    emitter = load_module("pnp_onenot_emitter",path)
    emitter.TEMPLATE = str(HERE / "template.lean")
    n=8
    f = emitter.truth(n, edges)
    if row is None:
        heuristic=load_module("pnp_onenot_screen",HERE/"search.py")
        biclique=load_module("pnp_biclique",path.with_name("biclique.py"))
        w=heuristic.greedy(n,edges,biclique.build)
        pairs=heuristic.screen(emitter,n,f,w)
        if pairs is None:return None
        row={"n":n,"M":len(w)}
    else:
        w = [(a, b, {int(k): v for k, v in tt.items()}) for a, b, tt in row["wit"]]
        pairs = [tuple(p) for p in row["pairs"]]
    if n != row["n"] or len(w) != row["M"] or not pairs or len(pairs) > 128:
        raise ValueError("invalid candidate dimensions")
    for i, (a, b, tt) in enumerate(w):
        if not (0 <= a < n+i and 0 <= b < n+i and a != b) or tt not in ({0:0,1:0,2:0,3:1}, {0:0,1:1,2:1,3:1}):
            raise ValueError("invalid monotone gate")
    if not all(emitter.evaluate(n, w, r) == f[r] for r in range(1 << n)):
        raise ValueError("invalid witness")
    if not all(0 <= a < len(f) and 0 <= b < len(f) and f[a] == 1 and f[b] == 0 for a,b in pairs):
        raise ValueError("invalid sampled pairs")
    return emitter.lean_file(gid, statement.strip(), n, pairs, len(w), w)


def main():
    gid, source, output = sys.argv[1:]
    text = generate(gid, Path(source).read_text())
    if text is None:
        return 3
    Path(output).write_text(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

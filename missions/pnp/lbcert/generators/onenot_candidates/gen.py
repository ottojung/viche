"""Precomputed one-NOT candidates, never a kernel receipt."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from functools import lru_cache

HERE = Path(__file__).resolve().parent
DATA_SHA = "5f60823c01db97ed9366508233b5053a08ce97f6f18e451dddd821b6e29068f4"
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


def matches(statement):
    return statement.strip() in records()


def generate(gid, statement):
    row = records().get(statement.strip())
    if row is None or row["gid"] != gid:
        return None
    pinned(HERE / "template.lean", TEMPLATE_SHA)
    path = HERE.parent.parent / "onenot" / "onenot.py"
    spec = importlib.util.spec_from_file_location("pnp_onenot_emitter", path)
    emitter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(emitter)
    emitter.TEMPLATE = str(HERE / "template.lean")
    n, edges = emitter.parse(statement)
    f = emitter.truth(n, edges)
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

"""Allow the ordinary lower-bound engine in the held posting lane."""
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(HERE))
import lbparse

ENGINE_SHA = "156bcc7495facb6efd554a726478dcba644b603c64d239f7ab59b60f7c04a3a0"

def matches(statement):
    c = lbparse.classify(statement)
    return c is not None and 1 <= c["n"] <= 11

def main():
    gid, source, output = sys.argv[1:]
    m = re.fullmatch(r"L-meta-([0-9]+)", gid)
    if m is None or not matches(Path(source).read_text()):
        return 3
    root = Path(os.environ.get("PNP_STATE_ROOT", "/var/lib/lubko/wd/viche-state/pnp"))
    engine = root / "lbcert" / "engine7281.lean"
    try:
        if hashlib.sha256(engine.read_bytes()).hexdigest() != ENGINE_SHA:
            print("lower-bound template digest mismatch", file=sys.stderr)
            return 2
    except OSError:
        print("pinned lower-bound template unavailable", file=sys.stderr)
        return 3
    result = subprocess.run([sys.executable, str(HERE / "lbassemble.py"), str(engine),
        "PEqualNP.Outside.L_meta_" + m[1], source, output,
        "--maxstates", "4800", "--chunks", "40"])
    if result.returncode in (2, 3, 4):
        Path(output).unlink(missing_ok=True)
        return 3
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())

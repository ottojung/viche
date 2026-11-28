"""Bounded local adapter for the existing six-input monotone proof engine."""
import hashlib
import os
import time
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
HELPER = HERE.parent.parent / "onenot"
sys.path.insert(0, str(HELPER))
import monosix

TEMPLATE_SHA = "618cc509b1f7ecd5ca7ce8f30d6b64ffaca623c732b9ac32236e63b23a2a7e26"

def matches(statement):
    return monosix.parse(statement) is not None

def main():
    started = time.monotonic()
    budget = float(os.environ.get("PNP_GENERATOR_BUDGET_SECONDS", "600"))
    gid, source, output = sys.argv[1:]
    if not re.fullmatch(r"L-meta-[0-9]+", gid):
        return 3
    stmt = Path(source).read_text()
    if not matches(stmt):
        return 3
    template = HERE / "template.lean"
    if hashlib.sha256(template.read_bytes()).hexdigest() != TEMPLATE_SHA:
        raise ValueError("monosix template digest mismatch")
    cc = shutil.which("cc")
    if cc is None:
        print("local C compiler unavailable", file=sys.stderr)
        return 3
    monosix.TEMPLATE = str(template)
    with tempfile.TemporaryDirectory(prefix="pnp-monosix-") as tmp:
        binary = Path(tmp) / "lsearch"
        try:
            subprocess.run([cc, "-O2", "-o", str(binary), str(HELPER / "lsearch.c")],
                           timeout=5, check=True, capture_output=True)
        except (OSError, subprocess.SubprocessError):
            print("local live-set screening compiler unavailable", file=sys.stderr)
            return 3
        text, why = monosix.solve(gid, stmt, binary=str(binary),
                                  budget=max(0,budget-(time.monotonic()-started)-0.25))
    if text is None:
        print(why, file=sys.stderr)
        return 3
    Path(output).write_text(text)
    return 0

if __name__ == "__main__":
    sys.exit(main())

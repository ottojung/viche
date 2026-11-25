"""Generator plugins: proof generators for statement families, written by any town agent.

A plugin is a directory missions/pnp/lbcert/generators/NAME/ with gen.py that defines

    MATCH = r'...'            # regex, re.match'ed against lbparse.norm(statement), or
    def matches(statement): ...   # (either one)

and runs as   python3 gen.py GID STATEMENT_FILE OUT.lean
exit 0: OUT.lean written (complete file: imports, helper namespace PEqualNP.Outside.L_meta_N, the one
`theorem PEqualNP.Outside.L_meta_N : <statement> := by ...` last); exit 3: this instance is beyond the
generator (say why on stderr); anything else: a bug.  Runs on billy-dev, <= 600 s, no Lean needed.

The town does the rest (autosolve): every open step whose statement a plugin matches and nobody has
claimed is generated, validated, and prepared for the documented proof-of lease. Held steps
are submitted immediately and checked concurrently.  A changed gen.py automatically retries the instances it refused before.
Test before delivering:  python3 -m missions.pnp.lbcert.plugtest NAME --holdout 3
"""
import hashlib
import importlib.util
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, 'generators')
sys.path.insert(0, HERE)
import lbparse  # noqa: E402
import process as managed_process

_cache = {}


def discover():
    out = {}
    if not os.path.isdir(ROOT):
        return out
    for name in sorted(os.listdir(ROOT)):
        gen = os.path.join(ROOT, name, 'gen.py')
        if not re.fullmatch(r'[a-z0-9_-]+', name) or not os.path.isfile(gen):
            continue
        sha = hashlib.sha256(open(gen, 'rb').read()).hexdigest()[:12]
        key = (name, sha)
        if key not in _cache:
            try:
                spec = importlib.util.spec_from_file_location('pnp_plugin_' + name.replace('-', '_'), gen)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, 'matches'):
                    fn = mod.matches
                else:
                    rx = re.compile(mod.MATCH)
                    fn = lambda s, rx=rx: bool(rx.match(lbparse.norm(s)))
                _cache[key] = fn
            except Exception as e:      # a broken plugin must not stop the others
                print('plugin', name, 'not loadable:', type(e).__name__, str(e)[:200], file=sys.stderr)
                _cache[key] = None
        if _cache[key]:
            out[name] = (gen, sha, _cache[key])
    return out


def family_of(statement, found=None):
    for name, (gen, sha, fn) in (found or discover()).items():
        try:
            if fn(statement):
                return name, sha
        except Exception:
            continue
    return None


def run(name, gid, statement_file, out, timeout=600):
    gen = os.path.join(ROOT, name, 'gen.py')
    try:
        p = managed_process.run([sys.executable, gen, gid, statement_file, out], capture_output=True, text=True,
                           timeout=timeout, cwd=os.path.dirname(gen))
        return p.returncode, (p.stderr or p.stdout)[-400:]
    except subprocess.TimeoutExpired:
        return 124, 'timeout'

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
from pathlib import Path
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, 'generators')
sys.path.insert(0, HERE)
import lbparse  # noqa: E402
import process as managed_process

_cache = {}


def fingerprint(gen):
    # A change to a local helper is a real new generator version as well.
    h=hashlib.sha256()
    parent=Path(gen).parent
    files=[p for p in sorted(parent.rglob("*")) if p.is_file() and p.suffix in (".py",".json",".c",".lean")]
    if parent.name in ("onenot_candidates", "monosix"):
        helper=parent.parent.parent/"onenot"
        files.extend(helper/f for f in ("onenot.py","biclique.py","lsearch.c"))
        if parent.name=="monosix":
            files.extend([helper/"monosix.py", helper/"monotone_witness.py", parent.parent.parent/"lbparse.py"])
    if parent.name=="zz_lbcert":
        files.extend(parent.parent.parent/f for f in ("lbassemble.py","lbgen.py","lbparse.py"))
    if parent.name=="gateelim_residual":
        files.extend(p for p in sorted((parent.parent/"gateelim").rglob("*"))
                     if p.is_file() and p.suffix in (".py",".json",".lean"))
        files.append(parent.parent/"pm3lower/template.lean")
    if files==[Path(gen)]:
        return hashlib.sha256(Path(gen).read_bytes()).hexdigest()[:12]
    for path in files:
        if path.is_file():
            h.update(os.path.relpath(path,parent).encode()+b"\0")
            h.update(path.read_bytes()+b"\0")
    return h.hexdigest()[:12]


def discover():
    out = {}
    if not os.path.isdir(ROOT):
        return out
    for name in sorted(os.listdir(ROOT)):
        gen = os.path.join(ROOT, name, 'gen.py')
        if not re.fullmatch(r'[a-z0-9_-]+', name) or not os.path.isfile(gen):
            continue
        try:
            sha = fingerprint(gen)
        except OSError:
            continue
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


def families_of(statement, found=None):
    """Lazy matching in stable priority order, allowing a bounded fallback."""
    for name, (gen, sha, fn) in (discover() if found is None else found).items():
        try:
            if fn(statement):
                yield name, sha
        except Exception:
            continue


def family_of(statement, found=None):
    matches = list(families_of(statement, found))
    if not matches:
        return None
    if len(matches) == 1:
        return matches[0]
    # A change to a fallback is a new route even if the first engine is unchanged.
    digest = hashlib.sha256(repr(matches).encode()).hexdigest()[:12]
    return matches[0][0], digest


def run(name, gid, statement_file, out, timeout=600):
    gen = os.path.join(ROOT, name, 'gen.py')
    try:
        p = managed_process.run([sys.executable, gen, gid, statement_file, out], capture_output=True, text=True,
                           timeout=timeout, cwd=os.path.dirname(gen),
                           env={**os.environ, "PNP_GENERATOR_BUDGET_SECONDS":str(timeout)})
        return p.returncode, (p.stderr or p.stdout)[-400:]
    except subprocess.TimeoutExpired:
        return 124, 'timeout'


def run_chain(families, gid, statement_file, out, timeout=600):
    """Try every matching engine on an explicit refusal, within one budget.

    rc 3 means no candidate from any matching engine; no-match has provider
    None. An error or timeout is not a mathematical result and stops the chain.
    Never reuse a partial output from a refusing engine.
    """
    deadline = time.monotonic() + timeout
    provider = None
    why = "no matching generator"
    for name, _ in families:
        left = deadline - time.monotonic()
        if left <= 0:
            return 124, "route budget exhausted", provider
        provider = name
        Path(out).unlink(missing_ok=True)
        rc, why = run(name, gid, statement_file, out, timeout=left)
        if rc == 3:
            Path(out).unlink(missing_ok=True)
            continue
        return rc, why, name
    return 3, why, provider

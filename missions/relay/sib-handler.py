#!/usr/bin/env python3
"""marceline-dev handler for the relay op `sibling`: prove a step with a merged sibling's proof.

stdin:  {"statement", "module", "imports": [..], "max_tries": int}
stdout: {"module", "status": ok|none|error, "source", "variant", "tried", "secs", "corpus", "sha256",
         "bytes", "file_gz_b64", "log"}
Corpus: the upstream tree /home/lubko/pnp-verify-2171/up2 kept at origin/main (fetched at most every
2 minutes; definitions rebuilt after a move). Siblings = merged theorems with the same statement
skeleton (lbcert/sibling.py); newest first; each compiled with `lake env lean` (rc 0, no error/sorry).
"""
import base64, fcntl, gzip, hashlib, json, os, re, subprocess, sys, tempfile, time

TREE = '/home/lubko/pnp-verify-2171/up2'
TOOLS = '/home/lubko/pnp-infra/lbgen'
STATE = os.path.expanduser('~/.local/state/sibling')
os.makedirs(STATE, exist_ok=True)
sys.path.insert(0, TOOLS)
import sibling  # noqa: E402

ENV = dict(os.environ, PATH=os.path.expanduser('~/.elan/bin') + ':' + os.environ.get('PATH', '/usr/bin:/bin'))
ALLOWED = re.compile(r'^Mathlib(\.[A-Za-z][A-Za-z0-9_]*)*$')


def git(*a, check=False):
    return subprocess.run(['git', '-C', TREE] + list(a), capture_output=True, text=True, check=check, timeout=300)


def refresh():
    """Move the tree to origin/main (exclusive lock; compiles hold a shared lock)."""
    stamp = os.path.join(STATE, 'fetched')
    if os.path.exists(stamp) and time.time() - os.path.getmtime(stamp) < 120:
        return
    with open(os.path.join(STATE, 'tree.lock'), 'w') as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        if os.path.exists(stamp) and time.time() - os.path.getmtime(stamp) < 120:
            return
        git('fetch', '-q', 'origin', 'main')
        if git('rev-parse', 'HEAD').stdout.strip() != git('rev-parse', 'origin/main').stdout.strip():
            changed=git('diff','--quiet','HEAD','origin/main','--','lean/PEqualNP/Defs','lean/PEqualNP/Defs.lean','lean/lean-toolchain','lean/lake-manifest.json','lean/lakefile.toml').returncode
            git('checkout', '-q', '--detach', 'origin/main',check=True)
            if changed:
                with compile_slot():
                    subprocess.run(['lake', 'build', 'PEqualNP.Defs'], cwd=TREE + '/lean', env=ENV,
                                   capture_output=True, timeout=900,check=True)
        open(stamp, 'w').close()


def index():
    head = git('rev-parse', 'HEAD').stdout.strip()
    cache = os.path.join(STATE, 'index-%s.json' % head)
    if os.path.exists(cache):
        return head, json.load(open(cache))
    d = os.path.join(TREE, 'lean/PEqualNP/Outside')
    idx = {}
    for f in os.listdir(d):
        m = re.fullmatch(r'(L_meta_\d+)\.lean', f)
        if not m:
            continue
        p = os.path.join(d, f)
        if os.path.getsize(p) > 300000:
            continue
        text = open(p).read()
        mod = 'PEqualNP.Outside.' + m.group(1)
        mm = sibling.final_theorem(text, mod)
        if mm:
            idx.setdefault(sibling.skeleton(mm.group(1)), []).append(mod)
    for f in os.listdir(STATE):
        if f.startswith('index-'):
            os.unlink(os.path.join(STATE, f))
    json.dump(idx, open(cache, 'w'))
    return head, idx



def compile_slot():
    from compile_admission import slot
    return slot(12288, timeout=180)

def compiles(text):
    with tempfile.TemporaryDirectory() as d, open(os.path.join(STATE, 'tree.lock'), 'w') as lk:
        fcntl.flock(lk, fcntl.LOCK_SH)
        with compile_slot():
            f = os.path.join(d, 'Candidate.lean')
            open(f, 'w').write(text)
            try:
                p = subprocess.run(['lake', 'env', 'lean', '-M', '11776', f], cwd=TREE + '/lean', env=ENV,
                                   capture_output=True, text=True, timeout=600)
            except subprocess.TimeoutExpired:
                return False, 'timeout'
            out = p.stdout + p.stderr
            return p.returncode == 0 and 'error' not in out and 'sorry' not in out, out[-300:]

def imports_ok(text, allowed):
    for line in text.split('\n'):
        m = re.match(r'^import\s+(\S+)', line)
        if m and not (ALLOWED.match(m.group(1)) or m.group(1) in allowed):
            return False
    return True


def main():
    p = json.load(sys.stdin)
    t0 = time.time()
    res = {'module': p['module'], 'status': 'none', 'tried': 0, 'log': ''}
    try:
        refresh()
        head, idx = index()
        res['corpus'] = head
        sk = sibling.skeleton(p['statement'])
        srcs = sorted((m for m in idx.get(sk, []) if m != p['module']),
                      key=lambda m: -int(m.rsplit('_', 1)[1]))
        allowed = set(p.get('imports') or [])
        for mod in srcs:
            if res['tried'] >= p['max_tries']:
                break
            text = open(os.path.join(TREE, 'lean/PEqualNP/Outside', mod.split('.')[-1] + '.lean')).read()
            if not imports_ok(text, allowed):
                continue
            mm = sibling.final_theorem(text, mod)
            for name, cand in sibling.variants(text, mod, mm.group(1), p['module'], p['statement']):
                if res['tried'] >= p['max_tries']:
                    break
                res['tried'] += 1
                ok, log = compiles(cand)
                res['log'] = log
                if ok:
                    data = cand.encode()
                    res.update(status='ok', source=mod, variant=name, bytes=len(data),
                               sha256=hashlib.sha256(data).hexdigest(),
                               file_gz_b64=base64.b64encode(gzip.compress(data, 9)).decode())
                    res['secs'] = round(time.time() - t0)
                    print(json.dumps(res))
                    return
        res['siblings'] = len(srcs)
    except Exception as e:
        res.update(status='error', log=str(e)[-300:])
    res['secs'] = round(time.time() - t0)
    print(json.dumps(res))


if __name__ == '__main__':
    main()

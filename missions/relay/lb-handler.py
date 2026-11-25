#!/usr/bin/env python3
"""marceline-dev handler for the relay op `lb-cert`: build an lb_cert lower-bound certificate.

stdin: {"statement": str, "module": "PEqualNP.Outside.X", "maxstates": int, "chunks": int}
stdout: {"module", "status": ok|false|toobig|unsupported|error, "engine", "states", "bytes", "sha256",
         "file_gz_b64", "log"}   (status false = a circuit with K-1 gates exists: the twin is true)
Tools: /home/lubko/pnp-infra/lbgen (lbgen.py, lbparse.py, lbassemble.py) and the engine files beside it.
"""
import base64, gzip, hashlib, json, os, re, subprocess, sys, tempfile

TOOLS = '/home/lubko/pnp-infra/lbgen'
ENGINES = ['/home/lubko/pnp-infra/engine7281.lean', '/home/lubko/pnp-infra/engine7281.pruned.lean']

def compile_slot():
    from compile_admission import slot
    return slot(12288, timeout=180)

p = json.load(sys.stdin)
res = {'module': p['module'], 'status': 'error', 'engine': None, 'log': ''}
if p.get('check_file_gz_b64'):
    # check mode (billy-dev lbcert/checkremote.py): compile a file built elsewhere (generator
    # plugins written by the town) against current upstream, through the same compile slots.
    import fcntl
    data = gzip.decompress(base64.b64decode(p['check_file_gz_b64']))
    checked_base = None
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'c.lean')
        open(out, 'wb').write(data)
        st = os.path.expanduser('~/.local/state/sibling')
        os.makedirs(st, exist_ok=True)
        with open(os.path.join(st, 'tree.lock'), 'w') as lk:
            fcntl.flock(lk, fcntl.LOCK_SH)
            with compile_slot():
                env = dict(os.environ, PATH=os.path.expanduser('~/.elan/bin') + ':' + os.environ.get('PATH', ''))
                try:
                    c = subprocess.run(['lake', 'env', 'lean', '-M', '11776', out], cwd='/home/lubko/pnp-verify-2171/up2/lean', env=env,
                                       capture_output=True, text=True, timeout=int(p.get('timeout', 900)))
                    checked_base = subprocess.check_output(['git','-C','/home/lubko/pnp-verify-2171/up2','rev-parse','HEAD'], text=True, timeout=5).strip()
                    text = c.stdout + c.stderr
                    ok = c.returncode == 0 and 'error' not in c.stdout and 'sorry' not in text
                except subprocess.TimeoutExpired:
                    ok, text = False, 'timeout'
    res.update(status='ok' if ok else 'error', engine='check', log=text[-1500:],
               bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), checked_base=checked_base)
    print(json.dumps(res))
    sys.exit(0)
with tempfile.TemporaryDirectory() as d:
    sf, out = os.path.join(d, 's.txt'), os.path.join(d, 'c.lean')
    open(sf, 'w').write(p['statement'])
    for eng in ENGINES:
        mono = 'Monotone2' in p['statement']   # monotone-equals-general family: monofam.py
        onenot = (not p['statement'].lstrip().startswith('¬') and 'GateOp.not → i = j)' in p['statement']
                  and "∃ (gates' : List" in p['statement'])   # "one NOT gate saves nothing": onenot.py
        if onenot:
            gid = p['module'].rsplit('.', 1)[-1].replace('_', '-')
            cmd = [sys.executable, '/home/lubko/pnp-infra/onenot/onenot.py', gid, sf, out]
        else:
            cmd = ([sys.executable, 'monofam.py', eng, p['module'], sf, out] if mono else
                   [sys.executable, 'lbassemble.py', eng, p['module'], sf, out,
                    '--maxstates', str(p['maxstates']), '--chunks', str(p['chunks'])])
        r = None
        if mono:
            # live-set instantiation of the merged L-meta-13175 first (seconds); monofam's lb_cert after
            gid = p['module'].rsplit('.', 1)[-1].replace('_', '-')
            r = subprocess.run([sys.executable, '/home/lubko/pnp-infra/onenot/monosix.py', gid, sf, out],
                               cwd=TOOLS, capture_output=True, text=True, timeout=900)
            if r.returncode != 0:
                r = None
        if r is None:
            r = subprocess.run(cmd, cwd=TOOLS, capture_output=True, text=True, timeout=1700)
        if onenot:
            mono = True    # same compile gate below
            if r.returncode == 3:
                res.update(status='unsupported', log=r.stderr[-600:])
                break
            if r.returncode != 0:          # crash or timeout: retryable, never sticky
                res.update(status='error', log=r.stderr[-600:])
                break
        res['log'] = r.stderr[-600:]
        res['engine'] = os.path.basename(eng)
        m = re.search(r'states=(\d+)', r.stderr)
        if m:
            res['states'] = int(m.group(1))
        if r.returncode == 0 and mono and p.get('defer_compile') is not True:
            # small files (~40 s): compile against current upstream before anything is submitted
            import fcntl
            st = os.path.expanduser('~/.local/state/sibling')
            os.makedirs(st, exist_ok=True)
            with open(os.path.join(st, 'tree.lock'), 'w') as lk:
                fcntl.flock(lk, fcntl.LOCK_SH)
                with compile_slot():
                    env = dict(os.environ, PATH=os.path.expanduser('~/.elan/bin') + ':' + os.environ.get('PATH', ''))
                    c = subprocess.run(['lake', 'env', 'lean', '-M', '11776', out], cwd='/home/lubko/pnp-verify-2171/up2/lean', env=env,
                                       capture_output=True, text=True, timeout=900)
                    compiled_base = subprocess.check_output(['git','-C','/home/lubko/pnp-verify-2171/up2','rev-parse','HEAD'], text=True, timeout=5).strip()
            if c.returncode != 0 or 'error' in c.stdout:
                res.update(status='error', log='compile failed: ' + (c.stdout + c.stderr)[-400:])
                break
            res.update(compiled=True, checked_base=compiled_base)
        if r.returncode == 0:
            res.setdefault('compiled',False)
            data = open(out, 'rb').read()
            res.update(status='ok', bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                       file_gz_b64=base64.b64encode(gzip.compress(data, 9)).decode())
            break
        res['status'] = {2: 'unsupported', 3: 'false', 4: 'toobig'}.get(r.returncode, 'error')
        if not (r.returncode == 4 and 'TOO LARGE' in r.stderr):
            break
print(json.dumps(res))

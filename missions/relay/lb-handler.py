#!/usr/bin/env python3
"""marceline-dev handler for the relay op `lb-cert`: build an lb_cert lower-bound certificate.

stdin: {"statement": str, "module": "PEqualNP.Outside.X", "maxstates": int, "chunks": int}
stdout: {"module", "status": ok|false|toobig|unsupported|error, "engine", "states", "bytes", "sha256",
         "file_gz_b64", "log"}   (status false = a circuit with K-1 gates exists: the twin is true)
Tools: /home/lubko/pnp-infra/lbgen (lbgen.py, lbparse.py, lbassemble.py) and the engine files beside it.
"""
import base64, gzip, hashlib, io, json, os, re, subprocess, sys, tempfile

TOOLS = '/home/lubko/pnp-infra/lbgen'
ENGINES = ['/home/lubko/pnp-infra/engine7281.lean', '/home/lubko/pnp-infra/engine7281.pruned.lean']


def _descendants(pid):
    out, todo = [], [pid]
    while todo:
        q = todo.pop()
        try:
            for t in os.listdir('/proc/%d/task' % q):
                with open('/proc/%d/task/%s/children' % (q, t)) as f:
                    kids = [int(x) for x in f.read().split()]
                out += kids
                todo += kids
        except (OSError, ValueError):
            pass
    return out


def run_group(argv, timeout=None, **kw):
    """subprocess.run, but a timeout kills the child's whole process tree: `lake env lean` and
    generator scripts leave `lean`/`cadical` running when only the parent is killed (two orphaned
    lean compiles ran for 2-2.6 h on 2026-11-26).  The child stays in our process group, so the
    relay's group kill of this handler still reaches it."""
    import signal
    kw.pop('capture_output', None)
    p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kw)
    try:
        out, err = p.communicate(timeout=timeout)
    except BaseException:
        for q in [p.pid] + _descendants(p.pid):
            try:
                os.kill(q, signal.SIGKILL)
            except OSError:
                pass
        p.communicate()
        raise
    return subprocess.CompletedProcess(argv, p.returncode, out, err)

def compile_slot(rss=12288):
    from compile_admission import slot
    return slot(rss, timeout=180)

p = json.load(sys.stdin)
res = {'module': p['module'], 'status': 'error', 'engine': None, 'log': ''}
if p.get('check_file_gz_b64'):
    # check mode (billy-dev lbcert/checkremote.py): compile a file built elsewhere (generator
    # plugins written by the town) against current upstream, through the same compile slots.
    import fcntl
    encoded = p['check_file_gz_b64']
    if len(encoded)>768*1024:
        raise ValueError("oversized encoded proof")
    with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(encoded, validate=True))) as stream:
        data = stream.read(512*1024+1)
    if not data or len(data)>512*1024:
        raise ValueError("proof exceeds 512 KiB")
    checked_base = None
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'c.lean')
        open(out, 'wb').write(data)
        st = os.path.expanduser('~/.local/state/sibling')
        os.makedirs(st, exist_ok=True)
        with open(os.path.join(st, 'tree.lock'), 'w') as lk:
            fcntl.flock(lk, fcntl.LOCK_SH)
            # Most checks need far less than the 12 GiB reservation, which admitted one compile at a
            # time: try a 4 GiB slot first and only a memory failure takes the large one.
            for reserve, cap in ((4096, '3584'), (12288, '11776')):
                with compile_slot(reserve):
                    env = dict(os.environ, PATH=os.path.expanduser('~/.elan/bin') + ':' + os.environ.get('PATH', ''))
                    try:
                        c = run_group(['lake', 'env', 'lean', '-M', cap, out], cwd='/home/lubko/pnp-verify-2171/up2/lean', env=env,
                                           capture_output=True, text=True, timeout=int(p.get('timeout', 900)))
                        checked_base = subprocess.check_output(['git','-C','/home/lubko/pnp-verify-2171/up2','rev-parse','HEAD'], text=True, timeout=5).strip()
                        text = c.stdout + c.stderr
                        ok = c.returncode == 0 and 'error' not in c.stdout and 'sorry' not in text
                    except subprocess.TimeoutExpired:
                        ok, text = False, 'timeout'
                if ok or 'memory' not in text.lower():
                    break
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
            r = run_group([sys.executable, '/home/lubko/pnp-infra/onenot/monosix.py', gid, sf, out],
                               cwd=TOOLS, capture_output=True, text=True, timeout=900)
            if r.returncode != 0:
                r = None
        if r is None:
            r = run_group(cmd, cwd=TOOLS, capture_output=True, text=True, timeout=1700)
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
                    c = run_group(['lake', 'env', 'lean', '-M', '11776', out], cwd='/home/lubko/pnp-verify-2171/up2/lean', env=env,
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

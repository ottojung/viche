#!/usr/bin/env python3
"""Pre-generate lb_cert candidates for every open concrete circuit-size step on the public desk.

Why: concrete lower-bound steps ("Table 2: ... at least K gates", "Graph t5-...") are won within
10-20 minutes of posting. A candidate must exist BEFORE the town holds the step.

Every POLL seconds: read the public desk file, classify statements with lbparse, and generate a
certificate for each new concrete step. Generation runs on marceline-dev through the relay op
`lb-cert` (lbremote.py; ~20 s for a 4k-state certificate). billy-dev builds locally only when
the relay fails. Output under PNP_STATE_ROOT/lbcert:
  cands/<gap>.lean, cands/<gap>.status   ok ENGINE | false | toobig | unsupported | error
  twins.json   {negation-twin gap id: lower-bound gap id}
  desk.json    {gap id: pr_open} for the concrete family
The allocator fast lane (missions/pnp/fastlane.py) consumes these files: it submits ready
candidates for held steps and settles held false twins. This process never touches leases.

run: python3 -m missions.pnp.lbcert.autosolve   (allocator.sh keeps exactly one running)
stop: touch PNP_STATE_ROOT/lbcert/STOP
"""
import fcntl, hashlib, json, os, re, subprocess, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lbparse  # noqa: E402

STATE = os.environ.get('PNP_STATE_ROOT', '/var/lib/lubko/wd/viche-state/pnp')
WORK = os.path.join(STATE, 'lbcert')
CANDS = os.path.join(WORK, 'cands')
DESK = 'https://data.pequalnp.com/data/desk/gaps.json'
SOURCE = 'https://raw.githubusercontent.com/open-goat/pequalnp-proofs/main/lean/PEqualNP/Outside/L_meta_7281.lean'
SOURCE_SHA = '98c3a7192bc0d62775011eb073a212c7a2d0d9bf4da12e0e11980fd2fe002c74'
POLL = 45
REMOTE_WORKERS = 4   # marceline-dev runs at most 4 lb-cert jobs and 3 compiles at once
MAXSTATES = 6000       # the 512 KiB file limit caps certificates at ~5k states; larger searches only burn marceline
os.makedirs(CANDS, exist_ok=True)


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def get(url):
    r = urllib.request.Request(url, headers={'User-Agent': 'viche-town'})
    return urllib.request.urlopen(r, timeout=40).read()


def ensure_engines():
    eng = os.path.join(WORK, 'engine7281.lean')
    if not os.path.exists(eng):
        src = get(SOURCE)
        if hashlib.sha256(src).hexdigest() != SOURCE_SHA:
            raise RuntimeError('upstream L_meta_7281 changed; re-pin SOURCE_SHA after review')
        s = src.decode()
        open(eng, 'w').write(s[:s.index('def L_ : List ℕ :=')])
    pr = os.path.join(WORK, 'engine7281.pruned.lean')
    if not os.path.exists(pr):
        subprocess.run([sys.executable, os.path.join(HERE, 'prune_engine.py'), eng, pr], check=True)
    return [eng, pr]


def status(gid):
    p = os.path.join(CANDS, gid + '.status')
    return open(p).read().strip() if os.path.exists(p) else None


def write_status(gid, text):
    tmp = os.path.join(CANDS, gid + '.status.tmp')
    open(tmp, 'w').write(text)
    os.replace(tmp, os.path.join(CANDS, gid + '.status'))


QUEUED = set()


def generate(g, engines):
    gid, mod = g['id'], g['module']
    if status(gid) is not None:
        return
    sf = os.path.join(CANDS, gid + '.stmt')
    open(sf, 'w').write(g['statement'])
    out = os.path.join(CANDS, gid + '.lean')
    t0 = time.time()
    p = subprocess.run([sys.executable, os.path.join(HERE, 'lbremote.py'), sf, mod, out,
                        '--maxstates', str(MAXSTATES), '--chunks', '40'], capture_output=True, text=True, timeout=2000)
    try:
        r = json.loads(p.stdout.strip().split('\n')[-1])
    except Exception:
        r = {'status': 'relay_error'}
    where = 'marceline'
    if p.returncode == 1 and lbparse.family(g['statement']) == 'mono':
        QUEUED.discard(gid)   # only marceline-dev builds this family: retry on a later poll
        log('generate deferred', gid, r.get('status'), '%.0fs' % (time.time() - t0))
        return
    if p.returncode == 1:   # relay or handler trouble: build here, slower but independent
        where = 'local'
        r = {'status': 'error'}
        for eng in engines:
            q = subprocess.run([sys.executable, 'lbassemble.py', eng, mod, sf, out + '.tmp', '--maxstates', '4800',
                                '--chunks', '40'], cwd=HERE, capture_output=True, text=True, timeout=3600)
            if q.returncode == 0:
                os.replace(out + '.tmp', out)
                r = {'status': 'ok', 'engine': os.path.basename(eng)}
                break
            r = {'status': {2: 'unsupported', 3: 'false', 4: 'toobig'}.get(q.returncode, 'error')}
            if not (q.returncode == 4 and 'TOO LARGE' in q.stderr):
                break
    st = r.get('status')
    write_status(gid, '%s %s %s states=%s secs=%.0f' % (st, r.get('engine') or '-', where, r.get('states'), time.time() - t0))
    log('generated', gid, st, where, r.get('states'), '%.0fs' % (time.time() - t0))


SIB_RETRY = 300
SIB_STATE = os.path.join(WORK, 'sibling.json')


def sibling_pass():
    """Sibling transfer for held steps with no candidate (relay op `sibling`, compiled on marceline-dev).
    Retried every SIB_RETRY seconds while held: merged siblings appear in bursts."""
    gaps_dir = os.path.join(STATE, 'gaps')
    try:
        tried = json.load(open(SIB_STATE))
    except (OSError, ValueError):
        tried = {}
    now = time.time()
    for gid in os.listdir(gaps_dir):
        try:
            rec = json.load(open(os.path.join(gaps_dir, gid, 'state.json')))
        except (OSError, ValueError):
            continue
        if rec.get('state') not in ('LEASED', 'RESEARCHING') or rec.get('candidate_digest') or status(gid):
            continue
        if now - tried.get(gid, 0) < SIB_RETRY:
            continue
        tried[gid] = now
        sf = os.path.join(CANDS, gid + '.sib.stmt')
        open(sf, 'w').write(rec['statement'])
        out = os.path.join(CANDS, gid + '.lean')
        p = subprocess.run([sys.executable, os.path.join(HERE, 'sibremote.py'), sf, rec['module'], out,
                            '--imports', ','.join(rec.get('imports') or ['PEqualNP.Defs']), '--max-tries', '6'],
                           capture_output=True, text=True, timeout=2000)
        try:
            r = json.loads(p.stdout.strip().split('\n')[-1])
        except Exception:
            r = {}
        if p.returncode == 0:
            write_status(gid, 'ok sibling %s %s marceline compiled tried=%s' % (r.get('source'), r.get('variant'), r.get('tried')))
        log('sibling', gid, r.get('status'), 'source', r.get('source'), 'tried', r.get('tried'), 'siblings', r.get('siblings'))
    tmp = SIB_STATE + '.tmp'
    json.dump(tried, open(tmp, 'w'))
    os.replace(tmp, SIB_STATE)


def sibling_loop():
    while not os.path.exists(os.path.join(WORK, 'STOP')):
        try:
            sibling_pass()
        except Exception as e:
            log('sibling error', type(e).__name__, str(e)[:200])
        time.sleep(30)


def main():
    lock = open(os.path.join(WORK, 'autosolve.lock'), 'w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return 0
    engines = ensure_engines()
    import threading
    threading.Thread(target=sibling_loop, daemon=True).start()
    pool = ThreadPoolExecutor(REMOTE_WORKERS)
    queued = QUEUED
    while not os.path.exists(os.path.join(WORK, 'STOP')):
        try:
            gaps = json.loads(get(DESK))['gaps']
            pos, twins, desk = {}, {}, {}
            fam = {}
            for g in gaps:
                f = lbparse.family(g['statement'])
                if f:
                    fam[g['id']] = f
                    desk[g['id']] = g.get('pr_open', 0)
                if f == 'lb':
                    pos[lbparse.norm(g['statement'])] = g['id']
            for g in gaps:
                m = re.fullmatch(r'¬ ?\((.*)\)', lbparse.norm(g['statement']))
                if m and m.group(1) in pos:
                    twins[g['id']] = pos[m.group(1)]
                    desk[g['id']] = g.get('pr_open', 0)
            for name, obj in (('twins.json', twins), ('desk.json', desk)):
                tmp = os.path.join(WORK, name + '.tmp')
                json.dump(obj, open(tmp, 'w'))
                os.replace(tmp, os.path.join(WORK, name))
            # newest first: fresh batches are where the races are
            for g in sorted((g for g in gaps if g['id'] in fam),
                            key=lambda g: (g.get('pr_open', 0) > 0, -int(re.sub(r'\D', '', g['id']) or 0))):
                if g['id'] not in queued and status(g['id']) is None:
                    queued.add(g['id'])
                    pool.submit(generate, g, engines)
        except Exception as e:
            log('poll error', type(e).__name__, str(e)[:200])
        time.sleep(POLL)
    log('STOP file found; exiting')
    return 0


if __name__ == '__main__':
    sys.exit(main())

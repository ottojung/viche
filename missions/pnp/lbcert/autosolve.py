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
import process as managed_process
import threading
LOCAL_FALLBACK = threading.BoundedSemaphore(1)

# A running Python process does not reload a module whose source changes on
# disk. Without this guard, a fix delivered while autosolve is alive stays
# dormant until some unrelated restart, which previously left the poll loop
# throwing KeyError on value/template desk gaps for hours while generating no
# candidates. Detect a source change at each poll and exit cleanly; allocator.sh
# relaunches us with the current code within one tick (it holds our flock).
START_HASH = hashlib.sha256(open(HERE + '/autosolve.py', 'rb').read()).hexdigest()


def source_changed():
    try:
        now = hashlib.sha256(open(HERE + '/autosolve.py', 'rb').read()).hexdigest()
    except OSError:
        return False
    return now != START_HASH

STATE = os.environ.get('PNP_STATE_ROOT', '/var/lib/lubko/wd/viche-state/pnp')
WORK = os.path.join(STATE, 'lbcert')
CANDS = os.path.join(WORK, 'cands')
DESK = 'https://data.pequalnp.com/data/desk/gaps.json'
SOURCE = 'https://raw.githubusercontent.com/open-goat/pequalnp-proofs/main/lean/PEqualNP/Outside/L_meta_7281.lean'
SOURCE_SHA = '98c3a7192bc0d62775011eb073a212c7a2d0d9bf4da12e0e11980fd2fe002c74'
POLL = 10            # gaps.json is a conditional GET now (304 when unchanged)
REMOTE_WORKERS = 3   # expensive lower-bound search
PLUGIN_WORKERS = 2   # constructive generators cannot be starved by lower-bound search
PREPARE_WORKERS = 1  # exact checked receipt for a completed candidate
LB_MAX_INPUTS = 12   # see generate(): no lb_cert has ever succeeded above 11 inputs
MAXSTATES = 6000       # the 512 KiB file limit caps certificates at ~5k states; larger searches only burn marceline
GEN_TIMEOUT = 900      # successful runs take <= 546 s; a hung relay call must not hold a worker for 2000 s
os.makedirs(CANDS, exist_ok=True)


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def get(url):
    if url == DESK:
        import live
        return live.gaps_bytes()
    r = urllib.request.Request(url, headers={'User-Agent': 'viche-town'})
    return urllib.request.urlopen(r, timeout=40).read()


SEEN = os.path.join(WORK, 'seen.json')


def note_seen(ids):
    """Ledger stage 'seen': the first poll in which a step is open.  The first run records the
    current frontier silently, so only steps posted afterwards get a seen time."""
    from missions.pnp import ledger
    try:
        seen = set(json.load(open(SEEN)))
        first = False
    except (OSError, ValueError):
        seen, first = set(), True
    new = set(ids) - seen
    if not new:
        return
    if not first:
        for gid in sorted(new):
            ledger.mark('seen', gid)
    tmp = SEEN + '.tmp'
    json.dump(sorted(seen | new), open(tmp, 'w'))
    os.replace(tmp, SEEN)


def lease_now(gid):
    """A step just got an exact compiler receipt: ask the desk for it (proof-of) now, not at the
    allocator's next tick (30 s sleep plus the tick itself)."""
    try:
        from missions.pnp import allocator
        log('lease now', gid, allocator.proof_of_now(gid))
    except Exception as exc:
        log('lease now deferred', gid, type(exc).__name__, str(exc)[:160])


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
        managed_process.run([sys.executable, os.path.join(HERE, 'prune_engine.py'), eng, pr], check=True)
    return [eng, pr]


def status(gid):
    p = os.path.join(CANDS, gid + '.status')
    return open(p).read().strip() if os.path.exists(p) else None


def write_status(gid, text):
    tmp = os.path.join(CANDS, gid + '.status.tmp')
    open(tmp, 'w').write(text)
    os.replace(tmp, os.path.join(CANDS, gid + '.status'))
    if text.split()[0] in ('ok','generated'):
        try:
            from missions.pnp import fastlane
            fastlane.submit_ready(gid)
        except Exception as exc:
            log('ready notification deferred',gid,type(exc).__name__,str(exc)[:150])


QUEUED = set()


RETRY_DELAY = 1800


def retryable(gid):
    """An infrastructure failure is not evidence that a problem is unsolvable."""
    st = status(gid)
    if st is None:
        return True
    if not st or st.split()[0] not in ('relay_error', 'error', 'deferred'):
        return False
    try:
        return time.time() - os.stat(os.path.join(CANDS, gid + '.status')).st_mtime >= RETRY_DELAY
    except OSError:
        return False


def generate(g, engines):
    gid, mod = g['id'], g['module']
    if not retryable(gid):
        return
    # Record of every lb_cert run to 2026-11-26: 252 'ok' all at <= 11 inputs; at >= 12 inputs
    # every run ended toobig/error/relay_error after 980-1780 s, holding a relay slot each
    # (five such searches on 24-42 input edge-function rows were running at once).
    m = re.search(r'HasCircuitSize (\d+) ', g['statement'])
    if m and int(m.group(1)) > LB_MAX_INPUTS:
        write_status(gid, 'toobig - precheck inputs=%s > %d' % (m.group(1), LB_MAX_INPUTS))
        log('generated', gid, 'toobig precheck inputs', m.group(1))
        return
    sf = os.path.join(CANDS, gid + '.stmt')
    open(sf, 'w').write(g['statement'])
    out = os.path.join(CANDS, gid + '.lean')
    t0 = time.time()
    from missions.pnp import state, support
    rec = state.load(gid)
    defer = bool(support.active(rec) and rec['statement'] == g['statement'])
    try:
        p = managed_process.run([sys.executable, os.path.join(HERE, 'lbremote.py'), sf, mod, out,
                            '--maxstates', str(MAXSTATES), '--chunks', '40'] + (['--defer-compile'] if defer else []),
                           capture_output=True, text=True, timeout=GEN_TIMEOUT)
    except subprocess.TimeoutExpired:
        # A hung relay call otherwise raises out of generate(), leaves no status, and is
        # re-queued on the very next poll: three such steps held all REMOTE_WORKERS for hours
        # (9750/9756/9822 on 2026-11-26).  Record a retryable status so the worker is freed
        # for other steps and this step gets the normal RETRY_DELAY backoff.
        write_status(gid, 'deferred generation timeout %ss' % GEN_TIMEOUT)
        from missions.pnp import ledger
        ledger.mark('generated', gid, status='timeout', secs=GEN_TIMEOUT, where='relay')
        log('generated', gid, 'timeout', 'relay', None, '%ss' % GEN_TIMEOUT)
        return
    try:
        r = json.loads(p.stdout.strip().split('\n')[-1])
    except Exception:
        r = {'status': 'relay_error'}
    where = 'marceline'
    if os.path.exists(os.path.join(WORK, 'STOP')):
        return
    if p.returncode == 1 and lbparse.family(g['statement']) in ('mono', 'onenot'):
        write_status(gid, 'deferred relay unavailable')
        log('generate deferred', gid, r.get('status'), '%.0fs' % (time.time() - t0))
        return
    if p.returncode == 1:   # relay or handler trouble: build here, slower but independent
        if not LOCAL_FALLBACK.acquire(blocking=False):
            write_status(gid, 'deferred local fallback busy')
            log('local fallback deferred',gid)
            return
        try:
            where = 'local'
            r = {'status': 'error'}
            for eng in engines:
                q = managed_process.run([sys.executable, 'lbassemble.py', eng, mod, sf, out + '.tmp', '--maxstates', '4800',
                                    '--chunks', '40'], cwd=HERE, capture_output=True, text=True, timeout=300)
                if q.returncode == 0:
                    os.replace(out + '.tmp', out)
                    r = {'status': 'ok', 'engine': os.path.basename(eng)}
                    break
                r = {'status': {2: 'unsupported', 3: 'false', 4: 'toobig'}.get(q.returncode, 'error')}
                if not (q.returncode == 4 and 'TOO LARGE' in q.stderr):
                    break
        finally:
            LOCAL_FALLBACK.release()
    from missions.pnp import ledger
    ledger.mark('generated', gid, status=r.get('status'), secs=round(time.time() - t0), where=where)
    if r.get('status')=='ok' and r.get('compiled'):
        from missions.pnp.lbcert import ready
        if ready.record(gid,r,open(out,'rb').read()) and not defer:
            lease_now(gid)
    st = r.get('status')
    # Generation success is not an exact Lean compile receipt. Existing
    # checked/compiled marker semantics stay available to the bulk lane.
    if st == 'ok' and not r.get('compiled'):
        st = 'generated'
    write_status(gid, '%s %s %s states=%s secs=%.0f' % (st, r.get('engine') or '-', where, r.get('states'), time.time() - t0))
    log('generated', gid, st, where, r.get('states'), '%.0fs' % (time.time() - t0))


SIB_RETRY = 300
SIB_STATE = os.path.join(WORK, 'sibling.json')


def sibling_pass():
    """Sibling transfer for held steps with no candidate (relay op `sibling`, compiled on marceline-dev).

    A step whose statement skeleton is absent from the merged corpus cannot succeed: the relay
    returns tried=0/siblings=0 only after the handler has burned minutes of marceline compile time
    (measured 337 s for L-meta-8400, 2026-11-26).  Retried blindly every SIB_RETRY seconds this
    occupied the sibling thread and the shared Lean slots for hours with zero candidates.  Now a
    definitive no-match is remembered for the current corpus head; the step is retried when a new
    merge lands, or after SIB_RETRY seconds for a transient relay error.
    """
    gaps_dir = os.path.join(STATE, 'gaps')
    try:
        tried = json.load(open(SIB_STATE))
    except (OSError, ValueError):
        tried = {}
    head = None
    try:
        import sibling
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
        from missions.pnp import gitctl
        head, _idx = sibling.index(gitctl.MIRROR, WORK)
    except Exception:
        pass   # no corpus fingerprint: fall back to the time-based retry below
    now = time.time()
    changed = False
    for gid in os.listdir(gaps_dir):
        try:
            rec = json.load(open(os.path.join(gaps_dir, gid, 'state.json')))
        except (OSError, ValueError):
            continue
        if rec.get('state') not in ('LEASED', 'RESEARCHING') or rec.get('candidate_digest') or status(gid):
            continue
        prev = tried.get(gid)
        prev = prev if isinstance(prev, dict) else {}
        settled = bool(prev.get('settled')) and bool(head) and prev.get('head') == head
        if settled or now - prev.get('at', 0) < SIB_RETRY:
            continue
        tried[gid] = {'head': head, 'at': now, 'settled': False}
        changed = True
        sf = os.path.join(CANDS, gid + '.sib.stmt')
        open(sf, 'w').write(rec['statement'])
        out = os.path.join(CANDS, gid + '.lean')
        p = managed_process.run([sys.executable, os.path.join(HERE, 'sibremote.py'), sf, rec['module'], out,
                            '--imports', ','.join(rec.get('imports') or ['PEqualNP.Defs']), '--max-tries', '6'],
                           capture_output=True, text=True, timeout=2000)
        try:
            r = json.loads(p.stdout.strip().split('\n')[-1])
        except Exception:
            r = {}
        if p.returncode == 0:
            write_status(gid, 'ok sibling %s %s marceline compiled tried=%s' % (r.get('source'), r.get('variant'), r.get('tried')))
        elif head and (p.returncode == 5 or r.get('siblings') == 0):
            # Definitive no-match on this corpus: do not recompile it until a merge changes the index.
            tried[gid] = {'head': head, 'at': now, 'settled': True}
        log('sibling', gid, r.get('status'), 'source', r.get('source'), 'tried', r.get('tried'), 'siblings', r.get('siblings'))
    if changed:
        tmp = SIB_STATE + '.tmp'
        json.dump(tried, open(tmp, 'w'))
        os.replace(tmp, SIB_STATE)


def gen_plugin(g, name, sha):
    """A town-written generator plugin (lbcert/plugins.py): generate here, compile on marceline-dev."""
    import plugins, checkremote
    from missions.pnp import state, support, validate
    from missions.pnp.lbcert import ready
    gid = g['id']
    sf = os.path.join(CANDS, gid + '.stmt')
    open(sf, 'w').write(g['statement'])
    out = os.path.join(CANDS, gid + '.lean')
    t0 = time.time()
    rc, why = plugins.run(name, gid, sf, out + '.gen')
    if rc != 0:
        write_status(gid, '%s plugin %s %s rc=%s %s' % ('unsupported' if rc == 3 else 'failed', name, sha, rc,
                                                     why.strip().replace('\n', ' ')[-160:]))
        log('plugin', name, gid, 'rc', rc, '%.0fs' % (time.time() - t0))
        return
    # Statically validate exact output before any publication or remote check.
    meta={k:g[k] for k in ('id','file','module','statement','imports')}
    try:
        data=open(out+'.gen','rb').read()
        validate.validate(meta,data)
    except (OSError,validate.InvalidCandidate) as e:
        write_status(gid,'failed plugin %s %s invalid %s'%(name,sha,str(e)[:120]))
        return
    rec=state.load(gid)
    if support.active(rec) and rec['statement']==g['statement']:
        os.replace(out+'.gen',out)
        write_status(gid,'generated plugin %s %s secs=%.0f'%(name,sha,time.time()-t0))
        return
    crc, res = checkremote.check(out + '.gen', g['module'])
    if crc == 2:
        os.replace(out + '.gen', out)
        write_status(gid, 'generated plugin %s %s check deferred' % (name, sha))
        log('plugin', name, gid, 'check deferred', res.get('status'))
        return
    if crc == 0:
        os.replace(out + '.gen', out)
        recorded = ready.record(gid,dict(res,status='ok',compiled=True),data)
        write_status(gid, 'ok plugin %s %s marceline compiled secs=%.0f' % (name, sha, time.time() - t0))
        if recorded:
            lease_now(gid)
    else:
        write_status(gid, 'failed plugin %s %s compile: %s' % (name, sha, (res.get('log') or '').replace('\n', ' ')[-160:]))
    log('plugin', name, gid, 'ok' if crc == 0 else 'compile_error', '%.0fs' % (time.time() - t0))


def check_prepared(g):
    import checkremote
    from missions.pnp import state, support, validate, fastlane
    from missions.pnp.lbcert import ready
    gid=g['id']
    rec=state.load(gid)
    if support.active(rec):
        fastlane.submit_ready(gid)
        return
    path=os.path.join(CANDS,gid+'.lean')
    try:
        data=open(path,'rb').read()
        validate.validate({k:g[k] for k in ('id','file','module','statement','imports')},data)
    except (OSError,validate.InvalidCandidate) as e:
        log('prepared validation refused',gid,str(e)[:160]);return
    if ready.verified(gid):
        return
    code,result=checkremote.check(path,g['module'],timeout=600)
    if code==0:
        if ready.record(gid,dict(result,status='ok',compiled=True),data):
            log('prepared exact proof',gid,result.get('checked_base'))
            fastlane.submit_ready(gid)
            lease_now(gid)
    else:
        log('prepared check',gid,code,result.get('status'),str(result.get('log',''))[-180:])


def held_ids():
    out = set()
    d = os.path.join(STATE, 'gaps')
    for gid in os.listdir(d) if os.path.isdir(d) else []:
        try:
            if json.load(open(os.path.join(d, gid, 'state.json'))).get('state') in ('LEASED', 'RESEARCHING', 'CANDIDATE_READY'):
                out.add(gid)
        except (OSError, ValueError):
            pass
    return out


def fresh(gid, plugin_sha=None):
    """No status yet, or a plugin refused/failed it with an older version of its gen.py."""
    st = status(gid)
    if st is None:
        return True
    m = re.match(r'(unsupported|failed) plugin \S+ (\w+)', st)
    return bool(m and plugin_sha and m.group(2) != plugin_sha)


SWEEP_STATE = os.path.join(WORK, 'sweep.json')
SWEEP_MAX_TRIES = 4


def sweep_pass():
    """Sibling transfer for every open step nobody has claimed (pr_open == 0) and no generator owns,
    whose statement skeleton matches a merged file: the bulk lane publishes what compiles.
    Each step is tried once per upstream corpus commit."""
    import sibling
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
    from missions.pnp import gitctl
    head, idx = sibling.index(gitctl.MIRROR, WORK)
    try:
        tried = json.load(open(SWEEP_STATE))
    except (OSError, ValueError):
        tried = {}
    gaps = json.loads(get(DESK))['gaps']
    import live
    open_now = live.open_ids()
    if open_now is not None:
        gaps = [g for g in gaps if g['id'] in open_now]
    todo = [g for g in gaps if isinstance(g.get('statement'), str) and not g.get('pr_open')
            and status(g['id']) is None and not lbparse.family(g['statement'])
            and tried.get(g['id']) != head and sibling.skeleton(g['statement']) in idx]
    todo.sort(key=lambda g: -int(re.sub(r'\D', '', g['id']) or 0))
    log('sweep', len(todo), 'open unclaimed steps with a merged sibling at', head[:12])
    for g in todo:
        if os.path.exists(os.path.join(WORK, 'STOP')):
            break
        gid = g['id']
        sf = os.path.join(CANDS, gid + '.sib.stmt')
        open(sf, 'w').write(g['statement'])
        out = os.path.join(CANDS, gid + '.lean')
        p = managed_process.run([sys.executable, os.path.join(HERE, 'sibremote.py'), sf, g['module'], out,
                            '--imports', ','.join(g.get('imports') or ['PEqualNP.Defs']),
                            '--max-tries', str(SWEEP_MAX_TRIES)], capture_output=True, text=True, timeout=3000)
        try:
            r = json.loads(p.stdout.strip().split('\n')[-1])
        except Exception:
            r = {}
        if p.returncode == 0:
            write_status(gid, 'ok sibling %s %s marceline compiled tried=%s sweep' % (r.get('source'), r.get('variant'), r.get('tried')))
        if p.returncode in (0, 5):
            tried[gid] = head
            tmp = SWEEP_STATE + '.tmp'
            json.dump(tried, open(tmp, 'w'))
            os.replace(tmp, SWEEP_STATE)
        log('sweep', gid, r.get('status'), 'source', r.get('source'), 'tried', r.get('tried'))


def sibling_loop():
    while not os.path.exists(os.path.join(WORK, 'STOP')):
        try:
            sibling_pass()
        except Exception as e:
            log('sibling error', type(e).__name__, str(e)[:200])
        time.sleep(30)


def sweep_loop():
    from missions.pnp import gitctl
    last_radar = 0
    while not os.path.exists(os.path.join(WORK, 'STOP')):
        try:
            latest = gitctl.ensure_mirror()      # fresh upstream/main: new merges are new siblings
            try:
                gitctl.sync_fork_base(latest)    # proof pushes then send only their own objects
            except Exception as e:
                log('fork sync deferred', type(e).__name__, str(e)[:160])
            if time.time() - last_radar > 600:
                last_radar = time.time()
                from missions.pnp import radar   # family radar + tool/method backlogs
                radar.write(radar.build())
            sweep_pass()
        except Exception as e:
            log('sweep error', type(e).__name__, str(e)[:200])
        time.sleep(120)


def main():
    lock = open(os.path.join(WORK, 'autosolve.lock'), 'w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return 0
    engines = ensure_engines()
    import threading
    threading.Thread(target=sibling_loop, daemon=True).start()
    threading.Thread(target=sweep_loop, daemon=True).start()
    pool = ThreadPoolExecutor(REMOTE_WORKERS)
    plugin_pool = ThreadPoolExecutor(PLUGIN_WORKERS)
    prepare_pool = ThreadPoolExecutor(PREPARE_WORKERS)
    queued = QUEUED
    outstanding = {}
    plugin_pending = {}
    prepared = {}
    prepare_retry = {}
    while not os.path.exists(os.path.join(WORK, 'STOP')):
        if source_changed():
            # Exit now: returning would drop our flock while interpreter shutdown keeps draining the
            # pool's queue, so a second instance would run beside this one (seen 2026-11-25).
            log('source changed; exiting for clean restart')
            managed_process.stop_all()
            for executor in (pool, plugin_pool, prepare_pool):
                executor.shutdown(wait=False, cancel_futures=True)
            os._exit(0)
        try:
            for pending in (outstanding, plugin_pending):
                for gid,future in list(pending.items()):
                    if future.done():
                        try:future.result()
                        except Exception as e:log('generator interrupted',gid,type(e).__name__,str(e)[:160])
                        pending.pop(gid)
                        queued.discard(gid)
            for gid,future in list(prepared.items()):
                if future.done():
                    try:future.result()
                    except Exception as e:log('prepared interrupted',gid,type(e).__name__,str(e)[:120])
                    prepared.pop(gid)
                    queued.discard(gid)
                    prepare_retry[gid]=time.time()+600
            prepare_retry={g:t for g,t in prepare_retry.items() if t>time.time()}
            gaps = json.loads(get(DESK))['gaps']
            # The desk also publishes unresolved value/template gaps that carry
            # `template` with @@VALUE@@ holes and no concrete `statement`.
            # They are not certifiable yet; skip them instead of letting a
            # KeyError abort the whole poll and disable certificate generation.
            # Only steps open right now (desk/status): gaps.json also carries cut sub-steps,
            # waiting twins and closed steps (~25% of it), where any work is wasted.
            import live
            open_now = live.open_ids()
            if open_now is not None:
                gaps = [g for g in gaps if g['id'] in open_now]
            concrete = [g for g in gaps if isinstance(g.get('statement'), str)]
            if open_now is not None:
                note_seen(open_now)
            held = held_ids()
            pos, twins, desk = {}, {}, {}
            fam = {}
            for g in concrete:
                f = lbparse.family(g['statement'])
                if f:
                    fam[g['id']] = f
                    desk[g['id']] = g.get('pr_open', 0)
                if f == 'lb':
                    pos[lbparse.norm(g['statement'])] = g['id']
            for g in concrete:
                m = re.fullmatch(r'¬ ?\((.*)\)', lbparse.norm(g['statement']))
                if m and m.group(1) in pos:
                    twins[g['id']] = pos[m.group(1)]
                    desk[g['id']] = g.get('pr_open', 0)
            for name, obj in (('twins.json', twins), ('desk.json', desk)):
                tmp = os.path.join(WORK, name + '.tmp')
                json.dump(obj, open(tmp, 'w'))
                os.replace(tmp, os.path.join(WORK, name))
            # newest first: fresh batches are where the races are. The one-NOT family is the live
            # race (hundreds posted at once, cleared within the hour): first, and only while unclaimed.
            # Within the family, fewest edges first: those are the instances the generator can
            # do (monotone size <= 11) and the ones competitors take within minutes.
            from missions.pnp import cli
            held = {r['gap_id'] for r in cli.held_records()}
            from missions.pnp import fastlane
            for gid in held:
                try:fastlane.submit_ready(gid)
                except Exception as exc:log('held candidate deferred',gid,str(exc)[:120])
            from missions.pnp.lbcert import ready
            if len(prepared)<PREPARE_WORKERS:
                choices=[g for g in concrete if g['id'] not in held and g['id'] not in queued
                         and g['id'] not in prepare_retry and not g.get('pr_open',0)
                         and (status(g['id']) or '').split(' ')[0] in ('ok','generated')
                         and os.path.isfile(os.path.join(CANDS,g['id']+'.lean'))
                         and not ready.verified(g['id'])]
                if choices:
                    # Prefer recent, cheaply solved candidates; no old FIFO backlog.
                    g=max(choices,key=lambda x:os.stat(os.path.join(CANDS,x['id']+'.lean')).st_mtime)
                    queued.add(g['id'])
                    prepared[g['id']]=prepare_pool.submit(check_prepared,g)
            for g in sorted((g for g in gaps if g['id'] in fam),
                            key=lambda g: (g['id'] not in held, fam[g['id']] != 'onenot', g.get('pr_open', 0) > 0,
                                           g['statement'].count(',') if fam[g['id']] == 'onenot' else 0,
                                           -int(re.sub(r'\D', '', g['id']) or 0))):
                if g.get('pr_open', 0) and g['id'] not in held:
                    continue
                if len(outstanding) >= REMOTE_WORKERS:
                    break
                if g['id'] not in queued and retryable(g['id']):
                    queued.add(g['id'])
                    outstanding[g['id']] = pool.submit(generate, g, engines)
            # Constructive plugins use an independent bounded pool; expensive
            # lower-bound searches cannot consume their capacity.
            try:
                import plugins
                found = plugins.discover()
                if found:
                    for g in sorted(concrete, key=lambda g: (g['id'] not in held, -int(re.sub(r'\D', '', g['id']) or 0))):
                        if len(plugin_pending) >= PLUGIN_WORKERS:
                            break
                        if g['id'] in fam or (g.get('pr_open', 0) and g['id'] not in held) or g['id'] in queued:
                            continue
                        hit = plugins.family_of(g['statement'], found)
                        if hit and fresh(g['id'], hit[1]):
                            queued.add(g['id'])
                            plugin_pending[g['id']] = plugin_pool.submit(gen_plugin, g, hit[0], hit[1])
            except Exception as e:
                log('plugin poll error', type(e).__name__, str(e)[:200])
        except Exception as e:
            log('poll error', type(e).__name__, str(e)[:200])
        time.sleep(POLL)
    managed_process.stop_all()
    for executor in (pool, plugin_pool, prepare_pool):
        executor.shutdown(wait=False, cancel_futures=True)
    log('STOP file found; exiting')
    return 0


if __name__ == '__main__':
    sys.exit(main())

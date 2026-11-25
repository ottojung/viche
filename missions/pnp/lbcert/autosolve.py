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
POLL = 20
REMOTE_WORKERS = 6   # marceline-dev runs at most 6 lb-cert jobs and 3 compiles at once
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


def generate(g, engines):
    gid, mod = g['id'], g['module']
    if status(gid) is not None:
        return
    sf = os.path.join(CANDS, gid + '.stmt')
    open(sf, 'w').write(g['statement'])
    out = os.path.join(CANDS, gid + '.lean')
    t0 = time.time()
    from missions.pnp import state, support
    rec = state.load(gid)
    defer = bool(support.active(rec) and rec['statement'] == g['statement'])
    p = managed_process.run([sys.executable, os.path.join(HERE, 'lbremote.py'), sf, mod, out,
                        '--maxstates', str(MAXSTATES), '--chunks', '40'] + (['--defer-compile'] if defer else []), capture_output=True, text=True, timeout=2000)
    try:
        r = json.loads(p.stdout.strip().split('\n')[-1])
    except Exception:
        r = {'status': 'relay_error'}
    where = 'marceline'
    if p.returncode == 1 and lbparse.family(g['statement']) in ('mono', 'onenot'):
        log('generate deferred', gid, r.get('status'), '%.0fs' % (time.time() - t0))
        return
    if p.returncode == 1:   # relay or handler trouble: build here, slower but independent
        if not LOCAL_FALLBACK.acquire(blocking=False):
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
    if r.get('status')=='ok' and r.get('compiled'):
        from missions.pnp.lbcert import ready
        ready.record(gid,r,open(out,'rb').read())
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
        p = managed_process.run([sys.executable, os.path.join(HERE, 'sibremote.py'), sf, rec['module'], out,
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
        log('plugin', name, gid, 'check deferred', res.get('status'))
        return
    if crc == 0:
        os.replace(out + '.gen', out)
        ready.record(gid,dict(res,status='ok',compiled=True),data)
        write_status(gid, 'ok plugin %s %s marceline compiled secs=%.0f' % (name, sha, time.time() - t0))
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
            gitctl.ensure_mirror()      # fresh upstream/main: new merges are new siblings
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
    queued = QUEUED
    outstanding = {}
    prepared = {}
    prepare_retry = {}
    while not os.path.exists(os.path.join(WORK, 'STOP')):
        if source_changed():
            # Exit now: returning would drop our flock while interpreter shutdown keeps draining the
            # pool's queue, so a second instance would run beside this one (seen 2026-11-25).
            log('source changed; exiting for clean restart')
            managed_process.stop_all()
            pool.shutdown(wait=False, cancel_futures=True)
            os._exit(0)
        try:
            for gid, future in list(outstanding.items()):
                if future.done():
                    try:future.result()
                    except Exception as e:log('generator interrupted',gid,type(e).__name__,str(e)[:160])
                    outstanding.pop(gid)
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
            concrete = [g for g in gaps if isinstance(g.get('statement'), str)]
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
            if not prepared and len(outstanding)<REMOTE_WORKERS:
                choices=[g for g in concrete if g['id'] not in held and g['id'] not in queued
                         and g['id'] not in prepare_retry and not g.get('pr_open',0)
                         and (status(g['id']) or '').split(' ')[0] in ('ok','generated')
                         and os.path.isfile(os.path.join(CANDS,g['id']+'.lean'))
                         and not ready.verified(g['id'])]
                if choices:
                    # Prefer recent, cheaply solved candidates; no old FIFO backlog.
                    g=max(choices,key=lambda x:os.stat(os.path.join(CANDS,x['id']+'.lean')).st_mtime)
                    queued.add(g['id'])
                    prepared[g['id']]=pool.submit(check_prepared,g)
            for g in sorted((g for g in gaps if g['id'] in fam),
                            key=lambda g: (g['id'] not in held, fam[g['id']] != 'onenot', g.get('pr_open', 0) > 0,
                                           g['statement'].count(',') if fam[g['id']] == 'onenot' else 0,
                                           -int(re.sub(r'\D', '', g['id']) or 0))):
                if g.get('pr_open', 0) and g['id'] not in held:
                    continue
                if len(outstanding)+len(prepared) >= REMOTE_WORKERS:
                    break
                if g['id'] not in queued and status(g['id']) is None:
                    queued.add(g['id'])
                    outstanding[g['id']] = pool.submit(generate, g, engines)
            # Generator plugins share the same bounded queue and future lifecycle.
            try:
                import plugins
                found = plugins.discover()
                if found:
                    for g in sorted(concrete, key=lambda g: (g['id'] not in held, -int(re.sub(r'\D', '', g['id']) or 0))):
                        if len(outstanding)+len(prepared) >= REMOTE_WORKERS:
                            break
                        if g['id'] in fam or (g.get('pr_open', 0) and g['id'] not in held) or g['id'] in queued:
                            continue
                        hit = plugins.family_of(g['statement'], found)
                        if hit and fresh(g['id'], hit[1]):
                            queued.add(g['id'])
                            outstanding[g['id']] = pool.submit(gen_plugin, g, hit[0], hit[1])
            except Exception as e:
                log('plugin poll error', type(e).__name__, str(e)[:200])
        except Exception as e:
            log('poll error', type(e).__name__, str(e)[:200])
        time.sleep(POLL)
    managed_process.stop_all()
    pool.shutdown(wait=False, cancel_futures=True)
    log('STOP file found; exiting')
    return 0


if __name__ == '__main__':
    sys.exit(main())

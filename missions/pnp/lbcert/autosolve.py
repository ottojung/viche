#!/usr/bin/env python3
"""Pre-generate lb_cert candidates for every open concrete circuit-size step on the public desk.

Why: concrete lower-bound steps ("Table 2: ... at least K gates", "Graph t5-...") are won within
10-20 minutes of posting. Local generation and candidate preservation remain enabled; all Lean
checks must run through the managed compiler from an exact bound workspace.

Every POLL seconds: read the public desk file, classify statements with lbparse, and generate a
certificate locally for each new concrete step. Out-of-host proof generation/check transports are
disabled unconditionally. Output under PNP_STATE_ROOT/lbcert:
  cands/<gap>.lean, cands/<gap>.status   ok ENGINE | false | toobig | unsupported | error
  twins.json   {negation-twin gap id: lower-bound gap id}
  desk.json    {gap id: pr_open} for the concrete family
The allocator fast lane (missions/pnp/fastlane.py) consumes these files: it submits ready
candidates for held steps and settles held false twins. This process never touches leases.

run: python3 -m missions.pnp.lbcert.autosolve   (allocator.sh keeps exactly one running)
maintenance: python3 -m missions.pnp.pause maintenance --author AUTHOR --reason REASON
emergency: touch PNP_STATE_ROOT/lbcert/STOP
"""
import fcntl, hashlib, json, os, re, subprocess, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lbparse  # noqa: E402
import process as managed_process
import threading
from missions.pnp import pause, surge
LOCAL_FALLBACK = threading.BoundedSemaphore(1)

# Python retains imported helpers in memory even when their files are deployed.
# Include runtime sources and generator data; ignore docs, tests and bytecode.
# A clean restart is required for the registry and imported helpers to agree.
def runtime_hash(root=None):
    root=Path(root) if root is not None else Path(HERE).parent
    h=hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.suffix in (".py",".c",".sh",".json") and path.is_file():
            h.update(str(path.relative_to(root)).encode()+b"\0")
            h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()


START_HASH = runtime_hash()


def source_changed():
    try:
        return runtime_hash()!=START_HASH
    except OSError:
        return False


def drain_workers(executors):
    """Stop generator subprocess trees, then finish durable publisher/broker calls.

    Never drop the singleton lock while executor threads could still make a
    desk or publication mutation. Detached canonical publisher jobs are fenced
    separately and are not killed by this generator guardian.
    """
    managed_process.stop_all()
    for executor in executors:
        executor.shutdown(wait=True,cancel_futures=True)


STATE = os.environ.get('PNP_STATE_ROOT', '/var/lib/lubko/wd/viche-state/pnp')
WORK = os.path.join(STATE, 'lbcert')
CANDS = os.path.join(WORK, 'cands')
DESK = 'https://data.pequalnp.com/data/desk/gaps.json'
SOURCE = 'https://raw.githubusercontent.com/open-goat/pequalnp-proofs/main/lean/PEqualNP/Outside/L_meta_7281.lean'
SOURCE_SHA = '98c3a7192bc0d62775011eb073a212c7a2d0d9bf4da12e0e11980fd2fe002c74'
POLL = 10            # gaps.json is a conditional GET now (304 when unchanged)
LOCAL_GENERATORS = 1   # bounded local lower-bound generation
PLUGIN_WORKERS = 2   # constructive generators cannot be starved by lower-bound search
PREPARE_WORKERS = 1  # exact checked receipt for a completed candidate
LB_MAX_INPUTS = 12   # see generate(): no lb_cert has ever succeeded above 11 inputs
MAXSTATES = 4800       # keep local candidate generation below the 512 KiB certificate bound
GEN_TIMEOUT = 300      # bounded local CPU work; generation never invokes Lean
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
    # Complete frontier observations own the first-sighting clock.
    # This legacy hook must not label stale/open-cache IDs as new.
    return None

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
    if not engines:
        write_status(gid, 'deferred local engine unavailable')
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
    try:
        # Local bounded generator only. This constructs proof bytes but does not
        # claim compilation; exact checking is a separate managed-workspace lane.
        p = managed_process.run([sys.executable, 'lbassemble.py', engines[0], mod, sf, out + '.tmp',
                            '--maxstates', str(MAXSTATES), '--chunks', '40'],
                           cwd=HERE, capture_output=True, text=True, timeout=GEN_TIMEOUT)
    except subprocess.TimeoutExpired:
        # A hung local generator must not monopolize the bounded worker.
        write_status(gid, 'deferred generation timeout %ss' % GEN_TIMEOUT)
        from missions.pnp import ledger
        ledger.mark('generated', gid, status='timeout', secs=GEN_TIMEOUT, where='billy-dev')
        log('generated', gid, 'timeout', 'billy-dev', None, '%ss' % GEN_TIMEOUT)
        return
    where = 'billy-dev'
    if pause.paused_directory(WORK):
        return
    r = {'status': {0: 'ok', 2: 'unsupported', 3: 'false', 4: 'toobig'}.get(p.returncode, 'error'),
         'engine': os.path.basename(engines[0]) if engines else None}
    if p.returncode == 0 and os.path.isfile(out + '.tmp'):
        os.replace(out + '.tmp', out)
    from missions.pnp import ledger
    ledger.mark('generated', gid, status=r.get('status'), secs=round(time.time() - t0), where=where)
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
    """Refresh the local sibling index; do not generate/check via another host."""
    import sibling
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
    from missions.pnp import gitctl
    head, idx = sibling.index(gitctl.MIRROR, WORK)
    log('local sibling index', head[:12], 'shapes', len(idx or {}),
        'adaptation disabled until exact bound managed check')


def gen_plugin(g, name, sha):
    """A town-written local plugin: generate and validate, then check only in bound workspaces."""
    import plugins
    from missions.pnp import state, support, validate, fastlane, ledger
    from missions.pnp.lbcert import ready
    gid = g['id']
    sf = os.path.join(CANDS, gid + '.stmt')
    open(sf, 'w').write(g['statement'])
    sketch=g.get('sketch') or ''
    open(sf+'.sketch','w').write(sketch if isinstance(sketch,str) else '')
    out = os.path.join(CANDS, gid + '.lean')
    t0 = time.time()
    rc, why = plugins.run(name, gid, sf, out + '.gen')
    if pause.paused_directory(WORK):
        return
    ledger.mark('generated',gid,status='ok' if rc==0 else 'failed',engine=name,secs=round(time.time()-t0,3))
    if rc != 0:
        write_status(gid, '%s plugin %s %s rc=%s %s' % ('unsupported' if rc == 3 else 'failed', name, sha, rc,
                                                     why.strip().replace('\n', ' ')[-160:]))
        log('plugin', name, gid, 'rc', rc, '%.0fs' % (time.time() - t0))
        return
    # Statically validate exact output before any publication or managed local check.
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
        fastlane.submit_ready(gid)
        return
    from missions.pnp.lbcert import checklocal
    crc, res = checklocal.check(out + '.gen', g['module'])
    if crc == 2:
        os.replace(out + '.gen', out)
        write_status(gid, 'generated plugin %s %s check deferred' % (name, sha))
        log('plugin', name, gid, 'check deferred', res.get('status'))
        return
    if crc == 0:
        os.replace(out + '.gen', out)
        recorded = ready.record(gid,dict(res,status='ok',compiled=True),data)
        write_status(gid, 'ok plugin %s %s managed-local compiled secs=%.0f' % (name, sha, time.time() - t0))
        if recorded:
            lease_now(gid)
    else:
        write_status(gid, 'failed plugin %s %s compile: %s' % (name, sha, (res.get('log') or '').replace('\n', ' ')[-160:]))
    log('plugin', name, gid, 'ok' if crc == 0 else 'compile_error', '%.0fs' % (time.time() - t0))


def check_prepared(g):
    if pause.paused_directory(WORK):
        return
    from missions.pnp.lbcert import checklocal
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
    code,result=checklocal.check(path,g['module'],timeout=600)
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
    """Retain the local corpus index; sibling adaptation is deliberately not auto-checked."""
    sibling_pass()


def sibling_loop():
    while not pause.paused_directory(WORK):
        if surge.active():
            time.sleep(30)
            continue
        try:
            sibling_pass()
        except Exception as e:
            log('sibling error', type(e).__name__, str(e)[:200])
        time.sleep(30)


def sweep_loop():
    last_radar = 0
    while not pause.paused_directory(WORK):
        if surge.active():
            time.sleep(30)
            continue
        try:
            if time.time() - last_radar > 600:
                last_radar = time.time()
                from missions.pnp import radar   # family radar + tool/method backlogs
                radar.write(radar.build())
            sweep_pass()
        except Exception as e:
            log('sweep error', type(e).__name__, str(e)[:200])
        time.sleep(120)


def promise_batch_loop():
    """Independent shared-table lane; the guardian kills it with autosolve."""
    while not pause.paused_directory(WORK):
        try:
            p=managed_process.run([sys.executable,"-m","missions.pnp.lbcert.generators.promise.batch"],timeout=900)
            if p.returncode:log("promise batch deferred",p.returncode)
        except Exception as e:
            log("promise batch error",type(e).__name__,str(e)[:180])
        time.sleep(5)


def main():
    lock = open(os.path.join(WORK, 'autosolve.lock'), 'w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return 0
    if pause.paused_directory(WORK):
        log('STOP file found; exiting before starting workers')
        return 0
    engines = ensure_engines()
    import threading
    threading.Thread(target=sibling_loop, daemon=True).start()
    threading.Thread(target=sweep_loop, daemon=True).start()
    threading.Thread(target=promise_batch_loop, daemon=True).start()
    pool = ThreadPoolExecutor(LOCAL_GENERATORS)
    plugin_pool = ThreadPoolExecutor(PLUGIN_WORKERS)
    prepare_pool = ThreadPoolExecutor(PREPARE_WORKERS)
    queued = QUEUED
    outstanding = {}
    plugin_pending = {}
    prepared = {}
    prepare_retry = {}
    while not pause.paused_directory(WORK):
        if source_changed():
            log('runtime changed; draining workers for clean restart')
            drain_workers((pool,plugin_pool,prepare_pool))
            return 0
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
            records=cli.held_records()
            held = {r['gap_id'] for r in records}
            posting_held={r['gap_id'] for r in records if r.get('work_lane')=='posting'}
            from missions.pnp import fastlane
            for gid in held-posting_held:
                try:fastlane.submit_ready(gid)
                except Exception as exc:log('held candidate deferred',gid,str(exc)[:120])
            from missions.pnp.lbcert import ready
            # The held posting lane owns batch-time CPU. Continue catalog and
            # cached-candidate publication, but start no new speculative
            # certificate builds or per-instance background searches.
            if surge.active():
                time.sleep(POLL)
                continue
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
                if g['id'] in posting_held or (g.get('pr_open', 0) and g['id'] not in held):
                    continue
                if len(outstanding) >= LOCAL_GENERATORS:
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
                    from missions.pnp.lbcert.generators.promise import batch
                    batch_active=batch.alive()
                    batch_fallback=batch.fallback_keys() if batch_active else set()
                    for g in sorted(concrete, key=lambda g: (g['id'] not in held, not ('A held answer' in str(g.get('sketch') or '')), -int(re.sub(r'\D', '', g['id']) or 0))):
                        if len(plugin_pending) >= PLUGIN_WORKERS:
                            break
                        if g['id'] in posting_held or g['id'] in fam or (g.get('pr_open', 0) and g['id'] not in held) or g['id'] in queued:
                            continue
                        if batch_active and batch.claimed(g,batch_fallback):
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
    drain_workers((pool,plugin_pool,prepare_pool))
    log('STOP file found; exiting')
    return 0


if __name__ == '__main__':
    sys.exit(main())

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
stop: touch PNP_STATE_ROOT/lbcert/STOP
"""
import fcntl, hashlib, json, os, re, subprocess, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

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
SOURCE_FILES = (
    Path(HERE) / "autosolve.py",
    Path(HERE) / "plugins.py",
    Path(HERE) / "generators" / "promise" / "stock_index.py",
    Path(HERE) / "ready.py",
    Path(HERE) / "live.py",
    Path(HERE).parent / "fastlane.py",
    Path(HERE).parent / "jobs.py",
)


def source_digest():
    h = hashlib.sha256()
    for path in SOURCE_FILES:
        h.update(str(path).encode() + b"\0")
        try:
            h.update(path.read_bytes())
        except OSError:
            h.update(b"\0missing")
    return h.hexdigest()


START_HASH = source_digest()


def source_changed():
    return source_digest() != START_HASH

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
    if os.path.exists(os.path.join(WORK, 'STOP')):
        return
    r = {'status': {0: 'ok', 2: 'unsupported', 3: 'false', 4: 'toobig'}.get(p.returncode, 'error'),
         'engine': os.path.basename(engines[0]) if engines else None}
    if p.returncode == 0 and os.path.isfile(out + '.tmp'):
        if not stage_bytes(out+'.tmp',out):
            write_status(gid,'deferred existing candidate differs; alternate retained')
            return
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


def stage_bytes(source,out):
    """Publish candidate bytes atomically without replacing any earlier proof."""
    try:
        os.link(source,out)
        os.unlink(source)
        return True
    except FileExistsError:
        if not os.path.islink(out) and Path(source).read_bytes()==Path(out).read_bytes():
            os.unlink(source)
            return True
        return False


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
    try:
        rc, why = plugins.run(name, gid, sf, out + '.gen')
    except (OSError, subprocess.SubprocessError) as exc:
        rc, why = 75, type(exc).__name__ + ': ' + str(exc)
    if os.path.exists(os.path.join(WORK, 'STOP')):
        return
    ledger.mark('generated',gid,status='ok' if rc==0 else 'failed',engine=name,secs=round(time.time()-t0,3))
    if rc != 0:
        outcome = 'unsupported' if rc == 3 else 'deferred' if rc in (75, 124) else 'failed'
        write_status(gid, '%s plugin %s %s rc=%s %s' % (outcome, name, sha, rc,
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
    if not stage_bytes(out+'.gen',out):
        # An existing checked or generated proof is not ours to replace.
        # Keep the new alternate as .gen for inspection; no receipt created.
        if status(gid) is None:
            write_status(gid,'deferred alternate retained; existing bytes not attributed')
        if support.active(rec) and rec['statement']==g['statement']:
            from missions.pnp import jobs
            jobs.submit(gid,out+'.gen',expected_lease=rec['lease'],only_unclaimed=True)
        return
    write_status(gid,'generated plugin %s %s staged for private check'%(name,sha))
    if support.active(rec) and rec['statement']==g['statement']:
        fastlane.submit_ready(gid)
    else:
        log('plugin',name,gid,'staged, not checked')


def check_prepared(g):
    """Compatibility entry point: unheld candidates belong to private intake."""
    if os.path.exists(os.path.join(WORK,'STOP')):
        return
    from missions.pnp import state,support,fastlane
    rec=state.load(g['id'])
    if support.active(rec) and rec.get('statement')==g.get('statement'):
        fastlane.submit_ready(g['id'])


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
    """No status yet, or a plugin refused/failed it with an older generation version."""
    st = status(gid)
    if st is None:
        return True
    m = re.match(r'(unsupported|failed|deferred) plugin \S+ (\w+)', st)
    return bool(m and ((plugin_sha and m.group(2) != plugin_sha)
                       or (m.group(1) == 'deferred' and retryable(gid))))


def generation_rank(gap, held, recent):
    """Actual first observation precedes numeric IDs, without extra I/O."""
    gid = gap['id']
    return (gid not in held, gid not in recent,
            gap.get('offerable_now') is not True)


SWEEP_STATE = os.path.join(WORK, 'sweep.json')
SWEEP_MAX_TRIES = 4


def sweep_pass():
    """Retain the local corpus index; sibling adaptation is deliberately not auto-checked."""
    sibling_pass()


def sibling_loop():
    while not os.path.exists(os.path.join(WORK, 'STOP')):
        try:
            sibling_pass()
        except Exception as e:
            log('sibling error', type(e).__name__, str(e)[:200])
        time.sleep(30)


def sweep_loop():
    last_radar = 0
    while not os.path.exists(os.path.join(WORK, 'STOP')):
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
    while not os.path.exists(os.path.join(WORK, 'STOP')):
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
    if os.path.exists(os.path.join(WORK, 'STOP')):
        log('STOP file found; exiting before starting workers')
        return 0
    engines = ensure_engines()
    import threading
    threading.Thread(target=sibling_loop, daemon=True).start()
    threading.Thread(target=sweep_loop, daemon=True).start()
    threading.Thread(target=promise_batch_loop, daemon=True).start()
    pool = ThreadPoolExecutor(LOCAL_GENERATORS)
    plugin_pool = ThreadPoolExecutor(PLUGIN_WORKERS)
    queued = QUEUED
    outstanding = {}
    plugin_pending = {}
    while not os.path.exists(os.path.join(WORK, 'STOP')):
        if source_changed():
            # Exit now: returning would drop our flock while interpreter shutdown keeps draining the
            # pool's queue, so a second instance would run beside this one (seen 2026-11-25).
            log('source changed; exiting for clean restart')
            managed_process.stop_all()
            for executor in (pool, plugin_pool):
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
            from missions.pnp import cli, freshness
            records=cli.held_records()
            recent=freshness.recent()
            held = {r['gap_id'] for r in records}
            posting_held={r['gap_id'] for r in records if r.get('work_lane')=='posting'}
            from missions.pnp import fastlane
            for gid in held-posting_held:
                try:fastlane.submit_ready(gid)
                except Exception as exc:log('held candidate deferred',gid,str(exc)[:120])
            from missions.pnp.lbcert import ready
            for g in sorted((g for g in gaps if g['id'] in fam),
                            key=lambda g: (*generation_rank(g, held, recent), fam[g['id']] != 'onenot', g.get('pr_open', 0) > 0,
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
                    for g in sorted(concrete, key=lambda g: (*generation_rank(g, held, recent), not ('A held answer' in str(g.get('sketch') or '')), -int(re.sub(r'\D', '', g['id']) or 0))):
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
    managed_process.stop_all()
    for executor in (pool, plugin_pool):
        executor.shutdown(wait=False, cancel_futures=True)
    log('STOP file found; exiting')
    return 0


if __name__ == '__main__':
    sys.exit(main())

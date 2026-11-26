"""The live desk frontier: which steps are open right now (desk/status), with holders and points.

data/desk/gaps.json lists ~25% more steps than are open (2026-11-26: 2359 vs 1827): sub-steps of
cuts, waiting twins and steps already closed.  Generating, checking or asking proof-of leases for
those is wasted work (four checked proofs sat unpublishable for hours because their steps had
closed).  open_ids() returns the live open set, cached for CACHE_SECONDS in
PNP_STATE_ROOT/lbcert/live.json; None when the desk cannot be read (callers then keep their old
behaviour, never "nothing is open").
"""
import fcntl
import json
import os
import time
import threading
import urllib.error
import urllib.request

STATE = os.environ.get('PNP_STATE_ROOT', '/var/lib/lubko/wd/viche-state/pnp')
CACHE = os.path.join(STATE, 'lbcert', 'live.json')
URL = 'https://pequalnp.com/desk/status?handle=ottojung'
CACHE_SECONDS = 60


def snapshot(max_age=CACHE_SECONDS):
    try:
        d = json.load(open(CACHE))
        if time.time() - d['at'] < max_age:
            return d
    except (OSError, ValueError, KeyError):
        pass
    try:
        s = status_doc(max_age=max_age)
        gaps = {g['id']: {k: g.get(k) for k in ('held', 'parallel', 'points', 'level', 'kind')}
                for g in s.get('gaps', []) if isinstance(g, dict) and g.get('id')}
        if not gaps:
            return None
        d = {'at': time.time(), 'updated_at': s.get('updated_at'), 'gaps': gaps}
        tmp = '%s.%d.%d.tmp' % (CACHE, os.getpid(), threading.get_ident())
        json.dump(d, open(tmp, 'w'))
        os.replace(tmp, CACHE)
        return d
    except Exception:
        try:
            d = json.load(open(CACHE))      # stale but real beats nothing for up to 15 minutes
            return d if time.time() - d['at'] < 900 else None
        except (OSError, ValueError, KeyError):
            return None


STATUS_CACHE = os.path.join(STATE, 'lbcert', 'status-cache.json')


def status_doc(max_age=15, timeout=45):
    """The whole desk/status document (420 kB, 2-4 s from billy-dev), shared by the allocator's
    frontier snapshot and this module: one fetch per max_age seconds instead of one per caller."""
    try:
        if time.time() - os.path.getmtime(STATUS_CACHE) < max_age:
            return json.load(open(STATUS_CACHE))
    except (OSError, ValueError):
        pass
    r = urllib.request.Request(URL, headers={'User-Agent': 'viche-town', 'Accept-Encoding': 'gzip'})
    resp = urllib.request.urlopen(r, timeout=timeout)
    body = resp.read()
    if resp.headers.get('Content-Encoding') == 'gzip':
        import gzip
        body = gzip.decompress(body)
    s = json.loads(body)
    if not isinstance(s, dict) or 'open_gaps' not in s:
        raise ValueError('unexpected desk status shape')
    tmp = '%s.%d.%d.tmp' % (STATUS_CACHE, os.getpid(), threading.get_ident())
    open(tmp, 'wb').write(body)
    os.replace(tmp, STATUS_CACHE)
    return s


GAPS_URL = 'https://data.pequalnp.com/data/desk/gaps.json'
GAPS_CACHE = os.path.join(STATE, 'lbcert', 'gaps-cache.json')


def gaps_bytes(timeout=40, max_age=15):
    """Share one catalog request across callers; never refresh age on failure."""
    os.makedirs(os.path.dirname(GAPS_CACHE), exist_ok=True)
    def cached(age):
        try:
            with open(GAPS_CACHE + '.meta') as f:
                m = json.load(f)
            if 0 <= time.time() - m['at'] <= age:
                with open(GAPS_CACHE, 'rb') as f:
                    return f.read()
        except (OSError, ValueError, KeyError, TypeError):
            return None
    with open(GAPS_CACHE + '.lock', 'a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            body = cached(600)
            if body is not None:
                return body
            raise OSError("catalog refresh already running and no usable cache")
        body = cached(max_age)
        return body if body is not None else _fetch_gaps(timeout)


def _fetch_gaps(timeout):
    """gaps.json is 6.2 MB (850 kB gzipped) and was fetched whole every 20 s by autosolve, plus by
    the sweep and the radar.  Ask with gzip and If-None-Match against one shared on-disk copy:
    unchanged -> 304 and the cached bytes; a failure with a copy younger than 10 minutes -> the
    copy.  Same bytes as an unconditional GET."""
    import gzip
    meta = GAPS_CACHE + '.meta'
    try:
        m = json.load(open(meta))
    except (OSError, ValueError):
        m = {}
    headers = {'User-Agent': 'viche-town', 'Accept-Encoding': 'gzip'}
    if m.get('etag') and os.path.exists(GAPS_CACHE):
        headers['If-None-Match'] = m['etag']
    try:
        r = urllib.request.urlopen(urllib.request.Request(GAPS_URL, headers=headers), timeout=timeout)
        body = r.read()
        if r.headers.get('Content-Encoding') == 'gzip':
            body = gzip.decompress(body)
        doc = json.loads(body)
        if not isinstance(doc, dict) or not isinstance(doc.get('gaps'), list):
            raise ValueError('unexpected catalog shape')
        tmp = '%s.%d.%d.tmp' % (GAPS_CACHE, os.getpid(), threading.get_ident())
        open(tmp, 'wb').write(body)
        os.replace(tmp, GAPS_CACHE)
        m = {'etag': r.headers.get('ETag'), 'at': time.time()}
        tmp = '%s.%d.%d.tmp' % (meta, os.getpid(), threading.get_ident())
        json.dump(m, open(tmp, 'w'))
        os.replace(tmp, meta)
        return body
    except urllib.error.HTTPError as e:
        if e.code == 304 and os.path.exists(GAPS_CACHE):
            m['at'] = time.time()
            tmp = '%s.%d.%d.tmp' % (meta, os.getpid(), threading.get_ident())
            json.dump(m, open(tmp, 'w'))
            os.replace(tmp, meta)
            return open(GAPS_CACHE, 'rb').read()
        raise
    except Exception:
        if os.path.exists(GAPS_CACHE) and time.time() - m.get('at', 0) < 600:
            return open(GAPS_CACHE, 'rb').read()
        raise


def open_ids():
    d = snapshot()
    return set(d['gaps']) if d else None


def points(gid):
    d = snapshot()
    return ((d or {}).get('gaps', {}).get(gid) or {}).get('points') or 0

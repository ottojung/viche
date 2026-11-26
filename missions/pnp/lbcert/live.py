"""The live desk frontier: which steps are open right now (desk/status), with holders and points.

data/desk/gaps.json lists ~25% more steps than are open (2026-11-26: 2359 vs 1827): sub-steps of
cuts, waiting twins and steps already closed.  Generating, checking or asking proof-of leases for
those is wasted work (four checked proofs sat unpublishable for hours because their steps had
closed).  open_ids() returns the live open set, cached for CACHE_SECONDS in
PNP_STATE_ROOT/lbcert/live.json; None when the desk cannot be read (callers then keep their old
behaviour, never "nothing is open").
"""
import json
import os
import time
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
        r = urllib.request.Request(URL, headers={'User-Agent': 'viche-town'})
        s = json.loads(urllib.request.urlopen(r, timeout=45).read())
        gaps = {g['id']: {k: g.get(k) for k in ('held', 'parallel', 'points', 'level', 'kind')}
                for g in s.get('gaps', []) if isinstance(g, dict) and g.get('id')}
        if not gaps:
            return None
        d = {'at': time.time(), 'updated_at': s.get('updated_at'), 'gaps': gaps}
        tmp = CACHE + '.tmp'
        json.dump(d, open(tmp, 'w'))
        os.replace(tmp, CACHE)
        return d
    except Exception:
        try:
            d = json.load(open(CACHE))      # stale but real beats nothing for up to 15 minutes
            return d if time.time() - d['at'] < 900 else None
        except (OSError, ValueError, KeyError):
            return None


def open_ids():
    d = snapshot()
    return set(d['gaps']) if d else None


def points(gid):
    d = snapshot()
    return ((d or {}).get('gaps', {}).get(gid) or {}).get('points') or 0

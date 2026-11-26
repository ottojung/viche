"""Desk broker: the only component allowed to claim, renew or release leases.

Research agents never call this module.  All requests are rate limited and
retry with backoff; a parse error is never converted into "no gap" (fail
closed).  Live instructions are re-read on startup rather than trusting the
stale 30-minute beat comment in tools/pnp.sh.
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from . import config


class DeskError(Exception):
    pass


def http_request(method, url, params=None):
    """Return (status, text).  Injected in unit tests."""
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, data=(b"" if method == "POST" else None),
                                 method=method, headers={"User-Agent": "curl/8.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


class Desk:
    def __init__(self, request=None, min_interval=None, sleep=None):
        self.request = request or http_request
        self.min_interval = (config.REQUEST_MIN_INTERVAL
                             if min_interval is None else min_interval)
        self.sleep = sleep or time.sleep
        self.last = 0.0

    def _call(self, method, path, params=None, expect_json=True):
        now = time.monotonic()
        wait = self.min_interval - (now - self.last)
        if wait > 0:
            self.sleep(wait)
        url = config.DESK_BASE + path
        delay = 1.0
        for attempt in range(5):
            self.last = time.monotonic()
            try:
                status, text = self.request(method, url, params)
            except Exception as e:                      # network outage
                if attempt == 4:
                    raise DeskError("desk request failed: %s" % e)
                self.sleep(delay)
                delay *= 2
                continue
            if status == 429 or 500 <= status < 600:
                if attempt == 4:
                    raise DeskError("desk HTTP %d after retries" % status)
                self.sleep(delay)
                delay *= 2
                continue
            if status == 410:
                return 410, ("gone" if expect_json else text)
            if status != 200:
                raise DeskError("desk HTTP %d: %s" % (status, text[:300]))
            if not expect_json:
                return status, text
            try:
                return status, json.loads(text)
            except ValueError as e:
                raise DeskError("desk returned invalid JSON: %s" % e)
        raise DeskError("desk unavailable")

    def docs(self, refresh=False):
        """Re-read the live join.txt; cache only with a timestamp."""
        if not refresh and os.path.exists(config.DOCS_CACHE):
            age = time.time() - os.path.getmtime(config.DOCS_CACHE)
            if age < 6 * 3600:
                with open(config.DOCS_CACHE, encoding="utf-8") as f:
                    return f.read()
        req = urllib.request.Request(config.JOIN_URL, headers={"User-Agent": "curl/8.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                text = r.read().decode("utf-8", "replace")
        except Exception as e:
            if os.path.exists(config.DOCS_CACHE):
                with open(config.DOCS_CACHE, encoding="utf-8") as f:
                    return f.read()
            raise DeskError("cannot read live desk docs: %s" % e)
        os.makedirs(config.CACHE_DIR, exist_ok=True)
        from .state import atomic_write
        atomic_write(config.DOCS_CACHE, text)
        return text

    def status(self):
        """Read-only.  Never infer an empty frontier from a parser failure."""
        _, data = self._call("GET", "/status", {"handle": config.DESK_HANDLE})
        if not isinstance(data, dict) or "open_gaps" not in data:
            raise DeskError("unexpected desk status shape")
        return data

    def next_gap(self, hard=False, another=False):
        raise DeskError("next is a mutating acquisition, not a diagnostic. "
                        "Use status; the automatic allocator records every claim.")

    def _next_gap(self, hard=False, another=False, proof_of=None):
        """Private wire operation; only the locked, recording broker calls it."""
        params = {"handle": config.DESK_HANDLE}
        if hard:
            params["hard"] = "1"
        if another:
            params["another"] = "1"
        if proof_of is not None:
            if not config.GAP_ID_RE.fullmatch(proof_of):
                raise DeskError("invalid proof-of gap")
            params.update(gap=proof_of, have="proof")
        _, data = self._call("GET", "/next", params)
        if not isinstance(data, dict):
            raise DeskError("unexpected desk next shape")
        gap = data.get("gap")
        lease = data.get("lease")
        if gap is None:
            # join.txt: "If `gap` is null, every step is taken right now:
            # wait a few minutes and ask again."  That documented empty-frontier
            # answer omits `lease`, so an explicit null gap is no-gap regardless
            # of whether a lease key is present.  A *missing* gap key or a
            # malformed shape stays a protocol error: never turn a parser
            # failure into "no gaps" (fail closed).
            if "gap" in data:
                return None
            raise DeskError("desk next is missing gap key")
        if lease is None:
            raise DeskError("desk next offered a gap without a lease")
        if not isinstance(gap, dict):
            raise DeskError("desk gap is not an object")
        return {"gap": gap, "lease": lease, **{k: data[k] for k in ("shard", "shards") if k in data}}

    def beat(self, lease):
        status, _ = self._call("POST", "/beat", {"lease": lease},
                               expect_json=False)
        return status  # 410 means the gap was settled/withdrawn: stop work

    def release(self, lease, reason, program=None):
        if reason not in config.RELEASE_REASONS:
            raise DeskError("unknown release reason: %r" % reason)
        params = {"lease": lease, "reason": reason}
        if program is not None:
            params["program"] = program
        _, data = self._call("POST", "/release", params)
        return data

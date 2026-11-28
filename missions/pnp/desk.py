"""Desk broker: the only component allowed to claim, renew or release leases.

Research agents never call this module.  All requests are rate limited and
retry with backoff; a parse error is never converted into "no gap" (fail
closed).  Live instructions are re-read on startup rather than trusting the
stale 30-minute beat comment in tools/pnp.sh.
"""
import json
import math
from email.utils import parsedate_to_datetime
import fcntl
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from . import config


class DeskError(Exception):
    pass


def retry_path():
    return os.path.join(config.STATE_ROOT, "desk-retry.json")


def _retry_data():
    try:
        with open(retry_path()) as f:obj=json.load(f)
        return obj if isinstance(obj,dict) else {}
    except (OSError,ValueError,TypeError):
        return {}


def retry_until(target=None):
    data=_retry_data()
    values=[data.get("until",0)]
    if target:
        targets=data.get("targets")
        if isinstance(targets,dict):values.append(targets.get(target,0))
    return max((v for v in values if type(v) in (float,int)),default=0)


def positive_seconds(value):
    try:return type(value) in (int,float) and math.isfinite(value) and value>0
    except OverflowError:return False


def record_retry(data,target=None):
    seconds=data.get("retry_after_s")
    if not positive_seconds(seconds):return
    from . import state
    os.makedirs(config.STATE_ROOT,exist_ok=True)
    with open(os.path.join(config.STATE_ROOT,"desk-retry.lock"),"a+") as lk:
        fcntl.flock(lk,fcntl.LOCK_EX)
        now=time.time()
        obj=_retry_data()
        old_targets=obj.get("targets")
        targets={k:v for k,v in old_targets.items() if type(v) in (int,float) and v>now} if isinstance(old_targets,dict) else {}
        note=str(data.get("note") or data.get("error") or "").lower()
        if any(x in note for x in ("rate limit","too many requests","too many steps","at capacity","holding limit")):target=None
        if target:
            targets[target]=max(targets.get(target,0),now+seconds)
        else:
            obj["until"]=max(retry_until(),now+seconds)
        obj["targets"]=targets
        state.atomic_write(retry_path(),json.dumps(obj))


def _capacity_path():
    return os.path.join(config.STATE_ROOT, "desk-capacity.json")


def record_capacity(data):
    """/next reports {"holding": h, "capacity": c} ("You hold as many steps as you have earned;
    capacity grows as your proofs are checked").  Keep it so the allocator stops asking at cap."""
    cap, hold = data.get("capacity"), data.get("holding")
    if type(cap) is not int or cap < 1:
        return
    try:
        from . import state
        state.atomic_write(_capacity_path(), json.dumps(
            {"capacity": cap, "holding": hold if type(hold) is int else None, "at": time.time()}))
    except Exception:
        pass


def capacity():
    """Last desk-reported earned capacity, retained until a newer observation."""
    try:
        with open(_capacity_path()) as f:d=json.load(f)
        if type(d["capacity"]) is int and d["capacity"] >= 1:
            return d["capacity"]
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None


def lease_limit():
    """Slots we may actually fill: config.MAX_LEASES (join.txt's five) capped by the desk's
    earned capacity.  At capacity the desk answers /next with an existing lease, so asking is waste."""
    cap = capacity()
    return min(config.MAX_LEASES, cap) if cap else config.MAX_LEASES


def retry_response(body,headers=None):
    """Prefer a positive server duration; honor a longer Retry-After header too."""
    try:data=json.loads(body)
    except (ValueError,TypeError):data={}
    if not isinstance(data,dict):data={}
    seconds=data.get("retry_after_s")
    delays=[seconds] if positive_seconds(seconds) else []
    header=headers.get("Retry-After") if headers else None
    if header:
        try:delay=float(header)
        except (ValueError,TypeError):
            try:delay=parsedate_to_datetime(header).timestamp()-time.time()
            except (ValueError,TypeError,OverflowError):delay=0
        if positive_seconds(delay):delays.append(delay)
    data["retry_after_s"]=max(delays,default=60)
    return data


def status_retry_until():
    try:
        with open(os.path.join(config.STATE_ROOT,"desk-status-retry.json")) as f:
            until=json.load(f)["until"]
        return until if positive_seconds(until) else 0
    except (OSError,ValueError,TypeError,KeyError):return 0


def record_status_retry(data):
    # Separate read-only endpoint cooldown; acquisition retry is not cleared.
    from . import state,ledger
    seconds=data.get("retry_after_s")
    if not positive_seconds(seconds):return
    os.makedirs(config.STATE_ROOT,exist_ok=True)
    with open(os.path.join(config.STATE_ROOT,"desk-status-retry.lock"),"a") as lk:
        fcntl.flock(lk,fcntl.LOCK_EX)
        until=max(status_retry_until(),time.time()+seconds)
        state.atomic_write(os.path.join(config.STATE_ROOT,"desk-status-retry.json"),json.dumps({"until":until}))
    ledger.mark("desk_rate_limit","desk",endpoint="/status",method="GET",retry_after_s=data["retry_after_s"],until=until)


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
        raw=e.read().decode("utf-8","replace")
        if e.code==429:raw=json.dumps(retry_response(raw,e.headers))
        return e.code,raw


def pace(interval,sleep=time.sleep):
    """Serialize request starts across allocator, publisher and heartbeat processes."""
    if interval<=0:return
    os.makedirs(config.STATE_ROOT,exist_ok=True)
    with open(os.path.join(config.STATE_ROOT,"desk-request.lock"),"a+") as f:
        fcntl.flock(f,fcntl.LOCK_EX)
        f.seek(0)
        try:last=float(f.read())
        except ValueError:last=0
        now=time.monotonic()
        if 0<=now-last<interval:sleep(interval-(now-last))
        f.seek(0);f.truncate();f.write(str(time.monotonic()));f.flush()


class Desk:
    def __init__(self, request=None, min_interval=None, sleep=None):
        self.request = request or http_request
        self.shared_pace = request is None
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
            if self.shared_pace:pace(self.min_interval,self.sleep)
            if path=="/next" and retry_until((params or {}).get("gap"))>time.time():
                raise DeskError("desk acquisition cooldown")
            if path=="/status" and status_retry_until()>time.time():
                raise DeskError("desk status cooldown")
            self.last = time.monotonic()
            try:
                status, text = self.request(method, url, params)
            except Exception as e:                      # network outage
                if attempt == 4:
                    raise DeskError("desk request failed: %s" % e)
                self.sleep(delay)
                delay *= 2
                continue
            if status == 429:
                data=retry_response(text)
                if path=="/status":record_status_retry(data)
                else:
                    record_retry(data)
                    from . import ledger
                    ledger.mark("desk_rate_limit","desk",endpoint=path,method=method,
                                retry_after_s=data["retry_after_s"],until=retry_until())
                raise DeskError("desk rate limited on %s; honoring retry_after_s=%s" % (path,data["retry_after_s"]))
            if 500 <= status < 600:
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

    def _next_gap(self, hard=False, another=False, proof_of=None, level=None, kind=None):
        """Private wire operation; only the locked, recording broker calls it."""
        if retry_until(proof_of) > time.time():
            return None
        params = {"handle": config.DESK_HANDLE,"model":"unknown"}
        if level is not None:
            if level not in ("warmup", "solid", "hard", "open") or proof_of is not None:
                raise DeskError("invalid level for next")
            params["level"] = level
        if kind is not None:
            if kind not in ("prove", "refute", "search", "cut", "value") or proof_of is not None:
                raise DeskError("invalid kind for next")
            params["kind"] = kind
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
        record_capacity(data)
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
                record_retry(data,proof_of)
                from . import ledger
                ledger.mark("offer_declined",proof_of or "ordinary",
                            retry_after_s=data.get("retry_after_s"),note=str(data.get("note") or "")[:200],
                            holding=data.get("holding"),capacity=data.get("capacity"),requested_kind=kind)
                return None
            raise DeskError("desk next is missing gap key")
        if lease is None:
            raise DeskError("desk next offered a gap without a lease")
        if not isinstance(gap, dict):
            raise DeskError("desk gap is not an object")
        return {"gap": gap, "lease": lease, **{k: data[k] for k in ("shard", "shards") if k in data}}

    def beat(self, lease):
        status, body = self._call("POST", "/beat", {"lease": lease},
                                  expect_json=False)
        # Keep the desk's own expiry when it states one (lease.expires_at, ISO 8601).
        self.last_expires_at = None
        try:
            import datetime
            exp = json.loads(body)["lease"]["expires_at"]
            self.last_expires_at = datetime.datetime.fromisoformat(exp.replace("Z", "+00:00")).timestamp()
        except Exception:
            pass
        return status  # 410 means the gap was settled/withdrawn: stop work

    def release(self, lease, reason, program=None):
        if reason not in config.RELEASE_REASONS:
            raise DeskError("unknown release reason: %r" % reason)
        params = {"lease": lease, "reason": reason}
        if program is not None:
            params["program"] = program
        _, data = self._call("POST", "/release", params)
        return data

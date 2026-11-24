"""Atomic, locked, append-only state for one leased gap at a time.

Every external effect is preceded by a write-ahead intent record; recovery
queries remote ground truth before retrying anything (see reconcile.py).
"""
import contextlib
import fcntl
import json
import os
import tempfile
import time

from . import config

EMPTY = {
    "gap_id": None,
    "state": "DISCOVERED",
    "statement": None,
    "module": None,
    "path": None,
    "imports": [],
    "gap_title": None,
    "context": None,
    "dead": None,
    "lease": None,
    "lease_obtained_at": None,
    "lease_expires_at": None,
    "base_sha": None,
    "lean_toolchain": config.LEAN_TOOLCHAIN,
    "researchers": [],
    "candidate_digest": None,
    "branch": None,
    "worktree": None,
    "commit_sha": None,
    "pr_number": None,
    "pr_url": None,
    "external_verdict": None,
    "failure_reason": None,
    "intent": None,
    "last_reconcile": None,
    "created_at": None,
    "updated_at": None,
}


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def gap_dir(gap_id):
    if not config.GAP_ID_RE.match(gap_id):
        raise ValueError("invalid gap id: %r" % gap_id)
    return os.path.join(config.GAPS_DIR, gap_id)


def state_path(gap_id):
    return os.path.join(gap_dir(gap_id), "state.json")


def events_path(gap_id):
    return os.path.join(gap_dir(gap_id), "events.jsonl")


@contextlib.contextmanager
def lock(gap_id):
    d = gap_dir(gap_id)
    os.makedirs(d, exist_ok=True)
    fd = os.open(os.path.join(d, ".lock"), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def atomic_write(path, data):
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def load(gap_id):
    p = state_path(gap_id)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save(rec):
    rec["updated_at"] = _now()
    atomic_write(state_path(rec["gap_id"]),
                 json.dumps(rec, indent=2, sort_keys=True) + "\n")


def event(gap_id, kind, detail=None):
    rec = {"at": _now(), "kind": kind, "detail": detail or {}}
    with open(events_path(gap_id), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())


def create(gap_id, **fields):
    if load(gap_id) is not None:
        raise ValueError("gap already exists: " + gap_id)
    rec = dict(EMPTY)
    rec.update(fields)
    rec["gap_id"] = gap_id
    rec["created_at"] = _now()
    rec["updated_at"] = rec["created_at"]
    with lock(gap_id):
        save(rec)
        event(gap_id, "created", {"state": rec["state"]})
    return rec


def transition(gap_id, new_state, **fields):
    with lock(gap_id):
        rec = load(gap_id)
        if rec is None:
            raise KeyError(gap_id)
        if new_state not in config.ALLOWED.get(rec["state"], set()):
            raise ValueError("illegal transition %s -> %s" %
                             (rec["state"], new_state))
        rec.update(fields)
        rec["state"] = new_state
        save(rec)
        event(gap_id, "state", {"to": new_state, "fields": fields})
    return rec


def reacquire(gap_id, **fields):
    """Adopt a freshly granted desk lease for a gap with local history.

    The desk may re-offer a gap that was previously released or went stale
    once its cooldown expires.  Releasing that fresh lease back with reason
    'other' (the old cli.py behaviour) re-arms the desk's one-hour cooldown
    and feeds its ten-minute step rate limit; with several workers this
    locked the whole handle out of the desk.  Reuse the new lease instead.
    The append-only event log preserves every earlier attempt.
    """
    with lock(gap_id):
        rec = load(gap_id)
        if rec is None:
            raise KeyError(gap_id)
        if rec["state"] not in ("RELEASED", "STALE"):
            raise ValueError("refusing to reacquire gap in state %s" %
                             rec["state"])
        previous = rec["state"]
        lease_fields = ("lease", "lease_obtained_at", "lease_expires_at")
        meta_fields = ("statement", "module", "path", "imports", "gap_title",
                       "context", "dead")
        for key in lease_fields + meta_fields:
            if key in fields:
                rec[key] = fields[key]
        # A re-leased gap starts a fresh publication cycle.  Stale digest or
        # publish artifacts from an earlier attempt would make publish()
        # abort ("candidate digest changed since local check") or reuse an
        # old base/branch/PR, driving the gap to FAULT instead of credited.
        for key in ("candidate_digest", "base_sha", "branch", "worktree",
                    "commit_sha", "pr_number", "pr_url", "external_verdict"):
            rec[key] = None
        rec["failure_reason"] = None
        rec["intent"] = None
        rec["researchers"] = []
        rec["state"] = "LEASED"
        save(rec)
        event(gap_id, "reacquired", {"previous_state": previous,
                                     "lease": rec["lease"]})
    return rec


def update(gap_id, **fields):
    with lock(gap_id):
        rec = load(gap_id)
        if rec is None:
            raise KeyError(gap_id)
        rec.update(fields)
        save(rec)
        event(gap_id, "update", {"fields": fields})
    return rec


def intent(gap_id, what, payload):
    """Write-ahead intent before an external effect."""
    return update(gap_id, intent={"what": what, "at": _now(),
                                  "payload": payload})


def clear_intent(gap_id):
    return update(gap_id, intent=None)


def all_gaps():
    try:
        return sorted(d for d in os.listdir(config.GAPS_DIR)
                      if config.GAP_ID_RE.match(d))
    except FileNotFoundError:
        return []

"""Independent exact-candidate check, concurrent with signed PR publication.

No result from this worker is required to open a PR. Infrastructure failures
fall back to the ordinary postcheck; only matching compiler outcomes update
the current revision. No worktree or publisher lock is shared.
"""
import fcntl
import json
import os
from pathlib import Path
import sys
import time

from . import config, state, support
from .remote import protocol

LIVE = ("SIGNED", "PUSHED", "PR_OPEN")


def key(rec):
    return protocol.digest(protocol.canonical([
        rec["gap_id"], rec["lease"], rec["base_sha"], rec["candidate_digest"],
        rec["commit_sha"]]))


def root(rec):
    return Path(state.gap_dir(rec["gap_id"]), "earlycheck", key(rec))


def lock(rec):
    d = root(rec)
    d.mkdir(parents=True, exist_ok=True)
    fd = os.open(d/"lock", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        return None
    return fd


def pending(rec):
    if not rec or rec.get("state") not in LIVE or rec.get("local_check_status") != "pending":
        return False
    return all(rec.get(k) for k in ("base_sha", "candidate_digest", "commit_sha", "lease"))


def inflight(rec):
    if not pending(rec):
        return False
    fd = lock(rec)
    if fd is None:
        return True
    os.close(fd)
    return False


def start(rec, data):
    # Publication's legacy parallel checker was a relay transport. Never start
    # a subprocess here; ordinary postcheck uses the managed local compiler.
    return False


def apply(gap, expected_key, job, result):
    r = protocol.result(protocol.canonical(result), job)
    if r["status"] not in ("elaborated", "rejected"):
        return False
    with state.lock(gap):
        rec = state.load(gap)
        if not pending(rec) or key(rec) != expected_key:
            return False
        if (rec["base_sha"] != job["base"] or rec["candidate_digest"] != job["source_sha256"]
                or support.attempt(rec) != job["attempt"]):
            return False
        fields = {"local_check_status":"passed" if r["status"]=="elaborated" else "failed",
                  "local_check_log":r["diagnostic"][-2000:], "local_check_retry_at":None,
                  "publisher_memory_required":None}
        rec.update(fields)
        state.save(rec)
        state.event(gap, "parallel_check", {"sha":rec["commit_sha"], "job":job["job"],
                                            "elapsed_ms":r["elapsed_ms"], **fields})
        return True


def run(gap, expected_key, fd):
    d = Path(state.gap_dir(gap), "earlycheck", expected_key)
    outcome = {"at":time.time(), "status":"disabled",
               "reason":"out-of-host early check transport disabled; use managed local postcheck"}
    try:
        pass
    except (OSError, ValueError, KeyError) as e:
        outcome["reason"] = str(e)[-500:]
    finally:
        try:
            state.atomic_write(str(d/"attempted.json"), json.dumps(outcome))
        finally:
            os.close(fd)


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2], int(sys.argv[3]))

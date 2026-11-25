"""Independent exact-candidate check, concurrent with signed PR publication.

No result from this worker is required to open a PR. Infrastructure failures
fall back to the ordinary postcheck; only matching compiler outcomes update
the current revision. No worktree or publisher lock is shared.
"""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from . import config, state, support
from .remote import protocol

RELAY = str(Path.home()/".local/bin/marceline-request")
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
    if not pending(rec) or not Path(RELAY).is_file():
        return False
    fd = lock(rec)
    if fd is None:
        return True
    try:
        d = root(rec)
        if (d/"attempted.json").exists():
            return False
        meta = {"id":rec["gap_id"], "file":rec["path"], "module":rec["module"],
                "statement":rec["statement"], "imports":rec["imports"]}
        job = protocol.make(meta, data, rec["base_sha"], config.LEAN_TOOLCHAIN,
                            support.attempt(rec), wall=600, rss_mib=8192)
        if job["source_sha256"] != rec["candidate_digest"]:
            return False
        state.atomic_write(str(d/"job.json"), protocol.canonical(job).decode())
        with (d/"worker.log").open("ab") as log:
            subprocess.Popen([sys.executable, "-m", "missions.pnp.earlycheck",
                              rec["gap_id"], key(rec), str(fd)],
                             cwd=str(Path(__file__).resolve().parents[2]),
                             stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                             pass_fds=(fd,), start_new_session=True)
        return True
    finally:
        os.close(fd)


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
    outcome = {"at":time.time(), "status":"deferred"}
    try:
        rec = state.load(gap)
        if not pending(rec) or key(rec) != expected_key:
            return
        job, _ = protocol.request((d/"job.json").read_bytes())
        avail = json.loads(subprocess.check_output([RELAY,"status",job["base"]], timeout=15))
        if not avail.get("base_available"):
            outcome["reason"] = "exact base unavailable"
            return
        from .research.async_check import recover_request, ID
        rid = recover_request(job["job"])
        if not rid:
            p = subprocess.run([RELAY,"submit","lean-check",str(d/"job.json")],
                               capture_output=True, text=True, timeout=30)
            rid = p.stdout.strip()
            if not ID.fullmatch(rid):
                rid = recover_request(job["job"])
        if not rid:
            outcome["reason"] = "no remote request"
            return
        outcome["request"] = rid
        p = subprocess.run([RELAY,"wait",rid,"900"], capture_output=True,
                           text=True, timeout=930)
        if p.returncode:
            outcome["reason"] = "remote check unavailable"
            return
        result = json.loads(p.stdout)["result"]
        outcome["result"] = protocol.result(protocol.canonical(result), job)
        outcome["status"] = "applied" if apply(gap, expected_key, job, result) else "deferred"
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as e:
        outcome["reason"] = str(e)[-500:]
    finally:
        try:
            state.atomic_write(str(d/"attempted.json"), json.dumps(outcome))
        finally:
            os.close(fd)


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2], int(sys.argv[3]))

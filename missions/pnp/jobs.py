"""Durable one-command publication, independent of agent/tool timeouts."""
import fcntl
import os
import subprocess
import sys
import time

from . import config, publish, state, validate

READY = ("CANDIDATE_READY", "LOCAL_CHECKED", "SIGNED", "PUSHED", "REJECTED")


def candidate_path(gap):
    return os.path.join(state.gap_dir(gap), "candidate.lean")


def claim(gap):
    fd = os.open(os.path.join(state.gap_dir(gap), ".publisher.lock"),
                 os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        return None
    return fd


def launch(gap, fd):
    """The child inherits the lock; death releases it, including SIGKILL."""
    log = os.path.join(state.gap_dir(gap), "publisher.log")
    with open(log, "ab") as out:
        subprocess.Popen([sys.executable, "-m", "missions.pnp.jobs", gap,
                          str(fd)], cwd=os.path.dirname(os.path.dirname(
                              os.path.dirname(os.path.abspath(__file__)))),
                         stdin=subprocess.DEVNULL, stdout=out, stderr=out,
                         pass_fds=(fd,), start_new_session=True)


def submit(gap, source, expected_lease=None):
    rec = state.load(gap)
    if expected_lease and (not rec or rec.get("lease") != expected_lease):
        raise publish.StopPublish("assignment superseded")
    if not rec:
        raise publish.StopPublish("no acquired gap")
    fd = claim(gap)
    if fd is None:
        return {"gap": gap, "status": "publishing"}
    try:
        with open(source, "rb") as f:
            data = f.read(config.MAX_FILE_BYTES + 1)
        with state.lock(gap):
            rec = state.load(gap)
            if not rec or (expected_lease and rec.get("lease") != expected_lease):
                raise publish.StopPublish("assignment superseded")
            if rec["state"] not in ("LEASED", "RESEARCHING", "PR_OPEN") + READY:
                raise publish.StopPublish("gap not publishable: " + rec["state"])
            meta = {"id": gap, "file": rec["path"], "module": rec["module"],
                    "statement": rec["statement"], "imports": rec["imports"]}
            digest = validate.validate(meta, data)
            if rec["state"] in ("SIGNED", "PUSHED") and digest != rec["candidate_digest"]:
                raise publish.StopPublish("signed proof is immutable")
            before = rec["state"]
            if rec["state"] == "PR_OPEN":
                if (digest == rec.get("candidate_digest") or rec.get("local_check_status") != "failed"
                        or rec.get("external_verdict") == "ACCEPTED"):
                    return {"gap": gap, "pr": rec["pr_number"], "url": rec["pr_url"]}
                rec["state"] = "REJECTED"
            if (rec["state"] == "REJECTED" and digest == rec.get("candidate_digest")
                    and not rec.get("queued_lease")):
                raise publish.StopPublish("correction must change the proof")
            state.atomic_write(candidate_path(gap), data.decode("utf-8"))
            if before in ("LEASED", "RESEARCHING", "CANDIDATE_READY"):
                rec.update(state="CANDIDATE_READY", candidate_digest=digest,
                           failure_reason=None)
            rec.update(queued_lease=rec["lease"], publisher_retry_at=None,
                       publisher_failures=0, publisher_memory_required=None)
            state.save(rec)
            if before != rec["state"]:
                state.event(gap, "state", {"to": rec["state"], "fields": {"candidate_digest": digest}})
            state.event(gap, "update", {"fields": {"queued_lease": rec["lease"]}})
        launch(gap, fd)
        return {"gap": gap, "status": "publishing", "digest": digest}
    finally:
        # Do not unlock explicitly: the child owns this open description.
        os.close(fd)


def resume(gap):
    rec = state.load(gap)
    if (not rec or rec["state"] not in READY or
            not rec.get("queued_lease") or rec["queued_lease"] != rec["lease"] or
            not os.path.isfile(candidate_path(gap))):
        return False
    if (rec.get("publisher_retry_at") or 0) > time.time():
        return True
    fd = claim(gap)
    if fd is None:
        return True
    try:
        launch(gap, fd)
        return True
    finally:
        os.close(fd)


def defer(gap, lease):
    """Bound retries without turning transient outages into failed proofs."""
    rec = state.load(gap)
    if (not rec or rec.get("lease") != lease or rec["state"] not in READY
            or rec.get("queued_lease") != lease):
        return
    attempts = min(8, (rec.get("publisher_failures") or 0) + 1)
    delay = min(900, 30 * 2 ** (attempts - 1))
    state.update(gap, publisher_failures=attempts,
                 publisher_retry_at=time.time() + delay)


def run(gap, fd):
    lease = None
    try:
        os.environ["PNP_PUBLISH_LOCK_FD"] = str(fd)
        rec = state.load(gap)
        if rec["state"] == "PR_OPEN":
            from . import postcheck
            postcheck.run(gap)
            return
        if rec["state"] not in READY or rec.get("queued_lease") != rec["lease"]:
            return
        os.environ["PNP_PUBLISH_GAP"] = gap
        lease = rec.get("lease")
        os.environ["PNP_PUBLISH_LEASE"] = lease or ""
        result = publish.publish(gap, candidate_path(gap))
        print(result, flush=True)
        from . import postcheck
        postcheck.run(gap)
    except publish.StopPublish as exc:
        print("publication stopped:", exc, flush=True)
        if lease:
            defer(gap, lease)
    except Exception as exc:
        # Preserve the pending candidate for the ordinary recovery cycle.
        print("publication interrupted:", exc, flush=True)
        if lease:
            defer(gap, lease)
    finally:
        os.close(fd)


if __name__ == "__main__":
    run(sys.argv[1], int(sys.argv[2]))

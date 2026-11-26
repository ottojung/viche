"""Independent local verification of a published, immutable candidate revision."""
import hashlib
import os
from pathlib import Path
import time

from . import build_control, earlycheck, gitctl, state


def pending(rec):
    return (rec and rec.get("state") == "PR_OPEN" and
            rec.get("local_check_status") == "pending" and
            rec.get("commit_sha") and rec.get("worktree"))


def run(gap, git=gitctl):
    rec = state.load(gap)
    if not pending(rec) or earlycheck.inflight(rec):
        return
    sha = rec["commit_sha"]
    if not build_control.resource_ready(rec):
        return
    def update(**fields):
        with state.lock(gap):
            current = state.load(gap)
            if pending(current) and current["commit_sha"] == sha:
                current.update(fields)
                state.save(current)
                state.event(gap, "postcheck", {"sha": sha, **fields})
    os.environ.update(PNP_PUBLISH_GAP=gap, PNP_PUBLISH_LEASE=rec["lease"],
                      PNP_POSTCHECK_SHA=sha)
    try:
        wt = rec["worktree"]
        def exact():
            return (git.run(["git", "-C", wt, "rev-parse", "HEAD"]).stdout.strip() == sha
                    and not git.run(["git", "-C", wt, "status", "--porcelain",
                                     "--untracked-files=all", "--", "lean"]).stdout.strip()
                    and hashlib.sha256(Path(wt, rec["path"]).read_bytes()).hexdigest()
                    == rec["candidate_digest"])
        if not exact():
            raise gitctl.GitError("published checkout differs from exact proof")
        ok, log = git.build(wt, rec["module"], rec["statement"])
        if not exact():
            raise gitctl.GitError("published checkout changed during check")
        update(local_check_status="passed" if ok else "failed",
               local_check_log=log[-2000:], local_check_retry_at=None,
               publisher_memory_required=None)
    except Exception as exc:
        fields = {"local_check_retry_at": time.time() + 60,
                  "local_check_log": str(exc)[-2000:]}
        if isinstance(exc, build_control.MemoryDeferred):
            fields["publisher_memory_required"] = exc.required
        update(**fields)
    finally:
        os.environ.pop("PNP_POSTCHECK_SHA", None)


def resume(gap, rec):
    from . import jobs
    if (not pending(rec) or earlycheck.inflight(rec) or (rec.get("local_check_retry_at") or 0) > time.time()
            or not build_control.resource_ready(rec)):
        return
    fd = jobs.claim(gap)
    if fd is not None:
        try:
            jobs.launch(gap, fd)
        finally:
            os.close(fd)

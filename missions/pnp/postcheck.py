"""Independent local verification of a published, immutable candidate revision."""
import fcntl
import hashlib
import os
from pathlib import Path
import shutil
import tempfile
import time

from . import build_control, config, earlycheck, gitctl, state

POSTCHECK_PREFIX = "pnp-postcheck-"
# A heavy publication build can legitimately run for a while under load. Only
# reclaim a checkout that no live process holds and that is well past that.
STALE_AFTER = 20 * 60
SHARED_BUILDS = "postcheck-build"


def pending(rec):
    # The fast signed-commit path publishes with worktree=None, but the exact
    # signed bytes are still in the mirror. Requiring a worktree left those
    # PRs permanently 'pending' with no local verification.
    return bool(rec and rec.get("state") == "PR_OPEN" and
                rec.get("local_check_status") == "pending" and
                rec.get("commit_sha") and
                (rec.get("worktree") or (rec.get("base_sha") and rec.get("candidate_digest"))))


def _fast_worktree(sha):
    """Detached, disposable checkout of the exact signed commit in the mirror."""
    gd = "--git-dir=" + gitctl.MIRROR
    if gitctl.run(["git", gd, "cat-file", "-e", sha + "^{commit}"], check=False).returncode:
        raise gitctl.GitError("signed commit absent from mirror")
    parent = Path(config.WORKTREES_DIR)
    parent.mkdir(parents=True, exist_ok=True)
    path = tempfile.mkdtemp(prefix="pnp-postcheck-", dir=str(parent))
    os.rmdir(path)
    try:
        gitctl.run(["git", gd, "worktree", "add", "--quiet", "--detach", path, sha], check=True)
        gitctl.run(["git", "-C", path, "config", "core.hooksPath", "/dev/null"])
    except BaseException:
        shutil.rmtree(path, ignore_errors=True)
        raise
    return path


def _drop_fast_worktree(path):
    """Dispose of a disposable postcheck checkout, even if `add` was interrupted.

    A killed `git worktree add` can leave a locked admin record whose worktree
    has no `.git` file; path-based `worktree remove` then fails validation and
    a raised git exception used to abort the rmtree entirely. Each step is
    isolated so no git failure can prevent reclaiming the multi-gigabyte build.
    """
    path = os.fspath(path)
    gd = "--git-dir=" + gitctl.MIRROR

    def quiet(argv):
        try:
            gitctl.run(argv, check=False)
        except Exception:
            pass

    quiet(["git", gd, "worktree", "unlock", path])
    quiet(["git", gd, "worktree", "remove", "--force", path])
    shutil.rmtree(path, ignore_errors=True)
    # The admin record is keyed by the worktree's unique basename. Clear its
    # lock and the record itself when git could not validate a missing .git.
    admin = os.path.join(gitctl.MIRROR, "worktrees", os.path.basename(path))
    try:
        locked = os.path.join(admin, "locked")
        if os.path.isfile(locked):
            os.unlink(locked)
    except OSError:
        pass
    if os.path.isdir(admin):
        shutil.rmtree(admin, ignore_errors=True)


def _held(path):
    """True when an agent or process still uses this path; fail closed."""
    p = os.fspath(path)
    try:
        from .staffing import backend
        agents = backend.running()
    except Exception:
        return True
    for agent in agents:
        for key in ("cwd", "invocation_cwd"):
            value = agent.get(key)
            if isinstance(value, str) and (value == p or value.startswith(p + os.sep)):
                return True
    try:
        entries = list(Path("/proc").iterdir())
    except OSError:
        return True
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            if entry.stat().st_uid != os.getuid():
                continue
        except OSError:
            continue
        links = [entry / "cwd"]
        try:
            links.extend(entry.joinpath("fd").iterdir())
        except OSError:
            pass
        for link in links:
            try:
                target = os.readlink(link).removesuffix(" (deleted)")
            except OSError:
                continue
            if target == p or target.startswith(p + os.sep):
                return True
    return False


def sweep():
    """Reclaim postcheck checkouts abandoned by an interrupted publisher."""
    try:
        candidates = list(Path(config.WORKTREES_DIR).glob(POSTCHECK_PREFIX + "*"))
    except OSError:
        return 0
    now = time.time()
    reaped = 0
    for path in candidates:
        try:
            if now - path.stat().st_mtime < STALE_AFTER or _held(path):
                continue
        except OSError:
            continue
        _drop_fast_worktree(path)
        reaped += 1
    _trim_shared_builds()
    if reaped:
        print("postcheck sweep reaped %d abandoned worktrees" % reaped, flush=True)
    return reaped


def _shared_build(worktree, sha):
    """Share one Lean artifact dir per exact signed commit; return a lock fd.

    Same-commit checks serialize so Lake never writes one build dir at once.
    Distinct commits never share artifacts. The caller closes the fd after the
    build, whether it succeeded or failed.
    """
    if not sha or len(sha) != 40:
        return None
    try:
        cache = Path(config.CACHE_DIR, SHARED_BUILDS)
        cache.mkdir(parents=True, exist_ok=True)
        target = cache / sha
        target.mkdir(exist_ok=True)
        fd = os.open(cache / (sha + ".lock"), os.O_CREAT | os.O_RDWR, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX)
        local = Path(worktree, "lean", ".lake")
        local.mkdir(parents=True, exist_ok=True)
        build = local / "build"
        if not build.exists() and not build.is_symlink():
            os.symlink(target, build, target_is_directory=True)
        return fd
    except (OSError, ValueError):
        return None


def _trim_shared_builds(keep=2):
    """Bound the shared build cache, which lives on the mission's own disk."""
    cache = Path(config.CACHE_DIR, SHARED_BUILDS)
    try:
        dirs = sorted((d for d in cache.iterdir() if d.is_dir()),
                      key=lambda d: d.stat().st_mtime, reverse=True)
    except OSError:
        return
    for d in dirs[keep:]:
        try:
            fd = os.open(cache / (d.name + ".lock"), os.O_CREAT | os.O_RDWR, 0o600)
        except OSError:
            continue
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(fd)
            continue
        try:
            shutil.rmtree(d, ignore_errors=True)
        finally:
            os.close(fd)


def run(gap, git=gitctl):
    rec = state.load(gap)
    if not pending(rec) or earlycheck.inflight(rec):
        return
    sweep()
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
        fast = rec.get("worktree") is None
        wt = _fast_worktree(sha) if fast else rec["worktree"]
        try:
            def exact():
                return (git.run(["git", "-C", wt, "rev-parse", "HEAD"]).stdout.strip() == sha
                        and not git.run(["git", "-C", wt, "status", "--porcelain",
                                         "--untracked-files=all", "--", "lean"]).stdout.strip()
                        and hashlib.sha256(Path(wt, rec["path"]).read_bytes()).hexdigest()
                        == rec["candidate_digest"])
            if not exact():
                raise gitctl.GitError("published checkout differs from exact proof")
            build_lock = _shared_build(wt, sha) if fast else None
            try:
                ok, log = git.build(wt, rec["module"], rec["statement"])
            finally:
                if build_lock is not None:
                    os.close(build_lock)
            if not exact():
                raise gitctl.GitError("published checkout changed during check")
            update(local_check_status="passed" if ok else "failed",
                   local_check_log=log[-2000:], local_check_retry_at=None,
                   publisher_memory_required=None)
        finally:
            # The fast path owns its disposable checkout; never publish or
            # reuse it and never mutate the gap's worktree field.
            if fast:
                _drop_fast_worktree(wt)
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

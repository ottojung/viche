"""Fresh-checkout, signed-commit and restricted-push plumbing.

The publisher is the only caller.  Repository, remote, branch, author,
committer and signing key are fixed in config.py; no candidate or worker
prompt can supply them.
"""
import os
import fcntl
import time
import shutil
import subprocess
import tempfile

from . import config, github, build_control, compile as compiler

MIRROR = os.path.join(config.CACHE_DIR, "fork.git")


class GitError(Exception):
    pass


GOOD_SIGNATURES = {"G", "U"}   # U = good signature, key not locally trusted


def check_commit_fields(fmt):
    """Verify %G?, %GF, author and committer.  Testable without a real key."""
    if len(fmt) != 6 or fmt[0] not in GOOD_SIGNATURES:
        raise GitError("commit is not good-signed: %r" % fmt[:2])
    if fmt[1].upper() != config.SIGNING_KEY.rstrip("!").upper():
        raise GitError("wrong signing subkey: " + fmt[1])
    if fmt[2:4] != [config.AUTHOR_NAME, config.AUTHOR_EMAIL]:
        raise GitError("wrong author: %r" % fmt[2:4])
    if fmt[4:6] != [config.AUTHOR_NAME, config.AUTHOR_EMAIL]:
        raise GitError("wrong committer: %r" % fmt[4:6])


def run(argv, cwd=None, check=True):
    if cwd is None:
        # A publisher or reconciler may inherit the cwd of a worktree that was
        # removed after publication. Git resolves its repository from the
        # process cwd, so even remote-only commands such as `git ls-remote`
        # then fail with "Unable to read current working directory". Run every
        # git subprocess from a durable directory unless a caller pins one.
        cwd = config.CACHE_DIR
        os.makedirs(cwd, exist_ok=True)
    p = subprocess.run(argv, cwd=cwd, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, text=True, timeout=90)
    if check and p.returncode != 0:
        raise GitError("%s failed (%d): %s" %
                       (" ".join(argv[:4]), p.returncode,
                        p.stderr.strip()[:600]))
    return p


def upstream_url():
    return "https://github.com/" + github.repository_name(config.UPSTREAM_ID) + ".git"


def fork_url():
    return "git@github.com:" + github.repository_name(config.FORK_ID) + ".git"


def ensure_mirror():
    """Serialize writers to the shared upstream ref across all town processes.

    Concurrent callers can share a fetch completed within the last three
    seconds, but always resolve the actual pinned ref while holding the lock.
    A failed refresh never publishes a freshness marker.
    """
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    marker = os.path.join(config.CACHE_DIR, "mirror-fetch.stamp")
    with open(os.path.join(config.CACHE_DIR, "mirror-fetch.lock"), "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if not os.path.exists(os.path.join(MIRROR, "HEAD")):
            run(["git", "clone", "--bare", "--quiet", fork_url(), MIRROR])
        try:
            age = time.time() - os.stat(marker).st_mtime
            with open(marker, encoding="ascii") as f:
                previous = f.read().strip()
            current = run(["git", "--git-dir=" + MIRROR, "rev-parse",
                           "refs/remotes/upstream/main"]).stdout.strip()
            if 0 <= age <= 3 and previous == current and len(current) == 40:
                return current
        except (OSError, GitError):
            pass
        run(["git", "--git-dir=" + MIRROR, "fetch", "--quiet", upstream_url(),
             "+refs/heads/main:refs/remotes/upstream/main"])
        current = run(["git", "--git-dir=" + MIRROR, "rev-parse",
                       "refs/remotes/upstream/main"]).stdout.strip()
        with open(marker, "w", encoding="ascii") as f:
            f.write(current)
        return current


def upstream_has_path(base_sha, path):
    """A public pinned base already containing the path cannot accept an add."""
    import re
    if not re.fullmatch(r"[0-9a-f]{40}", base_sha or ""):
        raise GitError("base is not a full SHA")
    if not path.startswith("lean/") or ".." in path.split("/"):
        raise GitError("candidate path is outside lean/")
    return run(["git", "--git-dir=" + MIRROR, "cat-file", "-e",
                base_sha + ":" + path], check=False).returncode == 0


def remote_branch_sha(branch):
    p = run(["git", "ls-remote", "--heads", fork_url(),
             "refs/heads/" + branch], check=False)
    if p.returncode != 0:
        raise GitError("cannot check fork branch: " + p.stderr[:300])
    for line in p.stdout.splitlines():
        sha, ref = line.split("\t", 1)
        if ref == "refs/heads/" + branch:
            return sha
    return None


def fresh_worktree(gap_id, base_sha, branch):
    """Create an isolated checkout at the pinned SHA; never reuse untrusted
    candidate Git state, hooks or configs."""
    if not config.BRANCH_RE.match(branch):
        raise GitError("unsafe branch name")
    path = os.path.join(config.WORKTREES_DIR, gap_id)
    os.makedirs(config.WORKTREES_DIR, exist_ok=True)
    if os.path.exists(os.path.join(path, ".git")):
        run(["git", "--git-dir=" + MIRROR, "worktree", "remove", "--force",
             path], check=False)
        shutil.rmtree(path, ignore_errors=True)
    branches = run(["git", "--git-dir=" + MIRROR, "branch", "--list",
                    branch]).stdout.strip()
    if branches == branch:
        run(["git", "--git-dir=" + MIRROR, "worktree", "add", "--quiet",
             path, branch])
    else:
        run(["git", "--git-dir=" + MIRROR, "worktree", "add", "--quiet",
             "-b", branch, path, base_sha])
    run(["git", "-C", path, "config", "core.hooksPath", "/dev/null"])
    return path


def pin_candidate(worktree, path, candidate_bytes, correction=False):
    """Stage only the independently approved exact path as a new file."""
    target = os.path.join(worktree, path)
    if not target.startswith(os.path.join(worktree, "lean" + os.sep)):
        raise GitError("candidate path is outside lean/")
    if os.path.exists(target) and not correction:
        raise GitError("candidate path already exists at base")
    if correction and not os.path.isfile(target):
        raise GitError("correction requires the existing proof file")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "wb") as f:              # candidate is data, not code
        f.write(candidate_bytes)
    run(["git", "-C", worktree, "add", "--", path])
    staged = run(["git", "-C", worktree, "diff", "--cached",
                  "--name-status"]).stdout.splitlines()
    expected_status = "M" if correction else "A"
    if staged != [expected_status + "\t" + path]:
        raise GitError("staged change is not exactly one proof file: %r" %
                       staged)
    other = run(["git", "-C", worktree, "status", "--porcelain"]).stdout
    other = [l for l in other.splitlines() if l[3:] != path]
    if other:
        raise GitError("unexpected additional worktree changes: %r" % other)


def prepare_build_cache(worktree):
    """Share pinned dependency packages, never another proof's mutable .lake."""
    seed = os.environ.get("PNP_SHARED_LAKE",
                          "/home/lubko/pequalnp-research-20261123/lean/.lake")
    lean = os.path.join(worktree, "lean")
    for name in ("lean-toolchain", "lake-manifest.json"):
        with open(os.path.join(lean, name), "rb") as a, \
             open(os.path.join(os.path.dirname(seed), name), "rb") as b:
            if a.read() != b.read():
                raise GitError("pinned dependency cache differs: " + name)
    local = os.path.join(lean, ".lake")
    if os.path.islink(local):
        raise GitError("publication checkout must not share mutable build state")
    os.makedirs(local, exist_ok=True)
    packages = os.path.join(seed, "packages")
    if not os.path.isdir(packages):
        raise GitError("pinned Mathlib package cache unavailable")
    dest = os.path.join(local, "packages")
    if not os.path.lexists(dest):
        os.symlink(packages, dest)
    elif not os.path.isdir(dest):
        raise GitError("invalid local package cache")


def build(worktree, module, statement, runner=None):
    """One required local build; authoritative verdict comes from the PR.

    No local checker directory lock or second verifier build. The upstream
    checker independently judges the exact statement and allowed axioms.
    """
    if runner is not None:
        return runner(worktree, module, statement)
    if not isinstance(statement, str) or not statement.strip():
        return False, "missing authoritative gap statement"
    prepare_build_cache(worktree)
    lock_fd = os.environ.get("PNP_PUBLISH_LOCK_FD")
    inherited = (int(lock_fd),) if lock_fd else ()
    with tempfile.TemporaryFile() as output:
        code = compiler.run(["lake", "build", "+" + module],
                            cwd=os.path.join(worktree, "lean"),
                            heavy=True, publication=True,
                            output=output, inherited=inherited)
        output.seek(max(0, output.tell() - 8000))
        log = output.read().decode("utf-8", "replace")
    if code and ("error: PEqualNP/" not in log and "error: ./PEqualNP/" not in log):
        raise GitError("local build interrupted: " + log[-600:])
    return code == 0, log[-2000:]


def reusable_checked_tree(worktree, base_sha, path, data):
    """Reuse only the publisher's exact successful pinned build, never worker output."""
    if not worktree or not base_sha:
        return False
    try:
        if run(["git", "-C", worktree, "rev-parse", "HEAD"]).stdout.strip() != base_sha:
            return False
        if run(["git", "-C", worktree, "status", "--porcelain"]).stdout.splitlines() != ["A  " + path]:
            return False
        # Staged and working copies must both match the validated bytes.
        with open(os.path.join(worktree, path), "rb") as f:
            if f.read() != data:
                return False
        if run(["git", "-C", worktree, "diff", "--quiet"], check=False).returncode != 0:
            return False
        return True
    except (OSError, GitError, subprocess.SubprocessError):
        return False


def signed_commit(worktree, base_sha, message, signer=None, correction=False):
    """Create and cryptographically verify exactly one signed commit."""
    if signer is not None:
        return signer(worktree, base_sha, message)
    run(["git", "-C", worktree, "config", "user.name", config.AUTHOR_NAME])
    run(["git", "-C", worktree, "config", "user.email", config.AUTHOR_EMAIL])
    run(["git", "-C", worktree, "config", "user.signingkey",
         config.SIGNING_KEY])
    run(["git", "-C", worktree, "config", "commit.gpgsign", "true"])
    run(["git", "-C", worktree, "commit", "-m", message])
    sha = run(["git", "-C", worktree, "rev-parse", "HEAD"]).stdout.strip()
    count = run(["git", "-C", worktree, "rev-list", "--count",
                 base_sha + "..HEAD"]).stdout.strip()
    if not correction and count != "1":
        raise GitError("expected exactly one new commit, got " + count)
    if correction and int(count) < 2:
        raise GitError("correction did not extend original commit history")
    fmt = run(["git", "-C", worktree, "log", "-1", "--format=" +
               "%G?%n%GF%n%an%n%ae%n%cn%n%ce"]).stdout.splitlines()
    check_commit_fields(fmt)
    v = run(["git", "-C", worktree, "verify-commit", sha], check=False)
    if v.returncode != 0:
        raise GitError("git verify-commit failed")
    return sha


def fast_signed_commit(base_sha, branch, path, candidate_bytes, message):
    """The same single signed commit as fresh_worktree + pin_candidate + signed_commit, built with
    plumbing in the bare mirror (temporary index, no checkout of the whole repository): about 1 s
    instead of 15-20 s on billy-dev.  Only for a new proof file on a pinned base; corrections keep
    the worktree path.  The local branch ref is (re)pointed at the new commit; the remote branch
    is checked by the publisher before any push, exactly as before."""
    import re
    if not config.BRANCH_RE.match(branch):
        raise GitError("unsafe branch name")
    if not re.fullmatch(r"[0-9a-f]{40}", base_sha or ""):
        raise GitError("base is not a full SHA")
    if not path.startswith("lean/") or ".." in path.split("/"):
        raise GitError("candidate path is outside lean/")
    gd = "--git-dir=" + MIRROR
    if run(["git", gd, "cat-file", "-e", base_sha + ":" + path], check=False).returncode == 0:
        raise GitError("candidate path already exists at base")
    p = subprocess.run(["git", gd, "hash-object", "-w", "--stdin"], input=candidate_bytes,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60, cwd=config.CACHE_DIR)
    if p.returncode != 0:
        raise GitError("hash-object failed: " + p.stderr.decode()[:300])
    blob = p.stdout.decode().strip()
    fd, index = tempfile.mkstemp(prefix="pnp-index-", dir=config.CACHE_DIR)
    os.close(fd)
    os.unlink(index)
    env = dict(os.environ, GIT_INDEX_FILE=index,
               GIT_AUTHOR_NAME=config.AUTHOR_NAME, GIT_AUTHOR_EMAIL=config.AUTHOR_EMAIL,
               GIT_COMMITTER_NAME=config.AUTHOR_NAME, GIT_COMMITTER_EMAIL=config.AUTHOR_EMAIL)

    def g(*argv, **kw):
        q = subprocess.run(["git", gd] + list(argv), env=env, cwd=config.CACHE_DIR, text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90, **kw)
        if q.returncode != 0:
            raise GitError("git %s failed: %s" % (argv[0], q.stderr.strip()[:400]))
        return q.stdout.strip()
    try:
        g("read-tree", base_sha)
        g("update-index", "--add", "--cacheinfo", "100644,%s,%s" % (blob, path))
        tree = g("write-tree")
        sha = g("-c", "user.signingkey=" + config.SIGNING_KEY, "commit-tree", tree, "-p", base_sha,
                "-S" + config.SIGNING_KEY, "-m", message)
    finally:
        try:
            os.unlink(index)
        except OSError:
            pass
    changed = run(["git", gd, "diff-tree", "--no-commit-id", "--name-status", "-r", base_sha, sha]).stdout.splitlines()
    if changed != ["A\t" + path]:
        raise GitError("commit is not exactly one added proof file: %r" % changed)
    fmt = run(["git", gd, "log", "-1", "--format=%G?%n%GF%n%an%n%ae%n%cn%n%ce", sha]).stdout.splitlines()
    check_commit_fields(fmt)
    if run(["git", gd, "verify-commit", sha], check=False).returncode != 0:
        raise GitError("git verify-commit failed")
    run(["git", gd, "update-ref", "refs/heads/" + branch, sha])
    return sha


def sync_fork_base(latest=None):
    """Keep the fork's object store current with upstream main by advancing one fork branch
    (pnp/upstream-sync, never a PR head) to upstream main, off the critical path.  A proof
    branch then pushes three new objects instead of every upstream commit since our last push
    (the mirror's main was 9123 commits behind upstream on 2026-11-26)."""
    latest = latest or run(["git", "--git-dir=" + MIRROR, "rev-parse", "refs/remotes/upstream/main"]).stdout.strip()
    p = run(["git", "--git-dir=" + MIRROR, "push", "--quiet", fork_url(),
             latest + ":refs/heads/" + SYNC_BRANCH], check=False)
    if p.returncode != 0:
        raise GitError("fork sync push failed: " + p.stderr.strip()[:300])
    return latest


SYNC_BRANCH = "pnp/upstream-sync"


def push_branch(branch, pusher=None):
    """Non-force push of one branch to the fork only."""
    if pusher is not None:
        return pusher(branch)
    if not config.BRANCH_RE.match(branch):
        raise GitError("unsafe branch name")
    p = run(["git", "--git-dir=" + MIRROR, "push", fork_url(),
             "refs/heads/" + branch + ":refs/heads/" + branch], check=False)
    if p.returncode != 0:
        raise GitError("push failed: " + p.stderr.strip()[:400])
    return remote_branch_sha(branch)


def new_commits(worktree, base_sha):
    """All commits introduced above the pinned base, oldest first."""
    return list(reversed(run(["git", "-C", worktree, "rev-list",
                              base_sha + "..HEAD"]).stdout.split()))


def all_new_commits_signed(worktree, base_sha):
    """For corrections: every PR commit beyond base must be signed/attributed."""
    shas = new_commits(worktree, base_sha)
    for sha in shas:
        fmt = run(["git", "-C", worktree, "log", "-1", "--format=" +
                   "%G?%n%GF%n%an%n%ae%n%cn%n%ce", sha]).stdout.splitlines()
        try:
            check_commit_fields(fmt)
        except GitError:
            return False
    return bool(shas)


def prepare_unpublished(worktree, branch, base, previous=None):
    """Recover a crash before recording SIGNED, never rewrite a remote head."""
    remote = remote_branch_sha(branch)
    if remote != previous:
        raise GitError("unexpected remote branch before staging")
    target = previous or base
    run(["git", "-C", worktree, "reset", "--hard", target])
    run(["git", "-C", worktree, "clean", "-fd", "--", "lean"])


def is_upstream_ancestor(sha, latest):
    """Use a prior checked upstream base only if its ancestry is confirmed."""
    import re
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        return False
    return run(["git", "--git-dir=" + MIRROR, "merge-base", "--is-ancestor",
                sha, latest], check=False).returncode == 0

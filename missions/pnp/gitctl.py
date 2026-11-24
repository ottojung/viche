"""Fresh-checkout, signed-commit and restricted-push plumbing.

The publisher is the only caller.  Repository, remote, branch, author,
committer and signing key are fixed in config.py; no candidate or worker
prompt can supply them.
"""
import os
import signal
import shutil
import subprocess
import tempfile

from . import config

UPSTREAM_URL = "https://github.com/" + config.UPSTREAM + ".git"
FORK_URL = "git@github.com:" + config.FORK + ".git"
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
    p = subprocess.run(argv, cwd=cwd, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, text=True, timeout=90)
    if check and p.returncode != 0:
        raise GitError("%s failed (%d): %s" %
                       (" ".join(argv[:4]), p.returncode,
                        p.stderr.strip()[:600]))
    return p


def ensure_mirror():
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    if not os.path.exists(os.path.join(MIRROR, "HEAD")):
        run(["git", "clone", "--bare", "--quiet", FORK_URL, MIRROR])
    # Upstream objects are needed to build from a pinned public base SHA.
    run(["git", "--git-dir=" + MIRROR, "fetch", "--quiet", UPSTREAM_URL,
         "+refs/heads/main:refs/remotes/upstream/main"])
    return run(["git", "--git-dir=" + MIRROR, "rev-parse",
                "refs/remotes/upstream/main"]).stdout.strip()


def remote_branch_sha(branch):
    p = run(["git", "ls-remote", "--heads", FORK_URL,
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
    shim = os.path.join(worktree, "tools", "bin", "lake")
    env = {k: v for k, v in os.environ.items()
           if not (k.startswith("LEAN_") or k.startswith("LAKE_")
                   or k in ("PEQUALNP_IN_QUEUE", "PEQUALNP_REAL_LAKE"))}
    # Use the upstream build queue and content-addressed artifact cache.
    # Never inherit an untrusted worker's Lake search path/options.
    # Retain the publisher lock across an orphaned build subprocess, too.
    lock_fd = os.environ.get("PNP_PUBLISH_LOCK_FD")
    inherited = (int(lock_fd),) if lock_fd else ()
    with tempfile.TemporaryFile() as output:
        proc = subprocess.Popen([shim, "build", "+" + module],
                                cwd=os.path.join(worktree, "lean"),
                                env=env, stdout=output, stderr=output,
                                start_new_session=True, pass_fds=inherited)
        try:
            code = proc.wait(timeout=600)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
            raise GitError("local Lean build timed out; retry without stale lock")
        output.seek(max(0, output.tell() - 8000))
        log = output.read().decode("utf-8", "replace")
    if code and ("error: PEqualNP/" not in log and "error: ./PEqualNP/" not in log):
        raise GitError("local build interrupted: " + log[-600:])
    return code == 0, log[-2000:]


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


def push_branch(branch, pusher=None):
    """Non-force push of one branch to the fork only."""
    if pusher is not None:
        return pusher(branch)
    if not config.BRANCH_RE.match(branch):
        raise GitError("unsafe branch name")
    p = run(["git", "--git-dir=" + MIRROR, "push", FORK_URL,
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

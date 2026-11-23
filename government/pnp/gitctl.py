"""Fresh-checkout, signed-commit and restricted-push plumbing.

The publisher is the only caller.  Repository, remote, branch, author,
committer and signing key are fixed in config.py; no candidate or worker
prompt can supply them.
"""
import os
import shutil
import subprocess

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
                       stderr=subprocess.PIPE, text=True)
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


def pin_candidate(worktree, path, candidate_bytes):
    """Stage only the independently approved exact path as a new file."""
    target = os.path.join(worktree, path)
    if not target.startswith(os.path.join(worktree, "lean" + os.sep)):
        raise GitError("candidate path is outside lean/")
    if os.path.exists(target):
        raise GitError("candidate path already exists at base")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "wb") as f:              # candidate is data, not code
        f.write(candidate_bytes)
    run(["git", "-C", worktree, "add", "--", path])
    staged = run(["git", "-C", worktree, "diff", "--cached",
                  "--name-status"]).stdout.splitlines()
    if staged != ["A\t" + path]:
        raise GitError("staged change is not exactly one added file: %r" %
                       staged)
    other = run(["git", "-C", worktree, "status", "--porcelain"]).stdout
    other = [l for l in other.splitlines() if l[3:] != path]
    if other:
        raise GitError("unexpected additional worktree changes: %r" % other)


def build(worktree, module, runner=None):
    """Run the pinned Lean/Mathlib build.  Failure is never hidden."""
    if runner is not None:
        return runner(worktree, module)
    toolchain = config.LEAN_TOOLCHAIN
    p = run(["elan", "run", toolchain, "lake", "exe", "cache", "get"],
            cwd=os.path.join(worktree, "lean"), check=False)
    if p.returncode != 0:
        return False, "Mathlib cache get failed: " + p.stderr[:400]
    p = run(["elan", "run", toolchain, "lake", "build", module],
            cwd=os.path.join(worktree, "lean"), check=False)
    return p.returncode == 0, (p.stdout + p.stderr)[-1200:]


def signed_commit(worktree, base_sha, message, signer=None):
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
    if count != "1":
        raise GitError("expected exactly one new commit, got " + count)
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

"""Fresh-checkout, signed-commit and restricted-push plumbing.

The publisher is the only caller.  Repository, remote, branch, author,
committer and signing key are fixed in config.py; no candidate or worker
prompt can supply them.
"""
import os
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
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    if not os.path.exists(os.path.join(MIRROR, "HEAD")):
        run(["git", "clone", "--bare", "--quiet", fork_url(), MIRROR])
    # Upstream objects are needed to build from a pinned public base SHA.
    run(["git", "--git-dir=" + MIRROR, "fetch", "--quiet", upstream_url(),
         "+refs/heads/main:refs/remotes/upstream/main"])
    return run(["git", "--git-dir=" + MIRROR, "rev-parse",
                "refs/remotes/upstream/main"]).stdout.strip()


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


def share_pinned_corpus(worktree, base):
    """Hardlink byte-identical pinned source files to one central corpus.

    `git worktree add` checks out a full copy of the pinned tree (~446 MB at
    present) for every gap attempt, and reclaimed space immediately refills.
    All attempts at the same pinned base are identical for their tracked
    files, so replace those copies with hard links to one preserved central
    corpus. Files a worker creates or mutates remain ordinary per-attempt
    files. Never touches .git or the shared .lake packages.

    The shared corpus is made immutable so an in-place worker edit cannot
    corrupt every attempt that hardlinks it; workers add new candidate files
    rather than rewriting pinned sources. Best effort: a failure here leaves
    the ordinary full checkout in place rather than blocking research.
    """
    import fcntl
    import re

    sha = run(["git", "--git-dir=" + MIRROR, "rev-parse",
               base + "^{commit}"]).stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise GitError("cannot resolve pinned base for corpus sharing")
    root = os.path.join(config.CACHE_DIR, "pinned-corpus")
    os.makedirs(root, exist_ok=True)
    central = os.path.join(root, sha)
    lock = os.path.join(root, sha + ".lock")
    fd = os.open(lock, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        if not os.path.exists(central):
            tmp = central + ".tmp-" + str(os.getpid())
            shutil.rmtree(tmp, ignore_errors=True)
            os.makedirs(tmp, exist_ok=True)
            archive = subprocess.Popen(
                ["git", "--git-dir=" + MIRROR, "archive", sha],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            extract = subprocess.Popen(
                ["tar", "-x", "-C", tmp], stdin=archive.stdout,
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            archive.stdout.close()
            extract_err = extract.communicate()[1]
            archive_err = archive.stderr.read()
            archive.stderr.close()
            archive.wait()
            if archive.returncode or extract.returncode:
                shutil.rmtree(tmp, ignore_errors=True)
                raise GitError("pinned corpus archive failed: " +
                               (archive_err + extract_err).decode(
                                   "utf-8", "replace")[:300])
            for r, _dirs, files in os.walk(tmp):
                for name in files:
                    os.chmod(os.path.join(r, name), 0o444)
            os.replace(tmp, central)
    finally:
        os.close(fd)
    linked = 0
    for r, dirs, files in os.walk(worktree):
        if ".git" in dirs:
            dirs.remove(".git")
        if ".lake" in dirs:
            dirs.remove(".lake")
        rel = os.path.relpath(r, worktree)
        for name in files:
            dst = os.path.join(r, name)
            src = os.path.join(central, name) if rel == "." else \
                os.path.join(central, rel, name)
            try:
                if not os.path.isfile(src) or \
                        os.path.getsize(src) != os.path.getsize(dst):
                    continue
                st = os.stat(dst)
                # rename() of two hardlinks to the same inode is a no-op and
                # would leave the temporary name behind. Already shared: skip.
                if st.st_ino == os.stat(src).st_ino:
                    continue
                tmpdst = dst + ".pnp-link"
                os.link(src, tmpdst)
                os.utime(tmpdst, ns=(st.st_atime_ns, st.st_mtime_ns))
                os.replace(tmpdst, dst)
                linked += 1
            except OSError:
                if os.path.lexists(dst + ".pnp-link"):
                    os.unlink(dst + ".pnp-link")
    return linked


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

"""Deterministic publisher: the ONLY supported authenticated mutation path.

Parameters are strictly (gap id, local candidate file).  Repository, remote,
branch, author, committer, signing key and PR target are internal constants.
Recovery queries remote ground truth before retrying any external effect, so a
restart after SIGNED, PUSHED or PR_OPEN never duplicates a branch or PR.
"""
import os
import time

from . import config, desk as desk_mod, gitctl, github, state, validate


class StopPublish(Exception):
    """A safety condition stopped publication; the reason is recorded."""


def _stop(gap_id, reason):
    rec = state.load(gap_id)
    cur = rec["state"]
    target = "FAULT" if "FAULT" in config.ALLOWED.get(cur, set()) else cur
    if target != cur:
        state.transition(gap_id, target, failure_reason=reason)
    else:
        state.update(gap_id, failure_reason=reason)
    raise StopPublish(reason)


def _retry_later(gap_id, reason):
    """Preserve signed/PUSHED state for transient outages, no PR mutation."""
    state.update(gap_id, failure_reason=reason)
    raise StopPublish(reason)


def _open_gap_ids(desk):
    data = desk.status()
    return {g.get("id") for g in data.get("gaps", [])
            if isinstance(g, dict) and g.get("id")}


def _read_candidate(path):
    if not os.path.isfile(path):
        raise StopPublish("candidate file does not exist")
    with open(path, "rb") as f:
        return f.read()


def publish(gap_id, candidate_path, desk=None, git=None, gh=None,
            build_runner=None, signer=None, pusher=None, known_prs=None):
    """Publish one validated, signed, checked candidate.  Idempotent."""
    desk = desk or desk_mod.Desk()
    git = git or gitctl
    gh = gh or github
    if not config.GAP_ID_RE.match(gap_id):
        raise StopPublish("gap id fails the published grammar")
    rec = state.load(gap_id)
    if rec is None:
        raise StopPublish("gap has no state record")
    if rec["state"] not in ("CANDIDATE_READY", "LOCAL_CHECKED", "SIGNED",
                            "PUSHED", "REJECTED"):
        raise StopPublish("state %s is not publishable" % rec["state"])
    correction = rec["state"] == "REJECTED"
    resume = rec["state"] in ("SIGNED", "PUSHED")

    # Re-read live instructions at startup; a stale pnp.sh comment is not law.
    try:
        desk.docs()
    except Exception as e:
        _retry_later(gap_id, "cannot re-read live desk docs: %s" % e)

    # Fetch public metadata independently; never trust candidate metadata.
    if gap_id not in _open_gap_ids(desk) and not rec.get("pr_number"):
        _stop(gap_id, "gap is not currently posted at the desk")
    gap_meta = {
        "id": gap_id, "file": rec.get("path"), "module": rec.get("module"),
        "statement": rec.get("statement"), "imports": rec.get("imports"),
    }
    data = _read_candidate(candidate_path)
    try:
        digest = validate.validate(gap_meta, data)
    except validate.InvalidCandidate as e:
        _stop(gap_id, "candidate validation failed: %s" % e)
    if (rec.get("candidate_digest") and
            rec["candidate_digest"] != digest and not correction):
        _stop(gap_id, "candidate digest changed since local check")
    state.update(gap_id, candidate_digest=digest)

    # Renew the lease before submitting; 410 means someone else settled it.
    if rec.get("lease") and not correction and not resume and not rec.get("pr_number"):
        try:
            if desk.beat(rec["lease"]) == 410:
                _stop(gap_id, "lease returned 410 at submission")
        except StopPublish:
            raise
        except Exception as e:
            _stop(gap_id, "lease renewal failed: %s" % e)
        state.update(gap_id, lease_expires_at=time.time() +
                     config.LEASE_TTL_SECONDS)

    branch = rec.get("branch") or config.branch_for(gap_id)
    if not resume:
        latest_base = git.ensure_mirror()
        base_sha = (rec.get("base_sha") if correction else latest_base)
        if not base_sha:
            _stop(gap_id, "correction has no pinned original base")
        state.update(gap_id, base_sha=base_sha, branch=branch)
        worktree = git.fresh_worktree(gap_id, base_sha, branch)
        state.update(gap_id, worktree=worktree)
        try:
            if correction:
                git.pin_candidate(worktree, rec["path"], data, correction=True)
            else:
                git.pin_candidate(worktree, rec["path"], data)
        except Exception as e:
            _stop(gap_id, "staging failed: %s" % e)
        ok, log = git.build(worktree, rec["module"], rec["statement"],
                            runner=build_runner)
        if not ok:
            _stop(gap_id, "pinned Lean/Mathlib build failed: %s" % log[-300:])
        if rec["state"] == "CANDIDATE_READY":
            state.transition(gap_id, "LOCAL_CHECKED", candidate_digest=digest)
        state.intent(gap_id, "signed_commit",
                     {"base": base_sha, "path": rec["path"]})
        try:
            if correction:
                sha = git.signed_commit(worktree, base_sha, gap_id,
                                        signer=signer, correction=True)
            else:
                sha = git.signed_commit(worktree, base_sha, gap_id,
                                        signer=signer)
        except Exception as e:
            _stop(gap_id, "signed commit failed: %s" % e)
        state.clear_intent(gap_id)
        if correction and not git.all_new_commits_signed(worktree, base_sha):
            _stop(gap_id, "a PR-range commit is unsigned or misattributed")
        if correction:
            state.transition(gap_id, "RESEARCHING")
            state.transition(gap_id, "CANDIDATE_READY")
            state.transition(gap_id, "LOCAL_CHECKED")
        state.transition(gap_id, "SIGNED", commit_sha=sha)
        expected_commits = (git.new_commits(worktree, base_sha) if correction
                            and hasattr(git, "new_commits") else [sha])
    else:
        sha = rec.get("commit_sha")
        base_sha = rec.get("base_sha")
        if not sha or not base_sha:
            _stop(gap_id, "resume lacks a signed commit or pinned base")
        expected_commits = [sha]

    # Before any mutation: authenticated identity and remote ground truth.
    try:
        gh.identity()
    except Exception as e:
        _retry_later(gap_id, "GitHub identity preflight failed: %s" % e)
    remote = git.remote_branch_sha(branch)
    if remote == sha:
        pass                                   # already pushed: recover
    elif correction and remote == rec.get("commit_sha"):
        # The fork still carries the rejected, signed commit.  The new
        # signed commit must descend from it; Git rejects non-FF pushes.
        state.intent(gap_id, "push_correction",
                     {"branch": branch, "sha": sha, "previous": remote})
        try:
            pushed = git.push_branch(branch, pusher=pusher)
        except Exception as e:
            _stop(gap_id, "correction push failed: %s" % e)
        state.clear_intent(gap_id)
        if pushed != sha:
            _stop(gap_id, "correction push returned a different SHA")
    elif remote is not None:
        _stop(gap_id, "remote branch differs from our signed commit")
    elif rec["state"] == "PUSHED":
        _stop(gap_id, "state says pushed but the fork branch is missing")
    else:
        state.intent(gap_id, "push", {"branch": branch, "sha": sha})
        try:
            pushed = git.push_branch(branch, pusher=pusher)
        except Exception as e:
            _stop(gap_id, "push failed: %s" % e)
        state.clear_intent(gap_id)
        if pushed != sha:
            _stop(gap_id, "pushed SHA differs from signed SHA")
    if state.load(gap_id)["state"] == "SIGNED":
        state.transition(gap_id, "PUSHED", commit_sha=sha)

    try:
        ver = gh.commit_verification(sha)
    except Exception as e:
        _retry_later(gap_id, "GitHub verification unavailable: %s" % e)
    if ver.get("verified") is not True:
        _retry_later(gap_id, "GitHub signature not yet verified; no PR opened")
    if (ver.get("name") != config.AUTHOR_NAME or
            ver.get("email") != config.AUTHOR_EMAIL):
        _stop(gap_id, "GitHub commit identity mismatch; no PR opened")

    number = rec.get("pr_number") or gh.pr_exists_for(
        branch, gap_id, api=known_prs)
    if not number:
        state.intent(gap_id, "create_pr", {"branch": branch, "gap": gap_id})
        try:
            number = gh.create_pr(branch, gap_id)
        except Exception as e:
            _retry_later(gap_id, "PR creation failed; reconcile before retry: %s" % e)
        state.clear_intent(gap_id)
    number = int(number)
    pr, problems = gh.validate_created(number, sha, rec["path"],
                                       expected_commits=expected_commits)
    if problems:
        _stop(gap_id, "post-create PR validation failed: " + "; ".join(problems))
    if rec.get("lease") and not correction and not rec.get("pr_number"):
        try:
            desk.release(rec["lease"], "submitted")
        except Exception as e:
            state.update(gap_id, failure_reason="release retry needed: %s" % e)
    if state.load(gap_id)["state"] in ("PUSHED", "SIGNED", "LOCAL_CHECKED"):
        state.transition(gap_id, "PR_OPEN", pr_number=number,
                         pr_url=pr.get("url"), external_verdict="pending",
                         failure_reason=None)
    else:
        state.update(gap_id, pr_number=number, pr_url=pr.get("url"),
                     external_verdict="pending")
    state.event(gap_id, "published", {"sha": sha, "pr": number,
                                      "digest": digest})
    return {"gap": gap_id, "sha": sha, "pr": number, "url": pr.get("url"),
            "digest": digest}


def correct(gap_id, candidate_path, **kwargs):
    """Allowed correction: fixed file, same PR, every new commit signed."""
    return publish(gap_id, candidate_path, **kwargs)

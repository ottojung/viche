"""Deterministic publisher: the ONLY supported authenticated mutation path.

Parameters are strictly (gap id, local candidate file).  Repository, remote,
branch, author, committer, signing key and PR target are internal constants.
Recovery queries remote ground truth before retrying any external effect, so a
restart after SIGNED, PUSHED or PR_OPEN never duplicates a branch or PR.
"""
import os
import time

from . import config, desk as desk_mod, gitctl, github, state, validate, evidence


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


def _candidate_failed(gap_id, reason):
    rec = state.load(gap_id)
    if rec["state"] in ("CANDIDATE_READY", "LOCAL_CHECKED"):
        state.transition(gap_id, "RESEARCHING", candidate_digest=None,
                         queued_lease=None, failure_reason=reason)
    else:
        state.update(gap_id, queued_lease=None, failure_reason=reason)
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


def release_submitted(gap_id, desk):
    """A validated PR is tracked even if the desk release needs retry."""
    rec = state.load(gap_id)
    if not rec.get("release_pending"):
        return
    try:
        desk.release(rec["lease"], "submitted")
    except Exception as exc:
        state.update(gap_id, failure_reason="release retry needed: %s" % exc)
        return
    state.update(gap_id, release_pending=False, failure_reason=None)


def record_pr(gap_id, rec, number, pr, desk):
    """Commit verified PR identity before attempting the separate desk effect."""
    with state.lock(gap_id):
        current = state.load(gap_id)
        if (current.get("commit_sha") != rec.get("commit_sha") or
                current.get("lease") != rec.get("lease") or
                current["state"] not in ("SIGNED", "PUSHED", "LOCAL_CHECKED", "FAULT", "PR_OPEN")):
            raise StopPublish("publication changed during PR verification")
        release = bool(current.get("lease") and not current.get("pr_number")
                       and not current.get("correction_from_sha"))
        current.update(state="PR_OPEN", pr_number=number, pr_url=pr.get("url"),
                       pending_pr_number=None, external_verdict="pending",
                       queued_lease=None, failure_reason=None, correction_from_sha=None,
                       release_pending=release or current.get("release_pending", False),
                       intent=None)
        state.save(current)
        state.event(gap_id, "published", {"sha": current.get("commit_sha"),
                                          "pr": number, "digest": current.get("candidate_digest")})
    release_submitted(gap_id, desk)


def publish(gap_id, candidate_path, desk=None, git=None, gh=None,
            build_runner=None, signer=None, pusher=None, known_prs=None):
    """Publish a complete statically validated candidate immediately. Idempotent."""
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
    correction = rec["state"] == "REJECTED" or bool(rec.get("correction_from_sha"))
    resume = rec["state"] in ("SIGNED", "PUSHED")

    # Re-read live instructions at startup; a stale pnp.sh comment is not law.
    try:
        desk.docs()
    except Exception as e:
        _retry_later(gap_id, "cannot re-read live desk docs: %s" % e)

    # The exact statement comes from the acquired lease. A status listing may
    # be incomplete; use the authoritative beat instead of a redundant GET.
    if not rec.get("lease") and not rec.get("pr_number"):
        _stop(gap_id, "no live assignment or existing PR")
    gap_meta = {
        "id": gap_id, "file": rec.get("path"), "module": rec.get("module"),
        "statement": rec.get("statement"), "imports": rec.get("imports"),
    }
    data = _read_candidate(candidate_path)
    try:
        digest = validate.validate(gap_meta, data)
    except validate.InvalidCandidate as e:
        _candidate_failed(gap_id, "candidate validation failed: %s" % e)
    if (rec.get("candidate_digest") and
            rec["candidate_digest"] != digest and not correction):
        _candidate_failed(gap_id, "candidate digest changed since local check")
    state.update(gap_id, candidate_digest=digest)

    # Renew the lease before submitting; 410 means someone else settled it.
    if rec.get("lease") and not correction and not resume and not rec.get("pr_number"):
        try:
            if desk.beat(rec["lease"]) == 410:
                state.stale_lease(gap_id, rec["lease"], "lease returned 410 at submission")
                raise StopPublish("lease returned 410 at submission")
        except StopPublish:
            raise
        except Exception as e:
            _retry_later(gap_id, "lease renewal failed: %s" % e)
        state.update(gap_id, lease_expires_at=time.time() +
                     config.LEASE_TTL_SECONDS)

    branch = rec.get("branch") or config.branch_for(gap_id)
    if not resume:
        base_sha = rec.get("base_sha")
        worktree = rec.get("worktree")
        try:
            latest_base = git.ensure_mirror()
            base_sha = rec.get("base_sha") or latest_base
            old = (rec.get("build_evidence") or {}).get("base")
            if (not correction and not rec.get("base_sha")
                    and hasattr(git, "is_upstream_ancestor")
                    and old and evidence.matching(rec, digest, old)
                    and git.is_upstream_ancestor(old, latest_base)):
                base_sha = old
            if not base_sha:
                _stop(gap_id, "missing pinned base")
            if correction:
                previous = rec.get("correction_from_sha") or rec.get("commit_sha")
                pr = gh.get_pr(rec["pr_number"])
                if pr.get("state") != "open" or pr.get("head_sha") != previous:
                    _stop(gap_id, "correction requires the original open PR head")
                state.update(gap_id, correction_from_sha=previous)
            state.update(gap_id, base_sha=base_sha, branch=branch)
            worktree = git.fresh_worktree(gap_id, base_sha, branch)
            state.update(gap_id, worktree=worktree)
            if hasattr(git, "prepare_unpublished"):
                git.prepare_unpublished(worktree, branch, base_sha,
                                        previous if correction else None)
            if correction:
                git.pin_candidate(worktree, rec["path"], data, correction=True)
            else:
                git.pin_candidate(worktree, rec["path"], data)
        except StopPublish:
            raise
        except Exception as e:
            _retry_later(gap_id, "publication checkout unavailable: %s" % e)
        # No local build gate. Reuse exact managed evidence if available;
        # otherwise the signed revision is checked after PR creation.
        checked = evidence.matching(state.load(gap_id), digest, base_sha)
        state.update(gap_id, local_check_status="passed" if checked else "pending",
                     local_check_retry_at=None, local_check_log=None)
        # Recheck lease immediately before external publication.
        if not correction:
            current = state.load(gap_id)
            if current["state"] in ("STALE", "RELEASED") or current.get("lease") != rec.get("lease"):
                raise StopPublish("gap settled during local build")
            try:
                live = desk.beat(current["lease"])
            except Exception as e:
                _retry_later(gap_id, "lease recheck failed: %s" % e)
            if live == 410:
                state.stale_lease(gap_id, current["lease"], "lease lost during build")
                raise StopPublish("lease lost during build")
            state.update(gap_id, lease_expires_at=time.time() + config.LEASE_TTL_SECONDS)
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
        expected_commits = (git.new_commits(worktree, base_sha) if correction
                            and hasattr(git, "new_commits") else [sha])
        state.transition(gap_id, "SIGNED", commit_sha=sha,
                         expected_commits=expected_commits)
    else:
        sha = rec.get("commit_sha")
        base_sha = rec.get("base_sha")
        if not sha or not base_sha:
            _stop(gap_id, "resume lacks a signed commit or pinned base")
        expected_commits = rec.get("expected_commits") or [sha]

    # Before any mutation: authenticated identity and remote ground truth.
    try:
        gh.identity()
    except Exception as e:
        _retry_later(gap_id, "GitHub identity preflight failed: %s" % e)
    remote = git.remote_branch_sha(branch)
    if correction:
        existing = gh.get_pr(rec["pr_number"])
        if existing.get("state") != "open" or existing.get("head_sha") not in (remote, sha):
            _stop(gap_id, "correction PR no longer open at expected head")
    if remote == sha:
        pass                                   # already pushed: recover
    elif correction and remote == (rec.get("correction_from_sha") or rec.get("commit_sha")):
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

    number = rec.get("pr_number") or rec.get("pending_pr_number") or gh.pr_exists_for(
        branch, gap_id, api=known_prs)
    if not number:
        if not correction:
            # Recheck only when resuming a signed/pushed proof: the old beat
            # may no longer be live. Existing PRs can always be recovered.
            if resume:
                try:
                    if desk.beat(rec["lease"]) == 410:
                        _stop(gap_id, "lease ended before PR creation")
                except StopPublish:
                    raise
                except Exception as exc:
                    _retry_later(gap_id, "lease recheck failed: %s" % exc)
        state.intent(gap_id, "create_pr", {"branch": branch, "gap": gap_id})
        try:
            number = gh.create_pr(branch, gap_id)
        except Exception as e:
            _retry_later(gap_id, "PR creation failed; reconcile before retry: %s" % e)
        # Persist the observed number before any fallible validation call.
        state.update(gap_id, pending_pr_number=int(number), intent=None)
    number = int(number)
    pr, problems = gh.validate_created(number, sha, rec["path"],
                                       expected_commits=expected_commits)
    if problems:
        _stop(gap_id, "post-create PR validation failed: " + "; ".join(problems))
    record_pr(gap_id, state.load(gap_id), number, pr, desk)
    return {"gap": gap_id, "sha": sha, "pr": number, "url": pr.get("url"),
            "digest": digest}


def correct(gap_id, candidate_path, **kwargs):
    """Allowed correction: fixed file, same PR, every new commit signed."""
    return publish(gap_id, candidate_path, **kwargs)

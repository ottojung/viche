"""Nonfatal, idempotent reconciliation after interruption or restart.

Queries remote ground truth (desk, fork, upstream PRs) before retrying.
Never opens a PR itself and never mistakes a checker verdict for novelty.
"""
import os
import re
import time

from . import config, desk as desk_mod, gitctl, github, state, frontier

VERDICT = re.compile(
    r"^Checked on the base repository at commit `([0-9a-f]{9,40})`\.\s+"
    r"\*\*(ACCEPTED|REJECTED|FAULT|REFUSED) \([^\n]*\)\*\*", re.M)


def current_verdict(comments, sha):
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        return None
    verdicts = []
    for comment in comments:
        if comment.get("author") != "LiorDagan":
            continue
        body = comment.get("body") or ""
        match = VERDICT.search(body)
        if (match and sha.startswith(match[1]) and
                re.search(r"^Run: https://github\.com/brilliant-hq/pequalnp-proofs/actions/runs/[0-9]+$", body, re.M)):
            verdicts.append((comment.get("created_at", ""), match[2]))
    return max(verdicts)[1] if verdicts else None


def _heartbeat(gap_id, rec, desk, force=False):
    if not rec.get("lease") or rec["state"] not in (
            "LEASED", "RESEARCHING", "CANDIDATE_READY", "LOCAL_CHECKED"):
        return
    now = time.time()
    last = rec.get("lease_expires_at") or 0
    if not force and now < last - config.LEASE_TTL_SECONDS + config.BEAT_INTERVAL_SECONDS:
        return
    try:
        status = desk.beat(rec["lease"])
    except Exception:
        return
    if status == 410:
        state.stale_lease(gap_id, rec["lease"], "lease returned 410")
    else:
        state.update(gap_id, lease_expires_at=now + config.LEASE_TTL_SECONDS)


def reconcile_gap(gap_id, desk=None, gh=None, git=None, observed=None):
    """Return a short summary; never raise for one bad gap."""
    desk = desk or desk_mod.Desk()
    gh = gh or github
    git = git or gitctl
    rec = state.load(gap_id)
    if rec is None:
        return {"gap": gap_id, "result": "no-state"}
    if rec["state"] in ("ACCEPTED", "RELEASED", "STALE"):
        return {"gap": gap_id, "result": "terminal", "state": rec["state"]}

    # Missing from a complete fresh frontier is a reason to confirm, not a verdict.
    _heartbeat(gap_id, rec, desk, force=frontier.missing(observed or {}, gap_id))
    rec = state.load(gap_id)
    if rec["state"] in ("ACCEPTED", "RELEASED", "STALE"):
        return {"gap": gap_id, "result": "terminal", "state": rec["state"]}

    # A detached deterministic publisher owns a durable candidate. Recovery
    # never starts a competing build or holds the short reconciliation pass.
    from . import jobs
    if rec["state"] != "PR_OPEN" and jobs.resume(gap_id):
        return {"gap": gap_id, "result": "publishing", "state": rec["state"]}

    branch = rec.get("branch") or config.branch_for(gap_id)
    remote = (git.remote_branch_sha(branch)
              if rec["state"] in ("SIGNED", "PUSHED", "PR_OPEN")
              else None)
    if remote and rec["state"] == "SIGNED":
        if remote == rec.get("commit_sha"):
            state.transition(gap_id, "PUSHED")
        else:
            state.transition(gap_id, "FAULT",
                             failure_reason="remote branch SHA differs")
    elif not remote and rec["state"] == "PUSHED":
        # Branch disappeared: do not silently re-push; record for inspection.
        state.update(gap_id, failure_reason="pushed branch missing at fork")

    number = rec.get("pr_number")
    if not number and rec["state"] in ("SIGNED", "PUSHED", "PR_OPEN"):
        number = gh.pr_exists_for(branch, gap_id)
    if not number and rec["state"] in ("SIGNED", "PUSHED"):
        # A process can die after push and before gh pr create.  Do not
        # strand a signed contribution indefinitely: finish idempotently
        # from its preserved proof file and pinned commit.
        candidate = os.path.join(rec.get("worktree") or "",
                                 rec.get("path") or "")
        if rec.get("worktree") and os.path.isfile(candidate):
            try:
                from . import publish
                published = publish.publish(
                    gap_id, candidate, desk=desk, git=git, gh=gh)
                state.update(gap_id, last_reconcile=time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
                return {"gap": gap_id, "result": "publish-recovered",
                        "state": "PR_OPEN", "pr": published["pr"]}
            except Exception as e:
                state.update(gap_id, failure_reason=(
                    "retry PR publication after push: %s" % e))
        else:
            state.update(gap_id, failure_reason=(
                "signed publication recovery requires the preserved candidate"))
    if number:
        number = int(number)
        pr = gh.get_pr(number)
        if rec["state"] in ("PUSHED", "SIGNED", "LOCAL_CHECKED") and pr.get("head_sha") == rec.get("commit_sha"):
            state.transition(gap_id, "PR_OPEN", pr_number=number,
                             pr_url=pr.get("url"),
                             external_verdict="pending")
        state.update(gap_id, pr_number=number, pr_url=pr.get("url"))
        current = state.load(gap_id)
        if current["state"] in ("PR_OPEN", "REJECTED") and not current.get("queued_lease") and pr.get("head_sha") == current.get("commit_sha"):
            verdict = current_verdict(gh.pr_comments(number), current.get("commit_sha"))
            # A checker success is not a merged contribution; a competitor
            # can win before the merge. Never apply an old revision's verdict.
            with state.lock(gap_id):
                latest = state.load(gap_id)
                if latest["state"] in ("PR_OPEN", "REJECTED") and not latest.get("queued_lease") and latest.get("commit_sha") == current.get("commit_sha"):
                    before = latest["state"]
                    if pr.get("merged") is True and verdict == "ACCEPTED":
                        latest.update(state="ACCEPTED", external_verdict="ACCEPTED", queued_lease=None)
                    elif pr.get("state") == "closed" and not pr.get("merged"):
                        latest.update(state="STALE", failure_reason="PR closed without merge", queued_lease=None)
                    elif verdict in ("REJECTED", "REFUSED"):
                        latest.update(state="REJECTED", external_verdict=verdict, queued_lease=None)
                    elif verdict == "FAULT":
                        latest.update(external_verdict="FAULT")
                    elif verdict == "ACCEPTED":
                        latest.update(external_verdict="ACCEPTED")
                    state.save(latest)
                    if latest["state"] != before:
                        state.event(gap_id, "state", {"to": latest["state"], "sha": latest.get("commit_sha")})
            from . import postcheck
            postcheck.resume(gap_id, state.load(gap_id))
    rec = state.load(gap_id)
    state.update(gap_id, last_reconcile=time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                      time.gmtime()))
    return {"gap": gap_id, "result": "ok", "state": rec["state"],
            "pr": rec.get("pr_number")}


def reconcile_all(desk=None, gh=None, git=None):
    results = []
    observed = frontier.load()
    desk = desk or desk_mod.Desk()
    for gap_id in state.all_gaps():
        try:
            results.append(reconcile_gap(gap_id, desk=desk, gh=gh, git=git, observed=observed))
        except Exception as e:                       # nonfatal by construction
            try:
                rec = state.load(gap_id)
                if rec:
                    # Network or checker outages must not expire unrelated
                    # running research: preserve current state and retry.
                    state.update(gap_id, failure_reason="reconcile: %s" % e)
            except Exception:
                pass
            results.append({"gap": gap_id, "result": "error", "detail": str(e)})
    return results

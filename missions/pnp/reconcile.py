"""Nonfatal, idempotent reconciliation after interruption or restart.

Queries remote ground truth (desk, fork, upstream PRs) before retrying.
Never opens a PR itself and never mistakes a checker verdict for novelty.
"""
import os
import re
import time

from . import config, desk as desk_mod, gitctl, github, state

VERDICT = re.compile(r"\b(ACCEPTED|REJECTED|FAULT)\b")


def _heartbeat(gap_id, rec, desk):
    if not rec.get("lease") or rec["state"] not in (
            "LEASED", "RESEARCHING", "CANDIDATE_READY", "LOCAL_CHECKED"):
        return
    now = time.time()
    last = rec.get("lease_expires_at") or 0
    if now < last - config.LEASE_TTL_SECONDS + config.BEAT_INTERVAL_SECONDS:
        return
    try:
        status = desk.beat(rec["lease"])
    except Exception:
        return
    if status == 410:
        state.transition(gap_id, "STALE", failure_reason="lease returned 410")
    else:
        state.update(gap_id, lease_expires_at=now + config.LEASE_TTL_SECONDS)


def reconcile_gap(gap_id, desk=None, gh=None, git=None):
    """Return a short summary; never raise for one bad gap."""
    desk = desk or desk_mod.Desk()
    gh = gh or github
    git = git or gitctl
    rec = state.load(gap_id)
    if rec is None:
        return {"gap": gap_id, "result": "no-state"}
    if rec["state"] in ("ACCEPTED", "RELEASED", "STALE") or (
            rec["state"] == "REJECTED" and not rec.get("queued_lease")):
        return {"gap": gap_id, "result": "terminal", "state": rec["state"]}

    _heartbeat(gap_id, rec, desk)
    rec = state.load(gap_id)
    if rec["state"] in ("ACCEPTED", "RELEASED", "STALE") or (
            rec["state"] == "REJECTED" and not rec.get("queued_lease")):
        return {"gap": gap_id, "result": "terminal", "state": rec["state"]}

    # A detached deterministic publisher owns a durable candidate. Recovery
    # never starts a competing build or holds the short reconciliation pass.
    from . import jobs
    if jobs.resume(gap_id):
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
        if rec["state"] in ("PUSHED", "SIGNED", "LOCAL_CHECKED"):
            state.transition(gap_id, "PR_OPEN", pr_number=number,
                             pr_url=pr.get("url"),
                             external_verdict="pending")
        state.update(gap_id, pr_number=number, pr_url=pr.get("url"))
        comments = gh.pr_comments(number)
        verdicts = [(m.get("created_at", ""),
                     VERDICT.search(m.get("body", "")).group(1))
                    for m in comments
                    if VERDICT.search(m.get("body", ""))]
        if verdicts:
            verdict = sorted(verdicts)[-1][1]
            if verdict != "FAULT":
                state.transition(gap_id, verdict,
                                 external_verdict=verdict, queued_lease=None)
            else:
                state.update(gap_id, external_verdict="FAULT",
                             failure_reason="upstream checker FAULT; will recheck")
    else:
        # If the desk no longer lists the gap and nothing was submitted, it
        # is genuinely gone; keep the research record.
        if rec["state"] == "LEASED" or rec["state"] == "RESEARCHING":
            try:
                open_ids = {g.get("id") for g in desk.status().get("gaps", [])
                            if isinstance(g, dict)}
            except Exception:
                open_ids = None
            if open_ids is not None and gap_id not in open_ids:
                state.transition(gap_id, "STALE",
                                 failure_reason="gap no longer posted")
    rec = state.load(gap_id)
    state.update(gap_id, last_reconcile=time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                      time.gmtime()))
    return {"gap": gap_id, "result": "ok", "state": rec["state"],
            "pr": rec.get("pr_number")}


def reconcile_all(desk=None, gh=None, git=None):
    results = []
    for gap_id in state.all_gaps():
        try:
            results.append(reconcile_gap(gap_id, desk=desk, gh=gh, git=git))
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

"""Allocator fast lane: turn held concrete steps into PRs within one tick, and keep slots cycling.

Called by allocator.tick before fill(). Consumes the files written by missions.pnp.lbcert.autosolve
(PNP_STATE_ROOT/lbcert). Three rules, each recorded as a gap event:

1. SUBMIT. A held step with a ready lb_cert candidate goes straight to the ordinary publisher
   (jobs.submit). No local re-verification: the generator's certificates were ACCEPTED by the
   official checker on every instance tried (7309, 5459, 8493, 8487, 8483), and the races for this
   family are lost by minutes.
2. FALSE TWIN. A held negation is released only when an exact compiler receipt
   exists for its negated twin. The checked twin goes through the allocator's
   documented proof-of acquisition rather than a separate unheld PR path.
3. CYCLE. Research leases may hold at most RESEARCH_SLOTS of the MAX_LEASES slots. When all slots
   are full and more are held by research, release the oldest non-focus research lease that has been
   held at least the desk's twenty minutes and has no candidate (reason out_of_time). The freed slot
   is refilled by fill() in the same tick, which is how the town receives freshly posted steps.
"""
import json
import os
import re
import subprocess
import sys
import time

from . import cli, config, focus, jobs, state, support

WORK = os.path.join(config.STATE_ROOT, "lbcert")
CANDS = os.path.join(WORK, "cands")
RESEARCH_SLOTS = 1
RESEARCH_MIN_AGE = 20 * 60
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lbcert"))
import lbparse  # noqa: E402


def _read(name, default):
    try:
        with open(os.path.join(WORK, name), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def cand_ready(gap, allow_generated=True):
    from .lbcert import ready
    receipt=ready.verified(gap)
    if receipt and receipt.get("origin")=="private-prelease":
        return str(ready.directory()/(gap+".lean"))
    try:
        with open(os.path.join(CANDS, gap + ".status"), encoding="utf-8") as f:
            marker = f.read().split()
            ok = bool(marker and (marker[0] == "ok" or allow_generated and marker[0] == "generated"))
    except OSError:
        return None
    path = os.path.join(CANDS, gap + ".lean")
    return path if ok and os.path.exists(path) else None


def submit_ready(gap):
    """Generator completion wakes the ordinary publisher immediately.

    No build gate, no direct GitHub mutation, no acquisition and no release.
    The normal jobs lock handles a concurrent allocator tick or worker.
    """
    from . import posting
    if posting.paused():return None
    rec = state.load(gap)
    if not support.active(rec) or rec.get("queued_lease") or rec.get("candidate_digest"):
        return None
    if rec.get("work_lane") == "posting":
        from .lbcert import ready
        # A stock completion may race a freshly acquired assignment. Only
        # exact receipts, and no already-observed rival, are useful here.
        if posting.rival(rec,ready.competition(time.time())) or not ready.verified(gap):
            return None
    path = cand_ready(gap)
    if not path:
        return None
    result = jobs.submit(gap, path, expected_lease=rec["lease"],only_unclaimed=True)
    state.event(gap, "generator_ready_submit", {"status": str(result)[:300]})
    return result


def concrete(rec):
    s = rec.get("statement") or ""
    return bool(lbparse.family(s) or re.fullmatch(r"¬ ?\((.*)\)", lbparse.norm(s)) and
                lbparse.classify(re.fullmatch(r"¬ ?\((.*)\)", lbparse.norm(s)).group(1)))


def release(d, mem, gap, reason, evidence, expected_lease=None):
    fd = jobs.claim(gap)
    if fd is None:
        return False
    try:
        with state.lock(gap):
            rec = state.load(gap)
            if (not support.active(rec) or (expected_lease and rec.get("lease") != expected_lease) or rec.get("queued_lease") or rec.get("intent")
                    or rec.get("pr_number") or rec.get("candidate_digest")):
                return False
            rec["intent"] = {"what": "fastlane_release", "payload": {"reason": reason}}
            state.save(rec)
            try:
                d.release(rec["lease"], reason)
            except Exception as exc:
                rec["intent"] = None
                state.save(rec)
                print("fastlane release deferred:", gap, str(exc)[:200], flush=True)
                return False
            rec.update(state="RELEASED", failure_reason=reason, intent=None)
            state.save(rec)
            state.event(gap, "fastlane_release", {"reason": reason, "evidence": evidence})
        mem.pop("last_null_ordinary", None)
        mem.pop("last_null_hard", None)
        mem.pop("posting_retry_at", None)
        return True
    finally:
        os.close(fd)


def tick(d, mem, now, roster_known=True, cycle_research=True):
    out = {"submitted": [], "twin_published": [], "released": []}
    from . import posting
    if posting.paused():return out
    twins, desk = _read("twins.json", {}), _read("desk.json", {})
    held = cli.held_records()
    for rec in held:
        gap = rec["gap_id"]
        if not support.active(rec, now) or rec.get("work_lane") == "posting" or rec.get("queued_lease") or rec.get("candidate_digest"):
            continue
        path = cand_ready(gap)
        if path:
            try:
                res = jobs.submit(gap, path,expected_lease=rec["lease"],only_unclaimed=True)
                state.event(gap, "fastlane_submit", {"candidate": path, "result": str(res)[:300]})
                out["submitted"].append(gap)
            except Exception as exc:
                state.event(gap, "fastlane_submit_failed", {"error": str(exc)[:300]})
                print("fastlane submit failed:", gap, str(exc)[:200], flush=True)
            continue
        lb = twins.get(gap)
        if not lb:
            continue
        from .lbcert import ready
        # A mathematical candidate or old "ok" marker is not a kernel
        # proof of the negated twin. Only exact checked evidence justifies
        # release, then the checked twin enters targeted acquisition.
        if not ready.verified(lb):
            continue
        if release(d, mem, gap, "statement_seems_false",
                   "Exact checked proof of the negated twin %s establishes that this negation is false." % lb,expected_lease=rec["lease"]):
            out["released"].append(gap)
    # Rule 3: keep two slots cycling.
    held = cli.held_records()
    chosen = focus.current()
    research = [r for r in held if support.active(r, now) and r.get("work_lane") != "posting" and not concrete(r) and not r.get("queued_lease")
                and not r.get("candidate_digest") and not r.get("pr_number")]
    # An incomplete worker roster means we cannot see who is working; never cycle then.
    # The desk's earned capacity (3 on 2026-11-26) may be below MAX_LEASES: cycle against it, keeping
    # min(2, limit - 1) slots for fresh steps, else this rule never fires and research holds every slot.
    from . import desk as desk_mod
    limit = desk_mod.lease_limit()
    slots = min(RESEARCH_SLOTS, max(1, limit - 2))
    if cycle_research and roster_known and len(held) >= limit and len(research) > slots:
        old = sorted((r for r in research if not (chosen and focus.key(chosen) == focus.key(r))
                      and now - (r.get("lease_obtained_at") or now) >= RESEARCH_MIN_AGE),
                     key=lambda r: r.get("lease_obtained_at") or now)
        if old:
            r = old[0]
            if release(d, mem, r["gap_id"], "out_of_time",
                       "fast-lane slot cycling: research leases may hold at most %d of %d slots; this was the oldest "
                       "non-focus research lease (%d min) with no candidate." % (
                           slots, limit, (now - r["lease_obtained_at"]) // 60)):
                out["released"].append(r["gap_id"])
    return out

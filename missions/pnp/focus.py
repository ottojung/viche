"""One stable research target; all other held gaps are intentional reserves."""
import json
import os
import time

from . import config, state


def correction(rec):
    return bool(rec and rec.get("pr_number") and not rec.get("queued_lease")
                and rec.get("external_verdict") != "ACCEPTED"
                and (rec.get("state") == "REJECTED" or
                     (rec.get("state") == "PR_OPEN" and rec.get("local_check_status") == "failed")))


def eligible(rec, now=None):
    if correction(rec):
        return True
    return bool(rec and rec.get("state") in ("LEASED", "RESEARCHING")
                and rec.get("lease") and not rec.get("queued_lease")
                and isinstance(rec.get("lease_expires_at"), (int, float))
                and rec["lease_expires_at"] > (time.time() if now is None else now))


def key(rec):
    return rec["gap_id"], rec["lease"]


def priority(rec):
    context = (rec.get("context") or "").lower()
    concrete = any(s in context for s in ("data row", "explicit object", "witness to formalize",
                                          "closes in", "by decide"))
    # An ordinary lease and concrete checked witness are useful signals, not
    # predictions of success. Never preempt a live focus on this heuristic.
    return (not correction(rec), not concrete, rec.get("acquisition_hard") is not False,
            rec.get("acquisition_prs") if type(rec.get("acquisition_prs")) is int else 999,
            len(rec.get("statement") or ""),
            rec.get("lease_obtained_at") or 0, rec["gap_id"])


def choose(records, previous=None, staffed=(), now=None):
    candidates = [r for r in records if eligible(r, now)]
    for rec in candidates:
        if previous and key(rec) == tuple(previous):
            return rec
    if not candidates:
        return None
    return min(candidates, key=lambda r: (key(r) not in staffed, priority(r)))


def current():
    try:
        with open(os.path.join(config.STATE_ROOT, "allocator.json"), encoding="utf-8") as f:
            selected = json.load(f).get("focus")
        if isinstance(selected, list) and len(selected) == 2:
            rec = state.load(selected[0])
            if eligible(rec) and key(rec) == tuple(selected):
                return rec
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    # Before the first allocator tick, or during a rotation, report a useful
    # provisional focus. Only the allocator persists a choice.
    return choose([state.load(g) for g in state.all_gaps()])

"""Observed research funnel. Lease-slot time is not CPU or agent time."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import statistics

from . import state, leaderboard


def timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def replay(events, now):
    attempts, prs, checks = [], {}, Counter()
    current = None
    malformed = 0
    for event in events:
        try:
            t = timestamp(event["at"])
            kind = event["kind"]
            d = event["detail"]
            if not isinstance(d, dict):
                raise ValueError("detail")
        except (ValueError, TypeError, KeyError, AttributeError):
            malformed += 1
            continue
        if kind == "acquired":
            if current and current["end"] is None:
                current.update(end=max(current["start"], t), outcome="superseded")
            current = dict(start=t, end=None, outcome="active", candidate=None, pr=None)
            attempts.append(current)
        elif kind == "state":
            target = d.get("to")
            if current and target == "CANDIDATE_READY" and current["candidate"] is None:
                current["candidate"] = max(current["start"], t)
            if current and current["end"] is None and target in ("RELEASED", "STALE"):
                current.update(end=max(current["start"], t), outcome=target.lower())
            if target == "ACCEPTED":
                for item in prs.values():
                    if item["sha"] == d.get("sha"):
                        item["accepted"] = t
        elif kind == "portfolio_release":
            if current and current["end"] is None:
                current.update(end=max(current["start"], t), outcome="released")
        elif kind == "published":
            pr = d.get("pr")
            if not isinstance(pr, int) or isinstance(pr, bool):
                continue
            if pr not in prs:
                prs[pr] = dict(first=t, sha=d.get("sha"), accepted=None)
            else:
                prs[pr]["sha"] = d.get("sha")
            if current and current["end"] is None:
                current.update(end=max(current["start"], t), outcome="submitted", pr=pr)
        elif kind == "postcheck":
            checks[d.get("local_check_status") or "deferred_or_unspecified"] += 1
    for a in attempts:
        a["slot_seconds"] = max(0, (a["end"] if a["end"] is not None else now) - a["start"])
    return attempts, prs, checks, malformed


def snapshot(now=None):
    now = datetime.now(timezone.utc).timestamp() if now is None else now
    attempts, prs, checks, malformed = [], {}, Counter(), 0
    for gap in state.all_gaps():
        events = []
        try:
            with open(state.events_path(gap)) as f:
                for line in f:
                    try:
                        events.append(json.loads(line))
                    except ValueError:
                        malformed += 1
        except OSError:
            continue
        a, p, c, m = replay(events, now)
        rec = state.load(gap)
        if a and a[-1]["outcome"] == "active" and (not rec or rec.get("state") not in ("LEASED", "RESEARCHING", "CANDIDATE_READY", "BUILDING", "SIGNED", "PUSHED")):
            a[-1]["outcome"] = "unresolved_history"
            a[-1]["slot_seconds"] = 0
        attempts.extend(a)
        prs.update(p)
        checks.update(c)
        malformed += m
    outcomes = Counter(a["outcome"] for a in attempts)
    hours = sum(a["slot_seconds"] for a in attempts) / 3600
    def median(values):
        return round(statistics.median(values), 1) if values else None
    accepted = [p for p in prs.values() if p["accepted"] is not None]
    board = leaderboard.load()
    return {
        "at": datetime.fromtimestamp(now, timezone.utc).isoformat(),
        "observed_acquisitions": len(attempts),
        "attempt_outcomes": dict(outcomes),
        "lease_slot_hours_including_active": round(hours, 3),
        "submitted_per_slot_hour": round(outcomes["submitted"] / hours, 4) if hours else None,
        "median_acquisition_to_candidate_seconds": median([a["candidate"]-a["start"] for a in attempts if a["candidate"] is not None]),
        "median_acquisition_to_submission_seconds": median([a["slot_seconds"] for a in attempts if a["outcome"]=="submitted"]),
        "unique_published_prs": len(prs),
        "observed_accepted_prs": len(accepted),
        "median_submission_to_acceptance_seconds": median([max(0,p["accepted"]-p["first"]) for p in accepted]),
        "local_check_events": dict(checks),
        "official_checked_steps": board.get("our_steps") if board.get("available") else None,
        "official_score_observed_at": board.get("observed_at"),
        "malformed_events_skipped": malformed,
        "notes": "Event history only; active durations censored; unresolved histories excluded from slot-hour denominator; repeated checks count as events, not distinct proofs. Not agent-hours or CPU-hours. Official score is authoritative."
    }


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(snapshot(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

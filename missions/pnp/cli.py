#!/usr/bin/env python3
"""Stable operator interface for the PnP contribution workflow.

    python3 missions/pnp/cli.py status
    python3 missions/pnp/cli.py acquire [--hard]
    python3 missions/pnp/cli.py beat <gap-id>
    python3 missions/pnp/cli.py release <gap-id> <reason>
    python3 missions/pnp/cli.py submit <gap-id> <candidate-file>
    python3 missions/pnp/cli.py reconcile
"""
import argparse
import contextlib
import fcntl
import json
import os
from pathlib import Path
import sys
import time

if __package__ in (None, ""):
    # Support the required direct invocation:
    #   python3 missions/pnp/cli.py <command>
    sys.path.insert(0, os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..")))
    from missions.pnp import (config, desk as desk_mod, publish,
                                reconcile, state, jobs, frontier, assignment, support)
else:
    from . import config, desk as desk_mod, publish, reconcile, state, jobs, frontier, assignment, support


def _printer(data):
    print(json.dumps(data, indent=2, sort_keys=True))


def cmd_status(args):
    d = desk_mod.Desk()
    docs = d.docs()
    desk_state = d.status()
    _printer({
        "headline": config.HEADER,
        "open_gaps": desk_state.get("open_gaps"),
        "held_now": desk_state.get("held_now"),
        "docs_bytes": len(docs),
        "leases": [{"gap": g,
                    "state": state.load(g)["state"],
                    "expires": state.load(g).get("lease_expires_at")}
                   for g in state.all_gaps()
                   if state.load(g).get("lease")],
        "gaps": [{k: state.load(g).get(k)
                  for k in ("gap_id", "state", "lease", "branch",
                            "commit_sha", "pr_number", "external_verdict")}
                 for g in state.all_gaps()],
    })


@contextlib.contextmanager
def acquisition_lock():
    os.makedirs(config.STATE_ROOT, exist_ok=True)
    fd = os.open(os.path.join(config.STATE_ROOT, "acquisition.lock"),
                 os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def held_records():
    # Signed/pushed candidates and unpublished faults still occupy a lease.
    # Submitted PRs do not; the remote desk independently enforces its cap.
    result = []
    for gid in state.all_gaps():
        rec = state.load(gid)
        if rec and rec.get("lease") and rec["state"] not in (
                "RELEASED", "STALE", "ACCEPTED", "PR_OPEN", "REJECTED"):
            if rec["state"] == "FAULT" and (rec.get("lease_expires_at") or 0) <= time.time():
                continue
            result.append(rec)
    return result


def cmd_acquire(args):
    # Manual maintenance is supported only when the allocator is absent.
    # Do not let a stale Executive instruction compete with the live broker.
    os.makedirs(config.STATE_ROOT, exist_ok=True)
    fd = os.open(os.path.join(config.STATE_ROOT, "allocator-loop.lock"),
                 os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("allocator running; use status and staff research_focus", file=sys.stderr)
            return 2
        with acquisition_lock():
            return acquire(args, desk_mod.Desk())
    finally:
        os.close(fd)


def acquire(args, d, report=True):
    """Caller holds acquisition_lock; both CLI and daemon use this path."""
    d.docs()
    held = len(held_records())
    if held >= config.MAX_LEASES:
        print("refusing to exceed the desk's %d active leases" %
              config.MAX_LEASES, file=sys.stderr)
        return 2
    answer = d._next_gap(hard=args.hard, another=args.another)
    if answer is None:
        print("no claimable gap right now; retry later", file=sys.stderr)
        return 1
    gap, lease_data = answer["gap"], answer["lease"]
    lease = lease_data.get("id") if isinstance(lease_data, dict) else lease_data
    if not isinstance(lease, str) or not lease:
        print("desk returned a malformed lease", file=sys.stderr)
        return 2
    gid = gap.get("id")
    if not isinstance(gid, str) or not config.GAP_ID_RE.match(gid):
        print("desk returned a gap id failing the grammar", file=sys.stderr)
        return 2
    if not all(isinstance(gap.get(k), str) and gap[k].strip()
               for k in ("statement", "module", "file")):
        print("desk returned incomplete assignment metadata", file=sys.stderr)
        return 2
    prior = state.load(gid)
    if prior is not None:
        # The desk granted a fresh lease for a gap we have seen before.  The
        # old behaviour released it with reason 'other', which (per live
        # join.txt) re-arms a one-hour cooldown and feeds the ten-minute step
        # rate limit.  With several workers churning acquire/release this
        # locked the whole handle out of the desk.  Adopt the fresh lease so
        # the gap can actually be worked; the event log keeps every attempt.
        if prior["state"] in ("RELEASED", "STALE"):
            rec = state.reacquire(
                gid, statement=gap.get("statement"),
                module=gap.get("module"), path=gap.get("file"),
                imports=gap.get("imports") or [],
                gap_title=gap.get("title"),
                context=gap.get("context"), dead=gap.get("dead"),
                acquisition_hard=bool(args.hard), acquisition_prs=gap.get("pr_open"),
                lease=lease, lease_obtained_at=time.time(),
                lease_expires_at=time.time() +
                config.LEASE_TTL_SECONDS)
            state.event(gid, "acquired", {"hard": bool(args.hard),
                                          "another": bool(args.another),
                                          "reacquired": True})
            if report:
                _printer({"gap": gid, "file": rec["path"],
                          "module": rec["module"], "lease": lease,
                          "reacquired": True, "headline": config.HEADER})
            return 0
        if prior.get("lease") == lease:
            # At capacity the desk may return an existing lease rather than
            # null. This is idempotent, not a spare lease or a new assignment.
            print("desk returned already recorded lease for " + gid, file=sys.stderr)
            return 1
        # Genuine duplicate: an active lease/PR already exists.  Never
        # release the spare lease with 'other'/'out_of_time': that triggers
        # the cooldown and rate limit.  Let the spare lease expire on its own.
        print("gap already has an active local lease; ignoring spare desk "
              "lease (it will expire) - never release it as 'other'",
              file=sys.stderr)
        return 1
    rec = state.create(gid, state="LEASED",
                       statement=gap.get("statement"),
                       module=gap.get("module"), path=gap.get("file"),
                       imports=gap.get("imports") or [],
                       gap_title=gap.get("title"),
                       context=gap.get("context"), dead=gap.get("dead"),
                       acquisition_hard=bool(args.hard), acquisition_prs=gap.get("pr_open"),
                       lease=lease, lease_obtained_at=time.time(),
                       lease_expires_at=time.time() +
                       config.LEASE_TTL_SECONDS)
    state.event(gid, "acquired", {"hard": bool(args.hard),
                                  "another": bool(args.another)})
    if report:
        _printer({"gap": gid, "file": rec["path"], "module": rec["module"],
                  "lease": lease, "headline": config.HEADER})
    return 0


def cmd_beat(args):
    rec = state.load(args.gap)
    if not rec or not rec.get("lease"):
        print("no lease for gap", file=sys.stderr)
        return 2
    status = desk_mod.Desk().beat(rec["lease"])
    if status == 410:
        state.transition(args.gap, "STALE",
                         failure_reason="lease returned 410")
        print("lease is gone (410); stop work on this gap", file=sys.stderr)
        return 1
    state.update(args.gap, lease_expires_at=time.time() +
                 config.LEASE_TTL_SECONDS)
    print("lease renewed")
    return 0


def cmd_release(args):
    rec = state.load(args.gap)
    if not rec or not rec.get("lease"):
        print("no lease for gap", file=sys.stderr)
        return 2
    desk_mod.Desk().release(rec["lease"], args.reason)
    state.transition(args.gap, "RELEASED", failure_reason=args.reason)
    print("released " + args.gap + " with reason " + args.reason)
    return 0


def cmd_submit(args):
    try:
        expected = None
        for path in (Path.cwd(), Path(args.candidate).resolve().parent):
            if assignment.workspace(path):
                gap, lease = assignment.resolve(args.gap, cwd=path)
                if expected is not None and expected != lease:
                    raise ValueError("candidate belongs to a different assignment")
                expected = lease
        _printer(jobs.submit(args.gap, args.candidate, expected_lease=expected))
    except (publish.StopPublish, jobs.validate.InvalidCandidate, OSError, ValueError) as exc:
        print("PUBLISH STOPPED: " + str(exc), file=sys.stderr)
        return 1
    return 0


def cmd_reconcile(args):
    _printer(reconcile.reconcile_all())
    return 0


def cmd_guard(args):
    try:
        gap, lease = assignment.resolve(args.gap, args.lease)
        result = frontier.checkpoint(gap, lease)
        if result["decision"] == "continue":
            from missions.pnp import focus
            chosen = focus.current()
            rec = state.load(gap)
            if chosen and rec and focus.key(chosen) != (gap, lease) and rec["state"] in ("LEASED","RESEARCHING") and not assignment.general():
                result = {"decision":"wait","reason":"focus switched; preserve work and finish cooperatively",
                          "research_focus":chosen["gap_id"]}
        if result["decision"] == "continue":
            # Advisory only; an unavailable evidence channel must not stop work.
            try:
                rec = state.load(gap)
                if rec and rec.get("lease") == lease:
                    advice = support.read(rec)
                    if advice:
                        result["research_advice"] = advice
                    findings = support.findings(rec)
                    if findings:
                        result["research_findings"] = findings
            except (OSError, ValueError, TypeError, KeyError):
                pass
    except (OSError, ValueError) as exc:
        result = {"decision": "wait", "reason": str(exc)}
    _printer(result)
    return 0


def cmd_assignment(args):
    try:
        _printer(assignment.prepare(args.gap, worker=getattr(args, "worker", None)))
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print("assignment unavailable: " + str(exc), file=sys.stderr)
        return 1


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pnp")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    acq = sub.add_parser("acquire")
    acq.add_argument("--hard", action="store_true")
    acq.add_argument("--another", action="store_true")
    acq.set_defaults(fn=cmd_acquire)
    beat = sub.add_parser("beat")
    beat.add_argument("gap")
    beat.set_defaults(fn=cmd_beat)
    rel = sub.add_parser("release")
    rel.add_argument("gap")
    rel.add_argument("reason")
    rel.set_defaults(fn=cmd_release)
    subp = sub.add_parser("submit")
    subp.add_argument("gap")
    subp.add_argument("candidate")
    subp.set_defaults(fn=cmd_submit)
    guard = sub.add_parser("guard")
    guard.add_argument("gap", nargs="?")
    guard.add_argument("--lease")
    guard.set_defaults(fn=cmd_guard)
    bind = sub.add_parser("assignment")
    bind.add_argument("gap")
    bind.add_argument("--worker", help="distinct parallel research workspace label")
    bind.set_defaults(fn=cmd_assignment)
    sub.add_parser("reconcile").set_defaults(fn=cmd_reconcile)
    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())

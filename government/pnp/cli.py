#!/usr/bin/env python3
"""Stable operator interface for the PnP contribution workflow.

    python3 government/pnp/cli.py status
    python3 government/pnp/cli.py acquire [--hard]
    python3 government/pnp/cli.py beat <gap-id>
    python3 government/pnp/cli.py release <gap-id> <reason>
    python3 government/pnp/cli.py submit <gap-id> <candidate-file>
    python3 government/pnp/cli.py reconcile
"""
import argparse
import json
import os
import sys
import time

if __package__ in (None, ""):
    # Support the required direct invocation:
    #   python3 government/pnp/cli.py <command>
    sys.path.insert(0, os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..")))
    from government.pnp import (config, desk as desk_mod, publish,
                                reconcile, state)
else:
    from . import config, desk as desk_mod, publish, reconcile, state


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


def cmd_acquire(args):
    d = desk_mod.Desk()
    d.docs(refresh=True)                       # live rules on startup
    held = sum(1 for g in state.all_gaps()
               if state.load(g).get("lease") and
               state.load(g)["state"] not in
               ("RELEASED", "STALE", "ACCEPTED"))
    if held >= config.MAX_LEASES:
        print("refusing to exceed the desk's %d active leases" %
              config.MAX_LEASES, file=sys.stderr)
        return 2
    answer = d.next_gap(hard=args.hard, another=args.another)
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
    if state.load(gid) is not None:
        # A new desk lease was already granted; release it instead of leaving
        # an orphan lease that other contributors cannot use.
        try:
            d.release(lease, "other")
        except Exception as exc:
            print("duplicate claim could not be released: %s" % exc,
                  file=sys.stderr)
        print("gap already has local state; not duplicating", file=sys.stderr)
        return 1
    rec = state.create(gid, state="DISCOVERED",
                       statement=gap.get("statement"),
                       module=gap.get("module"), path=gap.get("file"),
                       imports=gap.get("imports") or [],
                       gap_title=gap.get("title"),
                       context=gap.get("context"), dead=gap.get("dead"),
                       lease=lease, lease_obtained_at=time.time(),
                       lease_expires_at=time.time() +
                       config.LEASE_TTL_SECONDS)
    state.transition(gid, "LEASED")
    state.event(gid, "acquired", {"hard": bool(args.hard),
                                  "another": bool(args.another)})
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
    # The research worker supplies only a candidate file, never a Git
    # history.  Move a leased gap to publication-ready deterministically.
    rec = state.load(args.gap)
    if not rec:
        print("gap must be acquired by Viche before submission", file=sys.stderr)
        return 2
    if rec["state"] == "LEASED":
        state.transition(args.gap, "RESEARCHING")
        rec = state.load(args.gap)
    if rec["state"] == "RESEARCHING":
        state.transition(args.gap, "CANDIDATE_READY")
    try:
        result = publish.publish(args.gap, args.candidate)
    except publish.StopPublish as e:
        print("PUBLISH STOPPED: " + str(e), file=sys.stderr)
        return 1
    _printer(result)
    return 0


def cmd_reconcile(args):
    _printer(reconcile.reconcile_all())
    return 0


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
    sub.add_parser("reconcile").set_defaults(fn=cmd_reconcile)
    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())

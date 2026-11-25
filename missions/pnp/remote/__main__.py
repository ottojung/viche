"""Prepare/inspect an offline remote-build bundle from a bound research lease.

There is no network transport or compiler worker enabled by this command.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess

from .. import assignment, config, focus, state, support
from . import protocol
from .spool import Spool


def live_binding(cwd):
    bound = assignment.binding(cwd)
    if not bound:
        raise ValueError("use the bound research workspace")
    rec = state.load(bound[0])
    if not rec or rec["lease"] != bound[1] or not focus.eligible(rec):
        raise ValueError("obsolete assignment")
    return rec


def prepare(cwd, file, wall, memory):
    rec = live_binding(cwd)
    work = assignment.workspace(cwd)[1].resolve()
    path = (cwd / file).resolve()
    if not path.is_relative_to(work) or not path.is_file():
        raise ValueError("source must be an existing file inside this workspace")
    with path.open("rb") as f:
        source = f.read(config.MAX_FILE_BYTES + 1)
    if len(source) > config.MAX_FILE_BYTES:
        raise ValueError("source too large")
    base = subprocess.check_output(["git","-C",str(work),"rev-parse","HEAD"],
                                   text=True, timeout=10).strip()
    toolchain = (work/"lean"/"lean-toolchain").read_text().strip()
    gap = {"id":rec["gap_id"],"file":rec["path"],"module":rec["module"],
           "statement":rec["statement"],"imports":rec.get("imports") or []}
    job = protocol.make(gap,source,base,toolchain,support.attempt(rec),wall,memory)
    latest = live_binding(cwd)
    if support.attempt(latest) != job["attempt"]:
        raise ValueError("assignment changed during packaging")
    return job


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    pack = sub.add_parser("pack",help="Stage validated private bundle; does not send or run")
    pack.add_argument("file",type=Path)
    pack.add_argument("--wall",type=int,default=600)
    pack.add_argument("--rss-mib",type=int,default=8192)
    inspect = sub.add_parser("poll",help="Read local result only, bound to current assignment")
    inspect.add_argument("job")
    cancel = sub.add_parser("cancel",help="Cancel local spool job for current assignment")
    cancel.add_argument("job")
    args = p.parse_args()
    try:
        cwd = Path.cwd()
        root = Path(config.STATE_ROOT)/"remote-build-private"
        spool = Spool(root)
        if args.cmd == "pack":
            job = prepare(cwd,args.file,args.wall,args.rss_mib)
            ident = spool.submit(protocol.canonical(job))
            print(json.dumps({"job":ident,"state":"staged_local_only",
                              "transport_available":False}))
        else:
            rec = live_binding(cwd)
            raw = spool.read(args.job,"request")
            if raw is None:
                raise ValueError("unknown job")
            job,_ = protocol.request(raw,{"attempt":support.attempt(rec)})
            if job["job"] != args.job or job["gap"]["id"] != rec["gap_id"]:
                raise ValueError("job not bound to current assignment")
            if args.cmd == "cancel":
                spool.cancel(args.job)
                print(json.dumps({"job":args.job,"cancelled_local":True}))
            else:
                print(json.dumps(spool.poll(args.job),ensure_ascii=False))
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        p.error(str(exc))

if __name__ == "__main__":
    main()

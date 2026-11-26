"""Work-conserving desk broker. Never starts or stops research agents."""
import json
import os
import re
from pathlib import Path
import sys
import time
from types import SimpleNamespace

from . import assignment, cli, competition, config, desk, fastlane, frontier, focus, state, status, portfolio, support, posting

POLL_SECONDS = 30
NULL_RETRY_SECONDS = 120  # the fast lane clears this backoff whenever it frees a slot


def memory_path():
    return os.path.join(config.STATE_ROOT, "allocator.json")


def read_memory():
    try:
        with open(memory_path(), encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    return {}


def bound_roster():
    """Use immutable workspace bindings, not mutable agent titles."""
    roster = status.workers()
    if roster["coverage"] != "complete":
        return None
    bindings = set()
    uncertain = set()
    for agent in roster["agents"]:
        cwd = agent.get("cwd")
        if not cwd:
            return None
        path = Path(cwd)
        bound = assignment.binding(path)
        if bound:
            bindings.add(bound)
        elif (workspace := assignment.workspace(path)):
            uncertain.add(workspace[0])
        elif (match := re.search(r"\bL-[a-z0-9]+(?:-[a-z0-9]+)+\b", agent.get("title") or "")):
            # A researcher temporarily outside its bound cwd is not proof
            # of abandonment. Only protect; never use a title as ownership.
            uncertain.add(match.group(0))
    # A detached experiment (SAT, Lean or another process) can outlive
    # its researcher. Protect every same-UID live process in a bound cwd.
    try:
        for p in Path("/proc").iterdir():
            if not p.name.isdigit():
                continue
            try:
                if p.stat().st_uid != os.getuid():
                    continue
                cwd = (p / "cwd").resolve(strict=True)
                bound = assignment.binding(cwd)
                if bound:
                    bindings.add(bound)
                elif (workspace := assignment.workspace(cwd)):
                    uncertain.add(workspace[0])
            except FileNotFoundError:
                continue
            except PermissionError:
                continue  # unrelated system processes
            except OSError:
                return None
    except OSError:
        return None
    return bindings, uncertain


def fill(d, mem, now, snapshot):
    """Reserve most capacity for posting-time solid work, never for late stock.

    A positive fresh frontier can wake an ordinary probe, but server-supplied
    retry_after_s always wins. At most one expensive open research lease.
    """
    from .lbcert import ready
    acquired=[]
    ordinary=snapshot.get("ordinary")
    previous=mem.get("posting_ordinary")
    mem["posting_ordinary"]=ordinary
    if type(ordinary) is int and ordinary>0 and previous==0:
        mem.pop("posting_retry_at",None)
    if desk.retry_until()>time.time():
        return acquired
    with cli.acquisition_lock():
        for _ in range(desk.lease_limit()):
            held=cli.held_records()
            if len(held)>=desk.lease_limit() or desk.retry_until()>time.time():
                break
            # A research lease is optional. Only the high-value open lane is
            # probed, and only if the fresh public status confirms opportunity.
            research=any(support.active(r,now) and r.get("work_lane")!="posting" for r in held)
            rows=snapshot.get("gaps",{})
            high=any(row.get("level")=="open" and type(row.get("points")) is int
                     and row["points"]>=posting.MIN_RESEARCH_POINTS
                     and type(row.get("held")) is int and type(row.get("parallel")) is int
                     and row["held"]<row["parallel"] for row in rows.values())
            open_probe=(not research and high and desk.lease_limit()>1 and len(held)==desk.lease_limit()-1
                        and now-mem.get("last_open_probe",0)>=300)
            if open_probe:
                level,lane="open","research"
                mem["last_open_probe"]=now
            else:
                level,lane="solid","posting"
                if now < mem.get("posting_retry_at",0):
                    # When no solid work is offered, checked *uncontested*
                    # stock is the only permitted targeted fallback.
                    target=competition.fallback_target(ready.offers(snapshot,mem,now,uncontested=True),mem,now) if snapshot.get("complete") else None
                    if not target:
                        break
                    mem["proof_of_attempts"][target]=now
                    before={r["gap_id"] for r in held}
                    result=cli.acquire(SimpleNamespace(hard=False,another=bool(held),
                                        proof_of=target,work_lane="posting"),d,report=False)
                    new={r["gap_id"] for r in cli.held_records()}-before
                    if result==0 and new:
                        acquired.extend(sorted(new))
                        for gid in sorted(new):posting.launch(gid)
                    # Only one fallback probe per tick.
                    break
            before={r["gap_id"] for r in held}
            result=cli.acquire(SimpleNamespace(hard=level=="open",another=bool(held),
                                level=level,work_lane=lane),d,report=False)
            new={r["gap_id"] for r in cli.held_records()}-before
            if result==0 and new:
                acquired.extend(sorted(new))
                if lane=="posting":
                    for gid in sorted(new):posting.launch(gid)
                mem.pop("posting_retry_at",None)
                continue
            if result==2 or desk.retry_until()>time.time():
                break
            if level=="solid":
                mem["posting_retry_at"]=now+NULL_RETRY_SECONDS
                break
            # No high-value open offer: try solid next, not another hard unit.
    return acquired


def proof_of_now(gid, d=None, now=None):
    """No asynchronous stock event may take capacity from the fresh broker."""
    from .lbcert import ready
    if not ready.verified(gid):
        return "no receipt"
    if any(r["gap_id"]==gid for r in cli.held_records()):
        rec=state.load(gid)
        if rec.get("work_lane")=="posting":
            posting.launch(gid)
        else:
            fastlane.submit_ready(gid)
        return "already held"
    return "retained for uncontested allocator fallback"


def posting_tick(d=None, now=None):
    """Cheap single-writer path: no remote catalog, roster or model calls."""
    d=d or desk.Desk()
    now=time.time() if now is None else now
    mem=read_memory()
    try:
        snap=frontier.load(now)
        released=posting.maintain(d,mem,now,snap,cli.held_records())
        if released:
            # No extra backoff after a successful release; shared desk pacing
            # and the server's retry_after_s still constrain every request.
            mem.pop("posting_retry_at",None)
        acquired=fill(d,mem,now,snap)
        selected=focus.choose([state.load(g) for g in state.all_gaps()],mem.get("focus"),(),time.time())
        mem["focus"]=list(focus.key(selected)) if selected else None
        mem["posting_at"]=time.time()
        return {"released":released,"acquired":acquired,"held":len(cli.held_records()),
                "focus":selected["gap_id"] if selected else None}
    finally:
        state.atomic_write(memory_path(),json.dumps(mem,sort_keys=True)+"\n")


def tick(d=None, now=None):
    d = d or desk.Desk()
    now = time.time() if now is None else now
    mem = read_memory()
    mem.pop("parked", None)
    mem.pop("observations", None)
    mem["observed_at"] = now
    try:
        roster = bound_roster()
        portfolio.apply_switch(mem, now)
        released = portfolio.apply_release(d, mem, now)
        # Make a focus decision visible before potentially slow desk I/O.
        selected = focus.choose([state.load(g) for g in state.all_gaps()], mem.get("focus"), roster[0] if roster else (), time.time())
        mem["focus"] = list(focus.key(selected)) if selected else None
        state.atomic_write(memory_path(), json.dumps(mem, sort_keys=True)+"\n")
        if released:
            print("released by evaluator", released, flush=True)
        # Renew due leases every tick (30 s cadence): the separate heartbeat loop sleeps 7 min,
        # longer than half the desk's 10-minute lease.  _heartbeat only calls the desk when due.
        try:
            from . import reconcile
            for rec in cli.held_records():
                reconcile._heartbeat(rec["gap_id"], rec, d)
        except Exception as exc:
            print("allocator heartbeat deferred:", type(exc).__name__, str(exc)[:200], flush=True)
        # Read the cheap snapshot ourselves, independent of slow Executive.
        try:
            snapshot = frontier.refresh()
        except Exception as exc:
            snapshot = {}
            print("allocator frontier unavailable:", exc, flush=True)
        # Fast lane: submit ready certificates, settle false twins, keep two slots cycling.
        try:
            lane = fastlane.tick(d, mem, now, roster_known=roster is not None, cycle_research=False)
            if any(lane.values()):
                print("fastlane", json.dumps(lane), flush=True)
                released = list(released) + lane["released"]
        except Exception as exc:
            print("fastlane deferred:", type(exc).__name__, str(exc)[:300], flush=True)
        # The cheap loop fills every five seconds; on this maintenance pass
        # use its freshly observed frontier and do not wait for the next tick.
        released = list(released) + posting.maintain(d,mem,now,snapshot,cli.held_records())
        acquired = fill(d, mem, now, snapshot)
        if acquired:
            print("new assignments:", acquired, flush=True)
        records = cli.held_records()
        selected = focus.choose([state.load(g) for g in state.all_gaps()], mem.get("focus"), roster[0] if roster else (), now)
        mem["focus"] = list(focus.key(selected)) if selected else None
        return {"released": released, "acquired": acquired,
                "held": len(records), "focus": selected["gap_id"] if selected else None}
    finally:
        state.atomic_write(memory_path(), json.dumps(mem, sort_keys=True)+"\n")


if __name__ == "__main__":
    try:
        print(json.dumps(posting_tick() if "--posting" in sys.argv[1:] else tick()), flush=True)
    except Exception as exc:
        print("allocator tick deferred:", exc, file=sys.stderr, flush=True)
        sys.exit(1)

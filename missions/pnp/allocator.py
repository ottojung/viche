"""Work-conserving desk broker. Never starts or stops research agents."""
import json
import os
import re
from pathlib import Path
import sys
import time
from types import SimpleNamespace

from . import assignment, cli, competition, config, desk, fastlane, frontier, focus, state, status, portfolio, support, posting, freshness, ledger, surge

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


def roster_path():
    return os.path.join(config.STATE_ROOT, "cache", "allocator-roster.json")


def observe():
    """Only read remote observations; never claim, release, submit or staff."""
    try:
        snapshot=frontier.refresh()
        from . import posting_kind
        posting_kind.observe(snapshot)
    except Exception as exc:
        print("allocator frontier unavailable:", type(exc).__name__, flush=True)
    at=time.time()
    roster=bound_roster()
    payload={"at":at,"complete":roster is not None,
             "bindings":sorted(roster[0]) if roster else [],
             "uncertain":sorted(roster[1]) if roster else []}
    state.atomic_write(roster_path(),json.dumps(payload)+"\n")
    try:
        from . import promotion_observer
        promotion_observer.observe()
    except Exception as exc:
        print("private competition observation deferred:",type(exc).__name__,flush=True)
    return {"complete":payload["complete"]}


def observed_roster(now=None):
    now=time.time() if now is None else now
    try:
        with open(roster_path(),encoding="utf-8") as f:
            d=json.load(f)
        if d.get("complete") is not True or not 0<=now-d["at"]<=45:
            return None
        bindings=d["bindings"]; uncertain=d["uncertain"]
        if not isinstance(bindings,list) or not isinstance(uncertain,list):
            return None
        if any(not isinstance(b,list) or len(b)!=2 or
               not all(isinstance(x,str) for x in b) for b in bindings):
            return None
        if any(not isinstance(g,str) for g in uncertain):
            return None
        return set(map(tuple,bindings)),set(uncertain)
    except (OSError,ValueError,TypeError,KeyError):
        return None


def ready_attempt(gid,d,mem,now,held,reason):
    """Called with acquisition lock. Exact receipt + broker-side lease recording."""
    from .lbcert import ready
    if (not ready.verified(gid) or desk.retry_until(gid)>time.time()
            or len(held)>=desk.lease_limit()):
        return None
    before={r["gap_id"] for r in held}
    if gid in before:
        return None
    # Separate event-path throttle from allocator memory; multiple generators
    # can finish one gap concurrently. A single writer owns this file.
    marker=Path(config.STATE_ROOT,"lbcert","target-attempts",gid+".json")
    try:
        old=json.loads(marker.read_text())
        if 0<=now-old["at"]<30:
            return None
    except (OSError,ValueError,KeyError,TypeError):
        pass
    state.atomic_write(str(marker),json.dumps({"at":now,"reason":reason}))
    mem.setdefault("proof_of_attempts",{})[gid]=now
    try:
        result=cli.acquire(SimpleNamespace(hard=False,another=bool(held),
                           proof_of=gid,work_lane="posting"),d,report=False)
    except desk.DeskError as e:
        ledger.mark("proof_of_attempt",gid,result="error",reason=reason)
        return None
    new={r["gap_id"] for r in cli.held_records()}-before
    ledger.mark("proof_of_attempt",gid,result=result,reason=reason)
    if result==0 and gid in new:
        # The returned exact statement is independently checked by jobs.submit.
        # Publish now rather than spawn a generator that already has a proof.
        try:
            if not fastlane.submit_ready(gid):posting.launch(gid)
        except Exception:posting.launch(gid)
        return gid
    # If desk unexpectedly gave a different valid assignment, don't drop it.
    for other in new:
        posting.launch(other)
    return None


def fresh_targets(snapshot,now,seen):
    from .lbcert import ready
    counts=ready.competition(now)
    rows=snapshot.get("gaps",{})
    result=[]
    for gid,t in seen.items():
        if counts.get(gid,0)>0 or not freshness.available(gid,snapshot,t):
            continue
        r=state.load(gid)
        if r and (r.get("pr_number") or r["state"] not in ("RELEASED","STALE")):
            continue
        if desk.retry_until(gid)>now:
            continue
        if freshness.fresh(gid,ready.verified(gid),seen,now):
            result.append(gid)
    return sorted(result,key=lambda g:(-(rows.get(g,{}).get("points") or 0),-seen[g],g))


def fill(d, mem, now, snapshot):
    """Hybrid: fresh checked proofs first, ordinary posting lanes second.

    Outside a productive surge, verified stock with a direct zero-rival
    observation precedes arbitrary ordinary work. During a productive surge
    it remains a quiet/backoff fallback. A short reservation leaves capacity
    for new arrivals while their exact
    checks are running. Never exceed earned capacity or server pacing.
    """
    from .lbcert import ready
    acquired=[]
    seen=freshness.recent(now)
    batch=surge.update(snapshot,seen,now)
    # Existing leases continue through heartbeat/portfolio; no new hybrid
    # claims while the executive has paused the generator.
    if posting.paused():
        return acquired
    ordinary=snapshot.get("ordinary")
    quiet_empty=frontier.quiet(snapshot,now)
    offerable=snapshot.get("offerable")
    quiet_open=quiet_empty and type(offerable) is int and offerable>0
    previous=mem.get("posting_ordinary")
    mem["posting_ordinary"]=ordinary
    if type(ordinary) is int and ordinary>0 and (previous==0 or (batch and type(previous) is int and previous<100<=ordinary)):
        mem.pop("posting_retry_at",None)
    if desk.retry_until()>time.time():
        return acquired
    urgent=fresh_targets(snapshot,now,seen)
    # Network reads for older stock happen before, not inside, the claim lock.
    old_target=None
    # A large ordinary frontier does not make random acquisitions useful.
    # Prefer one already checked, independently uncontested candidate outside
    # a productive burst. This is the existing proof-of path, not a new claim
    # mode; no unchecked stock may enter it.
    stock_priority=(not batch or surge.recovery(now)) and frontier.ordinary_count(snapshot,now) is not None
    if (not urgent and (stock_priority or quiet_empty or now<mem.get("posting_retry_at",0))
            and snapshot.get("complete") and len(cli.held_records())<desk.lease_limit()):
        old_target=competition.fallback_target(ready.offers(snapshot,mem,now,uncontested=True),mem,now)
    with cli.acquisition_lock():
        for _ in range(desk.lease_limit()):
            held=cli.held_records()
            if len(held)>=desk.lease_limit() or desk.retry_until()>time.time():
                break
            if urgent:
                gid=urgent.pop(0)
                result=ready_attempt(gid,d,mem,now,held,"fresh")
                if result:
                    acquired.append(result)
                    continue
                if desk.retry_until()>time.time():break
                # One targeted miss per tick; ordinary can use remaining
                # capacity, but never spin against a server cooldown.
            rows=snapshot.get("gaps",{})
            high=any(row.get("level")=="open" and type(row.get("points")) is int
                     and row["points"]>=posting.MIN_RESEARCH_POINTS
                     and type(row.get("held")) is int and type(row.get("parallel")) is int
                     and row["held"]<row["parallel"] for row in rows.values())
            levels=snapshot.get("offerable_levels")
            hard_fallback=(quiet_open and isinstance(levels,dict)
                           and not levels.get("open") and type(levels.get("hard")) is int and levels["hard"]>0)
            # A bounded high-value probe may use a genuinely spare slot even
            # while another lease is live research. The desk advertises these
            # units far above a random solid posting lease; this neither
            # preempts the research lease nor fills an already full pool.
            open_probe=(not batch and (high or hard_fallback)
                        and desk.lease_limit()>1 and (len(held)==desk.lease_limit()-1 or quiet_open)
                        and now-mem.get("last_open_probe",0)>=300)
            # Reserve only when genuinely new units are still being solved.
            # A due open probe is the deliberate use of that reserved slot.
            reserve=bool(seen and any(freshness.available(g,snapshot,seen[g])
                       and not state.load(g) and not ready.verified(g)
                       for g in seen))
            if not batch and reserve and not open_probe and desk.lease_limit()>1 and len(held)>=desk.lease_limit()-1:
                break
            if stock_priority and old_target:
                gid,old_target=old_target,None
                result=ready_attempt(gid,d,mem,now,held,"checked_stock")
                if result:
                    acquired.append(result)
                    continue
                if desk.retry_until()>time.time():break
            if open_probe:
                level,lane=("hard" if hard_fallback else "open"),"research"
                mem["last_open_probe"]=now
            else:
                level,lane="solid","posting"
                if quiet_empty or now < mem.get("posting_retry_at",0):
                    if old_target:
                        result=ready_attempt(old_target,d,mem,now,held,"checked_stock")
                        if result:acquired.append(result)
                    break
            before={r["gap_id"] for r in held}
            from . import posting_kind
            kind=posting_kind.choose(mem,snapshot,now) if lane=="posting" else None
            result=cli.acquire(SimpleNamespace(hard=level in ("open","hard"),another=bool(held),
                                level=level,work_lane=lane,kind=kind),d,report=False)
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
    return acquired


def proof_of_now(gid, d=None, now=None):
    """Immediate event path for freshly seen, exactly checked proofs."""
    if posting.paused():
        return "paused"
    from .lbcert import ready
    now=time.time() if now is None else now
    receipt=ready.verified(gid)
    if not receipt:return "no receipt"
    if any(r["gap_id"]==gid for r in cli.held_records()):
        fastlane.submit_ready(gid)
        return "already held"
    seen=freshness.recent(now)
    if not freshness.fresh(gid,receipt,seen,now):
        return "retained for uncontested allocator fallback"
    snap=frontier.load(now)
    if ready.competition(now).get(gid,0)>0 or not freshness.available(gid,snap,seen[gid]):
        return "known contested or unavailable"
    d=d or desk.Desk()
    if desk.retry_until(gid)>time.time():return "desk backoff"
    with cli.acquisition_lock():
        held=cli.held_records()
        if any(r["gap_id"]==gid for r in held):
            fastlane.submit_ready(gid)
            return "already held"
        if len(held)>=desk.lease_limit():
            # Never preempt young, focused or concrete work for a race.
            chosen=focus.current()
            candidates=[r for r in held if support.active(r,now)
                and r.get("work_lane")!="posting" and not fastlane.concrete(r)
                and not r.get("candidate_digest") and not r.get("queued_lease")
                and not r.get("intent") and not r.get("pr_number")
                and now-(r.get("lease_obtained_at") or now)>=posting.HARD_MIN_SECONDS
                and posting.points(r,snap) is not None and posting.points(r,snap)<posting.MIN_RESEARCH_POINTS
                and not (chosen and focus.key(chosen)==focus.key(r))]
            candidates.sort(key=lambda r:r.get("lease_obtained_at") or now)
            if not candidates:return "no free slot"
            r=candidates[0]
            if not fastlane.release(d,{},r["gap_id"],"out_of_time",
                    "fresh exact checked proof "+gid,expected_lease=r["lease"]):
                return "no free slot"
            held=cli.held_records()
        result=ready_attempt(gid,d,{},now,held,"fresh_event")
        return "acquired" if result else "deferred"


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
        from .lbcert import promotion
        for event in promotion.promote_once():
            print("private receipt",json.dumps(event),flush=True)
        acquired=fill(d,mem,now,snap)
        roster=observed_roster()
        selected=focus.choose([state.load(g) for g in state.all_gaps()],mem.get("focus"),roster[0] if roster else (),time.time())
        mem["focus"]=list(focus.key(selected)) if selected else None
        mem["posting_at"]=time.time()
        return {"released":released,"acquired":acquired,"held":len(cli.held_records()),
                "focus":selected["gap_id"] if selected else None}
    finally:
        state.atomic_write(memory_path(),json.dumps(mem,sort_keys=True)+"\n")


def tick(d=None, now=None, cached=False):
    d = d or desk.Desk()
    now = time.time() if now is None else now
    mem = read_memory()
    mem.pop("parked", None)
    mem.pop("observations", None)
    mem["observed_at"] = now
    try:
        roster = observed_roster(now) if cached else bound_roster()
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
            snapshot = frontier.load(now) if cached else frontier.refresh()
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
        if released:
            mem.pop("posting_retry_at",None)
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
        print(json.dumps(observe() if "--observe" in sys.argv[1:] else posting_tick() if "--posting" in sys.argv[1:] else tick(cached="--cached" in sys.argv[1:])), flush=True)
    except Exception as exc:
        print("allocator tick deferred:", exc, file=sys.stderr, flush=True)
        sys.exit(1)

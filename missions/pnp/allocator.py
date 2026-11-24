"""Work-conserving desk broker. Never starts or stops research agents."""
import json
import os
import re
from pathlib import Path
import sys
import time
from types import SimpleNamespace

from . import assignment, cli, config, desk, frontier, focus, jobs, state, status

POLL_SECONDS = 30
NULL_RETRY_SECONDS = 120
ABANDONED_GRACE = 5 * 60
HARD_MIN_AGE = 20 * 60


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


def abandonable(rec, now, absent, staffed):
    if rec["state"] not in ("LEASED", "RESEARCHING") or rec.get("queued_lease"):
        return False
    if rec.get("intent") and rec["intent"].get("what") != "allocator_release":
        return False
    acquired = rec.get("lease_obtained_at")
    if not isinstance(acquired, (int, float)):
        return False
    # A never-staffed reserve is intentional, not abandoned.
    return staffed and now - acquired >= HARD_MIN_AGE and now - absent >= ABANDONED_GRACE


def release_abandoned(rec, d, now, absent, staffed):
    gap, lease = rec["gap_id"], rec["lease"]
    # Exclude a publisher or a candidate being queued concurrently.
    fd = jobs.claim(gap)
    if fd is None:
        return False
    try:
        with state.lock(gap):
            latest = state.load(gap)
            if not latest or latest.get("lease") != lease or not abandonable(latest, now, absent, staffed):
                return False
            roster = bound_roster()
            if roster is None or (gap, lease) in roster[0] or gap in roster[1]:
                return False
            latest["intent"] = {"what": "allocator_release", "payload": {"lease": lease, "reason": "other"}}
            state.save(latest)
            d.release(lease, "other")
            latest.update(state="RELEASED", failure_reason="other", intent=None)
            state.save(latest)
            state.event(gap, "state", {"to": "RELEASED", "fields": {"failure_reason": "other", "allocator": True}})
            return True
    finally:
        os.close(fd)


def retire(d, mem, now, roster):
    if roster is None:
        # An observation failure cannot count towards an absence.
        for old in mem.get("observations", {}).values():
            old.pop("absent_since", None)
        return []
    bound, uncertain = roster
    observations = mem.setdefault("observations", {})
    next_obs = {}
    released = []
    for rec in cli.held_records():
        gap, lease = rec["gap_id"], rec["lease"]
        if rec["state"] not in ("LEASED", "RESEARCHING"):
            continue
        old = observations.get(gap, {})
        if old.get("lease") != lease:
            old = {"lease": lease}
        if (gap, lease) in bound:
            next_obs[gap] = {"lease": lease, "staffed": True}
            continue
        if gap in uncertain:
            next_obs[gap] = {"lease": lease, "staffed": bool(old.get("staffed"))}
            continue
        absent = old.get("absent_since", now)
        staffed = bool(old.get("staffed"))
        next_obs[gap] = {"lease": lease, "absent_since": absent, "staffed": staffed}
        if abandonable(rec, now, absent, staffed):
            try:
                if release_abandoned(rec, d, now, absent, staffed):
                    released.append(gap)
                    next_obs.pop(gap, None)
            except Exception as exc:
                print("abandoned release deferred:", gap, exc, flush=True)
    mem["observations"] = next_obs
    return released


def fill(d, mem, now, snapshot):
    """Ordinary first, hard fallback, only documented allocator requests."""
    ordinary = snapshot.get("ordinary")
    total = snapshot.get("offerable")
    revision = snapshot.get("source_updated_at")
    hard_count = total - ordinary if type(total) is int and type(ordinary) is int else None
    # Status is advisory; even a snapshot saying zero cannot suppress the
    # periodic probe forever. A new positive ordinary signal can wake us early.
    old_ordinary = mem.get("ordinary")
    old_hard = mem.get("hard_count")
    mem["ordinary"] = ordinary
    mem["hard_count"] = hard_count
    signals = {False: ordinary, True: hard_count}
    previous = {False: old_ordinary, True: old_hard}
    acquired = []
    with cli.acquisition_lock():
        while len(cli.held_records()) < config.MAX_LEASES:
            held = len(cli.held_records())
            for hard in (False, True):
                key = "last_null_hard" if hard else "last_null_ordinary"
                signal_key = "last_signal_hard" if hard else "last_signal_ordinary"
                count = signals[hard]
                early = (type(count) is int and count > 0 and
                         (previous[hard] in (None, 0) or
                          (revision and mem.get(signal_key) != revision)))
                if not early and now - mem.get(key, 0) < NULL_RETRY_SECONDS:
                    continue
                # A positive hard count is not proof of eligibility, and a
                # negative one may be stale. Probe both modes periodically.
                before = {r["gap_id"] for r in cli.held_records()}
                if revision:
                    mem[signal_key] = revision
                previous[hard] = count
                result = cli.acquire(SimpleNamespace(hard=hard, another=bool(held)), d, report=False)
                after = {r["gap_id"] for r in cli.held_records()}
                if result == 0 and after - before:
                    acquired.extend(sorted(after - before))
                    mem.pop(key, None)
                    break
                mem[key] = now
                if result == 2:
                    return acquired
            else:
                break
    return acquired


def tick(d=None, now=None):
    d = d or desk.Desk()
    now = time.time() if now is None else now
    mem = read_memory()
    # A daemon restart or long sampling outage is not evidence of absence.
    if now - mem.get("observed_at", 0) > POLL_SECONDS * 3:
        for old in mem.get("observations", {}).values():
            old.pop("absent_since", None)
    mem["observed_at"] = now
    try:
        roster = bound_roster()
        released = retire(d, mem, now, roster)
        if released:
            print("released abandoned", released, flush=True)
        # Read the cheap snapshot ourselves, independent of slow Executive.
        try:
            snapshot = frontier.refresh()
        except Exception as exc:
            snapshot = {}
            print("allocator frontier unavailable:", exc, flush=True)
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
        print(json.dumps(tick()), flush=True)
    except Exception as exc:
        print("allocator tick deferred:", exc, file=sys.stderr, flush=True)
        sys.exit(1)

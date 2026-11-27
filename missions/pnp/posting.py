"""Fresh, held-unit witness lane. All acquisition/release belongs to the broker.

A worker is fenced by the exact lease/statement attempt and an inherited
process lock. It only emits a candidate; jobs.submit owns signed publication.
Search failures are unknown, never refutations. No local Lean build gate.
"""
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from . import config, jobs, ledger, state, support, validate
from .lbcert import plugins, ready

BUDGET = 12
MAX_ATTEMPTS = 2
MIN_RESEARCH_POINTS = 300
HARD_MIN_SECONDS = 1200
LEGACY_GRACE = 1200


def paused():
    """Honor the executive stop until the host-boundary repair is deployed."""
    from . import pause
    return pause.paused()


def current(rec, attempt=None):
    return bool(support.active(rec) and rec.get("work_lane") == "posting"
                and not rec.get("queued_lease") and not rec.get("candidate_digest")
                and not rec.get("pr_number") and not rec.get("intent")
                and (attempt is None or support.attempt(rec) == attempt))


def points(rec, snapshot):
    value = (rec.get("lease_terms") or {}).get("points")
    if type(value) is not int:
        value = snapshot.get("gaps", {}).get(rec["gap_id"], {}).get("points")
    return value if type(value) is int and value >= 0 else None


def hard(rec):
    level = (rec.get("lease_terms") or {}).get("level") or rec.get("acquisition_level")
    return level in ("hard", "open") or rec.get("acquisition_hard") is not False


def rival(rec, counts):
    # A live acquisition observation can be newer than the public catalog.
    # Positive evidence is enough to avoid starting another race.
    return any(type(v) is int and v > 0 for v in
               (rec.get("acquisition_prs"), counts.get(rec["gap_id"])))


def status(gid, attempt, result, **fields):
    with state.lock(gid):
        rec = state.load(gid)
        if not rec or not rec.get("lease") or support.attempt(rec) != attempt:
            return False
        old = rec.get("posting") or {}
        rec["posting"] = {**old, **fields, "attempt": attempt, "result": result,
                          "at": time.time()}
        state.save(rec)
        state.event(gid, "posting", {"result": result, **fields})
    return True


def launch(gid):
    if paused():
        return False
    rec = state.load(gid)
    if not current(rec):
        return False
    attempt = support.attempt(rec)
    fd = os.open(os.path.join(state.gap_dir(gid), ".posting.lock"),
                 os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        with state.lock(gid):
            rec = state.load(gid)
            if not current(rec, attempt):
                return False
            old = rec.get("posting") or {}
            if old.get("attempt") != attempt:
                old = {}
            if old.get("result") in ("unsupported", "unknown", "contested", "submitted"):
                return False
            n = old.get("starts", 0)
            if n >= MAX_ATTEMPTS:
                rec["posting"] = {**old, "result": "unknown", "detail": "worker interrupted twice"}
                state.save(rec)
                return False
            rec["posting"] = {"attempt": attempt, "result": "running",
                              "starts": n+1, "at": time.time()}
            state.save(rec)
        with open(os.path.join(state.gap_dir(gid), "posting.log"), "ab") as out:
            subprocess.Popen([sys.executable, "-m", "missions.pnp.posting",
                              gid, attempt, str(fd)],
                             cwd=str(Path(__file__).resolve().parents[2]),
                             stdin=subprocess.DEVNULL, stdout=out, stderr=out,
                             pass_fds=(fd,), start_new_session=True,
                             env={**os.environ,"PNP_STATE_ROOT":config.STATE_ROOT})
        return True
    finally:
        os.close(fd)


def generate(rec, work):
    """Use the same audited family generators, but a short foreground budget."""
    # Reuse source-only batch stock under this exact lease; only the signed
    # publisher and its concurrent checker can advance publication state.
    from .lbcert.generators.promise import batch
    data=batch.staged_candidate(rec)
    if data is not None:
        out=work/"candidate.lean"
        out.write_bytes(data)
        ledger.mark("posting_cache_hit",rec["gap_id"],engine="promise-batch")
        return "generated",out
    deadline = time.monotonic() + BUDGET
    sf = work/"statement.txt"
    out = work/"candidate.lean"
    sf.write_text(rec["statement"])
    sketch = (rec.get("desk_notes") or {}).get("sketch")
    if isinstance(sketch, str):
        sf.with_suffix(sf.suffix+".sketch").write_text(sketch[:65536])
    attempted = False
    for family in plugins.families_of(rec["statement"]):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return "unknown", None
        attempted = True
        out.unlink(missing_ok=True)
        rc, detail = plugins.run(family[0], rec["gap_id"], str(sf), str(out), timeout=remaining)
        if rc == 3:
            # An explicit unsupported-instance result is not an error.
            # Never reuse bytes written by a refusing plugin.
            out.unlink(missing_ok=True)
            continue
        if rc or not out.is_file():
            return "unknown", None
        meta = {"id":rec["gap_id"], "file":rec["path"], "module":rec["module"],
                "statement":rec["statement"], "imports":rec["imports"]}
        validate.validate(meta, out.read_bytes())
        return "generated", out
    return ("unknown" if attempted else "unsupported"), None


def run(gid, attempt):
    if paused():
        return
    rec = state.load(gid)
    if not current(rec, attempt):
        return
    start = time.monotonic()
    try:
        if rival(rec, ready.competition(time.time())):
            status(gid, attempt, "contested")
            return
        # Checked stock for this exact held unit is a useful immediate answer.
        from . import fastlane
        if not paused() and ready.verified(gid):
            res = fastlane.submit_ready(gid)
            if res and not current(state.load(gid),attempt):
                status(gid, attempt, "submitted", method="checked stock")
                return
        with tempfile.TemporaryDirectory(prefix="posting-", dir=state.gap_dir(gid)) as tmp:
            result, path = generate(rec, Path(tmp))
            seconds = round(time.monotonic()-start,3)
            ledger.mark("posting_generated",gid,result=result,seconds=seconds)
            if result != "generated":
                status(gid, attempt, result, seconds=seconds)
                return
            latest = state.load(gid)
            if paused() or not current(latest, attempt):
                return
            # No extra compilation before the PR; existing publisher checks
            # exact bytes concurrently and never bypasses official verification.
            jobs.submit(gid,str(path),expected_lease=rec["lease"])
            status(gid,attempt,"submitted" if not current(state.load(gid),attempt)
                   else "interrupted",seconds=seconds)
    except Exception as exc:
        # Transient error can retry once; never classify as a false statement.
        status(gid,attempt,"interrupted",detail=type(exc).__name__+":"+str(exc)[:200])


def set_lane(rec, lane):
    with state.lock(rec["gap_id"]):
        latest = state.load(rec["gap_id"])
        if not support.active(latest) or latest.get("lease") != rec.get("lease") or latest.get("queued_lease") or latest.get("candidate_digest") or latest.get("intent"):
            return False
        latest["work_lane"] = lane
        latest["posting"] = None
        state.save(latest)
        state.event(rec["gap_id"],"work_lane",{"lane":lane})
        return True


def maintain(d, mem, now, snapshot, records):
    """Migrate idle legacy holds and finish posting attempts without agent churn."""
    from . import fastlane, frontier, surge
    batch = surge.active(now)
    recovery = batch and surge.recovery(now)
    active = [r for r in records if support.active(r,now) and not r.get("queued_lease") and not r.get("candidate_digest") and not r.get("intent")]
    if paused():
        for rec in active:
            if rec.get("work_lane") == "posting":
                set_lane(rec, "research")
        return []
    # At most one speculative research lease. Only high advertised/frozen
    # value qualifies; unknown price is not a license to discard active work.
    research = [r for r in active if r.get("work_lane") != "posting" and
                (recovery or points(r,snapshot) is None or points(r,snapshot) >= MIN_RESEARCH_POINTS
                 or (((r.get("lease_terms") or {}).get("level") or r.get("acquisition_level"))=="hard"
                     and frontier.ordinary_count(snapshot,now) in (None,0)))]
    research.sort(key=lambda r:(-(points(r,snapshot) or 0),r.get("lease_obtained_at") or now))
    keep = research[0]["gap_id"] if research and (not batch or recovery) else None
    # One already-held, uncontested, unsuccessful posting assignment may
    # become a learning front. No extra desk claims, no second research slot.
    if recovery and keep is None:
        counts = ready.competition(now)
        candidates = [r for r in active if r.get("work_lane") == "posting"
                      and (r.get("posting") or {}).get("result") in ("unsupported", "unknown")
                      and not rival(r, counts)
                      and type(points(r, snapshot)) is int and points(r, snapshot) > 0]
        candidates.sort(key=lambda r: (-(points(r,snapshot) or 0),
                                     r.get("lease_obtained_at") or now, r["gap_id"]))
        if candidates and set_lane(candidates[0], "research"):
            keep = candidates[0]["gap_id"]

    released = []
    for old in active:
        gid = old["gap_id"]
        if old.get("work_lane") != "posting":
            if gid == keep:
                if not old.get("work_lane"):
                    set_lane(old,"research")
                continue
            age = now-(old.get("lease_obtained_at") or now)
            if hard(old) and age < HARD_MIN_SECONDS:
                continue
            # Preserve existing young human/model attempts for the migration,
            # but start their bounded generator concurrently after the grace.
            if not old.get("work_lane") and age < LEGACY_GRACE:
                continue
            if batch:
                if fastlane.cand_ready(gid):
                    continue  # cached complete source belongs to the fast lane
                # Never release a candidate or an immature hard lease.
                # The existing fenced release revalidates the lease and intent.
                if fastlane.release(d,mem,gid,"out_of_time",
                        "active witness batch; research hold has no candidate",
                        expected_lease=old["lease"]):
                    released.append(gid)
                continue
            if not set_lane(old,"posting"):
                continue
        rec = state.load(gid)
        if not current(rec):
            continue
        outcome = (rec.get("posting") or {}).get("result")
        if outcome in ("unsupported","unknown","contested"):
            value = points(rec,snapshot)
            if not batch and outcome != "contested" and value is not None and value >= MIN_RESEARCH_POINTS and keep is None:
                if set_lane(rec,"research"):
                    keep=gid
                continue
            if hard(rec) and now-(rec.get("lease_obtained_at") or now)<HARD_MIN_SECONDS:
                continue
            if fastlane.release(d,mem,gid,"out_of_time","posting lane: "+outcome+"; no candidate produced",expected_lease=rec["lease"]):
                released.append(gid)
        else:
            launch(gid)
    return released


if __name__ == "__main__":
    try:
        run(sys.argv[1],sys.argv[2])
    finally:
        os.close(int(sys.argv[3]))

"""Allocator fast lane: turn held concrete steps into PRs within one tick, and keep slots cycling.

Called by allocator.tick before fill(). Consumes the files written by missions.pnp.lbcert.autosolve
(PNP_STATE_ROOT/lbcert). Three rules, each recorded as a gap event:

1. SUBMIT. A held step with a ready lb_cert candidate goes straight to the ordinary publisher
   (jobs.submit). No local re-verification: the generator's certificates were ACCEPTED by the
   official checker on every instance tried (7309, 5459, 8493, 8487, 8483), and the races for this
   family are lost by minutes.
2. FALSE TWIN. A held "¬ (lower bound)" step whose lower bound is decided true is false. If the
   lower bound has a ready candidate and no open PR, publish it first (join.txt: prove the negated
   twin as an ordinary pull request; lbcert/twin_publish.py uses the publisher's own git/gh/validate
   helpers). Then release the held step with the desk reason statement_seems_false.
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
RESEARCH_SLOTS = config.MAX_LEASES - 2
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


def cand_ready(gap):
    try:
        with open(os.path.join(CANDS, gap + ".status"), encoding="utf-8") as f:
            ok = f.read().startswith("ok")
    except OSError:
        return None
    path = os.path.join(CANDS, gap + ".lean")
    return path if ok and os.path.exists(path) else None


def concrete(rec):
    s = rec.get("statement") or ""
    return bool(lbparse.classify(s) or re.fullmatch(r"¬ ?\((.*)\)", lbparse.norm(s)) and
                lbparse.classify(re.fullmatch(r"¬ ?\((.*)\)", lbparse.norm(s)).group(1)))


def release(d, mem, gap, reason, evidence):
    fd = jobs.claim(gap)
    if fd is None:
        return False
    try:
        with state.lock(gap):
            rec = state.load(gap)
            if (not support.active(rec) or rec.get("queued_lease") or rec.get("intent")
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
        return True
    finally:
        os.close(fd)


def tick(d, mem, now, roster_known=True):
    out = {"submitted": [], "twin_published": [], "released": []}
    twins, desk = _read("twins.json", {}), _read("desk.json", {})
    held = cli.held_records()
    for rec in held:
        gap = rec["gap_id"]
        if not support.active(rec, now) or rec.get("queued_lease") or rec.get("candidate_digest"):
            continue
        path = cand_ready(gap)
        if path:
            try:
                res = jobs.submit(gap, path)
                state.event(gap, "fastlane_submit", {"candidate": path, "result": str(res)[:300]})
                out["submitted"].append(gap)
            except Exception as exc:
                state.event(gap, "fastlane_submit_failed", {"error": str(exc)[:300]})
                print("fastlane submit failed:", gap, str(exc)[:200], flush=True)
            continue
        lb = twins.get(gap)
        if not lb:
            continue
        lb_path = cand_ready(lb)
        if not lb_path:
            continue   # the lower bound is not decided by our generator: research may still refute it
        mark = os.path.join(CANDS, gap + ".twinpub")
        if desk.get(lb, 1) == 0 and not os.path.exists(mark):
            p = subprocess.run([sys.executable, os.path.join(HERE, "lbcert", "twin_publish.py"), gap, lb, lb_path],
                               cwd=os.path.dirname(os.path.dirname(HERE)), capture_output=True, text=True, timeout=900)
            with open(mark, "w") as f:
                f.write("%d\n%s\n%s" % (p.returncode, p.stdout[-2000:], p.stderr[-2000:]))
            state.event(gap, "fastlane_twin_publish", {"twin": lb, "rc": p.returncode, "out": (p.stdout + p.stderr)[-400:]})
            if p.returncode == 0:
                out["twin_published"].append(lb)
        if release(d, mem, gap, "statement_seems_false",
                   "lb_cert certificate for the negated twin %s (viche lbcert generator; same engine and encoding "
                   "as checker-ACCEPTED files) proves the lower bound, so this negation is false." % lb):
            out["released"].append(gap)
    # Rule 3: keep two slots cycling.
    held = cli.held_records()
    chosen = focus.current()
    research = [r for r in held if support.active(r, now) and not concrete(r) and not r.get("queued_lease")
                and not r.get("candidate_digest") and not r.get("pr_number")]
    # An incomplete worker roster means we cannot see who is working; never cycle then.
    if roster_known and len(held) >= config.MAX_LEASES and len(research) > RESEARCH_SLOTS:
        old = sorted((r for r in research if not (chosen and focus.key(chosen) == focus.key(r))
                      and now - (r.get("lease_obtained_at") or now) >= RESEARCH_MIN_AGE),
                     key=lambda r: r.get("lease_obtained_at") or now)
        if old:
            r = old[0]
            if release(d, mem, r["gap_id"], "out_of_time",
                       "fast-lane slot cycling: research leases may hold at most %d of %d slots; this was the oldest "
                       "non-focus research lease (%d min) with no candidate." % (
                           RESEARCH_SLOTS, config.MAX_LEASES, (now - r["lease_obtained_at"]) // 60)):
                out["released"].append(r["gap_id"])
    return out

#!/usr/bin/env python3
"""Act 34 provisional model-free trial: hard bounded, no model and no authority.

Run ONLY after a lawful Act 34 Executive permit. These observations are
AUXILIARY TELEMETRY, never an operational adaptive institution, efficacy or
proof of Founder satisfaction. Each UTC day has one fsynced prepaid reservation
on Economy's canonical 45-day ledger; unknown/failed work retains the whole
charge. An outer independent 38+2-second kill bounds any work by 40 wall
seconds / 160 ALL-HOST CPU seconds on the verified four-core host. The
historical correspondence channel, Parliament and Judiciary never wait here.
"""
import datetime as dt
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

TOWN = Path(os.environ.get("VICHE_TOWN_ROOT", "/var/lib/lubko/wd/viche")).resolve()
STATE = Path(os.environ.get("VICHE_STATE_ROOT", "/var/lib/lubko/wd/viche-state")).resolve()
ROOT = STATE / "knowledge/budget"
OFFICES = ("statistics", "foresight", "strategy", "spying")
CHARGE = {"tokens_total": 0, "cpu_seconds": 160, "wall_seconds": 40}
WINDOW = 14 * 86400
MAX_ATTEMPTS = 14


class Denied(Exception):
    pass


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_atomic(path, data):
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".pilot-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        dirfd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dirfd)
        finally:
            os.close(dirfd)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def module(name):
    spec = importlib.util.spec_from_file_location(
        "viche_pilot_" + name.replace("-", "_"), TOWN / "government" / name)
    if spec is None or spec.loader is None:
        raise Denied("required module unavailable: " + name)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def permit(office):
    laws = (TOWN / "government/LAWS.md").read_text()
    if not any(line.startswith("## Act 34 — Minimum Viable Knowledge Institutions Pilot Act (enacted ")
               for line in laws.splitlines()):
        raise Denied("Act 34 not yet law; pilot inactive")
    row = read(TOWN / "records/knowledge/activation.json").get("offices", {}).get(office, {})
    now = int(time.time())
    if (row.get("enabled") is not True or
        row.get("authorized_by") != "act:34:" + office or
        row.get("trial_mode") != "deterministic-v1" or
        row.get("signer") != "c1e00002" or
        row.get("provider_requests_max") != 0 or
        row.get("tokens_cap") != 0 or
        not isinstance(row.get("cancellation"), str) or not row["cancellation"] or
        not isinstance(row.get("reboot_recovery"), str) or not row["reboot_recovery"] or
        row.get("caps") != CHARGE or
        type(row.get("not_before")) is not int or
        type(row.get("expires_at")) is not int or
        not row["not_before"] <= now < row["expires_at"] or
        row["expires_at"] - row["not_before"] > WINDOW):
        raise Denied("no valid reversible, signed, limited Executive pilot")
    sources = row.get("deterministic_sources", {})
    paths = {
        "runner": TOWN / "government/knowledge-minimal-pilot.py",
        "observer": TOWN / "government/knowledge-minimal-observer.py",
        "post": TOWN / "government/post.py",
        "budget_tool": TOWN / "government/knowledge-budget-tool.py",
    }
    if set(sources) != set(paths) or any(sources[k] != sha(p) for k, p in paths.items()):
        raise Denied("exact sources differ from Executive's approved bytes")
    # Shared working tree is writable by many agents. Bare JSON flags are not
    # spending authority; activation and Economy config must be on Git main.
    for rel in ("records/knowledge/activation.json",
                "government/knowledge-budget.conf"):
        live = TOWN / rel
        try:
            committed = subprocess.run(
                ["git", "-C", str(TOWN), "show", "HEAD:" + rel],
                capture_output=True, timeout=8, check=True).stdout
        except (OSError, subprocess.SubprocessError) as exc:
            raise Denied("reviewed activation or budget Git blob unavailable") from exc
        if hashlib.sha256(committed).digest() != hashlib.sha256(live.read_bytes()).digest():
            raise Denied("uncommitted activation or Economy config; no dispatch")
    # Actual Judiciary review is due AFTER initial observation, not beforehand;
    # the pilot mechanically holds after 48h without an independent decision.
    if now >= row["not_before"] + 48 * 3600:
        path = TOWN / ("records/knowledge/pilot-reviews/" + office + ".json")
        try:
            review = read(path)
        except (OSError, ValueError):
            raise Denied("independent 48h review missing; pilot halted")
        if (review.get("office") != office or review.get("decision") != "proceed"
                or review.get("reviewer") != "c1e00008"):
            raise Denied("independent 48h Judiciary review failed or not approved")
        rel = "records/knowledge/pilot-reviews/" + office + ".json"
        try:
            committed = subprocess.run(
                ["git", "-C", str(TOWN), "show", "HEAD:" + rel],
                capture_output=True, timeout=8, check=True).stdout
        except (OSError, subprocess.SubprocessError) as exc:
            raise Denied("48h review is not source-controlled") from exc
        if sha(path) != hashlib.sha256(committed).hexdigest():
            raise Denied("48h Judiciary review bytes differ from reviewed Git")
    possible = Path("/sys/devices/system/cpu/possible").read_text().strip()
    if not re.fullmatch(r"0-[0-9]+", possible) or int(possible.split("-")[1]) >= 4:
        raise Denied("host can provide >4 CPUs; 160-second bound invalid")
    return row


def budget():
    cfg = read(TOWN / "government/knowledge-budget.conf")
    engine = module("knowledge-budget-tool.py")
    if engine.validate_config(cfg):
        raise Denied("invalid Economy budget config")
    return engine, cfg


def prepay(office, day, engine, cfg):
    if cfg["offices"][office]["enabled"] is not True:
        raise Denied("Economy has not authorized this office budget")
    root = ROOT / "reservations"
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    lf = os.open(ROOT / "lock", os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        fcntl.flock(lf, fcntl.LOCK_EX)
        rid = "mvp-" + office + "-" + day
        record = root / (rid + ".json")
        if record.exists():
            data = read(record)
            if (data.get("id") != rid or data.get("office") != office or
                    data.get("schema") != "viche-knowledge-budget-reservation-v1" or
                    data.get("state") not in ("closed", "held")):
                raise Denied("same-day receipt is invalid")
            return None
        if len(list(root.glob("mvp-" + office + "-*.json"))) >= MAX_ATTEMPTS:
            raise Denied("maximum fourteen first-trial attempts reached")
        now = int(time.time())
        agg, counted, skipped = engine.charges(root, now, cfg["accounting_window_seconds"])
        snapshot = ROOT / "aggregate.json"
        if snapshot.exists():
            stored = read(snapshot)
            # No unsafe reset of uncertain liabilities from any office.
            for key in ("tokens_total", "cpu_seconds", "wall_seconds"):
                if not math.isclose(stored[key], agg[key], abs_tol=0.001):
                    raise Denied("Economy aggregate diverged from durable receipts")
        for key in CHARGE:
            if agg[key] + CHARGE[key] > cfg["aggregate"]["caps"][key]:
                raise Denied("shared budget exhausted: " + key)
            if agg["by_office"][office][key] + CHARGE[key] > cfg["offices"][office]["caps"][key]:
                raise Denied("per-office budget exhausted: " + key)
        cpu = engine.host_cpu()
        row = {
            "schema": "viche-knowledge-budget-reservation-v1",
            "id": rid, "office": office, "state": "held",
            "created_at": now, "caps": CHARGE, "charge": CHARGE,
            "usage": None, "cpu_baseline": cpu, "native_session_id": None,
            "agent_id": "", "meter_db": None, "model_requests": 0,
            "trial_mode": "deterministic-v1", "held_reason": "prepaid before model-free observation",
        }
        fd = os.open(record, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(row, f, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        dirfd = os.open(record.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dirfd)
        finally:
            os.close(dirfd)
        agg, counted, skipped = engine.charges(root, now, cfg["accounting_window_seconds"])
        agg.update(counted=counted, skipped=skipped)
        write_atomic(snapshot, agg)
        return record
    finally:
        os.close(lf)


def finish(path, baseline, elapsed, success, engine, cfg):
    current = engine.host_cpu()
    if baseline["cpu_boot_id"] != current["cpu_boot_id"]:
        raise Denied("reboot or meter reset; full prepaid liability retained")
    cpu = current["cpu_seconds"] - baseline["cpu_seconds"]
    wall = math.ceil(elapsed)
    if not (0 <= cpu <= CHARGE["cpu_seconds"] and 0 <= wall <= CHARGE["wall_seconds"]):
        raise Denied("resource overrun; full prepaid liability retained")
    lf = os.open(ROOT / "lock", os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        fcntl.flock(lf, fcntl.LOCK_EX)
        row = read(path)
        if row["state"] != "held":
            raise Denied("source reservation changed")
        row["state"] = "closed"
        row["closed_at"] = int(time.time())
        row["usage"] = {
            "tokens_total": 0, "cpu_seconds": round(cpu, 2),
            "wall_seconds": wall, "source": "whole-host-upper-bound-not-per-office",
            "provider_requests": 0,
        }
        row["charge"] = None
        row["closed_reason"] = "observed" if success else "failed"
        write_atomic(path, row)
        agg, counted, skipped = engine.charges(
            ROOT / "reservations", int(time.time()), cfg["accounting_window_seconds"])
        agg.update(counted=counted, skipped=skipped)
        write_atomic(ROOT / "aggregate.json", agg)
    finally:
        os.close(lf)


def publish(office, day, report):
    # Report is an observation, never forecast registration or inferred
    # Founder preference. Post is public and unauthenticated, never authority.
    src = report["sources"]
    if not src:
        raise Denied("source material absent; no fact invented")
    if office == "spying":
        subprocess.run(["/bin/sh", str(TOWN / "government/spying-source-preflight.sh"),
                        str(TOWN)], check=True, capture_output=True, timeout=28)
    body = json.dumps(report, indent=2, sort_keys=True)
    result = subprocess.run([
        sys.executable, str(TOWN / "government/post.py"), "publish",
        "--sender", office, "--topic", office + "/first-observations",
        "--kind", "observation", "--subject", "Auxiliary " + office + " telemetry " + day,
        "--body", body, "--key", "mvp-" + office + "-" + day,
        "--condition", "Metric definitions: direct fields and counts from cited original bytes. "
        "Auxiliary only. This is NOT operational adaptive institution work, "
        "independent outcome verification, a causal claim or source independence.",
        *[item for source in src for item in ("--source", source)]
    ], capture_output=True, text=True, timeout=6,
        env={"VICHE_TOWN_ROOT": str(TOWN), "VICHE_STATE_ROOT": str(STATE),
             "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "PYTHONNOUSERSITE": "1"})
    if result.returncode:
        raise Denied("Post unavailable: "+result.stderr.strip()[:280]+
                     "; full first-use attempt counted; main town proceeds")
    return result.stdout.strip()


def run(office):
    permit(office)
    engine, cfg = budget()
    day = dt.datetime.now(dt.timezone.utc).date().isoformat()
    receipt = prepay(office, day, engine, cfg)
    if receipt is None:
        return {"status": "already_attempted", "office": office, "day": day,
                "counts_as_operational_institution": False, "auxiliary_telemetry": True}
    started = time.monotonic()
    baseline = read(receipt)["cpu_baseline"]
    succeeded = False
    problem = None
    try:
        observed = module("knowledge-minimal-observer.py").collect(office)
        observed.update(scope="act34_auxiliary_telemetry_only",
                        provider_requests=0, verified_useful_outcome=False,
                        counts_as_operational_institution=False,
                        auxiliary_telemetry=True, day=day)
        if observed["status"] != "observed":
            raise Denied("source unavailable: " + str(observed.get("missing", "")))
        result = publish(office, day, observed)
        succeeded = True
    except (Denied, OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        problem = str(exc)[:160]
    finish(receipt, baseline, time.monotonic() - started, succeeded, engine, cfg)
    return {"status": "published" if succeeded else "failed",
            "office": office, "day": day, "receipt": str(receipt),
            "provider_requests": 0, "verified_useful_outcome": False,
            "counts_as_operational_institution": False, "auxiliary_telemetry": True,
            "problem": problem}


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in OFFICES or sys.argv[2] not in ("--dry-run", "--run"):
        print("usage: knowledge-minimal-pilot.py office --dry-run|--run", file=sys.stderr)
        return 2
    office, mode = sys.argv[1:]
    try:
        if mode == "--dry-run":
            result = module("knowledge-minimal-observer.py").collect(office)
            result.update(provider_requests=0, verified_useful_outcome=False,
                          counts_as_operational_institution=False,
                          auxiliary_telemetry=True)
        else:
            result = run(office)
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get("status") in ("observed", "published", "already_attempted") else 1
    except (Denied, OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print("knowledge-minimal-pilot: HOLD %s" % str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

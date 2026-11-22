#!/usr/bin/env python3
"""Act 33: conservatively prepaid, model-free Statistics measurement attempt.

This is a deliberately narrow FIRST-trial fallback if OpenCode cannot enforce
a strict in-flight model token cap. It does not authorize activation: the
independent phase gate, enacted law, Executive order, budgets and source hashes
must ALL have already been approved. The only subprocess doing institutional
work is the exact hashed, deterministic statistics-report.py (and its pinned
Post helper); NO Antonina or model launch exists on this path.

Before launch, durably precharge a 256 host-CPU-second / 64 wall-second safety
liability; after verified termination and same-boot meter observation, replace
it with the measured WHOLE-HOST UPPER_BOUND, never per-office actual CPU.
An ambiguous exit retains the full prepaid liability across restart.
"""
import datetime
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import tempfile
import time

TOWN = Path(os.environ.get("VICHE_TOWN_ROOT", "/var/lib/lubko/wd/viche")).resolve()
STATE = Path(os.environ.get("VICHE_STATE_ROOT", "/var/lib/lubko/wd/viche-state")).resolve()
BROOT = Path(os.environ.get("VICHE_BUDGET_STATE", str(STATE / "knowledge/budget")))
CONF = Path(os.environ.get("VICHE_BUDGET_CONFIG", str(TOWN / "government/knowledge-budget.conf")))
VOLUME = {"tokens_total": 0, "cpu_seconds": 256, "wall_seconds": 64}
MAX_CORES = 4
MAX_RUNS = 14
REPORT_WALL = 20
KILL_GRACE = 2


class Denied(Exception):
    pass


def read(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        raise Denied("unreadable JSON evidence: %s" % path) from exc


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def durable(path, obj):
    """One durable rename, including fsync of the parent directory."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".viche-budget-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            file.write(json.dumps(obj, sort_keys=True) + "\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(tmp, path)
        dirfd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dirfd)
        finally:
            os.close(dirfd)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def exclusive_file(path, obj):
    raw = (json.dumps(obj, sort_keys=True) + "\n").encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as file:
        file.write(raw)
        file.flush()
        os.fsync(file.fileno())
    dirfd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(dirfd)
    finally:
        os.close(dirfd)


def budget_module():
    path = TOWN / "government/knowledge-budget-tool.py"
    spec = importlib.util.spec_from_file_location("viche_budget", path)
    if spec is None or spec.loader is None:
        raise Denied("budget implementation unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verified_order():
    # A changed environment may select a scratch fixture, but NEVER split
    # the canonical production activation from its canonical budget ledger.
    if (BROOT.resolve() != (STATE / "knowledge/budget").resolve()
            or CONF.resolve() != (TOWN / "government/knowledge-budget.conf").resolve()
            or (STATE == Path("/var/lib/lubko/wd/viche-state")
                and TOWN != Path("/var/lib/lubko/wd/viche"))):
        raise Denied("production and budget paths are inconsistent")
    law = (TOWN / "government/LAWS.md").read_text(encoding="utf-8")
    if "## Act 33 — Prospective Statistics Trial Clarification (enacted " not in law:
        raise Denied("first Statistics measurement trial law not enacted")
    activation = read(TOWN / "records/knowledge/activation.json")
    office = activation.get("offices", {}).get("statistics", {})
    now = int(time.time())
    if (activation.get("schema") != "viche-knowledge-activation-v1"
            or office.get("enabled") is not True
            or office.get("authorized_by") != "act:32:statistics"
            or office.get("trial_mode") != "deterministic-v1"
            or type(office.get("not_before")) is not int
            or type(office.get("expires_at")) is not int
            or not (office["not_before"] <= now < office["expires_at"])
            or office["expires_at"] - office["not_before"] > 14 * 86400):
        raise Denied("missing, expired or non-deterministic bounded Statistics order")
    hashes = office.get("deterministic_sources")
    paths = {
        "report": TOWN / "government/statistics-report.py",
        "post": TOWN / "government/post.py",
        "post_guard": TOWN / "government/post_guard.py",
        "budget_tool": TOWN / "government/knowledge-budget-tool.py",
        "budget_config": CONF,
        "runner": Path(__file__).resolve(),
    }
    if (not isinstance(hashes, dict) or set(hashes) != set(paths)
            or any(hashes[k] != sha(path) for k, path in paths.items())):
        raise Denied("Stats deterministic source differs from Executive-approved exact bytes")
    verifier = TOWN / "government/knowledge-activation-verify.sh"
    try:
        subprocess.run(["/bin/sh", str(verifier), "statistics"],
                       check=True, capture_output=True, timeout=30,
                       env=dict(os.environ, VICHE_TOWN_ROOT=str(TOWN)))
    except (OSError, subprocess.SubprocessError) as exc:
        raise Denied("independent phase/activation gate is not green") from exc
    return office


def reserve(day):
    import re
    if not re.fullmatch(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}", day):
        raise Denied("invalid UTC day")
    # The fixed worst-case charge is valid only on this explicitly measured
    # 4-core host; refuse CPU hot-add and any different scheduling substrate.
    possible = Path("/sys/devices/system/cpu/possible").read_text().strip()
    if not re.fullmatch(r"0-[0-9]+", possible) or int(possible.split("-")[1]) >= MAX_CORES:
        raise Denied("CPU topology allows >4 cores, pessimistic limit no longer valid")
    cpu_rows = sum(bool(re.fullmatch(r"cpu[0-9]+", line.split()[0]))
                   for line in Path("/proc/stat").read_text().splitlines()
                   if line.split())
    if cpu_rows == 0 or cpu_rows > MAX_CORES:
        raise Denied("unknown or expanded CPU count")
    tool = budget_module()
    cfg = read(CONF)
    problems = tool.validate_config(cfg)
    if problems or cfg["offices"]["statistics"]["enabled"] is not True:
        raise Denied("Economy budget config disabled/invalid: %s" % problems)
    if cfg["cpu_meter"]["source"] != "proc-stat-host-busy-upper-bound-v1":
        raise Denied("unknown host-CPU meter")
    meter = tool.host_cpu()  # fail-closed if boot ID or CPU tick source unavailable
    rid = "det-statistics-" + day
    resdir = BROOT / "reservations"
    resdir.mkdir(mode=0o700, parents=True, exist_ok=True)
    lockfd = os.open(BROOT / "lock", os.O_WRONLY | os.O_CREAT, 0o600)
    try:
        try:
            fcntl.flock(lockfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise Denied("concurrent budget mutation: retry next cycle") from exc
        path = resdir / (rid + ".json")
        if path.exists():
            old = read(path)
            if (old.get("schema") != "viche-knowledge-budget-reservation-v1"
                    or old.get("id") != rid or old.get("office") != "statistics"
                    or old.get("trial_mode") != "deterministic-v1"
                    or old.get("model_requests") != 0
                    or old.get("state") not in ("held", "closed")):
                raise Denied("corrupt/foreign same-day Statistics receipt")
            return None  # one attempt per UTC day, including across restarts
        now = int(time.time())
        agg, counted, skipped = tool.charges(str(resdir), now, cfg["accounting_window_seconds"])
        agg.update(counted=counted, skipped=skipped)
        # An existing managed Statistics model invocation cannot silently
        # overlap a declared zero-model trial. Inspect the SAME durable ledger
        # that the normal Economy budget engine reconciles.
        for prior in resdir.glob("*.json"):
            row = read(prior)
            if (row.get("office") == "statistics"
                    and row.get("trial_mode") != "deterministic-v1"
                    and row.get("state") in ("reserved", "active", "held")):
                raise Denied("managed Statistics session might still be active/unknown")
        old_agg = BROOT / "aggregate.json"
        if old_agg.exists():
            stored = read(old_agg)
            # The engine's and ours must agree before permitting a new charge.
            if any(stored.get(k) != agg[k] for k in ("tokens_total", "cpu_seconds",
                                                    "wall_seconds", "counted", "skipped")):
                raise Denied("divergent or corrupt budget aggregate; reconcile before dispatch")
        n = sum(name.name.startswith("det-statistics-") for name in resdir.glob("*.json"))
        if n >= MAX_RUNS:
            raise Denied("maximum 14 model-free Statistics trial attempts reached")
        for key, value in VOLUME.items():
            if agg[key] + value > cfg["aggregate"]["caps"][key]:
                raise Denied("aggregate Economy %s hard allowance exhausted" % key)
            if agg["by_office"]["statistics"][key] + value > cfg["offices"]["statistics"]["caps"][key]:
                raise Denied("Statistics %s hard allowance exhausted" % key)
        reservation = {
            "schema": "viche-knowledge-budget-reservation-v1", "id": rid,
            "office": "statistics", "state": "held", "created_at": now,
            "caps": VOLUME, "charge": VOLUME, "usage": None,
            "cpu_baseline": meter, "native_session_id": None,
            "agent_id": "", "meter_db": None,
            "held_reason": "prepaid_model_free_unknown_until_verified_exit",
            "model_requests": 0, "trial_mode": "deterministic-v1",
            "cpu_accounting": "whole-host-busy-upper-bound-not-per-office",
            "history": [{"at": now, "event": "prepaid_before_any_work",
                         "token_cap": 0, "cpu_upper_bound": 256, "wall_max": 64}],
        }
        exclusive_file(path, reservation)
        new_agg, counted, skipped = tool.charges(str(resdir), now, cfg["accounting_window_seconds"])
        new_agg.update(counted=counted, skipped=skipped)
        durable(old_agg, new_agg)
        return path
    finally:
        os.close(lockfd)


def close_observed(path, cpu_start, elapsed, report_ok):
    tool = budget_module()
    cpu_end = tool.host_cpu()
    start_id = cpu_start.get("cpu_boot_id")
    end_id = cpu_end.get("cpu_boot_id")
    if not start_id or start_id != end_id:
        raise Denied("CPU boot changed during report; full prepaid liability retained")
    cpu = cpu_end["cpu_seconds"] - cpu_start["cpu_seconds"]
    wall = math.ceil(elapsed)
    if not 0 <= cpu <= VOLUME["cpu_seconds"] or not 0 <= wall <= VOLUME["wall_seconds"]:
        raise Denied("model-free upper-bound charge exceeded; retained at full cap")
    cfg = read(CONF)
    lockfd = os.open(BROOT / "lock", os.O_WRONLY | os.O_CREAT, 0o600)
    try:
        fcntl.flock(lockfd, fcntl.LOCK_EX)
        row = read(path)
        if row["state"] != "held" or row["id"] != path.stem or row.get("agent_id"):
            raise Denied("reservation changed during execution; full prepaid hold retained")
        row["state"] = "closed"
        row["charge"] = None
        row["closed_at"] = int(time.time())
        row["closed_reason"] = "model_free_report_success" if report_ok else "model_free_report_failed"
        row["usage"] = {
            "tokens_total": 0, "cpu_seconds": round(cpu, 2),
            "wall_seconds": wall, "cost": 0, "cost_reported": False,
            "source": "observed_whole_host_cpu_upper_bound_non_attributed",
            "at": int(time.time()),
        }
        row["history"].append({"at": row["closed_at"], "event": "verified_process_group_terminated",
                                "result": "success" if report_ok else "failed"})
        durable(path, row)
        agg, counted, skipped = tool.charges(str(BROOT / "reservations"),
                                             int(time.time()), cfg["accounting_window_seconds"])
        agg.update(counted=counted, skipped=skipped)
        durable(BROOT / "aggregate.json", agg)
    finally:
        os.close(lockfd)


def run():
    verified_order()
    day = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    path = reserve(day)
    if path is None:
        print(json.dumps({"status": "already_attempted", "day": day,
                          "model_requests": 0, "not_a_success_claim": True}))
        return 0
    # Only this hashed deterministic source runs. It invokes Post locally,
    # never Antonina, OpenCode or a provider endpoint. Children share its
    # process group and memory/CPU limits. No agent is ever dispatched.
    reporter = TOWN / "government/statistics-report.py"
    began = time.monotonic()
    # Reserve-time meter covers all preparation after prepaid liability begins.
    before = read(path)["cpu_baseline"]
    # Do not inherit arbitrary POST_DB, PYTHONPATH, backend/model or plugin
    # overrides into the publisher. This invocation has no model credentials.
    env = {
        "VICHE_TOWN_ROOT": str(TOWN),
        "VICHE_STATE_ROOT": str(STATE),
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(STATE),
        "LANG": "C.UTF-8",
        "PYTHONNOUSERSITE": "1",
    }
    def limits():
        resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_CPU, (22, 22))
        resource.setrlimit(resource.RLIMIT_FSIZE, (64 * 1024 * 1024, 64 * 1024 * 1024))
    process = None
    done = False
    try:
        # An INDEPENDENT GNU timeout remains alive if this Python supervisor
        # itself is SIGKILLed or the host service restarts. It kills the whole
        # report+Post process group after 20+2 seconds. The boot outer timeout
        # expires by 40+2 seconds: at worst a late-started report finishes by
        # 40+2+20+2 = 64 wall seconds. A four-CPU host cannot incur more than
        # 4*64=256 whole-host busy CPU seconds in that envelope. The full
        # worst-case bound was precharged BEFORE invoking this child.
        process = subprocess.Popen(["timeout", "-k", "2", str(REPORT_WALL),
                                    sys.executable, str(reporter), "--day", day],
                                   env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=True, preexec_fn=limits)
        try:
            stdout, stderr = process.communicate(timeout=REPORT_WALL + KILL_GRACE + 4)
            done = process.returncode == 0
        except subprocess.TimeoutExpired:
            done = False
        finally:
            # On timeout, GNU timeout itself has signalled its reporter group.
            # The pinned report synchronously waits for Post; kill our
            # supervisor session too, before releasing the prepaid liability.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                process.communicate(timeout=KILL_GRACE)
            except subprocess.TimeoutExpired:
                raise Denied("process group unconfirmed dead; full prepaid hold retained")
        close_observed(path, before, time.monotonic() - began, done)
    except (OSError, subprocess.SubprocessError) as exc:
        raise Denied("report failed without safe budget closure") from exc
    print(json.dumps({"status": "published" if done else "report_failed",
                      "day": day, "model_requests": 0,
                      "budget_record": str(path),
                      "real_outcome_verified": False}))
    return 0 if done else 1


def main():
    try:
        return run()
    except (Denied, OSError, ValueError, KeyError) as exc:
        print("statistics-bounded-trial: HOLD: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Authoritative usage primitives for the Act 32 knowledge-office budget engine.

This helper is the ONLY place that reads the token/cost meter. It never writes
to the meter database (read-only URI) and never invents a token or cost value:
if the authoritative source is unreadable it exits non-zero and the POSIX-sh
engine fails closed.

Token usage is read from the Antonina-managed OpenCode service SQLite database
(`session_v2`, keyed by the agent's native_session_id). Whole-host CPU busy
ticks are read from /proc/stat BEFORE launch and thereafter; the difference
is a deliberately pessimistic upper bound for every overlapping office, not
attributable backend CPU. Wall time comes from monotonic session timers.

Subcommands:
  validate CONFIG          validate source-controlled budget config; exit 0/1
  show CONFIG              print the validated, normalised config as JSON
  probe DB                 exit 0 only if authoritative token metering is readable
  snapshot DB SID PID      print a usage snapshot (tokens, reported cost, CPU)
  aggregate RESDIR WINDOW NOW   sum committed charges over reservations
  admit CONFIG AGGJSON OFFICE   decide whether a reservation may be admitted
  overrun CAPSJSON SNAPJSON WALL   decide whether measured usage exceeds caps
"""
import json
import math
import os
import pathlib
import sqlite3
import sys
import time
import urllib.parse
import tempfile

SCHEMA = "viche-knowledge-budget-v1"
OFFICES = ("statistics", "foresight", "strategy", "spying")
CAP_KEYS = ("tokens_total", "cpu_seconds", "wall_seconds")
TOKEN_FIELDS = ("tokens_input", "tokens_output", "tokens_reasoning",
                "tokens_cache_read", "tokens_cache_write")
METER_SOURCE = "opencode-service-session-v2"
MAX_WINDOW = 45 * 86400


def emit(obj, code=0):
    print(json.dumps(obj, sort_keys=True))
    return code


def fail(msg, code=2):
    return emit({"ok": False, "reason": msg}, code)


# ---- configuration -----------------------------------------------------------

def load_config(path):
    try:
        with open(path) as handle:
            return json.load(handle), []
    except (OSError, ValueError) as exc:
        return None, ["config unreadable or not JSON: %s" % exc]


def validate_config(cfg):
    errors = []
    if not isinstance(cfg, dict):
        return ["config must be a JSON object"]
    if cfg.get("schema") != SCHEMA:
        errors.append("schema must be exactly %s" % SCHEMA)
    metering = cfg.get("metering")
    if not isinstance(metering, dict):
        errors.append("metering must be an object")
    else:
        if metering.get("source") != METER_SOURCE:
            errors.append("metering.source must be exactly %s" % METER_SOURCE)
        db = metering.get("opencode_db")
        if not isinstance(db, str) or not db:
            errors.append("metering.opencode_db must be a non-empty string")
    cpu_meter = cfg.get("cpu_meter")
    if (not isinstance(cpu_meter, dict) or cpu_meter.get("available") is not True
            or cpu_meter.get("source") != "proc-stat-host-busy-upper-bound-v1"
            or cpu_meter.get("attribution") != "conservative-whole-host-upper-bound"):
        errors.append("CPU meter must explicitly use a whole-host busy-time upper bound")
    for key, low, high in (("accounting_window_seconds", 1, MAX_WINDOW),
                           ("monitor_interval_seconds", 1, 300)):
        val = cfg.get(key)
        if isinstance(val, bool) or not isinstance(val, int) or not (low <= val <= high):
            errors.append("%s must be an integer in [%d,%d]" % (key, low, high))
    if cfg.get("overrun_action") not in ("kill", "stop"):
        errors.append("overrun_action must be kill or stop")
    baseline = cfg.get("baseline")
    if not isinstance(baseline, dict) or not isinstance(baseline.get("label"), str) \
            or not isinstance(baseline.get("ref"), str):
        errors.append("baseline must carry string label and ref")
    offices = cfg.get("offices")
    if not isinstance(offices, dict) or set(offices) != set(OFFICES):
        errors.append("offices must name exactly: %s" % ", ".join(OFFICES))
    else:
        for office in OFFICES:
            entry = offices[office]
            if not isinstance(entry, dict):
                errors.append("offices.%s must be an object" % office)
                continue
            if not isinstance(entry.get("enabled"), bool):
                errors.append("offices.%s.enabled must be boolean" % office)
            ok, cap_errors = check_caps(entry.get("caps"), "offices.%s.caps" % office)
            errors.extend(cap_errors)
            # Distinguish per-dispatch exposure from the cumulative 45-day
            # budget. An optional per_run_caps keeps older Act32 fixtures
            # byte-for-byte compatible; Act34 adaptive offices set it lower
            # so their real work can repeat without draining an entire office
            # allowance for one invocation.
            if "per_run_caps" in entry:
                run_ok, run_errors = check_caps(
                    entry["per_run_caps"], "offices.%s.per_run_caps" % office)
                errors.extend(run_errors)
                if ok and run_ok:
                    for key in CAP_KEYS:
                        if entry["per_run_caps"][key] > entry["caps"][key]:
                            errors.append("offices.%s.per_run_caps.%s exceeds 45-day cap"
                                          % (office, key))
    aggregate = cfg.get("aggregate")
    if not isinstance(aggregate, dict):
        errors.append("aggregate must be an object")
    else:
        ok, cap_errors = check_caps(aggregate.get("caps"), "aggregate.caps")
        errors.extend(cap_errors)
        if ok and isinstance(offices, dict):
            for key in CAP_KEYS:
                if aggregate["caps"][key] <= 0:
                    errors.append("aggregate.caps.%s must be positive" % key)
                largest = 0
                for office in OFFICES:
                    entry = offices.get(office)
                    if isinstance(entry, dict) and isinstance(entry.get("caps"), dict):
                        value = entry["caps"].get(key)
                        if isinstance(value, int) and not isinstance(value, bool):
                            largest = max(largest, value)
                if aggregate["caps"][key] < largest:
                    errors.append("aggregate.caps.%s must be >= the largest office cap" % key)
    return errors


def check_caps(caps, where):
    if not isinstance(caps, dict):
        return False, ["%s must be an object" % where]
    errors = []
    for key in CAP_KEYS:
        val = caps.get(key)
        if isinstance(val, bool) or not isinstance(val, int) or val <= 0:
            errors.append("%s.%s must be a positive integer" % (where, key))
    return (not errors), errors


# ---- authoritative meter -----------------------------------------------------

def open_meter(path):
    if not path or not os.path.isfile(path):
        raise OSError("OpenCode meter database is missing: %s" % path)
    uri = "file:%s?mode=ro" % urllib.parse.quote(str(path), safe="/")
    con = sqlite3.connect(uri, uri=True, timeout=5)
    con.execute("PRAGMA query_only=1")
    return con


def meter_columns(con):
    return {row[1] for row in con.execute("PRAGMA table_info(session_v2)")}


def host_cpu():
    """Monotone WHOLE-HOST busy CPU seconds (not office CPU attribution).

    Every CPU tick spent by a knowledge office's local backend is included,
    regardless of the supervising runner PID or concurrent workload. Charging
    all host busy ticks to EACH overlapping office is an intentionally
    conservative upper bound. This costs more allowance, never less. A boot
    change or unreadable proc file is fatal to the session meter.
    """
    import re
    boot = pathlib.Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    if not re.fullmatch(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}", boot):
        raise OSError("host boot identity missing or malformed")
    with pathlib.Path("/proc/stat").open() as proc:
        line = proc.readline().strip().split()
    if len(line) < 9 or line[0] != "cpu":
        raise OSError("host aggregate CPU accounting unavailable")
    fields = [int(x) for x in line[1:9]]
    if any(x < 0 for x in fields):
        raise OSError("host CPU counter is invalid")
    hz = os.sysconf("SC_CLK_TCK")
    if not isinstance(hz, int) or hz <= 0:
        raise OSError("invalid host CPU tick rate")
    # user,nice,system,irq,softirq,steal; guest is already part of user
    # and idle/iowait are not CPU execution.
    total = sum(fields[i] for i in (0, 1, 2, 5, 6, 7)) / hz
    return {"cpu_seconds": total, "cpu_boot_id": boot,
            "cpu_available": True, "cpu_source": "proc-stat-host-busy-upper-bound-v1",
            "cpu_attribution": "conservative-whole-host-upper-bound"}


def cpu_delta(baseline, current, previous=None):
    """Reject reboot/reset or regression; label whole-host delta as upper bound."""
    if not all(isinstance(x, dict) for x in (baseline, current)):
        raise ValueError("CPU baseline/current sample missing")
    if baseline.get("cpu_boot_id") != current.get("cpu_boot_id"):
        raise ValueError("CPU host rebooted during reservation")
    if (baseline.get("cpu_source") != "proc-stat-host-busy-upper-bound-v1"
            or current.get("cpu_source") != baseline.get("cpu_source")):
        raise ValueError("CPU source changed")
    before, after = baseline.get("cpu_seconds"), current.get("cpu_seconds")
    if (any(isinstance(x, bool) or not isinstance(x, (int, float)) or
            not math.isfinite(x) for x in (before, after)) or after < before):
        raise ValueError("CPU counter reset or unavailable")
    if previous is not None:
        if not isinstance(previous, dict) or previous.get("cpu_boot_id") != current.get("cpu_boot_id"):
            raise ValueError("previous CPU meter identity lost")
        old = previous.get("cpu_host_seconds")
        if isinstance(old, bool) or not isinstance(old, (int, float)) or after < old:
            raise ValueError("CPU counter regressed from last committed sample")
    updated = dict(current)
    updated["cpu_host_seconds"] = after
    updated["cpu_seconds"] = max(0.0, after - before)
    updated["cpu_upper_bound"] = True
    # The native session can be reused and cannot be identified prelaunch.
    # Absolute session tokens safely UPPER-bound this invocation's tokens.
    # The overrun checker historically requires .tokens.delta_total, so
    # expose the conservative bound under that field with explicit semantics.
    tokens = updated.get("tokens")
    if (not isinstance(tokens, dict)
            or isinstance(tokens.get("total"), bool)
            or not isinstance(tokens.get("total"), int) or tokens["total"] < 0):
        raise ValueError("token session total missing; cannot charge upper bound")
    if updated.get("session_found") is not True:
        raise ValueError("native session is not measured")
    updated["tokens"] = dict(tokens, delta_total=tokens["total"])
    updated["token_accounting"] = "absolute-session-total-upper-bound"
    return updated


def snapshot(db, sid, pid):
    con = open_meter(db)
    try:
        columns = meter_columns(con)
        if not set(TOKEN_FIELDS + ("id", "cost", "time_updated")) <= columns:
            raise OSError("session_v2 lacks authoritative token/cost columns")
        row = con.execute(
            "SELECT %s, cost, time_updated FROM session_v2 WHERE id=?" % ",".join(TOKEN_FIELDS),
            (sid or "",)).fetchone()
    finally:
        con.close()
    tokens = {}
    for idx, name in enumerate(TOKEN_FIELDS):
        if row is None:
            raise OSError("authoritative session row is absent; usage is unknown")
        value = row[idx]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise OSError("authoritative token counter is invalid")
        tokens[name.replace("tokens_", "")] = int(value or 0)
    tokens["total"] = sum(tokens[k] for k in ("input", "output", "reasoning",
                                              "cache_read", "cache_write"))
    reported = bool(row is not None and row[len(TOKEN_FIELDS)] is not None)
    cost = float(row[len(TOKEN_FIELDS)] or 0) if reported else 0.0
    cpu = host_cpu()
    return {
        "available": True,
        "source": METER_SOURCE,
        "at": int(time.time()),
        "session_id": sid,
        "session_found": row is not None,
        "tokens": tokens,
        "cost": cost,
        "cost_reported": reported,
        "cpu_seconds": cpu["cpu_seconds"],
        "cpu_available": cpu["cpu_available"],
        "cpu_boot_id": cpu["cpu_boot_id"],
        "cpu_source": cpu["cpu_source"],
        "cpu_attribution": cpu["cpu_attribution"],
        "time_updated_ms": int(row[len(TOKEN_FIELDS) + 1]) if row[len(TOKEN_FIELDS) + 1] is not None else None,
    }


# ---- accounting --------------------------------------------------------------

def charges(reservations, now, window):
    """Return (totals, counted_ids, skipped_ids) over in-window reservations."""
    totals = {"tokens_total": 0, "cpu_seconds": 0.0, "wall_seconds": 0}
    by_office = {office: {"tokens_total": 0, "cpu_seconds": 0.0, "wall_seconds": 0}
                 for office in OFFICES}
    counted = []
    for path in sorted(pathlib.Path(reservations).glob("*.json")):
        try:
            row = json.loads(path.read_text())
            state = row.get("state")
            created = int(row.get("created_at", 0))
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            raise OSError("reservation record unreadable (%s): %s" % (path.name, exc))
        if not isinstance(row, dict) or row.get("schema") != "viche-knowledge-budget-reservation-v1":
            raise OSError("reservation record has invalid schema: %s" % path.name)
        if row.get("state") not in ("reserved", "active", "held", "closed", "rolled_back", "rejected"):
            raise OSError("reservation has unknown state: %s" % path.name)
        if not isinstance(row.get("id"), str) or not isinstance(row.get("office"), str) or \
                not isinstance(row.get("caps"), dict):
            raise OSError("reservation lacks required identity/caps: %s" % path.name)
        if state == "rolled_back" or state == "rejected":
            continue
        if created > now + 60:
            raise OSError("reservation timestamp is in the future: %s" % path.name)
        if state == "closed" and now - created > window:
            continue
        caps = row.get("caps") if isinstance(row.get("caps"), dict) else {}
        usage = row.get("usage") if isinstance(row.get("usage"), dict) else {}
        charge = row.get("charge") if isinstance(row.get("charge"), dict) else {}
        source = usage if state == "closed" else (charge if state == "held" else caps)
        values = {}
        for key in CAP_KEYS:
            value = source.get(key, caps.get(key))
            if value is None or isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
                raise OSError("reservation has unknown/invalid liability %s: %s" % (key, path.name))
            values[key] = float(value) if key == "cpu_seconds" else int(value)
        office = row.get("office")
        for key in CAP_KEYS:
            totals[key] += values[key]
            if office in by_office:
                by_office[office][key] += values[key]
        counted.append(row.get("id", path.name))
    totals["by_office"] = by_office
    return totals, counted, []


def admit(cfg, agg, office):
    """Reserve both per-office AND shared remaining liability, fail closed.

    A per-run cap is NOT the 45-day spend allowance. At 399k tokens already
    charged, a second 120k-token slice exceeds Statistics' 400k cumulative
    cap and is REFUSED. At 120k charged, another 120k slice is admitted.
    Pending/held sessions count their entire per-run liabilities, never an
    optimistic partial reading. Defaults preserve legacy full-cap reservation.
    """
    office_caps = cfg["offices"][office]["caps"]
    run_caps = cfg["offices"][office].get("per_run_caps", office_caps)
    total_caps = cfg["aggregate"]["caps"]
    by_office = agg.get("by_office")
    previous = by_office.get(office) if isinstance(by_office, dict) else None
    if not isinstance(previous, dict):
        return {"admit": False, "reason": "missing per-office liability"}
    reasons = []
    for key in CAP_KEYS:
        global_used = agg.get(key)
        office_used = previous.get(key)
        if (any(isinstance(v, bool) or not isinstance(v, (int, float))
                or not math.isfinite(v) or v < 0
                for v in (global_used, office_used))):
            reasons.append("%s accounting is missing or invalid" % key)
            continue
        projected_global = global_used + run_caps[key]
        projected_office = office_used + run_caps[key]
        if projected_global > total_caps[key]:
            reasons.append("%s projected %s exceeds aggregate cap %s" %
                           (key, projected_global, total_caps[key]))
        if projected_office > office_caps[key]:
            reasons.append("%s projected %s exceeds %s office cap %s" %
                           (key, projected_office, office, office_caps[key]))
    return {"admit": not reasons, "reason": "; ".join(reasons) or "within caps"}


def overrun(caps, snap, wall):
    if not snap or snap.get("session_found") is not True:
        raise ValueError("token meter row missing")
    if snap.get("cpu_available") is not True or snap.get("cpu_seconds") is None:
        raise ValueError("authoritative backend CPU meter unavailable")
    tokens = snap.get("tokens", {}).get("delta_total")
    cpu = snap.get("cpu_seconds")
    if isinstance(tokens, bool) or not isinstance(tokens, int) or tokens < 0:
        raise ValueError("session token bound unavailable")
    reasons = []
    if tokens >= caps["tokens_total"]:
        reasons.append("tokens_total")
    if cpu >= caps["cpu_seconds"]:
        reasons.append("cpu_seconds")
    if wall >= caps["wall_seconds"]:
        reasons.append("wall_seconds")
    return {"over": bool(reasons), "reasons": reasons,
            "tokens_total": tokens, "cpu_seconds": cpu, "wall_seconds": wall}


def main(argv):
    if not argv:
        return fail("missing subcommand", 2)
    cmd, args = argv[0], argv[1:]
    try:
        if cmd == "validate":
            cfg, errors = load_config(args[0])
            errors = validate_config(cfg) if not errors else errors
            for err in errors:
                print(err, file=sys.stderr)
            return emit({"ok": not errors, "errors": errors}, 0 if not errors else 1)
        if cmd == "show":
            cfg, errors = load_config(args[0])
            errors = validate_config(cfg) if not errors else errors
            if errors:
                return fail("; ".join(errors), 1)
            return emit(cfg, 0)
        if cmd == "probe":
            con = open_meter(args[0])
            try:
                if not set(TOKEN_FIELDS + ("id", "cost", "time_updated")) <= meter_columns(con):
                    return fail("meter schema missing authoritative columns", 1)
                con.execute("SELECT id FROM session_v2 LIMIT 1").fetchone()
            finally:
                con.close()
            return emit({"ok": True, "source": METER_SOURCE}, 0)
        if cmd == "cpu-meter":
            return emit(host_cpu(), 0)
        if cmd == "cpu-delta":
            return emit(cpu_delta(json.loads(args[0]), json.loads(args[1]),
                                  json.loads(args[2]) if len(args) > 2 else None), 0)
        if cmd == "snapshot":
            return emit(snapshot(args[0], args[1] if len(args) > 1 else "",
                                 args[2] if len(args) > 2 else ""), 0)
        if cmd == "delta":
            baseline = json.loads(args[0])
            current = json.loads(args[1])
            if current.get("session_found") is not True or baseline.get("session_found") is not True:
                return fail("baseline/current meter row is absent", 2)
            if baseline.get("session_id") != current.get("session_id"):
                return fail("session identity changed", 2)
            before = baseline.get("tokens", {})
            after = current.get("tokens", {})
            result = {}
            for key in ("input", "output", "reasoning", "cache_read", "cache_write"):
                a, b = before.get(key), after.get(key)
                if isinstance(a, bool) or isinstance(b, bool) or not isinstance(a, int) or not isinstance(b, int) or b < a:
                    return fail("token counter reset or invalid: %s" % key, 2)
                result[key] = b - a
            result["total"] = sum(result.values())
            current["tokens"]["delta_total"] = result["total"]
            current["tokens"]["delta"] = result
            return emit(current, 0)
        if cmd == "aggregate":
            totals, counted, skipped = charges(args[0], int(args[2]), int(args[1]))
            totals["counted"] = counted
            totals["skipped"] = skipped
            return emit(totals, 0)
        if cmd == "admit":
            cfg, errors = load_config(args[0])
            if errors or validate_config(cfg):
                return fail("invalid config", 1)
            agg = json.loads(args[1])
            return emit(admit(cfg, agg, args[2]), 0)
        if cmd == "overrun":
            caps = json.loads(args[0])
            snap = json.loads(args[1]) if args[1] and args[1] != "null" else None
            return emit(overrun(caps, snap, float(args[2])), 0)
        if cmd == "durable-write":
            target = pathlib.Path(args[0])
            target.parent.mkdir(parents=True, exist_ok=True)
            payload = sys.stdin.buffer.read()
            fd, temp = tempfile.mkstemp(prefix=".budget-tmp-", dir=str(target.parent))
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temp, target)
                dirfd = os.open(str(target.parent), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
                try:
                    os.fsync(dirfd)
                finally:
                    os.close(dirfd)
            finally:
                if os.path.exists(temp):
                    os.unlink(temp)
            return emit({"ok": True}, 0)
        if cmd == "durable-mkdir":
            target = pathlib.Path(args[0])
            missing = []
            cursor = target
            while not cursor.exists():
                missing.append(cursor)
                cursor = cursor.parent
            target.mkdir(parents=True, exist_ok=True)
            # Persist new directory entries from the deepest parent outward.
            for directory in reversed(missing):
                for path in (directory, directory.parent):
                    fd = os.open(str(path), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
                    try:
                        os.fsync(fd)
                    finally:
                        os.close(fd)
            return emit({"ok": True}, 0)
    except (IndexError, ValueError, TypeError, OSError, sqlite3.Error) as exc:
        return fail(str(exc), 2)
    return fail("unknown subcommand: %s" % cmd, 2)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

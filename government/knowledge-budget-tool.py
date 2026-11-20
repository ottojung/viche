#!/usr/bin/env python3
"""Authoritative usage primitives for the Act 32 knowledge-office budget engine.

This helper is the ONLY place that reads the token/cost meter. It never writes
to the meter database (read-only URI) and never invents a token or cost value:
if the authoritative source is unreadable it exits non-zero and the POSIX-sh
engine fails closed.

Token usage is read from the Antonina-managed OpenCode service SQLite database
(`session_v2`, keyed by the agent's native_session_id). CPU time is read from
/proc for the agent's runner process (including reaped children). Wall time is
computed by the shell from authoritative timestamps.

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
            if ok:
                for key in CAP_KEYS:
                    if entry["caps"][key] <= 0:
                        errors.append("offices.%s.caps.%s must be positive" % (office, key))
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


def cpu_seconds(pid):
    try:
        raw = pathlib.Path("/proc/%s/stat" % pid).read_text()
        rest = raw[raw.rfind(")") + 2:].split()
        utime, stime, cutime, cstime = (int(x) for x in rest[11:15])
        ticks = os.sysconf("SC_CLK_TCK")
        return (utime + stime + cutime + cstime) / float(ticks), True
    except (OSError, ValueError, IndexError):
        return 0.0, False


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
        value = row[idx] if row is not None else 0
        tokens[name.replace("tokens_", "")] = int(value or 0)
    tokens["total"] = sum(tokens[k] for k in ("input", "output", "reasoning",
                                              "cache_read", "cache_write"))
    reported = bool(row is not None and row[len(TOKEN_FIELDS)] is not None)
    cost = float(row[len(TOKEN_FIELDS)] or 0) if reported else 0.0
    cpu, cpu_ok = cpu_seconds(pid)
    return {
        "available": True,
        "source": METER_SOURCE,
        "at": int(time.time()),
        "session_id": sid,
        "session_found": row is not None,
        "tokens": tokens,
        "cost": cost,
        "cost_reported": reported,
        "cpu_seconds": round(cpu, 3),
        "cpu_available": cpu_ok,
        "time_updated": int(row[len(TOKEN_FIELDS) + 1]) if row is not None and row[len(TOKEN_FIELDS) + 1] is not None else None,
    }


# ---- accounting --------------------------------------------------------------

def charges(reservations, now, window):
    """Return (totals, counted_ids, skipped_ids) over in-window reservations."""
    totals = {"tokens_total": 0, "cpu_seconds": 0.0, "wall_seconds": 0}
    by_office = {office: {"tokens_total": 0, "cpu_seconds": 0.0, "wall_seconds": 0}
                 for office in OFFICES}
    counted, skipped = [], []
    for path in sorted(pathlib.Path(reservations).glob("*.json")):
        try:
            row = json.loads(path.read_text())
            state = row.get("state")
            created = int(row.get("created_at", 0))
        except (OSError, ValueError, TypeError):
            skipped.append(path.name)
            continue
        if state == "rolled_back" or state == "rejected":
            skipped.append(row.get("id", path.name))
            continue
        if created > now + 60 or now - created > window:
            skipped.append(row.get("id", path.name))
            continue
        caps = row.get("caps") if isinstance(row.get("caps"), dict) else {}
        usage = row.get("usage") if isinstance(row.get("usage"), dict) else {}
        charge = row.get("charge") if isinstance(row.get("charge"), dict) else {}
        source = usage if state == "closed" else (charge if state == "held" else caps)
        values = {}
        for key in CAP_KEYS:
            value = source.get(key, caps.get(key, 0))
            values[key] = float(value) if key == "cpu_seconds" else int(value or 0)
        office = row.get("office")
        for key in CAP_KEYS:
            totals[key] += values[key]
            if office in by_office:
                by_office[office][key] += values[key]
        counted.append(row.get("id", path.name))
    totals["by_office"] = by_office
    return totals, counted, skipped


def admit(cfg, agg, office):
    office_caps = cfg["offices"][office]["caps"]
    total_caps = cfg["aggregate"]["caps"]
    reasons = []
    for key in CAP_KEYS:
        projected = agg.get(key, 0) + office_caps[key]
        if projected > total_caps[key]:
            reasons.append("%s projected %s exceeds aggregate cap %s" %
                           (key, projected, total_caps[key]))
    return {"admit": not reasons, "reason": "; ".join(reasons) or "within caps"}


def overrun(caps, snap, wall):
    tokens = snap.get("tokens", {}).get("total", 0) if snap else 0
    cpu = snap.get("cpu_seconds", 0.0) if snap else 0.0
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
        if cmd == "snapshot":
            return emit(snapshot(args[0], args[1] if len(args) > 1 else "",
                                 args[2] if len(args) > 2 else ""), 0)
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
    except (IndexError, ValueError, TypeError, OSError, sqlite3.Error) as exc:
        return fail(str(exc), 2)
    return fail("unknown subcommand: %s" % cmd, 2)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""Deterministic content-addressed single-proof build request.

This is an integrity format, not an authenticated transport. Callers MUST
authenticate both endpoints outside this module and keep all blobs private.
No requests contain shell commands, credentials, or raw lease tokens.
"""
import base64
import binascii
import hashlib
import json
import re

from .. import config, validate

VERSION = 1
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_LOG_BYTES = 64 * 1024
MAX_WALL = 900
MAX_RSS_MIB = 12288


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def hexstr(value, length):
    return isinstance(value, str) and re.fullmatch("[0-9a-f]{%d}" % length, value) is not None


def uint(value, low, high):
    return type(value) is int and low <= value <= high


def strict_load(raw):
    require(isinstance(raw, bytes) and len(raw) <= MAX_JSON_BYTES, "oversized message")
    def unique(items):
        d = {}
        for k, v in items:
            require(k not in d, "duplicate key")
            d[k] = v
        return d
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique,
                      parse_constant=lambda s: (_ for _ in ()).throw(ValueError("non-finite number")))


def make(gap, source, base, toolchain, attempt, wall=600, rss_mib=8192):
    meta = {k: gap[k] for k in ("id", "file", "module", "statement", "imports")}
    obj = {"version": VERSION, "base": base, "toolchain": toolchain,
           "attempt": attempt, "gap": meta, "mode": "elaborate",
           "wall_seconds": wall, "rss_mib": rss_mib,
           "source_sha256": digest(source),
           "source_b64": base64.b64encode(source).decode("ascii")}
    obj["job"] = digest(canonical(obj))
    request(canonical(obj))
    return obj


def request(raw, expected=None):
    obj = strict_load(raw)
    require(isinstance(obj, dict) and set(obj) == {
        "version", "base", "toolchain", "attempt", "gap", "mode",
        "wall_seconds", "rss_mib", "source_sha256", "source_b64", "job"}, "request schema")
    require(type(obj["version"]) is int and obj["version"] == VERSION, "protocol version")
    require(hexstr(obj["base"], 40), "base revision")
    require(obj["toolchain"] == config.LEAN_TOOLCHAIN, "unapproved toolchain")
    require(isinstance(obj["attempt"], str) and re.fullmatch("[0-9a-f]{24}-[0-9a-f]{16}", obj["attempt"]), "attempt identifier")
    require(obj["mode"] == "elaborate", "unapproved build mode")
    require(uint(obj["wall_seconds"], 1, MAX_WALL), "wall budget")
    require(uint(obj["rss_mib"], 256, MAX_RSS_MIB), "memory budget")
    require(hexstr(obj["job"], 64) and obj["job"] == digest(canonical({k:v for k,v in obj.items() if k != "job"})), "job digest")
    gap = obj["gap"]
    require(isinstance(gap, dict) and set(gap) == {"id", "file", "module", "statement", "imports"}, "gap schema")
    require(isinstance(gap["imports"], list), "imports schema")
    require(isinstance(gap["file"], str) and isinstance(gap["module"], str)
            and gap["file"] == "lean/" + gap["module"].replace(".", "/") + ".lean", "module/path disagreement")
    try:
        source = base64.b64decode(obj["source_b64"], validate=True)
    except (TypeError, ValueError, binascii.Error):
        raise ValueError("invalid source encoding")
    require(hexstr(obj["source_sha256"], 64) and digest(source) == obj["source_sha256"], "source digest")
    try:
        validate.validate(gap, source)
    except validate.InvalidCandidate as exc:
        raise ValueError("candidate: " + str(exc)) from exc
    if expected is not None:
        require(all(obj[k] == v for k,v in expected.items()), "stale or mismatched request")
    return obj, source


def make_result(job, status, elapsed_ms, peak_rss_kib, diagnostic="", exit_code=None):
    require(isinstance(diagnostic, str), "diagnostic must be text")
    diag = diagnostic.encode("utf-8")[:MAX_LOG_BYTES].decode("utf-8", errors="ignore")
    obj = {"version": VERSION, "job": job["job"], "base": job["base"],
           "toolchain": job["toolchain"], "source_sha256": job["source_sha256"],
           "attempt": job["attempt"], "status": status, "elapsed_ms": elapsed_ms,
           "peak_rss_kib": peak_rss_kib, "diagnostic": diag, "exit_code": exit_code}
    result(canonical(obj), job)
    return obj


def result(raw, job):
    obj = strict_load(raw)
    require(isinstance(obj, dict) and set(obj) == {
        "version", "job", "base", "toolchain", "source_sha256", "attempt",
        "status", "elapsed_ms", "peak_rss_kib", "diagnostic", "exit_code"}, "result schema")
    require(type(obj["version"]) is int and obj["version"] == VERSION, "protocol version")
    require(all(obj[k] == job[k] for k in ("job", "base", "toolchain", "source_sha256", "attempt")), "result identity mismatch")
    require(obj["status"] in ("elaborated", "rejected", "resource", "obsolete", "infrastructure"), "result status")
    require(uint(obj["elapsed_ms"], 0, (job["wall_seconds"] + 60) * 1000), "elapsed budget")
    require(obj["peak_rss_kib"] is None or uint(obj["peak_rss_kib"], 0, 2**40), "peak memory")
    require(obj["exit_code"] is None or uint(obj["exit_code"], -255, 255), "exit code")
    require(isinstance(obj["diagnostic"], str) and len(obj["diagnostic"].encode("utf-8")) <= MAX_LOG_BYTES, "diagnostic size")
    require(obj["status"] != "elaborated" or obj["exit_code"] == 0, "successful exit required")
    require(obj["status"] != "rejected" or obj["exit_code"] not in (None, 0), "failure exit required")
    return obj

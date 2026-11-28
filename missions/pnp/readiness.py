"""Read-only readiness probe; never claims a unit, publishes or clears STOP."""
import json
import math
import os
import re
from pathlib import Path
import socket
import subprocess
import tempfile
import time

from . import cli, config, desk, frontier, github, gitctl, posting, state, validate
from .lbcert import plugins, plugtest

MAX_BEAT_AGE = 300
MAX_FRONTIER_AGE = 60
MANDATE = "IL6wUXaBGXiOmp4aAI8B4c-possesses"


def lease_errors(records, now):
    errors = []
    for rec in records:
        expiry = rec.get("lease_expires_at")
        if (type(expiry) not in (int, float) or not math.isfinite(expiry)
                or expiry > now + config.LEASE_TTL_SECONDS + 30
                or expiry - now < config.LEASE_TTL_SECONDS - MAX_BEAT_AGE):
            errors.append(str(rec.get("gap_id", "unknown")))
    return errors


# A known merged control case, not an estimate of current family coverage.
# It passed production probes repeatedly on 2026-11-27, and passed again
# on 2026-11-28 after falling outside the rolling 4,000-file scan window.
PROMISE_CONTROL = "L-meta-26403"


def promise_control():
    num = PROMISE_CONTROL.rsplit("-", 1)[1]
    module = "PEqualNP.Outside.L_meta_" + num
    file = "lean/PEqualNP/Outside/L_meta_" + num + ".lean"
    src = subprocess.run(["git", "--git-dir=" + gitctl.MIRROR, "show",
                          "refs/remotes/upstream/main:" + file],
                         capture_output=True, text=True, check=True, timeout=10).stdout
    match = re.search(r"(?ms)^theorem " + re.escape(module) +
                      r"\s*:\s*(.*?)\s*:=\s*by\b", src)
    if match is None:
        raise RuntimeError("merged promise control theorem unavailable")
    return {"id": PROMISE_CONTROL, "module": module, "file": file,
            "statement": match.group(1).strip(),
            "imports": plugtest.historical_imports(src)}


def promise_probe():
    found = plugins.discover()
    if "promise" not in found:
        raise RuntimeError("promise plugin absent")
    case = promise_control()
    if not found["promise"][2](case["statement"]):
        raise RuntimeError("promise control no longer matches generator")
    with tempfile.TemporaryDirectory(prefix="pnp-readiness-") as tmp:
        source, output = Path(tmp)/"statement.txt", Path(tmp)/"candidate.lean"
        source.write_text(case["statement"], encoding="utf-8")
        start = time.monotonic()
        rc, _ = plugins.run("promise", case["id"], str(source), str(output),
                            timeout=posting.BUDGET)
        elapsed = time.monotonic() - start
        if rc != 0 or elapsed > posting.BUDGET:
            raise RuntimeError("promise holdout failed within posting budget")
        validate.validate(case, output.read_bytes())
        return {"gap": case["id"], "seconds": round(elapsed, 3),
                "static_validated": True, "kernel_checked": False,
                "scope": "fixed merged operational control, not family coverage"}


def check(now=None):
    now = time.time() if now is None else now
    errors, checks = {}, {}
    def run(name, fn):
        try:
            checks[name] = fn()
        except Exception as exc:
            # Never include auth, raw desk or candidate data in diagnostics.
            errors[name] = type(exc).__name__
    def require(condition, value):
        if not condition:
            raise RuntimeError("readiness condition failed")
        return value
    run("posting_enabled", lambda: require(not posting.paused(), True))
    run("capacity", lambda: require(desk.capacity() is not None, desk.capacity()))
    snapshot = frontier.load(now)
    run("frontier", lambda: require(
        bool(snapshot) and 0 <= now - snapshot.get("observed", 0) <= MAX_FRONTIER_AGE,
        {"observed": snapshot.get("observed"), "ordinary": snapshot.get("ordinary")}))
    stale = lease_errors(cli.held_records(), now)
    if stale:
        errors["heartbeat"] = stale
    else:
        checks["heartbeat"] = "fresh"
    run("github_identity", github.identity)
    run("fork_identity", lambda: github.repository_name(config.FORK_ID))
    run("upstream_identity", lambda: github.repository_name(config.UPSTREAM_ID))
    run("promise", promise_probe)
    return {"at": time.time(), "ready": not errors, "checks": checks, "errors": errors}


def report_board(result):
    # The standing mission explicitly calls for regular truthful board updates.
    # Report only sanitized diagnostic names; no credentials or lease IDs.
    label = "READY" if result["ready"] else "NOT READY"
    probe = result["checks"].get("promise", {})
    failures = ", ".join(sorted(result["errors"])) or "none"
    body = (f"PnP batch readiness: {label}; failures: {failures}; "
            f"promise control: {probe.get('seconds', 'unverified')} s "
            "(candidate/static validation only, not upstream credit). "
            "Local details: pnp/cache/readiness.json. Standing mission remains open.")
    try:
        p = subprocess.run(["antonina", "board", "comment", "--id", MANDATE,
                            "--author", "Viche PnP readiness", "--body", body],
                           capture_output=True, timeout=15)
        return p.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def main():
    # A probe is not permission to perform research on another host.
    if socket.gethostname().split(".")[0] != "billy-dev":
        print("NOT READY: readiness must execute on billy-dev")
        return 2
    result = check()
    path = Path(config.STATE_ROOT)/"cache"/"readiness.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    state.atomic_write(str(path), json.dumps(result, sort_keys=True)+"\n")
    if "--report" in __import__("sys").argv[1:]:
        result["board_reported"] = report_board(result)
        state.atomic_write(str(path), json.dumps(result, sort_keys=True)+"\n")
    print(("READY" if result["ready"] else "NOT READY")+" "+json.dumps(result, sort_keys=True))
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

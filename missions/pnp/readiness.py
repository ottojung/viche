"""Read-only readiness probe; never claims a unit, publishes or clears STOP."""
import json
import math
import os
from pathlib import Path
import socket
import tempfile
import time

from . import cli, config, desk, frontier, github, posting, state, validate
from .lbcert import plugins, plugtest

MAX_BEAT_AGE = 300
MAX_FRONTIER_AGE = 60


def lease_errors(records, now):
    errors = []
    for rec in records:
        expiry = rec.get("lease_expires_at")
        if (type(expiry) not in (int, float) or not math.isfinite(expiry)
                or expiry > now + config.LEASE_TTL_SECONDS + 30
                or expiry - now < config.LEASE_TTL_SECONDS - MAX_BEAT_AGE):
            errors.append(str(rec.get("gap_id", "unknown")))
    return errors


def promise_probe():
    found = plugins.discover()
    if "promise" not in found:
        raise RuntimeError("promise plugin absent")
    cases = plugtest.merged(found["promise"][2], 1)
    if not cases:
        raise RuntimeError("no matching merged holdout in local mirror")
    case = cases[0]
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
                "static_validated": True, "kernel_checked": False}


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


def main():
    # A probe is not permission to perform research on another host.
    if socket.gethostname().split(".")[0] != "billy-dev":
        print("NOT READY: readiness must execute on billy-dev")
        return 2
    result = check()
    path = Path(config.STATE_ROOT)/"cache"/"readiness.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    state.atomic_write(str(path), json.dumps(result, sort_keys=True)+"\n")
    print(("READY" if result["ready"] else "NOT READY")+" "+json.dumps(result, sort_keys=True))
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

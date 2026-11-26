#!/usr/bin/env python3
"""Parallel, order-preserving board activity signature for the dispatch gate.

`dispatch-gate.sh board-signature` used to run one `antonina board show` per
eligible issue serially. With a growing open-issue set that cost ~98s and, on
top of the other read-only scans, pushed the Executive cycle past its 300s
budget. Fetch concurrently within a bounded pool and emit one
"<issue> <updatedAt> <latest-message-id>" line per issue in INPUT ORDER, the
exact contract the shell caller hashes.

Any failed or unparseable lookup still exits non-zero: the gate fails open on a
broken probe so a monitoring failure can never suppress legitimate work.
VICHE_BOARD_SIGNATURE_WORKERS=1 preserves the historical serial behaviour.
"""
import concurrent.futures
import json
import os
import re
import subprocess
import sys


def _int_env(name, default, low, high):
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return max(low, min(value, high))


WORKERS = _int_env("VICHE_BOARD_SIGNATURE_WORKERS", 8, 1, 16)
TIMEOUT = _int_env("VICHE_BOARD_TIMEOUT", 35, 1, 120)
ISSUE_RE = re.compile(r"[a-zA-Z0-9_-]+\Z")


def _dash(value):
    """Mirror jq's `.x // "-"` (null and false become '-', other values kept)."""
    if value is None or value is False:
        return "-"
    return value if isinstance(value, str) else str(value)


def fetch(issue):
    proc = subprocess.run(
        ["antonina", "board", "show", "--id", issue, "--page", "1", "--json"],
        text=True, capture_output=True, check=False, timeout=TIMEOUT,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"board show {issue} exited {proc.returncode}: {proc.stderr.strip()[:180]}")
    data = json.loads(proc.stdout)
    if not isinstance(data, dict):
        raise ValueError(f"board show {issue} did not return an object")
    messages = data.get("messages")
    latest = messages[0].get("id") if isinstance(messages, list) and messages and isinstance(messages[0], dict) else None
    return f"{issue} {_dash(data.get('updatedAt'))} {_dash(latest)}"


def main(argv):
    if not argv:
        return 2
    for issue in argv:
        if not ISSUE_RE.match(issue):
            print(f"bad issue id {issue}", file=sys.stderr)
            return 2
    results = [None] * len(argv)
    workers = min(WORKERS, len(argv))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(fetch, issue) for issue in argv]
        for index, future in enumerate(futures):
            try:
                line = future.result()
            except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as exc:
                print(f"board-signature: {exc}", file=sys.stderr)
                return 1
            if not line:
                return 1
            results[index] = line
    sys.stdout.write("\n".join(results) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

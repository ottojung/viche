#!/usr/bin/env python3
"""Agent-facing remote Lean check from the immutable bound PnP workspace."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("file", type=Path)
    p.add_argument("--async", dest="asynchronous", action="store_true")
    p.add_argument("--wall", type=int, default=600)
    p.add_argument("--rss-mib", type=int, default=8192)
    a = p.parse_args()
    root = Path("/var/lib/lubko/wd/viche")
    if not (root / "missions/pnp/remote/__main__.py").is_file():
        p.exit(1, "Canonical PnP remote packer not deployed; use the local managed compiler.\n")
    sys.path.insert(0, str(root))
    from missions.pnp.remote.__main__ import prepare
    from missions.pnp.remote import protocol
    relay = str(Path.home() / ".local/bin/marceline-request")
    try:
        job = prepare(Path.cwd(), a.file, a.wall, a.rss_mib)
        status = json.loads(subprocess.check_output([relay, "status"], text=True, timeout=15))
        if (status.get("age_seconds") is None or status["age_seconds"] > 180 or
                job["base"] not in (status.get("capabilities") or {}).get("lean_bases", [])):
            p.exit(1, "Remote service or exact pinned base unavailable; use local Lean.\n")
        with tempfile.TemporaryDirectory(prefix="pnp-remote-job-") as tmp:
            bundle = Path(tmp) / "job.json"
            bundle.write_bytes(protocol.canonical(job))
            bundle.chmod(0o600)
            if a.asynchronous:
                return subprocess.call([relay, "submit", "lean-check", str(bundle)])
            proc = subprocess.run([relay, "lean-check", str(bundle)], stdout=subprocess.PIPE)
            if proc.returncode:
                sys.stdout.buffer.write(proc.stdout)
                return proc.returncode
            receipt = json.loads(proc.stdout)
            result = protocol.result(protocol.canonical(receipt["result"]), job)
            print(json.dumps(receipt, ensure_ascii=False))
            return 0 if result["status"] == "elaborated" and result["exit_code"] == 0 else 1
    except (OSError, ValueError, subprocess.SubprocessError, KeyError) as exc:
        p.exit(1, f"Remote check unavailable: {type(exc).__name__}; use local Lean.\n")

if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Act 19 §3.2 — durable handoff queue at records/handoffs/ (POSIX-invokable).

Subcommands:
  append  <office> <work> <evidence> <authority>   -> prints new open id
  open    <office>                                 -> prints one JSON per open handoff (none if empty)
  done    <id> <evidence>                          -> mark done with evidence
  supersede <id>                                   -> mark superseded
"""
import json
import os
import sys
import time
from pathlib import Path

TOWN = Path(os.environ.get("VICHE_TOWN_ROOT", "/var/lib/lubko/wd/viche"))
QUEUE = TOWN / "records" / "handoffs"


def emit(obj):
    sys.stdout.write(json.dumps(obj, sort_keys=True) + "\n")


def append(office, work, evidence, authority):
    QUEUE.mkdir(parents=True, exist_ok=True)
    hid = "HO-%d-%04x" % (int(time.time()), int.from_bytes(os.urandom(2), "big"))
    entry = {"id": hid, "office": office, "work": work, "evidence": evidence,
             "authority": authority, "ts": int(time.time()), "status": "open"}
    (QUEUE / f"{hid}.json").write_text(json.dumps(entry, sort_keys=True, indent=2) + "\n")
    print(hid)


def open_(office):
    if not QUEUE.is_dir():
        return
    for f in sorted(QUEUE.glob("HO-*.json")):
        try:
            e = json.loads(f.read_text())
        except Exception:
            continue
        if e.get("office") == office and e.get("status") == "open":
            emit(e)


def transition(hid, status, evidence=None):
    f = QUEUE / f"{hid}.json"
    if not f.exists():
        raise SystemExit(f"handoff {hid} not found")
    e = json.loads(f.read_text())
    e["status"] = status
    e["closed_at"] = int(time.time())
    if evidence is not None:
        e["evidence"] = evidence
    f.write_text(json.dumps(e, sort_keys=True, indent=2) + "\n")


def main():
    if len(sys.argv) < 2:
        raise SystemExit(2)
    cmd = sys.argv[1]
    if cmd == "append":
        append(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    elif cmd == "open":
        open_(sys.argv[2])
    elif cmd == "done":
        transition(sys.argv[2], "done", sys.argv[3])
    elif cmd == "supersede":
        transition(sys.argv[2], "superseded")
    else:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Fixed daily plenary sitting (Founder directive 2026-11-16, item 5).

Measured problem: 8 of 10 parliamentary seats had not run since Nov 8, because
a seat only sits when the Clerk summons it and the Clerk summons nobody when no
new business arrives. A quorum (six seats) could therefore never form.

Once per UTC day, at or after VICHE_PARLIAMENT_HOUR (default 17), every
non-Clerk seat is added to records/SUMMONED.txt with a generated summons that
points at a short agenda. The constitutional boot dispatches each seat once;
this script then removes the seats it added so they are not re-run every
sitting interval. No model call is made here.

  daily-sitting.py run               called from government/boot.sh each cycle
  daily-sitting.py dispatched SEAT   called by sitting.sh when SEAT is dispatched
  daily-sitting.py status            print today's record

Environment
  VICHE_DAILY_SITTING=off     disable
  VICHE_PARLIAMENT_HOUR       UTC hour, default 17
  VICHE_PARLIAMENT_SEATS      all (default) or N: summon only the first N
                              non-Clerk seats (N=5 gives a six-seat quorum
                              with the Clerk)
  VICHE_DAILY_NOW             epoch override for tests
"""
import datetime
import json
import os
import pathlib
import sys
import tempfile
import time

TOWN = pathlib.Path(os.environ.get("VICHE_TOWN_ROOT", "/var/lib/lubko/wd/viche"))
STATE = pathlib.Path(os.environ.get("VICHE_STATE_ROOT", "/var/lib/lubko/wd/viche-state"))
ROOT = STATE / "parliament" / "daily"
SUMMONED = TOWN / "records" / "SUMMONED.txt"
MARKER = "<!-- daily-plenary -->"
WINDOW_SECONDS = 6 * 3600


def now():
    return int(os.environ.get("VICHE_DAILY_NOW", time.time()))


def atomic_write(path, text):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".tmp.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(text)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def seat_ids():
    path = TOWN / "government" / "seats.tsv"
    ids = []
    if path.is_file():
        for line in path.read_text().splitlines():
            if line.strip():
                ids.append(line.split("\t")[0])
    return ids


def summoned_ids():
    if not SUMMONED.is_file():
        return []
    return [line.strip() for line in SUMMONED.read_text().splitlines() if line.strip()]


def write_summoned(ids):
    SUMMONED.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(SUMMONED, "".join(i + "\n" for i in ids))


def record_path(day):
    return ROOT / (day + ".json")


def load(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def release_finished(current):
    """Remove from SUMMONED.txt the seats this script added and that have sat
    (or whose six-hour window expired). Seats the Clerk summoned itself are
    never touched."""
    if not ROOT.is_dir():
        return
    for path in sorted(ROOT.glob("2*.json")):
        data = load(path)
        if not isinstance(data, dict):
            continue
        added = list(data.get("added", []))
        dispatched = set(data.get("dispatched", []))
        convened = int(data.get("convened_at", 0))
        release = [s for s in added if s in dispatched or current - convened > WINDOW_SECONDS]
        if not release:
            continue
        write_summoned([i for i in summoned_ids() if i not in set(release)])
        data["added"] = [s for s in added if s not in release]
        data["released"] = sorted(set(data.get("released", [])) | set(release))
        atomic_write(path, json.dumps(data, sort_keys=True) + "\n")


def bills_without_ballots(current):
    bills = TOWN / "records" / "bills"
    ballots = TOWN / "records" / "ballots"
    found = []
    if bills.is_dir():
        for path in sorted(bills.glob("*.md")):
            try:
                recent = current - path.stat().st_mtime < 21 * 86400
            except OSError:
                continue
            if recent and not (ballots / (path.stem + ".tsv")).exists():
                found.append(path.stem)
    return found


def convene(current):
    day = datetime.datetime.fromtimestamp(current, datetime.timezone.utc)
    try:
        hour = int(os.environ.get("VICHE_PARLIAMENT_HOUR", "17"))
    except ValueError:
        hour = 17
    if day.hour < hour:
        return
    stamp = day.strftime("%Y-%m-%d")
    if record_path(stamp).exists():
        return
    if not (STATE / "inaugurated").exists():
        return
    seats = seat_ids()
    if not seats:
        return
    clerk, others = seats[0], seats[1:]
    limit = os.environ.get("VICHE_PARLIAMENT_SEATS", "all")
    if limit.isdigit():
        others = others[: int(limit)]
    agenda = ROOT / "plenary-agenda.md"
    lines = ["# Daily plenary sitting " + stamp, "",
             "Convened automatically (Founder directive 2026-11-16, Act 30). Quorum is six seats, so every",
             "summoned seat is needed. Spend this sitting on decisions, not on re-reading history.", "",
             "## Bills with no recorded ballots (touched in the last 21 days)"]
    pending = bills_without_ballots(current)
    lines += ["- %s  (records/bills/%s.md)" % (b, b) for b in pending] or ["- none"]
    lines += ["", "## Standing items",
              "- Founder directive Acts 29 and 30 (Ministry of Economy; proceed-by-default and obligation expiry): ratify, amend or reject.",
              "- Read the Founder daily digest on Town Hall and any open item marked NEEDS-FOUNDER.",
              "- Requests waiting on you in records/proceed/ (each has a deadline).", "",
              "## What a seat delivers",
              "- A recorded ballot on each bill above, or an evidence-based reason to abstain or to amend; or",
              '- "No business for this seat today" with the one fact that justifies it. Then stop.', ""]
    atomic_write(agenda, "\n".join(lines))
    summons_dir = TOWN / "records" / "summons"
    summons_dir.mkdir(parents=True, exist_ok=True)
    existing = summoned_ids()
    added = []
    for seat in others:
        file = summons_dir / (seat + ".md")
        if not file.exists() or file.stat().st_size == 0 or MARKER in file.read_text():
            atomic_write(file, "%s\n# Daily plenary sitting %s for seat %s\n\nRead %s and deliver what it asks.\n"
                               "This summons was generated; the Clerk may replace it with a specific assignment.\n"
                         % (MARKER, stamp, seat, agenda))
        if seat not in existing:
            existing.append(seat)
            added.append(seat)
    write_summoned(existing)
    atomic_write(record_path(stamp), json.dumps(
        {"day": stamp, "clerk": clerk, "convened_at": current, "added": added,
         "dispatched": [], "bills_listed": pending}, sort_keys=True) + "\n")
    print("Viche: daily plenary convened for %s with %d seat(s)" % (stamp, len(added)), file=sys.stderr)


def dispatched(seat):
    current = now()
    stamp = datetime.datetime.fromtimestamp(current, datetime.timezone.utc).strftime("%Y-%m-%d")
    path = record_path(stamp)
    data = load(path)
    if not isinstance(data, dict) or seat not in data.get("added", []):
        return
    data["dispatched"] = sorted(set(data.get("dispatched", [])) | {seat})
    atomic_write(path, json.dumps(data, sort_keys=True) + "\n")


def main(argv):
    command = argv[0] if argv else "run"
    if command == "run":
        if os.environ.get("VICHE_DAILY_SITTING", "on") == "off":
            return 0
        ROOT.mkdir(parents=True, exist_ok=True)
        release_finished(now())
        convene(now())
    elif command == "dispatched" and len(argv) == 2:
        dispatched(argv[1])
    elif command == "status":
        stamp = datetime.datetime.fromtimestamp(now(), datetime.timezone.utc).strftime("%Y-%m-%d")
        data = load(record_path(stamp))
        if data is not None:
            print(json.dumps(data, sort_keys=True, indent=2))
    else:
        print("usage: daily-sitting.py run|dispatched SEAT|status", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

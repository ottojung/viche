#!/usr/bin/env python3
"""The public, all-time P vs NP leaderboard is the research mission's scoreboard.

Only the site's exported credited points count, never agent/PR activity.
The immutable contributor-file path is taken from the site's live head.json.
"""
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

BASE = "https://data.pequalnp.com/"
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from missions.pnp import config

OWNER = config.DESK_HANDLE
PATH_RE = re.compile(r"data/contributors\.[0-9a-f]{8,64}\.json\Z")


# The export includes every credited lemma, so its size grows with the race.
# Retain a hard bound before JSON parsing and while curl receives the body.
HEAD_LIMIT = 1024 * 1024
CONTRIBUTORS_LIMIT = 32 * 1024 * 1024


def fetch_json(url, max_bytes=CONTRIBUTORS_LIMIT):
    p = subprocess.run(["curl", "--fail", "--silent", "--show-error",
                        "--location", "--max-time", "15",
                        "--max-filesize", str(max_bytes), url],
                       capture_output=True, timeout=20, check=True)
    if len(p.stdout) > max_bytes:
        raise ValueError("oversized leaderboard export")
    return json.loads(p.stdout)


def scoreboard(entries, owner=OWNER):
    if not isinstance(entries, list):
        raise ValueError("contributors list is missing")
    rows = []
    seen = set()
    for entry in entries:
        name = entry.get("github")
        score = entry.get("points")
        steps = entry.get("steps")
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9-]{1,39}", name):
            raise ValueError("invalid contributor handle")
        if type(score) is not int or score < 0 or type(steps) is not int or steps < 0 or name.lower() in seen:
            raise ValueError("invalid or duplicated points/step count")
        seen.add(name.lower())
        rows.append({"handle": name, "steps": steps, "points": score,
                     "first": entry.get("first_proof_at") or ""})
    # Official join.txt: rank by points. Earliest proof breaks equal scores.
    rows.sort(key=lambda x: (-x["points"], x["first"] or "9999",
                             x["handle"].lower()))
    mine = next(((i + 1, p) for i, p in enumerate(rows)
                 if p["handle"].lower() == owner.lower()), None)
    rank = mine[0] if mine else None
    our_steps = mine[1]["steps"] if mine else 0
    our_points = mine[1]["points"] if mine else 0
    competitors = [p for p in rows if p["handle"].lower() != owner.lower()]
    runner_up = competitors[0] if competitors else None
    leader = rows[0] if rows else None
    their_best = runner_up["points"] if runner_up else 0
    return {"rank": rank, "contributors": len(rows),
            "score_metric": "points", "our_steps": our_steps, "our_points": our_points, "leader": leader,
            "runner_up": runner_up if rank == 1 else
                         (rows[1] if len(rows) > 1 else None),
            "our_margin_vs_best_competitor": our_points - their_best,
            "lead_over_second": (our_points - their_best if rank == 1 else None),
            "additional_points_to_clear_first": max(0, their_best + 1 - our_points),
            "rank_one": rank == 1}


def credit_details(entries, owner=OWNER):
    """Validate the public contributor's complete per-unit credit breakdown.

    A missing, truncated, or inconsistent list is unknown, not zero credit.
    The all-time scoreboard remains independently usable.
    """
    entry = next((e for e in entries if e.get("github", "").lower() == owner.lower()), None)
    if entry is None:
        return {}
    lemmas = entry.get("lemmas")
    if not isinstance(lemmas, list) or len(lemmas) != entry.get("steps"):
        return None
    credits = {}
    for row in lemmas:
        if not isinstance(row, dict):
            return None
        gid, points, at = row.get("id"), row.get("points"), row.get("at")
        if (not isinstance(gid, str) or not config.GAP_ID_RE.fullmatch(gid)
                or gid in credits or type(points) is not int or points < 0
                or not isinstance(at, str)):
            return None
        try:
            dt = datetime.datetime.fromisoformat(at.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                return None
            ts = dt.timestamp()
        except (ValueError, OverflowError, OSError):
            return None
        credits[gid] = {"points": points, "at": ts,
                        "estimated": row.get("points_estimated") is True}
    if sum(c["points"] for c in credits.values()) != entry.get("points"):
        return None
    return credits


def record_path():
    return Path(os.environ.get("VICHE_STATE_ROOT",
                              "/var/lib/lubko/wd/viche-state")) / "pnp/leaderboard"


def load():
    path = record_path() / "latest.json"
    try:
        data = json.loads(path.read_text())
        if data.get("score_metric") != "points":
            return {"available": False, "reason": "legacy proof-count snapshot; refresh required"}
        return data
    except (OSError, ValueError):
        return {"available": False, "reason": "no verified leaderboard snapshot"}


def save(snapshot):
    path = record_path()
    path.mkdir(parents=True, exist_ok=True)
    old = load()
    old_margin = old.get("our_margin_vs_best_competitor")
    snapshot["margin_change_since_previous_snapshot"] = (
        snapshot["our_margin_vs_best_competitor"] - old_margin
        if isinstance(old_margin, int) and old.get("score_metric") == "points" else None)
    old_core = {k: old.get(k) for k in
                ("score_metric", "rank", "our_points", "our_steps", "leader", "runner_up")}
    new_core = {k: snapshot.get(k) for k in old_core}
    # Only append history when scoreboard values change.
    if old_core != new_core:
        with (path / "history.jsonl").open("a", encoding="utf-8") as history:
            history.write(json.dumps(snapshot, sort_keys=True) + "\n")
    fd, tmp = tempfile.mkstemp(prefix=".leaderboard-", dir=path)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(snapshot, file, sort_keys=True, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(tmp, path / "latest.json")
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def update():
    head = fetch_json(BASE + "head.json", HEAD_LIMIT)
    rel = head.get("files", {}).get("contributors", "")
    if not isinstance(rel, str) or not PATH_RE.fullmatch(rel):
        raise ValueError("unexpected contributor file in live export")
    source = fetch_json(BASE + rel)
    entries = source.get("contributors", source.get("entries"))
    result = scoreboard(entries)
    checked_at = head.get("checked_at") or head.get("generated_at")
    if not isinstance(checked_at, str) or not checked_at:
        raise ValueError("leaderboard source timestamp missing")
    result.update({"available": True, "source": BASE + rel,
                   "our_credit_details": credit_details(entries),
                   "source_version": head.get("version"),
                   "source_checked_at": checked_at,
                   "observed_at": datetime.datetime.now(
                       datetime.timezone.utc).isoformat()})
    save(result)
    return result


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("update", "status"):
        raise SystemExit("usage: leaderboard.py update|status")
    try:
        result = update() if sys.argv[1] == "update" else load()
        print(json.dumps(result, sort_keys=True))
    except (subprocess.SubprocessError, OSError, ValueError,
            json.JSONDecodeError) as exc:
        print("PnP leaderboard unavailable (preserved last good snapshot): " +
              str(exc), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()

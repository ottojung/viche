#!/usr/bin/env python3
"""Ten-line daily digest for the Founder (Founder directive, 2026-11-16).

Deterministic and read-only apart from its own output: no model call, so it
still reports when every model is exhausted, and it costs no quota. Lines:

   1  header and window
   2  shipped: Viche main
   3  shipped: other repositories and closed board issues
   4  agent invocations finished in the window
   5  blocked: open durable handoffs
   6  blocked: open institutional cases (and today's automatic closures)
   7  quota split: model steps and context tokens by consumer
   8  model availability and provider limit errors
   9  what needs the Founder
  10  where the detail lives

Usage: daily-digest.py [--post] [--force] [--now EPOCH]
Without --post it prints the digest. With --post it also writes
$VICHE_STATE_ROOT/digest/YYYY-MM-DD.md and comments it on Town Hall, at most
once per UTC day and not before VICHE_DIGEST_HOUR (UTC, default 15 = 07:00
Pacific). --force ignores both guards.

Any source that cannot be read is reported as "unavailable", never as zero.
"""
import argparse
import collections
import datetime
import glob
import json
import os
import pathlib
import re
import subprocess
import sys
import time

WINDOW = 24 * 3600
LINE_MAX = 300
NEEDS_FOUNDER = re.compile(r"^\s*NEEDS-FOUNDER:\s*(.+)$", re.M)

town = pathlib.Path(os.environ.get("VICHE_TOWN_ROOT", "/var/lib/lubko/wd/viche"))
state = pathlib.Path(os.environ.get("VICHE_STATE_ROOT", "/var/lib/lubko/wd/viche-state"))
home = pathlib.Path(os.environ.get("HOME", "/home/lubko"))
ant_state = pathlib.Path(os.environ.get("XDG_STATE_HOME", str(home / ".local/state"))) / "antonina"
ant_config = pathlib.Path(os.environ.get("XDG_CONFIG_HOME", str(home / ".config"))) / "antonina/config.json"
townhall = os.environ.get("VICHE_TOWNHALL_ID", "302")
other_repos = [p for p in os.environ.get("VICHE_DIGEST_REPOS", str(home / "soring301")).split(":") if p]


class Unavailable(Exception):
    pass


def run(args, timeout=60):
    try:
        done = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise Unavailable(str(error)[:80])
    if done.returncode != 0:
        raise Unavailable((done.stderr.strip() or "exit %d" % done.returncode)[-80:])
    return done.stdout


def antonina_json(*args):
    try:
        return json.loads(run(["antonina", *args, "--json"]))
    except ValueError:
        raise Unavailable("unparseable antonina output")


def age(seconds):
    if seconds < 3600:
        return "%dm" % (seconds // 60)
    if seconds < 2 * 86400:
        return "%dh" % (seconds // 3600)
    return "%dd" % (seconds // 86400)


def iso_epoch(value):
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def guarded(fn, label):
    try:
        return fn()
    except Unavailable as error:
        return "%s unavailable (%s)" % (label, error)
    except Exception as error:  # a digest line must never take the others down
        return "%s unavailable (%s)" % (label, type(error).__name__)


def git_log(repo, since, ref):
    """Non-merge commits since `since`, each as {subject, files}."""
    out = run(["git", "-C", str(repo), "log", ref, "--no-merges", "--since=@%d" % since,
               "--format=%x00%s", "--name-only"])
    changes = []
    for chunk in out.split("\0")[1:]:
        lines = [line.strip() for line in chunk.split("\n")]
        changes.append({"subject": lines[0], "files": [line for line in lines[1:] if line]})
    return changes


def line_viche(now):
    try:
        run(["git", "-C", str(town), "fetch", "-q", "origin", "main"], timeout=40)
        ref = "FETCH_HEAD"
    except Unavailable:
        ref = "main"
    changes = git_log(town, now - WINDOW, ref)
    code = [c for c in changes if any(not f.startswith("records/") for f in c["files"])]
    records = sum(1 for c in changes if c["files"] and c not in code)  # empty commits count as neither
    head = "; ".join(c["subject"][:70] for c in code[:3])
    return "Shipped (Viche main): %d law/code change(s), %d records-only commit(s)%s" % (
        len(code), records, (" — " + head) if head else "")


def line_elsewhere(now):
    parts = []
    for repo in other_repos:
        name = pathlib.Path(repo).name
        try:
            try:
                run(["git", "-C", repo, "fetch", "-q", "origin", "main"], timeout=40)
                ref = "FETCH_HEAD"
            except Unavailable:
                ref = "origin/main"
            changes = git_log(repo, now - WINDOW, ref)
            parts.append("%s main %d commit(s)" % (name, len(changes)))
        except Unavailable:
            parts.append("%s unavailable" % name)
    closed = []
    for page in range(1, 11):
        issues = antonina_json("board", "list", "--state", "closed", "--page", str(page))
        if not isinstance(issues, list):
            raise Unavailable("board list shape")
        for issue in issues:
            when = iso_epoch(issue.get("updatedAt") or issue.get("lastActivityAt"))
            if when is not None and when >= now - WINDOW:
                closed.append(issue.get("title", "")[:50])
        if len(issues) == 0:
            break
    detail = (" — " + "; ".join(closed[:3])) if closed else ""
    return "Shipped (elsewhere): %s; board issues closed (whole board): %d%s" % (", ".join(parts) or "none tracked", len(closed), detail)


def all_agents():
    agents = []
    for page in range(1, 100):
        data = antonina_json("agent", "list", "--page", str(page), "--limit", "100")
        if data.get("unreadable"):
            raise Unavailable("%d unreadable agent records" % len(data["unreadable"]))
        batch = data.get("agents") or []
        agents += batch
        if len(batch) < 100:
            return agents
    raise Unavailable("agent pagination incomplete")


def line_agents(now, agents):
    done = [a for a in agents if (a.get("finished_at") or 0) >= now - WINDOW]
    states = collections.Counter(a.get("state") for a in done)
    running = sum(1 for a in agents if a.get("state") == "running")
    return "Agent runs finished: %d (%d clean, %d failed, %d stopped/killed); %d running now" % (
        len(done), states.get("clearexit", 0), states.get("failed", 0),
        states.get("stopped", 0) + states.get("killed", 0), running)


def line_handoffs(now):
    out = run(["/bin/sh", str(town / "government/handoff-queue.sh"), "list-open", str(town)])
    rows = [r.split("\t") for r in out.split("\n") if r.strip()]
    if not rows:
        return "Blocked (handoffs): none open"
    oldest = rows[0]
    created = iso_epoch(oldest[0]) or now
    return "Blocked (handoffs): %d open, oldest %s — %s" % (len(rows), age(now - created), oldest[2][:120])


def line_cases(now):
    index = json.loads((state / "institutional-cases/index.json").read_text())
    cases = []
    for path in sorted((state / "institutional-cases").glob("*.json")):
        if path.name.startswith("archive-") or path.name == "index.json":
            continue
        try:
            case = json.loads(path.read_text())
        except ValueError:
            continue
        if isinstance(case, dict) and case.get("state") == "open":
            cases.append(case)
    auto_today = sum(1 for c in index.get("auto_closed", []) if (c.get("closed_at") or 0) >= now - WINDOW)
    if not cases:
        return "Blocked (cases): none open; auto-closed in window: %d" % auto_today
    oldest = min(cases, key=lambda c: c.get("first_seen", now))
    return "Blocked (cases): %d open, oldest %s (%s, owner %s); auto-closed in window: %d" % (
        len(cases), age(now - oldest.get("first_seen", now)), oldest.get("signal"), oldest.get("owner"), auto_today)


def scan_logs(now):
    """Model steps, context tokens and provider-limit errors per consumer in the window."""
    since_ms = (now - WINDOW) * 1000
    steps = collections.Counter()
    tokens = collections.Counter()
    limits = collections.Counter()
    for meta_path in glob.glob(str(ant_state / "agents/*/meta.json")):
        log = pathlib.Path(meta_path).with_name("output.log")
        try:
            if log.stat().st_mtime < now - WINDOW:
                continue
            meta = json.loads(pathlib.Path(meta_path).read_text())
        except (OSError, ValueError):
            continue
        title = (meta.get("title") or "") + " " + (meta.get("cwd") or "")
        who = "SoringP1" if "soring" in title.lower() else "town" if "viche" in title.lower() else "other"
        with open(log, errors="replace") as handle:
            for line in handle:
                if line.startswith('{"type":"step_finish"'):
                    try:
                        event = json.loads(line)
                    except ValueError:
                        continue
                    if event.get("timestamp", 0) < since_ms:
                        continue
                    t = event.get("part", {}).get("tokens") or {}
                    steps[who] += 1
                    tokens[who] += int(t.get("input", 0)) + int((t.get("cache") or {}).get("read", 0)) \
                        + int(t.get("output", 0)) + int(t.get("reasoning", 0))
                elif line.startswith('{"type":"error"'):
                    try:
                        event = json.loads(line)
                    except ValueError:
                        continue
                    if event.get("timestamp", 0) < since_ms:
                        continue
                    kind = (event.get("error") or {}).get("type") or ""
                    if kind in ("provider.quota", "provider.free-limit") or "usage limit" in str(event.get("error")):
                        limits["quota"] += 1
                    elif kind == "provider.rate-limit":
                        limits["rate"] += 1
    return steps, tokens, limits


def line_quota(scan):
    steps, tokens, _ = scan
    total = sum(tokens.values())
    if total == 0:
        return "Quota split: no model steps completed in the window"
    def pct(value):
        share = 100 * value / total
        return "<1%" if 0 < share < 0.5 else "%d%%" % round(share)
    split = ", ".join("%s %s" % (k, pct(tokens[k])) for k in ("town", "SoringP1", "other") if tokens[k]) or "none"
    return "Quota split (context+output tokens): %s — %.1fM tokens over %d steps" % (
        split, total / 1e6, sum(steps.values()))


def line_models(now, scan):
    models = [m["model"] for m in json.loads(ant_config.read_text())["models"]]
    cooling = {}
    for path in glob.glob(str(ant_state / "model-cooldowns/*.json")):
        try:
            entry = json.loads(pathlib.Path(path).read_text())
        except (OSError, ValueError):
            continue
        if entry.get("model") in models and (entry.get("until") or 0) > now:
            cooling[entry["model"]] = entry
    _, _, limits = scan
    detail = "; ".join("%s %s for %s" % (m.split("/")[-1], e["reason"].replace("_", " "), age(e["until"] - now))
                       for m, e in sorted(cooling.items(), key=lambda kv: kv[1]["until"]))
    return "Models: %d/%d usable now%s; provider limit errors in window: %d quota, %d rate" % (
        len(models) - len(cooling), len(models), (" — " + detail) if detail else "", limits["quota"], limits["rate"])


def line_needs(now, scan_ok):
    needs = []
    try:
        models = [m["model"] for m in json.loads(ant_config.read_text())["models"]]
        cooling = 0
        for path in glob.glob(str(ant_state / "model-cooldowns/*.json")):
            entry = json.loads(pathlib.Path(path).read_text())
            if entry.get("model") in models and (entry.get("until") or 0) > now:
                cooling += 1
        if models and cooling == len(models):
            needs.append("every configured model is rate-limited or out of quota (add quota or a model)")
    except (OSError, ValueError, KeyError):
        pass
    try:
        show = antonina_json("board", "show", "--id", townhall, "--page", "1")
        for message in show.get("messages") or []:
            when = iso_epoch(message.get("createdAt"))
            if when is None or when < now - WINDOW or message.get("author") == "Vitalik":
                continue
            for match in NEEDS_FOUNDER.finditer(message.get("body") or ""):
                needs.append(match.group(1).strip()[:110])
    except Unavailable:
        needs.append("Town Hall unreadable, so requests may be missing")
    inbox = state / "founder-inbox"
    try:
        acked = {p.name for p in (inbox / "ack").iterdir()} if (inbox / "ack").exists() else set()
        pending = []
        for sub in ("pending", "sent"):
            if (inbox / sub).exists():
                pending += [p for p in (inbox / sub).iterdir()
                            if p.name.split(".")[0] not in acked and now - p.stat().st_mtime > 3600]
        if pending:
            needs.append("%d Founder message(s) unacknowledged for over an hour" % len(pending))
    except OSError:
        pass
    return "Needs you: " + ("; ".join(needs[:4]) if needs else "nothing")


def build(now):
    stamp = datetime.datetime.fromtimestamp(now, datetime.timezone.utc)
    try:
        agents = all_agents()
        agents_line = line_agents(now, agents)
    except Unavailable as error:
        agents_line = "Agent runs: unavailable (%s)" % error
    try:
        scan = scan_logs(now)
        scan_ok = True
    except OSError:
        scan, scan_ok = (collections.Counter(), collections.Counter(), collections.Counter()), False
    lines = [
        "Viche daily digest — %s (24h to %s)" % (stamp.strftime("%Y-%m-%d"), stamp.strftime("%H:%MZ")),
        guarded(lambda: line_viche(now), "Shipped (Viche main):"),
        guarded(lambda: line_elsewhere(now), "Shipped (elsewhere):"),
        agents_line,
        guarded(lambda: line_handoffs(now), "Blocked (handoffs):"),
        guarded(lambda: line_cases(now), "Blocked (cases):"),
        line_quota(scan) if scan_ok else "Quota split: agent logs unavailable",
        guarded(lambda: line_models(now, scan), "Models:"),
        line_needs(now, scan_ok),
        "Detail: %s/digest/, records/handoffs/, institutional-cases/index.json; generated without a model call" % state,
    ]
    lines = [(l if len(l) <= LINE_MAX else l[:LINE_MAX - 1] + "…") for l in lines]
    assert len(lines) == 10
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--post", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--now", type=float)
    args = parser.parse_args()
    now = args.now or time.time()
    day = datetime.datetime.fromtimestamp(now, datetime.timezone.utc)
    out_dir = state / "digest"
    marker = out_dir / "last-posted"
    if args.post and not args.force:
        if day.hour < int(os.environ.get("VICHE_DIGEST_HOUR", "15")):
            return 0
        if marker.exists() and marker.read_text().strip() == day.strftime("%Y-%m-%d"):
            return 0
    digest = build(now)
    if not args.post:
        sys.stdout.write(digest)
        return 0
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / (day.strftime("%Y-%m-%d") + ".md")).write_text(digest)
    run(["antonina", "board", "comment", "--id", townhall, "--author", "Viche daily digest",
         "--body", digest], timeout=60)
    marker.write_text(day.strftime("%Y-%m-%d") + "\n")
    sys.stdout.write(digest)
    return 0


if __name__ == "__main__":
    sys.exit(main())

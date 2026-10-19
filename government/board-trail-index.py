#!/usr/bin/env python3
"""Act 18 (Board Reporting Act) §7 — generate records/board-trail/index.json.

The index is GENERATED, never hand-maintained. The issue->work mapping comes
from the curated cross-check file records/board-trail/originating.tsv (the
Act 18 §5 lens input), NOT from parsing bill/LAWS prose (which mis-maps: bills
cite other issues as examples). For each originating issue the generator emits
one entry — issue, title, work, owning_office, stage, terminal_status,
git_only_gap — using that mapping plus the Antonina board's terminal-update
check.

git_only_gap is true when the underlying work is enacted/completed in Git while
the originating issue lacks a terminal board update — the defect class Act 18 §2
names, decidable from Git and the board alone.

The board scan is best-effort: if the board is unreachable the index is still
produced from the curated mapping, with git_only_gap computed from Git-only
evidence and the title left blank. POSIX-friendly; no third-party deps.
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

TOWN = Path(os.environ.get("VICHE_TOWN_ROOT", "/var/lib/lubko/wd/viche"))
STATE = Path(os.environ.get("VICHE_STATE_ROOT", "/var/lib/lubko/wd/viche-state"))
INDEX = TOWN / "records" / "board-trail" / "index.json"
ORIGINATING = TOWN / "records" / "board-trail" / "originating.tsv"

STAGE_MARKERS = ("proposal", "enactment", "deployment", "verification")
TERMINAL_STATES = (
    "verification:confirmed",
    "verification:blocked",
    "enactment:not_enacted",
    "deferred",
)

# Act 18 §3.4 content standard: a terminal update carries exactly one stage
# marker AND a DECLARED terminal state. Both the §5 lens
# (government/board-trail-check.sh) and this §7 generator use the SAME rules so
# the two instruments cannot disagree. A terminal token counts only in a
# declaration position — start of line, after a sentence/clause terminator, or
# after a declaration label — never as a bare prose/quoted mention.
STAGE_MARKER_RE = re.compile(
    r"(?i)stage\s*marker[^\n]{0,12}\b(proposal|enactment|deployment|verification)\b")
TERMINAL_DECLARATION_RE = re.compile(
    r"(?m)(^|[.:;—-]\s*|(?i:state|status|terminal|result|outcome|transition)\s+)"
    r"(verification:confirmed|verification:blocked|enactment:not_enacted|deferred)"
    r"([.\s,;:]|$)")


def read(path):
    try:
        return Path(path).read_text()
    except OSError:
        return ""


def board_invoke(*args):
    done = subprocess.run(("antonina", "board", *args), capture_output=True,
                          text=True, timeout=35)
    if done.returncode:
        raise RuntimeError(done.stderr[-160:])
    return json.loads(done.stdout)


def board_title(num):
    try:
        issue = board_invoke("show", "--id", str(num), "--page", "1", "--json")
        return issue.get("title", "") or ""
    except Exception:
        return ""


def board_terminal_state(num):
    """Return the DECLARED terminal state of an originating issue, or None.

    Act 18 §3.3/§3.4: a terminal update carries a stage marker AND a declared
    terminal state — a terminal token in a declaration position, not a
    quoted/prose mention. Automated scheduler/agent status lines are not
    updates. Mirrors the §5 lens exactly (same regexes) so §5 and §7 agree."""
    try:
        issue = board_invoke("show", "--id", str(num), "--page", "1", "--json")
    except Exception:
        return None
    for msg in issue.get("messages") or []:
        body = msg.get("body") or ""
        low = body.lower()
        if "[scheduler-turn]" in low or "[terminal-handoff]" in low:
            continue
        if not STAGE_MARKER_RE.search(body):
            continue
        declared = TERMINAL_DECLARATION_RE.search(body)
        if declared:
            return declared.group(2)
    return None


def parse_originating():
    """Return list of {issue, work_id, act, enacted_epoch, type} from the
    curated mapping file. Skips comments/blank/header rows."""
    rows = []
    for line in read(ORIGINATING).splitlines():
        line = line.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) < 5 or cols[0].strip() == "issue":
            continue
        try:
            issue = int(cols[0])
        except ValueError:
            continue
        rows.append({
            "issue": issue,
            "work_id": cols[1].strip(),
            "act": cols[2].strip(),
            "enacted_epoch": int(cols[3]) if cols[3].strip().isdigit() else 0,
            "type": cols[4].strip(),
        })
    return rows


def work_title(row):
    """Human-readable work description: the bill's title if available, else id."""
    bid = row["work_id"]
    if row["act"] not in ("-", ""):
        law = re.search(
            r"(?m)^## Act " + re.escape(row["act"]) + r" — (.+)$",
            read(TOWN / "government" / "LAWS.md"))
        if law:
            title = law.group(1).strip()
            title = re.sub(r"\s*\(enacted.*$", "", title)
            return f"Act {row['act']} — {title}"
    hm = re.search(r"(?m)^# (.+)$", read(TOWN / "records" / "bills" / f"{bid}.md"))
    if hm:
        return hm.group(1).strip()
    return bid


def owning_office(row):
    # Act 18 §3.2: Clerk owns legislative items (bills, drafts, mandates,
    # proceedings); Executive owns task items.
    return "Executive" if row["type"] == "task" else "Clerk"


def build_index():
    rows = parse_originating()
    by_issue = {}
    for row in rows:
        by_issue.setdefault(row["issue"], []).append(row)

    entries = []
    for num in sorted(by_issue):
        work_list = by_issue[num]
        enacted = any(w["type"] == "law" and w["enacted_epoch"] > 0 for w in work_list)
        title = board_title(num)
        declared = board_terminal_state(num)
        has_terminal = declared is not None
        # git_only_gap: work enacted/completed in Git but no terminal board update.
        git_only_gap = enacted and not has_terminal
        stage = "enactment" if enacted else "proposal"
        if enacted and has_terminal:
            terminal = declared
        elif enacted:
            terminal = None  # enacted but not yet a terminal board update
        elif any(w["type"] == "draft" for w in work_list):
            terminal = "enactment:not_enacted"
        else:
            terminal = None
        entries.append({
            "issue": num,
            "title": title,
            "work": "; ".join(work_title(w) for w in work_list),
            "owning_office": owning_office(work_list[0]),
            "stage": stage,
            "terminal_status": terminal,
            "git_only_gap": git_only_gap,
            "transition_history": [
                {"transition": "enacted" if (w["type"] == "law" and w["enacted_epoch"] > 0) else "proposed",
                 "stage": "enactment" if (w["type"] == "law" and w["enacted_epoch"] > 0) else "proposal",
                 "timestamp": w["enacted_epoch"],
                 "evidence_link": f"records/bills/{w['work_id']}.md"}
                for w in work_list
            ],
        })

    return {
        "generated_at": int(os.environ.get("VICHE_BOARD_TRAIL_NOW", time.time())),
        "generator": "government/board-trail-index.py",
        "mapping_source": "records/board-trail/originating.tsv",
        "issues": entries,
    }


def main():
    index = build_index()
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    tmp = INDEX.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(index, sort_keys=True, indent=2) + "\n")
    os.replace(tmp, INDEX)
    print(f"board-trail-index: {len(index['issues'])} originating issue(s) -> {INDEX}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as err:
        print(f"board-trail-index failed: {err}", file=sys.stderr)
        sys.exit(1)

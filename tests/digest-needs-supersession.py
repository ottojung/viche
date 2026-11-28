#!/usr/bin/env python3
"""The Founder-facing 'Needs you' line must not repeat stale asks or amputate words.

Hermetic: no board, agent, model or state files are read. Only the pure helpers
and line_needs() are exercised, with townhall_needs_messages replaced.
"""
import importlib.util
import os
import pathlib
import sys

root = pathlib.Path(os.environ.get("VICHE_TOWN_ROOT", ".")).resolve()
spec = importlib.util.spec_from_file_location("daily_digest", root / "government" / "daily-digest.py")
digest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(digest)

NOW = 1795850000
TS_NEW = "2026-11-28T08:00:00Z"
TS_OLD = "2026-11-27T08:00:00Z"


def msg(body, when=TS_NEW, author="Ministry of Economy", mid=None):
    return {"author": author, "createdAt": when, "body": body, "id": mid}


def line_with(messages):
    digest.townhall_needs_messages = lambda now: messages
    return digest.line_needs(NOW, True)


# 1. Supersession: the newest reading of a volatile topic replaces older ones.
new_disk = "disk state is short (86% used, 31.9 GiB free) after the Janitor pipeline ran; free space on this box"
old_disk = "disk state is critical (87.1% used, 28.6 GiB free, full in about 18 h); free space on this box"
quota = "approve paid quota for the research fleet"
line = line_with([
    msg("NEEDS-FOUNDER: " + new_disk, TS_NEW),
    msg("NEEDS-FOUNDER: " + old_disk, TS_OLD),
    msg("NEEDS-FOUNDER: " + quota, TS_NEW),
])
assert new_disk in line, line
assert "18 h" not in line and "critical" not in line, line
assert quota in line, line

# 2. A reversed message order must not change which reading wins.
line_rev = line_with([
    msg("NEEDS-FOUNDER: " + old_disk, TS_OLD),
    msg("NEEDS-FOUNDER: " + new_disk, TS_NEW),
])
assert "18 h" not in line_rev and new_disk in line_rev, line_rev

# 3. No mid-word amputation: the surviving prefix is a literal prefix of the ask.
long_ask = ("approve an increase in the model quota for the research fleet because "
            "every free model is exhausted and the frontier has stopped making progress "
            "for several hours while the queue continues to grow beyond capacity")
line_long = line_with([msg("NEEDS-FOUNDER: " + long_ask)])
assert len(line_long) <= digest.LINE_MAX, (len(line_long), line_long)
assert line_long.startswith("Needs you: "), line_long
head = line_long[len("Needs you: "):].split(" … (see detail)")[0]
assert long_ask.startswith(head), (head, long_ask)
assert "… (see detail)" in line_long, line_long
assert head.endswith("capacity") is False  # clipped, not the whole sentence

# 4. Every ellipsis carries an explicit pointer; none is a silent line-boundary cut.
line_many = line_with([
    msg("NEEDS-FOUNDER: " + ("a distinct consequential preference question about the " + ("frontier " * 12))),
    msg("NEEDS-FOUNDER: " + ("another reserved authorization for external compute " + ("resources " * 12))),
    msg("NEEDS-FOUNDER: " + ("a third genuinely different ask requiring the Founder " + ("alone " * 12))),
])
assert len(line_many) <= digest.LINE_MAX, (len(line_many), line_many)
for chunk in line_many.split("…")[1:]:
    assert chunk.startswith(" (see detail)") or chunk.startswith(" +"), line_many

# 5. Founder text, scheduler records and non-Founder chatter stay excluded.
line_excl = line_with([
    msg("NEEDS-FOUNDER: ignore, from the Founder", TS_NEW, author="Vitalik"),
    msg("[scheduler-turn] NEEDS-FOUNDER: ignore, scheduler record", TS_NEW,
        author="antonina-scheduler"),
    msg("NEEDS-FOUNDER: " + quota, TS_NEW, author="an ordinary user"),
])
assert "ignore" not in line_excl and quota in line_excl, line_excl

# 6. Pure helper keeps a word boundary even at a tiny budget.
tiny = digest.clip_ask("approve paid quota for the research fleet", 24)
assert "approve" in tiny and tiny.endswith("(see detail)"), tiny

# 7. Crowding drops the oldest Town Hall asks, not an unacknowledged Founder
# message or an unreadability warning.
import tempfile
import time

with tempfile.TemporaryDirectory() as td:
    pending = pathlib.Path(td) / "founder-inbox" / "pending"
    pending.mkdir(parents=True)
    note = pending / "urgent.json"
    note.write_text("{}")
    old = NOW - 7200
    os.utime(note, (old, old))
    real_state = digest.state
    digest.state = pathlib.Path(td)
    try:
        crowded = [
            msg("NEEDS-FOUNDER: " + ("distinct ask number %d needing a Founder decision " % n + "detail " * 6))
            for n in range(8)
        ]
        line_crowded = line_with(crowded)
        assert "unacknowledged for over an hour" in line_crowded, line_crowded
        assert len(line_crowded) <= digest.LINE_MAX
    finally:
        digest.state = real_state

print("Digest needs-you supersession test passed")

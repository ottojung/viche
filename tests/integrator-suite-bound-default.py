#!/usr/bin/env python3
"""The default Act 21 suite bound must fit a legitimate suite under host load.

On 2026-11-26 four valid candidates failed closed at the old 900 s bound while
the box ran at load 15-17 with concurrent research, and each needed a wasteful
fresh-slug re-proposal. Act 21 §1 may rerun a red suite, so the bound must allow
two full passes yet stay finite and well below the outer `timeout 7200` wrapper.

The literal default is read from source so an operator's VICHE_SUITE_TIMEOUT
override cannot make this invariant check spuriously fail.
"""
import pathlib
import re

repo = pathlib.Path(__file__).resolve().parent.parent
src = (repo / "government" / "integrator.py").read_text()
match = re.search(
    r'os\.environ\.get\(\s*"VICHE_SUITE_TIMEOUT"\s*,\s*"(\d+)"\s*\)', src)
assert match, "no VICHE_SUITE_TIMEOUT default found in integrator.py"
default = int(match.group(1))
assert 900 < default < 7200, (
    "default suite bound %ds must exceed the old 900 s bound (host load) "
    "and stay below the 7200 s integrator wrapper" % default)

print("integrator suite default bound: %ds (load-tolerant, bounded below wrapper)" % default)

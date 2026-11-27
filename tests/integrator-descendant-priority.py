#!/usr/bin/env python3
"""Act 31 queue: a newer approved descendant must take the single full-suite
slot of a pass ahead of the older approved ancestors it already contains.

This is pure ordering, not a gate waiver: the descendant's exact merged
candidate still gets the normal Act 21/28 suite and its own review; when it
lands the ancestor's merge has no tree delta and is absorbed as no_delta.
If the descendant later fails or is refused it leaves `ready`, so the ancestor
is no longer marked contained and is attempted normally on a later pass.
"""
import importlib.util
import pathlib
import subprocess
import sys
import tempfile

repo = pathlib.Path(__file__).resolve().parent.parent
module_path = repo / "government" / "integrator.py"
spec = importlib.util.spec_from_file_location("viche_integrator_desc_test", str(module_path))
integrator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integrator)

NOW = 1_800_000_000
AGED = NOW - integrator.FULL_SUITE_PRIORITY_AGE - 60
FULL = "tests/run-all.sh"
RECORDS = "tests/records-smoke.sh"


def prop(head, when, branch="b", suite=FULL):
    return {"head": head, "at": when, "branch": branch}, None, None, suite


# 1. Pure ordering: aged descendant before equally-old contained ancestors.
olds = ["a" * 40, "b" * 40, "c" * 40, "d" * 40]
contained = set(olds[:3])          # third is the newest coherent combination
ready = [prop(h, AGED + i, "d%d" % i) for i, h in enumerate(olds)]
key = lambda item: integrator.ready_priority_key(item[0], item[3], contained, NOW)
ordered = sorted(ready, key=key)
# The descendant tip is not contained and sorts first; the contained ancestors
# follow it even though they were proposed earlier.
assert ordered[0][3] == FULL and ordered[0][0]["head"] == "d" * 40, ordered[0]
assert all(k[0]["head"] in contained for k in ordered[1:]), ordered

# 2. Records still precede young full candidates and are not reordered.
assert key(prop("a" * 40, NOW - 60, suite=RECORDS)) < key(prop("a" * 40, NOW - 60))
# Aged full candidates still precede records.
assert key(prop("a" * 40, AGED)) < key(prop("a" * 40, AGED, suite=RECORDS))

# 3. A contained head never becomes terminal here; removing the descendant
# from `ready` restores its original priority (no starvation).
assert integrator.ready_priority_key(prop("a" * 40, AGED)[0], FULL, contained, NOW)[1] == 1
assert integrator.ready_priority_key(prop("a" * 40, AGED)[0], FULL, set(), NOW)[1] == 0

# 4. contained_heads uses real git ancestry and is defensive on failure.
integrator.contained_heads(ready)  # pure path does not mutate its input
with tempfile.TemporaryDirectory() as td:
    town = pathlib.Path(td)
    subprocess.run(["git", "init", "-q", "-b", "main", str(town)], check=True)
    subprocess.run(["git", "-C", str(town), "config", "user.email", "t@e.invalid"], check=True)
    subprocess.run(["git", "-C", str(town), "config", "user.name", "T"], check=True)

    def commit(name):
        (town / name).write_text(name + "\n")
        subprocess.run(["git", "-C", str(town), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(town), "commit", "-qm", name], check=True)
        return subprocess.run(["git", "-C", str(town), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()

    a = commit("a")
    b = commit("b")
    c = commit("c")
    old_town = integrator.TOWN
    integrator.TOWN = town
    try:
        assert integrator.is_ancestor_head(a, c) is True
        assert integrator.is_ancestor_head(c, a) is False
        assert integrator.is_ancestor_head(a, a) is False
        chain = [prop(h, AGED, "b%d" % i) for i, h in enumerate((a, b, c))]
        got = integrator.contained_heads(chain)
        assert got == {a, b}, got
        # A descendant that is not approved/ready cannot mark ancestors contained.
        assert integrator.contained_heads([prop(a, AGED, "ancestor")]) == set()
    finally:
        integrator.TOWN = old_town

print("integrator descendant priority: coherent tip first, no starvation, real ancestry verified")

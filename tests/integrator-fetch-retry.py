#!/usr/bin/env python3
"""Hermetic regression for bounded retry of the integrator's checked fetch.

A transient DNS/SSH fault must not abort a whole integration pass on the first
failed fetch. The retry is read-only and idempotent; exhaustion must still fail
closed. No live git command, queue state or writer is touched: integrator.py is
imported with private roots and every git/time call is stubbed.
"""
import importlib.util
import inspect
import os
import pathlib
import tempfile
import time as real_time

here = pathlib.Path(__file__).resolve().parent
repo = here.parent
module_path = repo / "government" / "integrator.py"

tmp = tempfile.mkdtemp(prefix="viche-integrator-fetch-test-")
os.environ["VICHE_TOWN_ROOT"] = tmp
os.environ["VICHE_STATE_ROOT"] = os.path.join(tmp, "state")
os.environ["VICHE_INTEGRATOR_NO_REVIEWER"] = "1"

spec = importlib.util.spec_from_file_location("viche_integrator_fetch_test", str(module_path))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# The retry budget is deliberately small and finite.
assert 1 <= mod.FETCH_ATTEMPTS <= 3, mod.FETCH_ATTEMPTS
assert 0 <= mod.FETCH_RETRY_DELAY_SECONDS <= 5, mod.FETCH_RETRY_DELAY_SECONDS
assert (mod.FETCH_ATTEMPTS - 1) * mod.FETCH_RETRY_DELAY_SECONDS <= 10


class FakeTime:
    def __init__(self):
        self.delays = []

    def sleep(self, seconds):
        self.delays.append(seconds)

    def time(self):
        return real_time.time()


clock = FakeTime()
mod.time = clock
calls = []


def ok_git(*args, **kwargs):
    calls.append((args, kwargs))
    return "ok"


mod.git = ok_git

# 1. A healthy fetch is untouched: one call, no backoff.
calls.clear()
clock.delays.clear()
ref = "+refs/heads/main:refs/remotes/origin/main"
assert mod.fetch_origin(ref) == "ok"
assert calls == [(("fetch", "-q", "origin", ref), {})], calls
assert clock.delays == [], clock.delays

# 2. A transient DNS outage is retried with bounded backoff, then succeeds.
calls.clear()
clock.delays.clear()
attempts = [0]


def flaky_git(*args, **kwargs):
    calls.append((args, kwargs))
    attempts[0] += 1
    if attempts[0] < mod.FETCH_ATTEMPTS:
        raise mod.GitError("git fetch: Could not resolve hostname github.com")
    return "ok"


mod.git = flaky_git
assert mod.fetch_origin(ref) == "ok"
assert len(calls) == mod.FETCH_ATTEMPTS, calls
assert clock.delays == [mod.FETCH_RETRY_DELAY_SECONDS * i
                        for i in range(1, mod.FETCH_ATTEMPTS)], clock.delays

# 3. Exhaustion still fails closed with the original GitError.
calls.clear()
clock.delays.clear()


def always_fail(*args, **kwargs):
    calls.append((args, kwargs))
    raise mod.GitError("git fetch: still down")


mod.git = always_fail
try:
    mod.fetch_origin(ref)
    raise AssertionError("expected GitError after the retry budget")
except mod.GitError:
    pass
assert len(calls) == mod.FETCH_ATTEMPTS, calls
assert len(clock.delays) == mod.FETCH_ATTEMPTS - 1, clock.delays

# 4. The pass-level fetch uses the helper and returns 1 (nothing done) when it
#    cannot recover. This is the exact failure the repair targets.
mod.git = ok_git
seen = []


def dead_helper(*refs):
    seen.append(refs)
    raise mod.GitError("git fetch: resolver still down")


mod.fetch_origin = dead_helper
assert mod.run_locked() == 1
assert len(seen) == 1, seen
assert seen[0] == (ref, "+refs/heads/delivery/*:refs/remotes/origin/delivery/*"), seen

# 5. Both checked call sites route through the helper; no checked git fetch
#    remains in them. Best-effort fetches elsewhere are intentionally untouched.
for fn in (mod.land, mod.run_locked):
    source = inspect.getsource(fn)
    assert "fetch_origin(" in source, fn.__name__
    for line in source.splitlines():
        if 'git("fetch"' in line:
            assert "check=False" in line, (fn.__name__, line)

print("integrator fetch retry: hermetic regression OK")

#!/usr/bin/env python3
"""Hermetic regression: a hung Act 21 suite must be bounded and fail closed.

Reproduces a hung verifier by substituting subprocess.run with a fake that
raises TimeoutExpired. No real test, git command, queue state or writer is
touched; the fake also proves the subprocess carries a finite timeout bound.
"""
import importlib.util
import os
import pathlib
import subprocess
import tempfile

here = pathlib.Path(__file__).resolve().parent
repo = here.parent
module_path = repo / "government" / "integrator.py"

# Isolate module-level paths from the live Town before importing.
tmp = tempfile.mkdtemp(prefix="viche-integrator-timeout-test-")
os.environ["VICHE_TOWN_ROOT"] = tmp
os.environ["VICHE_STATE_ROOT"] = os.path.join(tmp, "state")
os.environ["VICHE_SUITE_TIMEOUT"] = "7"

spec = importlib.util.spec_from_file_location("viche_integrator_timeout_test", str(module_path))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

real_run = mod.subprocess.run
try:
    # A hung suite is bounded and fails the candidate closed: no push, no
    # gate waiver, and the verifier runs in its own session for group kill.
    seen = {}

    def fake_hang(cmd, **kw):
        seen.update(kw)
        raise subprocess.TimeoutExpired(cmd, kw.get("timeout"))

    mod.subprocess.run = fake_hang
    entry = {}
    result = mod.verify_suite(pathlib.Path(tmp), "candidate123", "tests/run-all.sh",
                              pathlib.Path(tmp) / "logs", entry)
    assert result is None, "a hung suite must return None (failure to the caller)"
    bound = seen.get("timeout")
    assert isinstance(bound, (int, float)) and bound > 0, "suite subprocess must be time-bounded: %r" % (bound,)
    assert seen.get("start_new_session") is True, "verifier must run in its own session"
    assert entry.get("status") == "red", "a hung suite must fail closed: %r" % (entry,)
    reason = entry.get("reason", "")
    assert "failed closed" in reason and "Act 21 gate intact" in reason, reason
    assert entry.get("log") is None

    # A normal, completed verification returns a result and leaves the entry
    # untouched (so the existing green/red handling downstream still applies).
    def fake_ok(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 0, stdout="green", stderr="")

    mod.subprocess.run = fake_ok
    entry2 = {}
    result2 = mod.verify_suite(pathlib.Path(tmp), "candidate456", "tests/records-smoke.sh",
                               pathlib.Path(tmp) / "logs", entry2)
    assert result2 is not None and result2.returncode == 0
    assert entry2 == {}, "a completed suite must not mutate the entry: %r" % (entry2,)
finally:
    mod.subprocess.run = real_run

print("integrator suite timeout: hung suite bounded and failed closed; green suite unaffected")

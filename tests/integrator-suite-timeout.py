#!/usr/bin/env python3
"""Hermetic regression for a hung Act 21 suite.

A real hanging verifier (a shell with a child holding the same output pipes)
must be bounded, must fail the candidate closed, and must leave no orphaned
test tree. A completing verifier must be unaffected. No git command, queue
state or live writer is touched: the verifier is a private temp script.

A mocked TimeoutExpired is deliberately NOT used: on this box's Python 3.12
subprocess.run() raises TimeoutExpired without a .process attribute, so a
fake that only raises hides whether the whole process group was terminated.
"""
import importlib.util
import os
import pathlib
import subprocess
import tempfile
import time

here = pathlib.Path(__file__).resolve().parent
repo = here.parent
module_path = repo / "government" / "integrator.py"

# Isolate module-level paths from the live Town before importing.
tmp = tempfile.mkdtemp(prefix="viche-integrator-timeout-test-")
os.environ["VICHE_TOWN_ROOT"] = tmp
os.environ["VICHE_STATE_ROOT"] = os.path.join(tmp, "state")
os.environ["VICHE_SUITE_TIMEOUT"] = "1"

spec = importlib.util.spec_from_file_location("viche_integrator_timeout_test", str(module_path))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# The bound is read at import: it must be positive and finite.
assert 0 < mod.SUITE_TIMEOUT_SECONDS < 60, mod.SUITE_TIMEOUT_SECONDS

worktree = pathlib.Path(tmp)
gov = worktree / "government"
gov.mkdir(exist_ok=True)
script = gov / "suite-status.sh"
logs = worktree / "logs"
logs.mkdir(exist_ok=True)
child_file = worktree / "child.pid"
os.environ["RS_TEST_CHILD_PID_FILE"] = str(child_file)


def alive(pid):
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, PermissionError):
        return False
    return True


def child_pid():
    try:
        return int(child_file.read_text().strip())
    except (OSError, ValueError):
        return None


def reap_child():
    pid = child_pid()
    if pid and alive(pid):
        try:
            os.kill(pid, 9)
        except ProcessLookupError:
            pass


try:
    # The hung verifier spawns a child that inherits the pipes, then hangs.
    # Both must be gone when verify_suite returns.
    script.write_text(
        "#!/bin/sh\n"
        "sleep 30 & echo $! > \"$RS_TEST_CHILD_PID_FILE\"\n"
        "sleep 30\n")
    entry = {}
    started = time.monotonic()
    result = mod.verify_suite(worktree, "candidate123", "tests/run-all.sh", logs, entry)
    elapsed = time.monotonic() - started
    assert result is None, "a hung suite must return None (failure to the caller)"
    assert elapsed < 20, "verifier wait must be bounded, took %.1fs" % elapsed
    assert entry.get("status") == "red", "a hung suite must fail closed: %r" % (entry,)
    reason = entry.get("reason", "")
    assert "failed closed" in reason and "Act 21 gate intact" in reason, reason
    assert entry.get("log") is None

    pid = child_pid()
    assert pid, "hung verifier never spawned its child"
    deadline = time.monotonic() + 3
    while alive(pid) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not alive(pid), "hung child was orphaned (pid %d)" % pid

    # A normal, completed verification returns a result and leaves the entry
    # untouched (so the existing green/red handling downstream still applies).
    script.write_text("#!/bin/sh\necho green\nexit 0\n")
    entry2 = {}
    result2 = mod.verify_suite(worktree, "candidate456", "tests/records-smoke.sh", logs, entry2)
    assert result2 is not None and result2.returncode == 0, (result2,)
    assert "green" in (result2.stdout or ""), result2
    assert entry2 == {}, "a completed suite must not mutate the entry: %r" % (entry2,)
finally:
    reap_child()

print("integrator suite timeout: hung verifier bounded, failed closed, no orphan; green suite unaffected")

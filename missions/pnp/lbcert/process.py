"""Bounded subprocess trees for generators; Linux parent-death cleanup."""
import os
import signal
import subprocess
import sys
import threading
from pathlib import Path

_lock = threading.Lock()
_running = set()
_stopping = False


def terminate(proc):
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def stop_all():
    global _stopping
    with _lock:
        _stopping = True
        for proc in tuple(_running):
            terminate(proc)


def run(argv, timeout=None, **kwargs):
    """Compatible with the bounded capture_output calls in the generator."""
    check = kwargs.pop("check", False)
    if kwargs.pop("capture_output", False):
        kwargs.update(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    with _lock:
        if _stopping:
            raise RuntimeError("generator shutting down")
        proc = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                                 str(os.getpid()), *argv], start_new_session=True, **kwargs)
        _running.add(proc)
    try:
        out, err = proc.communicate(timeout=timeout)
    except BaseException:
        terminate(proc)
        proc.communicate()
        raise
    finally:
        with _lock:
            _running.discard(proc)
    result = subprocess.CompletedProcess(argv, proc.returncode, out, err)
    if check:
        result.check_returncode()
    return result


def child(parent, argv):
    # The guardian is not exec'ed away: if the autosolver dies, it kills
    # its entire child session, including nested generator/compiler processes.
    import ctypes
    def stop(*_):
        os.killpg(os.getpgrp(), signal.SIGKILL)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    if ctypes.CDLL(None, use_errno=True).prctl(1, signal.SIGTERM, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "prctl(PR_SET_PDEATHSIG)")
    if os.getppid() != parent:
        return 125
    p = subprocess.Popen(argv)
    return p.wait()


if __name__ == "__main__":
    sys.exit(child(int(sys.argv[1]), sys.argv[2:]))

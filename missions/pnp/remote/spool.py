"""Private single-host spool, also usable behind a future authenticated relay.

The directory is an operator-owned boundary, not a security sandbox. No Lean
execution occurs here. A trusted runner must enforce isolated pinned checkout,
toolchain, memory, timeout, no network/credentials and cancellation.
"""
import contextlib
import fcntl
import os
from pathlib import Path
import stat
import tempfile

from . import protocol
from .. import build_control


class Spool:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = self.root.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError("spool must be a private directory owned by this user")

    def path(self, job, kind):
        if not protocol.hexstr(job, 64) or kind not in ("request", "result", "cancel", "lock"):
            raise ValueError("invalid spool object name")
        return self.root / (job + "." + kind)

    def read(self, job, kind):
        p = self.path(job, kind)
        try:
            fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except FileNotFoundError:
            return None
        with os.fdopen(fd, "rb") as f:
            info = os.fstat(f.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise ValueError("invalid spool file")
            raw = f.read(protocol.MAX_JSON_BYTES + 1)
            if len(raw) > protocol.MAX_JSON_BYTES:
                raise ValueError("oversized spool file")
            return raw

    def write(self, job, kind, data):
        p = self.path(job, kind)
        fd, tmp = tempfile.mkstemp(dir=self.root, prefix=".incoming-")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, p)
            fd = os.open(self.root, os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    @contextlib.contextmanager
    def locked(self, job):
        fd = os.open(self.path(job, "lock"), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise ValueError("invalid lock object")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                yield False
                return
            yield True
        finally:
            os.close(fd)

    def submit(self, raw):
        job, _ = protocol.request(raw)
        # Equivalent submissions converge on the same content-addressed object.
        self.write(job["job"], "request", protocol.canonical(job))
        return job["job"]

    def cancel(self, job):
        self.write(job, "cancel", b"cancelled\n")

    def poll(self, job):
        raw = self.read(job, "request")
        if raw is None:
            return None
        req, _ = protocol.request(raw)
        if req["job"] != job:
            raise ValueError("request filename disagrees with job identity")
        raw = self.read(job, "result")
        if raw is None:
            return None
        return protocol.result(raw, req)

    def run_one(self, job, runner, headroom=build_control.headroom):
        """Call a trusted isolated runner(req, source, cancelled) once.

        Admission is serialized across this spool. Other host workloads still
        need host-enforced resource controls. Unknown headroom defers.
        Resource/infrastructure results are retryable, never cached as final.
        """
        with self.locked("0"*64) as acquired:
            if not acquired:
                return "busy"
            raw = self.read(job, "request")
            if raw is None:
                return "missing"
            req, source = protocol.request(raw)
            if req["job"] != job:
                raise ValueError("request filename disagrees with job identity")
            def cancelled():
                return self.read(job, "cancel") is not None
            if cancelled():
                out = protocol.make_result(req, "obsolete", 0, None)
            else:
                old = self.poll(job)
                if old and old["status"] in ("elaborated", "rejected", "obsolete"):
                    return "cached"
                free = headroom()
                if free is None or free < build_control.RESERVE + req["rss_mib"] * 1024**2:
                    return "deferred"
                out = runner(req, source, cancelled)
                protocol.result(protocol.canonical(out), req)
                if cancelled():
                    out = protocol.make_result(req, "obsolete", 0, None)
            self.write(job, "result", protocol.canonical(out))
            return out["status"]

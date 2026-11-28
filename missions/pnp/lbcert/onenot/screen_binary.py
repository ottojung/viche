"""Local, content-addressed cache for the untrusted live-set *screen*.

This never produces a proof receipt. Reuse avoids competing C compilations
for each candidate. The Lean kernel still checks every emitted theorem.
"""
import fcntl
import hashlib
import os
from pathlib import Path
import platform
import shutil
import stat
import subprocess
import tempfile
import time

FLAGS = ("-O2",)


def _private_dir(path):
    path.mkdir(mode=0o700, exist_ok=True)
    st = path.lstat()
    if (not stat.S_ISDIR(st.st_mode) or st.st_uid != os.getuid()
            or st.st_mode & 0o077):
        raise OSError("unsafe screen cache directory")


def cached_screen(source, budget=5, root=None):
    """Return a locally compiled screen, or None within the supplied budget."""
    deadline = time.monotonic() + max(0, budget)
    cc = shutil.which("cc")
    if cc is None or budget <= 0:
        return None
    try:
        compiler = Path(cc).resolve(strict=True)
        info = compiler.stat()
        raw = Path(source).read_bytes()
        identity = (str(compiler), info.st_size, info.st_mtime_ns,
                    platform.machine(), FLAGS)
        key = hashlib.sha256(raw + repr(identity).encode()).hexdigest()
        cache = Path(root) if root is not None else Path(tempfile.gettempdir()) / ("viche-screen-" + str(os.getuid()))
        _private_dir(cache)
        target = cache / (key + ".bin")
        lockpath = cache / (key + ".lock")
        fd = os.open(lockpath, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        return None
                    time.sleep(min(0.02, max(0, deadline-time.monotonic())))
            try:
                st = target.lstat()
                if (stat.S_ISREG(st.st_mode) and st.st_uid == os.getuid()
                        and st.st_mode & 0o100 and not st.st_mode & 0o077
                        and st.st_size > 0):
                    return str(target)
                target.unlink()
            except FileNotFoundError:
                pass
            left = deadline-time.monotonic()
            if left <= 0:
                return None
            with tempfile.TemporaryDirectory(prefix="build-", dir=cache) as work:
                src = Path(work)/"screen.c"
                tmp = Path(work)/"screen"
                src.write_bytes(raw)
                subprocess.run([str(compiler), *FLAGS, "-o", str(tmp), str(src)],
                               check=True, timeout=left, capture_output=True)
                tmp.chmod(0o700)
                os.replace(tmp,target)
            return str(target)
        finally:
            os.close(fd)
    except (OSError, subprocess.SubprocessError):
        return None

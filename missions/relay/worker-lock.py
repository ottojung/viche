#!/usr/bin/env python3
"""Single-worker lock held across exec, released by the kernel on exit."""
import fcntl
import os
from pathlib import Path
import stat
import sys

root = Path.home() / ".local/state/marceline-relay"
root.mkdir(mode=0o700, parents=True, exist_ok=True)
info = root.lstat()
if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
    raise SystemExit("relay state directory must be private")
fd = os.open(root / "worker.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
if not stat.S_ISREG(os.fstat(fd).st_mode):
    raise SystemExit("invalid relay worker lock")
try:
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    raise SystemExit("relay worker already running")
os.set_inheritable(fd, True)
node = str(Path.home() / ".local/bin/node")
os.execv(node, [node, sys.argv[1], "worker"])

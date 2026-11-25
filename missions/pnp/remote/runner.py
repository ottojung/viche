"""Explicitly invoked, local worker for an operator-provisioned pinned cache.

No transport, automatic provisioning, credentials, or host network access.
The manifest is local trusted configuration; never accept it from a job.
Read-only mounts protect the cache from the container, not from host writers.
"""
import json
import os
from pathlib import Path
import re
import selectors
import subprocess
import tempfile
import time
import uuid

from . import protocol
from .spool import Spool


def manifest(path):
    p = Path(path)
    info = p.stat()
    if not p.is_file() or info.st_uid != os.getuid() or info.st_mode & 0o022:
        raise ValueError("manifest must be owned and not group/world writable")
    data = protocol.strict_load(p.read_bytes())
    if not isinstance(data, dict) or set(data) != {"base", "toolchain", "image", "toolchain_root", "libraries"}:
        raise ValueError("invalid worker manifest")
    if not protocol.hexstr(data["base"], 40) or not re.fullmatch(r"sha256:[0-9a-f]{64}", data["image"]):
        raise ValueError("pin base and local image by digest")
    if not isinstance(data["libraries"], list) or not 1 <= len(data["libraries"]) <= 64:
        raise ValueError("library list required")
    roots = [data["toolchain_root"], *data["libraries"]]
    for path in roots:
        if not isinstance(path, str) or not Path(path).is_absolute():
            raise ValueError("absolute trusted cache paths required")
        q = Path(path).resolve(strict=True)
        if not q.is_dir() or ":" in str(q) or "," in str(q) or q == Path("/"):
            raise ValueError("invalid mount path")
    if not (Path(roots[0]) / "bin/lean").is_file():
        raise ValueError("missing pinned Lean executable")
    return data


def command(cache, req, source, name):
    """Only operator paths and validated integer bounds affect argv."""
    if req["base"] != cache["base"] or req["toolchain"] != cache["toolchain"]:
        raise ValueError("no matching operator-provisioned cache")
    rss = req["rss_mib"]
    a = ["podman", "run", "--rm", "--pull=never", "--name", name,
         "--network=none", "--read-only", "--cap-drop=all",
         "--http-proxy=false", "--env-host=false", "--log-driver=none",
         "--timeout", str(req["wall_seconds"]), "--entrypoint", "/toolchain/bin/lean",
         "--security-opt=no-new-privileges", "--memory", f"{rss}m",
         "--memory-swap", f"{rss}m", "--pids-limit=128", "--cpus=2",
         "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=64m",
         "--env", "HOME=/tmp", "--env", "PATH=/toolchain/bin:/usr/bin:/bin",
         "-v", f"{Path(cache['toolchain_root']).resolve()}:/toolchain:ro"]
    inside = []
    for i, path in enumerate(cache["libraries"]):
        dest = f"/deps/{i}"
        a += ["-v", f"{Path(path).resolve()}:{dest}:ro"]
        inside.append(dest)
    a += ["--env", "LEAN_PATH="+":".join(inside+["/toolchain/lib/lean"]),
          "-v", f"{source}:/input.lean:ro", cache["image"],
          "-M", str(max(128, rss-256)), "/input.lean"]
    return a


def run(cache, req, source, cancelled):
    start = time.monotonic()
    name = "pnp-check-"+uuid.uuid4().hex
    log = bytearray()
    status = "infrastructure"
    rc = None
    proc = None
    launched = False
    def result():
        return protocol.make_result(req, status, min(int((time.monotonic()-start)*1000),
            (req["wall_seconds"]+60)*1000), None, log.decode("utf-8", "replace"), rc)
    try:
        if cancelled():
            status = "obsolete"
            return result()
        with tempfile.TemporaryDirectory(prefix="pnp-remote-") as tmp:
            f = Path(tmp)/"input.lean"
            f.write_bytes(source)
            f.chmod(0o600)
            argv = command(cache, req, f, name)
            proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, start_new_session=True)
            launched = True
            with selectors.DefaultSelector() as sel:
                sel.register(proc.stdout, selectors.EVENT_READ)
                deadline = start+req["wall_seconds"]
                while True:
                    if cancelled():
                        status = "obsolete"
                        break
                    if time.monotonic() >= deadline:
                        status = "resource"
                        break
                    for key, _ in sel.select(timeout=0.2):
                        chunk = os.read(key.fileobj.fileno(), 8192)
                        if chunk:
                            log.extend(chunk[:max(0, protocol.MAX_LOG_BYTES-len(log))])
                        else:
                            sel.unregister(key.fileobj)
                    if proc.poll() is not None and not sel.get_map():
                        rc = proc.returncode
                        if rc == 0:
                            status = "elaborated"
                        elif rc in (125, 126, 127):
                            status = "infrastructure"
                        elif rc < 0 or rc >= 128 or any(x in log.lower() for x in
                                (b"out of memory", b"memory limit", b"heartbeat", b"maximum recursion")):
                            status = "resource"
                        else:
                            # Conservative: a compiler failure is diagnostic, not
                            # evidence that a mathematical statement is false.
                            status = "rejected"
                        break
            if proc.poll() is None:
                subprocess.run(["podman", "rm", "-f", name], stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=10, check=False)
                proc.kill()
                proc.wait(timeout=5)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        log.extend(str(exc).encode("utf-8")[:max(0,protocol.MAX_LOG_BYTES-len(log))])
        status = "infrastructure"
    finally:
        if proc is not None and proc.poll() is None:
            proc.kill()
            try:
                proc.wait(timeout=5)
            except subprocess.SubprocessError:
                pass
        if launched:
            try:
                subprocess.run(["podman", "rm", "-f", name], stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=10, check=False)
            except (OSError, subprocess.SubprocessError):
                status = "infrastructure"
    return result()


def main():
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", required=True)
    p.add_argument("--spool", required=True)
    p.add_argument("job")
    a = p.parse_args()
    try:
        cache = manifest(a.manifest)
        spool = Spool(a.spool)
        outcome = spool.run_one(a.job, lambda req, src, stop: run(cache, req, src, stop))
        print(json.dumps({"job": a.job, "outcome": outcome}))
    except (ValueError, OSError) as exc:
        p.error(str(exc))


if __name__ == "__main__":
    main()

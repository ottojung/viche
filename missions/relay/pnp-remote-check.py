#!/usr/bin/env python3
"""Remote Lean from a bound PnP workspace. Async for expensive iterations."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path("/var/lib/lubko/wd/viche")
HOME = Path.home()
RELAY = str(HOME / ".local/bin/marceline-request")

def load_protocol():
    sys.path.insert(0, str(ROOT))
    import missions.pnp
    # Transitional, independently approved source snapshot, until canonical
    # remote packer lands. Canonical state/assignment/validator remain in use.
    if not (ROOT/"missions/pnp/remote/protocol.py").is_file():
        fallback = HOME/".local/share/viche/relay/pnp-remote-fallback"
        if (fallback/"remote/protocol.py").is_file():
            missions.pnp.__path__.append(str(fallback))
    from missions.pnp.remote import protocol
    return protocol

def current():
    from missions.pnp import assignment, focus, state, support
    cwd = Path.cwd()
    bound = assignment.binding(cwd)
    if not bound:
        raise ValueError("run from a bound research workspace")
    rec = state.load(bound[0])
    if not rec or rec["lease"] != bound[1] or not focus.eligible(rec):
        raise ValueError("obsolete assignment")
    work = assignment.workspace(cwd)[1].resolve()
    base = subprocess.check_output(["git", "-C", str(work), "rev-parse", "HEAD"], text=True, timeout=5).strip()
    toolchain = (work/"lean/lean-toolchain").read_text().strip()
    return rec, work, base, toolchain, support.attempt(rec)

def availability(base):
    status = json.loads(subprocess.check_output([RELAY, "status", base], text=True, timeout=15))
    return status

def scratch(protocol, file, a, binding):
    rec, work, base, toolchain, attempt = binding
    source = (Path.cwd()/file).resolve()
    if not source.is_relative_to(work) or not source.is_file():
        raise ValueError("file outside bound workspace")
    with source.open("rb") as f:
        raw = f.read(512*1024+1)
    if len(raw)>512*1024:
        raise ValueError("scratch file exceeds 512 KiB")
    raw.decode("utf-8")
    if not protocol.uint(a.wall,1,protocol.MAX_WALL) or not protocol.uint(a.rss_mib,256,protocol.MAX_RSS_MIB):
        raise ValueError("invalid resource limits")
    job={"version":1,"mode":"scratch","base":base,"toolchain":toolchain,"attempt":attempt,
         "wall_seconds":a.wall,"rss_mib":a.rss_mib,"source_sha256":protocol.digest(raw),
         "source_b64":base64.b64encode(raw).decode("ascii")}
    job["job"]=protocol.digest(protocol.canonical(job))
    return job

def record(name):
    try:
        from missions.pnp import tools
        tools.record(name)
    except (ImportError, AttributeError):
        # Same bounded evidence format until the independently reviewed tools
        # inventory lands. No private source or command arguments in telemetry.
        try:
            from missions.pnp import assignment, state, support
            bound=assignment.binding(Path.cwd())
            if not bound:return
            rec=state.load(bound[0])
            if not support.active(rec) or rec["lease"]!=bound[1]:return
            path=support.directory(rec)/"tool-use"/assignment.worker_label(Path.cwd())/(name+".json")
            state.atomic_write(str(path),json.dumps({"tool":name,"at":time.time(),"attempt":support.attempt(rec)})+"\n")
        except Exception:
            pass
    except Exception:
        pass

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("file", type=Path, nargs="?")
    p.add_argument("--availability", action="store_true", help="report current checkout's remote availability and queue")
    p.add_argument("--scratch", action="store_true", help="check an intermediate Lean file (not a complete proof)")
    p.add_argument("--async", dest="asynchronous", action="store_true")
    p.add_argument("--wall", type=int, default=600)
    p.add_argument("--rss-mib", type=int, default=8192)
    a = p.parse_args()
    sys.path.insert(0,str(ROOT))
    try:
        binding=current()
        status=availability(binding[2])
        if a.availability:
            print(json.dumps(status))
            record("remote-availability")
            return 0 if status.get("base_available") else 1
        if a.file is None:
            p.error("FILE required (or --availability)")
        if not status.get("base_available"):
            p.exit(1, "Remote service or exact base unavailable; use local Lean.\n")
        protocol=load_protocol()
        if a.scratch:
            job=scratch(protocol,a.file,a,binding)
        else:
            from missions.pnp.remote.__main__ import prepare
            job=prepare(Path.cwd(),a.file,a.wall,a.rss_mib)
        if current()[2:] != binding[2:]:
            raise ValueError("assignment changed during packaging")
        record("remote-scratch" if a.scratch else "remote-check")
        with tempfile.TemporaryDirectory(prefix="pnp-remote-job-") as tmp:
            bundle=Path(tmp)/"job.json"
            bundle.write_bytes(protocol.canonical(job))
            bundle.chmod(0o600)
            if a.asynchronous:
                return subprocess.call([RELAY,"submit","lean-check",str(bundle)])
            proc=subprocess.run([RELAY,"lean-check",str(bundle)],stdout=subprocess.PIPE)
            if proc.returncode:
                sys.stdout.buffer.write(proc.stdout)
                return proc.returncode
            receipt=json.loads(proc.stdout)
            result=protocol.result(protocol.canonical(receipt["result"]),job)
            print(json.dumps(receipt,ensure_ascii=False))
            return 0 if result["status"]=="elaborated" and result["exit_code"]==0 else 1
    except (ImportError,OSError,ValueError,subprocess.SubprocessError,KeyError) as exc:
        p.exit(1, f"Remote check unavailable: {type(exc).__name__}: {exc}; use local Lean.\n")

if __name__=="__main__":
    raise SystemExit(main())

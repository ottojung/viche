#!/usr/bin/env python3
"""Fixed data-only adapter to the existing isolated PnP runner.

The operator supplies the trusted checkout and pinned cache manifests. The
request can select only a validated PnP job whose base has a matching manifest.
"""
import json
import base64
import os
from pathlib import Path
import signal
import subprocess
import re
import stat
import sys

def private_file(p):
    info = p.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("configuration must be private and operator owned")
    return p

def unpack(protocol, raw):
    job=protocol.strict_load(raw)
    if job.get("mode")!="scratch":
        return protocol.request(raw)
    keys={"version","mode","base","toolchain","attempt","wall_seconds","rss_mib",
          "source_sha256","source_b64","job"}
    protocol.require(set(job)==keys and job["version"]==1, "scratch schema")
    protocol.require(protocol.hexstr(job["base"],40) and protocol.hexstr(job["job"],64), "scratch identity")
    protocol.require(re.fullmatch(r"[0-9a-f]{24}-[0-9a-f]{16}",job["attempt"]) is not None, "scratch attempt")
    protocol.require(protocol.uint(job["wall_seconds"],1,protocol.MAX_WALL), "scratch wall")
    protocol.require(protocol.uint(job["rss_mib"],256,protocol.MAX_RSS_MIB), "scratch memory")
    protocol.require(protocol.digest(protocol.canonical({k:v for k,v in job.items() if k!="job"}))==job["job"], "scratch digest")
    source=base64.b64decode(job["source_b64"],validate=True)
    protocol.require(len(source)<=512*1024 and protocol.digest(source)==job["source_sha256"], "scratch source")
    source.decode("utf-8")
    return job,source

def main():
    configuration = json.loads(private_file(Path(sys.argv[1])).read_text())
    if set(configuration) != {"runner_root", "manifests"}:
        raise ValueError("invalid operator configuration")
    root = Path(configuration["runner_root"]).resolve(strict=True)
    manifests = Path(configuration["manifests"]).resolve(strict=True)
    if not root.is_dir() or not manifests.is_dir():
        raise ValueError("missing operator-provisioned paths")
    sys.path.insert(0, str(root))
    from missions.pnp.remote import protocol, runner
    raw = sys.stdin.buffer.read(protocol.MAX_JSON_BYTES + 1)
    req, source = unpack(protocol, raw)
    p = manifests / (req["base"] + ".json")
    if not p.is_file():
        return protocol.make_result(req, "infrastructure", 0, None, "no pinned cache for this base")
    cache = runner.manifest(private_file(p))
    if cache["base"] != req["base"] or cache["toolchain"] != req["toolchain"]:
        raise ValueError("cache identity mismatch")
    # The shared dependency cache is deliberately not duplicated; verify its
    # pinned package identities on every request. Operator-owned compiled
    # files must remain immutable between provisioning and use.
    provenance = json.loads(private_file(manifests / (req["base"] + ".provenance.json")).read_text())
    if provenance["base"] != req["base"] or provenance["runner_revision"] != (root / "REVISION").read_text().strip():
        raise ValueError("cache provenance mismatch")
    checkout = Path(provenance["dependency_checkout"]).resolve(strict=True)
    for name, revision in provenance["package_revisions"].items():
        if not re.fullmatch(r"[A-Za-z0-9_-]+", name) or not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise ValueError("invalid package provenance")
        actual = subprocess.check_output(
            ["git", "-C", str(checkout / name), "rev-parse", "HEAD"],
            text=True, timeout=5, stderr=subprocess.DEVNULL).strip()
        if actual != revision:
            return protocol.make_result(req, "infrastructure", 0, None, "shared dependency revision changed")
    for module in re.findall(r"(?m)^import\s+([A-Za-z0-9_.]+)\s*$", source.decode("utf-8")):
        rel = module.replace(".", "/") + ".olean"
        if not any((Path(lib) / rel).is_file() for lib in cache["libraries"]):
            return protocol.make_result(req, "infrastructure", 0, None, "pinned cache lacks an imported module")
    cancelled = False
    def stop(*_):
        nonlocal cancelled
        cancelled = True
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    from compile_admission import slot
    try:
        with slot(req["rss_mib"], timeout=120, cancelled=lambda:cancelled):
            out = runner.run(cache, req, source, lambda: cancelled)
    except TimeoutError:
        return protocol.make_result(req, "resource", 0, None, "shared compiler admission deferred")
    protocol.result(protocol.canonical(out), req)
    return out

if __name__ == "__main__":
    try:
        print(json.dumps(main(), ensure_ascii=False))
    except Exception:
        # Never print unpublished proof content or a config path to service logs.
        print(json.dumps({"error":"job or isolated runner validation failed"}))

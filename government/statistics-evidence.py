#!/usr/bin/env python3
"""Deterministic evidence utilities for the Act 32 Statistics trial preflight.

No network, no clock, no randomness: the same bytes always yield the same
output. Used to freeze source snapshots, detect tampering and record missing
observations honestly (unavailable is not zero). POSIX-invocable from sh.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

REQUIRED_DESIGN_FIELDS = (
    "candidate_outcome", "numerator", "denominator_statistical",
    "denominator_resource", "negative_controls", "missingness",
    "observation_windows", "comparison", "falsifiers", "gates",
)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def snapshot_path(root, name):
    """Return a path only for a plain, non-symlink filename inside root.

    Rejects '', '.', '..', any path separator, NUL and symlinks so a crafted
    attestation cannot make verify() read outside the pinned snapshot set.
    """
    if not isinstance(name, str) or not name or name in (".", ".."):
        return None
    if "/" in name or "\\" in name or "\x00" in name:
        return None
    if os.path.basename(name) != name:
        return None
    path = root / name
    if os.path.islink(path):
        return None
    try:
        if path.resolve().parent != root.resolve():
            return None
    except OSError:
        return None
    return path


def manifest(source_dir):
    """Return sha256sum-style lines for every regular file, sorted by name."""
    root = Path(source_dir)
    if not root.is_dir():
        raise SystemExit("evidence: not a directory: %s" % source_dir)
    lines = []
    for path in sorted(root.iterdir()):
        if path.is_symlink():
            continue
        if not path.is_file() or path.name == "MANIFEST.sha256":
            continue
        lines.append("%s  %s" % (sha256_of(path), path.name))
    return "\n".join(lines) + ("\n" if lines else "")


def load_attestation(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def verify(attestation_path, source_dir):
    """Check pinned source snapshots against their declared hashes and sizes.

    Prints a JSON report. Exit 0 only when every attested snapshot is a plain
    in-root file with matching hash and size, the attested set equals the files
    present, and the frozen MANIFEST (if present) is consistent.
    """
    att = load_attestation(attestation_path)
    root = Path(source_dir)
    problems = []
    sources = att.get("sources")
    if not isinstance(sources, list) or not sources:
        problems.append("no pinned sources in attestation")
        sources = []
    declared_names = []
    for entry in sources:
        if not isinstance(entry, dict):
            problems.append("malformed source entry")
            continue
        name = entry.get("snapshot")
        path = snapshot_path(root, name)
        if path is None:
            problems.append("unsafe or missing snapshot name: %r" % (name,))
            continue
        declared_names.append(name)
        if not path.is_file():
            problems.append("missing source: %s" % name)
            continue
        got_hash = sha256_of(path)
        want_hash = entry.get("sha256")
        want_size = entry.get("size_bytes")
        size = path.stat().st_size
        if want_hash is not None and got_hash != want_hash:
            problems.append("hash mismatch: %s" % name)
        if want_size is not None and size != want_size:
            problems.append("size mismatch: %s" % name)
    present = {p.name for p in root.iterdir()
               if p.is_file() and not p.is_symlink() and p.name != "MANIFEST.sha256"}
    extra = sorted(present - set(declared_names))
    if extra:
        problems.append("unattested files present: %s" % ",".join(extra))
    manifest_path = root / "MANIFEST.sha256"
    if manifest_path.is_file() and not manifest_path.is_symlink():
        declared = {}
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            parts = line.split("  ", 1)
            if len(parts) == 2:
                declared[parts[1]] = parts[0]
        for name, digest in sorted(declared.items()):
            path = snapshot_path(root, name)
            if path is None or not path.is_file():
                problems.append("manifest file missing or unsafe: %s" % name)
            elif sha256_of(path) != digest:
                problems.append("manifest hash mismatch: %s" % name)
    report = {
        "verified": not problems,
        "source_count": len(sources),
        "problems": problems,
    }
    print(json.dumps(report, sort_keys=True))
    return 0 if not problems else 1


def missingness(attestation_path):
    """Assert the design is present and measurements are not fabricated.

    An unmetered resource must be recorded as "unavailable"; writing 0 would
    manufacture a comparator the Town does not have. A claimed meter must carry
    a frozen source snapshot, numeric values, timestamps and a method.
    """
    att = load_attestation(attestation_path)
    problems = []
    for key in REQUIRED_DESIGN_FIELDS:
        if key not in att or att[key] in (None, "", [], {}):
            problems.append("missing design field: %s" % key)
    res = att.get("denominator_resource")
    if isinstance(res, dict):
        if res.get("meter_available") is not True:
            for field in ("tokens", "machine_time", "wall_time"):
                if res.get(field) == 0:
                    problems.append("unmetered %s recorded as zero" % field)
                if res.get(field) is None and field not in res.get("_declared_unavailable", []):
                    problems.append("unmetered %s not declared unavailable" % field)
        else:
            for field in ("units", "source_snapshot", "measured_at", "method"):
                value = res.get(field)
                if not isinstance(value, str) or not value or value == "unavailable":
                    problems.append("metered denominator missing %s" % field)
            values = res.get("values")
            if not isinstance(values, dict) or any(
                    not isinstance(values.get(k), (int, float)) or isinstance(values.get(k), bool)
                    for k in ("tokens", "machine_time", "wall_time")):
                problems.append("metered denominator lacks numeric values")
            if res.get("reproducible") is not True:
                problems.append("metered denominator not reproducible")
    else:
        problems.append("denominator_resource is not an object")
    report = {"honest": not problems, "problems": problems}
    print(json.dumps(report, sort_keys=True))
    return 0 if not problems else 1


def main(argv):
    if len(argv) < 2:
        raise SystemExit("usage: statistics-evidence.py manifest|verify|missingness ...")
    cmd = argv[1]
    if cmd == "manifest" and len(argv) == 3:
        sys.stdout.write(manifest(argv[2]))
        return 0
    if cmd == "verify" and len(argv) == 4:
        return verify(argv[2], argv[3])
    if cmd == "missingness" and len(argv) == 3:
        return missingness(argv[2])
    raise SystemExit("evidence: unknown command or argument count")


if __name__ == "__main__":
    sys.exit(main(sys.argv))

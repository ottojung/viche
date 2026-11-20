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


def manifest(source_dir):
    """Return sha256sum-style lines for every regular file, sorted by name."""
    root = Path(source_dir)
    if not root.is_dir():
        raise SystemExit("evidence: not a directory: %s" % source_dir)
    lines = []
    for path in sorted(root.iterdir()):
        if not path.is_file() or path.name == "MANIFEST.sha256":
            continue
        lines.append("%s  %s" % (sha256_of(path), path.name))
    return "\n".join(lines) + ("\n" if lines else "")


def load_attestation(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def verify(attestation_path, source_dir):
    """Check pinned source snapshots against their declared hashes and sizes.

    Prints a JSON report. Exit 0 only when every pinned snapshot is present and
    byte-identical and the frozen MANIFEST (if present) is consistent.
    """
    att = load_attestation(attestation_path)
    root = Path(source_dir)
    problems = []
    sources = att.get("sources")
    if not isinstance(sources, list) or not sources:
        problems.append("no pinned sources in attestation")
        sources = []
    for entry in sources:
        if not isinstance(entry, dict):
            problems.append("malformed source entry")
            continue
        name = entry.get("snapshot")
        if not name or not isinstance(name, str):
            problems.append("source entry without snapshot name")
            continue
        path = root / name
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
    manifest_path = root / "MANIFEST.sha256"
    if manifest_path.is_file():
        declared = {}
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            parts = line.split("  ", 1)
            if len(parts) == 2:
                declared[parts[1]] = parts[0]
        for name, digest in sorted(declared.items()):
            path = root / name
            if not path.is_file():
                problems.append("manifest file missing: %s" % name)
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
    """Assert the design is present and unavailable measures are not faked as 0.

    A resource measurement that was never metered must be recorded as
    "unavailable"; writing 0 would manufacture a comparator the Town does not
    have. Exit 0 only for an honest record.
    """
    att = load_attestation(attestation_path)
    problems = []
    for key in REQUIRED_DESIGN_FIELDS:
        if key not in att or att[key] in (None, "", [], {}):
            problems.append("missing design field: %s" % key)
    res = att.get("denominator_resource")
    if isinstance(res, dict):
        if res.get("meter_available") is True and res.get("units") in (None, "", "unavailable"):
            problems.append("meter claimed available without units")
        if res.get("meter_available") is not True:
            for field in ("tokens", "machine_time", "wall_time"):
                if res.get(field) == 0:
                    problems.append("unmetered %s recorded as zero" % field)
                if res.get(field) is None and field not in res.get("_declared_unavailable", []):
                    problems.append("unmetered %s not declared unavailable" % field)
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

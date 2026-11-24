#!/usr/bin/env python3
"""Reviewed shared routines for Act34 certification (separate from legacy gate)."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess


def committed(root, rel):
    path = root / rel
    raw = path.read_bytes()
    head = subprocess.run(["git", "-C", str(root), "show", "HEAD:" + rel],
                          check=True, capture_output=True, timeout=8).stdout
    if raw != head:
        raise ValueError("unreviewed bytes: " + rel)
    return hashlib.sha256(raw).hexdigest()


def attest(root, role, officer, ref, commit, digest, attestation, gate_id):
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{7,40}", commit):
        raise ValueError("origin commit missing")
    if committed(root, ref) != digest:
        raise ValueError("artifact digest mismatch")
    raw = subprocess.run(["git", "-C", str(root), "show", commit + ":" + ref],
                         check=True, capture_output=True, timeout=8).stdout
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("origin commit does not contain exact artifact")
    module = root / "government/knowledge-phase-verifier.py"
    committed(root, "government/knowledge-phase-verifier.py")
    spec = importlib.util.spec_from_file_location("act34_cert_phase", module)
    verifier = importlib.util.module_from_spec(spec); spec.loader.exec_module(verifier)
    errors = verifier.Verifier(str(root)).validate_attestation(
        attestation, gate_id=gate_id, officer_id=officer, role=role,
        artifact_commit=commit, historical=True)
    if errors:
        raise ValueError("unverified %s certification: %s" % (role, "; ".join(errors)[:250]))


def legacy_checks(root, office, activation, permit, permit_sha, start, now):
    # Reuse the exact old permit and Judiciary checks without invoking old
    # zero-cost byte-hash checks that v3 intentionally replaces.
    attestation = activation.get("permit_attestation")
    attest(root, "executive", "c1e00002",
           "records/knowledge/permits/%s.json" % office,
           activation.get("permit_origin_commit"), permit_sha, attestation,
           "act34-executive-" + office)
    review_rel = "records/knowledge/pilot-reviews/%s.json" % office
    review_path = root / review_rel
    if review_path.exists():
        review_sha = committed(root, review_rel)
        rev = json.loads(review_path.read_text(encoding="utf-8"))
        reviewed = rev.get("reviewed_at")
        if (rev.get("schema") != "viche-act34-judiciary-review-v1" or
                rev.get("office") != office or rev.get("reviewer") != "c1e00008" or
                rev.get("permit_sha256") != permit_sha or type(reviewed) is not int or
                not start <= reviewed < start + 48*3600 or reviewed > now):
            raise ValueError("uncorroborated or stale Judiciary disposition")
        auth_rel = "records/knowledge/pilot-reviews/%s-attestation.json" % office
        committed(root, auth_rel)
        auth = json.loads((root / auth_rel).read_text(encoding="utf-8"))
        attest(root, "judiciary", "c1e00008", review_rel,
               auth.get("artifact_commit"), review_sha, auth.get("attestation"),
               "act34-judiciary-" + office)
        if rev.get("decision") != "proceed":
            raise ValueError("Judiciary HOLD/STOP")
    elif now >= start + 48*3600:
        raise ValueError("Judiciary review missing after original permit start")
    if office == "spying" and not (root / "records/knowledge/spying-source-scope.json").is_file():
        raise ValueError("Spying permitted source-scope bundle absent")

#!/usr/bin/env python3
"""Opt-in certified Act34 parity-v3 control verifier (NOT the legacy gate).

This module is reached only from the non-hash-bound activation verifier, only
when the exact parity-v3 bill is genuinely codified and a durable permit
explicitly selects this route. It never edits anything and never authorizes an
office by itself. The legacy Act34 gate, its test and its eight bound controls
are byte-for-byte unchanged; legacy permits keep the legacy path.

Two distinct digests are used, exactly as the filed bill requires:

  * ``control_digest`` binds the current committed bytes of the eight shared
    controls (the ``gate_sha256`` control is THIS executable, not the old one);
  * ``policy_digest`` binds the parsed, key-sorted zero-billed policy content
    (models, source, go_source, review_after) plus the exact rejected-ID vector.
    It deliberately does NOT hash control bytes: a comment-only control repair
    keeps the policy digest and all four permit hashes unchanged.

The certification record is attested by Economy through the existing
institutionally-attested channels at its own origin commit. It never contains
its own digest (that would be a self-referential hash); the binding lives in a
separate activation evidence field. POSIX-compatible invocation via python3.
"""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import socket
import sys
import time

sys.dont_write_bytecode = True

OFFICES = ("statistics", "foresight", "strategy", "spying")
CERT_ID = "act34-common-zero-billed-controls-v1"
CONTROL_SET = "act34-free-dispatch-controls-v1"
GATE_ID = "act34-economy-free-provider-control"
BILL_ID = "act34-ordinary-funding-operations-parity-v3"
BILL_SHA = "5aed6101425568af6111b0bc6a85a85ce5733cae29254f30ccb90db240a109e9"
CERT_REF = "records/economy/act34-control-certification.json"
EVIDENCE_KEY = "act34_control_certification_evidence"
WINDOW = 45 * 86400
REVIEW = 48 * 3600
SHA_RE = re.compile(r"[0-9a-f]{64}")
COMMIT_RE = re.compile(r"[0-9a-f]{7,40}")
SNAPSHOT_RE = re.compile(r"records/economy/evidence/[A-Za-z0-9_.-]+[.]json")
CONTROL_KEYS = (
    "wrapper_sha256", "negative_test_sha256", "bounds_sha256",
    "zero_billed_policy_sha256", "zero_billed_verifier_sha256",
    "gate_sha256", "cycle_sha256", "provider_snapshot_sha256",
)


def fail(reason):
    print("Act34 certified HOLD: " + str(reason)[:300], file=sys.stderr)
    return 1


def sha(data):
    return hashlib.sha256(data).hexdigest()


def committed(root, rel):
    """Current working bytes must be exactly the current committed bytes."""
    path = root / rel
    raw = path.read_bytes()
    head = subprocess.run(["git", "-C", str(root), "show", "HEAD:" + rel],
                          check=True, capture_output=True, timeout=8).stdout
    if raw != head:
        raise ValueError("unreviewed working bytes: " + rel)
    return sha(raw)


def load_json(root, rel):
    return json.loads((root / rel).read_text(encoding="utf-8"))


def enacted_parity_act(laws):
    """Find the one genuinely codified parity-v3 Act; never hardcode its number.

    Real Act 31 codification carries an ``Enacts: BILL`` trailer and the exact
    balloted SHA inside the enacted Act section. A bare heading, a filed bill or
    a different bill id is not codification.
    """
    pattern = re.compile(
        r"(?ms)^## Act (\d+) — [^\n]*\(enacted [^\n]*\)\n(.*?)(?=^## Act |\Z)")
    found = []
    for match in pattern.finditer(laws):
        body = match.group(2)
        trailer = re.search(r"(?m)Enacts:\s*" + BILL_ID + r"\b", body)
        if trailer and BILL_SHA in body:
            found.append(int(match.group(1)))
    if len(found) != 1:
        raise ValueError("exactly one genuine parity-v3 codification required")
    return found[0]


def rejected_ids(root):
    """Read the exact vector from the committed legacy verifier source by AST.

    The vector is data, not executable code; literal_eval avoids importing or
    trusting a changed implementation while binding to reviewed bytes.
    """
    source = (root / "government/knowledge-zero-billed.py").read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef) and node.name == "negative_acceptance_digest":
            for stmt in node.body:
                if (isinstance(stmt, ast.Assign) and
                        any(isinstance(t, ast.Name) and t.id == "names" for t in stmt.targets)):
                    value = ast.literal_eval(stmt.value)
                    if not isinstance(value, (list, tuple)) or not value:
                        raise ValueError("empty rejected-ID vector")
                    return list(value)
    raise ValueError("rejected-ID vector not found in reviewed verifier")


def stable_policy_digest(policy, ids):
    """Parsed, key-sorted policy fields + rejected vector; never raw bytes."""
    parsed = {key: policy.get(key)
              for key in ("models", "source", "go_source", "review_after")}
    if (not isinstance(parsed["models"], dict) or not parsed["models"]
            or not isinstance(parsed["source"], dict)
            or not isinstance(parsed["go_source"], dict)
            or not isinstance(parsed["review_after"], str)):
        raise ValueError("zero-billed policy parsed fields missing")
    payload = {"rejected_ids": list(ids), "policy": parsed}
    return sha(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False).encode("utf-8"))


def control_paths(policy):
    """Eight controls; snapshot paths come from the current policy, never hardcoded."""
    snapshot = policy.get("snapshot_ref")
    go = policy.get("go_source")
    go_ref = go.get("snapshot_ref") if isinstance(go, dict) else None
    for ref in (snapshot, go_ref):
        if (not isinstance(ref, str) or not SNAPSHOT_RE.fullmatch(ref)
                or ".." in Path(ref).parts):
            raise ValueError("invalid dynamic provider snapshot reference")
    return {
        "wrapper_sha256": "government/knowledge-free-dispatch.sh",
        "negative_test_sha256": "tests/knowledge-free-dispatch-smoke.sh",
        "bounds_sha256": "government/knowledge-practical-bounds.py",
        "zero_billed_policy_sha256": "government/knowledge-zero-billed-policy.json",
        "zero_billed_verifier_sha256": "government/knowledge-zero-billed.py",
        "gate_sha256": "government/knowledge-act34-certified-gate.py",
        "cycle_sha256": "government/knowledge-office-cycle.sh",
        "provider_snapshot_sha256": snapshot,
    }, go_ref


def control_digest(hashes):
    return sha(json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("verifier module unavailable: " + str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def attest(root, role, officer, ref, commit, digest, attestation, gate_id):
    """Existing multi-channel officer-action check, inline and commit-bound."""
    if not isinstance(commit, str) or not COMMIT_RE.fullmatch(commit):
        raise ValueError("origin commit missing")
    if committed(root, ref) != digest:
        raise ValueError("artifact digest differs from committed bytes")
    at_commit = subprocess.run(
        ["git", "-C", str(root), "show", commit + ":" + ref],
        check=True, capture_output=True, timeout=8).stdout
    if sha(at_commit) != digest:
        raise ValueError("origin commit does not contain reviewed artifact")
    if os.environ.get("VICHE_PHASE_ATTESTATION_JSON") and not str(root).startswith("/tmp/"):
        raise ValueError("production cannot accept offline caller approval")
    verifier = module(root / "government/knowledge-phase-verifier.py", "act34_cert_phase")
    errors = verifier.Verifier(str(root)).validate_attestation(
        attestation, gate_id=gate_id, officer_id=officer, role=role,
        artifact_commit=commit, historical=True)
    if errors:
        raise ValueError("unverified %s action: %s" % (role, "; ".join(errors)[:250]))


def tracked(root, rel):
    """Absence on disk is not absence from the committed authority."""
    listing = subprocess.run(
        ["git", "-C", str(root), "ls-tree", "-z", "HEAD", "--", rel],
        check=True, capture_output=True, timeout=8).stdout
    return bool(listing)


def prior_deleted_review(root, rel, permit_sha):
    # A committed deletion is not a new after-start window for the same
    # permit. Check the last first-parent deletion, not arbitrary reflogs.
    deletion = subprocess.run(
        ["git", "-C", str(root), "log", "--first-parent", "--no-renames",
         "--diff-filter=D", "-1", "--format=%H", "HEAD", "--", rel],
        check=True, capture_output=True, text=True, timeout=8).stdout.strip()
    if not deletion:
        return False
    raw = subprocess.run(
        ["git", "-C", str(root), "show", deletion + "^:" + rel],
        check=True, capture_output=True, timeout=8).stdout
    old = json.loads(raw)
    if not isinstance(old, dict) or not isinstance(old.get("permit_sha256"), str):
        raise ValueError("deleted historical Judiciary evidence unreadable")
    return old["permit_sha256"] == permit_sha


def legacy_checks(root, office, a, permit, permit_sha, start, now):
    """Keep Executive, Judiciary and Spying checks; no HOLD bypass or clock reset."""
    attest(root, "executive", "c1e00002", a.get("permit_ref"),
           a.get("permit_origin_commit"), permit_sha, a.get("permit_attestation"),
           "act34-executive-" + office)
    review_rel = "records/knowledge/pilot-reviews/%s.json" % office
    auth_rel = "records/knowledge/pilot-reviews/%s-attestation.json" % office
    review_path, auth_path = root / review_rel, root / auth_rel
    review_tracked, auth_tracked = tracked(root, review_rel), tracked(root, auth_rel)
    if review_tracked or auth_tracked or review_path.exists() or auth_path.exists():
        if not (review_tracked and auth_tracked and review_path.is_file() and auth_path.is_file()):
            raise ValueError("committed Judiciary disposition or attestation missing")
        review_sha = committed(root, review_rel)
        rev = load_json(root, review_rel)
        reviewed = rev.get("reviewed_at")
        if (rev.get("schema") != "viche-act34-judiciary-review-v1"
                or rev.get("office") != office or rev.get("reviewer") != "c1e00008"
                or rev.get("permit_sha256") != permit_sha or type(reviewed) is not int
                or not start <= reviewed < start + REVIEW or reviewed > now):
            raise ValueError("uncorroborated or stale Judiciary disposition")
        committed(root, auth_rel)
        auth = load_json(root, auth_rel)
        attest(root, "judiciary", "c1e00008", review_rel,
               auth.get("artifact_commit"), review_sha, auth.get("attestation"),
               "act34-judiciary-" + office)
        if rev.get("decision") != "proceed":
            raise ValueError("Judiciary HOLD/STOP")
    else:
        if prior_deleted_review(root, review_rel, permit_sha):
            raise ValueError("same-permit Judiciary disposition was deleted")
        if now >= start + REVIEW:
            raise ValueError("Judiciary review missing 48h after original permit start")
    if office == "spying" and not (root / "records/knowledge/spying-source-scope.json").is_file():
        raise ValueError("Spying source-scope bundle absent")


def check(office, root):
    if office not in OFFICES:
        raise ValueError("unknown office")
    laws_rel = "government/LAWS.md"
    committed(root, laws_rel)
    laws = (root / laws_rel).read_text(encoding="utf-8")
    enacted_parity_act(laws)  # exact codification, no arbitrary Act number
    if not re.search(
            r"(?m)^## Act 34 — Rapid Full Institutional Activation and Continuous Improvement Act \(enacted ",
            laws):
        raise ValueError("Act34 authority is absent; parity does not renumber authority")
    if committed(root, "records/bills/" + BILL_ID + ".md") != BILL_SHA:
        raise ValueError("filed v3 bill bytes differ from the enacted SHA")
    # The certified gate itself and the legacy helpers it reuses must be reviewed bytes.
    self_digest = sha(Path(__file__).read_bytes())
    if committed(root, "government/knowledge-act34-certified-gate.py") != self_digest:
        raise ValueError("running gate bytes differ from committed gate")
    for rel in ("government/knowledge-act34-gate.py",
                "government/knowledge-phase-verifier.py",
                "government/knowledge-zero-billed.py"):
        committed(root, rel)

    activation_rel = "records/knowledge/activation.json"
    committed(root, activation_rel)
    activation = load_json(root, activation_rel)
    a = activation.get("offices", {}).get(office, {})
    permit_rel = "records/knowledge/permits/" + office + ".json"
    permit_sha = committed(root, permit_rel)
    permit = load_json(root, permit_rel)
    budget_rel = "government/knowledge-budget.conf"
    budget_sha = committed(root, budget_rel)
    cfg = load_json(root, budget_rel)
    caps = cfg.get("offices", {}).get(office, {})
    now = int(time.time())
    start, expires = a.get("not_before"), a.get("expires_at")
    # The ordinary amendment does NOT renumber authority or change the office mode.
    if (activation.get("schema") != "viche-knowledge-activation-v1"
            or a.get("enabled") is not True or a.get("authorized_by") != "act:34:" + office
            or a.get("trial_mode") != "adaptive-v1" or a.get("signer") != "c1e00002"
            or type(start) is not int or type(expires) is not int
            or not start <= now < expires or not 0 < expires - start <= WINDOW
            or a.get("permit_ref") != permit_rel or a.get("permit_sha256") != permit_sha):
        raise ValueError("missing, expired or wrong-identity activation")
    if (caps.get("enabled") is not True
            or permit.get("schema") != "viche-act34-operating-permit-v1"
            or permit.get("office") != office or permit.get("signer") != "c1e00002"
            or permit.get("authorized_by") != "act:34:" + office
            or permit.get("not_before") != start or permit.get("expires_at") != expires
            or permit.get("budget_sha256") != budget_sha or permit.get("caps") != caps.get("caps")
            or permit.get("per_run_caps") != caps.get("per_run_caps", caps.get("caps"))
            or permit.get("host") != socket.gethostname()
            or permit.get("mission_source") != "government/KNOWLEDGE-OFFICES.md -> " + office
            or permit.get("signature_status") != "signed"
            or permit.get("provider_budget_mode") != "zero-billed-runtime-allowlist"
            or permit.get("provider_tier") != "free_only"
            or permit.get("inflight_overrun_risk_disclosed") is not True
            or permit.get("cancellation") != "stop-agent-and-hold-budget"
            or permit.get("reboot_recovery") != "reconcile-held-liability"):
        raise ValueError("permit is not bound to the real Executive budget/authority")
    if permit.get("control_certification") != {
            "certification_id": CERT_ID, "control_set": CONTROL_SET,
            "ref": CERT_REF, "gate_id": GATE_ID}:
        raise ValueError("permit did not explicitly choose this certified route")

    cert_sha = committed(root, CERT_REF)
    cert = load_json(root, CERT_REF)
    if (cert.get("schema") != "viche-act34-control-certification-v1"
            or cert.get("certification_id") != CERT_ID or cert.get("control_set") != CONTROL_SET
            or cert.get("gate_id") != GATE_ID or type(cert.get("not_before")) is not int
            or type(cert.get("expires_at")) is not int
            or not cert["not_before"] <= now < cert["expires_at"]):
        raise ValueError("certification identity or validity window invalid")
    policy_rel = "government/knowledge-zero-billed-policy.json"
    committed(root, policy_rel)
    policy = load_json(root, policy_rel)
    paths, go_ref = control_paths(policy)
    actual = {key: committed(root, rel) for key, rel in paths.items()}
    if set(actual) != set(CONTROL_KEYS) or cert.get("controls") != actual:
        raise ValueError("certified control bytes differ from committed controls")
    if actual["gate_sha256"] != self_digest:
        raise ValueError("certified gate control is not this executable")
    if cert.get("control_digest") != control_digest(actual):
        raise ValueError("control-set digest mismatch")

    # Dynamic snapshots: both the provider and the Go endpoint are verified.
    snapshot_ref = paths["provider_snapshot_sha256"]
    if committed(root, snapshot_ref) != policy.get("snapshot_sha256") or policy.get("snapshot_sha256") != policy["source"].get("sha256"):
        raise ValueError("provider snapshot bytes/source digest mismatch")
    if committed(root, go_ref) != policy["go_source"].get("sha256"):
        raise ValueError("Go snapshot bytes/source digest mismatch")
    zb = module(root / "government/knowledge-zero-billed.py", "act34_cert_zero")
    zb.load_verified(root / policy_rel, snapshot_path=root / snapshot_ref)
    allowed = zb.authorized_models(zb.global_config_path())
    subset = zb.verified_subset(root / policy_rel, allowed, snapshot_path=root / snapshot_ref)
    if not subset or any(mid not in allowed for mid in subset):
        raise ValueError("exact verified zero-cost/provider privacy subset absent")

    expected_policy = stable_policy_digest(policy, rejected_ids(root))
    if (cert.get("policy_digest") != expected_policy
            or permit.get("negative_acceptance_digest") != expected_policy):
        raise ValueError("policy digest differs from parsed policy/rejected vector")

    # Certification evidence lives outside the certification record and outside
    # the untouched legacy Economy evidence field; no self-referential hash.
    evidence = activation.get(EVIDENCE_KEY)
    ordinary_evidence = activation.get("economy_free_tier_evidence")
    # During mixed legacy/certified migration retain the legacy report.
    # Once migrated, accept the canonical field expressly named in v3.
    if isinstance(ordinary_evidence, dict) and "certification_ref" in ordinary_evidence:
        if evidence is not None and evidence != ordinary_evidence:
            raise ValueError("conflicting shared certification evidence")
        evidence = ordinary_evidence
    if (not isinstance(evidence, dict)
            or evidence.get("certification_ref") != CERT_REF
            or evidence.get("certification_sha256") != cert_sha):
        raise ValueError("separate certification evidence missing or stale")
    attest(root, "economy", "c1e00012", CERT_REF,
           evidence.get("certification_origin_commit"), cert_sha,
           evidence.get("attestation"), GATE_ID)
    legacy_checks(root, office, a, permit, permit_sha, start, now)


def main():
    if len(sys.argv) != 3:
        return fail("usage: knowledge-act34-certified-gate.py OFFICE TOWN_ROOT")
    try:
        check(sys.argv[1], Path(sys.argv[2]).resolve())
        return 0
    except Exception as exc:
        return fail(exc)


if __name__ == "__main__":
    raise SystemExit(main())

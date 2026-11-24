#!/usr/bin/env python3
"""Hermetic /tmp fixture builder for the certified Act34 parity-v3 smoke test.

Everything created here is synthetic and lives under a caller-supplied temp
directory. It creates no permit, attestation, board action, law or certification
in the live town. Real repository files are copied as source code; the enacted
Act section is a synthetic codification used only to exercise the verifier.
"""
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

OFFICES = ("statistics", "foresight", "strategy", "spying")
BILL = "act34-ordinary-funding-operations-parity-v3"
BILL_SHA = "5aed6101425568af6111b0bc6a85a85ce5733cae29254f30ccb90db240a109e9"
GOV_FILES = (
    "knowledge-act34-gate.py", "knowledge-phase-verifier.py",
    "knowledge-activation-verify.sh", "knowledge-budget.conf",
    "knowledge-free-dispatch.sh", "knowledge-practical-bounds.py",
    "knowledge-zero-billed.py", "knowledge-zero-billed-policy.json",
    "knowledge-office-cycle.sh", "knowledge-act34-certified-gate.py",
)
GOV_DIR = "government"
CERT_REF = "records/economy/act34-control-certification.json"
EVIDENCE_KEY = "act34_control_certification_evidence"
CERT_ID = "act34-common-zero-billed-controls-v1"
CONTROL_SET = "act34-free-dispatch-controls-v1"
GATE_ID = "act34-economy-free-provider-control"
AT = "2026-11-24T00:10:00Z"
AT1 = "2026-11-24T00:10:01Z"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def put(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True, timeout=30).stdout.decode().strip()


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def board(state, issue, reviewer, gate, commit):
    put(state / "board" / (issue + ".json"), {
        "review": {"commit": commit, "verdict": "approve", "reviewer": reviewer,
                   "recordedAt": AT},
        "messages": [{"author": reviewer, "body": gate + " " + commit + " reviewed",
                      "createdAt": AT1}],
    })


def recompute(root, gate, policy, cert, now):
    paths, go_ref = gate.control_paths(policy)
    actual = {key: sha((root / rel).read_bytes()) for key, rel in paths.items()}
    cert["controls"] = actual
    cert["control_digest"] = gate.control_digest(actual)
    cert["not_before"], cert["expires_at"] = now - 60, now + 86400
    return cert


def build(repo, town, state, variant="valid"):
    """Create a complete synthetic town and return a small facts dictionary."""
    repo, town, state = Path(repo), Path(town), Path(state)
    for path in (town / GOV_DIR, town / "tests", town / "records/knowledge/permits",
                 town / "records/knowledge/pilot-reviews", town / "records/economy/evidence",
                 town / "records/bills", state / "board", state / "appointments"):
        path.mkdir(parents=True, exist_ok=True)
    for name in GOV_FILES:
        shutil.copy2(repo / GOV_DIR / name, town / GOV_DIR / name)
    shutil.copy2(repo / "tests/knowledge-free-dispatch-smoke.sh",
                 town / "tests/knowledge-free-dispatch-smoke.sh")
    shutil.copy2(repo / "records/bills" / (BILL + ".md"), town / "records/bills" / (BILL + ".md"))
    for name in ("2026-11-24-provider-models.json", "2026-11-24-go-provider-models.json"):
        shutil.copy2(repo / "records/economy/evidence" / name, town / "records/economy/evidence" / name)

    laws = ("## Act 32 — Institutional Knowledge and Communications Act (enacted 2026-11-20)\n"
            "## Act 34 — Rapid Full Institutional Activation and Continuous Improvement Act "
            "(enacted 2026-11-23)\n")
    if variant != "pre-enactment":
        laws += ("\n## Act 35 — Knowledge Offices Ordinary Funding and Operations Parity Act 2026 "
                 "(enacted 2026-11-24, synthetic fixture)\n\n"
                 "Enacts: " + BILL + "\nsha256 " + BILL_SHA + "\n")
    (town / "government/LAWS.md").write_text(laws, encoding="utf-8")
    (town / "government/branch-officers.tsv").write_text(
        "executive\tc1e00002\tExecutive\neconomy\tc1e00012\tMinistry of Economy\n"
        "judiciary\tc1e00008\tJudiciary\n", encoding="utf-8")

    budget = read(town / "government/knowledge-budget.conf")
    for office in OFFICES:
        budget["offices"][office]["enabled"] = True
    put(town / "government/knowledge-budget.conf", budget)

    policy = read(town / "government/knowledge-zero-billed-policy.json")
    policy["source"]["retrieved_at"] = "2026-11-24T00:00:00Z"
    policy["go_source"]["retrieved_at"] = "2026-11-24T00:00:00Z"
    policy["review_after"] = "2099-01-01T00:00:00Z"  # hermetic, never expires mid-test
    put(town / "government/knowledge-zero-billed-policy.json", policy)

    gate = load_module(town / "government/knowledge-act34-certified-gate.py", "certgate_" + variant)
    ids = gate.rejected_ids(town)
    policy_digest = gate.stable_policy_digest(policy, ids)
    original_policy_digest = policy_digest
    if variant == "policy-digest":
        # The admitted policy changes, but the permit keeps the old stable
        # binding: the new certification must not silently rebind old permits.
        policy["source"]["note"] = "changed endpoint/scope note (synthetic policy change)"
        put(town / "government/knowledge-zero-billed-policy.json", policy)
        policy_digest = gate.stable_policy_digest(policy, ids)
    (town / "records/knowledge/spying-source-scope.json").write_text(
        '{"fixture": "authorized public sources"}\n', encoding="utf-8")
    report = town / "records/economy/2026-11-24-act34-fresh-verification.md"
    report.write_text("Synthetic Economy exact-path verification fixture.\n", encoding="utf-8")

    now = int(os.environ.get("ACT34_FIXTURE_NOW", str(int(time.time()))))
    start, expires = now - 120, now + 14 * 86400
    cert = {
        "schema": "viche-act34-control-certification-v1",
        "certification_id": CERT_ID, "control_set": CONTROL_SET,
        "gate_id": GATE_ID, "not_before": now - 60, "expires_at": now + 86400,
        "policy_digest": policy_digest,
    }
    cert = recompute(town, gate, policy, cert, now)
    if variant == "stale-cert":
        cert["expires_at"] = now - 1
    if variant != "missing-cert":
        put(town / CERT_REF, cert)

    budget_sha = sha((town / "government/knowledge-budget.conf").read_bytes())
    rows, permits = {}, {}
    for office in OFFICES:
        effective_start = now - 49 * 3600 if variant == "no-review-48h" else start
        permit = {
            "schema": "viche-act34-operating-permit-v1", "office": office,
            "signer": "c1e00099" if variant == "wrong-signer" else "c1e00002",
            "authorized_by": ("act:35:" + office if variant == "wrong-identity"
                              else "act:34:" + office),
            "not_before": effective_start, "expires_at": expires,
            "budget_sha256": budget_sha,
            "caps": (dict(budget["offices"][office]["caps"], tokens_total=1)
                     if variant == "wrong-caps" else budget["offices"][office]["caps"]),
            "provider_budget_mode": "zero-billed-runtime-allowlist",
            "provider_tier": "free_only", "signature_status": "signed",
            "inflight_overrun_risk_disclosed": True,
            "control_certification": {"certification_id": CERT_ID, "control_set": CONTROL_SET,
                                      "ref": CERT_REF, "gate_id": GATE_ID},
            # A policy change must invalidate this stable binding.
            "negative_acceptance_digest": (original_policy_digest
                                           if variant == "policy-digest" else policy_digest),
            "cancellation": "stop-agent-and-hold-budget",
            "reboot_recovery": "reconcile-held-liability",
        }
        ref = "records/knowledge/permits/" + office + ".json"
        put(town / ref, permit)
        permits[office] = sha((town / ref).read_bytes())
        rows[office] = {
            "enabled": True, "authorized_by": ("act:35:" + office if variant == "wrong-identity"
                                               else "act:34:" + office),
            "trial_mode": "adaptive-v1", "signer": "c1e00002",
            "not_before": effective_start, "expires_at": expires,
            "permit_ref": ref, "permit_sha256": permits[office],
        }
        if variant != "no-review-48h":
            put(town / "records/knowledge/pilot-reviews" / (office + ".json"), {
                "schema": "viche-act34-judiciary-review-v1", "office": office,
                "reviewer": "c1e00008", "permit_sha256": permits[office],
                "decision": "hold" if variant == "hold" else "proceed",
                "reviewed_at": effective_start + 10,
            })
            put(town / "records/knowledge/pilot-reviews" / (office + "-attestation.json"),
                {"placeholder": "filled after origin commit"})

    # Untouched legacy Economy evidence: the certified path must ignore it.
    activation = {
        "schema": "viche-knowledge-activation-v1", "offices": rows,
        "economy_free_tier_evidence": {
            "report_ref": "records/economy/2026-11-24-act34-fresh-verification.md",
            "artifact_commit": "0" * 40,
            "report_sha256": sha(report.read_bytes()),
            "sentinel": "legacy evidence MUST NOT be modified by certified path",
            "attestation": {"issue_id": "economy-test-issue", "expected_reviewer": "c1e00012",
                            "officer_agent_id": "econ-agent"},
        },
        EVIDENCE_KEY: {
            "certification_ref": CERT_REF,
            "certification_sha256": sha((town / CERT_REF).read_bytes()) if (town / CERT_REF).exists() else "0" * 64,
            "certification_origin_commit": "0" * 40,
            "attestation": {"issue_id": "economy-cert-issue", "expected_reviewer": "c1e00012",
                            "officer_agent_id": "econ-agent"},
        },
    }
    put(town / "records/knowledge/activation.json", activation)
    (state / "appointments/appointments.tsv").write_text(
        "executive\texec-agent\neconomy\tecon-agent\njudiciary\tjud-agent\n", encoding="utf-8")
    (state / "appointments/appointments.log").write_text(
        "2026-11-22T00:00:00Z\texecutive\t-\texec-agent\n"
        "2026-11-22T00:00:00Z\teconomy\t-\tecon-agent\n"
        "2026-11-22T00:00:00Z\tjudiciary\t-\tjud-agent\n", encoding="utf-8")
    (Path(state).parent / "global/antonina").mkdir(parents=True, exist_ok=True)
    (Path(state).parent / "global/antonina/config.json").write_text(json.dumps({"models": [
        {"model": "opencode-go/hy4-flash-free", "comment": "fixture", "variant": "low"},
        {"model": "opencode/hy4-flash-free", "comment": "fixture", "variant": "low"}]}), encoding="utf-8")

    git(town, "init", "-q")
    git(town, "config", "user.name", "Certified parity fixture")
    git(town, "config", "user.email", "fixture@example.invalid")
    git(town, "add", ".")
    git(town, "commit", "-qm", "Synthetic base permits and controls")
    origin = git(town, "rev-parse", "HEAD")

    # The first commitment fixes the artifact bytes that officer actions attest.
    anchor = origin
    # Second commitment records the attestation references to that real commit.
    activation = read(town / "records/knowledge/activation.json")
    for office in OFFICES:
        activation["offices"][office]["permit_origin_commit"] = anchor
        activation["offices"][office]["permit_attestation"] = {
            "issue_id": "executive-" + office + "-issue", "expected_reviewer": "c1e00002",
            "officer_agent_id": "exec-agent"}
        auth_path = town / "records/knowledge/pilot-reviews" / (office + "-attestation.json")
        if auth_path.exists():
            put(auth_path, {"artifact_commit": anchor, "attestation": {
                "issue_id": "judiciary-" + office + "-issue", "expected_reviewer": "c1e00008",
                "officer_agent_id": "jud-agent"}})
    if (town / CERT_REF).exists():
        activation[EVIDENCE_KEY]["certification_sha256"] = sha((town / CERT_REF).read_bytes())
    activation[EVIDENCE_KEY]["certification_origin_commit"] = anchor
    put(town / "records/knowledge/activation.json", activation)
    git(town, "add", ".")
    git(town, "commit", "-qm", "Synthetic officer attestation anchors")
    attest_commit = git(town, "rev-parse", "HEAD")

    for office in OFFICES:
        board(state, "executive-" + office + "-issue", "c1e00002",
              "act34-executive-" + office, anchor)
        board(state, "judiciary-" + office + "-issue", "c1e00008",
              "act34-judiciary-" + office, anchor)
    board(state, "economy-cert-issue", "c1e00012", GATE_ID, anchor)
    if variant == "forged-board":
        issue = read(state / "board/economy-cert-issue.json")
        issue["review"]["verdict"] = "reject"
        put(state / "board/economy-cert-issue.json", issue)
    if variant == "policy-bytes":
        # Genuinely committed policy change while the certification is stale.
        policy = read(town / "government/knowledge-zero-billed-policy.json")
        policy["models"]["opencode/hy4-flash-free"]["cost"]["input"] = 1
        put(town / "government/knowledge-zero-billed-policy.json", policy)
        git(town, "add", ".")
        git(town, "commit", "-qm", "Synthetic committed policy change")

    if variant == "repair":
        # Comment-only repair of one bound control; one Economy refresh; no
        # permit bytes change. This is the core v3 operational requirement.
        bounds = town / "government/knowledge-practical-bounds.py"
        bounds.write_text(bounds.read_text(encoding="utf-8") + "\n# semantics-preserving repair\n",
                          encoding="utf-8")
        policy = read(town / "government/knowledge-zero-billed-policy.json")
        cert = recompute(town, gate, policy, cert, int(time.time()))
        put(town / CERT_REF, cert)
        activation = read(town / "records/knowledge/activation.json")
        activation[EVIDENCE_KEY]["certification_sha256"] = sha((town / CERT_REF).read_bytes())
        activation[EVIDENCE_KEY]["certification_origin_commit"] = "pending"
        put(town / "records/knowledge/activation.json", activation)
        git(town, "add", ".")
        git(town, "commit", "-qm", "Synthetic one-refresh comment-only repair")
        repair_commit = git(town, "rev-parse", "HEAD")
        activation = read(town / "records/knowledge/activation.json")
        activation[EVIDENCE_KEY]["certification_origin_commit"] = repair_commit
        put(town / "records/knowledge/activation.json", activation)
        git(town, "add", ".")
        git(town, "commit", "-qm", "Synthetic refreshed certification evidence anchor")
        board(state, "economy-cert-issue", "c1e00012", GATE_ID, repair_commit)
    else:
        repair_commit = None

    return {"permits": permits, "origin": origin, "attest_commit": attest_commit,
            "repair_commit": repair_commit,
            "legacy_evidence": read(town / "records/knowledge/activation.json")["economy_free_tier_evidence"]}


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit("usage: fixture.py REPO TOWN STATE VARIANT")
    result = build(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    print(json.dumps({"permits": result["permits"], "origin_commit": result["origin"],
                      "attest_commit": result["attest_commit"],
                      "repair_commit": result["repair_commit"],
                      "legacy_evidence": result["legacy_evidence"]}))

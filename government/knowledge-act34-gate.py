#!/usr/bin/env python3
"""Act34 broad adaptive office authorization, no first-sample or value gate.

Enactment + reviewed written Executive permit + actual Economy config must be
valid before a model-using office dispatches. Judiciary inspects real work
WITHIN 48h after start, and any HOLD/STOP blocks immediately. The gate itself
is pure: no model, bills, file writes or mutable session side-effects.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

sys.dont_write_bytecode = True

OFFICES = ("statistics", "foresight", "strategy", "spying")
TITLE = "## Act 34 — Rapid Full Institutional Activation and Continuous Improvement Act (enacted "
WINDOW = 45 * 86400
REVIEW = 48 * 3600


def fail(reason):
    print("Act34 %s: HOLD: %s" % (sys.argv[1] if len(sys.argv) > 1 else "?", reason),
          file=sys.stderr)
    return 1


def load(path):
    return json.loads(path.read_text())


def on_main(root, path):
    rel = path.relative_to(root).as_posix()
    actual = path.read_bytes()
    committed = subprocess.run(["git", "-C", str(root), "show", "HEAD:" + rel],
                               check=True, capture_output=True, timeout=8).stdout
    if hashlib.sha256(actual).digest() != hashlib.sha256(committed).digest():
        raise ValueError("unreviewed canonical bytes: " + rel)
    return hashlib.sha256(actual).hexdigest()


def source_commit(root, ref, commit, expected_sha):
    """Match the office-authored Git object to the reviewed current bytes."""
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{7,40}", commit):
        raise ValueError("no verifiable original officer source commit")
    path = root / ref
    current = on_main(root, path)
    if current != expected_sha:
        raise ValueError("current officer artifact digest differs")
    blob = subprocess.run(
        ["git", "-C", str(root), "show", commit + ":" + ref],
        check=True, capture_output=True, timeout=8).stdout
    if hashlib.sha256(blob).hexdigest() != current:
        raise ValueError("original officer commit and reviewed main differ")
    return current


def institutionally_attested(root, role, officer, ref, commit, digest,
                             attestation, gate_id):
    """Act32's existing genuine multi-channel officer authenticity check.

    This is attribution of Executive/Economy/Judiciary ACTUAL actions, not
    pre-launch Judiciary efficacy certification or a serial trial gate.
    A self-labelled JSON signer is NEVER a signature on shared UID.
    """
    source_commit(root, ref, commit, digest)
    if os.environ.get("VICHE_PHASE_ATTESTATION_JSON") and not str(root).startswith("/tmp/"):
        raise ValueError("production must not accept caller-provided offline approval")
    module = root / "government/knowledge-phase-verifier.py"
    on_main(root, module)
    spec = importlib.util.spec_from_file_location("act34_phase_verifier", module)
    if spec is None or spec.loader is None:
        raise ValueError("independent institutional verifier unavailable")
    vmod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vmod)
    errors = vmod.Verifier(str(root)).validate_attestation(
        attestation, gate_id=gate_id, officer_id=officer,
        role=role, artifact_commit=commit)
    if errors:
        raise ValueError("unverified " + role + " action: " + "; ".join(errors)[:320])


def require_audited_free_tier(root, record, permit):
    """Only a verified FREE provider route has a demonstrated $0 exposure.

    Model tokens still count against Economy's cumulative budget. Stop-on-
    detection is NOT a hard in-flight token cap, and cannot license paid models.
    """
    mode = permit.get("provider_budget_mode")
    if (mode != "zero-billed-runtime-allowlist" or
            permit.get("inflight_overrun_risk_disclosed") is not True or
            permit.get("provider_tier") != "free_only"):
        raise ValueError("paid/unknown providers held; audited free tier only")
    evidence = record.get("economy_free_tier_evidence")
    if not isinstance(evidence, dict):
        raise ValueError("independent Economy model-source control missing")
    report_ref = "records/economy/2026-11-24-act34-zero-billed-verification.md"
    institutionally_attested(
        root, "economy", "c1e00012", report_ref,
        evidence.get("artifact_commit"), evidence.get("report_sha256"),
        evidence.get("attestation"), "act34-economy-free-provider-control")
    controls = (
        ("wrapper_sha256", "government/knowledge-free-dispatch.sh"),
        ("negative_test_sha256", "tests/knowledge-free-dispatch-smoke.sh"),
        ("bounds_sha256", "government/knowledge-practical-bounds.py"),
        ("zero_billed_policy_sha256", "government/knowledge-zero-billed-policy.json"),
        ("zero_billed_verifier_sha256", "government/knowledge-zero-billed.py"),
        ("gate_sha256", "government/knowledge-act34-gate.py"),
        ("cycle_sha256", "government/knowledge-office-cycle.sh"))
    for key, rel in controls:
        if evidence.get(key) != on_main(root, root / rel):
            raise ValueError("unverified Economy runtime control: " + rel)
    if not isinstance(evidence.get("negative_acceptance_digest"), str) or not re.fullmatch(
            r"[0-9a-f]{64}", evidence["negative_acceptance_digest"]):
        raise ValueError("negative-acceptance digest missing")
    # Exact provider/model cost evidence, not the name-derived rotation tier,
    # decides whether the live policy is admissible. The shared verifier also
    # enforces the evidence freshness deadline.
    module = root / "government/knowledge-zero-billed.py"
    spec = importlib.util.spec_from_file_location("act34_zero_billed", module)
    if spec is None or spec.loader is None:
        raise ValueError("zero-billed policy verifier unavailable")
    zmod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(zmod)
    state = Path(os.environ.get("VICHE_STATE_ROOT", "/var/lib/lubko/wd/viche-state"))
    policy = load(state / "economy/model-policy.json")
    cat = load(state / "economy/catalogue.json")
    models = cat.get("models") if isinstance(cat, dict) else None
    allowed = policy.get("prefer") if isinstance(policy, dict) else None
    if not isinstance(models, dict) or not isinstance(allowed, list) or not allowed:
        raise ValueError("free-tier policy/catalogue unavailable")
    zmod.verified_subset(root / "government/knowledge-zero-billed-policy.json", allowed, models)
    expected_digest = zmod.negative_acceptance_digest({
        "wrapper": root / "government/knowledge-free-dispatch.sh",
        "zero_billed_policy": root / "government/knowledge-zero-billed-policy.json",
        "bounds": root / "government/knowledge-practical-bounds.py",
        "negative_test": root / "tests/knowledge-free-dispatch-smoke.sh",
        "verifier": root / "government/knowledge-zero-billed.py",
        "gate": root / "government/knowledge-act34-gate.py",
        "cycle": root / "government/knowledge-office-cycle.sh"})
    if evidence.get("negative_acceptance_digest") != expected_digest:
        raise ValueError("negative-acceptance digest differs from exact controls")


def check(office, root):
    if office not in OFFICES:
        raise ValueError("unknown office")
    laws = (root / "government/LAWS.md").read_text()
    if sum(line.startswith(TITLE) for line in laws.splitlines()) != 1:
        raise ValueError("exactly one enacted Act34 required")
    on_main(root, root / "government/LAWS.md")
    activation = root / "records/knowledge/activation.json"
    budget = root / "government/knowledge-budget.conf"
    on_main(root, activation)
    budget_hash = on_main(root, budget)
    record = load(activation)
    if record.get("schema") != "viche-knowledge-activation-v1":
        raise ValueError("malformed activation schema")
    a = record.get("offices", {}).get(office, {})
    now = int(time.time())
    values = (a.get("not_before"), a.get("expires_at"))
    if (a.get("enabled") is not True or a.get("authorized_by") != "act:34:" + office
            or a.get("trial_mode") != "adaptive-v1" or a.get("signer") != "c1e00002"
            or any(type(x) is not int for x in values)
            or not values[0] <= now < values[1]
            or not 0 < values[1] - values[0] <= WINDOW):
        raise ValueError("missing/expired Executive adaptive office permit")
    ref = a.get("permit_ref")
    if not isinstance(ref, str) or not re.fullmatch(
            r"records/knowledge/permits/(statistics|foresight|strategy|spying)[.]json", ref):
        raise ValueError("operating permit ref missing or malformed")
    if ref != "records/knowledge/permits/" + office + ".json":
        raise ValueError("permit belongs to another office")
    permit_path = root / ref
    permit_hash = on_main(root, permit_path)
    if a.get("permit_sha256") != permit_hash:
        raise ValueError("written Executive permit digest mismatch")
    permit = load(permit_path)
    cfg = load(budget)
    caps = cfg.get("offices", {}).get(office, {})
    if (caps.get("enabled") is not True
            or permit.get("schema") != "viche-act34-operating-permit-v1"
            or permit.get("office") != office
            or permit.get("signer") != "c1e00002"
            or permit.get("authorized_by") != "act:34:" + office
            or permit.get("not_before") != values[0]
            or permit.get("expires_at") != values[1]
            or permit.get("budget_sha256") != budget_hash
            or permit.get("caps") != caps.get("caps")
            or permit.get("signature_status") != "signed"
            or permit.get("provider_budget_mode") != "zero-billed-runtime-allowlist"
            or permit.get("provider_tier") != "free_only"
            or permit.get("inflight_overrun_risk_disclosed") is not True
            or permit.get("cancellation") != "stop-agent-and-hold-budget"
            or permit.get("reboot_recovery") != "reconcile-held-liability"):
        raise ValueError("Executive permit is not bound to real active Economy budget")
    institutionally_attested(
        root, "executive", "c1e00002", ref, a.get("permit_origin_commit"),
        permit_hash, a.get("permit_attestation"), "act34-executive-" + office)
    require_audited_free_tier(root, record, permit)
    review_path = root / ("records/knowledge/pilot-reviews/" + office + ".json")
    # An early adverse Judiciary decision is immediately binding.
    if review_path.exists():
        on_main(root, review_path)
        rev = load(review_path)
        reviewed = rev.get("reviewed_at")
        if (rev.get("schema") != "viche-act34-judiciary-review-v1"
                or rev.get("office") != office or rev.get("reviewer") != "c1e00008"
                or rev.get("permit_sha256") != permit_hash
                or type(reviewed) is not int
                or not values[0] <= reviewed < values[0] + REVIEW
                or reviewed > now):
            raise ValueError("uncorroborated or stale Judiciary disposition")
        review_auth = root / ("records/knowledge/pilot-reviews/" + office + "-attestation.json")
        on_main(root, review_auth)
        auth = load(review_auth)
        institutionally_attested(
            root, "judiciary", "c1e00008",
            "records/knowledge/pilot-reviews/" + office + ".json",
            auth.get("artifact_commit"), hashlib.sha256(review_path.read_bytes()).hexdigest(),
            auth.get("attestation"), "act34-judiciary-" + office)
        if rev.get("decision") != "proceed":
            raise ValueError("Judiciary HOLD/STOP")
    elif now >= values[0] + REVIEW:
        raise ValueError("Judiciary review missing 48h after initial start")
    if office == "spying":
        # The caller separately runs the source-bundle preflight. A missing
        # bundle is never made a green result by this authorization gate.
        if not (root / "records/knowledge/spying-source-scope.json").is_file():
            raise ValueError("Spying permitted source-scope bundle absent")


def main():
    if len(sys.argv) != 3:
        return fail("usage: knowledge-act34-gate.py OFFICE TOWN_ROOT")
    try:
        check(sys.argv[1], Path(sys.argv[2]).resolve())
        return 0
    except Exception as exc:  # every missing/corrupt institutional channel fails closed
        return fail(str(exc)[:300])


if __name__ == "__main__":
    raise SystemExit(main())

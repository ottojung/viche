#!/usr/bin/env python3
"""Durable cross-branch corrective cases, with evidence-based operational closure.

A case is a monitored obligation, NOT a Judiciary verdict or an authorization
to enact law. Observation and routing remain deterministic even if every model
is down. Existing independent Judiciary/Parliament/Executive powers remain.
"""
import argparse
import hashlib
import json
import os
import pathlib
import stat
import tempfile
import time

ROOT = pathlib.Path(os.environ.get("VICHE_STATE_ROOT", "/var/lib/lubko/wd/viche-state"))
STORE = ROOT / "institutional-cases"


def read(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def atomic(path, item):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".case-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(item, handle, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def continuity_receipt(office):
    """Return the validated case-specific continuity receipt, or None.

    Retained from the continuity workflow: the reconciliation record and the
    Judiciary's verification must name the same previous/successor agents.
    """
    receipt = read(ROOT / ("continuity/reconciliation-" + office + ".json"))
    verified = read(ROOT / ("continuity/verified-" + office + ".json"))
    if receipt.get("state") != "awaiting_reconciliation":
        return None
    if verified.get("previous_agent") != receipt.get("previous_agent"):
        return None
    if verified.get("successor_agent") != receipt.get("successor_agent"):
        return None
    if verified.get("verified_by") != "judiciary":
        return None
    if verified.get("verification_scope") != "external_effect_reconciled":
        return None
    ref = verified.get("evidence_ref")
    if not isinstance(ref, str) or not ref.strip():
        return None
    return {
        "previous_agent": receipt.get("previous_agent"),
        "successor_agent": receipt.get("successor_agent"),
        "verified_by": "judiciary",
        "verification_scope": "external_effect_reconciled",
        "evidence_ref": ref.strip(),
    }


def collect():
    incident = read(ROOT / "branches/incident.json")
    signals = set(incident.get("signals", []))
    # A stale health file must NEVER be treated as current proof of operation.
    town = pathlib.Path(os.environ.get("VICHE_TOWN_ROOT", "/var/lib/lubko/wd/viche"))
    laws = (town / "government/LAWS.md").read_text() if (town / "government/LAWS.md").exists() else ""
    import re
    executive = bool(re.search(r"^## Act \d+ — Executive Innovation Office Act \(enacted ", laws, re.M))
    innovation_path = ("executive/innovation-office/health.json" if executive
                       else "legislature/innovation-centre/health.json")
    innovation = read(ROOT / innovation_path)
    now = int(os.environ.get("VICHE_CASE_NOW", time.time()))
    if innovation and now - innovation.get("observed_at", 0) > 1800:
        signals.add("innovation_stale")
    # A failed office may be masked by a stale or missing branch-health probe;
    # its terminal continuity record remains an independently observable case.
    for office in ("executive", "judiciary", "innovation-centre", "c1a00001"):
        receipt = read(ROOT / ("continuity/reconciliation-" + office + ".json"))
        if receipt.get("state") in ("preparing", "awaiting_reconciliation"):
            if continuity_receipt(office) is None:
                signals.add("continuity_unverified_" + office)
    return now, signals


def latest_health_observation():
    """Return the latest branch-health sample, not this reconciliation call.

    Reconciliation can run repeatedly against unchanged inputs. Its wall-clock
    time is therefore not an independent health observation. The branch
    liveness probe appends timestamp/signal rows to this durable source.

    These rows are a PRECONDITION only. They are produced by the same boot loop
    that runs this reconciler, so repeating them proves nothing about whether a
    repair was independently verified. Closure requires an independent
    verification artifact (see verification_artifact).
    """
    path = ROOT / "branches/observations.tsv"
    try:
        rows = path.read_text().splitlines()
    except OSError:
        return None
    for row in reversed(rows):
        fields = row.split("\t", 1)
        if len(fields) != 2:
            continue
        try:
            observed_at = int(fields[0])
        except ValueError:
            continue
        return observed_at, fields[1].strip()
    return None


INDEPENDENT_VERIFIERS = ("judiciary", "clerk")
MAX_EVIDENCE_BYTES = 4 * 1024 * 1024


def _is_int(value):
    # JSON booleans satisfy isinstance(x, int); they are not timestamps.
    return type(value) is int


def _within_root(ref):
    """True only for a real regular file inside ROOT, reached without symlinks."""
    relative = pathlib.PurePath(ref)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        return False
    path = ROOT
    for part in relative.parts:
        path = path / part
        # Reject symlinks anywhere on the path inside the state root.
        if path.is_symlink():
            return False
    try:
        info = path.lstat()
    except OSError:
        return False
    return stat.S_ISREG(info.st_mode) and info.st_size <= MAX_EVIDENCE_BYTES


def verification_artifact(case, now):
    """Validate the case-bound verification artifact, or None.

    Closure needs evidence recorded for THIS case by an office other than the
    one that owns the repair:

      * ``case_id`` equals this case's id (no reuse for a later case);
      * ``verified_by`` names an independent office;
      * ``first_seen < verified_at <= last_seen <= now``: the verification must
        postdate the last observed failure and cannot be future-dated;
      * ``evidence`` names a regular file inside the state root, reached with
        no symlinks and within a size cap, whose sha256 matches the recorded
        digest.

    Honest limit: all offices run as the same host user, so this validates the
    artifact's contents, not who wrote it. Provenance is enforced by process
    (the verification pipeline is the only intended writer), not by
    cryptography.
    """
    signal = case.get("signal")
    if not isinstance(signal, str) or not signal:
        return None
    if not signal.replace("_", "").replace("-", "").isalnum():
        return None
    path = ROOT / "verification" / (signal + ".json")
    artifact = read(path)
    if artifact.get("case_id") != case.get("id"):
        return None
    if artifact.get("verified_by") not in INDEPENDENT_VERIFIERS:
        return None
    verified_at = artifact.get("verified_at")
    first_seen = case.get("first_seen")
    last_seen = case.get("last_seen", first_seen)
    if not (_is_int(verified_at) and _is_int(first_seen) and _is_int(last_seen)):
        return None
    if not (first_seen < verified_at <= now and last_seen <= verified_at):
        return None
    evidence = artifact.get("evidence")
    if not isinstance(evidence, dict):
        return None
    ref = evidence.get("ref")
    digest = evidence.get("sha256")
    if not isinstance(ref, str) or not ref.strip() or not isinstance(digest, str):
        return None
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        return None
    if not _within_root(ref):
        return None
    try:
        data = (ROOT / ref).read_bytes()
    except OSError:
        return None
    if hashlib.sha256(data).hexdigest() != digest:
        return None
    return {
        "artifact": "verification/" + signal + ".json",
        "case_id": case.get("id"),
        "verified_by": artifact.get("verified_by"),
        "verified_at": verified_at,
        "evidence_ref": ref,
        "evidence_sha256": digest,
        "provenance": "declared_by_artifact_content_not_cryptographically_enforced",
    }


def owner(signal):
    # The law already authorizes operational continuity under Acts 2/5.
    if signal == "judiciary_mailbox_pending":
        return "judiciary"
    # Changing the offices or statutes requires actual parliamentary action.
    if signal.startswith("innovation_") or signal.startswith("continuity_"):
        return "executive"
    if signal.endswith("_unhealthy") or signal.endswith("_missing") or signal.endswith("_stale"):
        return "executive"
    return "legislature"


META_SIGNALS = {"case_awaiting_verification"}


def reconcile():
    now, signals = collect()
    health_observation = latest_health_observation()
    STORE.mkdir(parents=True, exist_ok=True)
    existing = sorted(STORE.glob("*.json"))
    names = set(signals) | {p.stem for p in existing}
    for signal in sorted(names):
        if not signal.replace("_", "").replace("-", "").isalnum():
            continue
        if signal in META_SIGNALS:
            # Advisory: derived from open cases, so it must not become a case
            # itself (that would be self-referential and unclosable).
            continue
        path = STORE / (signal + ".json")
        case = read(path)
        # Addendum/evidence files in this directory are not case objects. A
        # malformed or list-shaped record is evidence to preserve, never a
        # reason for the collector to crash and leave the index stale.
        if not isinstance(case, dict):
            case = {}
        if signal in signals:
            if not case or case.get("state") == "verified_closed":
                case = {
                    "id": f"{signal}:{now}", "signal": signal,
                    "first_seen": now, "state": "open",
                    "clear_observations": 0,
                    "judiciary": "independent_fact_finding_required",
                    "legislature": "consider_evidence_and_legislation_if_needed",
                    "executive": "investigate_and_repair_within_existing_authority",
                    "owner": owner(signal),
                    "closure_rule": "independent verification artifact bound to this case; "
                                    "healthy probes are only a precondition",
                }
            case["last_seen"] = now
            case["observations"] = case.get("observations", 0) + 1
            case["clear_observations"] = 0
            case.pop("awaiting_independent_verification", None)
        elif case.get("state") == "open":
            # Never count repeated reconciliations of one sample as separate
            # healthy observations. Require distinct durable probe rows, each
            # explicitly clear and later than the last time the signal held.
            if health_observation is None or health_observation[1] != "clear":
                case["clear_observations"] = 0
                case.pop("last_clear_observation", None)
                case.pop("awaiting_independent_verification", None)
            elif (health_observation[0] > case.get("last_seen", case.get("first_seen", 0))
                  and health_observation[0] != case.get("last_clear_observation")):
                case["clear_observations"] = case.get("clear_observations", 0) + 1
                case["last_clear_observation"] = health_observation[0]
            if case.get("clear_observations", 0) >= 2:
                # Healthy probes are necessary but NOT sufficient. An open
                # case closes only on a case-bound artifact from an
                # independent office whose cited evidence resolves.
                artifact = verification_artifact(case, now)
                continuity = None
                if signal.startswith("continuity_unverified_"):
                    continuity = continuity_receipt(signal[len("continuity_unverified_"):])
                if artifact is None or (signal.startswith("continuity_unverified_") and continuity is None):
                    case["awaiting_independent_verification"] = True
                    case.pop("closure_evidence", None)
                else:
                    case["state"] = "verified_closed"
                    case["verified_at"] = now
                    case.pop("awaiting_independent_verification", None)
                    case["verification"] = (
                        "closed on a case-bound independent verification artifact "
                        "with resolvable cited evidence")
                    case["closure_evidence"] = artifact
                    if continuity is not None:
                        case["closure_evidence"]["continuity_receipt"] = continuity
        elif not case:
            continue
        atomic(path, case)
    records = [x for x in (read(p) for p in sorted(STORE.glob("*.json")))
               if isinstance(x, dict) and x.get("id")]
    active = [x for x in records if x.get("state") == "open"]
    # A closed label is not resolution evidence. Some historical cases were
    # closed by the old absent-signal path and carry no case-bound artifact.
    # They must remain visible to monitoring and to the responsible office
    # until an authorized reconciliation supplies that evidence.
    unresolved = [x for x in records if closure_unsubstantiated(x)]
    atomic(STORE / "index.json", {
        "observed_at": now,
        "active": [x["id"] for x in active],
        "count": len(active),
        "unresolved_without_closure_evidence": [
            {"id": x.get("id"), "signal": x.get("signal"), "state": x.get("state"),
             "reason": "verified_closed without a case-bound closure artifact"}
            for x in unresolved],
        "unresolved_without_closure_evidence_count": len(unresolved),
        "total_obligations": len(active) + len(unresolved),
        "caveat": "operational health, not proof of delivery; a closed label "
                  "without a case-bound closure artifact is listed as unresolved",
    })
    return active


def closure_unsubstantiated(case):
    """True for a closed case whose closure is not backed by a case artifact.

    Historical closures from the absent-signal path have no closure_evidence.
    An artifact explicitly marked closure_eligible=false is likewise not
    resolution. This does not reopen or rewrite the case object; it keeps the
    obligation discoverable.
    """
    if case.get("state") != "verified_closed":
        return False
    evidence = case.get("closure_evidence")
    if not isinstance(evidence, dict) or not evidence:
        return True
    return evidence.get("closure_eligible") is False


def report():
    return [x for x in (read(p) for p in sorted(STORE.glob("*.json")))
            if isinstance(x, dict) and x.get("id") and x.get("state") == "open"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("reconcile", "report"))
    args = parser.parse_args()
    cases = reconcile() if args.operation == "reconcile" else report()
    print(json.dumps({
        "open_cases": cases,
        "rule": "Judiciary independently investigates; Parliament decides legal changes; "
                "Executive repairs within existing authority and implements ratified changes. "
                "Never close for agent activity, a comment, or a PR.",
    }, separators=(",", ":")))

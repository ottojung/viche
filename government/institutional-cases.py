#!/usr/bin/env python3
"""Durable cross-branch corrective cases, with evidence-based operational closure.

A case is a monitored obligation, NOT a Judiciary verdict or an authorization
to enact law. Observation and routing remain deterministic even if every model
is down. Existing independent Judiciary/Parliament/Executive powers remain.
"""
import argparse
import json
import os
import pathlib
import tempfile
import time

ROOT = pathlib.Path(os.environ.get("VICHE_STATE_ROOT", "/var/lib/lubko/wd/viche-state"))
STORE = ROOT / "institutional-cases"


def read(path):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, ValueError):
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
            verified = read(ROOT / ("continuity/verified-" + office + ".json"))
            valid = (receipt.get("state") == "awaiting_reconciliation"
                and verified.get("previous_agent") == receipt.get("previous_agent")
                and verified.get("successor_agent") == receipt.get("successor_agent")
                and verified.get("verified_by") == "judiciary"
                and verified.get("verification_scope") == "external_effect_reconciled"
                and isinstance(verified.get("evidence_ref"), str)
                and bool(verified["evidence_ref"].strip()))
            if not valid:
                signals.add("continuity_unverified_" + office)
    return now, signals


def latest_health_observation():
    """Return the latest branch-health sample, not this reconciliation call.

    Reconciliation can run repeatedly against unchanged inputs. Its wall-clock
    time is therefore not an independent health observation. The branch
    liveness probe appends timestamp/signal rows to this durable source.
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


def reconcile():
    now, signals = collect()
    health_observation = latest_health_observation()
    STORE.mkdir(parents=True, exist_ok=True)
    existing = sorted(STORE.glob("*.json"))
    names = set(signals) | {p.stem for p in existing}
    for signal in sorted(names):
        if not signal.replace("_", "").replace("-", "").isalnum():
            continue
        path = STORE / (signal + ".json")
        case = read(path)
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
                    "closure_rule": "two independent healthy observations, not agent/process success",
                }
            case["last_seen"] = now
            case["observations"] = case.get("observations", 0) + 1
            case["clear_observations"] = 0
        elif case.get("state") == "open":
            # Never count repeated reconciliations of one sample as separate
            # healthy observations. Require distinct durable probe rows, each
            # explicitly clear and later than the last time the signal held.
            if health_observation is None or health_observation[1] != "clear":
                case["clear_observations"] = 0
                case.pop("last_clear_observation", None)
            elif (health_observation[0] > case.get("last_seen", case.get("first_seen", 0))
                  and health_observation[0] != case.get("last_clear_observation")):
                case["clear_observations"] = case.get("clear_observations", 0) + 1
                case["last_clear_observation"] = health_observation[0]
            if case.get("clear_observations", 0) >= 2:
                case["state"] = "verified_closed"
                case["verified_at"] = now
                case["verification"] = "two distinct later branch-health samples explicitly clear"
        elif not case:
            continue
        atomic(path, case)
    open_cases = [read(p) for p in sorted(STORE.glob("*.json"))]
    active = [x for x in open_cases if x.get("state") == "open"]
    atomic(STORE / "index.json", {
        "observed_at": now, "active": [x["id"] for x in active],
        "count": len(active), "caveat": "operational health, not proof of delivery",
    })
    return active


def report():
    return [read(p) for p in sorted(STORE.glob("*.json"))
            if p.name != "index.json" and read(p).get("state") == "open"]


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

#!/usr/bin/env python3
"""Minimal source-linked first observations, not independent outcome claims.

The three non-Statistics institutions can begin doing real, limited work in
Act 34's reversible model-free pilot. This is an observation tool, NOT its
authorization or budget. No network or model. --dry-run only reads.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path

TOWN = Path(os.environ.get("VICHE_TOWN_ROOT", "/var/lib/lubko/wd/viche")).resolve()
STATE = Path(os.environ.get("VICHE_STATE_ROOT", "/var/lib/lubko/wd/viche-state")).resolve()
OFFICES = ("statistics", "foresight", "strategy", "spying")
LIMIT = 2 * 1024 * 1024


def measured(path):
    """Return actual bytes' digest, never shared-root counts as independent."""
    try:
        with path.open("rb") as handle:
            blob = handle.read(LIMIT + 1)
        if len(blob) > LIMIT:
            raise ValueError("source exceeds 2MiB observation limit")
        return json.loads(blob), "file:%s#sha256=%s" % (
            path, hashlib.sha256(blob).hexdigest())
    except (OSError, ValueError, UnicodeError) as exc:
        return None, "UNAVAILABLE:%s:%s" % (path, type(exc).__name__)


def statistics():
    # First observation is a source-attributed raw input comparison, never
    # independent verification merely because Statistics read it.
    paths = {
        "outcomes": STATE / "institutional-outcomes/latest.json",
        "resources": STATE / "economy/resources.json",
    }
    samples = {k: measured(p) for k, p in paths.items()}
    sources = [s for data, s in samples.values() if data is not None]
    missing = [s for data, s in samples.values() if data is None]
    outcomes = samples["outcomes"][0] or {}
    resources = samples["resources"][0] or {}
    return {
        "office": "statistics",
        "status": "observed" if sources else "unavailable",
        "sources": sources, "missing": missing,
        "facts": {
            "agent_processes_24h": outcomes.get("agents", {}).get("total"),
            "delivery_verified_by_input_probe":
                outcomes.get("delivery_verified_by_this_probe"),
            "disk_used_pct": resources.get("resources", {}).get("disk:state", {}).get("used_pct"),
        },
        "limits": [
            "Process counts, clean exits and merge counts do not measure useful outcomes.",
            "Input collectors are correlated; no independent result has been verified.",
            "Missing primary sources are explicit; source digests prove bytes only.",
        ],
    }


def foresight():
    path = TOWN / "records/predictions/calibration.json"
    value, source = measured(path)
    if not isinstance(value, dict):
        return {"office": "foresight", "status": "unavailable",
                "sources": [], "missing": source}
    counts = value.get("counts", {})
    count_keys = ("registered", "due", "due_resolved", "due_scored",
                  "due_unresolved", "resolved_scored", "unresolved")
    metrics = {k: counts.get(k) for k in count_keys}
    for k in ("due_resolution_coverage", "due_scored_coverage"):
        metrics[k] = value.get(k)
    metrics["brier"] = value.get("brier", {}).get("aggregate")
    metrics["numerical_gate_eligible"] = value.get(
        "act32_calibration_minimum_gate", {}).get("eligible")
    return {
        "office": "foresight", "status": "observed", "sources": [source],
        "facts": metrics,
        "scenarios": [
            "If new due forecasts remain unresolved, due resolution coverage declines.",
            "If new due forecasts are independently resolved and scored, calibration precision can improve.",
        ],
        "limits": [
            "Scored outcomes may be far fewer than due resolutions.",
            "Single-model-substrate predictions are not independent confirmations.",
            "No intervention is credited with a prevented outcome without observations.",
            "A forecast's registration or this report is never a scored forecast.",
        ],
    }


def strategy():
    path = STATE / "economy/resources.json"
    data, source = measured(path)
    disk = (data or {}).get("resources", {}).get("disk:state")
    if not isinstance(disk, dict) or not isinstance(disk.get("avail_gib"), (int, float)):
        return {"office": "strategy", "status": "unavailable",
                "sources": [], "missing": source,
                "limits": ["Resource risk cannot be inferred from missing metering."]}
    avail = disk.get("avail_gib")
    horizon = disk.get("hours_to_full")
    if not isinstance(horizon, (int, float)) or horizon <= 0:
        horizon = None
    # Use the reported trend as a CONDITIONAL scenario, never claim a causal
    # counterfactual from a single resource measurement.
    per_hour = avail / horizon if horizon else None
    marginal = (5.0 / per_hour) if per_hour and per_hour > 0 else None
    return {
        "office": "strategy", "status": "observed", "sources": [source],
        "facts": {"disk_status": disk.get("status"), "available_gib": avail,
                  "used_pct": disk.get("used_pct"),
                  "reported_hours_to_full": horizon},
        "options": [
            {"action": "Maintain current controls, inspect again next cycle",
             "conditional_result": "If the measured historical rate persists, "
                                  "reported horizon is %s hours" % horizon,
             "reversibility": "No storage action; retains present choices"},
            {"action": "Ask Economy to identify 5 GiB of safely reclaimable named files",
             "conditional_result": ("If 5 GiB is really reclaimed and the measured "
                                    "rate remains constant, estimated horizon gains %.1f h"
                                    % marginal if marginal is not None else
                                    "Unknown: no reliable trend"),
             "reversibility": "No deletion authorized by this report"},
        ],
        "limits": [
            "Single disk trend is an uncertain extrapolation, not a forecast registration.",
            "No autonomous deletion, funding request, or Executive order.",
            "The two options are hypotheses; their effects require later measurement.",
        ],
    }


def spying():
    # Public sources only. Do not republish Founder's text or derive a
    # personality/preference from the number of messages, silences or edits.
    path = TOWN / "records/knowledge/spying-source-allowlist.json"
    data, source = measured(path)
    if not isinstance(data, dict) or data.get("schema") != "viche-spying-source-allowlist-v1":
        return {"office": "spying", "status": "unavailable",
                "sources": [], "missing": source}
    allow = data.get("antonina", {}).get("messages", {})
    return {
        "office": "spying", "status": "observed", "sources": [source],
        "facts": {"pinned_public_founder_messages": len(allow) if isinstance(allow, dict) else None,
                  "allowlist_expiry_epoch": data.get("expires_at"),
                  "configured_public_repositories":
                      len(data.get("github_public", {}).get("repos", {}))},
        "limits": [
            "Configured pins are NOT independent verification of live authenticity.",
            "Live source-bundle preflight must pass before any actual publication.",
            "No personal preference inference; no secret-bearing source read.",
            "Silence, corrective complaints and attention are not authorization.",
        ],
    }


def collect(office):
    return {"statistics": statistics, "foresight": foresight, "strategy": strategy,
            "spying": spying}[office]()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("office", choices=OFFICES)
    args = parser.parse_args()
    report = collect(args.office)
    report["observed_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    report["scope"] = "provisional_model_free_auxiliary_telemetry_only"
    report["auxiliary_telemetry"] = True
    report["counts_as_operational_institution"] = False
    report["verified_useful_outcome"] = False
    report["provider_requests"] = 0
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "observed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

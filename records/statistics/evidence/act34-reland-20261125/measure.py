#!/usr/bin/env python3
"""Reproducible, read-only re-measurement of the Act 34 recurring-renewal chain.

Reads ONLY the byte-frozen primary copies in this directory. It never contacts
the live budget state, the board, or a provider. Importing the frozen
knowledge-budget-tool.py and calling its real charges()/admit() functions is a
re-execution of the deployed detection/admission logic, not a secondhand report.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

E = Path(__file__).resolve().parent
OFFICES = ("statistics", "foresight", "strategy", "spying")
CAP_KEYS = ("tokens_total", "cpu_seconds", "wall_seconds")
sys.dont_write_bytecode = True


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_map():
    out = {}
    for path in sorted(E.rglob("*")):
        if (path.is_file() and path.name not in ("measure.py", "measurement.json")
                and "__pycache__" not in path.parts):
            out[str(path.relative_to(E))] = sha(path)
    return out


def load(name):
    return json.loads((E / name).read_text())


def main():
    H = digest_map()
    act = load("activation.json")
    cfg = load("knowledge-budget.conf")
    control = {
        "zero_billed_verifier_sha256": H["knowledge-zero-billed.py"],
        "wrapper_sha256": H["knowledge-free-dispatch.sh"],
        "zero_billed_policy_sha256": H["knowledge-zero-billed-policy.json"],
    }
    econ_report = H["economy-zero-billed-verification-1831z.md"]

    permits = {o: load("permit-%s.json" % o) for o in OFFICES}

    permit_checks = {}
    for o in OFFICES:
        p = permits[o]
        ref = act["offices"][o]
        permit_checks[o] = {
            "sha256": H["permit-%s.json" % o],
            "matches_activation_permit_sha256": H["permit-%s.json" % o] == ref["permit_sha256"],
            "authorized_by": p["authorized_by"] == "act:34:%s" % o,
            "enabled_matches": p.get("status_note", "").startswith("SIGNED") and ref["enabled"] is True,
            "not_before_matches": p["not_before"] == ref["not_before"],
            "expiry_matches": p["expires_at"] == ref["expires_at"],
            "budget_sha256_matches_config": p["budget_sha256"] == H["knowledge-budget.conf"],
            "enforcement_control_hashes_match": all(
                p["enforcement_evidence"][k] == v for k, v in control.items()),
            "negative_acceptance_digest_consistent": (
                p["enforcement_evidence"]["negative_acceptance_digest"]
                == p["negative_acceptance_digest"]
                == act["economy_free_tier_evidence"]["negative_acceptance_digest"]),
            "origin_commit": p.get("permit_attestation_reference", {}).get("officer_agent_id")
                == ref["permit_attestation"]["officer_agent_id"],
        }

    econ = act["economy_free_tier_evidence"]
    econ_checks = {
        "report_sha256_matches_frozen_economy_report": econ["report_sha256"] == econ_report,
        "report_ref": econ["report_ref"],
        "control_hashes_match_frozen_controls": all(
            econ[k] == v for k, v in control.items()),
        "provider_snapshot_sha256": econ["provider_snapshot_sha256"],
    }

    cfg_checks = {
        "per_office_caps_match_permits": all(
            cfg["offices"][o]["caps"] == permits[o]["caps"] for o in OFFICES),
        "per_run_caps_match_permits": all(
            cfg["offices"][o]["per_run_caps"] == permits[o]["per_run_caps"] for o in OFFICES),
        "aggregate_equals_sum_of_office_caps": all(
            cfg["aggregate"]["caps"][k] == sum(cfg["offices"][o]["caps"][k] for o in OFFICES)
            for k in CAP_KEYS),
        "per_run_below_office_cap": all(
            cfg["offices"][o]["per_run_caps"][k] < cfg["offices"][o]["caps"][k]
            for o in OFFICES for k in CAP_KEYS),
        "accounting_window_seconds": cfg["accounting_window_seconds"],
    }

    # Re-execute the deployed module's own validation and admission logic.
    spec = importlib.util.spec_from_file_location("viche_budget_frozen", E / "knowledge-budget-tool.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cfg_errors = mod.validate_config(cfg)

    res_dir = E / "budget-state" / "reservations"
    now = 1795587774  # latest meter 'at' among the frozen reservations
    window = cfg["accounting_window_seconds"]
    charges, counted, skipped = mod.charges(str(res_dir), now, window)
    frozen_agg = load("budget-state/aggregate.json")
    agg_reproduces = all(
        charges.get(k) == frozen_agg.get(k) for k in CAP_KEYS
    ) and charges["by_office"] == frozen_agg["by_office"]

    rows = {}
    for path in sorted(res_dir.glob("*.json")):
        row = json.loads(path.read_text())
        rows[row["id"]] = row
    waves = {}
    for o in OFFICES:
        mine = [r for r in rows.values() if r["office"] == o]
        waves[o] = {
            "first_wave_0964bd1e": sorted(r["id"] for r in mine
                                          if r["config_sha256"] == "0964bd1e9c55b7953b3fbcb9efd4ed3ae565b0c4832b736780b8ba4a8f3d7ea6"),
            "second_wave_b80f48af": sorted(r["id"] for r in mine
                                           if r["config_sha256"] == "b80f48aff6b94382d4a5b859bab41906fa665c3b8cf4f6eb5bd0a84152ea8aab"),
            "second_wave_states": sorted(r["state"] for r in mine
                                         if r["config_sha256"] == "b80f48aff6b94382d4a5b859bab41906fa665c3b8cf4f6eb5bd0a84152ea8aab"),
            "second_wave_native_tokens": sorted(r["meter"]["tokens"]["delta_total"] for r in mine
                                                if r["config_sha256"] == "b80f48aff6b94382d4a5b859bab41906fa665c3b8cf4f6eb5bd0a84152ea8aab"),
        }
    stats_second = [r for r in rows.values()
                    if r["office"] == "statistics"
                    and r["config_sha256"] == "b80f48aff6b94382d4a5b859bab41906fa665c3b8cf4f6eb5bd0a84152ea8aab"]
    own_reservation = {
        "id": stats_second[0]["id"] if stats_second else None,
        "agent_id": stats_second[0]["agent_id"] if stats_second else None,
        "state": stats_second[0]["state"] if stats_second else None,
        "created_at": stats_second[0]["created_at"] if stats_second else None,
    }

    admits_new = {o: mod.admit(cfg, charges, o) for o in OFFICES}
    third_wave_projection = {
        o: {"office_used": charges["by_office"][o]["tokens_total"],
            "run_cap": cfg["offices"][o]["per_run_caps"]["tokens_total"],
            "office_cap": cfg["offices"][o]["caps"]["tokens_total"],
            "office_runs_remaining_at_full_ceiling": (
                cfg["offices"][o]["caps"]["tokens_total"]
                - charges["by_office"][o]["tokens_total"]) // cfg["offices"][o]["per_run_caps"]["tokens_total"]}
        for o in OFFICES
    }

    # Negative controls against the superseded configuration (frozen v1 copy).
    prev_cfg_path = E.parent / "act34-activation-20261124" / "knowledge-budget.conf"
    prev_cfg = json.loads(prev_cfg_path.read_text())
    admits_old = {o: mod.admit(prev_cfg, charges, o) for o in OFFICES}
    # Synthetic overload: one token past the office ceiling minus a run.
    overload = json.loads(json.dumps(charges))
    overload["by_office"]["statistics"]["tokens_total"] = (
        cfg["offices"]["statistics"]["caps"]["tokens_total"]
        - cfg["offices"]["statistics"]["per_run_caps"]["tokens_total"] + 1)
    admit_overload = mod.admit(cfg, overload, "statistics")

    result = {
        "captured_utc": "2026-11-25T06:24:32Z",
        "captured_from": "canonical main + /var/lib/lubko/wd/viche-state/knowledge/budget",
        "sha256": H,
        "activation_status": act["status"],
        "activation_note": act["note"],
        "permit_checks": permit_checks,
        "economy_checks": econ_checks,
        "config_checks": cfg_checks,
        "validate_config_errors": cfg_errors,
        "charges": charges,
        "charges_counted": counted,
        "charges_skipped": skipped,
        "charges_reproduce_frozen_aggregate": agg_reproduces,
        "frozen_aggregate_sha256": H["budget-state/aggregate.json"],
        "waves": waves,
        "own_statistics_reservation": own_reservation,
        "admit_new_config_at_current_charges": admits_new,
        "third_wave_projection_tokens": third_wave_projection,
        "negative_control_superseded_config": admits_old,
        "negative_control_overload_statistics": admit_overload,
    }
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    print()


if __name__ == "__main__":
    main()

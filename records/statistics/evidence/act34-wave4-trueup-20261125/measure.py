#!/usr/bin/env python3
"""Read-only re-measurement of Act 34 budget true-up and a new four-office wave.

Reads ONLY the byte-frozen primary copies in this directory. It never contacts
the live budget state, the board, an agent runner or a provider. Importing the
frozen knowledge-budget-tool.py and calling its real validate_config()/charges()/
admit() functions re-executes the deployed logic; it is not a secondhand report.

Comparison values from the preceding snapshot (act34-budget-trueup-20261125,
captured 2026-11-25T07:29:15Z, 9 reservations) are hardcoded here as content
assertions. A change in any expected byte/id/count is a falsifier, not a value
to be silently updated.
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

# Frozen expected values from records/statistics/evidence/act34-budget-trueup-20261125/
PRIOR = {
    "activation.json": "921b99ae1288769b4460ea25641cad93da8d1ed3c98ce1adfbecbd32b261587b",
    "knowledge-budget.conf": "b80f48aff6b94382d4a5b859bab41906fa665c3b8cf4f6eb5bd0a84152ea8aab",
    "knowledge-budget-tool.py": "4ecae5ea0c1bd3edaa4cb2262cd9b8208a1ee66830ff92ff6edf6ee2a40ce9f3",
    "superseded-knowledge-budget.conf": "0964bd1e9c55b7953b3fbcb9efd4ed3ae565b0c4832b736780b8ba4a8f3d7ea6",
    "reservation_count": 9,
    "tokens_total": 28732715,
    "cpu_seconds": 25648.819999999832,
    "wall_seconds": 6325,
    # Third statistics wave was ACTIVE at the prior capture, charged at ceiling.
    "third_stats_reservation_id": "r1795591522-KXZURRSN",
    "third_stats_prior_state": "active",
    "third_stats_prior_charge_tokens_at_ceiling": 11320103,
    "third_stats_prior_tokens_total_at_capture": 1229556,
    # At the prior capture spying had exactly one new-config reservation.
    "spying_new_config_ids_at_prior": ["r1795588177-2jkiJ5iT"],
}
# Reservations created strictly after the 07:29:15Z capture (new wave).
NEW_WAVE_IDS = {
    "foresight": "r1795591782-heuosi5E",
    "strategy": "r1795591787-oNrmHxIR",
    "spying": "r1795591797-d18DoUyx",
    "statistics": "r1795595233-CXGuJISF",
}
OWN_STATISTICS_AGENT = "dNnp3iuADUxoioMa5FGnwZ-sort"
NEW_CONFIG = "b80f48aff6b94382d4a5b859bab41906fa665c3b8cf4f6eb5bd0a84152ea8aab"
OLD_CONFIG = "0964bd1e9c55b7953b3fbcb9efd4ed3ae565b0c4832b736780b8ba4a8f3d7ea6"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_map():
    return {str(p.relative_to(E)): sha(p) for p in sorted(E.rglob("*"))
            if p.is_file() and p.name not in ("measure.py", "measurement.json")
            and "__pycache__" not in p.parts}


def main():
    H = digest_map()
    cfg = json.loads((E / "knowledge-budget.conf").read_text())
    act = json.loads((E / "activation.json").read_text())
    res_dir = E / "budget-state" / "reservations"
    rows = {p.stem: json.loads(p.read_text()) for p in sorted(res_dir.glob("*.json"))}

    file_keys = ("activation.json", "knowledge-budget.conf",
                 "knowledge-budget-tool.py", "superseded-knowledge-budget.conf")
    bytes_unchanged = {k: H.get(k) == PRIOR[k] for k in file_keys}
    activation_active = all(act["offices"][o]["enabled"] is True for o in OFFICES)

    spec = importlib.util.spec_from_file_location("viche_budget_frozen", E / "knowledge-budget-tool.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cfg_errors = mod.validate_config(cfg)

    now = max(max(r.get("meter", {}).get("at", 0), r.get("created_at", 0)) for r in rows.values())
    window = cfg["accounting_window_seconds"]
    charges, counted, skipped = mod.charges(str(res_dir), now, window)
    agg = json.loads((E / "budget-state" / "aggregate.json").read_text())
    agg_reproduces = (all(charges.get(k) == agg.get(k) for k in CAP_KEYS)
                      and charges["by_office"] == agg["by_office"]
                      and counted == agg["counted"])

    # True-up of the third statistics wave that was ACTIVE at the prior capture.
    rid = PRIOR["third_stats_reservation_id"]
    r = rows[rid]
    actual = r["usage"]["tokens_total"]
    true_up = {
        "id": rid,
        "office": r["office"],
        "prior_state": PRIOR["third_stats_prior_state"],
        "prior_charge_tokens_at_ceiling": PRIOR["third_stats_prior_charge_tokens_at_ceiling"],
        "prior_tokens_total_at_capture": PRIOR["third_stats_prior_tokens_total_at_capture"],
        "now_state": r["state"],
        "usage_tokens_total": actual,
        "charge_reduction_tokens": PRIOR["third_stats_prior_charge_tokens_at_ceiling"] - actual,
        "trued_down": r["state"] == "closed"
        and actual == r["meter"]["tokens"]["total"]
        and actual < PRIOR["third_stats_prior_charge_tokens_at_ceiling"],
        "closed_at": r.get("closed_at"),
        "closed_reason": r.get("closed_reason"),
        "config_sha256": r["config_sha256"],
    }

    # The four reservations created strictly after the prior capture.
    new_wave = {}
    for o, nid in NEW_WAVE_IDS.items():
        nr = rows[nid]
        new_wave[o] = {
            "id": nid,
            "agent_id": nr["agent_id"],
            "office": nr["office"],
            "state": nr["state"],
            "created_at": nr["created_at"],
            "closed_at": nr.get("closed_at"),
            "config_sha256": nr["config_sha256"],
            "usage_tokens_total": nr["usage"]["tokens_total"],
            "matches_this_appointment": (o == "statistics" and nr["agent_id"] == OWN_STATISTICS_AGENT),
        }
    new_wave_all_new_config = all(v["config_sha256"] == NEW_CONFIG for v in new_wave.values())
    new_wave_created_after_prior = all(
        v["created_at"] > 1795591755 for v in new_wave.values())  # 1795591755 = 07:29:15Z

    # Wave classification by config hash at this capture.
    waves = {}
    for o in OFFICES:
        mine = [r for r in rows.values() if r["office"] == o]
        waves[o] = {
            "old_config_0964bd1e_count": sum(r["config_sha256"] == OLD_CONFIG for r in mine),
            "new_config_b80f48af_ids": sorted(r["id"] for r in mine if r["config_sha256"] == NEW_CONFIG),
            "new_config_states": sorted(r["state"] for r in mine if r["config_sha256"] == NEW_CONFIG),
        }

    admits_new = {o: mod.admit(cfg, charges, o) for o in OFFICES}
    prev_cfg = json.loads((E / "superseded-knowledge-budget.conf").read_text())
    admits_old = {o: mod.admit(prev_cfg, charges, o) for o in OFFICES}
    overload = json.loads(json.dumps(charges))
    overload["by_office"]["statistics"]["tokens_total"] = (
        cfg["offices"]["statistics"]["caps"]["tokens_total"]
        - cfg["offices"]["statistics"]["per_run_caps"]["tokens_total"] + 1)
    admit_overload = mod.admit(cfg, overload, "statistics")

    result = {
        "captured_utc": "2026-11-25T08:28:30Z",
        "captured_from": "canonical main records/knowledge/activation.json, government/knowledge-budget.* and "
                         "/var/lib/lubko/wd/viche-state/knowledge/budget (aggregate + reservations)",
        "measurement_script": "measure.py in this directory (read-only on the frozen copies)",
        "sha256": H,
        "bytes_unchanged_vs_prior_snapshot": bytes_unchanged,
        "activation_all_offices_enabled": activation_active,
        "validate_config_errors": cfg_errors,
        "recomputed_now_unix": now,
        "accounting_window_seconds": window,
        "reservation_count": len(rows),
        "prior_reservation_count": PRIOR["reservation_count"],
        "counted": counted,
        "skipped": skipped,
        "recomputed_charges": {k: charges[k] for k in CAP_KEYS},
        "frozen_aggregate": {k: agg[k] for k in CAP_KEYS},
        "charges_reproduce_frozen_aggregate": agg_reproduces,
        "prior_snapshot_tokens_total": PRIOR["tokens_total"],
        "tokens_total_change_vs_prior": agg["tokens_total"] - PRIOR["tokens_total"],
        "third_wave_true_up": true_up,
        "new_wave": new_wave,
        "new_wave_all_new_config": new_wave_all_new_config,
        "new_wave_created_after_prior_capture": new_wave_created_after_prior,
        "waves": waves,
        "admit_new_config_at_current_charges": admits_new,
        "negative_control_superseded_config_admit": admits_old,
        "negative_control_overload_admit": admit_overload,
        "derived_measurement_sha256": None,
    }
    body = json.loads(json.dumps(result))
    body.pop("derived_measurement_sha256")
    result["derived_measurement_sha256"] = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    print()


if __name__ == "__main__":
    main()

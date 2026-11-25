#!/usr/bin/env python3
"""Read-only re-measurement of the Act 34 knowledge-budget true-up and wave admission.

Reads ONLY the byte-frozen primary copies in this directory. It never contacts
the live budget state, the board, an agent runner or a provider. Importing the
frozen knowledge-budget-tool.py and calling its real charges()/admit()/validate_config()
functions re-executes the deployed logic; it is not a secondhand report.

Comparison values from the preceding snapshot (act34-reland-20261125, captured
2026-11-25T06:24:32Z) are hardcoded here as content assertions. A change in any
expected byte is a falsifier, not a value to be silently updated.
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

# Frozen expected values from records/statistics/evidence/act34-reland-20261125/
PRIOR = {
    "activation.json": "921b99ae1288769b4460ea25641cad93da8d1ed3c98ce1adfbecbd32b261587b",
    "knowledge-budget.conf": "b80f48aff6b94382d4a5b859bab41906fa665c3b8cf4f6eb5bd0a84152ea8aab",
    "knowledge-budget-tool.py": "4ecae5ea0c1bd3edaa4cb2262cd9b8208a1ee66830ff92ff6edf6ee2a40ce9f3",
    "reservation_count": 7,
    "tokens_total": 32139944,
    "cpu_seconds": 28292.10999999987,
    "wall_seconds": 7027,
    "inflight": {
        "r1795587673-4BdLzlhX": {"office": "statistics", "charge_tokens": 11320103},
        "r1795587676-SJSZkBC8": {"office": "strategy", "charge_tokens": 11320103},
    },
    "spying_second_wave_ids": [],
}
# Named in records/investigations/recovery-steward-spying-unsafe-hold-reconciliation-20261125T0626Z.md
REPLACEMENT_SPYING_AGENT = "RdprsTnAGd7R1ZfoUhUlfV-elements"
OWN_STATISTICS_AGENT = "gwecoglvJR6RP10r8k6o6p-sundial"
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

    bytes_unchanged = {k: H.get(k) == v for k, v in PRIOR.items()
                       if isinstance(v, str)}
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

    # True-up of the two reservations that were ACTIVE (charged at ceiling) at the prior snapshot.
    true_up = {}
    for rid, prior in PRIOR["inflight"].items():
        r = rows[rid]
        actual = r["usage"]["tokens_total"]
        true_up[rid] = {
            "office": r["office"],
            "prior_state": "active",
            "prior_charge_tokens_at_ceiling": prior["charge_tokens"],
            "now_state": r["state"],
            "actual_usage_tokens": actual,
            "charge_reduction_tokens": prior["charge_tokens"] - actual,
            "trued_down": r["state"] == "closed"
            and actual == r["meter"]["tokens"]["total"]
            and actual < prior["charge_tokens"],
            "closed_at": r.get("closed_at"),
            "closed_reason": r.get("closed_reason"),
            "config_sha256": r["config_sha256"],
        }

    # Wave classification by config hash at the later capture.
    waves = {}
    for o in OFFICES:
        mine = [r for r in rows.values() if r["office"] == o]
        waves[o] = {
            "old_config_0964bd1e_ids": sorted(r["id"] for r in mine if r["config_sha256"] == OLD_CONFIG),
            "new_config_b80f48af_ids": sorted(r["id"] for r in mine if r["config_sha256"] == NEW_CONFIG),
            "new_config_states": sorted(r["state"] for r in mine if r["config_sha256"] == NEW_CONFIG),
            "new_config_native_tokens": sorted(r["usage"]["tokens_total"] for r in mine
                                               if r["config_sha256"] == NEW_CONFIG),
        }
    spying_new_now = waves["spying"]["new_config_b80f48af_ids"]
    spying_launch = rows.get("r1795588177-2jkiJ5iT")

    own = rows.get("r1795591522-KXZURRSN")

    admits_new = {o: mod.admit(cfg, charges, o) for o in OFFICES}
    prev_cfg = json.loads((E / "superseded-knowledge-budget.conf").read_text())
    admits_old = {o: mod.admit(prev_cfg, charges, o) for o in OFFICES}
    overload = json.loads(json.dumps(charges))
    overload["by_office"]["statistics"]["tokens_total"] = (
        cfg["offices"]["statistics"]["caps"]["tokens_total"]
        - cfg["offices"]["statistics"]["per_run_caps"]["tokens_total"] + 1)
    admit_overload = mod.admit(cfg, overload, "statistics")

    result = {
        "captured_utc": "2026-11-25T07:29:15Z",
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
        "counted": counted,
        "skipped": skipped,
        "recomputed_charges": {k: charges[k] for k in CAP_KEYS},
        "frozen_aggregate": {k: agg[k] for k in CAP_KEYS},
        "charges_reproduce_frozen_aggregate": agg_reproduces,
        "prior_snapshot_tokens_total": PRIOR["tokens_total"],
        "tokens_total_change_vs_prior": agg["tokens_total"] - PRIOR["tokens_total"],
        "true_up": true_up,
        "waves": waves,
        "spying_new_config_reservation": None if not spying_launch else {
            "id": spying_launch["id"],
            "agent_id": spying_launch["agent_id"],
            "matches_reconciliation_replacement_agent": spying_launch["agent_id"] == REPLACEMENT_SPYING_AGENT,
            "state": spying_launch["state"],
            "created_at": spying_launch["created_at"],
            "closed_at": spying_launch.get("closed_at"),
            "closed_reason": spying_launch.get("closed_reason"),
            "tokens_total": spying_launch["usage"]["tokens_total"],
            "cost": spying_launch["usage"]["cost"],
            "config_sha256": spying_launch["config_sha256"],
        },
        "spying_new_config_ids_now_nonempty": bool(spying_new_now),
        "own_statistics_reservation": None if not own else {
            "id": own["id"],
            "agent_id": own["agent_id"],
            "matches_this_appointment": own["agent_id"] == OWN_STATISTICS_AGENT,
            "state": own["state"],
            "created_at": own["created_at"],
            "tokens_total_at_capture": own["usage"]["tokens_total"],
            "config_sha256": own["config_sha256"],
        },
        "admit_new_config_at_current_charges": admits_new,
        "negative_control_superseded_config_admit": admits_old,
        "negative_control_overload_admit": admit_overload,
        "derived_measurement_sha256": None,
    }
    # Self-hash over the deterministic result without the self-reference field.
    body = json.loads(json.dumps(result))
    body.pop("derived_measurement_sha256")
    result["derived_measurement_sha256"] = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    print()


if __name__ == "__main__":
    main()

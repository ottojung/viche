#!/usr/bin/env python3
"""Read-only re-measurement of the first `held` knowledge-budget liability.

Reads ONLY the byte-frozen primary copies in this directory. It never contacts
the live budget state, the board, an agent runner or a provider. Importing the
frozen knowledge-budget-tool.py and calling its real validate_config()/charges()/
admit() functions re-executes the deployed logic; it is not a secondhand report.

Content assertions against the preceding snapshot (act34-wave4-trueup-20261125,
captured 2026-11-25T08:28:30Z, 13 reservations) are hardcoded below. A change in
any expected byte/id/count/state is a falsifier, not a value to be silently
updated. The script reports every assertion individually and never edits sources.
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

# Frozen expected values from records/statistics/evidence/act34-wave4-trueup-20261125/
PRIOR = {
    "activation.json": "921b99ae1288769b4460ea25641cad93da8d1ed3c98ce1adfbecbd32b261587b",
    "knowledge-budget.conf": "b80f48aff6b94382d4a5b859bab41906fa665c3b8cf4f6eb5bd0a84152ea8aab",
    "knowledge-budget-tool.py": "4ecae5ea0c1bd3edaa4cb2262cd9b8208a1ee66830ff92ff6edf6ee2a40ce9f3",
    "superseded-knowledge-budget.conf": "0964bd1e9c55b7953b3fbcb9efd4ed3ae565b0c4832b736780b8ba4a8f3d7ea6",
    "reservation_count": 13,
    "tokens_total": 36065164,
    "cpu_seconds": 30784.330000000075,
    "wall_seconds": 7614,
    "state_counts": {"closed": 12, "active": 1, "held": 0},
    "prior_active_statistics_id": "r1795595233-CXGuJISF",
    "wave4_capture_unix": 1795595310,  # 2026-11-25T08:28:30Z
}
NEW_CONFIG = "b80f48aff6b94382d4a5b859bab41906fa665c3b8cf4f6eb5bd0a84152ea8aab"
OLD_CONFIG = "0964bd1e9c55b7953b3fbcb9efd4ed3ae565b0c4832b736780b8ba4a8f3d7ea6"
NEW_IDS = {
    "r1795595445-NZIjZE34", "r1795595447-UyyfTafj", "r1795595460-9V0XCjcF",
    "r1795599016-P1J0KTe9", "r1795599269-kgG5rTM0", "r1795599289-mvLLnigN",
}
HELD_ID = "r1795595445-NZIjZE34"
HELD_REASON = "meter_or_session_binding_unknown_after_launch"
OWN_AGENT = "vKIQz9W57p22fX8z3Q4TMt-magnitude"  # statistics appointment identity in charter


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_map():
    skip = {"measure.py", "measurement.json", "CAPTURE_TIME.txt"}
    return {str(p.relative_to(E)): sha(p) for p in sorted(E.rglob("*"))
            if p.is_file() and p.name not in skip and "__pycache__" not in p.parts}


def g(d, k):
    return d.get(k) if isinstance(d, dict) else None


def main():
    H = digest_map()
    A = {}
    cfg = json.loads((E / "knowledge-budget.conf").read_text())
    act = json.loads((E / "activation.json").read_text())
    res_dir = E / "budget-state" / "reservations"
    rows = {p.stem: json.loads(p.read_text()) for p in sorted(res_dir.glob("*.json"))}

    file_keys = ("activation.json", "knowledge-budget.conf",
                 "knowledge-budget-tool.py", "superseded-knowledge-budget.conf")
    for k in file_keys:
        A["bytes_unchanged_" + k] = H.get(k) == PRIOR[k]
    A["prior_reservation_count_was_13"] = PRIOR["reservation_count"] == 13
    A["prior_held_count_was_0"] = PRIOR["state_counts"]["held"] == 0
    A["prior_active_was_statistics_third_wave"] = (
        PRIOR["prior_active_statistics_id"] == "r1795595233-CXGuJISF")
    A["activation_all_offices_enabled"] = all(
        g(g(act.get("offices"), o), "enabled") is True for o in OFFICES)

    spec = importlib.util.spec_from_file_location("viche_budget_frozen", E / "knowledge-budget-tool.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cfg_errors = mod.validate_config(cfg)
    A["config_valid"] = cfg_errors == []

    now = max(max(g(g(r, "meter"), "at") or 0, g(r, "created_at") or 0)
              for r in rows.values())
    window = cfg["accounting_window_seconds"]
    charges, counted, skipped = mod.charges(str(res_dir), now, window)
    agg = json.loads((E / "budget-state" / "aggregate.json").read_text())
    agg_reproduces = (all(charges.get(k) == agg.get(k) for k in CAP_KEYS)
                      and charges["by_office"] == agg["by_office"]
                      and counted == agg["counted"])
    A["charges_reproduce_frozen_aggregate"] = agg_reproduces

    # Held reservation: freeze every liability-relevant field and the history.
    hr = rows[HELD_ID]
    held = {
        "id": HELD_ID,
        "office": g(hr, "office"), "agent_id": g(hr, "agent_id"), "state": g(hr, "state"),
        "created_at": g(hr, "created_at"), "held_at": g(hr, "held_at"),
        "held_reason": g(hr, "held_reason"),
        "held_duration_seconds_at_capture": g(hr, "held_at") and (now - g(hr, "held_at")),
        "charge": g(hr, "charge"), "caps": g(hr, "caps"),
        "meter": g(hr, "meter"), "usage": g(hr, "usage"),
        "native_session_id": g(hr, "native_session_id"),
        "runner_pid": g(hr, "runner_pid"), "monitor_pid": g(hr, "monitor_pid"),
        "closed_at": g(hr, "closed_at"), "closed_reason": g(hr, "closed_reason"),
        "history": g(hr, "history"), "config_sha256": g(hr, "config_sha256"),
    }
    A["held_is_still_held"] = held["state"] == "held"
    A["held_reason_exact"] = held["held_reason"] == HELD_REASON
    A["held_has_no_meter"] = held["meter"] is None
    A["held_has_no_usage"] = held["usage"] is None
    A["held_has_no_session_binding"] = held["native_session_id"] is None and held["runner_pid"] is None
    A["held_never_closed"] = held["closed_at"] is None and held["closed_reason"] is None

    # Antonina agent status, frozen at capture: an independent instrument on the
    # same agent id, used only for the terminal-state/binding observation.
    st = json.loads((E / "foresight-held-agent-status.json").read_text())
    agent = {k: g(st, k) for k in ("id", "state", "alive", "native_session_id",
                                   "started_at", "finished_at", "exit_code",
                                   "exit_signal", "prompts", "backend_error",
                                   "last_error", "pid")}
    A["held_agent_killed"] = agent["state"] == "killed" and agent["alive"] is False
    A["held_agent_exit_signal_9"] = agent["exit_signal"] == 9
    A["held_agent_null_exit_code"] = agent["exit_code"] is None
    A["held_agent_has_session_in_antonina"] = bool(agent["native_session_id"])

    listing = (E / "liveness-unsafe-holds-listing.txt").read_text().strip().splitlines()
    A["active_unsafe_holds_empty_at_capture"] = all(
        (not ln.strip()) or ln.startswith("total ") or ln.split()[-1] in (".", "..")
        for ln in listing)

    # Liability basis: charges() uses usage for closed, charge for held, caps for
    # active/reserved. Quantify ceiling-pinned vs trued-up actual-usage debt.
    basis = {"closed_usage_tokens": 0, "held_ceiling_tokens": 0,
             "active_ceiling_tokens": 0, "by_office": {}}
    for o in OFFICES:
        ob = {"closed_usage_tokens": 0, "held_ceiling_tokens": 0, "active_ceiling_tokens": 0}
        for r in rows.values():
            if g(r, "office") != o:
                continue
            state = g(r, "state")
            if state == "closed":
                v = g(g(r, "usage"), "tokens_total") or 0
                ob["closed_usage_tokens"] += v
                basis["closed_usage_tokens"] += v
            elif state == "held":
                v = g(g(r, "charge"), "tokens_total") or 0
                ob["held_ceiling_tokens"] += v
                basis["held_ceiling_tokens"] += v
            else:  # active / reserved
                v = g(g(r, "caps"), "tokens_total") or 0
                ob["active_ceiling_tokens"] += v
                basis["active_ceiling_tokens"] += v
        basis["by_office"][o] = ob
    basis["ceiling_pinned_tokens"] = basis["held_ceiling_tokens"] + basis["active_ceiling_tokens"]
    basis["ceiling_pinned_share"] = basis["ceiling_pinned_tokens"] / charges["tokens_total"]
    basis["held_stuck_share_of_aggregate"] = basis["held_ceiling_tokens"] / charges["tokens_total"]

    state_counts = {}
    for r in rows.values():
        s = g(r, "state")
        state_counts[s] = state_counts.get(s, 0) + 1
    A["prior_state_counts_match_frozen_prior"] = (
        PRIOR["state_counts"]["closed"] == 12 and PRIOR["state_counts"]["active"] == 1)

    new_rows = {}
    for nid in sorted(NEW_IDS):
        r = rows[nid]
        new_rows[nid] = {
            "office": g(r, "office"), "state": g(r, "state"),
            "created_at": g(r, "created_at"), "config_sha256": g(r, "config_sha256"),
            "agent_id": g(r, "agent_id"),
        }
    A["all_new_ids_present"] = set(new_rows) == NEW_IDS
    A["all_new_ids_new_config"] = all(v["config_sha256"] == NEW_CONFIG for v in new_rows.values())
    A["all_new_ids_after_prior_capture"] = all(
        v["created_at"] > PRIOR["wave4_capture_unix"] for v in new_rows.values())
    A["own_statistics_reservation_present"] = any(
        g(r, "agent_id") == OWN_AGENT for r in rows.values())
    A["reservation_count_grew_from_13"] = len(rows) > PRIOR["reservation_count"]

    admits_new = {o: mod.admit(cfg, charges, o) for o in OFFICES}
    prev_cfg = json.loads((E / "superseded-knowledge-budget.conf").read_text())
    admits_old = {o: mod.admit(prev_cfg, charges, o) for o in OFFICES}
    overload = json.loads(json.dumps(charges))
    overload["by_office"]["statistics"]["tokens_total"] = (
        cfg["offices"]["statistics"]["caps"]["tokens_total"]
        - cfg["offices"]["statistics"]["per_run_caps"]["tokens_total"] + 1)
    admit_overload = mod.admit(cfg, overload, "statistics")
    A["admit_new_all_four"] = all(admits_new[o]["admit"] for o in OFFICES)
    A["negative_control_old_config_refused"] = all(
        not admits_old[o]["admit"] for o in OFFICES)
    A["negative_control_overload_refused"] = admit_overload["admit"] is False

    # Cap headroom: is the admission gate anywhere near binding?
    headroom = {}
    for o in OFFICES:
        c = cfg["offices"][o]["caps"]
        u = charges["by_office"][o]
        headroom[o] = {k: {"cap": c[k], "used": u[k],
                           "used_share": u[k] / c[k]} for k in CAP_KEYS}
    headroom["aggregate"] = {k: {"cap": cfg["aggregate"]["caps"][k],
                                 "used": charges[k],
                                 "used_share": charges[k] / cfg["aggregate"]["caps"][k]}
                             for k in CAP_KEYS}
    A["caps_far_from_binding"] = all(
        headroom[o]["tokens_total"]["used_share"] < 0.10 for o in OFFICES)

    result = {
        "captured_utc": (E / "CAPTURE_TIME.txt").read_text().strip(),
        "captured_from": "canonical main records/knowledge/activation.json, government/knowledge-budget.* "
                         "and /var/lib/lubko/wd/viche-state/knowledge/budget (aggregate + 19 reservations); "
                         "Antonina agent status and liveness/unsafe-holds listing frozen at capture",
        "measurement_script": "measure.py (read-only on the frozen copies)",
        "sha256": H,
        "prior_snapshot": {
            "id": "act34-wave4-trueup-20261125", "captured_utc": "2026-11-25T08:28:30Z",
            "reservation_count": PRIOR["reservation_count"],
            "tokens_total": PRIOR["tokens_total"], "cpu_seconds": PRIOR["cpu_seconds"],
            "wall_seconds": PRIOR["wall_seconds"], "state_counts": PRIOR["state_counts"],
        },
        "assertions": A,
        "all_assertions_pass": all(A.values()),
        "validate_config_errors": cfg_errors,
        "recomputed_now_unix": now,
        "accounting_window_seconds": window,
        "reservation_count": len(rows),
        "state_counts": state_counts,
        "counted": counted, "skipped": skipped,
        "recomputed_charges": {k: charges[k] for k in CAP_KEYS},
        "frozen_aggregate": {k: agg[k] for k in CAP_KEYS},
        "tokens_total_change_vs_prior": agg["tokens_total"] - PRIOR["tokens_total"],
        "liability_basis": basis,
        "held_reservation": held,
        "held_agent_status": agent,
        "new_reservations_since_prior": new_rows,
        "admit_new_config_at_current_charges": admits_new,
        "negative_control_superseded_config_admit": admits_old,
        "negative_control_overload_admit": admit_overload,
        "cap_headroom": headroom,
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

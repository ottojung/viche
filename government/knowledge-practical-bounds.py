#!/usr/bin/env python3
"""Act 29 Economy — practical, HONEST operational cost ceilings for broad model offices.

This module implements the tiered controls the Founder asked for on 2026-11-23,
so the four adaptive knowledge offices can actually dispatch under bounded risk
instead of being vetoed by an unattainable strict-hard-cap proof.

It is INERT until a lawfully enacted amendment (Act 34 or successor) and a
signed Executive permit exist. It does NOT edit activation.json, does NOT enable
any office, and does NOT reset or rebrand the accrued 45-day UPPER_BOUND ledger.

Honesty rules (deliberate, not a caveat to be hidden):
  * A -free provider tier has cost == 0 by provider contract. Verified live on
    billy-dev 2026-11-23: hy4-flash-free session cost=0.0 with real token use.
    The binding limits there are provider usage quotas (HTTP 429 time windows)
    and HOST resources (CPU/wall/inodes/concurrency), not money.
  * OpenCode's 20-second token poll is STOP-ON-DETECTION only. It is never
    represented as a strict in-flight hard cap. cap_kind is always explicit.
  * A paid/provider-billed model is refused unless a provider-enforced hard
    ceiling (prepaid key or gateway limit) is configured and independently
    verified. No fabricated numeric "proof" is accepted.
  * Per-request input/output ceilings REDUCE exposure; OpenCode auto-continuation
    can overshoot them, so the accounting charge uses a continuation multiplier.
    No claim is made that generation stops exactly at the ceiling.

Usage:
  knowledge-practical-bounds.py validate PROFILE_JSON
  knowledge-practical-bounds.py exposure PROFILE_JSON MODEL_ID
  knowledge-practical-bounds.py admit PROFILE_JSON AGG_JSON OFFICE OPEN_COUNT
  knowledge-practical-bounds.py ambiguous PROFILE_JSON RESERVATION_JSON
"""
import json
import sys

CAP_KEYS = ("tokens_total", "cpu_seconds", "wall_seconds")
LEDGER_NOTE = "45-day cumulative UPPER_BOUND ledger; never reset or rebranded"

# Honest defaults. All ceilings are ACCOUNTING/exposure bounds, not provider guarantees.
DEFAULT_PROFILE = {
    "schema": "viche-knowledge-practical-bounds-v1",
    "cap_kind": "stop_on_detection",
    "strict_hard_cap_claimed": False,
    "monitor_interval_seconds": 20,
    "max_concurrent_per_office": 1,
    "max_input_tokens_per_request": 8192,
    "max_output_tokens_per_request": 4096,
    "max_continuations": 2,
    "max_wall_seconds_per_invocation": 900,
    "max_cpu_seconds_per_invocation": 300,
    "per_office_caps": {"tokens_total": 400000, "cpu_seconds": 1800, "wall_seconds": 3600},
    "aggregate_caps": {"tokens_total": 1600000, "cpu_seconds": 7200, "wall_seconds": 14400},
    "accounting_window_seconds": 3888000,
    "zero_billing_tiers": ["-free"],
    "provider_hard_ceiling": None,
    "enabled_offices": [],
}


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0


def validate(profile):
    """Fail closed on a malformed or dishonest profile."""
    problems = []
    if profile.get("schema") != DEFAULT_PROFILE["schema"]:
        problems.append("wrong schema")
    if profile.get("cap_kind") != "stop_on_detection":
        problems.append("cap_kind must be stop_on_detection (no strict hard cap claim)")
    if profile.get("strict_hard_cap_claimed") is not False:
        problems.append("strict hard cap may not be claimed")
    for key in ("monitor_interval_seconds", "max_concurrent_per_office",
                "max_input_tokens_per_request", "max_output_tokens_per_request",
                "max_continuations", "max_wall_seconds_per_invocation",
                "max_cpu_seconds_per_invocation", "accounting_window_seconds"):
        if not is_number(profile.get(key)) or profile[key] <= 0:
            problems.append("invalid positive integer field: %s" % key)
    if profile.get("accounting_window_seconds") != 3888000:
        problems.append("45-day accounting window changed")
    for scope in ("per_office_caps", "aggregate_caps"):
        caps = profile.get(scope)
        if not isinstance(caps, dict):
            problems.append("%s missing" % scope)
            continue
        for key in CAP_KEYS:
            if not is_number(caps.get(key)) or caps[key] <= 0:
                problems.append("%s.%s invalid" % (scope, key))
    agg = profile.get("aggregate_caps", {})
    office = profile.get("per_office_caps", {})
    for key in CAP_KEYS:
        if isinstance(agg.get(key), (int, float)) and isinstance(office.get(key), (int, float)):
            if agg[key] < office[key]:
                problems.append("aggregate.%s < office.%s" % (key, key))
    tiers = profile.get("zero_billing_tiers")
    if not isinstance(tiers, list) or not tiers or not all(isinstance(t, str) and t for t in tiers):
        problems.append("zero_billing_tiers invalid")
    if not isinstance(profile.get("enabled_offices"), list):
        problems.append("enabled_offices must be a list (empty means inert)")
    return problems


def billing_tier(profile, model_id):
    """zero_free_tier when the model id carries a configured free component."""
    mid = str(model_id)
    free = any(t in mid.split("/") or mid.endswith(t) or ("-" + t.lstrip("-")) in mid
               for t in profile.get("zero_billing_tiers", []))
    if free:
        return {"tier": "zero_free_tier", "billing_exposure": 0,
                "binding_limits": ["provider usage quota (429 time window)",
                                   "host CPU/wall", "concurrency", "inodes"]}
    if profile.get("provider_hard_ceiling"):
        return {"tier": "paid_with_provider_ceiling",
                "billing_exposure": profile["provider_hard_ceiling"],
                "binding_limits": ["provider-enforced hard ceiling (must be independently verified)"]}
    return {"tier": "paid_unbounded", "billing_exposure": None,
            "binding_limits": [], "admit": False,
            "reason": "paid model requires a provider-enforced hard ceiling; none configured"}


def exposure(profile, model_id):
    """Conservative per-request exposure and honest cap labeling."""
    tier = billing_tier(profile, model_id)
    inp = profile["max_input_tokens_per_request"]
    out = profile["max_output_tokens_per_request"]
    mult = 1 + profile["max_continuations"]
    return {
        "model": str(model_id),
        "cap_kind": profile["cap_kind"],
        "strict_hard_cap": False,
        "per_request_input_ceiling": inp,
        "per_request_output_ceiling": out,
        "continuation_multiplier": mult,
        "worst_case_charge_tokens": inp + out * mult,
        "charge_is_accounting_bound_only": True,
        "billing": tier,
        "ledger": LEDGER_NOTE,
    }


def admit(profile, agg, office, open_count):
    """Admit a dispatch under practical bounds: concurrency + cumulative caps."""
    problems = validate(profile)
    if problems:
        return {"admit": False, "reason": "invalid profile: %s" % "; ".join(problems)}
    if office not in profile.get("enabled_offices", []):
        return {"admit": False, "reason": "office not enabled by a lawful permit"}
    if open_count >= profile["max_concurrent_per_office"]:
        return {"admit": False, "reason": "concurrency ceiling reached for %s" % office}
    by = agg.get("by_office", {}) if isinstance(agg, dict) else {}
    office_used = by.get(office, {}) if isinstance(by, dict) else {}
    # Charge uses the configured maximum exposure (no model id at admission).
    charge = profile["max_input_tokens_per_request"] + \
             profile["max_output_tokens_per_request"] * (1 + profile["max_continuations"])
    for key in CAP_KEYS:
        off_cap = profile["per_office_caps"][key]
        agg_cap = profile["aggregate_caps"][key]
        unit = charge if key == "tokens_total" else (
            profile["max_cpu_seconds_per_invocation"] if key == "cpu_seconds"
            else profile["max_wall_seconds_per_invocation"])
        if not is_number(agg.get(key)) or not is_number(office_used.get(key)):
            return {"admit": False, "reason": "missing/invalid cumulative %s accounting" % key}
        if office_used[key] + unit > off_cap:
            return {"admit": False, "reason": "%s office cap would be exceeded" % key}
        if agg[key] + unit > agg_cap:
            return {"admit": False, "reason": "%s aggregate cap would be exceeded" % key}
    return {"admit": True, "reason": "within practical bounds",
            "charge": {"tokens_total": charge,
                       "cpu_seconds": profile["max_cpu_seconds_per_invocation"],
                       "wall_seconds": profile["max_wall_seconds_per_invocation"]},
            "cap_kind": profile["cap_kind"], "ledger": LEDGER_NOTE}


def ambiguous(profile, reservation):
    """Fail closed on kill/overrun/ambiguous exit: hold the FULL prepaid charge."""
    caps = reservation.get("caps", {}) if isinstance(reservation, dict) else {}
    held = {k: caps.get(k, profile["per_office_caps"][k]) for k in CAP_KEYS}
    return {"state": "held", "charge": held, "released": 0,
            "reason": "ambiguous exit: full prepaid exposure retained, never released",
            "cap_kind": profile["cap_kind"], "ledger": LEDGER_NOTE}


def main(argv):
    if len(argv) < 2:
        print("usage: knowledge-practical-bounds.py validate|exposure|admit|ambiguous ...", file=sys.stderr)
        return 2
    cmd = argv[1]
    profile = load(argv[2])
    if cmd == "validate":
        out = {"ok": not validate(profile), "problems": validate(profile)}
    elif cmd == "exposure":
        out = exposure(profile, argv[3])
    elif cmd == "admit":
        out = admit(profile, load(argv[3]), argv[4], int(argv[5]))
    elif cmd == "ambiguous":
        out = ambiguous(profile, load(argv[3]))
    else:
        print("unknown command", file=sys.stderr)
        return 2
    print(json.dumps(out, sort_keys=True))
    return 0 if (cmd != "validate" or out["ok"]) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

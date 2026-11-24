#!/usr/bin/env python3
"""Targeted verification of the measured recurring-envelope candidates.

Uses ONLY the authoritative, read-only government primitives and the real
canonical ledger. Does not install, activate, sign, dispatch, or run the full
source suite. Writes one machine-readable result file next to this script.
"""
import copy
import json
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOWN = Path("/var/lib/lubko/wd/viche")
TOOL = TOWN / "government/knowledge-budget-tool.py"
RESDIR = Path("/var/lib/lubko/wd/viche-state/knowledge/budget/reservations")
LEDGER = Path("/var/lib/lubko/wd/viche-state/knowledge/budget/aggregate.json")
CANON = TOWN / "government/knowledge-budget.conf"
PRIMARY = HERE / "act34-recurring-envelope-primary-20261124.json"
FALLBACK = HERE / "act34-recurring-envelope-two-wave-fallback-20261124.json"
OUT = HERE / "act34-recurring-envelope-verification-20261124.json"
WINDOW = 3888000
OFFICES = ("statistics", "foresight", "strategy", "spying")
KEYS = ("tokens_total", "cpu_seconds", "wall_seconds")


def run(*args):
    p = subprocess.run(["python3", str(TOOL)] + [str(a) for a in args],
                       capture_output=True, text=True)
    out = p.stdout.strip()
    try:
        parsed = json.loads(out.splitlines()[-1]) if out else None
    except ValueError:
        parsed = out
    return {"exit": p.returncode, "stdout": out, "stderr": p.stderr.strip(),
            "json": parsed}


def load(path):
    return json.loads(Path(path).read_text())


def admit(cfg_path, agg, office):
    return run("admit", cfg_path, json.dumps(agg), office)["json"]


def projected(agg, cfg, turns):
    a = copy.deepcopy(agg)
    for office in OFFICES:
        for k in KEYS:
            unit = cfg["offices"][office]["per_run_caps"][k]
            a["by_office"][office][k] += turns * unit
            a[k] += turns * unit
    return a


report = {"generated_epoch": int(time.time()), "sources": {
    "tool": str(TOOL), "reservations": str(RESDIR), "ledger": str(LEDGER),
    "canonical_config": str(CANON), "primary_config": str(PRIMARY),
    "fallback_config": str(FALLBACK)}}

primary, fallback, canon = load(PRIMARY), load(FALLBACK), load(CANON)
report["sha256"] = {}
for name, path in (("primary", PRIMARY), ("fallback", FALLBACK), ("canonical", CANON)):
    import hashlib
    report["sha256"][name] = hashlib.sha256(Path(path).read_bytes()).hexdigest()

# Validation of both candidates and the canonical config.
report["validate"] = {
    "primary": run("validate", PRIMARY)["json"],
    "fallback": run("validate", FALLBACK)["json"],
    "canonical": run("validate", CANON)["json"],
}

# Reconstruct the ledger independently and compare with the disk aggregate.
agg = run("aggregate", RESDIR, WINDOW, int(time.time()))["json"]
disk = load(LEDGER)
report["ledger_reconstructed"] = agg
report["ledger_matches_disk"] = all(agg.get(k) == disk.get(k) for k in KEYS) and \
    sorted(agg.get("counted", [])) == sorted(disk.get("counted", []))

# Cost and exit verification from the primary source rows.
rows = []
for path in sorted(Path(RESDIR).glob("*.json")):
    row = load(path)
    rows.append({"id": row["id"], "office": row["office"], "state": row["state"],
                 "closed_reason": row.get("closed_reason"),
                 "tokens_total": row["usage"]["tokens_total"],
                 "cpu_seconds": row["usage"]["cpu_seconds"],
                 "wall_seconds": row["usage"]["wall_seconds"],
                 "cost": row["usage"]["cost"],
                 "cost_reported": row["usage"]["cost_reported"],
                 "config_sha256": row["config_sha256"]})
report["reservation_rows"] = sorted(rows, key=lambda r: r["office"])
report["all_zero_cost"] = all(r["cost"] == 0.0 and r["cost_reported"] for r in rows)
report["all_closed"] = all(r["state"] == "closed" for r in rows)

# Admission on the REAL (already-charged) ledger.
report["admit_real_ledger"] = {
    "canonical": {o: admit(CANON, agg, o) for o in OFFICES},
    "primary": {o: admit(PRIMARY, agg, o) for o in OFFICES},
    "fallback": {o: admit(FALLBACK, agg, o) for o in OFFICES},
}

# Exact admission boundary: n = follow-on turns already charged; admit() tests
# the NEXT (n+1) turn against the non-resettable cumulative cap.
def boundary(cfg_path, cfg):
    out = {}
    for office in OFFICES:
        admitted = []
        for n in range(0, 50):
            dec = admit(cfg_path, projected(agg, cfg, n), office)
            admitted.append({"already_charged_turns": n, "admit": dec.get("admit"),
                             "reason": dec.get("reason")})
        first_refused = next((r["already_charged_turns"] for r in admitted
                              if not r["admit"]), None)
        out[office] = {"first_refused_after_n_charged": first_refused,
                       "sequence": admitted}
    return out

report["admission_boundary_primary"] = boundary(PRIMARY, primary)
report["admission_boundary_fallback"] = boundary(FALLBACK, fallback)

# Headroom after the real first wave, per candidate.
def headroom(cfg):
    h = {}
    for o in OFFICES:
        h[o] = {k: cfg["offices"][o]["caps"][k] - agg["by_office"][o][k] for k in KEYS}
    h["aggregate"] = {k: cfg["aggregate"]["caps"][k] - agg[k] for k in KEYS}
    return h

report["headroom_primary"] = headroom(primary)
report["headroom_fallback"] = headroom(fallback)

# Physical host sanity check for the primary cumulative CPU cap.
# Whole-host UPPER_BOUND charge = 4 x physical busy core-seconds (4 CPUs).
phys_cap = 4 * WINDOW
report["physical_cpu_check"] = {
    "cpus": 4, "window_seconds": WINDOW,
    "physical_core_seconds_available": phys_cap,
    "primary_aggregate_cpu_charge": primary["aggregate"]["caps"]["cpu_seconds"],
    "implied_physical_core_seconds": primary["aggregate"]["caps"]["cpu_seconds"] / 4,
    "fraction_of_physical_capacity": primary["aggregate"]["caps"]["cpu_seconds"] / 4 / phys_cap,
}

OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "ledger_matches_disk": report["ledger_matches_disk"],
    "all_zero_cost": report["all_zero_cost"],
    "all_closed": report["all_closed"],
    "validate": {k: v.get("ok") for k, v in report["validate"].items()},
    "admit_real_canonical": {o: report["admit_real_ledger"]["canonical"][o]["admit"] for o in OFFICES},
    "admit_real_primary": {o: report["admit_real_ledger"]["primary"][o]["admit"] for o in OFFICES},
    "admit_real_fallback": {o: report["admit_real_ledger"]["fallback"][o]["admit"] for o in OFFICES},
    "first_refused_primary": {o: report["admission_boundary_primary"][o]["first_refused_after_n_charged"] for o in OFFICES},
    "first_refused_fallback": {o: report["admission_boundary_fallback"][o]["first_refused_after_n_charged"] for o in OFFICES},
}, indent=2, sort_keys=True))

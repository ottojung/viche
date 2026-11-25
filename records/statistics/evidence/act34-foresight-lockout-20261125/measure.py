#!/usr/bin/env python3
"""Hermetic, byte-frozen re-measurement of the foresight unbound-hold lockout.

Reads ONLY the primary copies frozen in this directory. It never reads or writes
the live budget ledger, never calls a live Antonina agent command (an `antonina`
stub is first on PATH), and probes a minimal scratch SQLite meter with the same
schema columns the deployed tool requires.

The deployed knowledge-budget.sh and knowledge-budget-tool.py are re-executed
from frozen bytes against scratch state directories. `guard` and `resolve` are
the ACTUAL deployed functions, not a paraphrase. A falsifier control removes
only the held row and re-runs `guard foresight`; if that does not flip the
decision to `guard ok`, the claimed sole cause is false.

The 09:54Z recovery-steward Post and the 10:18Z Judiciary disposition were read
as context/hypotheses only. No factual claim below rests on either: every claim
is re-derived here from byte-frozen deployed sources and scratch re-execution.

Content assertions against the prior snapshot (act34-held-liability-20261125,
captured 2026-11-25T09:35:55Z) are hardcoded. A mismatch is a falsifier, not a
value to be silently updated.
"""
import datetime
import hashlib
import importlib.util
import json
import os
import pathlib
import shutil
import sqlite3
import subprocess
import sys
import tempfile

E = pathlib.Path(__file__).resolve().parent
sys.dont_write_bytecode = True
OFFICES = ("statistics", "foresight", "strategy", "spying")
CAP_KEYS = ("tokens_total", "cpu_seconds", "wall_seconds")
HELD_ID = "r1795595445-NZIjZE34"
HELD_REASON = "meter_or_session_binding_unknown_after_launch"

PRIOR = {
    "activation.json": "921b99ae1288769b4460ea25641cad93da8d1ed3c98ce1adfbecbd32b261587b",
    "knowledge-budget.conf": "b80f48aff6b94382d4a5b859bab41906fa665c3b8cf4f6eb5bd0a84152ea8aab",
    "knowledge-budget-tool.py": "4ecae5ea0c1bd3edaa4cb2262cd9b8208a1ee66830ff92ff6edf6ee2a40ce9f3",
    "reservation_count": 19,
    "tokens_total": 81913486,
    "held_duration_seconds": 3867,
    "state_counts": {"closed": 15, "active": 3, "held": 1},
    "capture_unix": 1795599355,  # 2026-11-25T09:35:55Z
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_tool():
    spec = importlib.util.spec_from_file_location("kbtool_frozen", E / "knowledge-budget-tool.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def utc_unix(stamp):
    dt = datetime.datetime.strptime(stamp.strip(), "%Y-%m-%dT%H:%M:%SZ")
    return int(dt.replace(tzinfo=datetime.timezone.utc).timestamp())


def make_scratch(base, rows, status_path, tool):
    """Materialise a scratch budget tree from frozen bytes; return its paths."""
    budget = base / "budget"
    res = budget / "reservations"
    res.mkdir(parents=True)
    (budget / "lock").touch()
    for name, row in rows.items():
        (res / (name + ".json")).write_text(json.dumps(row, sort_keys=True))
    db = base / "meter.sqlite"
    con = sqlite3.connect(str(db))
    con.execute(
        "CREATE TABLE session_v2 (id TEXT PRIMARY KEY, cost REAL, time_updated INTEGER, "
        "tokens_input INTEGER, tokens_output INTEGER, tokens_reasoning INTEGER, "
        "tokens_cache_read INTEGER, tokens_cache_write INTEGER)")
    con.commit()
    con.close()
    bindir = base / "bin"
    bindir.mkdir()
    stub = bindir / "antonina"
    stub.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = agent ] && [ \"$2\" = status ]; then cat \"$STUB_STATUS\"; exit 0; fi\n"
        "printf '%s\\n' \"$*\" >> \"$STUB_LOG\"\n"
        "exit 0\n")
    stub.chmod(0o755)
    env = os.environ.copy()
    env.update({
        "VICHE_BUDGET_STATE": str(budget),
        "VICHE_BUDGET_CONFIG": str(E / "knowledge-budget.conf"),
        "VICHE_BUDGET_TOOL": str(E / "knowledge-budget-tool.py"),
        "VICHE_BUDGET_DB": str(db),
        "STUB_STATUS": str(status_path),
        "STUB_LOG": str(base / "antonina-calls.log"),
        "PATH": str(bindir) + os.pathsep + env.get("PATH", ""),
    })
    # Recompute the aggregate for THIS row set so guard's aggregate check is clean.
    totals, counted, skipped = tool.charges(str(res), utc_unix((E / "CAPTURE_TIME.txt").read_text()), 3888000)
    totals["counted"] = counted
    totals["skipped"] = skipped
    (budget / "aggregate.json").write_text(json.dumps(totals, sort_keys=True))
    return budget, res, db, env


def run_sh(env, *args):
    proc = subprocess.run(["/bin/sh", str(E / "knowledge-budget.sh"), *args],
                          env=env, cwd="/tmp", capture_output=True, text=True, timeout=60)
    return {"argv": ["knowledge-budget.sh", *args], "rc": proc.returncode,
            "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}


def decompose(rows, now, window):
    basis = {"closed_usage": 0, "held_charge": 0, "active_caps": 0, "reserved_caps": 0}
    counts = {}
    for row in rows.values():
        state = row["state"]
        counts[state] = counts.get(state, 0) + 1
        caps = row["caps"]
        if state == "closed":
            basis["closed_usage"] += int(row["usage"]["tokens_total"])
        elif state == "held":
            basis["held_charge"] += int(row["charge"]["tokens_total"])
        elif state == "active":
            basis["active_caps"] += int(caps["tokens_total"])
        elif state == "reserved":
            basis["reserved_caps"] += int(caps["tokens_total"])
    return basis, counts


def main():
    capture = (E / "CAPTURE_TIME.txt").read_text().strip()
    now = utc_unix(capture)
    tool = load_tool()
    cfg, errors = tool.load_config(str(E / "knowledge-budget.conf"))
    assert not errors and not tool.validate_config(cfg), "frozen config invalid"
    rows = {p.stem: json.loads(p.read_text())
            for p in sorted((E / "budget-state" / "reservations").glob("*.json"))}
    frozen_agg = json.loads((E / "budget-state" / "aggregate.json").read_text())
    totals, counted, skipped = tool.charges(str(E / "budget-state" / "reservations"), now, 3888000)
    totals["counted"] = counted
    totals["skipped"] = skipped

    A = {}
    H = {k: sha(E / k) for k in ("activation.json", "knowledge-budget.conf",
                                 "knowledge-budget-tool.py", "knowledge-budget.sh",
                                 "superseded-knowledge-budget.conf")}
    for k in ("activation.json", "knowledge-budget.conf", "knowledge-budget-tool.py"):
        A["bytes_unchanged_vs_0935_" + k] = H[k] == PRIOR[k]
    A["frozen_config_valid"] = not errors and not tool.validate_config(cfg)
    A["aggregate_reproduced_exactly"] = (totals == frozen_agg)
    A["prior_count_was_19"] = PRIOR["reservation_count"] == 19
    A["held_row_still_present"] = HELD_ID in rows
    held = rows[HELD_ID]
    A["held_state_still_held"] = held["state"] == "held"
    A["held_reason_unchanged"] = held["held_reason"] == HELD_REASON
    A["held_native_session_null"] = held.get("native_session_id") is None
    A["held_meter_and_usage_null"] = held.get("meter") is None and held.get("usage") is None
    A["held_charge_at_frozen_ceiling"] = int(held["charge"]["tokens_total"]) == 11320103
    A["held_no_closure_fields"] = all(held.get(k) is None for k in ("closed_at", "closed_reason", "resolved_by"))
    held_seconds = now - int(held["held_at"])
    A["held_longer_than_prior_3867s"] = held_seconds > PRIOR["held_duration_seconds"]

    basis, counts = decompose(rows, now, 3888000)
    total_tokens = totals["tokens_total"]
    active_open = {o: [r["id"] for r in rows.values()
                       if r["office"] == o and r["state"] in ("reserved", "active", "held")]
                   for o in OFFICES}
    admit = {o: tool.admit(cfg, totals, o) for o in OFFICES}
    A["admit_all_four_true"] = all(v["admit"] is True for v in admit.values())
    A["admit_foresight_true"] = admit["foresight"]["admit"] is True
    # Negative controls.
    old_cfg, _ = tool.load_config(str(E / "superseded-knowledge-budget.conf"))
    A["superseded_config_refuses_all"] = all(
        tool.admit(old_cfg, totals, o)["admit"] is False for o in OFFICES)
    over = dict(totals)
    over["by_office"] = dict(totals["by_office"])
    over["by_office"]["statistics"] = {"tokens_total": cfg["aggregate"]["caps"]["tokens_total"]}
    A["over_cap_refuses_statistics"] = tool.admit(cfg, over, "statistics")["admit"] is False

    # ---- hermetic re-execution of the DEPLOYED shell functions ----------------
    with tempfile.TemporaryDirectory(prefix="stat-lockout-", dir="/tmp/opencode") as td:
        base = pathlib.Path(td)
        _, _, _, env = make_scratch(base, rows, E / "foresight-held-agent-status.json", tool)
        guard_live = run_sh(env, "guard", "foresight")
        A["guard_foresight_refused"] = guard_live["rc"] != 0
        A["guard_foresight_blames_held_row"] = HELD_ID in guard_live["stderr"]
        guard_other = {o: run_sh(env, "guard", o) for o in ("statistics", "strategy", "spying")}

        # Falsifier control: remove ONLY the held row, recompute aggregate, retry.
        b2 = base / "control_noheld"
        rows2 = {k: dict(v) for k, v in rows.items() if k != HELD_ID}
        _, _, _, env2 = make_scratch(b2, rows2, E / "foresight-held-agent-status.json", tool)
        guard_noheld = run_sh(env2, "guard", "foresight")
        A["guard_flips_ok_when_held_removed"] = (
            guard_noheld["rc"] == 0 and "guard ok: foresight" in guard_noheld["stdout"])

        # Actual deployed resolve() on a scratch copy of the held row.
        b3 = base / "resolve_probe"
        _, res3, _, env3 = make_scratch(b3, rows, E / "foresight-held-agent-status.json", tool)
        resolve_run = run_sh(env3, "resolve", HELD_ID, "statistics-hermetic-reexec")
        after = json.loads((res3 / (HELD_ID + ".json")).read_text())
        A["resolve_rc_zero"] = resolve_run["rc"] == 0
        A["resolve_left_row_held"] = after["state"] == "held"
        A["resolve_did_not_close"] = all(
            after.get(k) is None for k in ("closed_at", "closed_reason", "resolved_by"))
        A["resolve_reason_was_identity_unresolved"] = (
            after.get("held_reason") == "operator_resolution_identity_unresolved")
        A["resolve_kept_full_ceiling"] = int(after["charge"]["tokens_total"]) == 11320103
        calls = (b3 / "antonina-calls.log")
        A["no_live_antonina_call_in_scratch"] = (not calls.exists()) or calls.read_text() == ""
        raw = {
            "guard_foresight": guard_live,
            "guard_other_offices": guard_other,
            "guard_foresight_without_held_row": guard_noheld,
            "resolve_held_row": resolve_run,
        }
        for name, payload in raw.items():
            (E / ("cmd-" + name + ".json")).write_text(json.dumps(payload, indent=2, sort_keys=True))

    result = {
        "capture_utc": capture,
        "captured_unix": now,
        "prior_capture_utc": "2026-11-25T09:35:55Z",
        "minutes_since_prior": round((now - PRIOR["capture_unix"]) / 60, 2),
        "all_assertions_pass": all(A.values()),
        "assertions": A,
        "hashes": H,
        "reservation_count": len(rows),
        "state_counts": counts,
        "liability_basis_tokens": basis,
        "tokens_total": total_tokens,
        "ceiling_pinned_tokens": basis["held_charge"] + basis["active_caps"] + basis["reserved_caps"],
        "ceiling_pinned_share": (basis["held_charge"] + basis["active_caps"] + basis["reserved_caps"]) / total_tokens,
        "held_id": HELD_ID,
        "held_duration_seconds_at_capture": held_seconds,
        "held_tokens": int(held["charge"]["tokens_total"]),
        "held_share_of_aggregate": int(held["charge"]["tokens_total"]) / total_tokens,
        "open_reservations_by_office": active_open,
        "admit_by_office": admit,
        "commands": raw,
        "resolve_row_after": {k: after.get(k) for k in (
            "state", "held_reason", "charge", "closed_at", "closed_reason", "resolved_by")},
    }
    # Digest over all evidence artifacts except this script, its output and prose.
    skip = {"measure.py", "measurement.json", "PROVENANCE.md", "CAPTURE_TIME.txt"}
    digests = {str(p.relative_to(E)): sha(p) for p in sorted(E.rglob("*"))
               if p.is_file() and p.name not in skip and "__pycache__" not in p.parts}
    result["derived_measurement_sha256"] = hashlib.sha256(
        json.dumps(digests, sort_keys=True).encode()).hexdigest()
    (E / "measurement.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_assertions_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())

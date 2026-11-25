#!/usr/bin/env python3
"""Hermetic, byte-frozen REVISIT of the foresight unbound-hold lockout.

Capture 2026-11-25T11:43:00Z, ~65.9 min after the 10:37:08Z snapshot. The
trigger is the Bureau's own revisit_when on act34-foresight-lockout-20261125
("a reconciliation record ... lands on main") plus a recovery-steward Post.
The Post is a hypothesis/trigger ONLY: no factual claim here rests on it.

This run re-derives every fact from byte-frozen primary sources. It never reads
or writes the live budget ledger from the shell probes, never calls a live
Antonina agent (an `antonina` stub is first on PATH) and uses a scratch SQLite
meter. The DEPLOYED knowledge-budget.sh guard/resolve functions are re-executed
from frozen bytes. A sole-cause falsifier removes ONLY the held row; if guard
foresight does not flip to `guard ok`, "held row is the sole blocker" is false.

Compared with the 10:37Z snapshot this run adds a landing-correction check:
the two claimed artifacts ARE now on canonical main, but they are an
investigation record and an explicitly NOT-ENACTED bill draft. The assertion
set tests that documentation landing did NOT change the operational substrate.
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
HELD_ID = "r1795595445-NZIjZE34"
HELD_REASON = "meter_or_session_binding_unknown_after_launch"
CEILING = 11320103

# Frozen point-in-time constants from the PRIOR snapshot (10:37:08Z), used as
# content assertions, never silently updated.
PRIOR = {
    "capture_utc": "2026-11-25T10:37:08Z",
    "capture_unix": 1795603028,
    "reservation_count": 21,
    "tokens_total": 77845120,
    "held_duration_seconds": 7553,
    "activation.json": "921b99ae1288769b4460ea25641cad93da8d1ed3c98ce1adfbecbd32b261587b",
    "knowledge-budget.conf": "b80f48aff6b94382d4a5b859bab41906fa665c3b8cf4f6eb5bd0a84152ea8aab",
    "knowledge-budget-tool.py": "4ecae5ea0c1bd3edaa4cb2262cd9b8208a1ee66830ff92ff6edf6ee2a40ce9f3",
    "knowledge-budget.sh": "4105567c3b902a23b917f2545effd51f5e6c167602aa6a9f0a2201cf76759c56",
}
CLAIMED_COMMITS = ("56dd2756a001", "30b8fe5fbf3f", "f3d9b6fae906", "249ff921f4a0")
CLAIMED_PATHS = (
    "records/investigations/recovery-steward-foresight-unbound-hold-20261125T0954Z.md",
    "records/bills/held-reservation-resolution-act.md",
)


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


def decompose(rows):
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
    for k in ("activation.json", "knowledge-budget.conf", "knowledge-budget-tool.py",
              "knowledge-budget.sh"):
        A["bytes_unchanged_vs_1037_" + k] = H[k] == PRIOR[k]
    A["frozen_config_valid"] = not errors and not tool.validate_config(cfg)
    A["aggregate_reproduced_exactly"] = (totals == frozen_agg)
    A["prior_count_was_21"] = PRIOR["reservation_count"] == 21
    A["reservation_count_grew"] = len(rows) > PRIOR["reservation_count"]

    A["held_row_still_present"] = HELD_ID in rows
    held = rows[HELD_ID]
    A["held_state_still_held"] = held["state"] == "held"
    A["held_reason_unchanged"] = held["held_reason"] == HELD_REASON
    A["held_native_session_null"] = held.get("native_session_id") is None
    A["held_meter_and_usage_null"] = held.get("meter") is None and held.get("usage") is None
    A["held_charge_at_frozen_ceiling"] = int(held["charge"]["tokens_total"]) == CEILING
    A["held_no_closure_fields"] = all(
        held.get(k) is None for k in ("closed_at", "closed_reason", "resolved_by"))
    held_seconds = now - int(held["held_at"])
    A["held_longer_than_prior_7553s"] = held_seconds > PRIOR["held_duration_seconds"]

    basis, counts = decompose(rows)
    total_tokens = totals["tokens_total"]
    active_open = {o: [r["id"] for r in rows.values()
                       if r["office"] == o and r["state"] in ("reserved", "active", "held")]
                   for o in OFFICES}
    admit = {o: tool.admit(cfg, totals, o) for o in OFFICES}
    A["admit_all_four_true"] = all(v["admit"] is True for v in admit.values())
    old_cfg, _ = tool.load_config(str(E / "superseded-knowledge-budget.conf"))
    A["superseded_config_refuses_all"] = all(
        tool.admit(old_cfg, totals, o)["admit"] is False for o in OFFICES)
    over = dict(totals)
    over["by_office"] = dict(totals["by_office"])
    over["by_office"]["statistics"] = {"tokens_total": cfg["aggregate"]["caps"]["tokens_total"]}
    A["over_cap_refuses_statistics"] = tool.admit(cfg, over, "statistics")["admit"] is False

    # ---- hermetic re-execution of the DEPLOYED shell functions --------------
    with tempfile.TemporaryDirectory(prefix="stat-lockout-revisit-", dir="/tmp/opencode") as td:
        base = pathlib.Path(td)
        _, _, _, env = make_scratch(base, rows, E / "foresight-held-agent-status.json", tool)
        guard_live = run_sh(env, "guard", "foresight")
        A["guard_foresight_refused"] = guard_live["rc"] != 0
        A["guard_foresight_blames_held_row"] = HELD_ID in guard_live["stderr"]
        guard_other = {o: run_sh(env, "guard", o) for o in ("statistics", "strategy", "spying")}
        # At 10:37Z the other three offices had no open rows; by this capture
        # they each have a fresh ACTIVE dispatch. Their guard refusal must cite
        # that office's own active row, never the held foresight row.
        A["other_offices_refuse_on_own_active_rows"] = all(
            v["rc"] != 0 and any(r in v["stderr"] for r in active_open[o])
            and HELD_ID not in v["stderr"]
            for o, v in guard_other.items())
        A["foresight_alone_blocked_by_held_row"] = (
            held["state"] == "held" and all(
                rows[r]["state"] != "held"
                for o in ("statistics", "strategy", "spying")
                for r in active_open[o] if r in rows))

        b2 = base / "control_noheld"
        rows2 = {k: dict(v) for k, v in rows.items() if k != HELD_ID}
        _, _, _, env2 = make_scratch(b2, rows2, E / "foresight-held-agent-status.json", tool)
        guard_noheld = run_sh(env2, "guard", "foresight")
        A["guard_flips_ok_when_held_removed"] = (
            guard_noheld["rc"] == 0 and "guard ok: foresight" in guard_noheld["stdout"])

        b3 = base / "resolve_probe"
        _, res3, _, env3 = make_scratch(b3, rows, E / "foresight-held-agent-status.json", tool)
        resolve_run = run_sh(env3, "resolve", HELD_ID, "statistics-hermetic-revisit")
        after = json.loads((res3 / (HELD_ID + ".json")).read_text())
        A["resolve_rc_zero"] = resolve_run["rc"] == 0
        A["resolve_left_row_held"] = after["state"] == "held"
        A["resolve_did_not_close"] = all(
            after.get(k) is None for k in ("closed_at", "closed_reason", "resolved_by"))
        A["resolve_reason_was_identity_unresolved"] = (
            after.get("held_reason") == "operator_resolution_identity_unresolved")
        A["resolve_kept_full_ceiling"] = int(after["charge"]["tokens_total"]) == CEILING
        calls = b3 / "antonina-calls.log"
        A["no_live_antonina_call_in_scratch"] = (not calls.exists()) or calls.read_text() == ""
        raw = {
            "guard_foresight": guard_live,
            "guard_other_offices": guard_other,
            "guard_foresight_without_held_row": guard_noheld,
            "resolve_held_row": resolve_run,
        }
        for name, payload in raw.items():
            (E / ("cmd-" + name + ".json")).write_text(json.dumps(payload, indent=2, sort_keys=True))

    # ---- landing-correction assertions (primary canonical-main checks) ------
    landing = (E / "remediation-landing-check.txt").read_text()
    landed = (E / "landed-artifacts.txt").read_text()
    A["claimed_records_present_on_main"] = all(
        "PRESENT " + p in landing for p in CLAIMED_PATHS)
    A["claimed_commits_all_ancestors_of_main"] = all(
        any(line.startswith(c + " ") and line.rstrip().endswith(" ANCESTOR")
            for line in landing.splitlines())
        for c in CLAIMED_COMMITS)
    A["bill_draft_explicitly_not_enacted"] = "NOT ENACTED" in landed
    A["no_law_entry_for_draft"] = "LAWS_MENTION: NO" in landing
    A["no_ballot_or_tally_for_draft"] = all(
        "ABSENT " + p in landing for p in (
            "records/ballots/held-reservation-resolution-act.tsv",
            "records/tally/held-reservation-resolution-act"))
    holds_listing = (E / "liveness-unsafe-holds-listing.txt").read_text()
    A["unsafe_holds_still_empty"] = not any(
        line.startswith("-") and not line.startswith("---")
        and not (line.endswith(" .") or line.endswith(" .."))
        for line in holds_listing.splitlines())
    A["landing_did_not_change_substrate"] = all([
        A["bytes_unchanged_vs_1037_activation.json"],
        A["bytes_unchanged_vs_1037_knowledge-budget.conf"],
        A["bytes_unchanged_vs_1037_knowledge-budget-tool.py"],
        A["bytes_unchanged_vs_1037_knowledge-budget.sh"],
        A["held_state_still_held"], A["held_no_closure_fields"],
        A["guard_foresight_refused"],
    ])

    result = {
        "capture_utc": capture,
        "captured_unix": now,
        "prior_capture_utc": PRIOR["capture_utc"],
        "minutes_since_prior": round((now - PRIOR["capture_unix"]) / 60, 2),
        "all_assertions_pass": all(A.values()),
        "assertions": A,
        "hashes": H,
        "reservation_count": len(rows),
        "prior_reservation_count": PRIOR["reservation_count"],
        "state_counts": counts,
        "liability_basis_tokens": basis,
        "tokens_total": total_tokens,
        "prior_tokens_total": PRIOR["tokens_total"],
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
        "correction_of_prior_finding_d": {
            "prior_statement": "claimed reconciliation record absent from canonical main (point-in-time, 10:37:47Z)",
            "status_now": "superseded at 11:43:00Z: both artifacts present on canonical main",
            "honest_scope": "the earlier observation was correct at its capture; this is a later-time update, not a rewrite. The landed material is an investigation record and an explicitly NOT-ENACTED draft, not a closure or repair of held row r1795595445-NZIjZE34.",
            "version": "v2 (revisit); v1 = act34-foresight-lockout-20261125, retained unchanged",
        },
    }
    skip = {"measure.py", "measurement.json", "PROVENANCE.md", "CAPTURE_TIME.txt"}
    digests = {str(p.relative_to(E)): sha(p) for p in sorted(E.rglob("*"))
               if p.is_file() and p.name not in skip and "__pycache__" not in p.parts}
    result["derived_measurement_sha256"] = hashlib.sha256(
        json.dumps(digests, sort_keys=True).encode()).hexdigest()
    (E / "measurement.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "capture_utc": capture,
        "all_assertions_pass": result["all_assertions_pass"],
        "failed": [k for k, v in A.items() if not v],
        "reservation_count": len(rows),
        "tokens_total": total_tokens,
        "held_seconds": held_seconds,
        "state_counts": counts,
        "derived": result["derived_measurement_sha256"],
    }, indent=2, sort_keys=True))
    return 0 if result["all_assertions_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())

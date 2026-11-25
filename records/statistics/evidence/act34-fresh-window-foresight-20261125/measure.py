#!/usr/bin/env python3
"""Hermetic, byte-frozen measurement of the recurring-renewal after-start window.

Reads ONLY primary copies frozen in this directory. It never reads or writes the
live budget ledger, never calls a live Antonina agent command (a PATH-first
`antonina` stub is used for the shell re-execution), and inspects the DEPLOYED
gate and budget source bytes rather than paraphrasing them.

Question (statistics inquiry act34-fresh-window-foresight-20261125): after the
2026-11-25 recurring renewal opened a fresh 48h after-start Judiciary window and
archived the first-wave reviews (including a Spying HOLD), are the review gate
and the budget guard INDEPENDENT blockers such that a timely `proceed` review
clears only the gate, while the unbound foresight held row still blocks dispatch;
and can the renewal's board-approval link be independently re-executed from this
office? The board claim is treated as UNVERIFIED, never as established here.
"""
import collections
import datetime
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import sqlite3
import subprocess
import sys
import tempfile

E = pathlib.Path(__file__).resolve().parent
sys.dont_write_bytecode = True
OFFICES = ("statistics", "foresight", "strategy", "spying")
HELD_ID = "r1795595445-NZIjZE34"
REVIEW = 48 * 3600
NEW_START = 1795560059          # recurring-renewal permit not_before
PRIOR_START = 1795544516        # first-wave permit start
FIRST_WAVE_SPYING_PERMIT = "3f5b92b9ff676dcbed44b6e4bb1df565776f13aa360ccd0ca6a823d82cd222ec"
CONFIG = "b80f48aff6b94382d4a5b859bab41906fa665c3b8cf4f6eb5bd0a84152ea8aab"
PRIOR = {
    "activation.json": "921b99ae1288769b4460ea25641cad93da8d1ed3c98ce1adfbecbd32b261587b",
    "knowledge-budget.conf": CONFIG,
    "knowledge-budget-tool.py": "4ecae5ea0c1bd3edaa4cb2262cd9b8208a1ee66830ff92ff6edf6ee2a40ce9f3",
    "permit_sha256": {
        "foresight": "57b9daa1495d4e6d40800f29dae05e6b72df91cd3190c3a8f7a5e00088acd7a9",
        "spying": "be8fbad593d54727e83b8112187ac41e86a97a2754814b7e00d73c3bc4cbfbd0",
        "statistics": "cb735305b408969b1e372a48ff2928dc736b594bf87dca5f3e65138587f70159",
        "strategy": "6121f77251694e24abf3f7da976fe5dc6fcd972fe157157552e64d1664a7f77c",
    },
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc_unix(stamp):
    dt = datetime.datetime.strptime(stamp.strip(), "%Y-%m-%dT%H:%M:%SZ")
    return int(dt.replace(tzinfo=datetime.timezone.utc).timestamp())


def load_tool():
    spec = importlib.util.spec_from_file_location("kbtool_frozen", E / "knowledge-budget-tool.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def make_scratch(base, rows, status_path, tool, now):
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
    totals, counted, skipped = tool.charges(str(res), now, 3888000)
    totals["counted"] = counted
    totals["skipped"] = skipped
    (budget / "aggregate.json").write_text(json.dumps(totals, sort_keys=True))
    return budget, res, db, env


def run_sh(env, *args):
    p = subprocess.run(["/bin/sh", str(E / "knowledge-budget.sh"), *args],
                       env=env, cwd="/tmp", capture_output=True, text=True, timeout=60)
    return {"argv": ["knowledge-budget.sh", *args], "rc": p.returncode,
            "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}


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

    A = {}  # assertions
    act = json.loads((E / "activation.json").read_text())
    A["activation_status_active"] = act.get("status") == "ACTIVE"
    A["all_four_enabled"] = all(act["offices"][o]["enabled"] is True for o in OFFICES)
    A["all_authorized_by_act34"] = all(
        act["offices"][o]["authorized_by"] == "act:34:" + o for o in OFFICES)
    A["all_not_before_new_start"] = all(
        act["offices"][o]["not_before"] == NEW_START for o in OFFICES)
    A["all_expiry_preserved"] = all(
        act["offices"][o]["expires_at"] == 1799432516 for o in OFFICES)
    deadline = NEW_START + REVIEW
    A["now_inside_fresh_window"] = NEW_START <= now < deadline
    A["fresh_window_deadline_20261126_224059Z"] = (
        datetime.datetime.fromtimestamp(deadline, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        == "2026-11-26T22:40:59Z")
    A["window_later_than_first_wave"] = NEW_START > PRIOR_START

    # Permits hash-bind to the same activation rows (re-confirmed on frozen bytes).
    permit_hash_ok = {}
    for o in OFFICES:
        permit_hash_ok[o] = sha(E / "permits" / (o + ".json")) == act["offices"][o]["permit_sha256"]
    A["permits_match_activation_and_prior"] = all(permit_hash_ok.values()) and all(
        act["offices"][o]["permit_sha256"] == PRIOR["permit_sha256"][o] for o in OFFICES)

    # First-wave Spying HOLD archived byte-identically, not silently rewritten.
    rev = json.loads((E / "archived-reviews" / "spying" / "review.json").read_text())
    prov = json.loads((E / "archived-reviews" / "spying" / "provenance.json").read_text())
    A["archived_review_is_spying_hold"] = rev.get("decision") == "hold"
    A["archived_review_permit_start_first_wave"] = rev.get("permit_start") == PRIOR_START
    A["archived_review_deadline_first_wave"] = rev.get("statutory_deadline") == PRIOR_START + REVIEW
    A["archived_review_in_window"] = PRIOR_START <= rev.get("reviewed_at", 0) < PRIOR_START + REVIEW
    A["archived_review_permit_sha256"] = rev.get("permit_sha256") == FIRST_WAVE_SPYING_PERMIT
    A["archived_review_bytes_match_provenance"] = (
        sha(E / "archived-reviews" / "spying" / "review.json")
        == prov["preserved_artifacts"]["review.json"]["sha256"])
    A["archived_review_original_path_was_pilot_reviews"] = (
        prov["preserved_artifacts"]["review.json"]["original_path"]
        == "records/knowledge/pilot-reviews/spying.json")
    A["no_current_review_file"] = not (E / "pilot-reviews").exists()  # frozen dir never copied

    # Gate/guard independence: the frozen DEPLOYED gate consults pilot-reviews,
    # never the budget ledger or held reservations. A `proceed` review can clear
    # only the gate; nothing in the gate can see the held row.
    gate_src = (E / "knowledge-act34-gate.py").read_text()
    A["gate_has_review_window_constant"] = "REVIEW = 48 * 3600" in gate_src
    A["gate_reads_pilot_reviews"] = "records/knowledge/pilot-reviews/" in gate_src
    A["gate_proceed_required"] = 'rev.get("decision") != "proceed"' in gate_src
    A["gate_fail_closed_after_deadline"] = "elif now >= values[0] + REVIEW:" in gate_src
    ledger_refs = [t for t in ("reservations/", "aggregate.json", "viche-state", "knowledge/budget")
                   if t in gate_src]
    A["gate_has_no_budget_ledger_reference"] = (len(ledger_refs) == 0)
    audit = {"ledger_refs_found": ledger_refs}

    # Live gate re-execution: fails at the board-attestation step for all four,
    # i.e. AFTER the deterministic permit/config binding checks, because the
    # shared board credential is absent in this office's environment. This is an
    # environment-dependent limitation, NOT a finding that the renewal is invalid.
    gl = json.loads((E / "gate-live.json").read_text())
    A["live_gate_all_four_fail_closed"] = all(v["rc"] != 0 for v in gl.values())
    A["live_gate_failure_is_board_query_not_permit_hash"] = all(
        "antonina query failed: board show" in v["stderr"] for v in gl.values())
    A["live_gate_reaches_attestation_step"] = all(
        "unverified executive action" in v["stderr"] for v in gl.values())

    # Dispatch census from frozen reservations under the new config.
    census = collections.defaultdict(collections.Counter)
    for r in rows.values():
        if r.get("config_sha256") == CONFIG:
            census[r["office"]][r["state"]] += 1
    census = {o: dict(census[o]) for o in OFFICES}
    A["foresight_has_two_completed_new_config_dispatches"] = census["foresight"].get("closed", 0) == 2
    A["held_row_present"] = HELD_ID in rows
    held = rows[HELD_ID]
    A["held_state_held"] = held["state"] == "held"
    A["held_config_new"] = held.get("config_sha256") == CONFIG
    A["held_native_session_null"] = held.get("native_session_id") is None
    A["held_meter_usage_null"] = held.get("meter") is None and held.get("usage") is None
    A["held_charge_at_ceiling"] = int(held["charge"]["tokens_total"]) == 11320103
    A["held_no_closure_fields"] = all(
        held.get(k) is None for k in ("closed_at", "closed_reason", "resolved_by"))

    # Aggregate reproduced exactly from all 37 frozen rows.
    A["aggregate_reproduced_exactly"] = (totals == frozen_agg)
    A["reservation_count_37"] = len(rows) == 37

    # Hermetic re-execution of DEPLOYED guard; sole-cause falsifier removes ONLY
    # the held row and must flip foresight to ok.
    commands = {}
    with tempfile.TemporaryDirectory(prefix="stat-freshwin-", dir="/tmp/opencode") as td:
        base = pathlib.Path(td)
        _, _, _, env = make_scratch(base, rows, E / "foresight-held-agent-status.json", tool, now)
        guard = run_sh(env, "guard", "foresight")
        A["guard_foresight_refused"] = guard["rc"] != 0
        A["guard_blames_held_row"] = HELD_ID in guard["stderr"]
        others = {o: run_sh(env, "guard", o) for o in ("statistics", "strategy", "spying")}
        b2 = base / "control_noheld"
        rows2 = {k: dict(v) for k, v in rows.items() if k != HELD_ID}
        _, _, _, env2 = make_scratch(b2, rows2, E / "foresight-held-agent-status.json", tool, now)
        noheld = run_sh(env2, "guard", "foresight")
        A["guard_flips_ok_when_only_held_removed"] = (
            noheld["rc"] == 0 and "guard ok: foresight" in noheld["stdout"])
        calls = base / "antonina-calls.log"
        A["no_live_antonina_call_in_scratch"] = (not calls.exists()) or calls.read_text() == ""
        commands = {"guard_foresight": guard, "guard_other_offices": others,
                    "guard_foresight_without_held_row": noheld}
        for name, payload in commands.items():
            (E / ("cmd-" + name + ".json")).write_text(json.dumps(payload, indent=2, sort_keys=True))

    result = {
        "capture_utc": capture,
        "captured_unix": now,
        "permit_start_unix": NEW_START,
        "fresh_window_deadline_unix": deadline,
        "fresh_window_remaining_seconds_at_capture": deadline - now,
        "first_wave_permit_start_unix": PRIOR_START,
        "all_assertions_pass": all(A.values()),
        "assertions": A,
        "audit": audit,
        "permit_hash_ok": permit_hash_ok,
        "archived_spying_hold": {k: rev.get(k) for k in
            ("office", "reviewer", "decision", "permit_start", "statutory_deadline", "reviewed_at",
             "permit_sha256", "handoff")},
        "dispatch_census_new_config": census,
        "reservation_count": len(rows),
        "aggregate_tokens_total": totals["tokens_total"],
        "held_id": HELD_ID,
        "held_created_utc": datetime.datetime.fromtimestamp(int(held["created_at"]),
            datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "commands": commands,
        "hashes": {k: sha(E / k) for k in (
            "activation.json", "knowledge-budget.conf", "knowledge-budget-tool.py",
            "knowledge-budget.sh", "knowledge-act34-gate.py", "gate-live.json")},
        "falsifiers": [
            "Any office enabled=false, authorized_by != act:34:OFFICE, not_before != 1795560059 or expiry != 1799432516 in the frozen activation.json.",
            "A replacement permit whose sha256 differs from its activation.json permit_sha256.",
            "An archived Spying review whose bytes do not reproduce its provenance sha256, whose decision is not hold, or whose permit_start/deadline are not the first-wave values.",
            "A gate source that reads any budget-ledger path, or that accepts a non-proceed review before the deadline.",
            "A live gate failure caused by a permit/config hash mismatch rather than the missing board credential.",
            "guard foresight returning ok with the held row present, or failing to flip to ok when only that row is removed.",
            "An aggregate that the frozen charges() cannot reproduce from the frozen reservations.",
        ],
    }
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

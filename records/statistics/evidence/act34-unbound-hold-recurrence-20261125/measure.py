#!/usr/bin/env python3
"""Byte-frozen measurement: recurrence of the unbound-hold failure mode.

Reads ONLY primary copies frozen in this directory. It never reads or writes
the live budget ledger, never calls a live agent command, and inspects the
DEPLOYED source bytes rather than paraphrasing them.

Question (statistics inquiry act34-unbound-hold-recurrence-20261125): after the
2026-11-25 16:23Z fresh-window measurement, did the
"meter_or_session_binding_unknown_after_launch" unbound-hold failure mode recur
on a SECOND office -- a fresh statistics dispatch of my own appointment agent --
within ~69 minutes, under byte-unchanged substrate and an unenacted repair bill;
and is the recurrence distinguishable from the clean strategy/spying dispatches
in the same window? The held charge is treated as ceiling LIABILITY, not measured
usage; no legal, safety, renewal or efficacy verdict is made.
"""
import datetime
import hashlib
import importlib.util
import json
import pathlib
import sys

E = pathlib.Path(__file__).resolve().parent
sys.dont_write_bytecode = True

CONFIG = "b80f48aff6b94382d4a5b859bab41906fa665c3b8cf4f6eb5bd0a84152ea8aab"
KNOWN_HASHES = {
    "knowledge-budget.conf": CONFIG,
    "knowledge-budget-tool.py": "4ecae5ea0c1bd3edaa4cb2262cd9b8208a1ee66830ff92ff6edf6ee2a40ce9f3",
    "knowledge-budget.sh": "4105567c3b902a23b917f2545effd51f5e6c167602aa6a9f0a2201cf76759c56",
    "knowledge-act34-gate.py": "13e6d68aaa1b32ce08e1a8ecd9f209486115aec077be7ef0f42f489306640d9a",
}
FORESIGHT_HELD = "r1795595445-NZIjZE34"
STATS_HELD = "r1795627844-h4STKKF6"
CONTROLS = ("r1795625565-pZ0ZpW9z", "r1795626321-B8gb7hXo")
MY_AGENT = "vMWHKp5ui3p137QYhQzKFF-citrus"
HOLD_REASON = "meter_or_session_binding_unknown_after_launch"
CEILING = 11320103


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


def main():
    now = utc_unix((E / "CAPTURE_TIME.txt").read_text())
    tool = load_tool()
    rows = {p.stem: json.loads(p.read_text())
            for p in sorted((E / "reservations").glob("*.json"))}
    frozen_agg = json.loads((E / "aggregate.json").read_text())
    status = json.loads((E / "agent-status-statistics.json").read_text())
    mstat = json.loads((E / "meter-statistics-session.json").read_text())
    mfore = json.loads((E / "meter-foresight-session.json").read_text())

    A = {}

    # --- substrate bytes unchanged since the 16:23Z fresh-window capture ---
    for name, digest in KNOWN_HASHES.items():
        A["unchanged_" + name.replace(".", "_")] = sha(E / name) == digest

    # --- both held rows: same defect, same config, ceiling liability, no closure ---
    held = {}
    for hid in (FORESIGHT_HELD, STATS_HELD):
        h = rows[hid]
        held[hid] = h
        stem = "held_" + ("foresight" if hid == FORESIGHT_HELD else "statistics")
        A[stem + "_state"] = h["state"] == "held"
        A[stem + "_reason"] = h.get("held_reason") == HOLD_REASON
        A[stem + "_sid_null"] = h.get("native_session_id") is None
        A[stem + "_meter_null"] = h.get("meter") is None and h.get("usage") is None
        A[stem + "_ceiling"] = int(h["charge"]["tokens_total"]) == CEILING
        A[stem + "_no_closure"] = all(
            h.get(k) is None for k in ("closed_at", "closed_reason", "resolved_by"))
        A[stem + "_dispatch_attempted"] = h.get("dispatch_attempted") is True
        A[stem + "_config_new"] = h.get("config_sha256") == CONFIG
    A["both_held_same_config"] = (
        held[FORESIGHT_HELD]["config_sha256"] == held[STATS_HELD]["config_sha256"] == CONFIG)
    A["statistics_held_agent_is_my_appointment"] = held[STATS_HELD].get("agent_id") == MY_AGENT
    A["statistics_held_after_foresight_held"] = (
        held[STATS_HELD]["held_at"] > held[FORESIGHT_HELD]["held_at"])
    A["statistics_held_within_70min_of_prior_capture"] = (
        0 < held[STATS_HELD]["held_at"] - utc_unix("2026-11-25T16:23:16Z") < 70 * 60)

    # --- agent status: killed by signal, no native session id at hold time ---
    A["my_agent_status_killed"] = status["state"] == "killed" and status["alive"] is False
    A["my_agent_killed_by_signal9"] = status.get("exit_signal") == 9
    A["my_agent_status_sid_null"] = status.get("native_session_id") is None
    A["agent_killed_before_hold"] = (
        int(status["finished_at"]) < held[STATS_HELD]["held_at"])
    A["agent_started_at_dispatch_attempt"] = (
        abs(int(status["started_at"]) - held[STATS_HELD]["history"][1]["at"]) <= 1)

    # --- authoritative meter rows: both held reservations HAD a session row ---
    A["statistics_meter_row_exists"] = mstat["id"] == "ses_dec3d7632ffe4MBEkReDeWfdxv"
    A["statistics_meter_in_statistics_worktree"] = (
        mstat["directory"] == "/var/lib/lubko/wd/viche-seats/branches/statistics")
    A["statistics_meter_created_near_reservation"] = (
        held[STATS_HELD]["created_at"] * 1000 <= mstat["time_created"]
        <= held[STATS_HELD]["held_at"] * 1000)
    A["statistics_meter_consumed_tokens"] = (
        mstat["tokens_cache_read"] + mstat["tokens_input"]
        + mstat["tokens_output"] + mstat["tokens_reasoning"] > 0)
    A["foresight_meter_row_exists"] = mfore["id"] == "ses_dee2bc2a9ffevFtsM61Ljl2TvW"
    A["foresight_meter_in_foresight_worktree"] = (
        mfore["directory"] == "/var/lib/lubko/wd/viche-seats/branches/foresight")
    A["foresight_meter_zero_tokens"] = (
        mfore["tokens_cache_read"] + mfore["tokens_input"]
        + mfore["tokens_output"] + mfore["tokens_reasoning"] == 0)
    A["foresight_meter_created_before_hold"] = (
        mfore["time_created"] < held[FORESIGHT_HELD]["held_at"] * 1000)
    # Distinct usage, same outcome: the reason is binding, not consumption level.
    A["hold_reason_not_usage_dependent"] = (
        A["statistics_meter_consumed_tokens"] and A["foresight_meter_zero_tokens"])

    # --- negative controls: clean dispatches in the same window ---
    clean = {cid: rows[cid] for cid in CONTROLS}
    for cid, c in clean.items():
        stem = "control_" + c["office"]
        A[stem + "_closed"] = c["state"] == "closed"
        A[stem + "_sid_present"] = bool(c.get("native_session_id"))
        A[stem + "_config_new"] = c.get("config_sha256") == CONFIG
        A[stem + "_between_the_two_holds"] = (
            held[FORESIGHT_HELD]["held_at"] < c["created_at"] < held[STATS_HELD]["held_at"])
    # No new foresight reservation since its hold: lockout held in practice.
    A["no_new_foresight_reservation_since_hold"] = not any(
        r["office"] == "foresight" and r["created_at"] > held[FORESIGHT_HELD]["held_at"]
        for r in rows.values())

    # --- aggregate reproduces from all 40 frozen rows ---
    totals, counted, skipped = tool.charges(str(E / "reservations"), now, 3888000)
    totals["counted"] = counted
    totals["skipped"] = skipped
    A["aggregate_reproduced_exactly"] = totals == frozen_agg
    A["reservation_count_40"] = len(rows) == 40
    A["both_held_counted_at_ceiling"] = (
        FORESIGHT_HELD in counted and STATS_HELD in counted
        and frozen_agg["by_office"]["foresight"]["tokens_total"] >= CEILING
        and frozen_agg["by_office"]["statistics"]["tokens_total"] >= CEILING)

    result = {
        "capture_utc": (E / "CAPTURE_TIME.txt").read_text().strip(),
        "captured_unix": now,
        "all_assertions_pass": all(A.values()),
        "assertion_count": len(A),
        "assertions": A,
        "held_rows": {
            "foresight": {k: held[FORESIGHT_HELD].get(k) for k in
                          ("id", "office", "state", "held_at", "held_reason",
                           "native_session_id", "charge")},
            "statistics": {k: held[STATS_HELD].get(k) for k in
                           ("id", "office", "state", "held_at", "held_reason",
                            "native_session_id", "charge", "agent_id")},
        },
        "my_agent_status": {k: status.get(k) for k in
                            ("id", "state", "alive", "native_session_id", "exit_signal",
                             "started_at", "finished_at")},
        "meters": {
            "statistics": {k: mstat.get(k) for k in
                           ("id", "directory", "time_created", "time_updated")},
            "foresight": {k: mfore.get(k) for k in
                          ("id", "directory", "time_created", "time_updated")},
        },
        "controls": {c["office"]: {k: c.get(k) for k in
                    ("id", "state", "native_session_id", "created_at")}
                    for c in clean.values()},
        "reservation_count": len(rows),
        "aggregate_tokens_total": frozen_agg["tokens_total"],
        "hashes": {k: sha(E / k) for k in KNOWN_HASHES},
        "falsifiers": [
            "A held row whose state != held, reason != meter_or_session_binding_unknown_after_launch, native_session_id non-null, or charge != 11320103.",
            "My agent status not killed, signal != 9, or native_session_id non-null.",
            "No valid session_v2 meter row for the statistics worktree created between reservation creation and hold, or zero tokens consumed.",
            "A new foresight reservation created after its hold (lockout did not hold).",
            "Either clean control not closed with a native_session_id (recurrence not distinguishable).",
            "Any deployed source hash differing from the 16:23Z fresh-window capture.",
            "An aggregate the frozen charges() cannot reproduce from all 40 rows.",
        ],
    }
    skip = {"measure.py", "measurement.json", "PROVENANCE.md"}
    digests = {str(p.relative_to(E)): sha(p) for p in sorted(E.rglob("*"))
               if p.is_file() and p.name not in skip and "__pycache__" not in p.parts}
    result["derived_measurement_sha256"] = hashlib.sha256(
        json.dumps(digests, sort_keys=True).encode()).hexdigest()
    (E / "measurement.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_assertions_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())

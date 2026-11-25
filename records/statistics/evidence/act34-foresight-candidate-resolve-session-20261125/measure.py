#!/usr/bin/env python3
"""Independent hermetic probe of the DRAFT resolve-session candidate.

Re-executes the candidate's exact frozen knowledge-budget.sh against a faithful
copy of the REAL held row r1795595445-NZIjZE34 and the REAL frozen Antonina
status / meter facts, on private scratch state. No production ledger byte, live
agent, credential or external side effect is touched. This measures deployed
*candidate decision logic*, NOT a repair, not production invocation, not a
legal verdict. Nominal case and two negative controls are preregistered below.
"""
import json, os, pathlib, shutil, sqlite3, subprocess, sys, tempfile, time

EVID = pathlib.Path(__file__).resolve().parent
ENGINE = EVID / "knowledge-budget.sh"
TOOL = EVID / "knowledge-budget-tool.py"
CONF = json.loads((EVID / "knowledge-budget.conf").read_text())
REAL_ROW = json.loads((EVID / "real-held-row.json").read_text())
STATUS = json.loads((EVID / "frozen-status.json").read_text())
SID = STATUS["native_session_id"]
AGENT = STATUS["id"]
RID = REAL_ROW["id"]
CAP = REAL_ROW["caps"]["tokens_total"]

STUB = r'''#!/bin/sh
# PATH-first antonina stub. Records kill/stop attempts; never dispatches.
mode=${CAND_TEST_MODE:-real}
case "$1 $2" in
  'agent status')
    case "$mode" in
      unreadable) exit 9 ;;
      wrong_sid) printf '{"id":"%s","state":"killed","native_session_id":"ses_WRONG","runner_pid":7796}\n' "$AGENT_ENV" ;;
      nonterminal) printf '{"id":"%s","state":"running","native_session_id":"%s","runner_pid":7796}\n' "$AGENT_ENV" "$SID_ENV" ;;
      *) printf '%s\n' "$STATUS_JSON" ;;
    esac ;;
  'agent kill'|'agent stop') printf '%s\n' "$*" >> "$KILL_LOG" ;;
  *) exit 17 ;;
esac
'''


def make_db(path):
    """session_v2 row with the REAL observed meter values for the killed sid."""
    c = sqlite3.connect(path)
    c.execute("create table session_v2 (id text primary key,tokens_input int,"
              "tokens_output int,tokens_reasoning int,tokens_cache_read int,"
              "tokens_cache_write int,cost real,time_updated int)")
    # Real observed meter: all token counters 0, cost 0.0, time_updated 1795595474716.
    c.execute("insert into session_v2 values (?,0,0,0,0,0,0.0,1795595474716)", (SID,))
    c.commit(); c.close()


def setup(root, mode):
    state = pathlib.Path(root) / "state"
    town = pathlib.Path(root) / "town"
    bindir = pathlib.Path(root) / "bin"
    (state / "knowledge" / "budget" / "reservations").mkdir(parents=True)
    (town / "government").mkdir(parents=True)
    bindir.mkdir(parents=True)

    db = str(pathlib.Path(root) / "meter.db")
    make_db(db)
    conf = json.loads(json.dumps(CONF))
    conf["metering"]["opencode_db"] = db
    (town / "government" / "knowledge-budget.conf").write_text(json.dumps(conf))

    row = json.loads(json.dumps(REAL_ROW))
    row["meter_db"] = db  # scratch meter, faithful real values
    (state / "knowledge" / "budget" / "reservations" / (RID + ".json")).write_text(json.dumps(row))

    stub = bindir / "antonina"
    stub.write_text(STUB)
    stub.chmod(0o755)

    kill_log = pathlib.Path(root) / "kills.log"
    kill_log.write_text("")
    env = os.environ.copy()
    env.update({
        "VICHE_STATE_ROOT": str(state),
        "VICHE_TOWN_ROOT": str(town),
        "VICHE_BUDGET_TOOL": str(TOOL),
        "PATH": str(bindir) + ":" + env.get("PATH", ""),
        "CAND_TEST_MODE": mode,
        "AGENT_ENV": AGENT,
        "SID_ENV": SID,
        "STATUS_JSON": json.dumps(STATUS),
        "KILL_LOG": str(kill_log),
    })
    return state, env, kill_log


def sh(env, *args):
    p = subprocess.run(["/bin/sh", str(ENGINE), *args], env=env,
                       capture_output=True, text=True, timeout=120)
    return {"rc": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}


def rowstate(state):
    return json.loads((state / "knowledge" / "budget" / "reservations" / (RID + ".json")).read_text())


result = {"capture_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "cases": {}}
root = tempfile.mkdtemp(prefix="viche-stats-cand-")

# -- nominal: real status + real meter ---------------------------------------
state, env, kills = setup(root + "/nominal", "real")
pre_guard = sh(env, "guard", "foresight")
# snapshot independently: does the real meter row satisfy the candidate's precondition?
snap = subprocess.run([sys.executable, str(TOOL), "snapshot", str(pathlib.Path(root) / "nominal" / "meter.db"), SID, "7796"],
                      capture_output=True, text=True, timeout=60)
snap_ok = snap.returncode == 0
snap_obj = json.loads(snap.stdout) if snap_ok else {"stderr": snap.stderr.strip()}

resolved = sh(env, "resolve-session", RID, "statistics-independent-probe",
              "--session", SID, "--by", "statistics-independent-probe")
post = rowstate(state)
post_guard = sh(env, "guard", "foresight")
result["cases"]["nominal"] = {
    "snapshot_succeeded": snap_ok,
    "snapshot_tokens": snap_obj.get("tokens", {}).get("total") if snap_ok else None,
    "snapshot_cost_reported": snap_obj.get("cost_reported") if snap_ok else None,
    "guard_before": pre_guard,
    "resolve": resolved,
    "guard_after": post_guard,
    "row_state": post.get("state"),
    "closed_reason": post.get("closed_reason"),
    "resolved_by": post.get("resolved_by"),
    "attestation": post.get("resolution_attestation"),
    "charge_tokens": (post.get("charge") or {}).get("tokens_total"),
    "usage_tokens": (post.get("usage") or {}).get("tokens_total"),
    "cap_tokens": CAP,
    "liability_not_reduced": (post.get("charge") or {}).get("tokens_total", 0) >= CAP,
    "agent_kill_stop_calls": kills.read_text().strip(),
    "history_last": (post.get("history") or [])[-1] if post.get("history") else None,
}

# -- negative control 1: wrong SID -----------------------------------------
state2, env2, kills2 = setup(root + "/wrong_sid", "wrong_sid")
r2 = sh(env2, "resolve-session", RID, "probe", "--session", SID, "--by", "probe")
p2 = rowstate(state2)
result["cases"]["wrong_sid"] = {
    "resolve": r2,
    "row_state": p2.get("state"),
    "held_reason": p2.get("held_reason"),
    "charge_tokens": (p2.get("charge") or {}).get("tokens_total"),
    "liability_not_reduced": (p2.get("charge") or {}).get("tokens_total", 0) >= CAP,
}

# -- negative control 2: unreadable status ----------------------------------
state3, env3, kills3 = setup(root + "/unreadable", "unreadable")
r3 = sh(env3, "resolve-session", RID, "probe", "--session", SID, "--by", "probe")
p3 = rowstate(state3)
result["cases"]["unreadable_status"] = {
    "resolve": r3,
    "row_state": p3.get("state"),
    "held_reason": p3.get("held_reason"),
    "charge_tokens": (p3.get("charge") or {}).get("tokens_total"),
    "liability_not_reduced": (p3.get("charge") or {}).get("tokens_total", 0) >= CAP,
}

# -- assertions -------------------------------------------------------------
n = result["cases"]["nominal"]
a = {
    "A1_snapshot_succeeded": n["snapshot_succeeded"] is True,
    "A2_snapshot_meter_zero_tokens": n["snapshot_tokens"] == 0,
    "A3_guard_before_refused": n["guard_before"]["rc"] != 0,
    "A4_resolve_rc0": n["resolve"]["rc"] == 0,
    "A5_row_closed": n["row_state"] == "closed",
    "A6_closed_reason_provenance": str(n["closed_reason"]).startswith("operator_resolved_session:"),
    "A7_resolved_by_recorded": n["resolved_by"] == "statistics-independent-probe",
    "A8_attestation_sid_matches": (n["attestation"] or {}).get("session_id") == SID,
    "A9_attestation_status_source": (n["attestation"] or {}).get("status_source") == "antonina agent status",
    "A10_liability_not_reduced": n["liability_not_reduced"] is True,
    "A11_guard_after_ok": n["guard_after"]["rc"] == 0 and n["guard_after"]["stdout"].startswith("guard ok"),
    "A12_no_agent_replay": n["agent_kill_stop_calls"] == "",
    "B1_wrong_sid_stays_held": result["cases"]["wrong_sid"]["row_state"] == "held",
    "B2_wrong_sid_reason": result["cases"]["wrong_sid"]["held_reason"] == "operator_resolution_session_mismatch",
    "B3_wrong_sid_no_liability_cut": result["cases"]["wrong_sid"]["liability_not_reduced"] is True,
    "C1_unreadable_stays_held": result["cases"]["unreadable_status"]["row_state"] == "held",
    "C2_unreadable_reason": result["cases"]["unreadable_status"]["held_reason"] == "operator_resolution_status_unreadable",
    "C3_unreadable_no_liability_cut": result["cases"]["unreadable_status"]["liability_not_reduced"] is True,
}
result["assertions"] = a
result["all_assertions_pass"] = all(a.values())
result["failed_assertions"] = [k for k, v in a.items() if not v]
result["assertion_count"] = len(a)

(EVID / "measurement.json").write_text(json.dumps(result, indent=2, sort_keys=True))
print(json.dumps(result, indent=2, sort_keys=True))
shutil.rmtree(root, ignore_errors=True)

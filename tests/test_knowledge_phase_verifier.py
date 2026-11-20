#!/usr/bin/env python3
"""End-to-end tests for the independent Act 32 phase-gate verifier.

All reviews/artifacts/snapshots here are SYNTHETIC fixtures created in throwaway
Git repositories. They are format/soundness tests only: they do not sign,
authorize or enable any real office, and they forge no real Judiciary/Governor
signature. The attestation snapshot stands in for the live Antonina board
review gate + officer comment + appointment/session channels.
"""

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "government" / "knowledge-phase-verifier.py"
SPEC = importlib.util.spec_from_file_location("knowledge_phase_verifier", VERIFIER)
kpv = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(kpv)

BASE = 1795198800                 # 2026-11-20T18:20:00Z
NB = BASE
EXP = NB + 14 * 86400 - 1         # just under the 14-day initial cap
BASELINE = "diagnostic-baseline-bytes\n"
ACTIVATION = "all-offices-disabled\n"
JUDGE = "c1e00008"
JUDGE_AGENT = "5mRzSPKbwvhnJy1Pt9lCLl-otis"


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def git(town: Path, *args: str) -> str:
    out = subprocess.run(["git", "-C", str(town), *args], check=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return out.stdout.decode().strip()


class PhaseVerifierTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="kpv-test-")
        self.town = Path(self.tmp.name) / "town"
        self.town.mkdir(parents=True)
        (self.town / "government").mkdir()
        (self.town / "records/knowledge/phases/rollbacks").mkdir(parents=True)
        (self.town / "government/LAWS.md").write_text(
            "## Act 32 — Institutional Knowledge and Communications Act "
            "(enacted 2026-11-20T07:33:00Z by recorded vote on bill "
            "institutional-knowledge-and-communications-act-v4)\n"
            "## Act 33 — Reauthorizing Act (enacted 2026-12-21T00:00:00Z)\n",
            encoding="utf-8")
        (self.town / "government/branch-officers.tsv").write_text(
            "executive\tc1e00002\tExecutive\n"
            "judiciary\t%s\tJudiciary\n"
            "innovation-centre\tc1e00011\tInnovation\n" % JUDGE,
            encoding="utf-8")
        (self.town / "records/knowledge/baseline-20261119.json").write_text(BASELINE, encoding="utf-8")
        (self.town / "records/knowledge/activation.json").write_text(ACTIVATION, encoding="utf-8")
        git(self.town, "init", "-q")
        git(self.town, "config", "user.email", "test@example.invalid")
        git(self.town, "config", "user.name", "test-fixture")
        git(self.town, "add", "-A")
        git(self.town, "commit", "-q", "-m", "base")
        self.base_commit = git(self.town, "rev-parse", "HEAD")
        self.evidence = [{
            "name": "baseline",
            "path": "records/knowledge/baseline-20261119.json",
            "sha256": sha(BASELINE),
            "git": {"commit": self.base_commit,
                    "path": "records/knowledge/baseline-20261119.json"},
        }]
        self.ev_digest = kpv.canonical_digest(self.evidence)
        self.snapshot = {
            "issues": {},
            "appointments": {"judiciary": JUDGE_AGENT},
            "agent_status": {"id": JUDGE_AGENT, "state": "idle"},
        }
        self.snapshot_path = str(Path(self.tmp.name) / "attestation.json")
        self._write_snapshot()

    def tearDown(self):
        self.tmp.cleanup()

    # ---- helpers --------------------------------------------------------
    def _write_snapshot(self):
        Path(self.snapshot_path).write_text(json.dumps(self.snapshot), encoding="utf-8")

    def artifact(self, gate_id="statistics-initial", reviewer=JUDGE,
                 role="judiciary", decision="proceed", digest=None,
                 reviewed_at="2026-11-21T12:00:00Z", name=None,
                 issue_id="issue-main", gate_ids=None,
                 board_commit=None, board_reviewer=None, with_comment=True):
        digest = digest or self.ev_digest
        text = (
            "gate: %s\nreviewer: %s\nreviewer_role: %s\ndecision: %s\n"
            "evidence_digest: %s\nreviewed_at: %s\n"
            % (gate_id, reviewer, role, decision, digest, reviewed_at)
        )
        rel = "records/knowledge/phases/%s.md" % (name or ("review-" + gate_id))
        (self.town / rel).write_text(text, encoding="utf-8")
        git(self.town, "add", rel)
        git(self.town, "commit", "-q", "-m", "review artifact " + (name or gate_id))
        commit = git(self.town, "rev-parse", "HEAD")
        gates = gate_ids or [gate_id]
        comment = "Reviewed gates %s against artifact %s" % (" ".join(gates), commit[:7])
        self.snapshot["issues"][issue_id] = {
            "number": issue_id,
            "review": {
                "commit": board_commit or commit,
                "reviewer": board_reviewer if board_reviewer is not None else ("%s (Judiciary)" % JUDGE),
                "verdict": "approve",
                "recordedAt": reviewed_at,
                "rationale": "synthetic fixture",
            },
            "comments": ([{"author": JUDGE, "body": comment}] if with_comment else []),
        }
        self._write_snapshot()
        return {"git_commit": commit, "git_path": rel, "sha256": sha(text)}, text

    def gate(self, *, gate_id="statistics-initial", office="statistics",
             phase="initial", decision="proceed", nb=NB, exp=EXP,
             reviewer=JUDGE, role="judiciary", pred=None,
             with_review=True, day30=None, reauth=None, signed=None,
             att_issue="issue-main", include_attestation=True):
        art, _ = self.artifact(gate_id=gate_id, reviewer=reviewer, role=role,
                              decision="proceed", issue_id=att_issue) \
            if with_review else (None, None)
        rec = {
            "schema": kpv.SCHEMA,
            "gate_id": gate_id,
            "act": 32,
            "act_bill_id": kpv.ACT_BILL_ID,
            "office": office,
            "phase": phase,
            "host": "billy-dev",
            "predecessor": pred,
            "next_office": "foresight" if office == "statistics" else None,
            "created_at": "2026-11-20T18:20:00Z",
            "created_epoch": BASE,
            "not_before": nb,
            "expires_at": exp,
            "decision": decision,
            "preconditions": {k: {"ok": True} for k in kpv.PRECONDITION_KEYS},
            "evidence": self.evidence,
            "evidence_digest": self.ev_digest,
            "review": None,
            "day30_review": None,
        }
        if include_attestation:
            rec["attestation"] = {"issue_id": att_issue,
                                  "expected_reviewer": JUDGE,
                                  "officer_agent_id": JUDGE_AGENT}
        if with_review and decision == "proceed":
            rec["review"] = {
                "reviewer": reviewer,
                "reviewer_role": role,
                "decision": "proceed",
                "signed_at": "2026-11-20T18:21:00Z",
                "signed_epoch": signed if signed is not None else NB + 100,
                "review_artifact": art,
            }
        if day30 is not None:
            rec["day30_review"] = day30
        if reauth is not None:
            rec["reauthorizing_act"] = reauth
        return rec

    def write_gate(self, rec, name=None):
        rel = "records/knowledge/phases/%s.json" % (name or rec["gate_id"])
        (self.town / rel).write_text(json.dumps(rec), encoding="utf-8")
        return rel

    def run_verifier(self, *args, at=None):
        cmd = [sys.executable, str(VERIFIER), "--town", str(self.town)]
        if at is not None:
            cmd += ["--at", str(at)]
        cmd += list(args)
        env = os.environ.copy()
        env["VICHE_PHASE_ATTESTATION_JSON"] = self.snapshot_path
        env.pop("VICHE_POST_DB", None)
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, env=env)
        try:
            out = json.loads(proc.stdout)
        except json.JSONDecodeError:
            out = {"raw": proc.stdout, "stderr": proc.stderr}
        return proc.returncode, out

    def verify(self, rec, at=None, name=None):
        rel = self.write_gate(rec, name)
        return self.run_verifier("verify", rel, at=at)

    # ---- happy paths -----------------------------------------------------
    def test_valid_statistics_initial_proceed_no_30day_wait(self):
        rec = self.gate()
        rc, out = self.verify(rec, at=NB + 200)
        self.assertEqual(rc, 0, out)
        self.assertEqual(out["decision"], "proceed")
        self.assertTrue(out["ok"])
        self.assertNotIn("day-30", " ".join(out["reasons"]))

    def test_check_subcommand_always_zero(self):
        rec = self.gate()
        rel = self.write_gate(rec)
        rc, out = self.run_verifier("check", rel, at=NB + 200)
        self.assertEqual(rc, 0)
        self.assertEqual(out["decision"], "proceed")

    def test_successor_chain_valid_even_if_predecessor_no_longer_live(self):
        pred = self.gate(gate_id="statistics-initial")
        pred_rel = self.write_gate(pred, name="statistics-initial")
        succ = self.gate(gate_id="foresight-initial", office="foresight",
                         nb=NB + 200, exp=NB + 200 + 13 * 86400,
                         signed=NB + 200, att_issue="issue-foresight",
                         pred={"gate_id": "statistics-initial", "office": "statistics",
                               "record": pred_rel})
        rc, out = self.verify(succ, name="foresight-initial", at=NB + 200)
        self.assertEqual(rc, 0, out)
        self.assertEqual(out["decision"], "proceed")

    # ---- fail-closed: reviewer / evidence / attestation -----------------
    def test_no_review_fails_closed(self):
        rec = self.gate(with_review=False)
        rc, out = self.verify(rec, at=NB + 200)
        self.assertNotEqual(rc, 0)
        self.assertNotEqual(out["decision"], "proceed")
        self.assertTrue(any("absent" in r for r in out["reasons"]), out)

    def test_signed_by_field_alone_is_ignored(self):
        rec = self.gate(with_review=False)
        rec["signed_by"] = JUDGE
        rec["signed-by"] = "Vitalik"
        rc, out = self.verify(rec, at=NB + 200)
        self.assertNotEqual(rc, 0)
        self.assertNotEqual(out["decision"], "proceed")

    def test_reviewer_not_in_registry(self):
        rec = self.gate(reviewer="c1e99999")
        rc, out = self.verify(rec, at=NB + 200)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("registry" in r for r in out["reasons"]), out)

    def test_non_judiciary_cannot_sign_proceed(self):
        rec = self.gate(reviewer="c1e00002", role="executive")
        rc, out = self.verify(rec, at=NB + 200)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("permitted" in r for r in out["reasons"]), out)

    def test_rogue_git_review_with_wrong_board_commit_fails(self):
        """A perfect Git text artifact with a real Judiciary id is not enough."""
        art, _ = self.artifact(gate_id="statistics-initial", name="rogue-artifact",
                               issue_id="issue-rogue", board_commit=self.base_commit)
        rec = self.gate()
        rec["review"]["review_artifact"] = art
        rec["attestation"] = {"issue_id": "issue-rogue",
                              "expected_reviewer": JUDGE,
                              "officer_agent_id": JUDGE_AGENT}
        rc, out = self.verify(rec, at=NB + 200)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("exact review-artifact commit" in r
                            for r in out["reasons"]), out)

    def test_missing_institutional_attestation_fails(self):
        rec = self.gate(include_attestation=False)
        rc, out = self.verify(rec, at=NB + 200)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("attestation" in r for r in out["reasons"]), out)

    def test_board_comment_by_officer_required(self):
        rec = self.gate()
        self.snapshot["issues"]["issue-main"]["comments"] = []
        self._write_snapshot()
        rc, out = self.verify(rec, at=NB + 200)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("officer-authored board comment" in r
                            for r in out["reasons"]), out)

    def test_agent_appointment_mismatch_fails(self):
        self.snapshot["appointments"]["judiciary"] = "some-rogue-agent"
        self._write_snapshot()
        rec = self.gate()
        rc, out = self.verify(rec, at=NB + 200)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("appointment registry" in r for r in out["reasons"]), out)

    def test_review_artifact_digest_mismatch(self):
        rec = self.gate()
        rec["review"]["review_artifact"]["sha256"] = "0" * 64
        rc, out = self.verify(rec, at=NB + 200)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("digest mismatch" in r for r in out["reasons"]), out)

    def test_forged_commit_rejected(self):
        rec = self.gate()
        rec["review"]["review_artifact"]["git_commit"] = "0" * 40
        rc, out = self.verify(rec, at=NB + 200)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("valid Git commit" in r for r in out["reasons"]), out)

    def test_unsafe_git_path_rejected(self):
        rec = self.gate()
        rec["review"]["review_artifact"]["git_path"] = "records/../etc/passwd"
        rc, out = self.verify(rec, at=NB + 200)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("unsafe artifact path" in r for r in out["reasons"]), out)

    def test_review_artifact_rebound_to_other_gate_rejected(self):
        art, _ = self.artifact(gate_id="statistics-initial", name="reused-artifact",
                               issue_id="issue-reused", board_commit=self.base_commit)
        rec = self.gate(gate_id="other-gate")
        rec["review"]["review_artifact"] = art
        rec["attestation"] = {"issue_id": "issue-reused",
                              "expected_reviewer": JUDGE,
                              "officer_agent_id": JUDGE_AGENT}
        rc, out = self.verify(rec, name="other-gate", at=NB + 200)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("binding mismatch" in r for r in out["reasons"]), out)

    def test_evidence_tamper_rejected(self):
        rec = self.gate()
        rec["evidence"][0]["sha256"] = "1" * 64
        rc, out = self.verify(rec, at=NB + 200)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("mismatch" in r for r in out["reasons"]), out)

    # ---- fail-closed: act / office / window -----------------------------
    def test_wrong_act_number(self):
        rec = self.gate()
        rec["act"] = 31
        rc, out = self.verify(rec, at=NB + 200)
        self.assertNotEqual(rc, 0)
        self.assertEqual(out["decision"], "invalid")

    def test_wrong_bill_id(self):
        rec = self.gate()
        rec["act_bill_id"] = "some-other-bill"
        rc, out = self.verify(rec, at=NB + 200)
        self.assertNotEqual(rc, 0)
        self.assertEqual(out["decision"], "invalid")

    def test_invalid_office(self):
        rec = self.gate(office="spying", pred=None)
        rc, out = self.verify(rec, at=NB + 200)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("predecessor" in r for r in out["reasons"]), out)

    def test_initial_window_over_14_days(self):
        rec = self.gate(exp=NB + 14 * 86400 + 5)
        rc, out = self.verify(rec, at=NB + 200)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("cap" in r for r in out["reasons"]), out)

    def test_renewal_window_over_45_days(self):
        rec = self.gate(phase="renewal", exp=NB + 45 * 86400 + 5,
                        reauth={"act": 33})
        rc, out = self.verify(rec, at=NB + 200)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("45-day" in r or "cap" in r for r in out["reasons"]), out)

    def test_precondition_false_holds(self):
        rec = self.gate()
        rec["preconditions"]["executive_order"]["ok"] = False
        rc, out = self.verify(rec, at=NB + 200)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("executive_order" in r for r in out["reasons"]), out)

    def test_expiry_refuses_new_launch(self):
        rec = self.gate()
        rc, out = self.verify(rec, at=EXP + 1)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("expired" in r for r in out["reasons"]), out)

    def test_not_yet_effective_holds(self):
        rec = self.gate()
        rc, out = self.verify(rec, at=NB - 1)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("not yet effective" in r for r in out["reasons"]), out)

    # ---- fail-closed: chain / renewal ----------------------------------
    def test_successor_not_before_before_predecessor_signed_date(self):
        pred = self.gate(gate_id="statistics-initial", signed=NB + 500)
        pred_rel = self.write_gate(pred, name="statistics-initial")
        succ = self.gate(gate_id="foresight-initial", office="foresight",
                         nb=NB + 200, exp=NB + 200 + 13 * 86400,
                         signed=NB + 200, att_issue="issue-foresight",
                         pred={"gate_id": "statistics-initial", "office": "statistics",
                               "record": pred_rel})
        rc, out = self.verify(succ, name="foresight-initial", at=NB + 200)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("precedes predecessor signed gate date" in r
                            for r in out["reasons"]), out)

    def _initial_and_renewal(self):
        initial = self.gate(gate_id="statistics-initial")
        rel = self.write_gate(initial, name="statistics-initial")
        renewal = self.gate(gate_id="statistics-renewal", phase="renewal",
                            nb=NB + 200, exp=NB + 200 + 40 * 86400,
                            signed=NB + 200, att_issue="issue-renewal",
                            pred={"gate_id": "statistics-initial", "office": "statistics",
                                  "record": rel},
                            reauth={"act": 33})
        return renewal

    def test_renewal_missing_day30_review_auto_holds(self):
        renewal = self._initial_and_renewal()
        rc, out = self.verify(renewal, name="statistics-renewal", at=NB + 200)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("day-30" in r and "automatic hold" in r
                            for r in out["reasons"]), out)

    def test_renewal_late_day30_review_holds(self):
        renewal = self._initial_and_renewal()
        art, _ = self.artifact(gate_id="statistics-renewal", name="day30-late",
                               issue_id="issue-day30", gate_ids=["statistics-renewal"])
        renewal["day30_review"] = {
            "reviewer": JUDGE, "reviewer_role": "judiciary", "decision": "proceed",
            "signed_at": "2026-12-25T00:00:00Z",
            "signed_epoch": NB + 30 * 86400 + 5,
            "review_artifact": art,
        }
        renewal["day30_attestation"] = {"issue_id": "issue-day30",
                                        "expected_reviewer": JUDGE,
                                        "officer_agent_id": JUDGE_AGENT}
        rc, out = self.verify(renewal, name="statistics-renewal", at=NB + 200)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("after deadline" in r for r in out["reasons"]), out)

    def test_renewal_missing_reauthorizing_act_holds(self):
        renewal = self._initial_and_renewal()
        del renewal["reauthorizing_act"]
        rc, out = self.verify(renewal, name="statistics-renewal", at=NB + 200)
        self.assertNotEqual(rc, 0)
        self.assertTrue(any("reauthorizing Act" in r for r in out["reasons"]), out)

    # ---- robustness: determinism / outage / invalid state / rollback ----
    def test_deterministic_across_repeated_runs(self):
        rec = self.gate()
        rel = self.write_gate(rec)
        rc1, out1 = self.run_verifier("verify", rel, at=NB + 200)
        rc2, out2 = self.run_verifier("verify", rel, at=NB + 200)
        self.assertEqual(rc1, rc2)
        self.assertEqual(json.dumps(out1, sort_keys=True), json.dumps(out2, sort_keys=True))

    def test_post_outage_does_not_change_decision(self):
        rec = self.gate()
        rel = self.write_gate(rec)
        before = self.run_verifier("verify", rel, at=NB + 200)
        (self.town / "government/post.db").write_text("not a database", encoding="utf-8")
        env = os.environ.copy()
        env["VICHE_POST_DB"] = str(self.town / "government/post.db")
        env["VICHE_PHASE_ATTESTATION_JSON"] = self.snapshot_path
        cmd = [sys.executable, str(VERIFIER), "--town", str(self.town),
               "--at", str(NB + 200), "verify", rel]
        after_proc = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, text=True)
        after = (after_proc.returncode, json.loads(after_proc.stdout))
        self.assertEqual(before, after)

    def test_invalid_git_state_fails_closed(self):
        rc, out = self.run_verifier("verify", "records/knowledge/phases/missing.json",
                                    at=NB + 200)
        self.assertNotEqual(rc, 0)
        self.assertEqual(out["decision"], "invalid")

    def test_rollback_blocks_proceed(self):
        rec = self.gate()
        rel = self.write_gate(rec)
        rc0, out0 = self.run_verifier("verify", rel, at=NB + 200)
        self.assertEqual(rc0, 0, out0)
        rc_rb, _ = self.run_verifier("rollback", "--gate-id", "statistics-initial",
                                     "--reason", "emergency hold after adverse evidence",
                                     at=NB + 300)
        self.assertEqual(rc_rb, 0)
        rc1, out1 = self.run_verifier("verify", rel, at=NB + 300)
        self.assertNotEqual(rc1, 0)
        self.assertTrue(any("rollback" in r for r in out1["reasons"]), out1)

    # ---- audit: expiry, in-flight, new invocation -----------------------
    def test_audit_flags_new_invocation_after_expiry(self):
        rec = self.gate()
        self.write_gate(rec)
        ledger = self.town / "records/knowledge/phases/dispatch-ledger.jsonl"
        lines = [
            {"gate_id": "statistics-initial", "kind": "launch", "at": NB + 10,
             "invocation_id": "ok-1"},
            {"gate_id": "statistics-initial", "kind": "launch", "at": EXP + 10,
             "invocation_id": "forged-after-expiry"},
        ]
        ledger.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
        rc, out = self.run_verifier("audit", at=EXP + 20)
        self.assertEqual(rc, 1)
        self.assertFalse(out["ok"])
        self.assertEqual(len(out["new_invocation_after_expiry"]), 1)
        self.assertTrue(out["violations"])

    def test_audit_distinguishes_inflight_after_expiry(self):
        rec = self.gate()
        self.write_gate(rec)
        ledger = self.town / "records/knowledge/phases/dispatch-ledger.jsonl"
        lines = [
            {"gate_id": "statistics-initial", "kind": "launch", "at": NB + 10,
             "invocation_id": "ok-1"},
            {"gate_id": "statistics-initial", "kind": "in_flight_continue",
             "at": EXP + 10, "invocation_id": "wind-down"},
        ]
        ledger.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
        rc, out = self.run_verifier("audit", at=EXP + 20)
        self.assertEqual(rc, 0, out)
        self.assertTrue(out["ok"])
        self.assertEqual(out["new_invocation_after_expiry"], [])
        self.assertTrue(out["in_flight_continuations"][0]["after_expiry"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

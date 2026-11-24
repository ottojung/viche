#!/usr/bin/env python3
"""Offline tests: parallel assistance must not control leases or publication."""
import contextlib
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from missions.pnp import assignment, cli, config, frontier, state, status, support
from missions.pnp.proofs import corpus

GAP = "L-meta-909"
GOAL = "∀ G : Nat, G = 0 → ∃ C : Nat, C ≤ 6 ∧ C = G"
NEGATION = "∀ G : Nat, G = 0 → ¬ (∃ C : Nat, C ≤ 6 ∧ C = G)"


class SupportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name) / "pnp"
        for obj, key, value in (
            (config, "STATE_ROOT", str(root)),
            (config, "GAPS_DIR", str(root / "gaps")),
            (config, "CACHE_DIR", str(root / "cache")),
            (status, "STATE", root.parent),
        ):
            p = patch.object(obj, key, value)
            p.start()
            self.addCleanup(p.stop)
        self.rec = state.create(GAP, state="LEASED", lease="first",
                                statement=GOAL, imports=[], context="test",
                                lease_expires_at=time.time() + 600)

    def test_direct_delivery_and_idempotence(self):
        target, = support.targets()
        self.assertNotIn("lease", target)
        self.assertNotIn("first", target["attempt"])
        note = support.advise(GAP, target["attempt"], "methods",
                              "/tmp/proof.lean", "Use the verified sublemma.")
        self.assertEqual(note, support.advise(GAP, target["attempt"], "methods",
                                              "/tmp/proof.lean", "Use the verified sublemma."))
        self.assertEqual(state.load(GAP), self.rec)
        # Guard retains its own independent decision and adds advice.
        with patch.object(assignment, "resolve", return_value=(GAP, "first")):
            with patch.object(frontier, "checkpoint", return_value={"decision": "continue"}):
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    self.assertEqual(cli.main(["guard"]), 0)
        result=json.loads(out.getvalue())
        self.assertIn("missions.pnp.tools",result.pop("research_tools")["command"])
        self.assertEqual(result,{"decision": "continue", "research_advice": [note]})

    def test_old_attempt_and_changed_statement_rejected(self):
        a = support.attempt(self.rec)
        support.advise(GAP, a, "knowledge", "proof link", "Check the statement.")
        state.update(GAP, statement=GOAL + " ∧ True")
        self.assertEqual(support.read(state.load(GAP)), [])
        with self.assertRaises(ValueError):
            support.advise(GAP, a, "flow", "log", "Stop wasting time.")
        state.update(GAP, statement=GOAL, lease="second")
        self.assertEqual(support.read(state.load(GAP)), [])
        with self.assertRaises(ValueError):
            support.advise(GAP, a, "methods", "artifact", "Reuse proof.")
        state.update(GAP, state="RELEASED")
        self.assertEqual(support.targets(), [])

    def test_corrupt_advice_isolated(self):
        path = support.directory(self.rec)
        path.mkdir(parents=True)
        (path / "knowledge.json").write_text("not JSON")
        (path / "flow.json").write_text(json.dumps(
            {"attempt": support.attempt(self.rec), "kind": "flow",
             "id": [], "coordinate": True, "message": "x", "evidence": "y"}))
        self.assertEqual(support.read(self.rec), [])
        self.assertEqual(frontier.checkpoint(GAP, "first")["decision"], "continue")

    def test_exact_opposite_and_near_miss(self):
        with corpus.open_index() as db:
            for path, stmt in [("same", GOAL), ("neg", NEGATION),
                               ("different_bound", NEGATION.replace("≤ 6", "≤ 7")),
                               ("different_hypothesis", NEGATION.replace("G = 0", "G = 1")),
                               ("not_final", NEGATION + " ∧ True")]:
                db.execute("insert into proof values(?,?,?,?,?,?)",
                           (path, "blob-" + path, stmt, "", "[]", "[]"))
        with corpus.open_index() as db:
            self.assertEqual({r["path"]: r["relation"] for r in support.matches(db, GOAL)},
                             {"same": "exact statement", "neg": "opposite conclusion"})
            self.assertEqual({r["path"]: r["relation"] for r in support.matches(db, NEGATION)},
                             {"same": "opposite conclusion", "neg": "exact statement"})

    @patch.object(support.github, "repository_name", return_value="fixture-owner/fixture-proofs")
    def test_scan_is_advisory_and_stable(self, repository_name):
        with corpus.open_index() as db:
            db.execute("insert into proof values(?,?,?,?,?,?)",
                       ("lean/PEqualNP/Outside/L_meta_905.lean", "abc", NEGATION, "", "[]", "[]"))
        with patch.object(corpus, "update", return_value="rev1"):
            self.assertEqual(support.scan()["matches"], 1)
        note, = support.read(self.rec)
        self.assertTrue(note["coordinate"])
        self.assertIn("opposite conclusion", note["message"])
        self.assertEqual(note["evidence"], "https://github.com/fixture-owner/fixture-proofs/blob/rev1/lean/PEqualNP/Outside/L_meta_905.lean")
        repository_name.assert_called_with(config.UPSTREAM_ID)
        with patch.object(corpus, "update", return_value="rev2"):
            support.scan()
        self.assertEqual(support.read(self.rec), [note])
        self.assertEqual(state.load(GAP), self.rec)
        with corpus.open_index() as db:
            db.execute("delete from proof")
        with patch.object(corpus, "update", return_value="rev3"):
            support.scan()
        self.assertEqual(support.read(self.rec), [])

    def test_support_not_primary_and_dispatch_coverage(self):
        roster = [{"id": "scout", "title": "Viche P vs NP support: knowledge, methods",
                   "state": "running", "cwd": "/tmp/scout"},
                  {"id": "primary", "title": "Viche P vs NP: L-meta-909",
                   "state": "running", "cwd": "/tmp/primary"}]
        self.assertEqual(support.roles(roster[0]), ["knowledge", "methods"])
        self.assertEqual(support.roles(roster[1]), [])
        reply = subprocess.CompletedProcess([], 0, json.dumps({"agents": roster}), "")
        with patch.object(status.subprocess, "run", return_value=reply):
            w = status.workers()
        self.assertEqual(w["count"], 1)
        self.assertEqual(len(w["support"]), 1)
        with patch.object(status, "workers", return_value=w), \
             patch.object(status.leaderboard, "load", return_value={}), \
             patch.object(status.frontier, "load", return_value={"gaps": {}, "ordinary": 0}), \
             patch.object(status.frontier.build_control, "legacy_compilers", return_value=[]), \
             patch.object(status.frontier.build_control, "headroom", return_value=1024):
            snap = status.snapshot()
        self.assertEqual(snap["research_support"]["coverage_missing"], ["flow", "lease-evaluation"])
        self.assertTrue(snap["coordination_due"])
        self.assertEqual(snap["workers"]["count"], 1)
        self.assertEqual(snap["dispatch_signal"]["missing_support"], ["flow", "lease-evaluation"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

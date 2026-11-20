#!/usr/bin/env python3
"""Hermetic Act 27 marker acceptance and fail-closed fixtures."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
from unittest.mock import patch
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "government/audit-accountability.py"
SPEC = importlib.util.spec_from_file_location("audit_accountability", SCRIPT)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)
CASE = "7750b56b775ed8959a"
TOKEN = "a" * 32


class LegacyMarkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.town = self.root / "town"
        self.state = self.root / "state/oversight"
        (self.town / "records/oversight/corrections").mkdir(parents=True)
        self.state.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.town)], check=True)
        self.env = {**os.environ, "VICHE_TOWN_ROOT": str(self.town),
                    "VICHE_STATE_ROOT": str(self.root / "state")}

    def tearDown(self):
        self.tmp.cleanup()

    def commit(self, path):
        subprocess.run(["git", "-C", str(self.town), "add", str(path.relative_to(self.town))], check=True)
        subprocess.run(["git", "-C", str(self.town), "-c", "user.name=Fixture", "-c",
                        "user.email=fixture@example.invalid", "commit", "-qm", "fixture"], check=True)

    def fixture(self, marker=True, review=True, bad_hash=False, post=False, registry="valid", twice=False):
        path = self.town / f"records/oversight/corrections/{CASE}.jsonl"
        legacy_rows = [
            {"at": 1792738483, "case_id": CASE, "correction": True,
             "confirmed": False, "verdict": "finding", "cycle_id": None},
            {"at": 1792738485, "case_id": CASE, "correction": True,
             "confirmed": True, "verdict": "finding", "cycle_id": None},
            {"at": 1792741896, "case_id": CASE, "correction": True,
             "confirmed": False, "verdict": "not_assigned", "cycle_id": None},
        ]
        raw = b"".join((json.dumps(row, sort_keys=True) + "\n").encode()
                       for row in legacy_rows)
        path.write_bytes(raw)
        self.commit(path)
        self.legacy_raw = raw
        # Act 27 hashes every exact JSONL row byte sequence at its introducing
        # commit, including each line terminator.
        # The closed Act 27 allowlist is anchored at this introducing commit.
        self.source_commit = "2c6d695298b855f1aebf42f3a972f2007eed31f8"
        rows = []
        for position, raw_row in enumerate(raw.splitlines(keepends=True), 1):
            digest = hashlib.sha256(raw_row).hexdigest()
            rows.append({"position": position, "introducing_commit": self.source_commit,
                         "sha256_row_bytes_including_LF": "0" * 64 if bad_hash and position == 1 else digest})
        appended = []
        if marker:
            m = {"type": "legacy_no_identity", "rows": rows,
                 "signature": {"filing_office": "judiciary", "officer": "c1e00008"},
                 "statement": "These rows predate the anchor rule; no cycle identity exists or is asserted."}
            with path.open("ab") as f:
                f.write((json.dumps(m, sort_keys=True) + "\n").encode())
            self.commit(path)
            self.marker_commit = subprocess.check_output(
                ["git", "-C", str(self.town), "rev-parse", "HEAD"], text=True).strip()
            if review:
                review_path = self.town / "records/reviews/CLERK-ACT27-LEGACY-MARKER-INDEPENDENT-REVIEW-20261120.md"
                review_path.parent.mkdir(parents=True, exist_ok=True)
                review_path.write_text(
                    "# Clerk independent review\n\n"
                    "Reviewer: Clerk `c1a00001`\n"
                    f"marker commit `{self.marker_commit}`\n"
                    "**APPROVE the narrow marker-integrity review.**\n"
                    "The Clerk independently derives hashes from introducing-commit Git blobs.\n"
                    "The source review is performed by a different office from the Judiciary filer.\n"
                    "Hashing includes each row's trailing LF, as specified.\n"
                    "markers remain ineffective until the Executive implements Act 27 §6\n"
                    + "\n".join(item["sha256_row_bytes_including_LF"] for item in rows) + "\n")
                self.commit(review_path)
        if post:
            appended.append({"case_id": CASE, "correction": True, "confirmed": False,
                             "at": 1795000000, "verdict": "finding"})
        else:
            correction = {"case_id": CASE, "correction": True, "confirmed": False,
                          "at": 1795000000, "verdict": "finding", "cycle_id": TOKEN}
            appended.append(correction)
            appended.append(dict(correction, confirmed=True))
            if twice:
                appended.append(dict(correction))
        with path.open("ab") as f:
            for row in appended:
                f.write((json.dumps(row, sort_keys=True) + "\n").encode())
        self.commit(path)
        registry_path = self.state / "audit-cycle-identities.tsv"
        if registry != "absent":
            registry_path.write_text(f"1795000000\t{TOKEN}\n" if registry == "valid" else
                "truncated\n" if registry == "truncated" else f"1795000000\t{'b'*32}\n")

    def check(self, succeeds):
        old = os.environ.copy()
        os.environ.update(self.env)
        try:
            original = audit.subprocess.run
            def run(args, **kwargs):
                if (len(args) > 4 and args[0] == "git" and args[3] == "show" and
                        args[-1].startswith(self.source_commit + ":")):
                    return subprocess.CompletedProcess(args, 0, stdout=self.legacy_raw, stderr=b"")
                return original(args, **kwargs)
            with patch.object(audit.subprocess, "run", side_effect=run):
                self._check(succeeds)
        finally:
            os.environ.clear()
            os.environ.update(old)

    def _check(self, succeeds):
        if succeeds:
            self.assertIsNotNone(audit.committed_confirmed_correction(CASE))
            self.assertEqual(audit.used_cycle_tokens({}, CASE), {TOKEN})
        else:
            with self.assertRaises(ValueError):
                audit.committed_confirmed_correction(CASE)

    def test_i_effective_marker_allows_one_token_cycle(self):
        self.fixture(); self.check(True)

    def test_ii_second_same_cycle_correction_rejected(self):
        self.fixture(twice=True); self.check(False)

    def test_iii_hash_mismatch_rejected(self):
        self.fixture(bad_hash=True); self.check(False)

    def test_iv_unmarked_legacy_rejected(self):
        self.fixture(marker=False); self.check(False)

    def test_v_post_commencement_tokenless_row_rejected(self):
        self.fixture(post=True); self.check(False)

    def test_vi_missing_independent_review_rejected(self):
        self.fixture(review=False); self.check(False)

    def test_vii_registry_absent_truncated_and_mismatched_rejected(self):
        for state in ("absent", "truncated", "mismatched"):
            with self.subTest(state=state):
                self.setUp()
                self.fixture(registry=state)
                self.check(False)
                self.tearDown()


if __name__ == "__main__":
    unittest.main(verbosity=2)

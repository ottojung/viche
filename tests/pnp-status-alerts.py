"""Regression for actionable publication alerts in the Executive status signal.

A permanently dead FAULT (expired lease, no signed commit to recover into a PR)
must not wake every Executive pass; live/recoverable faults and real failures
must stay visible.
"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from missions.pnp import status


def row(gap, state, **kw):
    d = {"gap": gap, "state": state, "lease_expires_at": None,
         "commit_sha": None, "failure_reason": None}
    d.update(kw)
    return d


class Tests(unittest.TestCase):
    NOW = 1000.0

    def test_stale_unrecoverable_fault_is_not_an_alert(self):
        rows = [row("L-meta-a", "FAULT", lease_expires_at=900.0,
                    failure_reason="signed commit failed: candidate path already exists at base")]
        self.assertEqual(status.actionable_publication_alerts(rows, self.NOW), [])

    def test_live_fault_without_commit_is_an_alert(self):
        rows = [row("L-meta-b", "FAULT", lease_expires_at=1100.0,
                    failure_reason="checkout unavailable")]
        self.assertEqual(status.actionable_publication_alerts(rows, self.NOW), ["L-meta-b"])

    def test_recoverable_fault_with_commit_is_an_alert(self):
        rows = [row("L-meta-c", "FAULT", lease_expires_at=900.0,
                    commit_sha="a" * 40, failure_reason="push failed")]
        self.assertEqual(status.actionable_publication_alerts(rows, self.NOW), ["L-meta-c"])

    def test_fault_without_lease_expiry_is_an_alert(self):
        rows = [row("L-meta-d", "FAULT", failure_reason="unknown fault")]
        self.assertEqual(status.actionable_publication_alerts(rows, self.NOW), ["L-meta-d"])

    def test_rejection_and_failed_pr_are_alerts(self):
        rows = [row("L-meta-e", "REJECTED", lease_expires_at=800.0),
                row("L-meta-f", "PR_OPEN", failure_reason="validation failed"),
                row("L-meta-g", "PR_OPEN")]
        self.assertEqual(status.actionable_publication_alerts(rows, self.NOW),
                         ["L-meta-e", "L-meta-f"])

    def test_mixed_pool_keeps_only_actionable(self):
        rows = [row("L-meta-z", "FAULT", lease_expires_at=900.0),
                row("L-meta-y", "FAULT", lease_expires_at=900.0, commit_sha="b" * 40),
                row("L-meta-x", "RELEASED"),
                row("L-meta-w", "PR_OPEN", failure_reason="drive failed")]
        self.assertEqual(status.actionable_publication_alerts(rows, self.NOW),
                         ["L-meta-w", "L-meta-y"])


if __name__ == "__main__":
    unittest.main()

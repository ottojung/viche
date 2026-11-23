#!/usr/bin/env python3
"""Offline, mocked acceptance tests for the PnP subsystem.

No real desk claim, Git push or upstream PR is made here; real external
effects are exercised only after these tests are green.
"""
import hashlib
import os
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
TMP = tempfile.mkdtemp(prefix="pnp-tests-")
os.environ["PNP_STATE_ROOT"] = os.path.join(TMP, "state")

from government.pnp import config, desk, gitctl, github, publish, reconcile, state, validate  # noqa: E402

GAP = "L-meta-582"
PATH = "lean/PEqualNP/Outside/L_meta_582.lean"
MODULE = "PEqualNP.Outside.L_meta_582"
STATEMENT = "1 + 1 = 2"
SHA = "a" * 40
GOOD = """import Mathlib

namespace PEqualNP.Outside.L_meta_582
lemma helper : 1 = 1 := rfl
end PEqualNP.Outside.L_meta_582

theorem PEqualNP.Outside.L_meta_582 : 1 + 1 = 2 := by
  norm_num
"""


def gap_meta():
    return {"id": GAP, "file": PATH, "module": MODULE,
            "statement": STATEMENT, "imports": []}


def new_state(status="CANDIDATE_READY", **extra):
    fields = dict(state="CANDIDATE_READY", statement=STATEMENT,
                  module=MODULE, path=PATH, imports=[],
                  lease="lease-1", lease_expires_at=time.time() + 1200,
                  candidate_digest=hashlib.sha256(GOOD.encode()).hexdigest())
    fields.update(extra)
    fields["state"] = status
    return state.create(GAP, **fields)


def candidate_file(content=GOOD):
    p = os.path.join(TMP, "candidate.lean")
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    return p


class FakeDesk:
    def __init__(self, beat=200):
        self.beat_status = beat
        self.beats = []
        self.releases = []

    def docs(self, refresh=False):
        return "join.txt"

    def status(self):
        return {"open_gaps": 1, "gaps": [{"id": GAP}]}

    def beat(self, lease):
        self.beats.append(lease)
        return self.beat_status

    def release(self, lease, reason, program=None):
        self.releases.append((lease, reason))
        return {}


class FakeGit:
    def __init__(self, remote=None, build_ok=True):
        self.remote = remote
        self.build_ok = build_ok
        self.calls = []

    def ensure_mirror(self):
        return "base1"

    def fresh_worktree(self, gid, base, branch):
        self.calls.append(("worktree", gid, branch))
        return os.path.join(TMP, "wt")

    def pin_candidate(self, wt, path, data):
        self.calls.append(("pin", path))

    def build(self, wt, module, runner=None):
        return self.build_ok, "ok" if self.build_ok else "boom"

    def signed_commit(self, wt, base, message, signer=None):
        self.calls.append(("commit", message))
        return SHA

    def remote_branch_sha(self, branch):
        return self.remote

    def push_branch(self, branch, pusher=None):
        self.calls.append(("push", branch))
        return SHA

    def all_new_commits_signed(self, wt, base):
        return True

    def new_commits(self, wt, base):
        return [SHA]


class FakeGH:
    def __init__(self, verified=True, existing=None):
        self.verified = verified
        self.existing = existing
        self.created = 0

    def identity(self):
        return config.GH_USER

    def commit_verification(self, sha):
        return {"sha": sha, "verified": self.verified,
                "name": config.AUTHOR_NAME, "email": config.AUTHOR_EMAIL}

    def pr_exists_for(self, branch, gap, api=None):
        return self.existing

    def create_pr(self, branch, gap):
        self.created += 1
        return "123"

    def validate_created(self, number, sha, path, expected_commits=None):
        return {"url": "https://example.test/pr/123"}, []


def fresh(gap=GAP):
    """Isolate each test's state directory."""
    state_path = state.state_path(gap)
    if os.path.exists(state_path):
        os.unlink(state_path)
    d = state.gap_dir(gap)
    events = state.events_path(gap)
    if os.path.exists(events):
        os.unlink(events)


class TestValidate(unittest.TestCase):
    def test_good_candidate(self):
        self.assertEqual(len(validate.validate(gap_meta(), GOOD.encode())), 64)

    def test_rejections(self):
        bad = {
            "sorry": GOOD.replace("norm_num", "sorry"),
            "axiom": "axiom foo : 1 = 2\n" + GOOD,
            "native_decide": GOOD.replace("norm_num", "native_decide"),
            "hash": GOOD + "\n#eval 1\n",
            "quotes": GOOD.replace("1 = 1 := rfl", '1 = 1 := by exact "x"'),
            "wrong statement": GOOD.replace("1 + 1 = 2", "1 + 1 = 3"),
            "extra theorem": GOOD + "\ntheorem other : True := by trivial\n",
            "bad import": GOOD.replace("import Mathlib", "import Mathlib\nimport Evil"),
            "bad option": GOOD.replace("theorem", "set_option pp.all true in\ntheorem"),
            "bad namespace": GOOD.replace("namespace PEqualNP.Outside.L_meta_582",
                                           "namespace Other"),
        }
        for name, content in bad.items():
            with self.subTest(name=name):
                with self.assertRaises(validate.InvalidCandidate):
                    validate.validate(gap_meta(), content.encode())

    def test_size_and_encoding(self):
        with self.assertRaises(validate.InvalidCandidate):
            validate.validate(gap_meta(), GOOD.encode() + b"x" * (513 * 1024))
        with self.assertRaises(validate.InvalidCandidate):
            validate.validate(gap_meta(), b"import Mathlib\n\xff")

    def test_bad_gap_id(self):
        m = gap_meta()
        m["id"] = "not a gap; rm -rf /"
        with self.assertRaises(validate.InvalidCandidate):
            validate.validate(m, GOOD.encode())


class TestState(unittest.TestCase):
    def setUp(self):
        fresh()

    def test_transitions_events_and_intent(self):
        new_state()
        self.assertEqual(state.load(GAP)["state"], "CANDIDATE_READY")
        state.intent(GAP, "push", {"sha": SHA})
        self.assertEqual(state.load(GAP)["intent"]["what"], "push")
        state.clear_intent(GAP)
        self.assertIsNone(state.load(GAP)["intent"])
        state.transition(GAP, "LOCAL_CHECKED")
        state.transition(GAP, "SIGNED", commit_sha=SHA)
        with self.assertRaises(ValueError):
            state.transition(GAP, "RESEARCHING")
        with open(state.events_path(GAP), encoding="utf-8") as f:
            kinds = [__import__("json").loads(l)["kind"] for l in f]
        self.assertIn("state", kinds)
        self.assertIn("update", kinds)


class TestPublish(unittest.TestCase):
    def setUp(self):
        fresh()
        self.file = candidate_file()

    def test_success(self):
        new_state()
        d, g, h = FakeDesk(), FakeGit(), FakeGH()
        r = publish.publish(GAP, self.file, desk=d, git=g, gh=h)
        self.assertEqual(r["pr"], 123)
        self.assertEqual(state.load(GAP)["state"], "PR_OPEN")
        self.assertEqual(h.created, 1)
        self.assertEqual(d.releases, [("lease-1", "submitted")])
        self.assertIn(("push", config.branch_for(GAP)), g.calls)

    def test_restart_after_push_does_not_duplicate(self):
        new_state("PUSHED", commit_sha=SHA, base_sha="base1",
                  branch=config.branch_for(GAP))
        d, g, h = FakeDesk(), FakeGit(remote=SHA), FakeGH(existing="123")
        r = publish.publish(GAP, self.file, desk=d, git=g, gh=h)
        self.assertEqual(r["pr"], 123)
        self.assertEqual(h.created, 0)
        self.assertNotIn(("push", config.branch_for(GAP)), g.calls)

    def test_existing_pr_is_reused(self):
        new_state("LOCAL_CHECKED")
        g, h = FakeGit(remote=SHA), FakeGH(existing="77")
        r = publish.publish(GAP, self.file, desk=FakeDesk(), git=g, gh=h)
        self.assertEqual(r["pr"], 77)
        self.assertEqual(h.created, 0)

    def test_failed_build_stops(self):
        new_state()
        with self.assertRaises(publish.StopPublish):
            publish.publish(GAP, self.file, desk=FakeDesk(),
                            git=FakeGit(build_ok=False), gh=FakeGH())
        self.assertEqual(state.load(GAP)["state"], "FAULT")

    def test_bad_candidate_stops_before_git(self):
        new_state()
        g = FakeGit()
        with self.assertRaises(publish.StopPublish):
            publish.publish(GAP, candidate_file(GOOD.replace("norm_num", "sorry")),
                            desk=FakeDesk(), git=g, gh=FakeGH())
        self.assertNotIn(("push", config.branch_for(GAP)), g.calls)
        self.assertEqual(state.load(GAP)["state"], "FAULT")

    def test_lease_410_stops(self):
        new_state()
        with self.assertRaises(publish.StopPublish):
            publish.publish(GAP, self.file, desk=FakeDesk(beat=410),
                            git=FakeGit(), gh=FakeGH())
        self.assertEqual(state.load(GAP)["state"], "FAULT")

    def test_github_verification_false_means_no_pr(self):
        new_state()
        h = FakeGH(verified=False)
        with self.assertRaises(publish.StopPublish):
            publish.publish(GAP, self.file, desk=FakeDesk(),
                            git=FakeGit(), gh=h)
        self.assertEqual(h.created, 0)
        self.assertEqual(state.load(GAP)["state"], "FAULT")


class TestSignatureFields(unittest.TestCase):
    def good(self, sig="U"):
        return [sig, config.SIGNING_KEY.rstrip("!"), config.AUTHOR_NAME,
                config.AUTHOR_EMAIL, config.AUTHOR_NAME, config.AUTHOR_EMAIL]

    def test_accepts_good_and_locally_untrusted(self):
        gitctl.check_commit_fields(self.good("G"))
        gitctl.check_commit_fields(self.good("U"))

    def test_rejects_wrong_key_author_committer_and_bad_signature(self):
        for fmt in ([self.good()[0], "AAAAAAAA", *self.good()[2:]],
                    [self.good()[0], self.good()[1], "Someone",
                     config.AUTHOR_EMAIL, *self.good()[4:]],
                    [self.good()[0], self.good()[1], *self.good()[2:4],
                     "Someone", config.AUTHOR_EMAIL],
                    self.good("N")):
            with self.subTest(fmt=fmt):
                with self.assertRaises(gitctl.GitError):
                    gitctl.check_commit_fields(fmt)


class TestGitHubValidation(unittest.TestCase):
    def test_post_create_checks(self):
        pr = {"number": 1, "author": config.GH_USER,
              "head_repo": config.FORK, "base_repo": config.UPSTREAM,
              "base_ref": "main", "url": "u"}
        with mock.patch.object(github, "get_pr", return_value=pr), \
             mock.patch.object(github, "pr_files", return_value=[PATH]), \
             mock.patch.object(github, "pr_commits", return_value=[SHA]), \
             mock.patch.object(github, "commit_verification",
                               return_value={"verified": True,
                                             "name": config.AUTHOR_NAME,
                                             "email": config.AUTHOR_EMAIL}):
            got, problems = github.validate_created(1, SHA, PATH)
            self.assertEqual(problems, [])
        with mock.patch.object(github, "get_pr", return_value=pr), \
             mock.patch.object(github, "pr_files", return_value=[PATH, "x"]), \
             mock.patch.object(github, "pr_commits", return_value=[SHA]), \
             mock.patch.object(github, "commit_verification",
                               return_value={"verified": False,
                                             "name": config.AUTHOR_NAME,
                                             "email": config.AUTHOR_EMAIL}):
            _, problems = github.validate_created(1, SHA, PATH)
            self.assertEqual(len(problems), 2)


class TestReconcile(unittest.TestCase):
    def setUp(self):
        fresh()

    def test_pushed_to_accepted(self):
        new_state("PUSHED", commit_sha=SHA, base_sha="base1",
                  branch=config.branch_for(GAP))
        gh = FakeGH(existing="123")
        gh.get_pr = lambda n: {"url": "u", "number": n}
        gh.pr_comments = lambda n: [{"body": "ACCEPTED", "created_at": "2026"}]
        g = FakeGit(remote=SHA)
        r = reconcile.reconcile_gap(GAP, desk=FakeDesk(), gh=gh, git=g)
        self.assertEqual(state.load(GAP)["state"], "ACCEPTED")
        self.assertEqual(r["state"], "ACCEPTED")

    def test_lease_410_becomes_stale(self):
        new_state("LEASED", lease_expires_at=time.time() - 1)
        r = reconcile.reconcile_gap(GAP, desk=FakeDesk(beat=410),
                                    gh=FakeGH(), git=FakeGit())
        self.assertEqual(state.load(GAP)["state"], "STALE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
